## Context

- **现状**：`001_core_tables` 已有 FK CASCADE、`ix_conversations_user_id`、`ix_messages_conversation_id`；无 messages API；conversations create 无首条消息。
- **约束**：迁移可回滚；不破坏 harness 现有用例。

## Goals / Non-Goals

**Goals:**

- 列表查询索引与 ER 文档一致。
- `create_conversation_with_message(user_id, title, content)` 单事务 commit。
- 连接池参数从 settings 读取，document 默认值。

**Non-Goals:**

- pgvector、读写分离、query log 分析。

## Decisions

### D1: 复合索引

- `CREATE INDEX ix_conversations_user_updated ON conversations (user_id, updated_at DESC)`
- `CREATE INDEX ix_messages_conv_created ON messages (conversation_id, created_at)`
- 若与 ORM `index=True` 单列重复，迁移中 drop redundant 或 skip 单列（design 实现时对照 DB）

### D2: 事务边界

- Service 方法内：`create conversation` → `add message` → `flush` → 返回；路由 `commit`；缓存 invalidate **commit 后**（同 3.3 模式）。

### D3: Pool

- `database_url` 不变；`DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10` 默认。

## Risks

| 风险 | 缓解 |
|:-----|:-----|
| 迁移锁表 | 开发库小表可接受；生产 EP08 维护窗 |
| 双索引冗余 | migration review 对照 `\d` |

## Migration Plan

`pnpm db:migrate` after deploy 002.
