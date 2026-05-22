#!/usr/bin/env bash
# MemoryOS - Docker Compose helpers (infra/docker)
set -eo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_DIR="${ROOT}/infra/docker"

require_docker() {
  if ! docker info >/dev/null 2>&1; then
    echo "[error] Docker is not running. Start Docker Desktop first."
    exit 1
  fi
}

cmd_up() {
  require_docker
  cd "${COMPOSE_DIR}"
  echo "[docker] compose up (${COMPOSE_DIR})"
  docker compose up -d
  echo "[docker] waiting for PostgreSQL..."
  local i
  for i in $(seq 1 30); do
    if docker compose exec -T postgres pg_isready -U memoryos -d memoryos >/dev/null 2>&1; then
      echo "[ok] PostgreSQL ready at localhost:5432 (db: memoryos)"
      return 0
    fi
    sleep 1
  done
  echo "[warn] timeout; run: pnpm db:logs"
  exit 1
}

cmd_down() {
  require_docker
  cd "${COMPOSE_DIR}"
  docker compose down
  echo "[ok] stopped"
}

cmd_ps() {
  require_docker
  cd "${COMPOSE_DIR}"
  docker compose ps
}

cmd_logs() {
  require_docker
  cd "${COMPOSE_DIR}"
  docker compose logs -f "${1:-postgres}"
}

cmd_psql() {
  require_docker
  cd "${COMPOSE_DIR}"
  docker compose exec postgres psql -U memoryos -d memoryos "$@"
}

case "${1:-up}" in
  up) cmd_up ;;
  down) cmd_down ;;
  ps) cmd_ps ;;
  logs) shift; cmd_logs "$@" ;;
  psql) shift; cmd_psql "$@" ;;
  *)
    echo "usage: $0 up | down | ps | logs [service] | psql"
    exit 1
    ;;
esac
