# 限流、Token 配额与审计

> **状态**：EP09 Story 9.3 / 9.4 **设计已定、尚未实现**（brownfield 无限流、无 `audit_log`、无 `token_usage`）  
> **关联**：[`ep09-optimization`](../../openspec/changes/ep09-optimization/) · [L07 §3–4](../tasks/learning/L07-optimization.md) · [聊天安全](./chat-security.md) · OpenSpec [`rate-limit-audit`](../../openspec/changes/ep09-optimization/specs/rate-limit-audit/spec.md) · [`token-usage`](../../openspec/changes/ep09-optimization/specs/token-usage/spec.md)

---

## 1. 这篇文档解决什么问题

MemoryOS 已具备 JWT 鉴权、会话 owner 校验、可选 Redis（流式 cancel、会话列表缓存）。但在 **防刷、控成本、事后追溯** 上仍是空白：

| 能力 | 现网 | EP09 目标 |
|:-----|:-----|:----------|
| 请求频率限制 | 无 | Redis 滑动窗口，按路由分级 |
| 日 Token 配额 | 无 | PG 落库 + 日聚合，超限 42902 |
| 敏感操作审计 | 无 | `audit_log` 表 + 关键事件写入 |
| Redis 不可用 | 聊天仍可用（redis 可选） | 限流 fail-open，缓存跳过（D6） |

本文说明：**我们要做什么、逻辑怎么设计、现网不足、企业级长什么样、差距在哪**。实现任务见 `openspec/changes/ep09-optimization/tasks.md` §3、§4。

---

## 2. 三层「滥用防护」如何分工

不要把限流、配额、安全过滤混为一谈。EP09 用三条独立防线：

```text
请求进入 API
    │
    ├─► Story 9.1 内容安全（422）
    │       长度、注入规则、RAG 清洗 — 「这条内容能不能进模型」
    │
    ├─► Story 9.4 限流（42901）
    │       短窗口请求次数 — 「你是不是刷接口」
    │
    ├─► Story 9.3 Token 配额（42902）
    │       当日累计 Token — 「你今天是不是用太多」
    │
    └─► 业务 handler → LLM / DB
            │
            └─► Story 9.4 审计（异步/同步写 PG）
                    「敏感操作留痕」— 不挡请求，供追溯
```

| 层级 | 错误码 | 检查时机 | 存储 | 典型攻击 |
|:-----|:-------|:---------|:-----|:---------|
| 内容安全 | 422 | LLM 前 | 无状态规则 | 注入、超长 |
| 限流 | **42901** | handler 前 | Redis | 脚本刷 chat、撞库 |
| Token 配额 | **42902** | 开流前 | PostgreSQL | 慢速烧钱、Agent 多轮 |
| 审计 | — | 操作成功后/失败后 | PostgreSQL | 事后追责、合规 |

**顺序建议**（实现时）：鉴权 → 限流 → 内容校验 → 配额 → 业务；审计在业务关键点 **追加写入**，不参与拒绝链（登录失败除外：可先限流再校验密码）。

---

## 3. 现网能力与不足（Brownfield）

### 3.1 已有

- **鉴权**：`/api/v1/auth/login|register`；chat / demo-turn 需 JWT；`get_owned_conversation` 防越权。
- **Redis（可选）**：`REDIS_URL` 未设则 `get_redis()` 返回 `None`；用于 stream cancel 标记、会话列表 cache 等。
- **Harness**：auth、chat SSE、demo-turn 契约测试；**尚无** 42901/42902/audit 断言。

### 3.2 不足（EP09 要补）

| 不足 | 风险 | EP09 对策 |
|:-----|:-----|:----------|
| chat / demo-turn **无频率上限** | 单账号脚本可打满 LLM、Tavily | 9.4 滑动窗口 |
| login **无 IP 限流** | 撞库、注册 spam | 9.4 login 10/min/IP |
| **无 Token 计量** | 账单不可见、无法按用户封顶 | 9.3 finalize 落库 |
| **无审计表** | demo 滥用、登录异常无法追溯 | 9.4 `audit_log` |
| 429 错误码 **未统一** | 前端/BFF 无法区分「刷太快」vs「配额用尽」 | 42901 vs 42902 |
| Redis 宕机 **无限流降级策略** | 要么全挂要么裸奔 | `RATE_LIMIT_FAIL_OPEN` |

### 3.3 与「聊天安全」文档的关系

[`chat-security.md`](./chat-security.md) 中的 **DoS / 烧钱、工具链滥用** 行，主防线即 **限流 + Token 配额**；审计负责 **事后**，不替代 9.1 内容过滤。

---

## 4. Story 9.4 限流 — 我们要做什么

### 4.1 目标

- Redis **滑动窗口**计数，按 **路由类别** 独立限额。
- Key：**已登录用 `user_id`**，**未登录用客户端 IP**（从 `X-Forwarded-For` 或 `request.client.host` 取，部署时需信任代理配置）。
- 环境开关：`RATE_LIMIT_ENABLED`（默认 development 可 off，staging/prod on）。
- 超限：`HTTP 429`，body `code=42901`, `message=rate_limit_exceeded`。
- Redis 不可用且 `RATE_LIMIT_FAIL_OPEN=true`：**放行 + structured warn**（与 D6 降级一致）。

### 4.2 路由与默认阈值（design D3）

| 路由类 | 标识 | 默认限额 | Key | 说明 |
|:-------|:-----|:---------|:----|:-----|
| Chat 流式 | `POST /api/v1/chat/completions` | **60 / 分钟 / user** | `user:{id}` | 含 regenerate；一次 POST 计 1 次 |
| Demo 分析 | `POST .../conversations/{id}/demo-turn` | **30 / 分钟 / user** | `user:{id}` | 触发完整 RAG+LLM，成本高 |
| 登录 | `POST /api/v1/auth/login` | **10 / 分钟 / IP** | `ip:{addr}` | **凭证校验前**限流，防撞库 |
| 注册（建议同 task 扩展） | `POST /api/v1/auth/register` | 可与 login 共用 IP 桶或略松 | `ip:{addr}` | spec 未单列，实现时可 5–10/min |

阈值均通过 env 覆盖，例如：

```text
RATE_LIMIT_CHAT_PER_MIN=60
RATE_LIMIT_DEMO_TURN_PER_MIN=30
RATE_LIMIT_LOGIN_PER_IP_PER_MIN=10
RATE_LIMIT_WINDOW_SECONDS=60
```

### 4.3 滑动窗口逻辑（Redis）

**推荐实现**：Sorted Set 时间戳日志（精确滑动窗，多 API 实例共享 Redis）。

```text
Key:    rl:{route_class}:{identity}
        例: rl:chat:user:550e8400-e29b-41d4-a716-446655440000
            rl:login:ip:203.0.113.42

Window: W 秒（默认 60）

每次请求:
  1. now = 当前 unix 时间（秒或毫秒，全链路统一）
  2. ZREMRANGEBYSCORE key 0 (now - W)     # 去掉窗口外记录
  3. count = ZCARD key
  4. if count >= limit → 拒绝 42901
  5. ZADD key now "{now}:{request_id}"     # member 唯一，防同秒覆盖
  6. EXPIRE key W + 小缓冲

Lua 脚本包 2–6 步，保证原子性。
```

**为何不用纯 INCR + TTL 固定窗**：固定 1 分钟窗在边界会出现「上一窗末尾 + 下一窗开头」双倍 burst；滑动窗更平滑。L07 提到的「令牌桶」允许合法 burst，EP09 **首版不采用**；若 demo 误伤多，可在 9.4 后迭代为 **滑动窗 + 小 burst 配额**。

**为何用 Redis 而非 PG**：限流是高频读写的 ephemeral 状态；PG 会成为热点且难跨实例原子计数。

### 4.4 接入方式

```text
FastAPI
  │
  ├─ Option A: RateLimitMiddleware（按 path 匹配 route_class）
  │
  └─ Option B: Depends(check_rate_limit("chat")) 挂在各 router

建议:
  - login: middleware 或 auth router 内 **最先** 执行（密码 hash 前）
  - chat / demo-turn: Depends，在 prepare_completion / append_demo 前
  - 限流失败 **不** 写 audit（避免 audit 表被刷爆）
```

**BFF（Next.js）**：可加同源限流减轻无效请求；**必须**在 FastAPI 再验，防直连 API。

### 4.5 与 Token 配额（9.3）的调用顺序

```text
chat/completions:
  1. JWT 有效
  2. rate limit 42901
  3. content_validator + prompt_security 422
  4. token_quota_service：当日 aggregate + 预估 42902（可选粗估）
  5. prepare_completion → stream → finalize 写 token_usage
```

配额用 **PostgreSQL** 聚合（`SUM(total_tokens) WHERE user_id AND date = UTC today`），与 Redis 限流 **解耦**：一个管「次数」，一个管「总量」。

### 4.6 Fail-open 行为

| `RATE_LIMIT_ENABLED` | Redis | `RATE_LIMIT_FAIL_OPEN` | 行为 |
|:---------------------|:------|:-----------------------|:-----|
| false | — | — | 不限流 |
| true | OK | — | 正常限流 |
| true | 失败 | true | **放行**，log `rate_limit_degraded` |
| true | 失败 | false | **503 或 429**（实现时二选一，design 倾向 fail-open） |

与 EP08 Docker 本地：`REDIS_URL` 未设时限流失效；生产应 **强制 Redis + 限流开启**。

---

## 5. Story 9.4 审计 — 我们要做什么

### 5.1 目标

- 持久化 **敏感、低频、高价值** 操作，供安全排查与运维追溯。
- **不是**全量 access log；**不是** LangSmith trace；**不是**每条 chat 消息。

### 5.2 表结构（规划）

```sql
-- Alembic migration（字段名实现时可微调）
CREATE TABLE audit_log (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NULL REFERENCES users(id),  -- 登录失败可为 NULL
  action          VARCHAR(64) NOT NULL,            -- 见下表
  resource_type   VARCHAR(32) NULL,                -- conversation, user, ...
  resource_id     VARCHAR(128) NULL,
  ip_address      INET NULL,
  user_agent      VARCHAR(512) NULL,
  metadata        JSONB NOT NULL DEFAULT '{}',     -- 轻量，禁止全量 prompt
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_user_created ON audit_log (user_id, created_at DESC);
CREATE INDEX idx_audit_log_action_created ON audit_log (action, created_at DESC);
```

### 5.3 首批写入事件（spec + design）

| action | 触发时机 | resource | metadata 示例 | 为何记 |
|:-------|:---------|:---------|:----------------|:-------|
| `demo_turn` | demo-turn **成功** append 后 | `conversation_id` | `template_id`, `match_id` | 高成本路径、产品滥用分析 |
| `login_failed` | 密码错误且 **同 IP 达阈值** 或 **每次失败**（实现择一） | — | `email_hash` 或 masked email | 撞库检测 |
| `login_success` | 可选，默认 **不记**（量大） | — | — | 企业版才常开 |
| `conversation_delete` | 若 API 暴露删除 | `conversation_id` | — | 防抵赖 |
| `rate_limit_exceeded` | 可选 | — | `route_class` | 安全分析；注意量 |

**明确不写 audit 的**：

- 每条 `chat/completions` 成功/失败（用 `token_usage` + 应用 log）
- 全量 request body / system prompt
- LangSmith 已采样的 span 重复落 audit

### 5.4 写入逻辑

```text
demo-turn handler:
  ... append_demo_turn 成功 ...
  await audit_repo.append(
      user_id=current_user.id,
      action="demo_turn",
      resource_type="conversation",
      resource_id=conversation_id,
      ip=client_ip,
      metadata={"template_id": ..., "match_id": ...},
  )
  await db.commit()  # 与业务同事务或紧随其后

login_failed:
  auth_service.login 抛 InvalidCredentials
  → 在 handler 或 service 内 audit（不阻塞响应）
  → metadata 脱敏：仅存 email 域或 HMAC(email)
```

**原则**：

1. **失败不影响主路径**：audit 写失败 log error，不导致 demo 已成功却返回 500（可 BackgroundTasks 异步写，Harness 用 sync 便于断言）。
2. **最小必要字段**：合规够用即可，避免 GDPR/PII 二次堆积。
3. **时钟 UTC**：与 token_usage 日界一致。

### 5.5 查询 API（EP09 最小集）

OpenSpec 仅要求：**未认证查 audit → 401**。

| 级别 | EP09 | 企业级 |
|:-----|:-----|:-------|
| 用户查自己 | 非必须 | 少见 |
| Admin RBAC | 非必须 | 必须 |
| 导出 SIEM | 无 | Splunk/Datadog |

EP09 **可不暴露** HTTP 查询接口，仅 DB/运维工具查；若加 `GET /api/v1/admin/audit`，须独立 admin 角色（Non-Goal 完整 RBAC 可后置）。

---

## 6. Story 9.3 Token 配额（交叉说明）

限流文档无法脱离成本管控，9.3 与 9.4 常一起落地：

| 项 | 设计 |
|:---|:-----|
| 落库 | stream **finalize** 读 provider `usage` → `token_usage` 表 |
| 聚合 | `user_id` + **UTC 日** `SUM(total_tokens)` |
| 配额 env | `USER_DAILY_TOKEN_QUOTA`（open question 默认 100000） |
| 拒绝 | 新开流前检查，**42902** `token_quota_exceeded` |
| 只读 API | `GET /api/v1/usage/me` 可选 |

**与限流区别**：用户 59 次/分钟各发 1k token，限流可能拦；用户 5 次/分钟各发 30k token，配额拦。Agent + Tavily 多轮场景 **两者都要**。

---

## 7. 企业级是什么样的

### 7.1 限流 / 配额（企业）

| 能力 | 企业常见做法 | MemoryOS EP09 |
|:-----|:-------------|:--------------|
| 入口 WAF / CDN 限流 | Cloudflare、AWS WAF 防 DDoS | 无（EP14/K8s 前置） |
| 多维度 key | user + org + API key + route | user 或 IP |
| 令牌桶 / leaky bucket | 允许短 burst | 滑动窗，无 burst |
| 分级套餐 | 免费 10/min，Pro 120/min | 全局 env |
| 分布式一致性 | Redis Cluster / 专用限流服务 | 单 Redis |
| 429 响应 | Retry-After、Problem Details | 统一 envelope 42901/02 |
| 成本预算 | 按 org 月预算、告警 | 按 user 日 Token |
| 实时账单 | Stripe + usage meter | 仅 DB 聚合 |

### 7.2 审计（企业）

| 能力 | 企业常见做法 | MemoryOS EP09 |
|:-----|:-------------|:--------------|
| 覆盖范围 | 所有 CRUD、权限变更、导出 | demo-turn + login 失败等 |
| 不可篡改 | append-only、WORM、哈希链 | 普通 PG 表 |
| 保留期 | 1–7 年策略 | 未定义（需 migration 文档补） |
| 查询 | Admin UI + SIEM | 无 UI，可选无 HTTP |
| 身份 | 谁、何时、何地、何设备、何结果 | user + ip + action |
| 关联 trace | trace_id 进 audit | 可选 metadata |
| 合规 | SOC2、ISO27001 控制项映射 | 学习/基线级 |

### 7.3 可观测分工（避免重复）

```text
应用 log（结构化）     → 排障、采样
LangSmith（9.7）       → LLM 链路、延迟、prompt 调试（生产采样）
token_usage（9.3）     → 成本计量
audit_log（9.4）       → 安全/合规敏感操作
access log（nginx）    → 基础设施层（EP09 不建表）
```

---

## 8. 差距总结

| 维度 | 现网 | EP09 完成后 | 企业级仍缺 |
|:-----|:-----|:------------|:-----------|
| 防刷 chat | ❌ | ✅ 60/min/user | WAF、bot 检测、CAPTCHA |
| 防撞库 | ❌ | ✅ 10/min/IP | 账户锁定、MFA、风险登录 |
| 日成本封顶 | ❌ | ✅ Token 配额 | 组织级预算、告警、发票 |
| 敏感操作追溯 | ❌ | ✅ 最小 audit | 全量 RBAC 审计、SIEM |
| Redis 降级 | 部分（无 Redis 仍可聊天） | ✅ fail-open 文档化 | 多 AZ Redis、限流专用集群 |
| 错误可区分 | ❌ | ✅ 42901/02 | 统一 API 网关错误规范 |
| 合规认证 | ❌ | ❌ | SOC2、数据驻留、保留策略 |

**EP09 定位**（proposal Non-Goals）：**企业可运维基线**，不是完整 SOC2 / 计费 / WAF。完成 9.3+9.4 后，MemoryOS 具备 **可演示的防刷 + 可追溯 + 可计量**；上公网 SaaS 仍需 WAF、MFA、SIEM、组织配额等 **EP09 之后** 的 change。

---

## 9. 实现清单与文件映射

| Task | 交付 | 路径（规划） |
|:-----|:-----|:-------------|
| 3.1 | 滑动窗 limiter + config | `apps/api/app/core/rate_limit.py`, `core/config.py` |
| 3.2 | 挂 login / chat / demo-turn | `middleware/rate_limit.py` 或 router Depends |
| 3.3 | audit 表 + 写入 | Alembic, `repositories/audit_repository.py`, demo-turn / auth 钩子 |
| 4.1–4.2 | token_usage + 配额 + `UsageRecorder` | `services/token_quota_service.py`, `chat_service.py` |
| Harness | 42901, 42902, audit 行 | `tests/harness/test_rate_limit_contract.py` 等 |

**建议实现顺序**：3.1 → 3.2（Harness 42901）→ 4.1 → 4.2（42902）→ 3.3（audit）→ fail-open 集成测试（task 8.2）。

---

## 10. 环境变量汇总（规划）

| 变量 | 默认（建议） | 作用 |
|:-----|:-------------|:-----|
| `RATE_LIMIT_ENABLED` | dev: false, prod: true | 总开关 |
| `RATE_LIMIT_FAIL_OPEN` | true | Redis 故障时放行 |
| `RATE_LIMIT_WINDOW_SECONDS` | 60 | 滑动窗宽度 |
| `RATE_LIMIT_CHAT_PER_MIN` | 60 | chat completions |
| `RATE_LIMIT_DEMO_TURN_PER_MIN` | 30 | demo-turn |
| `RATE_LIMIT_LOGIN_PER_IP_PER_MIN` | 10 | login |
| `USER_DAILY_TOKEN_QUOTA` | 100000（待定） | 日 Token 上限 |
| `REDIS_URL` | 本地可空 | 限流依赖 Redis |

---

## 11. 参考

- OpenSpec design **D3**（限流）、**D6**（Redis 降级）、**D2**（Token）、**D8**（北向治理 / EP13）
- [`chat-security.md`](./chat-security.md) §1 威胁表（DoS / 烧钱）
- [`chat-stream-cancel.md`](./chat-stream-cancel.md) — Redis 在 cancel 中的现有用法
- [EP13 分布式 epic](../tasks/epics/EP13-memory-distributed.md) · [EP14 K8s](../tasks/epics/EP14-k8s-cloud.md)
- [Redis rate limiting patterns](https://redis.io/docs/latest/develop/use/patterns/rate-limiting/)

---

## 12. 与 EP13 / EP14 分布式部署

> **结论**：EP09 的 Redis 限流、PG 审计/配额 **不阻碍** EP13 Remote Graph 热插拔与 EP14 多副本；它们是多实例下的 **正确抽象**。需遵守 **北向集中治理、东向最小暴露** 边界，避免 Remote 子服务重复或绕过防线。

### 12.1 目标架构（EP13 瘦身版）

```text
浏览器 → BFF → API 主编排（北向 EP09 防线）
                  │  JWT · 限流 · 输入 Guard · 配额 · audit 写入
                  │  graph_registry 动态路由
                  ▼
        ┌─────────┼─────────┐
        ▼         ▼         ▼
  langgraph-chat  langgraph-*  worker×N
        │         │         │
        └─────────┴─────────┘
                  ▼
        postgres（token_usage · audit_log · graph_registry）
        redis（限流 · cancel · cache）— 多 API Pod 共享
```

对外 **SSE / BFF 契约不变**（EP13 约束）；变的是 **LLM/Agent 执行位置**（embedded → remote），不是 **治理层位置**。

### 12.2 北向 vs 东向：EP09 各能力放哪

| EP09 能力 | 部署层 | EP13 remote 后 | 禁止 |
|:----------|:-------|:---------------|:-----|
| 限流 42901 | API 路由 / middleware | 仍在 API；Redis 全局计数 | 每 Remote Graph 各做一套 |
| Token 配额 42902 | API 开流前检查 + finalize 落库 | 配额检查在 API；usage 由 runner/SSE 回传 | Remote 直连公网不计费 |
| 输入 Guard 422 | API `prepare_completion` / demo-turn | 进 Remote **之前** 完成 | 把 Guard 只写在子图节点 |
| `rag_sanitizer` | ETL + retrieve（共用模块） | 子图若自 retrieve → **import 同一包** | 子图 copy 一套规则 |
| `audit_log` | API handler（demo-turn、login 等） | 仍在 API；子图失败由 API 记 degrade | 全量 chat 写 audit |
| BFF prompt-guard | Next BFF（可选 UX） | 不变；API 权威 | 仅 BFF 无 API |

**原则**：公网流量 **只打 API**；Remote Graph / worker **内网可达**，注册走 `POST /internal/graphs/register`（EP13，内网 token）。

### 12.3 为何 Redis 限流利于水平扩展

| 方式 | 多 API Pod | EP09 |
|:-----|:-----------|:-----|
| 进程内存计数 | 每 Pod 独立限额 → 总限额 = N × limit | ❌ |
| Redis 滑动窗 | 全集群共享 `rl:{route}:{user\|ip}` | ✅ task 3.1 |

与 **cancel**（Redis 标记）、**stream cache** 同一 Redis 实例；EP14 云 Redis / Redis Cluster 替换 URL 即可，**不改 limiter 逻辑**。

生产建议：`RATE_LIMIT_FAIL_OPEN=true` 仅 dev/staging；TKE 托管 Redis + 限流开启，fail-open 改为告警 + 可选 fail-closed（EP14 Story 14.4）。

### 12.4 Token 计量与 Remote Graph（EP13 契约）

EP09 embedded 路径：

```text
API ChatService.finalize → 读 runner usage → token_usage 表
```

EP13 remote 路径（**EP09 预留、EP13 实现**）：

```text
API 开流前：token_quota_service.check（42902）
Remote Agent Server 流式 → SSE 帧含 usage（或 done 事件）
API finalize：UsageRecorder.record(...)  ← 同一接口，embedded/remote 双 adapter
```

EP09 task **4.2** 须抽出 `UsageRecorder`（或等价 protocol），避免 EP13 重写配额逻辑。

### 12.5 RAG 清洗与热插拔 Agent

| 形态 | sanitizer 调用点 |
|:-----|:-----------------|
| embedded（EP09） | API `retrieve` 节点 + ETL |
| remote retrieve | 子图容器依赖 **`app.services.security.rag_sanitizer`** 同源 wheel/包 |
| retrieve 留 API | API 清洗后把 `<DOCS>` 传给 Remote（更简单，EP13 可选） |

`rag_sanitizer` 放在 **`services/security/` 可 import 包**（非 LangGraph 节点内联），便于 ETL、worker、未来子图共用。

### 12.6 SSE 多副本（EP13/14，与 EP09 无冲突）

| 话题 | 说明 |
|:-----|:-----|
| 限流 | 与哪台 Pod 处理无关（Redis） |
| 配额 | PG 聚合，与 Pod 无关 |
| SSE 粘滞 | EP13：chat **单副本** 或 Ingress **session affinity**；与 42901 独立 |
| audit | 写 PG，与 Pod 无关 |

EP09 **不解决** SSE 粘滞；EP14 Story 14.2 解决。两者并行。

### 12.7 EP09 实现约束（避免 EP13 返工）

1. 治理代码挂在 **FastAPI 路由 / ChatService 北向**，不塞进 `graphs/nodes/`（Remote 后节点可能不在本进程）。
2. `services/security/*` 无 FastAPI 依赖，ETL 脚本可 import。
3. 限流 key 格式稳定：`rl:{route_class}:{identity}`，便于 EP13 按 `graph_name` 扩展新 route_class。
4. Harness 断言 **HTTP envelope**（422/42901/42902），不绑 embedded 内部类；EP13 `LANGGRAPH_MODE=remote` 复用同一契约。
5. 架构图 task 9.1 增加 **北向治理层** 标注，与 EP13 `distributed-hotplug.md` 衔接。

### 12.8 EP13/14 再补的能力（非 EP09）

| 能力 | 史诗 |
|:-----|:-----|
| `graph_registry` + 热插拔 | EP13 |
| internal register API 限流 | EP13 |
| Remote usage SSE 回传 | EP13 Story 13.3 |
| Ingress 限流 / WAF | EP14 |
| 东向 mTLS | EP13+ backlog |

