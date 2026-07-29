from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from eurusd_regime_specialists import (
    neutral_late_session_inventory_unwind_v1_1 as module,
)


def _views() -> tuple[pd.DataFrame, pd.DataFrame]:
    points = pd.DataFrame(
        {
            "side": ["LONG", "SHORT", "LONG", "CASH"],
            "signal_eligible": [True, True, True, False],
            "inventory_displacement_pips": [7.0, 5.0, 4.0, 9.0],
        }
    )
    candidates = pd.DataFrame(
        {
            "side": ["LONG", "SHORT", "LONG"],
            "inventory_displacement_pips": [7.0, 5.0, 4.0],
            "risk_eligible": [True, True, True],
        }
    )
    return points, candidates


def test_six_pip_view_keeps_only_six_pip_signals() -> None:
    points, candidates = _views()
    view_points, view_candidates = module.derive_threshold_view(
        points,
        candidates,
        6.0,
    )
    assert int(view_points["signal_eligible"].sum()) == 1
    assert len(view_candidates) == 1
    assert view_candidates.iloc[0]["side"] == "LONG"


def test_cash_row_never_becomes_signal_at_lower_threshold() -> None:
    points, candidates = _views()
    view_points, _ = module.derive_threshold_view(
        points,
        candidates,
        4.0,
    )
    assert not bool(view_points.iloc[-1]["signal_eligible"])


def test_ladder_selects_highest_passing_threshold() -> None:
    threshold, passed = module.choose_threshold(
        [6.0, 4.0],
        {
            6.0: {"census_pass": True},
            4.0: {"census_pass": True},
        },
    )
    assert passed
    assert threshold == 6.0


def test_ladder_retains_floor_only_when_none_passes() -> None:
    threshold, passed = module.choose_threshold(
        [6.0, 4.0],
        {
            6.0: {"census_pass": False},
            4.0: {"census_pass": False},
        },
    )
    assert not passed
    assert threshold == 4.0


def test_config_has_final_four_pip_floor() -> None:
    cfg = module.load_config()
    assert cfg["strategy"][
        "absolute_inventory_displacement_threshold_ladder_pips"
    ] == [6.0, 4.0]
    assert cfg["closed_parent_family"][
        "observed_parent_capacity_only"
    ]["outcome_or_oracle_opened"] is False


def test_census_module_has_no_outcome_loader() -> None:
    forbidden = {
        "load_outcomes",
        "load_oracle",
        "run_backtest",
        "simulate_trades",
    }
    assert forbidden.isdisjoint(set(dir(module)))


def test_preregistration_lock_verifies() -> None:
    checked = module.verify_lock()
    lock = json.loads(
        Path(module.LOCK_PATH).read_text(encoding="utf-8")
    )
    assert checked == lock["files"]
