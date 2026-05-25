## Why

EP03 Story 3.1–3.2 已完成 PostgreSQL 与 conversations
CRUD，但会话列表每次命中数据库，且 EP02 流式对话需要临时缓冲 partial
token。Story 3.3 引入 **Redis 7**
作为缓存层，降低列表读负载并为 SSE 流式写入做准备。

## What Changes

- 启用 `infra/docker/docker-compose.yml` 中的 **Redis 7** 服务与持久化卷。
- 新增 `REDIS_URL` 配置与 `app/core/redis.py` 异步客户端封装。
- 实现 **Cache-Aside** 会话列表缓存（PostgreSQL 仍为真相源）。
- 实现 **流式临时缓存** 工具类（供 EP02 SSE 拼接 partial content）。
- 扩展 `/health` 与 `/api/v1/health` 返回 `postgres` / `redis` 依赖状态。
- 新增 Harness L1 契约测试；更新 `docs/database.md`、`infra/docker/README.md`。
- **不引入**：JWT 登录、refresh token 黑名单（Story 3.4）、业务索引优化（Story
  3.5）。

## Capabilities

### New Capabilities

- `redis-infra`: Docker Redis 7、连接配置、健康探测、脚本等待就绪。
- `redis-cache`: 会话列表 Cache-Aside、流式临时 key/TTL 约定与封装。

### Modified Capabilities

- `postgres-infra`: Compose 文档与 `pnpm db:up` 同时启动 Redis（双服务栈）。
- `data-access-layer`: `GET /api/v1/conversations`
  在 Redis 可用时使用缓存；创建会话后失效缓存。

## Impact

| 区域                            | 影响                                 |
| :------------------------------ | :----------------------------------- |
| `infra/docker/`                 | 启用 redis 服务、volume、healthcheck |
| `scripts/docker.sh`             | 等待 Redis PING                      |
| `apps/api/app/core/`            | `config.py`、`redis.py`（新）        |
| `apps/api/app/cache/`           | 缓存封装（新）                       |
| `apps/api/app/services/`        | `ConversationService` 集成缓存       |
| `apps/api/app/api/v1/health.py` | 依赖状态探测                         |
| `apps/api/tests/harness/`       | health / redis 契约                  |
| 依赖                            | `redis[hiredis]`                     |
| EP02                            | 复用 `StreamCache` 与 key 命名       |
