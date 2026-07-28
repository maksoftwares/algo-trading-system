from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from download_neutral_kraken_eurusd import (  # noqa: E402
    aggregate_m5,
    date_window,
    filter_window,
    parse_page,
    request_url,
)


def payload() -> bytes:
    return json.dumps(
        {
            "error": [],
            "result": {
                "EUR/USD": [
                    [
                        "1.10000",
                        "10.0",
                        1735688701.25,
                        "b",
                        "l",
                        "",
                        101,
                    ],
                    [
                        "1.10010",
                        "5.0",
                        1735688702.5,
                        "s",
                        "m",
                        "",
                        102,
                    ],
                ],
                "last": "1735688702500000000",
            },
        }
    ).encode()


def test_page_parser_preserves_reported_side_and_cursor() -> None:
    frame, cursor = parse_page(payload())
    assert cursor == "1735688702500000000"
    assert frame["reported_side"].tolist() == ["b", "s"]
    assert frame["trade_id"].tolist() == [101, 102]
    assert frame["trade_time_utc"].is_monotonic_increasing


def test_window_is_prior_hour_needed_by_four_clocks() -> None:
    start, end = date_window("2025-01-01")
    assert start == pd.Timestamp("2024-12-31T23:45:00Z")
    assert end == pd.Timestamp("2025-01-01T00:45:00Z")
    assert end - start == pd.Timedelta(hours=1)


def test_filter_window_excludes_end_boundary() -> None:
    frame, _ = parse_page(payload())
    start = pd.Timestamp("2024-12-31T23:45:00Z")
    end = frame["trade_time_utc"].iloc[1]
    filtered = filter_window(frame, start, end)
    assert filtered["trade_id"].tolist() == [101]


def test_filter_window_can_represent_zero_trade_date() -> None:
    frame, _ = parse_page(payload())
    start = pd.Timestamp("2025-01-02T00:00:00Z")
    filtered = filter_window(
        frame, start, start + pd.Timedelta(hours=1)
    )
    assert filtered.empty
    assert list(filtered.columns) == list(frame.columns)


def test_aggregate_m5_builds_reported_side_imbalance() -> None:
    frame, _ = parse_page(payload())
    output = aggregate_m5(frame)
    assert len(output) == 1
    expected_buy = 1.1 * 10.0
    expected_sell = 1.1001 * 5.0
    expected = (
        expected_buy - expected_sell
    ) / (expected_buy + expected_sell)
    assert abs(output["reported_side_imbalance"].iloc[0] - expected) < 1e-12
    assert output["trade_count"].iloc[0] == 2
    assert output["market_order_count"].iloc[0] == 1


def test_request_is_login_free_public_trades_endpoint() -> None:
    url = request_url("123")
    assert url.startswith(
        "https://api.kraken.com/0/public/Trades?"
    )
    assert "since=123" in url
    assert "pair=EURUSD" in url
