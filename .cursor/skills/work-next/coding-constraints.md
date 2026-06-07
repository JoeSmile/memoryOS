# 实现阶段 checklist

- **代码五条**：`docs/tech/code-quality.md` §1（写码质量）  
- **本文**：task 粒度与流程（与五条不重复）

## Propose（`tasks.md`）

- 模板：[openspec-tasks-template.md](../../../docs/tech/openspec-tasks-template.md)（**含 §0 人审门禁**）  
- 每条：预计 **≤3 文件**、**层**、是否先写 harness  
- propose 结束：**Task Review Pack → 停止**，不写码

## Task Review Gate（apply 前）

- [ ] `tasks.md` §0 **`Tasks reviewed by human`** 已勾选，或用户本轮明确批准（见 [task-review-gate.md](task-review-gate.md)）  
- [ ] 核对：前后端 scope 成对、Harness 覆盖 design scenarios

## 每个 task（开始前）

- [ ] `pnpm branch:task <change> <task-id>`（或 `branch:change` 后手动切分支）— 见 [branch-strategy.md](../../../docs/tech/branch-strategy.md)  
- [ ] 只做 **当前一条**；对照 tasks 里的预计文件/层  
- [ ] 读同目录现有文件 1–2 个；遵守代码五条  
- [ ] API：先/同步 harness L1，再实现  

## 完成后

输出 **Review 摘要**（层、文件列表、测试结果）→ **停止**（除非用户说「继续」）。

## Commit 前 Code Review Gate（HARD）

**任何 `git commit` 之前**必须先做 code review，**禁止**实现完直接提交。

1. **Verify** 通过（`pnpm lint` / `pnpm build` / `pnpm test:api:harness` 等，按改动范围）。
2. **Code review** — `requesting-code-review` skill 或 **code-reviewer** subagent；对照 OpenSpec task / design。
3. 输出结构化结论：**Strengths / Critical / Important / Minor / Verdict**。
4. **Critical / Important** 必须修完并 re-verify、re-review。
5. **仅当用户明确说「commit」**（或「提交」）且 Verdict 为 merge-ready → 再 `git commit`（本 task 范围；message 含 change/task id）。

用户未要求 commit 时：review 后停止，等待确认。

合并前：再次 `pnpm test:api:harness`（及 unit）。
