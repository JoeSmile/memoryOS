# L07 — 优化、安全、成本（第 9 周）

**对应史诗**：EP09

---

## 1. Prompt 注入与安全

### 学什么

- [ ] 📖 攻击类型：角色劫持、指令覆盖、间接注入（RAG 文档内藏指令）
- [ ] 📖 防护：system 边界、输入长度限制、敏感词、输出过滤（按需）
- [ ] 📖 RAG：检索内容当不可信输入处理
- [ ] 🔧 中间件 + prompt 模板加固
- [ ] 📖 项目落地：[`docs/tech/chat-security.md`](../../tech/chat-security.md)（纵深防御 + 包对比 + 试用计划）

### 面试常问

- 什么是 indirect prompt injection？知识库 PDF 里写「忽略上文」怎么办？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 把用户原文拼进 system | 易被覆盖 | 严格分隔 role |
| 无上传审计 | 恶意文件 | 鉴权 + 扫描（可选） |
| 日志打全量 prompt | 隐私泄露 | 脱敏 |

---

## 2. 性能与首 Token

### 学什么

- [ ] 📖 延迟构成：网络、排队、prefill、decode
- [ ] 📖 缩短 prefill：减历史、减检索、更快模型路由
- [ ] 📖 缓存：相同问题 hash（谨慎 TTL）、Embedding 缓存
- [ ] 📖 DB：索引、连接池、慢查询日志

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 冷启动大模型连接 | 首包慢 | 预热或保持连接 |
| 同步 embed 在请求里 | 阻塞 | 预计算或异步 |

---

## 3. Token 与成本管控

### 学什么

- [ ] 📖 记录：prompt_tokens、completion_tokens、按 user/day 聚合
- [ ] 📖 配额：日限额、会话上限、超限 429 友好提示
- [ ] 📖 模型路由：便宜模型做摘要，贵模型做最终回答（可选）
- [ ] 🔧 用量表 + 简单看板（可选）

### 面试常问

- 企业如何控制 LLM 成本？Token 统计放哪一层？

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 只记次数不记 token | 账单对不上 | 用 API 返回 usage |
| Agent 无步数上限 | 一夜烧光额度 | 配额 + 步数 |

---

## 4. 限流与审计

- [ ] 📖 项目落地：[`docs/tech/rate-limit-audit.md`](../../tech/rate-limit-audit.md)（限流逻辑、审计、企业差距）
- [ ] 📖 Redis 滑动窗口：IP + userId
- [ ] 📖 登录、发消息、demo-turn 单独限流；与 Token 配额（42901 vs 42902）分工
- [ ] 📖 审计：敏感操作写 `audit_log`，非全量 chat
- [ ] 🔧 中间件 + 管理查询接口（可选）

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 限流 key 只用 IP | 误伤 NAT | 登录后用 userId |
| 无 burst | 正常用户被拦 | 令牌桶 |

---

## 5. 降级矩阵

| 组件 | 降级策略 |
|:-----|:---------|
| LLM 主模型 | 切备用模型 / 返回维护提示 |
| 向量检索 | 关键词检索 / 仅 LLM |
| Redis | 直连 DB，性能降 |
| LangSmith | 关 tracing，核心服务不停 |

- [ ] 🔧 文档化 + 1 次演练（关 Redis 或 mock 500）

---

## 6. 架构图与 LangSmith 生产

- [ ] 🔧 `docs/architecture/`：系统总览、RAG、Agent 三张图
- [ ] 📖 生产 tracing 采样率；错误 100% 采样

---

## 7. Agent 过程态 UI（Story 9.8）

> EP05 只有 **结果态**（RAG chips、ToolTimeline）；retrieve / tool 执行时前端常静默。

### 学什么

- [ ] 📖 流式 UX 空窗：用户消息发出 → 首个 SSE 帧之间的感知延迟
- [ ] 📖 过程 vs 结果：phase 事件（retrieve / model / tool）与 chips / timeline 分工
- [ ] 📖 AI SDK `submitted` vs `streaming`；何时显示 Thinking 占位
- [ ] 🔧 L1 纯前端占位 → L2 SSE `phase` → L3 pending polish

### 实战易踩坑

| 坑 | 现象 | 规避 |
|:---|:-----|:-----|
| 等首个 token 才建助手气泡 | 长时间空白 | `submitted` 即显示 skeleton |
| retrieve 无 SSE | 检索 1–2s 无反馈 | runner 发 `phase:retrieve` |
| tool 结果到了才渲染 timeline | Tavily 期间像卡死 | `tool_call` 即 pending 行 |
| phase 与 EP05 chips 重复 | UI 噪音 | phase 简短条；chips 仍表检索命中 |

### 面试常问

- 如何让用户感知 Agent「正在干活」而不泄露完整 chain-of-thought？

## 阶段自测

- [ ] 用真实 trace 讲一次 RAG 慢在哪个 span  
- [ ] 列举 5 条安全/成本相关踩坑及本项目对策
