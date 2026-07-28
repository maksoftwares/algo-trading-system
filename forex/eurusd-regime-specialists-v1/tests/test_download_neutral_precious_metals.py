from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from download_neutral_precious_metals import (  # noqa: E402
    decode_to_m5,
    required_hours,
    validate_payload,
)


def payload() -> bytes:
    return json.dumps(
        {
            "timestamp": 1704067200000,
            "multiplier": 0.001,
            "ask": 24.002,
            "bid": 24.000,
            "times": [1000, 1000, 299000, 1000],
            "asks": [1, 1, 2, -1],
            "bids": [1, 1, 2, -1],
            "askVolumes": [1, 1, 1, 1],
            "bidVolumes": [1, 1, 1, 1],
        }
    ).encode("utf-8")


def test_required_hours_cover_prior_22_23_and_current_00() -> None:
    actual = required_hours(["2024-01-05"])
    assert actual == [
        pd.Timestamp("2024-01-04T22:00:00Z"),
        pd.Timestamp("2024-01-04T23:00:00Z"),
        pd.Timestamp("2024-01-05T00:00:00Z"),
    ]


def test_decoder_uses_cumulative_time_and_price_deltas() -> None:
    hour = pd.Timestamp("2024-01-01T00:00:00Z")
    frame = decode_to_m5(payload(), hour)
    assert list(frame["timestamp_utc"]) == [
        pd.Timestamp("2024-01-01T00:00:00Z"),
        pd.Timestamp("2024-01-01T00:05:00Z"),
    ]
    assert frame.loc[0, "bid_open"] == pytest.approx(24.001)
    assert frame.loc[0, "bid_close"] == pytest.approx(24.002)
    assert frame.loc[1, "ask_open"] == pytest.approx(24.006)
    assert frame.loc[1, "ask_close"] == pytest.approx(24.005)
    assert list(frame["tick_count"]) == [2, 2]


def test_validator_rejects_wrong_hour() -> None:
    with pytest.raises(ValueError, match="Unexpected source hour"):
        validate_payload(
            payload(), pd.Timestamp("2024-01-01T01:00:00Z")
        )
