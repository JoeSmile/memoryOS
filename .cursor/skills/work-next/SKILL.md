---
name: work-next
description: >-
  MemoryOS Collab workflow: OpenSpec align → Superpowers discipline (when needed)
  → Harness verify → review → archive. Use when the user says work-next, work
  <change>, 开始 Story, 按协作流程开发, or starts a new epic/story/API/Agent task.
---

# Work Next — MemoryOS Collab 开发流程

统一编排 **OpenSpec（What）→ Superpowers（How）→ Harness（Prove）**。

**主文档**：[docs/tech/ai-collab-stack.md](../../docs/tech/ai-collab-stack.md)  
**细节表**（何时跳过 Superpowers、Harness 分层）：[reference.md](reference.md)  
**代码五条**：[code-quality.md](../../docs/tech/code-quality.md) §1 · **流程 checklist**：[coding-constraints.md](coding-constraints.md)

---

## 输入

用户应提供 **至少一项**（缺则询问）：

| 输入 | 示例 |
|:-----|:-----|
| OpenSpec change 名 | `ep03-jwt`、`ep02-chat-sse` |
| Epic + Story | `EP03 Story 3.4` |
| 简短描述 | 「JWT 登录与 Bearer 中间件」 |

解析后 **宣布**：`Working on: <change-or-story>`。

---

## 流程总览

```text
0 Orient → 1 OpenSpec propose → 1.5 Task Review Gate（人审，HARD STOP）
→ 1.6 Branch（change / task 分支）→ 2 Superpowers? → 3 Harness plan → 4 Implement
→ 5 Verify → 6 Review → 7 Finish (commit/merge/archive)
```

**门禁**：`tasks.md` 生成后 **必须先等人审**（见 [task-review-gate.md](task-review-gate.md)）。  
AI **禁止** 在同一会话 propose 后直接写业务代码，除非用户明确说「tasks 人审通过」/「继续实现」。

每阶段结束在回复中简短汇报进度（change 名、task N/M、harness 结果）。

---

## 0. Orient（必做）

1. 读 `docs/tasks/epics/EP0x-*.md` 对应 Story 勾选项。
2. `openspec list --json` — 是否已有 active change？
3. 读相关 `openspec/specs/` 或已归档 change（若 brownfield）。

---

## 1. OpenSpec（必做，除纯 docs  typo）

**无 active change** → 读 [.cursor/skills/openspec-propose/SKILL.md](../openspec-propose/SKILL.md)，执行 `/opsx:propose "<name>"`，产出 proposal / design / specs / tasks（tasks 用 [openspec-tasks-template.md](../../docs/tech/openspec-tasks-template.md)：每条含 **预计文件 / 层**），与 epic 对齐。

**propose 完成后** → 读 [task-review-gate.md](task-review-gate.md)，输出 **Task Review Pack**，**停止**（不写码）。

**已有 change 且人审通过** → 读 [.cursor/skills/openspec-apply-change/SKILL.md](../openspec-apply-change/SKILL.md)：

```bash
openspec status --change "<name>" --json
openspec instructions apply --change "<name>" --json
```

按 `tasks.md` 逐项实现；每完成一项 `- [ ]` → `- [x]`。

**Apply 前**：确认 `tasks.md` §0 `Tasks reviewed by human` 已勾选，或用户本轮明确 **「tasks 人审通过」/「继续实现」**；否则 **停止** 并输出 Task Review Pack（见 task-review-gate.md）。

**Scope 膨胀** → 停，回到 propose 或拆新 change（见 reference.md）。

---

## 1.5 Task Review Gate（propose 后必做，apply 前必过）

读 [task-review-gate.md](task-review-gate.md)。

1. 展示 tasks 一览 + Review checklist（前后端成对、Harness 覆盖 epic 对齐）。
2. **HARD STOP** — 不创建/修改 `apps/` 业务代码。
3. 等人改 `tasks.md` 并说 **「tasks 人审通过」** 或 **「继续实现」** 后，才进入 §4 Implement。

**教训（ep03-jwt）**：后端有 register API 时，tasks 必须含注册页 task，不能只有登录页。

---

## 1.6 Branch（task 开始前）

详见 [docs/tech/branch-strategy.md](../../docs/tech/branch-strategy.md)。

1. §0 人审通过后，change 首个 task：`pnpm branch:change <name>` → `feat/<change>`
2. 每个 task 开始前：`pnpm branch:task <name> <task-id>`（或省略 id 取第一条 pending）
3. 回复中写明：**当前分支** + task id；再进入 §4 Implement

用户指定 `/work-next ep03-db-optimize 2.1` 时，应对应 `feat/ep03-db-optimize-t2-1-…`。

---

## 2. Superpowers（按条件，可跳过）

读 [reference.md § Superpowers 决策表](reference.md#superpowers-决策表)。

| 典型场景 | 使用 skill |
|:---------|:-----------|
| 需求/协议不清（EP02 SSE、Agent 分支） | **brainstorming** |
| 多文件 / 新模块 / P0 Story 首做 | **writing-plans** 或 OpenSpec tasks 已够则省略 |
| API / 业务行为变更 | **test-driven-development**（先 harness/unit 红灯） |
| Bug / 测试失败 | **systematic-debugging** |
| 声称完成 / commit / push 前 | **verification-before-completion** |
| merge 前 | **requesting-code-review** 或 **code-reviewer** subagent |
| 分支收尾 | **finishing-a-development-branch** |

**可跳过 Superpowers 整段**：单行 typo、纯文档索引、OpenSpec tasks 已极细且用户说「小改」— 仍须 **Verify + Harness（若动 API）**。

OpenSpec 的 design/tasks **不能替代** TDD 顺序与 verification 门禁。

---

## 3. Harness 计划（API / AI 必做）

**凡改动 `apps/api` 路由、响应 schema、Agent/LLM 行为** → 必须有 Harness 策略。

| 层 | 目录 | 何时 |
|:---|:-----|:-----|
| **L1** | `apps/api/tests/harness/test_*_contract.py` | 新/改 HTTP 契约、错误体、字段 |
| **L2** | `harness/cases/*.yaml` + 脚本 | EP02+ 对话质量、RAG rubric |
| **L3** | 多轮统计报告 | EP05+ Agent 稳定性 |

**TDD 默认（L1）**：

1. 先写或扩展 `test_*_contract.py`（预期失败）。
2. 实现代码至绿灯。
3. 根目录：`pnpm test:api:harness`

单元逻辑放 `tests/unit/`；**合并前 L1 必须绿**（或 documented skip 原因）。

---

## 4. Implement（循环）

**开始前必读** [coding-constraints.md](coding-constraints.md)（五条规范 + diff 预算 + 分层）。

对 OpenSpec 每条 pending task：

0. **分支**：`pnpm branch:task <change> <task-id>`（或用户已手动 checkout）；禁止在 `main` 上直接堆 task 代码（除非用户明确要求直推 main）
1. 声明：`Working on task X/Y: <描述>`（含当前分支名）
2. 若本 task 触 API → 同步步骤 3 Harness
3. **最小 diff**：≤3 文件 / ~150 行；一函数一事；复杂逻辑拆工具函数
4. 勾选 task；输出 **Review 摘要** 后 **停止**（除非用户说「继续下一 task」）

---

## 5. Verify（必做）

**verification-before-completion** — 无输出不算完成：

```bash
pnpm db:up                    # 需要 DB/Redis 时
pnpm test:api:harness         # 动过 API 时必跑
bash scripts/api.sh exec pytest tests/unit -q   # 有 unit 时
```

FE 变更：`pnpm lint` / 项目既有脚本。把 **命令 + 通过数** 写进回复。

---

## 6. Review（merge 前必做）

1. **code-reviewer** subagent 或 **requesting-code-review**
2. 对照：OpenSpec tasks、design、epic 勾选
3. **Critical / Important** 必须修；Minor 可记 issue
4. 修完 **重新跑步骤 5**

用户 `/babysit` → 读 babysit skill，盯 PR/CI/评论。

---

## 7. Finish（用户要求提交/合并时）

1. **Checkpoint commit（推荐）** — 每完成一条 OpenSpec task 且 Verify 通过后：
   - 用户未禁止 commit 时：`git add` 仅本 task 文件 → Conventional commit（如 `feat(api): ep03-jwt task 2.1 login endpoint`）
   - 便于 review / bisect；多个 task 不要攒成一个巨型 commit
2. **分支与 PR（推荐）** — `pnpm branch:task <change> <id>`；集成分支 `feat/<change>`，task 分支 `feat/<change>-tX-Y-slug`；单 PR ≤ **5 文件**
3. push / merge（**finishing-a-development-branch**）；直推 `main` 仅在小改且用户明确要求时
4. 读 [.cursor/skills/openspec-archive-change/SKILL.md](../openspec-archive-change/SKILL.md) → `/opsx:archive`（change 全部 task 完成后）
5. 勾选 `docs/tasks/epics/` 与 `docs/tasks/learning/` 相关项
6. 可选：沉淀 `docs/tech/knowledge/*.md`

---

## 输出模板

```markdown
## Work Next: <change-or-story>

**OpenSpec:** <name> — N/M tasks
**Superpowers:** <used skills or "skipped — reason">
**Harness:** <files added/updated> — `pnpm test:api:harness`: X passed

### Done this session
- [x] ...

### Next
- ...
```

---

## 子 skill 索引

| 阶段 | Skill 路径 |
|:-----|:-----------|
| Propose | `.cursor/skills/openspec-propose/SKILL.md` |
| Apply | `.cursor/skills/openspec-apply-change/SKILL.md` |
| Archive | `.cursor/skills/openspec-archive-change/SKILL.md` |
| Explore | `.cursor/skills/openspec-explore/SKILL.md` |

Superpowers 插件技能（brainstorming、TDD、verification 等）按 reference 决策表选用。

---

## 示例

```
/work-next ep03-jwt
开始 EP03 Story 3.4
work ep02-chat-sse
按协作流程做 JWT
```

Agent 从 **0 Orient** 开始，不要跳过 OpenSpec；不要在没有 harness 证据时声称 API 完成。
