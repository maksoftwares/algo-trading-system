from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_chop_anchor_validation import (
    apply_round_trip_cost,
    circular_block_bootstrap,
    count_utc_rollovers,
)
from eurusd_regime_specialists.neutral_h4_quiet_state_transfer import simulate_short


def _fixture(
    outcome: str,
    *,
    bars: int = 144,
    spread_pips: float = 0.7,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, dict, dict]:
    signal_time = pd.Timestamp("2026-01-05T06:00:00Z")
    entry_time = signal_time + pd.Timedelta(hours=1)
    timestamps = pd.date_range(entry_time, periods=bars, freq="5min", tz="UTC")
    bid = np.full(bars, 1.1000)
    spread = spread_pips * 0.0001
    m5 = pd.DataFrame(
        {
            "timestamp": timestamps,
            "bid_open": bid,
            "bid_high": bid + 0.00005,
            "bid_low": bid - 0.00005,
            "bid_close": bid,
            "ask_open": bid + spread,
            "ask_high": bid + spread + 0.00005,
            "ask_low": bid + spread - 0.00005,
            "ask_close": bid + spread,
        }
    )
    if outcome == "TARGET":
        m5.loc[2, "bid_low"] = 1.09693
        m5.loc[2, "ask_low"] = 1.0970
    elif outcome == "STOP":
        m5.loc[2, "ask_high"] = 1.1020
    elif outcome == "STOP_FIRST":
        m5.loc[2, "bid_low"] = 1.09693
        m5.loc[2, ["ask_high", "ask_low"]] = [1.1020, 1.0970]
    elif outcome == "STOP_GAP":
        m5.loc[2, ["ask_open", "ask_high", "ask_low", "ask_close"]] = [
            1.1020,
            1.1021,
            1.1019,
            1.1020,
        ]
    h1 = pd.DataFrame({"timestamp": [signal_time], "atr": [0.001]})
    mask = pd.Series([True])
    candidate = {
        "specialist_id": "FIXTURE",
        "owned_regime": "chop",
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
    return h1, m5, mask, candidate, config


def _run_fixture(outcome: str, **kwargs):
    args = _fixture(outcome, **kwargs)
    return simulate_short(*args)


def test_golden_target_stop_stop_first_gap_and_time_paths() -> None:
    expected = {
        "TARGET": "TARGET",
        "STOP": "STOP",
        "STOP_FIRST": "STOP",
        "STOP_GAP": "STOP_GAP",
        "TIME": "TIME",
    }
    for setup, reason in expected.items():
        trades, diagnostics = _run_fixture(setup)
        assert diagnostics["signals"] == 1
        assert len(trades) == 1
        assert trades.iloc[0]["exit_reason"] == reason


def test_golden_spread_incomplete_quarantine_and_delay_paths() -> None:
    trades, diagnostics = _run_fixture("TIME", spread_pips=2.1)
    assert trades.empty
    assert diagnostics["spread_rejection"] == 1

    trades, diagnostics = _run_fixture("TIME", bars=143)
    assert trades.empty
    assert diagnostics["incomplete_path"] == 1

    h1, m5, mask, candidate, config = _fixture("TIME")
    config["source"]["quarantine"] = [
        {
            "start_utc": "2026-01-05T07:30:00Z",
            "end_utc": "2026-01-05T08:30:00Z",
        }
    ]
    trades, diagnostics = simulate_short(h1, m5, mask, candidate, config)
    assert trades.empty
    assert diagnostics["quarantine_rejection"] == 1

    h1, m5, mask, candidate, config = _fixture("TIME", bars=147)
    trades, _ = simulate_short(h1, m5, mask, candidate, config, entry_delay_minutes=15)
    assert trades.iloc[0]["entry_time_utc"] == pd.Timestamp("2026-01-05T07:15:00Z")
    assert trades.iloc[0]["entry_delay_minutes"] == 15


def test_cost_rollover_and_bootstrap_are_deterministic() -> None:
    trades = pd.DataFrame(
        {
            "stop_pips": [10.0, 20.0],
            "r": [1.0, -1.0],
            "net_pips": [10.0, -20.0],
            "pnl_usd_001_lot": [1.0, -2.0],
        }
    )
    stressed = apply_round_trip_cost(trades, 1.0)
    assert stressed["r"].tolist() == [0.9, -1.05]
    assert (
        count_utc_rollovers(
            pd.Timestamp("2026-01-05T20:00:00Z"),
            pd.Timestamp("2026-01-05T22:00:00Z"),
        )
        == 1
    )
    values = np.array([1.0, -0.5, 1.0, -0.5, 0.25])
    first = circular_block_bootstrap(
        values, samples=100, block_trades=2, seed=7, lower_quantile=0.05
    )
    second = circular_block_bootstrap(
        values, samples=100, block_trades=2, seed=7, lower_quantile=0.05
    )
    assert first == second
