# Work Next — 参考

## Superpowers 决策表

| 条件 | 动作 |
|:-----|:-----|
| P0 Story 且 OpenSpec design 空或需求歧义 | **brainstorming** → 结论写入 proposal/design |
| tasks > 5 条或跨 web+api+infra | **writing-plans**（或 trust OpenSpec tasks 若已够细） |
| 改 API 行为 / 新 endpoint | **test-driven-development** + L1 harness |
| 测试红 / 行为异常 | **systematic-debugging** |
| commit / push / 「完成了」 | **verification-before-completion** |
| merge / PR 前 | **requesting-code-review** 或 **code-reviewer** |
| 功能完毕问怎么合 | **finishing-a-development-branch** |
| 仅改 Markdown 链接、注释 | **跳过** Superpowers；若未动 API 可跳过 harness |
| 仅改 FE 样式、无契约 | harness 跳过；`pnpm lint` 即可 |

**不跳过**：OpenSpec 对齐、API 变更的 L1 harness、verification（若有验证命令）。

---

## Harness 分层（MemoryOS）

| 层 | 测什么 | 命令/位置 |
|:---|:-------|:----------|
| L1 | HTTP 状态、`{code,message,data}`、关键字段 | `pnpm test:api:harness` |
| L2 | LLM rubric、对话案例 | `harness/cases/*.yaml`（EP02+） |
| L3 | 多轮 pass rate | EP05+ |

AI / Agent / 流式 / RAG 功能：**L1 每次必加**；上线前补 L2 说明或脚本。

---

## OpenSpec 命令

```bash
openspec list --json
openspec new change "<name>"
openspec status --change "<name>" --json
openspec instructions apply --change "<name>" --json
# Cursor: /opsx:propose | /opsx:apply | /opsx:archive
```

Change 命名：`ep<NN>-<topic>`（如 `ep03-jwt`、`ep02-chat-sse`）。  
单 Story 一个 change；过大则拆。

---

## 常用验证命令

```bash
pnpm db:up
pnpm db:migrate
pnpm test:api:harness
pnpm branch:change <change>
pnpm branch:task <change> [task-id]
pnpm dev:stack
bash scripts/api.sh exec pytest tests/unit -q
```

---

## Definition of Done（摘自 ai-collab-stack §6）

- [ ] Epic / OpenSpec `tasks.md` 已勾选（**含 §0 人审**）
- [ ] change propose → **task review gate** → apply → **archive**（或 PR 链到 change）
- [ ] Harness L1 绿（AI 功能附 L2/L3 计划）
- [ ] verification 证据已贴出
- [ ] 必要时有 `docs/tech/knowledge/` 沉淀

---

## 与 EP00 的关系

本 skill 是 EP00 Collab 轨道的 **可执行 SOP**。  
史诗计划仍在 `docs/tasks/epics/`；单次交付在 `openspec/changes/`。
