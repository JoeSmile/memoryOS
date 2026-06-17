"""Token usage repository unit tests (EP09 4.1)."""

from datetime import date, datetime, timezone

from app.repositories.token_usage_repository import utc_day_bounds


def test_utc_day_bounds():
    start, end = utc_day_bounds(date(2026, 6, 17))
    assert start == datetime(2026, 6, 17, 0, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 18, 0, 0, 0, tzinfo=timezone.utc)
