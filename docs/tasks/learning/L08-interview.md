# L08 — 打磨与面试（第 10-12 周）

**对应史诗**：EP10

---

## 1. 技术文档复盘

- [ ] 📖 检查 `docs/tech/*` 是否覆盖：FE/BE、LangGraph、双 RAG、Agent、记忆、部署
- [ ] 🔧 `docs/tech/challenges.md`：≥5 个难点，每个含现象→根因→方案→数据
- [ ] 🔧 架构图与代码目录可一一对应

---

## 2. 高频面试题（需结合本项目答）

### 架构选型

- [ ] 📖 为什么 Monorepo？为什么 FastAPI + Next 分离又协作？
- [ ] 📖 为什么 LangGraph 而不是裸调 OpenAI SDK？
- [ ] 📖 LangChain vs LlamaIndex 双 RAG 各解决什么？
- [ ] 📖 LangSmith 在线上排障中的角色？

### RAG（建议自建 `docs/interview/rag.md`）

- [ ] 📖 向量检索原理；TopK、阈值、重排
- [ ] 📖 幻觉原因与治理；引用溯源实现
- [ ] 📖 切块策略怎么选；PDF 难点
- [ ] 📖 评测：命中率、faithfulness（概念即可）

### Agent

- [ ] 📖 ReAct 流程；如何防止死循环
- [ ] 📖 工具安全：SQL、搜索、检索权限
- [ ] 📖 Function Calling 失败重试策略

### 流式与前端

- [ ] 📖 SSE vs WebSocket；Nginx 配置要点
- [ ] 📖 RSC + Client 分工；聊天为何大量 Client

### 工程化

- [ ] 📖 Docker standalone；Compose 组网
- [ ] 📖 JWT、限流、Token 成本
- [ ] 📖 你如何保证可回滚发布？

### 实战开放题

- [ ] 📖 如果召回率只有 30% 你怎么调？
- [ ] 📖 如果线上 token 费用一夜涨 10 倍你怎么查？

---

## 3. 项目话术（STAR）

- [ ] 🔧 简历 bullet：业务结果 + 技术关键词（LangGraph/LlamaIndex/pgvector）
- [ ] 🔧 3 分钟版：背景→架构→难点→成果
- [ ] 🔧 5 分钟版：加 demo 路径 + 指标（延迟、成本、准确率 qualitative）

**示例结构**（勿照抄，填真实数据）：

> Situation：AI 知识库 + 对话平台  
> Task：流式体验、可观测、成本可控  
> Action：LangGraph 编排、双 RAG、LangSmith、pgvector…  
> Result：首 token XX ms、部署上线、XX 功能闭环

---

## 4. 演示脚本（8–10 分钟）

1. 登录 / 会话列表  
2. 流式对话 + 停止生成  
3. 上传文档 → 知识库问答 + 引用  
4. 切换 Agent → 工具调用时间线  
5. LangSmith 打开一条 trace  
6. （可选）部署地址、架构图一页  

- [ ] 🔧 录屏 + 口述稿对照练 3 遍

---

## 5. 模拟面试

- [ ] 第 1 轮：基础 + RAG（自问自答 45min）
- [ ] 第 2 轮：Agent + 工程化
- [ ] 第 3 轮：系统设计「设计一个企业内部知识库问答」
- [ ] 每轮记录薄弱点，回炉对应 `L01`–`L07`

---

## 6. 易踩「面试坑」（答错会减分）

| 误区 | 更好答法 |
|:-----|:---------|
| 「我们用了 AI」无细节 | 具体到 Graph、检索、流式 |
| 把 LangChain 当万能 | 说清快链路与自研链路分工 |
| 否认幻觉 | 承认 + 说引用与拒答 |
| 只说 SSE 快不说 Nginx | 带全链路 |
| 没做过生产 | 诚实 + Compose/监控/限流已设计 |

---

## 阶段自测

- [ ] 无提示白板：用户提问 → 全链路  
- [ ] 任选 epic 讲满 5 分钟  
- [ ] `docs/interview/` 至少 20 题有标准答要点
