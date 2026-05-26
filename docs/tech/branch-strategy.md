# OpenSpec 分支策略

> 与 [CONTRIBUTING.md](../../CONTRIBUTING.md)、`/work-next`、Task Review Gate 配套。  
> 自动化：`pnpm branch:change` · `pnpm branch:task`

---

## 两层分支（默认）

```text
main
 └── feat/<change>                 # 整个 OpenSpec change 的集成分支
      └── feat/<change>-tX-Y-slug # 单个 task 的工作分支
```

| 层级 | 何时创建 | 命名 | 合并到 |
|:-----|:---------|:-----|:-------|
| **Change** | `tasks.md` §0 人审通过后、做该 change **第一个** task 前 | `feat/ep03-db-optimize` | 最终 PR → `main` |
| **Task** | 每个 task 开干前（`/work-next` 声明 X.Y 时） | `feat/ep03-db-optimize-t2-1-harness` | `feat/<change>`（推荐）或单人直 PR `main` |

---

## 命名规则

```text
feat/<change>
feat/<change>-t<major>-<minor>-<slug>
```

- `<change>`：与 `openspec/changes/<name>/` 一致（kebab-case）
- `<major>-<minor>`：对应 `tasks.md` 中的 `2.1`
- `<slug>`：从 task 描述提取 2～3 个英文词（脚本自动生成）

示例：

| Task 描述 | 分支 |
|:----------|:-----|
| `2.1 Harness 扩展…` | `feat/ep03-db-optimize-t2-1-harness` |
| `1.1 Alembic 002 复合索引` | `feat/ep03-db-optimize-t1-1-alembic` |

---

## 与协作流程的衔接

```text
/opsx:propose
    → Task Review Gate（人审 tasks §0）
    → pnpm branch:change <name>      # 集成分支
    → pnpm branch:task <name> [id] # 当前 task 分支
    → 实现一条 task → Verify → checkpoint commit
    → PR → feat/<change> 或 main
    → 下一 task：再 branch:task …
    → archive 后 feat/<change> → main
```

**禁止**：propose 同会话、§0 未勾选时建分支写业务代码（见 [task-review-gate](../../.cursor/skills/work-next/task-review-gate.md)）。

---

## 命令

在仓库根目录：

```bash
# 集成分支（从 main 拉出）
pnpm branch:change ep03-db-optimize

# 指定 task 的工作分支（从 feat/<change> 拉出；若无则先建 change 分支）
pnpm branch:task ep03-db-optimize 2.1

# 自动选第一条未勾选 task（跳过 §0）
pnpm branch:task ep03-db-optimize

# 仅打印将创建的分支名
pnpm branch:task ep03-db-optimize 2.1 --dry-run
```

实现：`scripts/branch-task.sh`。

---

## 模式选择

| 模式 | 适用 | 说明 |
|:-----|:-----|:-----|
| **A** 仅 change | 单人、change 很小 | 只 `feat/<change>`，task 用 commit 区分 |
| **B** change + task（**默认**） | 团队 / 要对齐 OpenSpec task | 小 PR、好 bisect |
| **C** 仅 task → main | 单人、不想维护集成分支 | 每 task 一个 `feat/<change>-t…` 直 PR main |

---

## Agent（work-next）约定

开始 **§4 Implement** 前：

1. 确认 §0 已勾选或用户已批准 tasks  
2. 运行 `pnpm branch:task <change> <task-id>`（或 `--dry-run` 展示分支名）  
3. 在回复中写明当前分支与 task id  
4. 再写业务代码  

用户说 `/work-next ep03-db-optimize 2.1` 时，Agent 应解析 task id 并建对应分支。

---

## 并行与 rebase

- 不同 **change** 的分支可并行（`feat/ep03-db-optimize` vs `feat/ep02-chat-sse`）。  
- 同 change 多人：共用 `feat/<change>`，各自 `feat/<change>-t…` → PR 进集成分支。  
- Task 分支合并前：`git rebase feat/<change>`（或 `main`）。
