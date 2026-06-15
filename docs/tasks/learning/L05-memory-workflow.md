# L05 — 记忆 + 工作流（第 7 周）

**对应史诗**：[EP06](../epics/EP06-memory.md)（P1，**已落地**）· ~~EP07 工作流~~（**已砍掉**，见 [EP07](../epics/EP07-workflow.md)）

| Part | 史诗 | 状态 | 权威文档 |
|:-----|:-----|:-----|:---------|
| A 记忆 | EP06 | ✅ | [memory-system.md](../../tech/memory-system.md) · [ep06-memory-design.md](../../tech/ep06-memory-design.md) |

---

# Part A — 记忆系统（EP06）

## 1. 上下文与 Token 预算

### 学什么

- [x] 📖 模型 context window；input + output 合计限制
- [x] 📖 tiktoken 按模型计数；中英混合差异
- [x] 📖 预算分配：system + 记忆 + RAG + 历史 + 用户输入
- [x] 🔧 `MAX_CONTEXT_TOKENS`、`RESERVE_FOR_REPLY`（`config.py`）

### 面试常问

- 上下文满了怎么办？业界有哪些方案？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 只数字符不数 token | 仍超限 API 报错 | 统一 `token_counter` |
| 未给回复留预算 | 生成被截断 | `RESERVE_FOR_REPLY` |

---

## 2. 短期记忆（滑动窗口）

### 学什么

- [x] 📖 保留最近 N 轮 / M tokens；从最旧 turn 删起
- [x] 📖 DB 全量 messages ≠ 进 LLM 的全量（裁剪仅图内）
- [x] 📖 `trim_history` 只裁 `messages`；`context_summary` 只参与 token 预算
- [x] 🔧 `services/memory/short_term.py` + `graphs/nodes/trim_history.py`

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 裁剪把 system 裁掉 | 人设丢失 | system / 注入块永不裁 |
| UI 与模型所见不一致 | 用户以为「忘了」 | Header 提示「后端裁剪」 |

---

## 3. 长期记忆

### 学什么

- [x] 📖 finalize 后异步抽取：preference / fact / constraint
- [x] 📖 `memories` 表 + pgvector；TopK 按 `user_id` 过滤
- [x] 📖 与 RAG 世界杯知识库 **读写分离**
- [x] 📖 同 `memory_key` upsert 覆盖；用户可删
- [x] 🔧 `long_term.py` + `load_user_memories` + 前端 `/memories`

### 面试常问

- 长期记忆和 RAG 知识库区别？会不会互相污染？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 抽取幻觉当事实 | 错误人设 | 用户删除 + prune |
| 记忆无限增长 | 检索噪声 | `expires_at` + importance 阈值 |

---

## 4. 会话摘要（中期记忆）

### 学什么

- [x] 📖 `conversations.context_summary`；rolling 合并
- [x] 📖 节流：首次 `SUMMARY_TRIGGER_TOKENS`；后续 increment + cooldown
- [x] 📖 摘要 **下一轮** 才注入；`BackgroundTasks` 不阻塞 SSE
- [x] 🔧 `summary_service.py` + `chat_service` finalize 调度

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 摘要丢关键约束 | 后续违反用户要求 | rolling prompt 强调约束 |
| 每轮都跑 summary | 成本爆炸 | increment + cooldown |

---

## 5. LangGraph 记忆节点（对话图）

- [x] 📖 拓扑：`trim_history` → `load_user_memories` → `retrieve` → `call_model` (± tools)
- [x] 📖 finalize 后并行：summary + memory extract
- [x] 🔧 详见 [ep06-memory-design.md §8 Walkthrough](../../tech/ep06-memory-design.md)

### MVP 后

- [ ] 持久队列、溯源、监控 → [EP11](../epics/EP11-memory-ops.md)
- [ ] 离线评测回归 → [EP12](../epics/EP12-memory-eval.md)

---

# ~~Part B — 工作流（EP07）~~

> **已砍掉**，不实施。部署与上线见 [L06 部署](./L06-deployment.md) · [EP08](../epics/EP08-deployment.md)。

---

## 阶段自测

**EP06（应能口述）**

- [ ] 短期 + 摘要 + 长期 如何同时进 prompt、`trim_history` 与摘要的关系
- [ ] 3 个记忆踩坑 + 对策（裁剪、摘要滞后、RAG 与记忆隔离）

部署上线 → [L06](./L06-deployment.md) · [EP08](../epics/EP08-deployment.md)。
