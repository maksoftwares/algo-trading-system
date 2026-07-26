from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.snapshot import completed_hour_floor, hour_range, parse_utc


def test_hour_range_is_end_exclusive() -> None:
    start = parse_utc("2026-07-01T00:00:00Z")
    end = parse_utc("2026-07-01T03:00:00Z")
    result = hour_range(start, end)
    assert len(result) == 3
    assert result[-1] == datetime(2026, 7, 1, 2, tzinfo=UTC)


def test_completed_hour_floor_excludes_open_hour() -> None:
    now = datetime(2026, 7, 22, 15, 56, 10, tzinfo=UTC)
    assert completed_hour_floor(now) == datetime(2026, 7, 22, 15, tzinfo=UTC)


def test_hour_range_rejects_non_aligned_boundary() -> None:
    with pytest.raises(ValueError, match="hour aligned"):
        hour_range(
            parse_utc("2026-07-01T00:00:00Z"),
            parse_utc("2026-07-01T03:01:00Z"),
        )
