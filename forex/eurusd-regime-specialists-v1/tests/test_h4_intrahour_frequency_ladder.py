from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_intrahour_frequency_ladder import (
    _period_metrics,
    build_resolution_mask,
)


def test_resolution_mask_uses_complete_reference_and_first_break() -> None:
    timestamps = pd.date_range("2026-01-05T00:00Z", periods=20, freq="30min")
    bars = pd.DataFrame(
        {
            "timestamp": timestamps,
            "complete_bar": True,
            "mid_low": [1.1] * 12 + [1.0] * 8,
            "mid_close": [1.2] * 12 + [1.0] * 8,
            "body_fraction": 0.8,
            "regime": "chop",
            "atr": 0.001,
        }
    )
    candidate = {
        "body_fraction_minimum": 0.35,
        "owned_regime": "chop",
    }
    mask = build_resolution_mask(bars, candidate, 30)
    assert mask.sum() == 1
    assert bars.loc[mask, "timestamp"].iloc[0] == pd.Timestamp("2026-01-05T06:00Z")


def test_period_metrics_encode_all_win_profit_factor_for_strict_json() -> None:
    trades = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2026-06-01T08:00Z", "2026-06-02T08:00Z"],
                utc=True,
            ),
            "exit_time_utc": pd.to_datetime(
                ["2026-06-01T09:00Z", "2026-06-02T09:00Z"],
                utc=True,
            ),
            "r": [1.0, 1.25],
            "stress_r": [1.0, 1.25],
            "pnl_usd_001_lot": [2.0, 3.0],
        }
    )
    rows = _period_metrics(trades, "%Y-%m")
    assert rows[0]["profit_factor"] is None
    assert rows[0]["profit_factor_is_infinite"] is True
    assert "profit_factor" in rows[0]["nonfinite_metrics"]
