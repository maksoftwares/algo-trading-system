from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.annual_expanding_cell_specialist import (
    eligible_in_window,
    select_completed_cells,
)

CONTRACT = {
    "columns": ["owner", "seed_id", "entry_hour_utc"],
    "training_start": "2019-01-01T00:00:00Z",
    "minimum_completed_trades": 4,
    "minimum_win_rate": 0.45,
    "maximum_win_rate": 0.65,
    "minimum_profit_factor": 1.3,
}


def opportunity_frame(
    outcomes: list[float],
    *,
    exits: pd.DatetimeIndex | None = None,
) -> pd.DataFrame:
    entries = pd.date_range("2021-01-01T10:00Z", periods=len(outcomes), freq="D")
    if exits is None:
        exits = entries + pd.Timedelta(hours=1)
    return pd.DataFrame(
        {
            "owner": ["REGIME"] * len(outcomes),
            "seed_id": ["SEED"] * len(outcomes),
            "entry_hour_utc": [10] * len(outcomes),
            "entry_time_utc": entries,
            "exit_time_utc": exits,
            "r": outcomes,
        }
    )


def test_cell_selection_uses_only_exits_completed_before_cutoff() -> None:
    frame = opportunity_frame([1.5, 1.5, -1.0, -1.0])
    frame.loc[3, "exit_time_utc"] = pd.Timestamp("2022-01-01T01:00Z")
    selected, all_cells = select_completed_cells(
        frame, CONTRACT, pd.Timestamp("2022-01-01T00:00Z")
    )
    assert all_cells.iloc[0]["trades"] == 3
    assert selected.empty


def test_cell_selection_applies_frozen_trade_win_and_pf_gates() -> None:
    passing = opportunity_frame([1.5, 1.5, -1.0, -1.0])
    selected, _ = select_completed_cells(
        passing, CONTRACT, pd.Timestamp("2022-01-01T00:00Z")
    )
    assert len(selected) == 1
    failing = opportunity_frame([1.0, 1.0, -1.0, -1.0])
    selected, _ = select_completed_cells(
        failing, CONTRACT, pd.Timestamp("2022-01-01T00:00Z")
    )
    assert selected.empty


def test_eligible_window_cannot_include_future_year_entries() -> None:
    opportunities = opportunity_frame([1.5, -1.0, 1.5, -1.0])
    opportunities.loc[3, "entry_time_utc"] = pd.Timestamp(
        "2023-01-01T10:00Z"
    )
    selected, _ = select_completed_cells(
        opportunities, CONTRACT, pd.Timestamp("2022-01-01T00:00Z")
    )
    eligible = eligible_in_window(
        opportunities,
        selected,
        list(CONTRACT["columns"]),
        ["2021-01-01T00:00Z", "2022-01-01T00:00Z"],
        "TEST_2021",
    )
    assert len(eligible) == 3
    assert eligible["entry_time_utc"].max() < pd.Timestamp(
        "2022-01-01T00:00Z"
    )
