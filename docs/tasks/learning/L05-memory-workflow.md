# L05 — 记忆 + 工作流（第 7 周）

**对应史诗**：EP06（P1）+ EP07（P2 可裁剪）

---

# Part A — 记忆系统（EP06）

## 1. 上下文与 Token 预算

### 学什么

- [ ] 📖 模型 context window；input+output 合计限制
- [ ] 📖 tiktoken 按模型计数；中英混合差异
- [ ] 📖 预算分配：system + 记忆 + 检索 + 历史 + 用户输入
- [ ] 🔧 配置项：`MAX_CONTEXT_TOKENS`、`RESERVE_FOR_REPLY`

### 面试常问

- 上下文满了怎么办？业界有哪些方案？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 只数字符不数 token | 仍超限 API 报错 | 统一 tokenizer |
| 未给回复留预算 | 生成被截断 | 预留 output tokens |

---

## 2. 短期记忆（滑动窗口）

### 学什么

- [ ] 📖 保留最近 N 轮或最近 M tokens
- [ ] 📖 与 DB 全量历史关系：DB 存档 ≠ 全部进 prompt
- [ ] 📖 LangGraph 节点：组装 messages 前裁剪
- [ ] 🔧 `services/memory/short_term.py`

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 裁剪把 system 裁掉 | 人设丢失 | system 永不裁 |
| 多 tab 会话串窗口 | 答非所问 | thread_id 隔离 |

---

## 3. 长期记忆与画像

### 学什么

- [ ] 📖 对话后异步抽取：偏好、事实、禁忌（结构化 JSON）
- [ ] 📖 `memories` 表：type、content、importance、embedding
- [ ] 📖 LlamaIndex 记忆索引：检索 TopK 注入 system
- [ ] 📖 矛盾更新：新事实覆盖旧（同 key 冲突策略）
- [ ] 🔧 `services/memory/long_term.py` + 前端「我的记忆」页

### 面试常问

- 长期记忆和 RAG 知识库区别？会不会互相污染？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 抽取幻觉当事实 | 错误人设 | 用户确认或置信度阈值 |
| 记忆无限增长 | 检索噪声 | 定期清理 + importance |
| 敏感信息进记忆 | 合规问题 | 脱敏 + 用户删除权 |

---

## 4. 摘要压缩

### 学什么

- [ ] 📖 触发条件：历史 token > 阈值
- [ ] 📖 摘要模型/提示词：保留决策、待办、用户约束
- [ ] 📖 结构：`[Summary] + [Recent turns]`
- [ ] 🔧 异步任务，不阻塞用户发消息

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 摘要丢关键约束 | 后续违反用户要求 | 摘要 prompt 强调约束 |
| 同步摘要做在热路径 | 首 token 慢 | 后台生成 |

---

## 5. LangGraph 记忆节点

- [ ] 📖 `load_memory` → `chat` → `extract_memory`（async）
- [ ] 🔧 `docs/tech/memory-system.md`

---

# Part B — 工作流（EP07，可选）

> Remote Graph / 子图热插拔见 [L09](./L09-distributed-orchestration.md)、[EP13](../epics/EP13-memory-distributed.md)。队列生产实现见 [EP11](../epics/EP11-memory-ops.md)。

## 1. 编排概念

- [ ] 📖 DAG vs 状态机；LangGraph 即状态机实现
- [ ] 📖 节点：解析 → 提取 → 匹配 → 报告
- [ ] 📖 队列：BackgroundTasks vs Celery/ARQ（量大再上）→ **EP11 落地队列，EP13 多 Worker 容器**

## 2. 简历 Demo

- [ ] 🔧 PDF 上传 → 技能 JSON → JD 匹配报告
- [ ] 🔧 简易进度 API + 前端步骤条

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 与 Agent 图两套标准 | 维护成本高 | 复用 LangGraph 模式 |
| 长任务无状态 | 刷新丢进度 | job_id + DB 状态 |

---

## 阶段自测

- [ ] 口述：短期 + 摘要 + 长期 如何同时进 prompt  
- [ ] 3 个记忆相关踩坑 + 对策  
- [ ] （EP07）Demo 录屏 2 分钟
