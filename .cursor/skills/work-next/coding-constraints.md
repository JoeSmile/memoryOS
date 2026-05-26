# 实现阶段 checklist

- **代码五条**：`docs/tech/code-quality.md` §1（写码质量）  
- **本文**：task 粒度与流程（与五条不重复）

## Propose（`tasks.md`）

- 模板：[openspec-tasks-template.md](../../../docs/tech/openspec-tasks-template.md)  
- 每条：预计 **≤3 文件**、**层**、是否先写 harness  

## 每个 task

- [ ] 只做 **当前一条**；对照 tasks 里的预计文件/层  
- [ ] 读同目录现有文件 1–2 个；遵守代码五条  
- [ ] API：先/同步 harness L1，再实现  

## 完成后

输出 **Review 摘要**（层、文件列表、测试结果）→ **停止**（除非用户说「继续」）。

用户允许提交时：**checkpoint commit**（仅本 task；message 含 change/task id）。

合并前：`pnpm test:api:harness`（及 unit）。
