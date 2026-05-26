# Redis 缓存实战总结（EP03 Story 3.3）

> 对应实现：OpenSpec [`ep03-redis`](../../../openspec/changes/archive/2026-05-22-ep03-redis/) · 代码 `apps/api/app/cache/`、`app/core/redis.py`  
> 学习路线：[L01 §4 Redis](../../tasks/learning/L01-foundation.md#4-redis)

---

## 一、本 Story 做了什么

| 能力                      | 路径 / 配置                                                  |
| :------------------------ | :----------------------------------------------------------- |
| Docker Redis 7            | `infra/docker/docker-compose.yml`                            |
| 连接与生命周期            | `app/core/redis.py`、`lifespan` 中 `close_redis()`           |
| 会话列表 Cache-Aside      | `app/cache/conversation_cache.py`                            |
| 流式临时缓冲（EP02 预埋） | `app/cache/stream_cache.py`                                  |
| 依赖健康检查              | `app/services/health_service.py` → `postgres` / `redis` 字段 |
| 环境变量                  | `REDIS_URL`（未配置则禁用缓存）                              |

---

## 二、知识点地图

### 1. 基础设施

- **Docker Compose 多服务**：`postgres` + `redis:7-alpine`，卷 `redis-data`，`healthcheck` + `redis-cli ping`
- **连接串**：宿主机 API 用 `localhost:6379`；容器内（EP08）用服务名 `redis`
- **启动顺序**：`pnpm db:up` → 先 Postgres ready，再 Redis PING

### 2. Redis 客户端（Python）

- **redis-py 5.x 异步**：`Redis.from_url()`，`decode_responses=True`
- **hiredis**：`redis[hiredis]`，降低解析 CPU
- **共享连接**：`ensure_redis()` 单例；路由通过 `Depends(get_redis)` 注入
- **关闭**：FastAPI `lifespan` 调用 `close_redis()`，避免连接泄漏

### 3. Cache-Aside（旁路缓存）— 核心

```text
读：Redis → miss → PostgreSQL → 回填 Redis（TTL）
写：PostgreSQL → commit 成功 → 删除 Redis key
```

| Key                                             | TTL        | 用途                                |
| :---------------------------------------------- | :--------- | :---------------------------------- |
| `memoryos:conversations:user:{user_id}`         | 300s       | 会话列表 JSON（`ConversationRead`） |
| `memoryos:stream:{conversation_id}:{stream_id}` | 3600s      | SSE partial content（EP02）         |
| `memoryos:jwt:blacklist:{jti}`                  | token 寿命 | Story 3.4 预留                      |

**原则**：PostgreSQL 是真相源；Redis 只加速读、临时缓冲，不是主存储。

### 4. 分层

```text
Router → Service（ConversationService + ConversationCache）→ Repository（仅 PG）
```

Repository 不感知 Redis；缓存失效在 **commit 之后**（见下文踩坑）。

### 5. StreamCache（String APPEND）

- `append`：`APPEND` + `EXPIRE`（pipeline）
- `get` / `delete`：供 EP02 SSE 拼接与清理
- 本 Story **未接** HTTP 路由，仅基础设施 + 单元测试

### 6. Health 与 Harness

- `data.status` 保持 `ok`（进程存活）
- `data.redis` / `data.postgres`：`ok` | `down` | `disabled`（依赖可用性）
- Harness：`test_health_contract`、`test_conversations_cache_contract`

---

## 三、必须留意的问题

### 1. 缓存一致性（最重要）

| 问题                       | 后果                           | 正确做法                           |
| :------------------------- | :----------------------------- | :--------------------------------- |
| **commit 前 `invalidate`** | 并发请求用未提交快照回填旧列表 | **`await db.commit()` 后再删 key** |
| 只写 DB 不删缓存           | TTL 内列表陈旧                 | 写成功后 `DELETE` 列表 key         |
| Redis 当唯一数据源         | 重启丢数据                     | 关键数据以 PG 为准                 |

Code review 曾指出此竞态；修复见 `conversations.py` 中 `commit` 后调用 `invalidate_list_cache()`。

### 2. 配置

| 项                      | 说明                                        |
| :---------------------- | :------------------------------------------ |
| `REDIS_URL` 默认 `None` | 未配置 = 禁用缓存；开发在 `.env` 显式设置   |
| 勿提交 `.env`           | 只维护 `.env.example`                       |
| 测试                    | 需 `pnpm db:up`；无 Redis 时相关测试 `skip` |

### 3. 连接与运维

| 项                           | 说明                       |
| :--------------------------- | :------------------------- |
| Health 复用 `ensure_redis()` | 避免每次 health 新建连接   |
| 生产禁用 `KEYS *`            | 按前缀设计 key，精确 `DEL` |
| 所有缓存 key 带 TTL          | 防止内存涨满               |
| 测试 `flushdb()`             | 仅本地测试，禁止用于生产   |

### 4. 实现细节

| 项                   | 说明                                                       |
| :------------------- | :--------------------------------------------------------- |
| 缓存命中仍查 `users` | 校验用户存在；只省略**列表** SQL                           |
| 序列化               | 用 Pydantic `model_dump(mode="json")`，**不要** pickle ORM |
| 异常                 | 缓存读写失败 → debug 日志 + 降级 PG，不抛 500              |

### 5. 本 Story 未做（边界）

- JWT / refresh / token 黑名单 → Story 3.4
- 限流、分布式锁 → EP09
- SSE 业务接入 `StreamCache` → EP02
- GitHub Actions 跑 harness → EP08 / EP00 可选

---

## 四、面试 / 复盘速答

**会话列表放 Redis 还是 PG？**  
列表可缓存；创建与持久化在 PG；Redis 丢数据不应影响业务恢复。

**Cache-Aside 和 Read/Write Through？**  
旁路由应用自己读/写缓存；本项目采用 Cache-Aside。

**Redis 与 PG 不一致？**  
写后删 key + TTL 上限；严重情况靠 invalidate 与较短 TTL。

**为何 Redis down 时 `status` 仍 ok？**  
区分进程存活与依赖可用；缓存可降级，API 仍可无缓存运行。

---

## 五、本地验证

```bash
pnpm db:up
pnpm test:api:harness
bash scripts/api.sh exec pytest tests/unit/test_conversation_cache.py tests/unit/test_stream_cache.py -q
```

---

## 六、相关文档

- [database.md](../../database.md) — Redis key 与 EP 规划
- [infra/docker/README.md](../../../infra/docker/README.md) — Compose 与命令
- [ai-collab-stack.md](../ai-collab-stack.md) — OpenSpec / Harness 协作
