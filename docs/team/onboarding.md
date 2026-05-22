# MemoryOS 团队 Onboarding 与协作手册

> **读者**：新加入的开发者、Tech Lead。  
> **配套**：[daily-playbook.md](./daily-playbook.md)（**工具太多时只读这篇**）· [ai-collab-stack.md](../tech/ai-collab-stack.md)
> · [ai-collab-best-practices.md](../tech/ai-collab-best-practices.md) ·
> [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

## 1. 这个项目怎么用（日常）

### 1.1 三条轨道

| 轨道       | 看什么                         | 做什么                           |
| :--------- | :----------------------------- | :------------------------------- |
| **Build**  | `docs/tasks/epics/EP0x-*.md`   | 勾选 Story，写功能代码           |
| **Learn**  | `docs/tasks/learning/L0x-*.md` | 📖 理解 + 🔧 落地勾选            |
| **Collab** | `docs/tasks/epics/EP00-*.md`   | OpenSpec + Superpowers + Harness |

**不要**三条混在一条聊天里；**先 Collab 对齐，再 Build**。

### 1.2 环境（一次性）

```bash
git clone <repo> memoryOS && cd memoryOS

# JS/TS
pnpm install

# Python API（Conda 推荐）
pnpm setup:api

# OpenSpec（Node >= 20）
npm install -g @fission-ai/openspec@latest
openspec init          # 若仓库已有 openspec/，改为 openspec update
```

### 1.3 每天开发

```bash
# 终端 1
pnpm dev:api

# 终端 2
pnpm dev:web

# 或一条命令
pnpm dev:all
```

提交前：

```bash
pnpm lint                    # 前端
pnpm test:api:harness        # API 契约
```

### 1.4 接一个功能的标准流程（单人 / 通用）

| 步骤 | 动作                                                                               |
| :--: | :--------------------------------------------------------------------------------- |
|  1   | 在 `docs/tasks/epics/` 找到本周 Story（如 EP03 Story 3.2）                         |
|  2   | Cursor：`/opsx:propose "ep03-data-storage"`（或更细的 change 名）                  |
|  3   | 自己 + （可选）他人审 `proposal.md` / `design.md` / `tasks.md`                     |
|  4   | Superpowers：**brainstorm**（需求不清时）→ **writing-plans**（细化 tasks）         |
|  5   | 先写 Harness / pytest（红）→ 实现（绿）                                            |
|  6   | 分支开发：`feat/ep03-sqlalchemy`                                                   |
|  7   | PR：贴 [PR 检查表](../tech/ai-collab-best-practices.md#41-单次功能检查表复制到-pr) |
|  8   | 合并后：`/opsx:archive`，勾选 epic + L00/L01                                       |

### 1.5 目录速查

```text
apps/web/          前端
apps/api/          后端 FastAPI
packages/shared/   无 React 共享
packages/ui/       共享 React 组件
docs/tasks/epics/  史诗任务（Build）
openspec/          OpenSpec specs + changes（Collab）
apps/api/tests/harness/   Harness L1+
```

---

## 2. 新同学加入：怎么处理

### 2.1 角色与职责（建议）

| 角色                   | 职责                                                                |
| :--------------------- | :------------------------------------------------------------------ |
| **Tech Lead**          | 维护 epic 优先级、approve OpenSpec proposal、Harness 基线、架构文档 |
| **Owner（按 change）** | 负责一个 `openspec/changes/<name>/` 从 propose 到 archive           |
| **开发者**             | 在 Owner 分支上按 tasks 提交 PR；小修可自任 Owner                   |
| **Reviewer**           | 审 spec 一致性 + 代码 + harness 是否绿                              |

第一版团队可 **一人兼 Lead + Owner**；超过 2 人再严格分 Owner。

### 2.2 入职时间线

#### 第 1 天：能跑起来

- [ ] 读完
      [CONTRIBUTING.md](../../CONTRIBUTING.md)、本文、[ai-collab-stack.md](../tech/ai-collab-stack.md)（30
      min）
- [ ] `pnpm install` + `pnpm setup:api` + `openspec update`
- [ ] 安装 Cursor + Superpowers
- [ ] `pnpm dev:all`，浏览器打开 web，Console
      `fetch('http://localhost:8000/health')`
- [ ] `pnpm test:api:harness` 通过
- [ ] 浏览 `docs/tasks/00-iteration-overview.md` 知道当前在第几周

#### 第 2 天：走通协作链

- [ ] 跟 Lead 过一遍当前 **active change** 列表（`openspec/changes/`）
- [ ] 领一个 **≤ 1 天** 的 task（从 `tasks.md` 勾一条）
- [ ] 用 Superpowers plan 实现该 task，提第一个 PR（哪怕很小）
- [ ] 参加或阅读最近一次 weekly retro（`docs/tasks/weekly-tracker.md`）

#### 第 1 周结束：独立接 Story

- [ ] 能独立 `propose` 一个小 change
- [ ] 能解释 OpenSpec / Superpowers / Harness 各解决什么问题（L00 §4 自测）

### 2.3 权限与仓库

| 事项     | 建议                                                                    |
| :------- | :---------------------------------------------------------------------- |
| Git      | 所有人从 `main` 拉 `feat/*`；禁止直接推 `main`                          |
| OpenSpec | 所有人可 propose；**archive 仅 Owner 或 Lead** 执行，避免 spec 冲突     |
| 密钥     | 每人本地 `.env` / `.env.local`；统一用 `.env.example` 文档              |
| AI 工具  | 统一 Cursor + 项目 rules；Superpowers 流程一致，减少「每人一套 prompt」 |

### 2.4 两人同时做不同功能

```text
开发者 A: change ep03-postgres     → 分支 feat/ep03-postgres
开发者 B: change ep02-chat-ui      → 分支 feat/ep02-chat-ui
```

- **不同 change、不同分支** → 通常无 OpenSpec 冲突。
- 若都改 `apps/api/app/main.py`：先在 design.md 标明模块划分，或
  **串行合并**（A 合完 B rebase）。
- 每日 10 分钟同步：active changes + 是否阻塞。

### 2.5 两人抢同一功能

- 指定 **唯一 Owner**；另一人 pair 或等下一 task。
- **禁止** 两个 PR 改同一 `openspec/changes/<name>/` without 合并文案。

### 2.6 PR 规范（团队版）

**标题**：`feat(api): ep03 add user model`（Conventional Commits）

**描述模板**：

```markdown
## OpenSpec

- Change: `openspec/changes/ep03-data-storage/`
- Tasks: 3.2.1, 3.2.2（已勾选）

## 测试

- [ ] pnpm test:api:harness
- [ ] 手动：\_\_\_\_

## 截图 / 说明

（前端改动时）
```

### 2.7 沟通节奏（推荐）

| 频率    | 内容                                               |
| :------ | :------------------------------------------------- |
| 每日    | active change 名 + 阻塞（可异步文字）              |
| 每周    | 更新 `progress-dashboard.md`、勾选 epic            |
| 每 epic | archive 全部相关 changes，retro 1 篇 `docs/tech/*` |

### 2.8 新人常见问题

| 问题                  | 答案                                                                                  |
| :-------------------- | :------------------------------------------------------------------------------------ |
| 小改要不要 OpenSpec？ | 见 [best-practices §1.1](../tech/ai-collab-best-practices.md#11-什么时候必须-propose) |
| 不会 Python           | 先 `python-getting-started.md`，EP03 边做边学                                         |
| 没有 conda            | `pnpm setup:api` 会建 `.venv`                                                         |
| OpenSpec 命令不存在   | `openspec update`，重启 Cursor                                                        |
| Harness 失败          | 先 `pnpm setup:api` 装 dev 依赖                                                       |

---

## 3. Tech Lead 清单（组队时）

- [ ] 仓库已提交 `openspec/`（或文档要求每人 `init` 后只 `update`）
- [ ] `openspec/config.yaml` 使用
      [openspec-config.example.yaml](../tech/openspec-config.example.yaml) 定制
- [ ] CONTRIBUTING + 本文链接进 README
- [ ] 约定当前迭代 active changes（不超过 **2 个** 并行）
- [ ] PR 模板含三件套检查表（见 best-practices）
- [ ] EP08 前 CI 跑 `pnpm test:api:harness`

---

## 4. 相关链接

| 文档                                                                | 用途             |
| :------------------------------------------------------------------ | :--------------- |
| [ai-collab-best-practices.md](../tech/ai-collab-best-practices.md)  | 最佳实践与反模式 |
| [EP00-ai-collaboration.md](../tasks/epics/EP00-ai-collaboration.md) | Collab 任务勾选  |
| [L00-ai-collab-stack.md](../tasks/learning/L00-ai-collab-stack.md)  | 学习路线         |
| [FE-engineering.md](../tech/FE-engineering.md)                      | 前端工程         |
| [BE-engineering.md](../tech/BE-engineering.md)                      | 后端工程         |
