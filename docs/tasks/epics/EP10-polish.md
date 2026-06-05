# EP10 — 项目打磨与面试冲刺

| 属性 | 值 |
|:-----|:---|
| **周期** | 第 10-12 周 |
| **优先级** | P0 |
| **学习路线** | [L08-interview.md](../learning/L08-interview.md) |

---

## Story 10.1 前端体验

- [ ] 消息重试、收藏、导出
- [ ] 知识库权限（私有/公开）
- [ ] UI 统一（Loading / Empty / Error）

## Story 10.2 多模型

- [ ] Provider 抽象：OpenAI / DeepSeek / 通义 / 本地
- [ ] 主备降级、灰度配置

## Story 10.3 质量

- [ ] 压测（k6 / locust）、修线上 BUG
- [ ] 跨浏览器冒烟

## Story 10.4 技术沉淀

- [ ] `docs/tech/` 难点与踩坑合集
- [ ] LangGraph + LangSmith + LlamaIndex 组合话术

## Story 10.5 面试素材

- [ ] RAG / Agent / 记忆高频题 + 本项目标准答
- [ ] 简历 STAR 改写
- [ ] 3min / 5min 项目口述稿
- [ ] 全真模拟面试 ≥ 3 轮

## Story 10.6 深度交互（V3 backlog，EP02–EP07 后再做）

> 目标：页面「多动手」且面试能讲清技术点；**不挡** `ep02-chat-sse` / `ep02-chat-ui` 最小闭环。

**聊天**

- [ ] 消息：重新生成、编辑后重发；建议追问 chips
- [ ] 侧栏：拖拽排序 / 置顶会话
- [ ] SSE 扩展事件：`step`（Agent/图节点）、`citation`（RAG 溯源）

**RAG（EP04 后）**

- [ ] 回答内引用点击 → 侧栏展示 chunk
- [ ] 上传进度 + 分块预览；dev 检索调试面板（TopK 滑动）

**记忆 / Agent（EP05–EP06）**

- [ ] 记忆卡片 CRUD；写入前用户确认（human-in-the-loop）
- [ ] Tool 调用卡片 + LangGraph 节点 live 状态

**预埋（EP02 做 chat 时注意）**

- [ ] 消息 `id` 稳定（勿 `key={index}`）；SSE 帧预留 `event` 字段扩展

---

## 同步学习

- [ ] 薄弱点针对性补强（自定清单）
- [ ] 大厂 / 外企 AI 岗面试侧重点
- [ ] 商业化与产品化思路（拓展）
