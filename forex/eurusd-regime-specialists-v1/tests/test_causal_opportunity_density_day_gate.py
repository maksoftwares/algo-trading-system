from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.causal_opportunity_density_day_gate import (
    build_daily_dataset,
    select_causal_trades,
)


def test_daily_count_feature_is_lagged() -> None:
    timestamps = pd.date_range(
        "2026-01-01T00:00Z", periods=30 * 12, freq="2h"
    )
    bid = pd.Series(range(len(timestamps)), dtype=float) * 0.00001 + 1.1
    m5 = pd.DataFrame(
        {
            "timestamp": timestamps,
            "bid_open": bid,
            "bid_high": bid + 0.0001,
            "bid_low": bid - 0.0001,
            "bid_close": bid + 0.00002,
            "ask_open": bid + 0.00007,
            "ask_high": bid + 0.00017,
            "ask_low": bid - 0.00003,
            "ask_close": bid + 0.00009,
        }
    )
    opportunities = pd.DataFrame(
        {
            "entry_date": ["2026-01-28", "2026-01-28", "2026-01-29"],
            "owner": ["A", "A", "A"],
            "r": [1.0, -1.0, 1.0],
        }
    )
    daily, _ = build_daily_dataset(
        m5,
        opportunities,
        start_date="2026-01-01",
        target_count=4,
    )
    day = pd.Timestamp("2026-01-29T00:00Z")
    assert daily.loc[day, "prior_opportunity_count"] == 2
    assert daily.loc[day, "opportunity_count"] == 1


def test_selected_trades_use_earliest_four_without_future_ranking() -> None:
    opportunities = pd.DataFrame(
        {
            "entry_date": ["2026-01-05"] * 5,
            "entry_time_utc": pd.date_range(
                "2026-01-05T01:00Z", periods=5, freq="h"
            ),
            "owner_priority": [0, 0, 0, 0, 0],
            "seed_priority": [0, 0, 0, 0, 0],
            "r": [-1.0, -1.0, -1.0, -1.0, 1.5],
        }
    )
    decisions = pd.DataFrame(
        {
            "date": [pd.Timestamp("2026-01-05")],
            "activated": [True],
        }
    )
    selected = select_causal_trades(opportunities, decisions, 4)
    assert len(selected) == 4
    assert selected["r"].tolist() == [-1.0, -1.0, -1.0, -1.0]
