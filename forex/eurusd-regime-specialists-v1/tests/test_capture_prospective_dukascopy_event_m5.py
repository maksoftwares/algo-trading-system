from __future__ import annotations

import json

import pandas as pd

from capture_prospective_dukascopy_event_m5 import (
    build_completed_m5,
    capture_event,
    decode_ticks,
    extract_event_feature,
    observation_window,
    required_hours,
)


def _payload(hour: str, prices: list[int]) -> bytes:
    start_ms = int(pd.Timestamp(hour).timestamp() * 1000)
    return json.dumps(
        {
            "timestamp": start_ms,
            "multiplier": 0.00001,
            "bid": 1.10000,
            "ask": 1.10010,
            "times": [0, 300000, 300000, 300000, 300000][
                : len(prices)
            ],
            "bids": prices,
            "asks": prices,
            "bidVolumes": [1.0] * len(prices),
            "askVolumes": [1.0] * len(prices),
        }
    ).encode("utf-8")


def _event_payload(hour: str) -> bytes:
    start_ms = int(pd.Timestamp(hour).timestamp() * 1000)
    return json.dumps(
        {
            "timestamp": start_ms,
            "multiplier": 0.00001,
            "bid": 1.10000,
            "ask": 1.10010,
            "times": [1500000, 300000, 300000, 300000],
            "bids": [0, 1, 1, 1],
            "asks": [0, 1, 1, 1],
            "bidVolumes": [1.0] * 4,
            "askVolumes": [1.0] * 4,
        }
    ).encode("utf-8")


def _bars(offset: float = 0.0) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-08-07T12:25:00Z", periods=4, freq="5min"
    )
    closes = [1.0, 1.1, 1.2, 1.3]
    return pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "mid_open": [value + offset for value in closes],
            "mid_high": [
                value + offset + 0.01 for value in closes
            ],
            "mid_low": [
                value + offset - 0.01 for value in closes
            ],
            "mid_close": [value + offset for value in closes],
        }
    )


def test_decoder_reconstructs_cumulative_ticks() -> None:
    raw = _payload("2026-08-07T12:00:00Z", [0, 1, -1])
    ticks = decode_ticks(
        raw, "EURUSD", "2026-08-07T12:00:00Z"
    )
    assert list(ticks["bid"]) == [1.1, 1.10001, 1.1]
    assert (ticks["ask"] >= ticks["bid"]).all()


def test_incomplete_m5_bar_is_excluded() -> None:
    raw = _payload(
        "2026-08-07T12:00:00Z", [0, 1, 1, 1, 1]
    )
    ticks = decode_ticks(
        raw, "EURUSD", "2026-08-07T12:00:00Z"
    )
    bars = build_completed_m5(
        ticks, "2026-08-07T12:19:59Z"
    )
    assert list(bars["timestamp_utc"]) == list(
        pd.date_range(
            "2026-08-07T12:00:00Z", periods=3, freq="5min"
        )
    )


def test_event_feature_uses_baseline_and_three_completed_bars() -> None:
    feature, coverage = extract_event_feature(
        {
            "EURUSD": _bars(),
            "DOLLARIDXUSD": _bars(10.0),
            "USTBONDTRUSD": _bars(20.0),
        },
        "2026-08-07T12:30:00Z",
        "2026-08-07T12:46:00Z",
    )
    assert coverage == "COMPLETE"
    assert feature["eurusd_pre_mid"].iloc[0] == 1.0
    assert feature["eurusd_post_mid"].iloc[0] == 1.3
    assert feature["dxy_pre_mid"].iloc[0] == 11.0
    assert feature["treasury_post_mid"].iloc[0] == 21.3


def test_missing_required_bar_produces_no_feature() -> None:
    incomplete = _bars().iloc[:-1]
    feature, coverage = extract_event_feature(
        {
            "EURUSD": incomplete,
            "DOLLARIDXUSD": _bars(10.0),
            "USTBONDTRUSD": _bars(20.0),
        },
        "2026-08-07T12:30:00Z",
        "2026-08-07T12:46:00Z",
    )
    assert feature.empty
    assert coverage == "EURUSD_REQUIRED_M5_MISSING"


def test_event_before_completed_window_makes_no_request(
    tmp_path,
) -> None:
    calls = []

    def fetcher(symbol, hour):
        calls.append((symbol, hour))
        raise AssertionError("Fetcher must not be called")

    result = capture_event(
        "2026-08-07T12:30:00Z",
        tmp_path,
        now_utc="2026-08-07T12:45:59Z",
        fetcher=fetcher,
    )
    assert result["network_request_made"] is False
    assert calls == []
    json.dumps(result)


def test_ready_event_persists_linked_immutable_snapshot(tmp_path) -> None:
    calls = []

    def fetcher(symbol, hour):
        calls.append((symbol, hour))
        return _event_payload("2026-08-07T12:00:00Z"), {
            "symbol": symbol,
            "hour_utc": hour,
            "url": f"https://example.invalid/{symbol}",
            "request_started_utc": pd.Timestamp(
                "2026-08-07T12:46:00Z"
            ),
            "request_finished_utc": pd.Timestamp(
                "2026-08-07T12:46:01Z"
            ),
            "http_date_utc": pd.Timestamp(
                "2026-08-07T12:46:01Z"
            ),
            "observed_at_utc": pd.Timestamp(
                "2026-08-07T12:46:01Z"
            ),
            "response_headers": {},
        }

    first = capture_event(
        "2026-08-07T12:30:00Z",
        tmp_path,
        now_utc="2026-08-07T12:46:01Z",
        fetcher=fetcher,
    )
    repeated = capture_event(
        "2026-08-07T12:30:00Z",
        tmp_path,
        now_utc="2026-08-07T12:46:01Z",
        fetcher=fetcher,
    )
    assert first["status"] == "EVENT_MARKET_FEATURE_CAPTURED"
    assert first["feature_rows"] == 1
    assert first["manifest_sha256"] == repeated["manifest_sha256"]
    assert len(calls) == 6
    assert len(list(tmp_path.glob("raw/**/*.json"))) == 3
    assert len(list(tmp_path.glob("normalized/*.parquet"))) == 1
    assert len(list(tmp_path.glob("manifests/*.json"))) == 1


def test_window_and_hour_contract_crosses_hour_safely() -> None:
    baseline, observation, completed = observation_window(
        "2026-08-07T12:58:00Z"
    )
    assert baseline == pd.Timestamp("2026-08-07T12:50:00Z")
    assert observation == pd.Timestamp("2026-08-07T13:00:00Z")
    assert completed == pd.Timestamp("2026-08-07T13:15:00Z")
    assert required_hours("2026-08-07T12:58:00Z") == [
        pd.Timestamp("2026-08-07T12:00:00Z"),
        pd.Timestamp("2026-08-07T13:00:00Z"),
    ]
