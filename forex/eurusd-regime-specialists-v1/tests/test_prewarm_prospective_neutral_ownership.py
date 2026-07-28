from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pytest

import prewarm_prospective_neutral_ownership as prewarm_module
from capture_prospective_neutral_ownership import _cached_hour
from prewarm_prospective_neutral_ownership import (
    prewarm_capture,
    prewarm_status,
)

SYMBOLS = (
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "DOLLARIDXUSD",
    "USTBONDTRUSD",
)
ELIGIBLE_DATE = pd.Timestamp("2026-08-07T00:00:00Z")
HOURS = [
    pd.Timestamp("2026-08-06T10:00:00Z"),
    pd.Timestamp("2026-08-06T11:00:00Z"),
]
OBSERVED = pd.Timestamp("2026-08-06T12:01:00Z")


def _payload(
    hour: pd.Timestamp,
    symbol: str,
) -> bytes:
    if symbol == "USDJPY":
        initial = 150.0
        multiplier = 0.001
    elif symbol in {"DOLLARIDXUSD", "USTBONDTRUSD"}:
        initial = 100.0
        multiplier = 0.001
    else:
        initial = 1.1
        multiplier = 0.00001
    return json.dumps(
        {
            "timestamp": int(hour.timestamp() * 1000),
            "multiplier": multiplier,
            "bid": initial,
            "ask": initial + 10 * multiplier,
            "times": [0, 300000, 300000],
            "bids": [0, 1, -1],
            "asks": [0, 1, -1],
            "bidVolumes": [1.0, 1.0, 1.0],
            "askVolumes": [1.0, 1.0, 1.0],
        }
    ).encode()


def _fetcher(calls: list[tuple[str, pd.Timestamp]]):
    def fetch(symbol: str, hour: pd.Timestamp):
        calls.append((symbol, hour))
        return _payload(hour, symbol), {
            "symbol": symbol,
            "hour_utc": hour,
            "url": f"https://example.invalid/{symbol}/{hour:%Y%m%d%H}",
            "request_started_utc": OBSERVED,
            "request_finished_utc": OBSERVED,
            "http_date_utc": OBSERVED,
            "observed_at_utc": OBSERVED,
            "response_headers": {},
        }

    return fetch


@pytest.fixture
def short_window(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        prewarm_module,
        "required_hours",
        lambda eligible_date, lookback_calendar_days: HOURS,
    )


def test_status_is_network_free_and_exposes_full_cold_start(
    tmp_path: Path,
) -> None:
    result = prewarm_status(
        "2026-07-29",
        tmp_path,
        now_utc="2026-07-28T15:20:00Z",
    )
    assert result["total_required_symbol_hours"] == 7200
    assert result["cached_symbol_hours"] == 0
    assert result["missing_safe_symbol_hours"] > 7000
    assert result["not_yet_safe_symbol_hours"] > 0
    assert result["network_request_made"] is False
    assert result["ownership_record_created"] is False
    assert result["broker_action_allowed"] is False


def test_capture_populates_exact_primary_cache_and_is_idempotent(
    tmp_path: Path,
    short_window: None,
) -> None:
    calls: list[tuple[str, pd.Timestamp]] = []
    first = prewarm_capture(
        ELIGIBLE_DATE,
        tmp_path,
        now_utc=OBSERVED,
        max_new_requests=20,
        fetcher=_fetcher(calls),
    )
    assert first["status"] == "PREWARM_COMPLETE"
    assert first["new_cached_symbol_hours"] == 10
    assert first["cached_symbol_hours"] == 10
    assert first["network_request_attempts"] == 10
    assert len(calls) == 10
    assert not list((tmp_path / "records").glob("*.json"))
    assert not list((tmp_path / "manifests").glob("*.json"))
    assert len(list((tmp_path / "prewarm_manifests").glob("*.json"))) == 1
    for symbol in SYMBOLS:
        for hour in HOURS:
            assert _cached_hour(tmp_path, symbol, hour) is not None

    second_calls: list[tuple[str, pd.Timestamp]] = []
    second = prewarm_capture(
        ELIGIBLE_DATE,
        tmp_path,
        now_utc=OBSERVED,
        max_new_requests=20,
        fetcher=_fetcher(second_calls),
    )
    assert second["status"] == "PREWARM_COMPLETE"
    assert second["network_request_made"] is False
    assert second_calls == []
    assert len(list((tmp_path / "prewarm_manifests").glob("*.json"))) == 1


def test_incomplete_hour_is_never_requested(
    tmp_path: Path,
    short_window: None,
) -> None:
    calls: list[tuple[str, pd.Timestamp]] = []
    result = prewarm_capture(
        ELIGIBLE_DATE,
        tmp_path,
        now_utc="2026-08-06T11:30:00Z",
        max_new_requests=20,
        fetcher=_fetcher(calls),
    )
    assert result["new_cached_symbol_hours"] == 5
    assert len(calls) == 5
    assert {hour for _, hour in calls} == {HOURS[0]}
    assert result["not_yet_safe_symbol_hours"] == 5


def test_transient_failure_uses_only_frozen_retry_budget(
    tmp_path: Path,
    short_window: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(prewarm_module.time, "sleep", lambda seconds: None)
    counts: defaultdict[tuple[str, pd.Timestamp], int] = defaultdict(int)

    def flaky(symbol: str, hour: pd.Timestamp):
        key = (symbol, hour)
        counts[key] += 1
        if counts[key] == 1:
            raise TimeoutError("synthetic transient failure")
        return _fetcher([])(symbol, hour)

    result = prewarm_capture(
        ELIGIBLE_DATE,
        tmp_path,
        now_utc="2026-08-06T11:30:00Z",
        max_new_requests=20,
        fetcher=flaky,
    )
    assert result["new_cached_symbol_hours"] == 5
    assert result["network_request_attempts"] == 10
    assert set(counts.values()) == {2}


def test_cached_hash_tamper_fails_closed(
    tmp_path: Path,
    short_window: None,
) -> None:
    prewarm_capture(
        ELIGIBLE_DATE,
        tmp_path,
        now_utc=OBSERVED,
        max_new_requests=20,
        fetcher=_fetcher([]),
    )
    raw_path = next((tmp_path / "raw" / "EURUSD").glob("*.json"))
    raw_path.write_bytes(raw_path.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="hash drift"):
        prewarm_status(
            ELIGIBLE_DATE,
            tmp_path,
            now_utc=OBSERVED,
        )


def test_request_limit_cannot_exceed_frozen_batch_cap(
    tmp_path: Path,
    short_window: None,
) -> None:
    with pytest.raises(ValueError, match="1 through 720"):
        prewarm_capture(
            ELIGIBLE_DATE,
            tmp_path,
            now_utc=OBSERVED,
            max_new_requests=721,
            fetcher=_fetcher([]),
        )
