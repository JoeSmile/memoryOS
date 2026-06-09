# EP09 — 性能优化与安全加固

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 9 周 |
| **优先级** | P1 |
| **学习路线** | [L07-optimization.md](../learning/L07-optimization.md) |

---

## Story 9.1 安全

- [ ] Prompt 注入检测与过滤
- [ ] RAG 检索内容清洗、输入长度限制

## Story 9.2 性能

- [ ] 首 Token 延迟优化
- [ ] 多级缓存（LLM / Embedding）
- [ ] 慢查询与索引复查

## Story 9.3 Token 与成本

- [ ] 全局 Token 统计（输入+输出）
- [ ] 用户配额、会话节流
- [ ] 可选：用量看板

## Story 9.4 限流与审计

- [ ] Redis 滑动窗口限流、防刷
- [ ] 操作审计日志

## Story 9.5 降级

- [ ] 模型故障自动切换（多模型路由）
- [ ] 向量库 / Redis / LLM 不可用兜底

## Story 9.6 架构图

- [ ] 系统总览、RAG、Agent 三张架构图 → `docs/architecture/`

## Story 9.7 LangSmith 生产策略

- [ ] 日志分级、采样率，控制免费额度

## Story 9.8 Agent 过程态 UI（Thinking / Phase）

> **背景**：EP05 已交付 RAG chips + ToolTimeline（**有结果才显示**）。retrieve、LLM 决策、tool 执行期间前端常静默，用户感知「点了发送没反应」。  
> **依赖**：EP05 Unified ReAct SSE（`sources` / `tool_call` / `tool_result` / `token`）。  
> **目标文档**：[`agent-langgraph.md`](../../tech/agent-langgraph.md) § SSE 阶段事件（实现时补充）。

### L1 — 纯前端（零后端改动）

- [ ] `status === "submitted"` 时显示 **Thinking / 处理中** 占位（助手 skeleton 或 composer 上方脉冲条）
- [ ] streaming 期间 composer disabled + Stop 状态与占位联动
- [ ] 空窗期可访问性：`aria-live` 播报「正在处理」

### L2 — SSE phase 事件（API + BFF + Web）

- [ ] Runner 补阶段事件（建议顺序：`start` → `phase:retrieve` → `sources?` → `phase:model` → `tool_call*` → `token*`）
- [ ] BFF 映射为 AI SDK `data-agent-phase`；前端 `AgentPhaseIndicator` 展示：
  - 检索知识库…
  - 分析检索结果…
  - 联网搜索（`tavily_search` 等，tool 名可本地化）
- [ ] Harness 断言 phase 顺序；Web 单测映射帧

### L3 — 体验 polish

- [ ] retrieve / tool 阶段 **pending 占位**（chips / timeline 提前出现「执行中」）
- [ ] 可选折叠「思考过程」面板（prod 默认收起）
- [ ] 与 EP05 `metadata.tool_steps` hydrate 行为一致（刷新后仍可还原）

### 验收

- [ ] 弱 RAG + Tavily 路径：用户从发送到首个可见反馈 ≤ 300ms（L1 占位）
- [ ] 有 Tavily 时：tool 执行期间 timeline 显示 pending → success
- [ ] 无 tool 时：retrieve 阶段有 phase 文案，token 前不再长时间空白

---

## 同步学习

- [ ] AI 安全风险与防护（理解 / 落地）
- [ ] 性能瓶颈定位（理解 / 落地）
- [ ] 企业级权限与数据安全（理解）
- [ ] LangSmith 生产上报策略（理解 / 落地）
- [ ] Agent 过程态 UX：Thinking 占位、SSE phase、ToolTimeline pending（理解 / 落地）→ Story 9.8
