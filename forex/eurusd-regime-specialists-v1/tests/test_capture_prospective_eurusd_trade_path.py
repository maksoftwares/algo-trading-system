from __future__ import annotations

import json

import pandas as pd

from capture_prospective_eurusd_trade_path import (
    capture_trade_path,
    path_capture_ready,
    required_path_hours,
)


SIGNAL_ID = "a" * 64


def _hour_payload(hour: pd.Timestamp, *, omit_last: bool = False) -> bytes:
    count = 11 if omit_last else 12
    return json.dumps(
        {
            "timestamp": int(hour.timestamp() * 1000),
            "multiplier": 0.00001,
            "bid": 1.10000,
            "ask": 1.10010,
            "times": [0] + [300000] * (count - 1),
            "bids": [0] * count,
            "asks": [0] * count,
            "bidVolumes": [1.0] * count,
            "askVolumes": [1.0] * count,
        }
    ).encode("utf-8")


def test_path_waits_until_deadline_plus_capture_lag(tmp_path) -> None:
    calls = []

    def fetcher(symbol, hour):
        calls.append((symbol, hour))
        raise AssertionError("Network must not be called")

    result = capture_trade_path(
        SIGNAL_ID,
        "2026-08-12T12:50:00Z",
        tmp_path,
        now_utc="2026-08-13T00:50:59Z",
        fetcher=fetcher,
    )
    assert result["status"] == "WAITING_FOR_12H_PATH_COMPLETION"
    assert result["network_request_made"] is False
    assert calls == []
    assert path_capture_ready(
        "2026-08-12T12:50:00Z",
        "2026-08-13T00:51:00Z",
    )


def test_complete_path_is_immutable_and_idempotent(tmp_path) -> None:
    calls = []
    observed = pd.Timestamp("2026-08-13T00:51:01Z")

    def fetcher(symbol, hour):
        calls.append((symbol, hour))
        return _hour_payload(hour), {
            "symbol": symbol,
            "hour_utc": hour,
            "url": f"https://example.invalid/{hour:%H}",
            "request_started_utc": observed,
            "request_finished_utc": observed,
            "http_date_utc": observed,
            "observed_at_utc": observed,
            "response_headers": {},
        }

    first = capture_trade_path(
        SIGNAL_ID,
        "2026-08-12T12:50:00Z",
        tmp_path,
        now_utc=observed,
        fetcher=fetcher,
    )
    repeated = capture_trade_path(
        SIGNAL_ID,
        "2026-08-12T12:50:00Z",
        tmp_path,
        now_utc=observed,
        fetcher=fetcher,
    )
    assert first["status"] == "TRADE_PATH_CAPTURED"
    assert first["path_rows"] == 144
    assert first["manifest_sha256"] == repeated["manifest_sha256"]
    assert repeated["network_request_made"] is False
    assert len(calls) == 13
    assert len(required_path_hours("2026-08-12T12:50:00Z")) == 13


def test_missing_m5_bar_never_becomes_a_closed_path(tmp_path) -> None:
    observed = pd.Timestamp("2026-08-13T00:51:01Z")

    def fetcher(symbol, hour):
        return _hour_payload(
            hour,
            omit_last=hour
            == pd.Timestamp("2026-08-12T18:00:00Z"),
        ), {
            "symbol": symbol,
            "hour_utc": hour,
            "url": "https://example.invalid/missing",
            "request_started_utc": observed,
            "request_finished_utc": observed,
            "http_date_utc": observed,
            "observed_at_utc": observed,
            "response_headers": {},
        }

    result = capture_trade_path(
        "b" * 64,
        "2026-08-12T12:50:00Z",
        tmp_path,
        now_utc=observed,
        fetcher=fetcher,
    )
    assert result["status"] == "TRADE_PATH_INCOMPLETE"
    assert result["path_rows"] == 143
    assert result["missing_m5_timestamps"] == [
        "2026-08-12T18:55:00+00:00"
    ]
