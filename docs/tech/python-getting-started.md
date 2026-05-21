# Python 入门（Story 1.4 最小集）

> 面向 **TS/JS 背景**、Python 几乎零基础。只学完成 EP01 Story
> 1.4 + 后续 EP03 必需的片段，其余边做边补。  
> **目标版本**：Python **3.11+**

---

## 1. 环境配置（第一次必做）

> **推荐**：在仓库**根目录**执行 `pnpm setup:api` / `pnpm dev:api`，无需每次 `cd apps/api`。  
> 本地已有 Conda 环境 **`memoryos-api`** 时：日常 **`pnpm dev:api`** 即可；仅首次克隆或 `requirements.txt` 变更后再 `pnpm setup:api`。  
> 下文 §1.2 为手动方式说明。

### 1.1 安装 Python

```bash
# macOS（Homebrew）
brew install python@3.12

python3 --version   # 应 >= 3.11
```

Windows：从 [python.org](https://www.python.org/downloads/) 安装，勾选 **Add to
PATH**。

### 1.2 虚拟环境（项目隔离，必用）

任选 **一种** 方式即可；已有 Conda 时推荐用 Conda，环境名与版本更好管理。

#### 方式 A：Conda（推荐，若本机已安装）

```bash
cd apps/api

# 创建环境（只需一次），Python 3.11+
conda create -n memoryos-api python=3.12 -y

# 激活（每次新开终端都要执行）
conda activate memoryos-api

# 确认用的是该环境的 Python
which python    # 应含 .../envs/memoryos-api/...
python --version
```

卸载 / 重建环境（可选）：

```bash
conda deactivate
conda env remove -n memoryos-api
```

> Conda 环境在 `~/miniconda3/envs/` 或 `~/anaconda3/envs/`
> 下，**不会**污染系统 Python，也无需在项目里生成 `.venv` 目录。

#### 方式 B：内置 venv（无 Conda 时）

```bash
cd apps/api

python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows PowerShell

which python   # 应指向 apps/api/.venv/bin/python
```

**不要**在 `base` 或系统 Python 里全局 `pip install` 项目依赖。

### 1.3 安装依赖

```bash
pip install -r requirements.txt
```

### 1.4 环境变量

```bash
cp .env.example .env
```

### 1.5 启动服务

```bash
# 在 memoryOS 根目录
pnpm dev:api
```

或手动：`cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

验证：

- 浏览器打开 <http://localhost:8000/docs>（Swagger 自动文档）
- <http://localhost:8000/health>

---

## 2. 和 TypeScript 的对照（先建立映射）

| TypeScript           | Python                         | 说明                     |
| :------------------- | :----------------------------- | :----------------------- |
| `const` / `let`      | 直接赋值，无 `const`           | 约定全小写+下划线命名    |
| `interface` / `type` | `class` + Pydantic `BaseModel` | API 入参/出参用 Pydantic |
| `async/await`        | `async def` + `await`          | FastAPI 路由常用 async   |
| `import { x } from`  | `from x import y`              |                          |
| `null` / `undefined` | `None`                         |                          |
| `===`                | `==`                           |                          |
| 数组 `[]`            | 列表 `[]`                      |                          |
| 对象 `{}`            | 字典 `{}`                      | key-value                |

---

## 3. 必会语法（30 分钟）

### 3.1 函数与类型注解

```python
def add(a: int, b: int) -> int:
    return a + b

async def fetch_user(user_id: str) -> dict:
    return {"id": user_id}
```

类型注解类似 TS，运行时不强制，但 IDE 和工具会检查。

### 3.2 字典与列表

```python
user = {"name": "alice", "age": 20}
print(user["name"])

items = [1, 2, 3]
for item in items:
    print(item)
```

### 3.3 异步（FastAPI 核心）

```python
import httpx

async def call_api():
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://example.com")
        return resp.status_code
```

理解：`async def` 的路由里可以 `await` 数据库/HTTP，不阻塞线程。

### 3.4 装饰器（读代码常见）

```python
@router.get("/health")
async def health():
    return {"ok": True}
```

类似「包装函数」；FastAPI 用装饰器注册路由，先会用即可。

### 3.5 模块与包

- 一个 `.py` 文件 = 一个模块
- 文件夹 + `__init__.py` = 包（类似目录模块）
- `from app.core.config import settings` ≈ 从子路径导入单例配置

---

## 4. FastAPI 必会概念（Story 1.4）

| 概念                  | 作用                    | 本项目位置               |
| :-------------------- | :---------------------- | :----------------------- |
| **App**               | 应用入口                | `app/main.py`            |
| **Router**            | 路由分组                | `app/api/v1/router.py`   |
| **Pydantic Settings** | 读 `.env` 配置          | `app/core/config.py`     |
| **CORS Middleware**   | 允许前端跨域            | `app/main.py`            |
| **Exception Handler** | 统一错误格式            | `app/core/exceptions.py` |
| **Uvicorn**           | ASGI 服务器，跑 FastAPI | 启动命令                 |

**请求路径示例**：

```
浏览器 GET /health
  → uvicorn
  → FastAPI app
  → health 路由函数
  → 返回 JSON
```

---

## 5. 建议学习顺序（配合 L01）

| 顺序 | 内容                                                               | 时间   |
| :--: | :----------------------------------------------------------------- | :----- |
|  1   | 本文 §1 环境跑通                                                   | 30 min |
|  2   | 读 `app/main.py` → `api/v1/health.py` → `core/config.py`           | 30 min |
|  3   | 改 `/health` 返回字段，观察热重载                                  | 15 min |
|  4   | 官方 [FastAPI 教程](https://fastapi.tiangolo.com/tutorial/) 前几章 | 2 h    |
|  5   | EP03 再学 SQLAlchemy（不必现在学完）                               | —      |

**不必先学**：装饰器原理、元类、numpy、pandas、Django。

---

## 6. 常见问题

| 现象                         | 处理                                                                            |
| :--------------------------- | :------------------------------------------------------------------------------ |
| `command not found: uvicorn` | 未 `conda activate memoryos-api` / 未激活 `.venv`，或未 `pip install`           |
| Conda 里 `pip` 装错包        | 先 `conda activate memoryos-api`，再 `which pip` 确认路径在 `envs/memoryos-api` |
| `ModuleNotFoundError: app`   | 须在 `apps/api` 目录启动，或设置 `PYTHONPATH`                                   |
| 改代码不生效                 | 确认 `--reload`；或重启 uvicorn                                                 |
| 端口 8000 占用               | `lsof -i :8000` 杀掉进程或改 `.env` 里 `PORT`                                   |
| pip 很慢                     | `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`   |

---

## 相关

- [BE-engineering.md](./BE-engineering.md) — 后端工程结构
- [L01-foundation.md](../tasks/learning/L01-foundation.md) — 学习勾选
- [apps/api/README.md](../../apps/api/README.md) — 启动命令
