## Why

EP03 Story 3.5：核心表已有基础 FK 与单列索引，但列表查询（按 `updated_at` / `created_at` 排序）与「创建会话 + 首条消息」事务尚未优化。本 change 补 **复合索引**、**Service 层事务** 与 **连接池基础调优**。

Story 3.4 JWT 在 change `ep03-jwt` 独立交付；本 change **依赖** JWT 可选（事务与 messages 创建不强制登录）。

## What Changes

- Alembic `002`：复合索引 `(conversations.user_id, updated_at DESC)`、`(messages.conversation_id, created_at)`（若与现有索引重复则合并设计）。
- `ConversationService`（或新 method）：单事务创建 conversation + 首条 user message。
- `create_async_engine` 连接池参数可配置（`pool_size`、`max_overflow`）。
- Harness：事务 + 列表 API 仍绿；可选 integration test。
- **不引入**：慢查询监控、生产 APM（EP09）。

## Capabilities

### New Capabilities

- （无独立 capability 名；归入 schema + data-access 增量）

### Modified Capabilities

- `core-schema`: 列表查询复合索引。
- `data-access-layer`: 创建会话与首条消息同一事务。

## Impact

| 区域 | 影响 |
|:-----|:-----|
| `alembic/versions/` | 002 迁移 |
| `app/services/` | 事务方法 |
| `app/core/database.py` | pool 配置 |
| `docs/database.md` | 索引说明 |
