from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.executable_sizing_frequency_portfolio import (
    outcome_metrics,
    restore_executable_sizing,
)


def test_restore_replaces_only_protected_pnl_and_volume() -> None:
    entries = pd.to_datetime(
        ["2026-01-05T10:00Z", "2026-01-06T10:00Z"], utc=True
    )
    exits = entries + pd.Timedelta(hours=1)
    combined = pd.DataFrame(
        {
            "entry_time": entries,
            "exit_time": exits,
            "side": ["SHORT", "LONG"],
            "pnl_usd": [1.0, 2.0],
            "component": ["M15_REGIME", "GATED_RSI"],
        }
    )
    protected = pd.DataFrame(
        {
            "entry_time": [entries[0].strftime("%Y.%m.%d %H:%M:%S")],
            "exit_time": [exits[0].strftime("%Y.%m.%d %H:%M:%S")],
            "profit": [2.0],
            "volume": [0.02],
        }
    )
    result = restore_executable_sizing(
        combined, protected, rsi_fixed_lots=0.01
    )
    assert result["pnl_usd"].tolist() == [2.0, 2.0]
    assert result["volume"].tolist() == [0.02, 0.01]


def test_stress_scales_with_volume() -> None:
    entries = pd.to_datetime(
        ["2026-01-05T10:00Z", "2026-01-06T10:00Z"], utc=True
    )
    frame = pd.DataFrame(
        {
            "entry_time": entries,
            "exit_time": entries + pd.Timedelta(hours=1),
            "component": ["M15_REGIME", "GATED_RSI"],
            "pnl_usd": [1.0, -0.5],
            "volume": [0.02, 0.01],
        }
    )
    metrics = outcome_metrics(
        frame, weekdays=2, extra_cost_usd_per_001_lot=0.05
    )
    assert metrics["net_pnl_usd"] == 0.5
    assert metrics["stressed_net_pnl_usd"] == 0.35
