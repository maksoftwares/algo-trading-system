from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_binance_eurusdt_flow import (  # noqa: E402
    build_decisions,
    build_flow_signals,
)


def config() -> dict:
    return {
        "strategy": {
            "required_trades_per_eligible_day": 4,
        },
        "flow_rule": {
            "completed_m5_bars": 3,
            "long_threshold": 0.0,
        },
        "windows": {
            "test": [
                "2021-01-04T00:00:00Z",
                "2021-01-04T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
    }


def flow() -> pd.DataFrame:
    index = pd.date_range(
        "2021-01-03T23:45:00Z",
        "2021-01-04T00:45:00Z",
        freq="5min",
    )
    return pd.DataFrame(
        {
            "open_time_utc": index,
            "close_time_utc": index + pd.Timedelta(minutes=5),
            "open": [1.1000] * len(index),
            "close": [1.1001] * len(index),
            "quote_volume": [100.0] * len(index),
            "taker_buy_quote_volume": [60.0] * len(index),
            "trade_count": [20] * len(index),
        }
    )


def points() -> pd.DataFrame:
    entries = pd.to_datetime(
        [
            "2021-01-04T00:00:00Z",
            "2021-01-04T00:15:00Z",
            "2021-01-04T00:30:00Z",
            "2021-01-04T00:45:00Z",
        ],
        utc=True,
    )
    return pd.DataFrame(
        {
            "entry_time_utc": entries,
            "eligible_date": ["2021-01-04"] * 4,
            "decision_id": [
                value.strftime("%Y-%m-%dT%H%M") for value in entries
            ],
        }
    )


def test_three_completed_bars_create_positive_flow() -> None:
    signals = build_flow_signals(flow(), config())
    row = signals[
        signals["entry_time_utc"].eq(
            pd.Timestamp("2021-01-04T00:00:00Z")
        )
    ].iloc[0]
    assert bool(row["flow_feature_valid"])
    assert abs(row["flow_taker_imbalance_15m"] - 0.2) < 1e-12
    assert row["flow_trade_count_15m"] == 60


def test_complete_day_creates_four_long_decisions() -> None:
    signals = build_flow_signals(flow(), config())
    decisions, census = build_decisions(
        points(),
        signals,
        config(),
        enforce_frozen_census=False,
    )
    assert len(decisions) == 4
    assert decisions["flow_side"].eq("LONG").all()
    assert census["eligible_day_exact_four_coverage"] == 1.0


def test_missing_required_flow_excludes_entire_day() -> None:
    frame = flow().drop(index=2).reset_index(drop=True)
    signals = build_flow_signals(frame, config())
    decisions, census = build_decisions(
        points(),
        signals,
        config(),
        enforce_frozen_census=False,
    )
    assert decisions.empty
    assert census["eligible_complete_days"] == 0
