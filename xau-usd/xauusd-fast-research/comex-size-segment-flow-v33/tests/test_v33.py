from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BASE_SRC = ROOT.parent / "comex-size-segment-flow-v32" / "src"
for source in (SRC, BASE_SRC):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from v33 import load_config, policy_grid, select_policy  # noqa: E402
from size_segment_flow import summarize_stage  # noqa: E402


def test_inherited_v32_config_resolves_from_package_root() -> None:
    config = load_config(ROOT / "config" / "comex_size_segment_flow_v33.json")
    assert config["campaign_id"] == "comex-size-segment-flow-v33"
    assert (
        config["families"]["large_small_divergence_continuation"][
            "maximum_hold_minutes"
        ]
        == 60
    )


def test_grid_is_exactly_96_registered_density_policies() -> None:
    config = {
        "calibration": {
            "large_trade_size_grid": [8, 10],
            "minimum_large_volume_grid": [20, 30, 40],
            "minimum_absolute_large_imbalance_grid": [0.25, 0.35],
            "minimum_absolute_opposing_small_imbalance_grid": [0.05, 0.1],
            "minimum_small_volume_grid": [30, 50],
            "cooldown_minutes_grid": [45, 60],
        }
    }
    assert len(policy_grid(config)) == 96


def test_selector_preserves_density_fields() -> None:
    row = {
        "policy_id": "p",
        "large_trade_size": 10,
        "minimum_large_volume": 30,
        "minimum_absolute_large_imbalance": 0.35,
        "minimum_absolute_opposing_small_imbalance": 0.1,
        "minimum_small_volume": 50,
        "cooldown_minutes": 45,
        "candidates_per_full_weekday": 2.9,
        "selection_eligible": True,
    }
    selected = select_policy([row], {"target_candidates_per_full_weekday": 2.9})
    assert selected == {
        key: row[key]
        for key in (
            "policy_id",
            "large_trade_size",
            "minimum_large_volume",
            "minimum_absolute_large_imbalance",
            "minimum_absolute_opposing_small_imbalance",
            "minimum_small_volume",
            "cooldown_minutes",
        )
    }


def test_inherited_stage_summary_handles_daily_zero_fill() -> None:
    config = load_config(ROOT / "config" / "comex_size_segment_flow_v33.json")
    dates = pd.date_range("2023-01-02", periods=10, freq="B", tz="UTC")
    rows = []
    for index, date in enumerate(dates):
        for trade in range(2):
            pnl = 2.0 if trade == 0 else -1.0
            rows.append(
                {
                    "candidate_id": f"{index}:{trade}",
                    "status": "RESOLVED",
                    "direction": "LONG" if (index + trade) % 2 == 0 else "SHORT",
                    "decision_time_utc": date + pd.Timedelta(hours=13 + trade),
                    "exit_time_utc": date + pd.Timedelta(hours=14 + trade),
                    "baseline_net_pnl_usd": pnl,
                    "stress_net_pnl_usd": pnl,
                }
            )
    result = summarize_stage(
        pd.DataFrame(rows),
        stage="development",
        eligible_dates=[str(date.date()) for date in dates],
        config=config,
    )
    assert result["metrics"]["eligible_full_weekdays"] == 10
    assert result["metrics"]["resolved_trades"] == 20
    assert result["metrics"]["stress_profit_factor"] == 2.0
