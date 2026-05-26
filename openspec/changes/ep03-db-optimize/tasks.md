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
