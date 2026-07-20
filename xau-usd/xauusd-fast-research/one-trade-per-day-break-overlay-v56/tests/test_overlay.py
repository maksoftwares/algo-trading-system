import hashlib
from pathlib import Path

import pandas as pd

from overlay import govern_incremental_overlay
from policy import resolve_config


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_v56_preserves_hard_drawdown_and_frequency_gates() -> None:
    path = ROOT / "config" / "one_trade_per_day_break_overlay_v56.json"
    resolved, overlay = resolve_config(REPO_ROOT, path)
    base_path = REPO_ROOT / overlay["base_config_path"]
    assert (
        hashlib.sha256(base_path.read_bytes()).hexdigest()
        == overlay["base_config_sha256"]
    )
    assert resolved["account"]["drawdown_suspend_usd"] == 225.0
    assert resolved["account"]["drawdown_resume_usd"] == 180.0
    assert resolved["account"]["maximum_combined_closed_drawdown_usd"] == 300.0
    assert resolved["gates"]["minimum_combined_trades_per_weekday"] == 1.0


def test_incremental_governor_keeps_fixed_trade_and_uses_spare_daily_slot() -> None:
    fixed = pd.DataFrame(
        [
            {
                "trade_id": "core",
                "sleeve_id": "V50_CORE",
                "entry_time": pd.Timestamp("2025-01-01T00:00:00Z"),
                "exit_time": pd.Timestamp("2025-01-01T01:00:00Z"),
                "pnl_usd": 10.0,
                "risk_usd": float("nan"),
            },
            {
                "trade_id": "base",
                "sleeve_id": "V7_SWING_HEALTH",
                "entry_time": pd.Timestamp("2025-01-02T00:00:00Z"),
                "exit_time": pd.Timestamp("2025-01-02T01:00:00Z"),
                "pnl_usd": 5.0,
                "risk_usd": 10.0,
            },
        ]
    )
    candidates = pd.DataFrame(
        [
            {
                "trade_id": "overlay",
                "entry_time": pd.Timestamp("2025-01-02T02:00:00Z"),
                "exit_time": pd.Timestamp("2025-01-02T03:00:00Z"),
                "pnl_usd": 7.0,
                "risk_usd": 10.0,
            }
        ]
    )
    account = {
        "maximum_addon_open_positions": 2,
        "maximum_addon_concurrent_initial_risk_usd": 45.0,
        "maximum_addon_entries_per_utc_date": 2,
        "drawdown_suspend_usd": 225.0,
        "drawdown_resume_usd": 180.0,
    }

    accepted, decisions = govern_incremental_overlay(candidates, fixed, account)

    assert fixed["trade_id"].tolist() == ["core", "base"]
    assert accepted["trade_id"].tolist() == ["overlay"]
    assert decisions.iloc[0]["decision_reason"] == "ACCEPTED"
