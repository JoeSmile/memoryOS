#!/usr/bin/env bash
# MemoryOS API — 从仓库根目录安装依赖、启动 Uvicorn（无需手动 cd apps/api）
# 日常：pnpm dev:api（已有 Conda memoryos-api 或 .venv 时）
# 首次 / 依赖变更：pnpm setup:api
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$ROOT/apps/api"
cd "$API_DIR"

has_conda() {
  command -v conda >/dev/null 2>&1
}

conda_env_exists() {
  has_conda && conda env list | awk '{print $1}' | grep -qx "memoryos-api"
}

use_conda() {
  conda_env_exists
}

run_in_api_env() {
  if use_conda; then
    conda run -n memoryos-api --no-capture-output "$@"
  elif [[ -x .venv/bin/python ]]; then
    exec .venv/bin/"$@"
  else
    echo "❌ 未找到 API 环境。请在仓库根目录执行: pnpm setup:api"
    echo "   （Conda: memoryos-api  或  apps/api/.venv）"
    exit 1
  fi
}

cmd_setup() {
  echo "→ API 目录: $API_DIR"

  if has_conda; then
    if ! conda_env_exists; then
      echo "→ 创建 Conda 环境 memoryos-api (Python 3.12)…"
      conda create -n memoryos-api python=3.12 -y
    else
      echo "→ 使用已有 Conda 环境 memoryos-api"
    fi
    echo "→ pip install -r requirements.txt …"
    conda run -n memoryos-api pip install -r requirements.txt
    if [[ -f requirements-dev.txt ]]; then
      conda run -n memoryos-api pip install -r requirements-dev.txt
    fi
  else
    if [[ ! -x .venv/bin/python ]]; then
      echo "→ 未检测到 conda，创建 .venv …"
      python3 -m venv .venv
    fi
    echo "→ pip install -r requirements.txt …"
    .venv/bin/pip install -r requirements.txt
    if [[ -f requirements-dev.txt ]]; then
      .venv/bin/pip install -r requirements-dev.txt
    fi
  fi

  if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "→ 已复制 .env.example → .env"
  fi

  echo "✅ API 依赖就绪。启动: pnpm dev:api"
}

cmd_dev() {
  if ! use_conda && [[ ! -x .venv/bin/python ]]; then
    echo "❌ 请先执行: pnpm setup:api"
    exit 1
  fi
  if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "→ 已复制 .env.example → .env"
  fi

  HOST="${HOST:-0.0.0.0}"
  PORT="${PORT:-8000}"
  echo "→ Uvicorn http://${HOST}:${PORT}  (docs: /docs)"
  run_in_api_env uvicorn app.main:app --reload --host "$HOST" --port "$PORT"
}

cmd_exec() {
  shift
  if [[ $# -eq 0 ]]; then
    echo "用法: $0 exec <command...>"
    exit 1
  fi
  if ! use_conda && [[ ! -x .venv/bin/python ]]; then
    echo "❌ 请先执行: pnpm setup:api"
    exit 1
  fi
  run_in_api_env "$@"
}

case "${1:-}" in
  setup) cmd_setup ;;
  dev) cmd_dev ;;
  exec) cmd_exec "$@" ;;
  *)
    echo "用法: $0 setup | dev | exec <cmd...>"
    exit 1
    ;;
esac
