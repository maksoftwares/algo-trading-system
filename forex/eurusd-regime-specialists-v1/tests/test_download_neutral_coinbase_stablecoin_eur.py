from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from download_neutral_coinbase_stablecoin_eur import (  # noqa: E402
    candle_url,
    date_window,
    parse_candles,
    parse_product,
)


def test_date_window_is_exactly_twelve_completed_m5_bars() -> None:
    start, end = date_window("2025-01-02")
    assert start == pd.Timestamp("2025-01-01T23:45:00Z")
    assert end == pd.Timestamp("2025-01-02T00:45:00Z")
    assert (end - start) == pd.Timedelta(minutes=60)
    url = candle_url("USDC-EUR", "2025-01-02")
    assert "granularity=300" in url


def test_candle_parser_filters_inclusive_endpoint_bar() -> None:
    rows = []
    start = pd.Timestamp("2025-01-01T23:45:00Z")
    for offset in range(13):
        stamp = start + pd.Timedelta(minutes=5 * offset)
        rows.append(
            [
                int(stamp.timestamp()),
                0.96,
                0.97,
                0.965,
                0.966,
                100.0 + offset,
            ]
        )
    payload = json.dumps(list(reversed(rows))).encode("utf-8")
    frame = parse_candles(payload, "USDC-EUR", "2025-01-02")
    assert len(frame) == 12
    assert frame["open_time_utc"].min() == start
    assert frame["open_time_utc"].max() == pd.Timestamp(
        "2025-01-02T00:40:00Z"
    )
    assert frame["base_volume"].gt(0).all()


def test_product_schema_is_pinned() -> None:
    payload = json.dumps(
        {
            "id": "USDC-EUR",
            "base_currency": "USDC",
            "quote_currency": "EUR",
            "quote_increment": "0.0001",
            "base_increment": "0.01",
            "status": "online",
        }
    ).encode("utf-8")
    product = parse_product(payload, "USDC-EUR")
    assert product["quote_currency"] == "EUR"
