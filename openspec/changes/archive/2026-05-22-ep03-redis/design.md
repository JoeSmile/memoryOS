## Context

- **现状**：`docker-compose.yml`
  已注释 Redis 占位；`ConversationService.list_for_user`
  直查 PostgreSQL；health 仅返回 app/env。
- **约束**：Cache-Aside；PG 为真相源；Redis 不可用时降级直查 DB；响应格式
  `{ code, message, data }` 不变。
- **范围**：Story 3.3 only；JWT 黑名单留 Story 3.4。

## Goals / Non-Goals

**Goals:**

- `pnpm db:up` 启动 Postgres + Redis 并等待 healthy。
- 会话列表缓存 TTL 5 分钟；创建会话后删除对应 user 的列表 key。
- 提供 `StreamCache`：`append` / `get` / `delete`，TTL 1 小时，key 前缀
  `memoryos:stream:`。
- Health 暴露 `postgres`、`redis` 状态：`ok` | `down` | `disabled`。

**Non-Goals:**

- JWT refresh / token 黑名单（仅文档预留 key 前缀 `memoryos:jwt:blacklist:`）。
- 分布式锁、限流（EP09）。
- 修改 conversations API 路径或响应 schema。

## Decisions

### D1: redis-py asyncio + hiredis

- **选择**：`redis[hiredis]>=5.0`，`Redis.from_url(REDIS_URL)`。
- **理由**：官方 async 支持，与 FastAPI 原生 async 一致。
- **备选**：aioredis（已并入 redis-py）。

### D2: Key 命名与 TTL

| 用途              | Key                                             | TTL            |
| :---------------- | :---------------------------------------------- | :------------- |
| 会话列表          | `memoryos:conversations:user:{user_id}`         | 300s           |
| 流式缓冲          | `memoryos:stream:{conversation_id}:{stream_id}` | 3600s          |
| JWT 黑名单（3.4） | `memoryos:jwt:blacklist:{jti}`                  | token 剩余寿命 |

- **序列化**：列表缓存存 `ConversationRead` JSON 数组（非 ORM pickle）。

### D3: Cache-Aside 在 Service 层

- **选择**：`ConversationCache` 由 `ConversationService`
  调用；Repository 仍只访问 PG。
- **失效**：`create` 成功后 `DELETE` 列表 key（先写 DB 再删缓存）。
- **降级**：`REDIS_URL` 未配置或 ping 失败 → 跳过缓存，记录 debug 日志。

### D4: Health 依赖探测

- **Postgres**：`SELECT 1` via existing engine。
- **Redis**：`PING`；未配置则 `disabled`。

## Risks / Trade-offs

| 风险                 | 缓解                                                   |
| :------------------- | :----------------------------------------------------- |
| 缓存与 DB 短暂不一致 | 写后删 key；TTL 5min 上限                              |
| Redis 宕机           | 降级直查 PG；health 显示 `down`                        |
| Harness 无 Redis     | 测试断言允许 `disabled`/`down` 或文档要求 `pnpm db:up` |

## Migration Plan

1. `pnpm db:up`（重建 compose 含 redis）。
2. 取消 `.env` 中 `REDIS_URL` 注释。
3. `pnpm setup:api` 安装 `redis` 依赖。
4. 无 Alembic 变更。
