# L02 — 流式对话 + LangGraph + LangSmith（第 3 周）

**对应史诗**：EP02

---

## 1. React 组件化

- [ ] 📖 容器/展示组件拆分、列表与输入区解耦
- [ ] 🔧 落地：`apps/web/components/chat/*`

## 2. Zustand

- [ ] 📖 store 划分：sessions / ui / stream
- [ ] 🔧 落地：`apps/web/stores/useChatStore.ts`

## 3. SSE 与流式

- [ ] 📖 SSE 帧格式、`text/event-stream`
- [ ] 📖 ReadableStream 在浏览器中的消费方式
- [ ] 🔧 落地：前后端各一套，Postman/curl 可测通

## 4. LangGraph 核心

- [ ] 📖 `StateGraph`、`State` TypedDict 设计
- [ ] 📖 Node 函数签名、Edge 条件路由
- [ ] 📖 流式节点 `astream_events` 或等价 API
- [ ] 🔧 落地：`apps/api/app/graphs/chat_graph.py`（命名可自定）
- [ ] 🔧 落地：`docs/tech/langgraph-chat.md`

## 5. LangSmith

- [ ] 📖 Project、Tracer、环境变量
- [ ] 📖 从 trace 看：输入 messages → 模型 → 输出
- [ ] 🔧 落地：`.env` 配置 + 一次完整对话 trace 截图存档

## 6. Prompt 与多轮上下文

- [ ] 📖 system / user / assistant 拼接顺序
- [ ] 📖 Token 粗算与历史截断（为 EP06 铺垫）
- [ ] 🔧 落地：`apps/api/app/prompts/chat.py`

---

## 沙箱建议（先实验再接入）

在 `apps/api/scripts/` 建：

- `sandbox_langgraph_minimal.py` — 3 节点图跑通  
- `sandbox_langsmith_trace.py` — 验证 key 有效  

---

## 自测清单

- [ ] 能口述：用户发消息 → LangGraph → SSE → 前端逐字显示  
- [ ] LangSmith 中能看到一次失败与一次成功 trace
