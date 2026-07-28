from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_precious_metals_consensus import (  # noqa: E402
    build_decisions,
    completed_return_vote,
)


def metal_frame(direction: float = 1.0) -> pd.DataFrame:
    index = pd.date_range(
        "2024-01-04T22:55:00Z", periods=16, freq="5min"
    )
    price = 20.0 + direction * np.arange(len(index)) * 0.01
    return pd.DataFrame(
        {
            "bid_close": price,
            "ask_close": price + 0.002,
        },
        index=index,
    )


def config() -> dict:
    return {
        "strategy": {"return_horizon_minutes": 60},
        "windows": {
            "test": [
                "2024-01-01T00:00:00Z",
                "2024-12-31T23:59:59Z",
            ]
        },
        "outcome_blind_census": None,
    }


def points() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "decision_id": ["a", "b"],
            "eligible_date": ["2024-01-05", "2024-01-05"],
            "entry_time_utc": pd.to_datetime(
                [
                    "2024-01-05T00:00:00Z",
                    "2024-01-05T00:15:00Z",
                ],
                utc=True,
            ),
        }
    )


def test_completed_return_requires_exact_contiguous_endpoints() -> None:
    close = pd.Series(
        np.arange(13, dtype=float) + 20.0,
        index=pd.date_range(
            "2024-01-01T00:00:00Z", periods=13, freq="5min"
        ),
    )
    returns, votes = completed_return_vote(close, 60)
    assert votes.iloc[-1] == 1.0
    broken = close.drop(close.index[5])
    broken_returns, broken_votes = completed_return_vote(broken, 60)
    assert pd.isna(broken_returns.iloc[-1])
    assert pd.isna(broken_votes.iloc[-1])


def test_consensus_uses_bar_completed_immediately_before_entry() -> None:
    attached, decisions, census = build_decisions(
        points(),
        {"XAUUSD": metal_frame(), "XAGUSD": metal_frame()},
        config(),
        enforce_frozen_census=False,
    )
    assert list(attached["signal_time_metals_utc"]) == [
        pd.Timestamp("2024-01-04T23:55:00Z"),
        pd.Timestamp("2024-01-05T00:10:00Z"),
    ]
    assert list(decisions["metals_side"]) == ["LONG", "LONG"]
    assert census["agreement_trade_candidates"] == 2
    assert census["predicted_long_rate"] == 1.0


def test_disagreement_stays_cash() -> None:
    _, decisions, census = build_decisions(
        points(),
        {"XAUUSD": metal_frame(), "XAGUSD": metal_frame(-1.0)},
        config(),
        enforce_frozen_census=False,
    )
    assert decisions.empty
    assert census["agreement_trade_candidates"] == 0
