#!/usr/bin/env bash
# Create/checkout OpenSpec-aligned git branches (change + task).
# Usage:
#   bash scripts/branch-task.sh <change> [task-id] [--change-only] [--dry-run] [--no-pull]
#   pnpm branch:task ep03-db-optimize 2.1
#   pnpm branch:change ep03-db-optimize
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

CHANGE=""
TASK_ID=""
CHANGE_ONLY=0
DRY_RUN=0
NO_PULL=0

usage() {
  cat <<'EOF'
Usage:
  pnpm branch:task <change> [task-id] [options]
  pnpm branch:change <change> [options]

Options:
  --change-only   Only create/checkout feat/<change> (integration branch)
  --dry-run       Print branch names; do not checkout
  --no-pull       Skip git pull on main

Examples:
  pnpm branch:change ep03-db-optimize
  pnpm branch:task ep03-db-optimize           # first pending task
  pnpm branch:task ep03-db-optimize 2.1
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --change-only) CHANGE_ONLY=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --no-pull) NO_PULL=1 ;;
    -h|--help) usage; exit 0 ;;
    -*)
      echo "[error] unknown option: $1" >&2
      usage
      exit 1
      ;;
    *)
      if [[ -z "${CHANGE}" ]]; then
        CHANGE="$1"
      elif [[ -z "${TASK_ID}" ]]; then
        TASK_ID="$1"
      else
        echo "[error] unexpected argument: $1" >&2
        usage
        exit 1
      fi
      ;;
  esac
  shift
done

if [[ -z "${CHANGE}" ]]; then
  echo "[error] missing <change> name" >&2
  usage
  exit 1
fi

TASKS_FILE="${ROOT}/openspec/changes/${CHANGE}/tasks.md"
if [[ ! -f "${TASKS_FILE}" ]]; then
  ARCHIVE_GLOB="${ROOT}/openspec/changes/archive/"*"-${CHANGE}/tasks.md"
  # shellcheck disable=SC2086
  set -- ${ARCHIVE_GLOB}
  if [[ -f "$1" ]]; then
    TASKS_FILE="$1"
    echo "[warn] using archived tasks: ${TASKS_FILE}"
  else
    echo "[error] tasks.md not found for change '${CHANGE}'" >&2
    exit 1
  fi
fi

slugify() {
  local text="$1"
  local slug=""
  local word
  while read -r word; do
    word="$(echo "${word}" | tr '[:upper:]' '[:lower:]')"
    [[ -z "${word}" ]] && continue
    if [[ -z "${slug}" ]]; then
      slug="${word}"
    else
      slug="${slug}-${word}"
    fi
    # shellcheck disable=SC2143
    [[ "$(echo "${slug}" | tr '-' '\n' | wc -l | tr -d ' ')" -ge 3 ]] && break
  done < <(echo "${text}" | grep -oE '[a-zA-Z][a-zA-Z0-9]*' || true)
  if [[ -z "${slug}" ]]; then
    echo "task"
  else
    echo "${slug}"
  fi
}

human_review_ok() {
  grep -qE '^- \[[xX]\] \*\*Tasks reviewed by human\*\*' "${TASKS_FILE}" 2>/dev/null
}

find_task_line() {
  local want_major="${1:-}"
  local want_minor="${2:-}"
  local line major minor rest
  while IFS= read -r line; do
    if [[ "${line}" =~ ^-[\ ]+\[[\ xX]\][\ ]+([0-9]+)\.([0-9]+)[\ ]+(.*)$ ]]; then
      major="${BASH_REMATCH[1]}"
      minor="${BASH_REMATCH[2]}"
      rest="${BASH_REMATCH[3]}"
      if [[ "${rest}" == *"Tasks reviewed by human"* ]]; then
        continue
      fi
      if [[ -n "${want_major}" ]]; then
        if [[ "${major}" == "${want_major}" && "${minor}" == "${want_minor}" ]]; then
          echo "${major}|${minor}|${rest}"
          return 0
        fi
      else
        if [[ "${line}" =~ ^-[[:space:]]+\[[[:space:]]\] ]]; then
          echo "${major}|${minor}|${rest}"
          return 0
        fi
      fi
    fi
  done < "${TASKS_FILE}"
  return 1
}

TASK_DESC=""
if [[ "${CHANGE_ONLY}" -eq 0 ]]; then
  MAJOR="" MINOR=""
  if [[ -n "${TASK_ID}" ]]; then
    TASK_ID="${TASK_ID//-/.}"
    if [[ ! "${TASK_ID}" =~ ^([0-9]+)\.([0-9]+)$ ]]; then
      echo "[error] task-id must be like 2.1 (got: ${TASK_ID})" >&2
      exit 1
    fi
    MAJOR="${BASH_REMATCH[1]}"
    MINOR="${BASH_REMATCH[2]}"
  fi

  if [[ -n "${MAJOR}" ]]; then
    TASK_INFO="$(find_task_line "${MAJOR}" "${MINOR}")" || {
      echo "[error] task ${MAJOR}.${MINOR} not found in ${TASKS_FILE}" >&2
      exit 1
    }
  else
    TASK_INFO="$(find_task_line)" || {
      echo "[error] no pending task (- [ ]) in ${TASKS_FILE}" >&2
      exit 1
    }
  fi
  IFS='|' read -r MAJOR MINOR TASK_DESC <<<"${TASK_INFO}"
fi

CHANGE_BRANCH="feat/${CHANGE}"
TASK_BRANCH=""
if [[ "${CHANGE_ONLY}" -eq 0 ]]; then
  SLUG="$(slugify "${TASK_DESC}")"
  TASK_BRANCH="feat/${CHANGE}-t${MAJOR}-${MINOR}-${SLUG}"
fi

if ! human_review_ok; then
  echo "[warn] tasks.md §0 'Tasks reviewed by human' is not checked."
  echo "       Review tasks before coding (see .cursor/skills/work-next/task-review-gate.md)."
fi

echo "[branch] change: ${CHANGE}"
echo "[branch] tasks:  ${TASKS_FILE}"
if [[ -n "${TASK_BRANCH}" ]]; then
  echo "[branch] task:   ${MAJOR}.${MINOR} — ${TASK_DESC}"
  echo "[branch] integration → ${CHANGE_BRANCH}"
  echo "[branch] working      → ${TASK_BRANCH}"
else
  echo "[branch] integration → ${CHANGE_BRANCH}"
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  exit 0
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "[error] not a git repository" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "[warn] working tree has uncommitted changes"
fi

git fetch origin main 2>/dev/null || git fetch origin 2>/dev/null || true

if git show-ref --verify --quiet "refs/heads/main"; then
  MAIN_REF="main"
elif git show-ref --verify --quiet "refs/heads/master"; then
  MAIN_REF="master"
else
  echo "[error] neither main nor master branch found" >&2
  exit 1
fi

checkout_branch() {
  local branch="$1"
  local base="$2"
  if git show-ref --verify --quiet "refs/heads/${branch}"; then
    echo "[git] checkout existing ${branch}"
    git checkout "${branch}"
  else
    echo "[git] create ${branch} from ${base}"
    git checkout -b "${branch}" "${base}"
  fi
}

if [[ "${NO_PULL}" -eq 0 ]]; then
  git checkout "${MAIN_REF}"
  if git rev-parse --verify "refs/remotes/origin/${MAIN_REF}" >/dev/null 2>&1; then
    git pull --ff-only "origin" "${MAIN_REF}" || echo "[warn] git pull failed; continuing on local ${MAIN_REF}"
  fi
else
  git checkout "${MAIN_REF}" 2>/dev/null || true
fi

if [[ "${CHANGE_ONLY}" -eq 1 ]]; then
  checkout_branch "${CHANGE_BRANCH}" "${MAIN_REF}"
  echo "[ok] on ${CHANGE_BRANCH}"
  exit 0
fi

# Ensure integration branch exists (from main)
if git show-ref --verify --quiet "refs/heads/${CHANGE_BRANCH}"; then
  git checkout "${CHANGE_BRANCH}"
else
  checkout_branch "${CHANGE_BRANCH}" "${MAIN_REF}"
fi

checkout_branch "${TASK_BRANCH}" "${CHANGE_BRANCH}"
echo "[ok] on ${TASK_BRANCH} (merge target: ${CHANGE_BRANCH} → ${MAIN_REF})"
