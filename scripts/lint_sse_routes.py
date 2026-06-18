#!/usr/bin/env python3
"""CI helper: fail if SSE routes use Depends(get_db/get_redis)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from tests.unit.test_sse_route_guards import find_sse_routes_with_forbidden_depends  # noqa: E402


def main() -> int:
    violations = find_sse_routes_with_forbidden_depends()
    if violations:
        print("SSE route guard violations:")
        for line in violations:
            print(f"  - {line}")
        return 1
    print("SSE route guards: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
