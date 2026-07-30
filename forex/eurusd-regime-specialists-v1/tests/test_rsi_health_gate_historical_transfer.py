from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.rsi_health_gate_historical_transfer import (
    causal_health_gate,
    nearest_signal_coverage,
    simulate_rsi_trades,
)

RULE = {
    "adverse_slippage_pips_per_side": 0.0,
    "maximum_trades_per_utc_day": 20,
    "maximum_entry_spread_pips": 10.0,
    "stop_atr_multiple": 1.4,
    "stop_floor_pips": 3.0,
    "stop_ceiling_pips": 70.0,
    "target_r": 0.8,
}


def test_same_bar_stop_wins_over_target() -> None:
    timestamps = pd.date_range("2026-01-05T10:00Z", periods=2, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp": timestamps,
            "bid_open": [1.1000, 1.1000],
            "bid_high": [1.1010, 1.1001],
            "bid_low": [1.0980, 1.0999],
            "bid_close": [1.1000, 1.1000],
            "ask_open": [1.1001, 1.1001],
            "ask_high": [1.1011, 1.1002],
            "ask_low": [1.0981, 1.1000],
            "ask_close": [1.1001, 1.1001],
        }
    )
    signals = pd.DataFrame(
        {
            "signal_time_utc": [pd.Timestamp("2026-01-05T09:45Z")],
            "entry_time_utc": [pd.Timestamp("2026-01-05T10:00Z")],
            "atr": [0.0005],
            "recent_low": [1.0994],
        }
    )
    trades = simulate_rsi_trades(m5, signals, RULE, [])
    assert len(trades) == 1
    assert trades.iloc[0]["exit_reason"] == "STOP"
    assert trades.iloc[0]["r"] < 0.0


def test_health_gate_uses_only_outcomes_completed_by_entry() -> None:
    entries = pd.to_datetime(
        [
            "2026-01-01T00:00Z",
            "2026-01-02T00:00Z",
            "2026-01-03T00:00Z",
        ],
        utc=True,
    )
    trades = pd.DataFrame(
        {
            "entry_time_utc": entries,
            "exit_time_utc": pd.to_datetime(
                [
                    "2026-01-01T01:00Z",
                    "2026-01-04T00:00Z",
                    "2026-01-03T01:00Z",
                ],
                utc=True,
            ),
            "pnl_usd_001_lot": [1.5, 1.5, -1.0],
        }
    )
    gated = causal_health_gate(
        trades,
        {
            "lookback_completed_shadow_trades": 1,
            "minimum_trailing_profit_factor": 1.05,
        },
    )
    assert not gated.iloc[0]["health_gate_admitted"]
    assert gated.iloc[1]["health_gate_admitted"]
    assert gated.iloc[2]["health_gate_admitted"]
    assert gated.iloc[2]["available_completed_shadow_trades"] == 1


def test_signal_coverage_obeys_fixed_tolerance() -> None:
    broker = pd.Series(
        pd.to_datetime(
            ["2026-01-05T10:00Z", "2026-01-05T11:00Z"], utc=True
        )
    )
    signals = pd.Series(
        pd.to_datetime(
            ["2026-01-05T10:15Z", "2026-01-05T11:16Z"], utc=True
        )
    )
    result = nearest_signal_coverage(broker, signals, 15)
    assert result["matching_entries"] == 1
    assert result["coverage"] == 0.5
