## 0. Human review（apply 前必过）

> propose 完成后 **必须停在这里**等人审；未勾选前 **禁止** 写业务代码。

- [ ] **Tasks reviewed by human** — 人审通过后再 `/opsx:apply`、`/work-next` 或说「继续实现」

### Review checklist

- [ ] 前后端 scope 成对；Harness 覆盖 design scenarios
- [ ] 与 EP03 Story 3.5 一致；每条 task ≤3 文件

**Reviewer notes:**

**EP02 Program：** 本 change = [`ep02-program`](../ep02-program/tasks.md) **Phase 1**（须先 archive 再进入 Phase 2）。

---

## 1. Migration

- [ ] 1.1 Alembic `002` 复合索引 + 更新 `docs/database.md`
  - 预计文件：2 · 层：alembic、docs

## 2. Transaction API

- [ ] 2.1 Harness 扩展或 unit：create conversation + message 原子性
  - 预计文件：1 · 层：tests

- [ ] 2.2 `Message` repository + `ConversationService.create_with_first_message`
  - 预计文件：3 · 层：repositories、services

- [ ] 2.3 API `POST /conversations` 可选 `initial_message` 或 dedicated endpoint（design 择一，≤3 文件）
  - 预计文件：2 · 层：api、schemas

## 3. Pool & docs

- [ ] 3.1 `database.py` pool 配置 + `.env.example`
  - 预计文件：2 · 层：core

- [ ] 3.2 勾选 EP03 Story 3.5；archive change
  - 预计文件：1 · docs/epic
