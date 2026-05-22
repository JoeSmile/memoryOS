# infra/docker — 本地数据服务

EP03 Story 3.1 起提供 PostgreSQL；Redis 在 Story 3.3 启用。

## 前置

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 或 Docker Engine + Compose v2

## 启动 PostgreSQL

**推荐：在仓库根目录**

```bash
pnpm db:up      # 启动并等待 healthy
pnpm db:ps      # 查看状态
```

或在本目录：

```bash
cd infra/docker
docker compose up -d
docker compose ps
```

期望 `memoryos-postgres` 状态为 `healthy`。

### 连接信息（开发默认）

| 项 | 值 |
|:---|:---|
| Host（宿主机跑 API） | `localhost` |
| Host（容器内跑 API，EP08） | `postgres` |
| Port | `5432` |
| Database | `memoryos` |
| User / Password | `memoryos` / `memoryos` |

**异步 SQLAlchemy 连接串**（复制到 `apps/api/.env`）：

```text
DATABASE_URL=postgresql+asyncpg://memoryos:memoryos@localhost:5432/memoryos
```

## 与开发服务配合

**一键（数据库 + 前后端）**：

```bash
# 仓库根目录
pnpm dev:stack    # db:up → dev:web + dev:api 并行
# 等价于: pnpm db:up && pnpm dev:all
```

分步：

1. `pnpm db:up`
2. `apps/api`：`cp .env.example .env`，确认 `DATABASE_URL`
3. `pnpm dev:api` 或 `pnpm dev:all`
4. Story 3.2：`pnpm db:migrate`（或 `cd apps/api && alembic upgrade head`）

API 进程在**宿主机**运行，因此 URL 使用 `localhost`，不要用服务名 `postgres`。

## 常用命令

```bash
# 查看日志
docker compose logs -f postgres

# 进入 psql
docker compose exec postgres psql -U memoryos -d memoryos

# 停止
docker compose down

# 停止并删除数据卷（清空库，慎用）
docker compose down -v
```

## 验证连接（任务 1.5）

```bash
docker compose exec postgres psql -U memoryos -d memoryos -c "SELECT 1 AS ok;"
```

或宿主机已安装 `psql`：

```bash
psql "postgresql://memoryos:memoryos@localhost:5432/memoryos" -c "SELECT 1;"
```

## 数据持久化

数据卷 `postgres-data` 由 Compose 管理；`.gitignore` 已忽略本地 `postgres-data/` 目录名（若 bind mount 时使用）。

## 后续（EP08）

完整栈将扩展 `web`、`api`、`nginx` 等于同一 compose 文件；当前仅数据库，便于 EP03 开发。
