from __future__ import annotations

import pandas as pd

from data import _aggregate_symbol


def test_macro_aggregation_requires_all_three_m5_bars() -> None:
    timestamps = pd.to_datetime(
        [
            "2026-01-05T00:00:00Z",
            "2026-01-05T00:05:00Z",
            "2026-01-05T00:10:00Z",
            "2026-01-05T00:15:00Z",
            "2026-01-05T00:25:00Z",
        ],
        utc=True,
    )
    frame = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "dollaridxusd_available": True,
            "dollaridxusd_mid_open": [100, 101, 102, 103, 105],
            "dollaridxusd_mid_high": [101, 102, 103, 104, 106],
            "dollaridxusd_mid_low": [99, 100, 101, 102, 104],
            "dollaridxusd_mid_close": [100.5, 101.5, 102.5, 103.5, 105.5],
            "dollaridxusd_mid_tick_count": 1.0,
        }
    )
    result = _aggregate_symbol(frame, "DOLLARIDXUSD")
    assert len(result) == 1
    assert result.iloc[0]["timestamp_utc"] == pd.Timestamp("2026-01-05T00:15:00Z")
    assert result.iloc[0]["dollaridxusd_close"] == 102.5


def test_unavailable_macro_rows_are_not_forward_filled() -> None:
    timestamps = pd.date_range("2026-01-05", periods=3, freq="5min", tz="UTC")
    frame = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "ustbondtrusd_available": [True, False, True],
            "ustbondtrusd_mid_open": [100.0, None, 101.0],
            "ustbondtrusd_mid_high": [100.1, None, 101.1],
            "ustbondtrusd_mid_low": [99.9, None, 100.9],
            "ustbondtrusd_mid_close": [100.0, None, 101.0],
            "ustbondtrusd_mid_tick_count": [1.0, None, 1.0],
        }
    )
    assert _aggregate_symbol(frame, "USTBONDTRUSD").empty
