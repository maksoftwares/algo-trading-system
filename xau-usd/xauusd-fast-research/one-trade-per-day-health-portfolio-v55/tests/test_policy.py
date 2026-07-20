import hashlib
from pathlib import Path

import pandas as pd

from policy import resolve_config
from risk_overlay import govern_addons_soft_risk


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_v55_changes_only_to_soft_drawdown_risk_fields_and_outputs() -> None:
    path = ROOT / "config" / "one_trade_per_day_health_portfolio_v55.json"
    resolved, overlay = resolve_config(REPO_ROOT, path)
    base_path = REPO_ROOT / overlay["base_config_path"]
    actual = hashlib.sha256(base_path.read_bytes()).hexdigest()
    assert actual == overlay["base_config_sha256"]
    assert resolved["account"]["drawdown_derisk_start_usd"] == 225.0
    assert resolved["account"]["drawdown_full_risk_resume_usd"] == 180.0
    assert resolved["account"]["drawdown_risk_multiplier"] == 0.5
    assert resolved["account"]["maximum_combined_closed_drawdown_usd"] == 300.0
    assert resolved["gates"]["minimum_combined_trades_per_weekday"] == 1.0


def test_drawdown_reduces_risk_without_deleting_the_next_trade() -> None:
    candidates = pd.DataFrame(
        [
            {
                "trade_id": "candidate",
                "sleeve_id": "test",
                "signal_time": pd.Timestamp("2025-01-02T00:00:00Z"),
                "entry_time": pd.Timestamp("2025-01-02T00:00:00Z"),
                "exit_time": pd.Timestamp("2025-01-02T01:00:00Z"),
                "direction": 1,
                "pnl_usd": 20.0,
                "risk_usd": 30.0,
            }
        ]
    )
    core = pd.DataFrame(
        [
            {
                "trade_id": "peak",
                "exit_time": pd.Timestamp("2025-01-01T00:00:00Z"),
                "pnl_usd": 100.0,
            },
            {
                "trade_id": "loss",
                "exit_time": pd.Timestamp("2025-01-01T01:00:00Z"),
                "pnl_usd": -230.0,
            },
        ]
    )
    account = {
        "maximum_addon_open_positions": 2,
        "maximum_addon_concurrent_initial_risk_usd": 45.0,
        "maximum_addon_entries_per_utc_date": 2,
        "drawdown_derisk_start_usd": 225.0,
        "drawdown_full_risk_resume_usd": 180.0,
        "drawdown_risk_multiplier": 0.5,
    }

    accepted, decisions = govern_addons_soft_risk(candidates, core, account)

    assert len(accepted) == 1
    assert accepted.iloc[0]["risk_usd"] == 15.0
    assert accepted.iloc[0]["pnl_usd"] == 10.0
    assert decisions.iloc[0]["decision_reason"] == "ACCEPTED"
    assert bool(decisions.iloc[0]["drawdown_derisked"])
