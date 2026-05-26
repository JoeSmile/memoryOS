# 可审查代码规范（MemoryOS）

> **代码五条**（结构与可读性）+ **协作流程**（小步、可 review）分工明确，互不替代。  
> 流程执行：[work-next](../../.cursor/skills/work-next/SKILL.md) · 概念：[ai-collab-stack.md](./ai-collab-stack.md)

---

## 1. 代码五条（写每一行时遵守）

1. **遵循当前项目目录与 lint 规范**  
   - 后端：[BE-engineering.md](./BE-engineering.md)（Router → Service → Repository）  
   - 前端：[FE-engineering.md](./FE-engineering.md)（App Router、ESLint、Prettier）  

2. **逻辑拆分：一个函数只做一件事**  
   - 禁止巨型函数（有效逻辑建议 ≤40 行）；handler 只做参数解析 → 调 Service → 返回 envelope。  

3. **关键分支与异常必须注释**  
   - 写清 **为什么**（业务规则、并发、降级），不是复述代码。  

4. **不引入未使用依赖、不写冗余逻辑**  
   - 禁止与当前 task 无关的改动（「顺手重构」另开 change）。  

5. **复杂逻辑拆成独立函数 / Hook / 工具模块**  
   - 后端：`services/`、`cache/`、`repositories/`；前端：`hooks/`、`lib/`；便于 unit / harness 覆盖。  

### 分层（五条 #1 的落地）

**后端**

```text
api/v1/ → services/ → repositories/ | cache/
schemas/ · models/ · core/
```

Router 无 SQL；Repository 无 Redis；Service 不返回裸 dict。

**前端（EP02 起）**：`app/` → `components/` · `hooks/` · `lib/` · `stores/`

---

## 2. 协作流程（小步 review — 由 work-next 执行）

下列内容 **不在此重复**，统一由 skill 与模板保证，避免与五条打架：

| 做法 | 载体 |
|:-----|:-----|
| 一次一个 OpenSpec task，做完 **Review 摘要** 并停止 | [work-next/SKILL.md](../../.cursor/skills/work-next/SKILL.md) §4 |
| 单 task ≤3 文件 / ~150 行；单 PR ≤5 文件 | [coding-constraints.md](../../.cursor/skills/work-next/coding-constraints.md) |
| Harness 先行（API）、checkpoint commit、feat 分支 | work-next §3、§7 |
| tasks 写「预计文件 / 层」 | [openspec-tasks-template.md](./openspec-tasks-template.md) |
| PR 自检与摘要 | [.github/PULL_REQUEST_TEMPLATE.md](../../.github/PULL_REQUEST_TEMPLATE.md) |
| CI harness 绿灯 | [.github/workflows/api-harness.yml](../../.github/workflows/api-harness.yml) |

**与五条的关系**：流程控制 **何时停、改多少文件**；五条控制 **怎么写每一文件里的代码**。  
TDD 会先写测试文件，仍计在「≤3 文件 / task」内（propose 时拆 task）。

---

## 3. Reviewer 快速扫 diff

1. [PR 模板](../../.github/PULL_REQUEST_TEMPLATE.md) 中的 **Review 摘要** 与文件数  
2. 是否落在正确 **层**（§1）  
3. **Harness / unit** 与行为一致  
4. 关键分支是否有 **注释**（五条 #3）  
5. 无无关重构、无未使用依赖（五条 #4）  

---

## 4. 相关文档

- [BE-engineering.md](./BE-engineering.md) · [FE-engineering.md](./FE-engineering.md)  
- [ai-collab-best-practices.md](./ai-collab-best-practices.md)  
- [work-next/coding-constraints.md](../../.cursor/skills/work-next/coding-constraints.md)
