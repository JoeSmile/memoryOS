# API Harness（L1 契约测试）

Agent / LLM 功能的**确定性回归**放此目录；与 `tests/unit/`（纯函数、无 HTTP）区分。

> **文档状态**：本文总结 **当前 L1 用法** 与局限。`cases/*.yaml`（L2）与多轮统计（L3）落地后，**再回头写一篇完整 Harness 指南**（契约 + 评测 + 统计一体）。

关联：[ai-collab-stack.md](../../../docs/tech/ai-collab-stack.md) §5 · [work-next reference](../../../.cursor/skills/work-next/reference.md)

---

## 1. Harness 是做什么的

**一句话**：在 **不依赖真 LLM Key** 的前提下，用 pytest + httpx 锁住 FastAPI 的 **HTTP 契约** 与 **SSE 帧形状**。

```text
OpenSpec（做什么）→ work-next 实现 → Harness（证明契约没坏）
```

| 测 | 不测 |
|:---|:---|
| 状态码、统一 envelope `{code, message, data}` | 回答是否聪明、准确 |
| 鉴权 / owner / 错误码语义（`40101`、`42201`…） | 浏览器 UI、BFF 路由 |
| SSE 事件类型与顺序（`token`、`sources`、`tool_call`…） | 生产延迟、账单 |
| Mock LLM / Mock Tavily 下图能跑通 | Prompt 注入 100% 防住（→ L2 / 红队） |

---

## 2. 怎么跑

**仓库根目录（推荐）**

```bash
pnpm test:api:harness
# → bash scripts/api.sh exec pytest tests/harness -q
```

**apps/api 内**

```bash
cd apps/api
conda activate memoryos-api   # 或 source .venv/bin/activate
pytest tests/harness -q
```

**前置**

- PostgreSQL 可连（`DATABASE_URL` / 默认 local）
- 已 `alembic upgrade head`
- 部分用例需 **World Cup ETL** 数据（如 `test_demo_turn_contract.py`、`test_rag_*`）

---

## 3. 当前用法（L1）

### 3.1 协作流程中的位置

| 时机 | 要求 |
|:-----|:-----|
| 改 API 行为 / 新 endpoint | **先**（或同步）加/改 `test_*_contract.py`，再实现（TDD） |
| 每个 OpenSpec task 完成 | `tasks.md` 里写的 Harness 用例必须通过 |
| 合并 / PR 前 | `pnpm test:api:harness` 全绿（动过 API 时） |
| 仅改 FE 样式、无 API 契约 | 可跳过 harness；跑 `pnpm --filter @memoryos/web test` |

### 3.2 写法约定

- 文件命名：`test_<领域>_contract.py`
- 客户端：`httpx.AsyncClient` + `ASGITransport(app=app)`，不启真实端口
- 鉴权：`_register_and_login` 辅助 → `Authorization: Bearer …`
- 断言：HTTP 状态 + `body["code"]` / `body["message"]` + 关键 `data` 字段
- **Mock**：fixture 里 `monkeypatch.setattr(settings, "openai_api_key", None)` 等，走 mock graph / mock Tavily，保证 **CI 无 Key 仍绿**

示例（SSE + mock LLM）见 `test_chat_sse_contract.py` 的 `mock_llm` fixture。

### 3.3 现有契约文件（13）

| 文件 | 覆盖 |
|:-----|:-----|
| `test_health_contract.py` | 健康检查 |
| `test_auth_contract.py` | 注册 / 登录 |
| `test_conversations_contract.py` | 会话 CRUD |
| `test_conversations_cache_contract.py` | 会话列表 Redis 缓存 |
| `test_chat_sse_contract.py` | 聊天 SSE、消息落库 |
| `test_chat_cancel_contract.py` | Stop / cancel API |
| `test_rag_contract.py` | 检索 API |
| `test_rag_chat_contract.py` | RAG + chat SSE、sources |
| `test_unified_react_contract.py` | ReAct、`tool_call` / `tool_result` |
| `test_demo_turn_contract.py` | WC demo-turn |
| `test_worldcup_matches_contract.py` | 比赛列表 |
| `test_memories_api_contract.py` | 记忆 API |
| `test_memory_context_contract.py` | 长上下文 / memory 注入 |

**规划中（EP09 等）**：`test_rate_limit_contract.py`、`test_usage_contract.py`、`test_chat_phase_contract.py` 等。

### 3.4 与 Web 测试分工

| 层 | 位置 | 命令 | 职责 |
|:---|:-----|:-----|:-----|
| API L1 | `apps/api/tests/harness/` | `pnpm test:api:harness` | FastAPI + SSE 契约 |
| API unit | `apps/api/tests/unit/` | `pytest tests/unit` | service / sanitizer / 限流算法 |
| Web unit | `apps/web/tests/unit/` | `pnpm --filter @memoryos/web test` | BFF 帧映射、UI 纯函数（如 `chat-thinking-state`） |

流式全链路 = **Harness（API 形状）+ Web unit（BFF 映射）**；不替代手工 smoke。

### 3.5 分层路线图

| 层 | 状态 | 目录约定 |
|:---|:-----|:---------|
| **L1** | ✅ 已落地 | 本目录 `test_*_contract.py` |
| **L2** | 📋 未建 | `cases/*.yaml` + rubric 评测脚本 |
| **L3** | 📋 未建 | 多轮 pass rate 报告 |

L2/L3 就绪后更新本文 **§6 完整总结**（见文末 TODO）。

---

## 4. 局限与弥补

### 4.1 局限

| 局限 | 说明 |
|:-----|:-----|
| **不评 LLM 质量** | Mock 固定输出；换真模型 harness 无感 |
| **Mock 路径 ≠ 生产** | 无 Key 时走 mock；真实 OpenAI/Tavily 超时、计费、格式差异未覆盖 |
| **环境重** | 依赖 PostgreSQL + migrate；部分需 WC ETL |
| **不测 BFF / 浏览器** | Next `route.ts`、AI SDK 集成不在此目录 |
| **L2/L3 空缺** | 回答好不好、注入能否防住，L1 断言不了 |
| **非确定性** | 真 LLM 接入 CI 时同一用例可能 flaky |
| **契约维护成本** | 过细 → 重构痛；过粗 → 漏回归 |

### 4.2 弥补（当前实践）

```text
L1 Harness（PR 必绿）     ← 本目录
Web unit（动 BFF/FE 必跑）  ← apps/web/tests/unit
API unit（算法/规则）       ← apps/api/tests/unit
手工 smoke（EP08 compose + Ollama）  ← 真流式，非 PR 门禁
Garak 红队（EP09 规划 nightly）      ← 非阻塞
LangSmith 采样（EP09 9.7）           ← 生产排障，非 CI 门禁
```

| 缺口 | 弥补 |
|:-----|:-----|
| 回答质量 | L2 `cases/*.yaml` + rubric（待建） |
| Mock vs 真模型 | Staging / local 设 Key 冒烟 |
| 前端 | vitest + 关键路径手点 |
| 安全 / 限流 | 专用 contract（EP09）+ Garak |
| 环境一致 | Docker compose + CI 文档固定 migrate/ETL |

**原则**：L1 永远当 **API 契约硬门禁**；质量与语义靠 L2+ 与人审，不把真 LLM 塞进每次 PR。

---

## 5. 发挥最大价值的检查清单

- [ ] API 变更是否先写了 contract 断言（状态码 + `code` + 关键字段）？
- [ ] 是否用 monkeypatch 关 Key，保证无 GPU/无 OpenAI 可跑？
- [ ] OpenSpec `tasks.md` 是否写明 Harness 文件名？
- [ ] 合并前是否 `pnpm test:api:harness` 全绿？
- [ ] 动 BFF/SSE 映射是否补了 `apps/web/tests/unit`？
- [ ] 需要语义评测的场景是否记在 L2 backlog，而不是硬塞进 L1？

---

## 6. TODO — L2/L3 后全文修订

当以下条件就绪时，**回头重写/扩展本文**为「Harness 完整指南」：

- [ ] `harness/cases/*.yaml`（足球正例、注入反例、RAG rubric）
- [ ] L2 评测脚本（可关 Key 的 rule 路径 + 可选 LLM judge）
- [ ] L3 多轮 pass rate 报告（Agent / 安全回归）
- [ ] EP09 安全 / 限流 / phase / usage 等 L1 contract 齐套

修订时合并：L1 契约表 + L2 案例说明 + L3 指标 + CI 矩阵 + 与 Garak/LangSmith 分工。
