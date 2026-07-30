from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_chop_exhaustion_rejection import (
    build_exhaustion_masks,
    enforce_one_open_position,
)


def test_exhaustion_mask_keeps_first_side_across_date() -> None:
    timestamps = pd.date_range("2026-01-05T10:00Z", periods=3, freq="h")
    h1 = pd.DataFrame(
        {
            "timestamp": timestamps,
            "complete_hour": True,
            "contiguous_next": True,
            "regime": "chop",
            "atr": 0.001,
            "h1_ema": 1.1000,
            "body_fraction": 0.5,
            "mid_open": [1.0990, 1.1010, 1.0990],
            "mid_high": [1.1000, 1.1010, 1.1000],
            "mid_low": [1.0990, 1.1000, 1.0990],
            "mid_close": [1.0995, 1.1005, 1.0995],
        }
    )
    hypothesis = {
        "owned_regime": "chop",
        "decision_hours_utc": [10, 11, 12],
        "envelope_atr_multiple": 0.75,
        "body_fraction_minimum": 0.35,
    }
    masks = build_exhaustion_masks(h1, hypothesis)
    assert masks["LONG"].sum() == 1
    assert masks["SHORT"].sum() == 0
    assert masks["LONG"].iloc[0]


def test_one_open_position_rejects_cross_side_overlap() -> None:
    trades = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2026-01-05T11:00Z", "2026-01-05T12:00Z"], utc=True
            ),
            "exit_time_utc": pd.to_datetime(
                ["2026-01-05T13:00Z", "2026-01-05T14:00Z"], utc=True
            ),
            "side": ["LONG", "SHORT"],
        }
    )
    accepted = enforce_one_open_position(trades)
    assert len(accepted) == 1
    assert accepted.iloc[0]["side"] == "LONG"

