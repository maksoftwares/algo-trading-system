from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_trend_pullback_continuation import (
    build_pullback_masks,
    protected_date_overlap,
)


def test_pullback_masks_are_mirrored_and_keep_first_signal_per_date() -> None:
    timestamps = pd.date_range("2026-01-05T10:00Z", periods=4, freq="h")
    h1 = pd.DataFrame(
        {
            "timestamp": timestamps,
            "complete_hour": True,
            "contiguous_next": True,
            "atr": 0.001,
            "h1_ema": 1.1000,
            "body_fraction": 0.5,
            "regime": ["trend_up", "trend_up", "trend_down", "trend_down"],
            "mid_open": [1.0995, 1.0996, 1.1005, 1.1004],
            "mid_high": [1.1010, 1.1011, 1.1010, 1.1011],
            "mid_low": [1.0990, 1.0991, 1.0990, 1.0989],
            "mid_close": [1.1005, 1.1006, 1.0995, 1.0994],
        }
    )
    hypothesis = {
        "decision_hours_utc": [10, 11, 12, 13],
        "body_fraction_minimum": 0.35,
    }
    masks = build_pullback_masks(h1, hypothesis)
    assert masks["H4_TREND_UP_H1_EMA_REJECTION_LONG"].sum() == 1
    assert masks["H4_TREND_DOWN_H1_EMA_REJECTION_SHORT"].sum() == 1
    assert masks["H4_TREND_UP_H1_EMA_REJECTION_LONG"].iloc[0]
    assert masks["H4_TREND_DOWN_H1_EMA_REJECTION_SHORT"].iloc[2]


def test_protected_date_overlap_counts_only_new_dates() -> None:
    trades = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2026-01-05T12:00Z", "2026-01-06T12:00Z"], utc=True
            )
        }
    )
    result = protected_date_overlap(
        trades, {"2026-01-05"}, broker_weekdays=10
    )
    assert result["candidate_active_dates"] == 2
    assert result["protected_overlap_dates"] == 1
    assert result["unique_dates"] == 1
    assert result["protected_overlap_share"] == 0.5
    assert result["unique_dates_per_broker_weekday"] == 0.1

