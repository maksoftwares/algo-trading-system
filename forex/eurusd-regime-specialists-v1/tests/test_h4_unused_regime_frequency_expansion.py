from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_unused_regime_frequency_expansion import (
    build_directional_masks,
    simulate_long,
)


def test_two_sided_mask_keeps_only_first_break_per_date() -> None:
    timestamps = pd.date_range("2026-01-05T00:00Z", periods=10, freq="h")
    h1 = pd.DataFrame(
        {
            "timestamp": timestamps,
            "complete_hour": True,
            "contiguous_next": True,
            "mid_high": [1.1] * 6 + [1.102, 1.1, 1.1, 1.1],
            "mid_low": [1.0] * 6 + [1.0, 0.998, 1.0, 1.0],
            "mid_close": [1.05] * 6 + [1.101, 0.999, 1.05, 1.05],
            "body_fraction": 0.8,
            "regime": "transition",
            "atr": 0.001,
        }
    )
    candidate = {
        "reference_hours_utc": [0, 1, 2, 3, 4, 5],
        "decision_hours_utc": [6, 7, 8, 9],
        "body_fraction_minimum": 0.35,
        "owned_regime": "transition",
        "direction": "TWO_SIDED",
    }
    masks = build_directional_masks(h1, candidate)
    assert masks["LONG"].sum() == 1
    assert masks["SHORT"].sum() == 0


def test_long_simulator_hits_target_with_ask_entry_and_bid_exit() -> None:
    signal_time = pd.Timestamp("2026-01-05T06:00Z")
    timestamps = pd.date_range(
        signal_time + pd.Timedelta(hours=1), periods=144, freq="5min"
    )
    bid = np.full(144, 1.1000)
    m5 = pd.DataFrame(
        {
            "timestamp": timestamps,
            "bid_open": bid,
            "bid_high": bid + 0.00005,
            "bid_low": bid - 0.00005,
            "bid_close": bid,
            "ask_open": bid + 0.00007,
            "ask_high": bid + 0.00012,
            "ask_low": bid + 0.00002,
            "ask_close": bid + 0.00007,
        }
    )
    m5.loc[2, "bid_high"] = 1.1030
    m5.loc[2, "ask_high"] = 1.10307
    h1 = pd.DataFrame({"timestamp": [signal_time], "atr": [0.001]})
    candidate = {
        "specialist_id": "LONG_FIXTURE",
        "owned_regime": "trend_up",
        "stop_atr_multiple": 1.75,
        "target_r_multiple": 1.25,
        "maximum_hold_hours": 12,
    }
    config = {
        "source": {"quarantine": []},
        "execution": {
            "minimum_retail_spread_pips": 0.7,
            "maximum_entry_spread_pips": 2.0,
            "adverse_slippage_pips_per_side": 0.1,
            "extra_round_trip_stress_pips": 0.5,
        },
    }
    trades, diagnostics = simulate_long(h1, m5, pd.Series([True]), candidate, config)
    assert diagnostics["signals"] == 1
    assert trades.iloc[0]["side"] == "LONG"
    assert trades.iloc[0]["exit_reason"] == "TARGET"
    assert trades.iloc[0]["r"] > 1.2
