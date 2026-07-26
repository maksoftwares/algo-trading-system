from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "src"))

from step_5_metrics import (  # noqa: E402
    equity_envelope_drawdown,
    profit_factor,
    window_metrics,
)


def test_profit_factor() -> None:
    assert np.isclose(profit_factor(np.array([3.0, -1.0, 2.0, -1.0])), 2.5)
    assert profit_factor(np.array([1.0, 2.0])) is None


def test_equity_envelope_drawdown_uses_prior_high_and_current_low() -> None:
    curve = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2025-01-01T00:00:00Z", "2025-01-01T00:05:00Z"]
            ),
            "high_equity_usd": [1010.0, 1005.0],
            "low_equity_usd": [1000.0, 980.0],
            "close_equity_usd": [1005.0, 990.0],
            "open_positions": [1, 1],
            "open_initial_risk_usd": [5.0, 5.0],
            "open_margin_usd": [10.0, 10.0],
        }
    )
    result = equity_envelope_drawdown(curve)
    assert np.isclose(result["maximum_drawdown_usd"], 30.0)
    assert np.isclose(result["maximum_drawdown_fraction_of_peak"], 30.0 / 1010.0)


def test_window_metrics_keeps_entry_frequency_separate_from_exit_pnl() -> None:
    ledger = pd.DataFrame(
        {
            "candidate_id": ["a", "b"],
            "family_id": ["R1_UPTREND", "R2_DOWNTREND"],
            "entry_time": pd.to_datetime(
                ["2025-01-02T01:00:00Z", "2025-01-03T01:00:00Z"]
            ),
            "label_end_time": pd.to_datetime(
                ["2025-01-03T01:00:00Z", "2025-01-06T01:00:00Z"]
            ),
            "pnl_usd": [3.0, -1.0],
            "stress_net_r": [1.0, -1.0],
        }
    )
    timestamps = pd.date_range(
        "2025-01-01T00:00:00Z", "2025-01-07T23:55:00Z", freq="5min"
    )
    curve = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "low_equity_usd": 1000.0,
            "high_equity_usd": 1000.0,
            "close_equity_usd": 1000.0,
            "open_positions": 0,
            "open_initial_risk_usd": 0.0,
            "open_margin_usd": 0.0,
        }
    )
    result = window_metrics(
        ledger,
        curve,
        policy_id="P",
        windows={"W": ["2025-01-01T00:00:00Z", "2025-01-08T00:00:00Z"]},
        starting_equity_usd=1000.0,
        top_winners_removed=1,
    ).iloc[0]
    assert result["entries"] == 2
    assert result["exits"] == 2
    assert np.isclose(result["net_usd"], 2.0)
    assert np.isclose(result["profit_factor"], 3.0)
    assert np.isclose(result["entries_per_weekday"], 2.0 / 5.0)
    assert np.isclose(result["top_winners_removed_net_usd"], -1.0)
