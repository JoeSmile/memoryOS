# infra/docker — 本地数据服务

EP03 Story 3.1 起提供 PostgreSQL；Story 3.3 起提供 **Redis 7**。

## 前置

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 或 Docker
  Engine + Compose v2

## 启动（PostgreSQL + Redis）

**推荐：在仓库根目录**

```bash
pnpm db:up      # 启动并等待 postgres + redis healthy
pnpm db:ps      # 查看状态
```

或在本目录：

```bash
cd infra/docker
docker compose up -d
docker compose ps
```

期望 `memoryos-postgres` 与 `memoryos-redis` 状态均为 `healthy`。

### 连接信息（开发默认）

| 服务       | Host（宿主机跑 API） | Port   | 连接串                                                           |
| :--------- | :------------------- | :----- | :--------------------------------------------------------------- |
| PostgreSQL | `localhost`          | `5432` | `postgresql+asyncpg://memoryos:memoryos@localhost:5432/memoryos` |
| Redis      | `localhost`          | `6379` | `redis://localhost:6379/0`                                       |

容器内跑 API（EP08）时主机名分别为 `postgres`、`redis`。

复制到 `apps/api/.env`（见 `.env.example`）。

## 与开发服务配合

**一键（数据库 + 前后端）**：

```bash
# 仓库根目录
pnpm dev:stack    # db:up → dev:web + dev:api 并行
# 等价于: pnpm db:up && pnpm dev:all
```

分步：

1. `pnpm db:up`
2. `apps/api`：`cp .env.example .env`，确认 `DATABASE_URL` 与 `REDIS_URL`
3. `pnpm dev:api` 或 `pnpm dev:all`
4. Story 3.2：`pnpm db:migrate`

API 在**宿主机**运行，URL 使用 `localhost`，不要用 Compose 服务名。

## 常用命令

```bash
# 查看日志
docker compose logs -f postgres
docker compose logs -f redis

# 进入 psql
docker compose exec postgres psql -U memoryos -d memoryos

# Redis CLI
docker compose exec redis redis-cli

# 停止
docker compose down

# 停止并删除数据卷（清空库与缓存，慎用）
docker compose down -v
```

## 验证连接

```bash
docker compose exec postgres psql -U memoryos -d memoryos -c "SELECT 1 AS ok;"
docker compose exec redis redis-cli ping
```

## Redis 缓存约定（Story 3.3）

| Key                                             | TTL   | 用途                  |
| :---------------------------------------------- | :---- | :-------------------- |
| `memoryos:conversations:user:{user_id}`         | 300s  | 会话列表 Cache-Aside  |
| `memoryos:stream:{conversation_id}:{stream_id}` | 3600s | EP02 SSE 流式临时缓冲 |
| `memoryos:jwt:blacklist:{jti}`                  | —     | Story 3.4 预留        |

## 数据持久化

卷 `postgres-data`、`redis-data` 由 Compose 管理。

## 后续（EP08）

完整栈将扩展 `web`、`api`、`nginx` 等于同一 compose 文件。
