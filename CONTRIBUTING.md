# 贡献指南

感谢你对 MemoryOS 的关注！欢迎通过 Issue 与 Pull Request 参与共建。

## 开发环境

| 工具 | 版本要求 |
|:-----|:---------|
| Node.js | >= 20 |
| pnpm | 9.x（见根目录 `packageManager`） |
| Python | >= 3.11 |
| Docker | 可选，EP03 起用于本地数据库 |

```bash
git clone https://github.com/<your-org>/memoryOS.git
cd memoryOS
pnpm install
pnpm setup:api    # 后端 Python
```

## AI 协作栈（OpenSpec · Superpowers · Harness）

参与功能开发前请阅读：

- [ai-collab-stack.md](./docs/tech/ai-collab-stack.md) — 概念与安装  
- [ai-collab-best-practices.md](./docs/tech/ai-collab-best-practices.md) — **最佳实践（必读）**  
- [team/onboarding.md](./docs/team/onboarding.md) — **日常用法与新人 onboarding**

| 工具 | 贡献者需知 |
|:-----|:-----------|
| **OpenSpec** | 较大功能先 `openspec init`（若仓库已有则 `openspec update`），用 change 文件夹记录 proposal / tasks |
| **Superpowers** | Cursor 建议先 plan 再实现；PR 避免单次超大 diff |
| **Harness** | API 变更需通过 `apps/api/tests/harness/`；合并前 `pnpm test:api:harness` |
| **代码质量** | [code-quality.md](./docs/tech/code-quality.md) — 分层、小步 diff、review 摘要 |
| **PR** | 填写 [PR 模板](.github/PULL_REQUEST_TEMPLATE.md) 中的 Review 摘要 |
| **CI** | API 改动依赖 `api-harness` workflow（见 Actions） |

任务与学习：[EP00](./docs/tasks/epics/EP00-ai-collaboration.md) · [L00](./docs/tasks/learning/L00-ai-collab-stack.md) · Cursor **`work-next`** skill

## 分支规范

| 分支 | 用途 |
|:-----|:-----|
| `main` | 稳定可发布分支 |
| `feat/<name>` | 新功能 |
| `fix/<name>` | Bug 修复 |
| `docs/<name>` | 文档更新 |
| `chore/<name>` | 工程化、依赖升级 |

从 `main` 拉取最新代码后创建功能分支，合并前请 rebase 保持提交历史清晰。

### OpenSpec 对齐分支（推荐）

与 `openspec/changes/<name>/tasks.md` 及 `/work-next` 配套，详见 [branch-strategy.md](./docs/tech/branch-strategy.md)。

| 分支 | 何时 | 示例 |
|:-----|:-----|:-----|
| `feat/<change>` | §0 人审通过后、change 第一个 task 前 | `feat/ep03-db-optimize` |
| `feat/<change>-t<major>-<minor>-<slug>` | 每个 task 开始前 | `feat/ep03-db-optimize-t2-1-harness` |

```bash
pnpm branch:change ep03-db-optimize      # 集成分支
pnpm branch:task ep03-db-optimize 2.1    # 当前 task 工作分支
pnpm branch:task ep03-db-optimize        # 自动选第一条未勾选 task
```

**不要**在 propose 完成、tasks 未人审时建分支写码。Task 分支合并到 `feat/<change>`，change 归档前再 PR 到 `main`。

## 提交规范（Conventional Commits）

```
<type>(<scope>): <subject>

[optional body]
```

| type | 说明 |
|:-----|:-----|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档 |
| `style` | 格式（不影响逻辑） |
| `refactor` | 重构 |
| `test` | 测试 |
| `chore` | 构建 / 工具链 |

示例：

```
feat(web): add chat message streaming UI
fix(api): handle SSE disconnect cleanup
docs: update README quick start
```

## 代码规范

### 全仓库通用（前端 + 后端）

- **Git 分支**：统一使用上文「分支规范」（`feat/*`、`fix/*` 等），前后端不另搞一套。
- **提交信息**：统一 **Conventional Commits**，通过 `scope` 区分子项目：
  - 前端：`feat(web): ...`、`fix(web): ...`
  - 后端：`feat(api): ...`、`fix(api): ...`
  - 公共：`chore: ...`、`docs: ...`、`feat(shared): ...`（Monorepo 包）
- **敏感信息**：禁止提交 `.env`、API Key、数据库文件；仅提交 `.env.example`。
- **PR**：合并前自测；前端 `pnpm lint`，后端（EP01.4 后）`ruff check` / `mypy`（待配置）。

### 前端（`apps/web`、`packages/*`）

- ESLint：共享规则见根目录 `eslint.shared.mjs`（`apps/web` 额外含 Next 规则）。
- Prettier：引号、分号等**只由 Prettier 管**，ESLint 不配置 `quotes`。
- 命名：组件 PascalCase，Hooks / 函数 camelCase。

### 后端（`apps/api`）

- Python **4 空格**缩进（与根目录 `.editorconfig` 一致）。
- 分层：**路由 → Service → Repository**，业务逻辑不写在路由函数体内。
- 提交 scope 使用 `api`；分支策略与前端相同。
- 详细工程约定见 `docs/tech/BE-engineering.md`（待编写，EP01.4 / EP03）。

## Pull Request 流程

1. `tasks.md` §0 人审通过 → `pnpm branch:change <name>`（可选）→ `pnpm branch:task <name> [task-id]`
2. 较大功能先有 OpenSpec change（见 best-practices）
3. 完成改动：`pnpm lint` + `pnpm test:api:harness`（API 改动时）
4. PR 描述使用下方模板（或 GitHub 自动模板）
5. Review 后合并；**Owner** 执行 `/opsx:archive` 并勾选 epic tasks

### PR 描述模板

```markdown
## OpenSpec
- Change: `openspec/changes/____/`
- Tasks: （已勾选的编号）

## Superpowers / 实现说明
- Plan 摘要或链接 tasks.md

## 测试
- [ ] pnpm lint
- [ ] pnpm test:api:harness
- [ ] 手动：____

## 关联
- Epic: EP0x Story x.x
```

## 报告问题

提交 Issue 时请包含：

- 复现步骤
- 期望行为 vs 实际行为
- 环境信息（OS、Node/Python 版本、相关配置）

如有疑问，欢迎在 Issue 中讨论。
