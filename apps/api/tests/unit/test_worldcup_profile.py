"""Unit tests for World Cup Bronze profile script."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PROFILE_SCRIPT = REPO_ROOT / "scripts" / "etl" / "worldcup" / "profile.py"
FIXTURES_DIR = REPO_ROOT / "scripts" / "etl" / "worldcup" / "fixtures"


def _load_profile_module():
    spec = importlib.util.spec_from_file_location("worldcup_bronze_profile", PROFILE_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def profile_mod():
    return _load_profile_module()


def test_profile_fixture_directory(profile_mod, tmp_path):
    manifest = profile_mod.profile_directory(FIXTURES_DIR, output_dir=tmp_path)

    assert manifest["file_count"] == 3
    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "report.md").is_file()

    names = {entry["name"] for entry in manifest["files"]}
    assert names == {"teams.csv", "matches.csv", "goals.csv"}

    saved = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert saved["column_index"]["tournament_id"] == ["goals.csv", "matches.csv"]

    match_fk = next(
        c
        for c in manifest["fk_checks"]
        if c["child_file"] == "goals.csv" and c["child_col"] == "match_id"
    )
    assert match_fk["orphan_count"] == 1
    assert "M-999-99" in match_fk["sample_orphans"]


def test_profile_missing_directory(profile_mod):
    with pytest.raises(FileNotFoundError):
        profile_mod.profile_directory(REPO_ROOT / "nonexistent-bronze-dir")


def test_profile_no_csv(profile_mod, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="No CSV"):
        profile_mod.profile_directory(empty)
