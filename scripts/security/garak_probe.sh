#!/usr/bin/env bash
# MemoryOS Garak red-team probe (EP09 2.12) — offline / nightly, non-blocking.
# Usage (from repo root):
#   GARAK_PROBE_ENABLED=true bash scripts/security/garak_probe.sh
#   pnpm security:garak
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
API_DIR="$ROOT/apps/api"
CONFIG="$ROOT/scripts/security/garak_memoryos.yaml"
REPORT_DIR="${GARAK_REPORT_DIR:-$ROOT/.garak/reports}"

is_enabled() {
  case "${GARAK_PROBE_ENABLED:-false}" in
    1 | true | TRUE | yes | YES) return 0 ;;
    *) return 1 ;;
  esac
}

if ! is_enabled; then
  echo "Garak probe skipped (GARAK_PROBE_ENABLED is not true)."
  exit 0
fi

echo "→ Garak red-team probe (EP09 2.12)"

if [[ -f "$API_DIR/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$API_DIR/.venv/bin/activate"
elif command -v conda >/dev/null 2>&1 && conda env list | awk '{print $1}' | grep -qx "memoryos-api"; then
  GARAK_CMD=(conda run -n memoryos-api --no-capture-output garak)
else
  GARAK_CMD=(garak)
fi

if ! command -v garak >/dev/null 2>&1 && [[ ${#GARAK_CMD[@]} -eq 1 ]]; then
  echo "→ installing garak (optional red-team dep)…"
  python -m pip install --no-cache-dir 'garak>=0.9,<1'
fi

mkdir -p "$REPORT_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
PREFIX="$REPORT_DIR/memoryos-$STAMP"

TARGET_TYPE="${GARAK_TARGET_TYPE:-mock}"
GENERATIONS="${GARAK_GENERATIONS:-1}"

echo "  target_type=$TARGET_TYPE generations=$GENERATIONS"
echo "  report_prefix=$PREFIX"

set +e
if [[ "$TARGET_TYPE" == "rest" && -n "${GARAK_GENERATOR_OPTIONS:-}" ]]; then
  "${GARAK_CMD[@]}" \
    --config "$CONFIG" \
    --target_type rest \
    --generator_option_file "$GARAK_GENERATOR_OPTIONS" \
    --generations "$GENERATIONS" \
    --report_prefix "$PREFIX"
else
  "${GARAK_CMD[@]}" \
    --config "$CONFIG" \
    --target_type "$TARGET_TYPE" \
    --generations "$GENERATIONS" \
    --report_prefix "$PREFIX"
fi
EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -ne 0 ]]; then
  echo "Garak finished with exit $EXIT_CODE (non-blocking for PR; review report under $REPORT_DIR)."
else
  echo "Garak finished OK. Report: $PREFIX.*"
fi

# Nightly / manual red-team: do not fail CI by default.
exit 0
