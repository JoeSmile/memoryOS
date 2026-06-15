# infra/docker — 本地数据服务

EP03 Story 3.1 起提供 PostgreSQL；Story 3.3 起提供 **Redis 7**。  
EP04 起 Postgres 使用 **`pgvector/pgvector:pg16`**（预装 `vector` 扩展，供 RAG 向量检索）。

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

### 从 `postgres:16-alpine` 升级到 pgvector（EP04，会清空数据）

若你曾在旧镜像上跑过迁移，需 **重建数据卷** 后重新 `pnpm db:migrate`：

```bash
cd infra/docker
docker compose down -v
docker compose up -d
# 仓库根目录
pnpm db:migrate
```

本地 chat / 世界杯 Silver 等数据会丢失；Gold `jsonl` 在仓库内，EP04 摄入可重跑。

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

### 验证 pgvector（EP04）

```bash
docker compose exec postgres psql -U memoryos -d memoryos -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

期望输出一行 `vector`。Alembic `011`/`012` 迁移也会执行 `CREATE EXTENSION`；首次换镜像或 **embedding 维度变更** 后请先 `down -v` 再 `up`，或 `alembic upgrade head`（`012` 会清空 `document_chunks`，需 re-ingest）。

换镜像或拉代码后若 `alembic upgrade` 报缺 `pgvector` 包，在仓库根目录执行 `pnpm setup:api`（或 `bash scripts/api.sh exec pip install -r requirements.txt`）。

## Redis 缓存约定（Story 3.3）

| Key                                             | TTL   | 用途                  |
| :---------------------------------------------- | :---- | :-------------------- |
| `memoryos:conversations:user:{user_id}`         | 300s  | 会话列表 Cache-Aside  |
| `memoryos:stream:{conversation_id}:{stream_id}` | 3600s | EP02 SSE 流式临时缓冲 |
| `memoryos:jwt:blacklist:{jti}`                  | —     | Story 3.4 预留        |

## 数据持久化

卷 `postgres-data`、`redis-data` 由 Compose 管理。

## EP08 — Full profile（部署契约本地验证）

与宿主机 `pnpm dev:stack` **并行**：默认 `docker compose up` 仍 **仅** PG+Redis。

### 1. 构建镜像（与上云同一 Dockerfile）

```bash
# 仓库根目录
docker build -f apps/web/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8080 \
  -t memoryos-web:local .

docker build -f apps/api/Dockerfile -t memoryos-api:local apps/api
```

### 2. 部署 env

```bash
cd infra/docker
cp .env.deployment.example .env.deployment.local
# 编辑 JWT、Ollama 等（勿提交 git）
```

> 文件放在 **`infra/docker/.env.deployment.local`**，不是 `apps/api/`。上云复制为 `.env.deployment.cloud`。

### 3. 启动全栈

```bash
cd infra/docker
docker compose --env-file .env.deployment.local --profile full up -d
docker compose --profile full ps
```

入口：`http://localhost:8080`（`NGINX_HTTP_PORT` 可改）。反代规则见 [`infra/nginx/default.conf`](../nginx/default.conf)。

### 4. 迁移

```bash
docker compose --env-file .env.deployment.local --profile full run --rm api alembic upgrade head
```

### 5. 晋级云

同一 `WEB_IMAGE` / `API_IMAGE` tag push 到 registry → `.env.deployment.cloud` 换托管 PG/Redis 与百炼 Key → 同一 `compose --profile full`。

详见 [`docs/tech/deployment.md`](../../docs/tech/deployment.md)。
