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
```

## 分支规范

| 分支 | 用途 |
|:-----|:-----|
| `main` | 稳定可发布分支 |
| `feat/<name>` | 新功能 |
| `fix/<name>` | Bug 修复 |
| `docs/<name>` | 文档更新 |
| `chore/<name>` | 工程化、依赖升级 |

从 `main` 拉取最新代码后创建功能分支，合并前请 rebase 保持提交历史清晰。

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

- **前端**：遵循各包 ESLint / Prettier 配置；组件与 Hooks 命名使用 PascalCase / camelCase
- **后端**：Python 4 空格缩进；路由 → Service → Repository 分层
- **通用**：不提交 `.env`、密钥、本地数据库数据；敏感配置使用 `.env.example` 模板

## Pull Request 流程

1. Fork 仓库并创建功能分支
2. 完成改动，确保 `pnpm lint`（如已配置）通过
3. 填写 PR 描述：背景、改动点、测试方式
4. 等待 Review 后合并

## 报告问题

提交 Issue 时请包含：

- 复现步骤
- 期望行为 vs 实际行为
- 环境信息（OS、Node/Python 版本、相关配置）

如有疑问，欢迎在 Issue 中讨论。
