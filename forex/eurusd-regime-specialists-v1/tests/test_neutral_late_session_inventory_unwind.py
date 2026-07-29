from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from eurusd_regime_specialists import (
    neutral_late_session_inventory_unwind as module,
)
from eurusd_regime_specialists.research import PIP


def _bar(mid_open: float, mid_close: float) -> dict[str, float]:
    half_spread = 0.4 * PIP
    high = max(mid_open, mid_close) + 0.5 * PIP
    low = min(mid_open, mid_close) - 0.5 * PIP
    return {
        "bid_open": mid_open - half_spread,
        "bid_high": high - half_spread,
        "bid_low": low - half_spread,
        "bid_close": mid_close - half_spread,
        "ask_open": mid_open + half_spread,
        "ask_high": high + half_spread,
        "ask_low": low + half_spread,
        "ask_close": mid_close + half_spread,
    }


def _frame(
    *,
    late_pips: float = -12.0,
    confirmation_pips: float = 3.0,
) -> pd.DataFrame:
    date = pd.Timestamp("2024-01-03T00:00:00Z")
    inventory_index = pd.date_range(
        date - pd.Timedelta(hours=4),
        periods=48,
        freq="5min",
    )
    confirmation_index = pd.date_range(date, periods=3, freq="5min")
    rows: list[dict[str, float]] = []
    index: list[pd.Timestamp] = []
    start = 1.1012
    inventory_targets = [
        start + late_pips * PIP * ((i + 1) / 48.0)
        for i in range(48)
    ]
    previous = start
    for timestamp, target in zip(
        inventory_index,
        inventory_targets,
        strict=True,
    ):
        rows.append(_bar(previous, target))
        index.append(timestamp)
        previous = target
    confirm_start = previous
    confirm_targets = [
        confirm_start
        + confirmation_pips * PIP * ((i + 1) / 3.0)
        for i in range(3)
    ]
    previous = confirm_start
    for timestamp, target in zip(
        confirmation_index,
        confirm_targets,
        strict=True,
    ):
        rows.append(_bar(previous, target))
        index.append(timestamp)
        previous = target
    rows.append(_bar(previous, previous))
    index.append(date + pd.Timedelta(minutes=15))
    return pd.DataFrame(rows, index=pd.DatetimeIndex(index))


def test_completed_down_inventory_and_up_confirmation_go_long() -> None:
    cfg = module.load_config()
    points = module.generate_inventory_points(
        _frame(),
        cfg,
        threshold_pips=10.0,
        dates=[pd.Timestamp("2024-01-03T00:00:00Z")],
    )
    assert len(points) == 1
    row = points.iloc[0]
    assert row["side"] == "LONG"
    assert bool(row["signal_eligible"])
    assert row["inventory_return_pips"] < -11.9
    assert row["confirmation_return_pips"] > 2.9


def test_displacement_below_threshold_stays_cash() -> None:
    cfg = module.load_config()
    points = module.generate_inventory_points(
        _frame(late_pips=-7.0),
        cfg,
        threshold_pips=8.0,
        dates=[pd.Timestamp("2024-01-03T00:00:00Z")],
    )
    assert points.iloc[0]["side"] == "CASH"


def test_confirmation_must_be_opposite() -> None:
    cfg = module.load_config()
    points = module.generate_inventory_points(
        _frame(confirmation_pips=-3.0),
        cfg,
        threshold_pips=10.0,
        dates=[pd.Timestamp("2024-01-03T00:00:00Z")],
    )
    assert points.iloc[0]["side"] == "CASH"


def test_entry_bar_values_do_not_change_signal() -> None:
    cfg = module.load_config()
    original = _frame()
    changed = original.copy()
    entry = pd.Timestamp("2024-01-03T00:15:00Z")
    changed.loc[entry] = _bar(1.2000, 1.2500)
    kwargs = {
        "threshold_pips": 10.0,
        "dates": [pd.Timestamp("2024-01-03T00:00:00Z")],
    }
    left = module.generate_inventory_points(original, cfg, **kwargs)
    right = module.generate_inventory_points(changed, cfg, **kwargs)
    columns = [
        "side",
        "inventory_return_pips",
        "confirmation_return_pips",
        "retracement_fraction",
    ]
    pd.testing.assert_frame_equal(left[columns], right[columns])


def test_ladder_selects_highest_capacity_compliant_threshold() -> None:
    summaries = {
        12.0: {"census_pass": False},
        10.0: {"census_pass": True},
        8.0: {"census_pass": True},
    }
    threshold, passed = module.choose_threshold(
        [12.0, 10.0, 8.0],
        summaries,
    )
    assert passed
    assert threshold == 10.0


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
