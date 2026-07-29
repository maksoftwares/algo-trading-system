from __future__ import annotations

import json
from pathlib import Path

import pytest

from capture_prospective_neutral_swfx_sentiment_source import (
    capture,
    is_scheduled_slot,
    load_and_verify_preregistration,
    next_scheduled_slot,
    normalize_eurusd_row,
    parse_jsonp_rows,
    scheduled_slots_for_date,
    status,
)


def _row() -> dict[str, object]:
    return {
        "name": "EUR/USD",
        "last_long": "-12.4",
        "last_short": "12.4",
        "sixhours_long": "-12.66",
        "sixhours_short": "12.66",
        "oneday_long": "-16.64",
        "oneday_short": "16.64",
        "fivedays_long": "-14.22",
        "fivedays_short": "14.22",
    }


def _payload() -> bytes:
    return ("callback(" + json.dumps([_row()]) + ");").encode()


def test_frozen_schedule_is_half_hourly_on_weekdays() -> None:
    config, _ = load_and_verify_preregistration()
    slots = scheduled_slots_for_date("2026-07-29T00:00:00Z", config)
    assert len(slots) == 48
    assert slots[0].isoformat() == "2026-07-29T00:02:00+00:00"
    assert slots[-1].isoformat() == "2026-07-29T23:32:00+00:00"
    assert is_scheduled_slot("2026-07-29T06:32:00Z", config)
    assert not is_scheduled_slot("2026-07-29T06:30:00Z", config)
    assert scheduled_slots_for_date("2026-08-01T00:00:00Z", config) == []
    assert next_scheduled_slot(
        "2026-07-31T23:33:00Z", config
    ).isoformat() == "2026-08-03T00:02:00+00:00"


def test_jsonp_parser_and_schema_are_fail_closed() -> None:
    config, _ = load_and_verify_preregistration()
    rows = parse_jsonp_rows(_payload())
    normalized = normalize_eurusd_row(rows, config)
    assert normalized["name"] == "EUR/USD"
    assert normalized["last_long"] == -12.4
    with pytest.raises(ValueError, match="exactly one"):
        normalize_eurusd_row(rows + rows, config)
    broken = _row()
    broken["last_short"] = "9.0"
    with pytest.raises(ValueError, match="long/short pair"):
        normalize_eurusd_row([broken], config)
    with pytest.raises(ValueError, match="JSON array"):
        parse_jsonp_rows(b"not jsonp")


def test_capture_before_clock_waits_without_network(tmp_path: Path) -> None:
    calls = 0

    def fetcher(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal calls
        del args, kwargs
        calls += 1
        raise AssertionError("network must not be called")

    result = capture(
        "2026-07-29T06:32:00Z",
        tmp_path,
        now_utc="2026-07-29T06:31:59Z",
        fetcher=fetcher,
    )
    assert result["status"] == "WAITING_FOR_SCHEDULED_CLOCK"
    assert calls == 0
    assert not list(tmp_path.rglob("*"))
    census = status(tmp_path, now_utc="2026-07-29T05:30:00Z")
    assert census["next_scheduled_capture_utc"] == (
        "2026-07-29T06:32:00+00:00"
    )


def test_valid_capture_is_immutable_source_only(tmp_path: Path) -> None:
    calls = 0

    def fetcher(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal calls
        del args, kwargs
        calls += 1
        return {
            "request_started_at_utc": "2026-07-29T06:32:01+00:00",
            "response_completed_at_utc": "2026-07-29T06:32:02+00:00",
            "request_url": "https://example.invalid",
            "final_url": "https://example.invalid",
            "request_headers": {},
            "response_headers": [["Date", "Wed, 29 Jul 2026 06:32:02 GMT"]],
            "http_status": 200,
            "payload": _payload(),
        }

    result = capture(
        "2026-07-29T06:32:00Z",
        tmp_path,
        now_utc="2026-07-29T06:32:01Z",
        fetcher=fetcher,
    )
    assert result["status"] == "VALID_SOURCE_CAPTURE"
    assert result["provider_settlement_timestamp_utc"] is None
    assert result["eurusd_prices_loaded"] is False
    assert result["eurusd_pnl_loaded"] is False
    assert result["direction_mapping_applied"] is False
    assert result["trade_created"] is False
    repeated = capture(
        "2026-07-29T06:32:00Z",
        tmp_path,
        now_utc="2026-07-29T06:33:00Z",
        fetcher=fetcher,
    )
    assert repeated["manifest_sha256"] == result["manifest_sha256"]
    assert calls == 1
    census = status(tmp_path, now_utc="2026-07-29T06:34:00Z")
    assert census["valid_source_captures"] == 1
    assert census["distinct_eurusd_states"] == 1
    assert census["source_admitted"] is False


def test_late_capture_does_not_backfill_or_call_network(
    tmp_path: Path,
) -> None:
    calls = 0

    def fetcher(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal calls
        del args, kwargs
        calls += 1
        raise AssertionError("network must not be called")

    result = capture(
        "2026-07-29T06:32:00Z",
        tmp_path,
        now_utc="2026-07-29T06:37:01Z",
        fetcher=fetcher,
    )
    assert result["status"] == "MISSED_NO_LATE_BACKFILL"
    assert calls == 0
    assert not list(tmp_path.rglob("*"))
