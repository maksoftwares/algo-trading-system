from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_reentry_frequency_ladder import (
    build_quota_signal_mask,
)


def test_quota_mask_limits_completed_signals_per_date() -> None:
    timestamps = pd.date_range("2026-01-05T00:00Z", periods=10, freq="h")
    h1 = pd.DataFrame(
        {
            "timestamp": timestamps,
            "complete_hour": True,
            "contiguous_next": True,
            "mid_low": [1.1] * 6 + [1.0] * 4,
            "mid_close": [1.2] * 6 + [1.0] * 4,
            "body_fraction": 0.8,
            "regime": "chop",
            "atr": 0.001,
        }
    )
    candidate = {
        "reference_hours_utc": [0, 1, 2, 3, 4, 5],
        "decision_hours_utc": [6, 7, 8, 9],
        "body_fraction_minimum": 0.35,
        "owned_regime": "chop",
    }
    assert build_quota_signal_mask(h1, candidate, 1).sum() == 1
    assert build_quota_signal_mask(h1, candidate, 2).sum() == 2
    assert build_quota_signal_mask(h1, candidate, 4).sum() == 4
