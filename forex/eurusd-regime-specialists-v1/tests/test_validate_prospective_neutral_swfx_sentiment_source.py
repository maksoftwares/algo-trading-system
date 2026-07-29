from __future__ import annotations

import json
from pathlib import Path

import pytest

from capture_prospective_neutral_swfx_sentiment_source import capture
from validate_prospective_neutral_swfx_sentiment_source import (
    build_validation_status,
    verify_validation_locks,
)


def _payload() -> bytes:
    row = {
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
    return ("callback(" + json.dumps([row]) + ");").encode()


def _fetcher(*args: object, **kwargs: object) -> dict[str, object]:
    del args, kwargs
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


def test_empty_validation_waits_without_network(tmp_path: Path) -> None:
    lock = verify_validation_locks()
    assert lock["validation_implementation"]["network_request_allowed"] is False
    result = build_validation_status(
        tmp_path,
        evaluated_at_utc="2026-07-29T06:31:00Z",
    )
    assert result["status"] == "ACCUMULATING_PROSPECTIVE_SOURCE_EVIDENCE"
    assert result["expected_scheduled_captures_due"] == 0
    assert result["immutable_manifests_replayed"] == 0
    assert result["source_admitted"] is False
    assert result["network_request_made"] is False
    assert result["broker_action_allowed"] is False


def test_independent_validator_replays_raw_capture(tmp_path: Path) -> None:
    captured = capture(
        "2026-07-29T06:32:00Z",
        tmp_path,
        now_utc="2026-07-29T06:32:01Z",
        fetcher=_fetcher,
    )
    assert captured["status"] == "VALID_SOURCE_CAPTURE"
    result = build_validation_status(
        tmp_path,
        evaluated_at_utc="2026-07-29T06:38:00Z",
    )
    assert result["expected_scheduled_captures_due"] == 1
    assert result["immutable_manifests_replayed"] == 1
    assert result["valid_source_captures"] == 1
    assert result["schedule_coverage_ratio"] == 1.0
    assert result["valid_capture_ratio"] == 1.0
    assert result["distinct_eurusd_states"] == 1
    assert result["source_admitted"] is False
    assert result["eurusd_prices_loaded"] is False
    assert result["eurusd_pnl_loaded"] is False


def test_raw_tampering_fails_closed(tmp_path: Path) -> None:
    captured = capture(
        "2026-07-29T06:32:00Z",
        tmp_path,
        now_utc="2026-07-29T06:32:01Z",
        fetcher=_fetcher,
    )
    raw_path = tmp_path / captured["raw"]["relative_path"]
    raw_path.write_bytes(raw_path.read_bytes() + b" ")
    with pytest.raises(RuntimeError, match="raw bytes/hash drift"):
        build_validation_status(
            tmp_path,
            evaluated_at_utc="2026-07-29T06:38:00Z",
        )


def test_missing_due_slot_counts_as_failure(tmp_path: Path) -> None:
    result = build_validation_status(
        tmp_path,
        evaluated_at_utc="2026-07-29T06:38:00Z",
    )
    assert result["expected_scheduled_captures_due"] == 1
    assert result["immutable_manifests_replayed"] == 0
    assert result["schedule_coverage_ratio"] == 0.0
    assert result["valid_capture_ratio"] == 0.0
    assert result["maximum_consecutive_failed_scheduled_captures"] == 1
