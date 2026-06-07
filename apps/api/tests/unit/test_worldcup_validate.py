"""Unit tests for World Cup Silver validation."""

from __future__ import annotations

import pytest

from app.etl.worldcup.validate import CheckResult, format_report


def test_format_report_all_pass():
    results = [
        CheckResult(name="count.wc_teams", passed=True, message="expected 88, got 88"),
        CheckResult(name="fk.wc_goals.match_id", passed=True, message="0 orphan rows"),
    ]
    report = format_report(results)
    assert "2/2 passed" in report
    assert "FAIL" not in report


def test_format_report_with_failures():
    results = [
        CheckResult(name="count.wc_teams", passed=False, message="expected 88, got 0"),
    ]
    report = format_report(results)
    assert "[FAIL]" in report
    assert "FAILED: 1 check(s)" in report


@pytest.mark.asyncio
@pytest.mark.skipif(
    __import__("os").environ.get("WC_VALIDATE_INTEGRATION") != "1",
    reason="set WC_VALIDATE_INTEGRATION=1 to run DB validation integration test",
)
async def test_run_validation_integration():
    from app.core.database import AsyncSessionLocal
    from app.etl.worldcup.validate import run_validation

    async with AsyncSessionLocal() as session:
        results = await run_validation(session)
    assert all(item.passed for item in results), format_report(results)
