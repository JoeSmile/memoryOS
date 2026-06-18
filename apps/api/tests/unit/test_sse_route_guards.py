"""Static guards: SSE routes must not hold get_db/get_redis via Depends for the stream lifetime."""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_SSE_DEPENDS = frozenset({"get_db", "get_redis"})


def _api_v1_python_files() -> list[Path]:
    root = Path(__file__).resolve().parents[2] / "app" / "api" / "v1"
    return sorted(root.rglob("*.py"))


def _depends_names(function_def: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(function_def):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "Depends":
            if node.args and isinstance(node.args[0], ast.Name):
                names.add(node.args[0].id)
            elif node.args and isinstance(node.args[0], ast.Attribute):
                names.add(node.args[0].attr)
    return names


def _returns_streaming_response(function_def: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(function_def):
        if isinstance(node, ast.Name) and node.id == "StreamingResponse":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "StreamingResponse":
            return True
    return False


def find_sse_routes_with_forbidden_depends() -> list[str]:
    violations: list[str] = []
    for path in _api_v1_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _returns_streaming_response(node):
                continue
            bad = _depends_names(node) & FORBIDDEN_SSE_DEPENDS
            if bad:
                rel = path.relative_to(Path(__file__).resolve().parents[2])
                violations.append(
                    f"{rel}:{node.lineno} {node.name} uses Depends({', '.join(sorted(bad))})",
                )
    return violations


def test_sse_routes_do_not_depend_on_get_db_or_get_redis():
    violations = find_sse_routes_with_forbidden_depends()
    assert not violations, (
        "SSE handlers must not use Depends(get_db/get_redis); "
        "use short-lived AsyncSessionLocal scopes inside the generator instead.\n"
        + "\n".join(violations)
    )
