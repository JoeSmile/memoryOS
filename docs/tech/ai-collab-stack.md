# AI 协作工程栈：Superpowers · OpenSpec · Harness

> MemoryOS 在「写业务代码」之外的**第三条轨道**：**协作轨（Collab）**——与 Build（史诗任务）、Learn（L01–L08）并列。  
> 目标：个人项目可复用，**组建 / 带团队**时可直接升格为团队规范。

---

## 1. 三者分工（一张表记住）

| 工具            | 解决什么问题                        | 类比（传统团队）               | MemoryOS 落点                                        |
| :-------------- | :---------------------------------- | :----------------------------- | :--------------------------------------------------- |
| **OpenSpec**    | 建什么、改什么，**先对齐再写码**    | PRD + 技术方案 + 任务拆解      | `openspec/` 变更文件夹、与 `docs/tasks/epics` 互补   |
| **Superpowers** | AI **怎么写**才不乱写、可审查       | 研发流程 + Code Review 纪律    | Cursor 技能 / 插件：brainstorm → plan → TDD → review |
| **Harness**     | Agent / LLM 功能 **测得住、可回归** | 测试框架 + 契约测试 + 灰度指标 | `apps/api/tests/harness/`、EP02+ 对话与工具评测      |

```text
OpenSpec（What）  →  Superpowers（How）  →  Harness（Prove it works）
     ↑                      ↑                        ↑
  人+AI 对齐需求          受控实现与评审              非确定性系统可验证
```

---

## 2. 与现有 `docs/tasks` 的关系

| 文档                                                               | 角色                                               |
| :----------------------------------------------------------------- | :------------------------------------------------- |
| `docs/tasks/epics/*.md`                                            | **产品/架构级** 史诗与 Story（12 周路线图）        |
| `openspec/changes/*`                                               | **单次变更级** proposal / design / tasks（可归档） |
| `docs/tech/ai-collab-stack.md`                                     | 本文：三者如何配合、团队怎么带                     |
| [L00-ai-collab-stack.md](../tasks/learning/L00-ai-collab-stack.md) | 学习勾选 + 面试/带团队话术                         |

**推荐节奏**（每个 Epic 或 Story 块）：

1. 在 `epics/EP0x` 勾选本周 Build 目标
2. **`/opsx:propose`** 为本变更建 OpenSpec 文件夹（proposal / design / tasks）
3. **Task Review Gate（必做）** — 人读并改 `tasks.md`，勾选 §0 或说「tasks 人审通过」；**AI 不得跳过**
4. **`pnpm branch:task <change> [id]`** — 当前 task 工作分支（§0 人审后）
5. **`/work-next <change>`** 或 **`/opsx:apply`** — 按 tasks 逐条实现（一次一条）
5. 用 **Superpowers** TDD / harness（大功能可 skip brainstorm，不 skip L1）
6. 合并前 **Review** + `pnpm test:api:harness`
7. **`/opsx:archive`** 把 spec 并回主规格

---

## 3. OpenSpec

### 安装（仓库根目录，Node ≥ 20）

```bash
npm install -g @fission-ai/openspec@latest
cd memoryOS
openspec init
openspec update    # 刷新 Cursor 等工具的 slash 命令
```

### 常用命令（在 Cursor 对话里）

| 命令                            | 用途                                                        |
| :------------------------------ | :---------------------------------------------------------- |
| `/opsx:propose "ep03-postgres"` | 创建 `openspec/changes/...`：proposal、specs、design、tasks |
| `/opsx:apply`                   | 按 tasks.md 实现                                            |
| `/opsx:archive`                 | 归档变更，更新主 spec                                       |

### MemoryOS 约定

- **史诗级**计划仍写在 `docs/tasks/epics/`（不变）。
- **单次 PR 级**改动用 OpenSpec change（例如
  `ep03-data-storage`、`ep02-chat-sse`）。
- `openspec/config.yaml` 可写入：Monorepo 结构、Python 在
  `apps/api`、pnpm 根脚本、BE/FE 工程文档链接。

官方文档：<https://openspec.dev/> ·
[GitHub Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)

---

## 4. Superpowers

### 是什么

[obra/superpowers](https://github.com/obra/superpowers)：**面向 AI 编程助手的技能框架 + 开发方法论**，强调先澄清、再计划、再小步实现与评审，而不是直接生成大段代码。

### 典型流程

```text
brainstorm → 写计划（小任务）→ TDD（红绿重构）→ code review → 合并
（可选）git worktree 隔离、subagent 分任务
```

### Cursor 接入

1. Cursor **Plugin Marketplace**
   搜索安装 Superpowers（或按官方 README 配置 skills）。
2. 大功能开发前显式触发：**brainstorming** / **writing-plans** 类技能。
3. 与 OpenSpec 配合：**tasks 人审通过（§0 勾选）后**再 `/opsx:apply` 或 `/work-next` 写码。

### 带团队时

| 角色      | 用法                                                |
| :-------- | :-------------------------------------------------- |
| Tech Lead | 要求「无 plan 不开工」；PR 描述链接 OpenSpec change |
| 开发      | 单任务粒度 ≤ 1 文件或 ≤ 50 行；必须带测试意图       |
| Reviewer  | 对照 Superpowers review 清单 + OpenSpec tasks 勾选  |

---

## 5. Harness（Agent Harness）

### 是什么

**Harness**
不是 LangGraph 本身，而是包住 Agent 的**运行时与验证层**：上下文、工具权限、停止条件、失败处理、**分层测试**。

参考概念：[Harness Engineering — Agent testing](https://harness-engineering.ai/blog/ai-agent-testing-how-to-build-reliable-production-ready-agent-systems/)

### 三层测试（MemoryOS 采用）

| 层              | 测什么                                            | 何时加                    |
| :-------------- | :------------------------------------------------ | :------------------------ |
| **L1 确定性**   | 路由存在、JSON schema、工具名/参数格式、HTTP 状态 | EP01 起（health、错误体） |
| **L2 模型评分** | 回答是否满足 rubric（另调 LLM 判分）              | EP02 对话、EP04 RAG       |
| **L3 统计**     | 同 prompt 多轮 pass rate                          | EP05 Agent、EP09 优化     |

### 仓库落点（随 EP00 Story 0.5 初始化）

```
apps/api/tests/
├── unit/           # 普通 pytest
└── harness/        # Agent / API 契约与评测
    ├── fixtures/
    ├── test_health_contract.py
    └── README.md
```

EP02 起为 `chat`、`rag`、`agent` 各加 `cases/*.yaml` + 运行脚本。

---

## 6. 团队 / 带队 playbook（精简版）

### 入职第一天

1. 读 `CONTRIBUTING.md` + 本文 + `FE-engineering` / `BE-engineering`
2. `pnpm install` + `pnpm setup:api`
3. `openspec init`（若仓库已提交 `openspec/`，则 `openspec update`）
4. 安装 Superpowers（Cursor）
5. 跑通 `pytest apps/api/tests/harness/test_health_contract.py`

### 每个功能的标准 Definition of Done

- [ ] `epics/EP0x` 或 OpenSpec `tasks.md` 项已勾选
- [ ] OpenSpec change 已 propose → apply → archive（或 PR 链接 change 目录）
- [ ] 实现过程有 plan（Superpowers 或 OpenSpec tasks）
- [ ] Harness L1 通过；AI 功能另附 L2/L3 说明
- [ ] `docs/tech/` 或 `docs/database.md` 有简短沉淀

### 站会三问（带团队版）

1. 当前 OpenSpec change 名？卡在哪条 task？
2. 有没有未经评审就扩 scope？（回到 `/opsx:propose`）
3. Harness 上次绿了吗？回归失败先修还是先合？

---

## 7. 与 12 周史诗的映射

| 周 / 史诗     | OpenSpec              | Superpowers      | Harness             |
| :------------ | :-------------------- | :--------------- | :------------------ |
| 1–2 EP01+EP03 | `ep03-data-storage`   | plan + 小步 CRUD | health / 错误体契约 |
| 3 EP02        | `ep02-streaming-chat` | TDD 流式切片     | SSE chunk schema    |
| 4–5 EP04      | `ep04-rag-*`          | 双栈分 change    | 检索命中率 L2       |
| 6 EP05        | `ep05-agent-tools`    | subagent 分工具  | 工具选择 L1+L3      |
| 8 EP08        | `ep08-deploy`         | 发布 checklist   | smoke + CI          |
| 10–12 EP10    | 归档全部 change       | 面试 retro 素材  | 演示评测报告        |

---

## 8. 文档索引

| 文档                                                           | 内容                                      |
| :------------------------------------------------------------- | :---------------------------------------- |
| [ai-collab-best-practices.md](./ai-collab-best-practices.md)   | **最佳实践**、反模式、PR 检查表、多人协作 |
| [../team/onboarding.md](../team/onboarding.md)                 | **本项目怎么用**、新人第 1–7 天、组队职责 |
| [openspec-config.example.yaml](./openspec-config.example.yaml) | `openspec/config.yaml` 模板               |

---

## 相关

- 任务：[EP00-ai-collaboration.md](../tasks/epics/EP00-ai-collaboration.md)
- 学习：[L00-ai-collab-stack.md](../tasks/learning/L00-ai-collab-stack.md)
