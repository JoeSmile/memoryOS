#!/usr/bin/env python3
"""Bronze World Cup CSV profiler — manifest + report for EP04-01."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

SEMANTIC_GROUPS: list[dict[str, Any]] = [
    {
        "id": "tournament",
        "columns": ["tournament_id", "tournament_name"],
        "notes": "赛会标识；多文件重复贴标",
    },
    {
        "id": "team_identifiers",
        "columns": [
            "team_id",
            "home_team_id",
            "away_team_id",
            "opponent_id",
            "player_team_id",
        ],
        "notes": "球队 ID；视角不同（主客/对手/球员所属队）",
    },
    {
        "id": "team_labels",
        "columns": [
            "team_name",
            "home_team_name",
            "away_team_name",
            "opponent_name",
            "player_team_name",
        ],
        "notes": "球队名称冗余列",
    },
    {
        "id": "match_ref",
        "columns": ["match_id", "match_name", "match_date"],
        "notes": "比赛引用",
    },
    {
        "id": "score_team_perspective",
        "columns": ["goals_for", "goals_against", "goal_differential"],
        "notes": "球队相对视角进球",
    },
    {
        "id": "score_match_perspective",
        "columns": [
            "home_team_score",
            "away_team_score",
            "home_team_score_margin",
            "away_team_score_margin",
        ],
        "notes": "比赛主客绝对比分",
    },
    {
        "id": "win_flags",
        "columns": [
            "home_team_win",
            "away_team_win",
            "win",
            "lose",
            "draw",
        ],
        "notes": "胜负标志；matches 主客 vs team_appearances 当前队",
    },
    {
        "id": "penalty_shootout",
        "columns": [
            "penalties_for",
            "penalties_against",
            "home_team_score_penalties",
            "away_team_score_penalties",
        ],
        "notes": "点球大战比分",
    },
]

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BRONZE_DIR = REPO_ROOT / "data" / "bronze" / "worldcup"

FK_CHECKS: list[dict[str, str]] = [
    {
        "child_file": "goals.csv",
        "child_col": "match_id",
        "parent_file": "matches.csv",
        "parent_col": "match_id",
    },
    {
        "child_file": "goals.csv",
        "child_col": "player_id",
        "parent_file": "players.csv",
        "parent_col": "player_id",
    },
    {
        "child_file": "squads.csv",
        "child_col": "player_id",
        "parent_file": "players.csv",
        "parent_col": "player_id",
    },
    {
        "child_file": "squads.csv",
        "child_col": "team_id",
        "parent_file": "teams.csv",
        "parent_col": "team_id",
    },
    {
        "child_file": "matches.csv",
        "child_col": "home_team_id",
        "parent_file": "teams.csv",
        "parent_col": "team_id",
    },
    {
        "child_file": "team_appearances.csv",
        "child_col": "match_id",
        "parent_file": "matches.csv",
        "parent_col": "match_id",
    },
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def profile_file(path: Path) -> dict[str, Any]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    # Treat empty strings as null for stats
    df = df.replace("", pd.NA)

    column_stats: dict[str, Any] = {}
    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        nunique = int(series.nunique(dropna=True))
        stat: dict[str, Any] = {
            "null_count": null_count,
            "null_pct": round(null_count / len(df) * 100, 2) if len(df) else 0.0,
            "nunique": nunique,
        }
        if nunique <= max(20, len(df)):
            stat["is_unique_key_candidate"] = nunique == len(df) and null_count == 0
        column_stats[col] = stat

    return {
        "name": path.name,
        "sha256": file_sha256(path),
        "row_count": len(df),
        "columns": list(df.columns),
        "column_stats": column_stats,
    }


def build_column_index(files: list[dict[str, Any]]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for entry in files:
        for col in entry["columns"]:
            index[col].append(entry["name"])
    return {key: sorted(values) for key, values in sorted(index.items())}


def build_semantic_groups(column_index: dict[str, list[str]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for group in SEMANTIC_GROUPS:
        present = [col for col in group["columns"] if col in column_index]
        if not present:
            continue
        groups.append(
            {
                "id": group["id"],
                "notes": group["notes"],
                "columns": present,
                "files_by_column": {col: column_index[col] for col in present},
            }
        )
    return groups


def run_fk_checks(
    bronze_dir: Path, frames: dict[str, pd.DataFrame]
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for spec in FK_CHECKS:
        child_name = spec["child_file"]
        parent_name = spec["parent_file"]
        if child_name not in frames or parent_name not in frames:
            continue
        child = frames[child_name][spec["child_col"]].astype(str)
        parent_keys = set(frames[parent_name][spec["parent_col"]].astype(str))
        orphans = child[~child.isin(parent_keys) & child.notna() & (child != "")]
        results.append(
            {
                **spec,
                "orphan_count": int(orphans.shape[0]),
                "sample_orphans": orphans.head(3).tolist(),
            }
        )
    return results


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# World Cup Bronze — Profile Report",
        "",
        f"- **Generated**: {manifest['generated_at']}",
        f"- **Bronze dir**: `{manifest['bronze_dir']}`",
        f"- **Files**: {manifest['file_count']}",
        "",
        "## File inventory",
        "",
        "| File | Rows | SHA256 (short) | Columns |",
        "| :--- | ---: | :--- | ---: |",
    ]
    for entry in manifest["files"]:
        short_hash = entry["sha256"][:12]
        lines.append(
            f"| {entry['name']} | {entry['row_count']} | `{short_hash}…` | {len(entry['columns'])} |"
        )

    lines.extend(["", "## Semantic alias groups", ""])
    for group in manifest["semantic_groups"]:
        cols = ", ".join(f"`{c}`" for c in group["columns"])
        lines.append(f"### {group['id']}")
        lines.append(f"- {group['notes']}")
        lines.append(f"- Columns: {cols}")
        lines.append("")

    lines.extend(["## FK spot checks", "", "| Child | Parent | Orphans |", "| :--- | :--- | ---: |"])
    for check in manifest["fk_checks"]:
        child = f"{check['child_file']}.{check['child_col']}"
        parent = f"{check['parent_file']}.{check['parent_col']}"
        lines.append(f"| {child} | {parent} | {check['orphan_count']} |")

    lines.extend(
        [
            "",
            "## High-frequency shared columns",
            "",
            "| Column | # Files |",
            "| :--- | ---: |",
        ]
    )
    for col, files in manifest["column_index"].items():
        if len(files) >= 8:
            lines.append(f"| `{col}` | {len(files)} |")

    lines.append("")
    return "\n".join(lines)


def profile_directory(bronze_dir: Path, output_dir: Path | None = None) -> dict[str, Any]:
    bronze_dir = bronze_dir.resolve()
    if not bronze_dir.is_dir():
        raise FileNotFoundError(f"Bronze directory not found: {bronze_dir}")

    csv_paths = sorted(bronze_dir.glob("*.csv"))
    if not csv_paths:
        raise ValueError(f"No CSV files in {bronze_dir}")

    out_dir = (output_dir or bronze_dir / "_profile").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = [profile_file(path) for path in csv_paths]
    column_index = build_column_index(files)

    frames: dict[str, pd.DataFrame] = {}
    for path in csv_paths:
        frames[path.name] = pd.read_csv(path, dtype=str, keep_default_na=False).replace(
            "", pd.NA
        )

    manifest: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "bronze_dir": str(bronze_dir),
        "file_count": len(files),
        "files": files,
        "column_index": column_index,
        "semantic_groups": build_semantic_groups(column_index),
        "fk_checks": run_fk_checks(bronze_dir, frames),
    }

    manifest_path = out_dir / "manifest.json"
    report_path = out_dir / "report.md"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    report_path.write_text(render_report(manifest), encoding="utf-8")

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile World Cup Bronze CSV files.")
    parser.add_argument(
        "bronze_dir",
        nargs="?",
        default=str(DEFAULT_BRONZE_DIR),
        help=f"Directory containing *.csv (default: {DEFAULT_BRONZE_DIR})",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: <bronze_dir>/_profile)",
    )
    args = parser.parse_args(argv)

    try:
        manifest = profile_directory(Path(args.bronze_dir), Path(args.output) if args.output else None)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out_dir = Path(args.output) if args.output else Path(args.bronze_dir) / "_profile"
    print(f"profiled {manifest['file_count']} files -> {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
