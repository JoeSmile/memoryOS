## 0. Human review（apply 前必过）

- [x] **Tasks reviewed by human**

### Review checklist

- [x] Phase 2 `langgraph-chat.md` 草稿已存在或与本 change 同步
- [x] Mock 路径满足 CI
- [x] 依赖版本与 Python 3.11 兼容

**Reviewer notes:** 用户确认「tasks 人审通过」；按 task 1.1 起 apply。

---

## 1. LangSmith & dependencies（Phase 3）

- [x] 1.1 LangSmith + OpenAI settings、`.env.example`、`requirements.txt`（langgraph、langchain-openai）
  - 预计文件：3 · 层：config、requirements、.env.example

## 2. Graph core

- [x] 2.1 `ChatState` + `chat_graph.py` 最小图（START → call_model → END）
  - 预计文件：2 · 层：graphs/

- [x] 2.2 `MockModelNode` + `stream_tokens` runner（async generator）
  - 预计文件：2 · 层：graphs/ 或 services/

## 3. Tests & docs

- [x] 3.1 `tests/unit/test_chat_graph.py` mock 流式；无网络
  - 预计文件：1 · 层：tests/unit

- [x] 3.2 完成 `docs/tech/langgraph-chat.md`；archive 前勾选 EP02 Story 2.6–2.7 基础项
  - 预计文件：2 · docs、epic

**前置：** `ep02-program` Phase 1 完成。  
**阻塞：** `ep02-chat-sse` Phase 5 后端。
