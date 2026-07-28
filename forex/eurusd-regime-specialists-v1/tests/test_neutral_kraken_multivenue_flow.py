from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_kraken_multivenue_flow import (  # noqa: E402
    build_decisions,
)


def config() -> dict:
    relationship = {
        "imbalance_correlation": -1.0,
        "return_correlation": -1.0,
        "sign_agreement": 0.0,
        "multivenue_predicted_long_rate": 0.5,
        "exact_score_ties": 0,
    }
    return {
        "strategy": {"required_trades_per_eligible_day": 4},
        "flow_rule": {"long_threshold": 0.0},
        "windows": {
            "test": [
                "2025-01-01T00:00:00Z",
                "2025-12-31T23:59:59Z",
            ]
        },
        "outcome_blind_census": {
            "outcome_blind_source_relationship": relationship,
        },
    }


def parent() -> pd.DataFrame:
    entries = pd.to_datetime(
        [
            "2025-01-02T00:00:00Z",
            "2025-01-02T00:15:00Z",
            "2025-01-02T00:30:00Z",
            "2025-01-02T00:45:00Z",
        ],
        utc=True,
    )
    return pd.DataFrame(
        {
            "entry_time_utc": entries,
            "eligible_date": ["2025-01-02"] * 4,
            "decision_id": [
                value.strftime("%Y-%m-%dT%H%M") for value in entries
            ],
        }
    )


def signals(prefix: str) -> pd.DataFrame:
    entries = parent()["entry_time_utc"]
    imbalance = (
        [0.8, -0.8, 0.4, -0.4]
        if prefix == "kraken"
        else [-0.2, 0.2, -0.6, 0.6]
    )
    values = {
        "entry_time_utc": entries,
        f"{prefix}_flow_valid": [True] * 4,
        f"{prefix}_return_15m": [0.01, -0.01, 0.02, -0.02],
    }
    if prefix == "kraken":
        values.update(
            {
                "kraken_quote_volume_15m": [100.0] * 4,
                "kraken_reported_buy_quote_volume_15m": [60.0] * 4,
                "kraken_trade_count_15m": [10] * 4,
                "kraken_reported_side_imbalance_15m": imbalance,
            }
        )
    else:
        values.update(
            {
                "binance_quote_volume_15m": [100.0] * 4,
                "binance_taker_buy_quote_volume_15m": [60.0] * 4,
                "binance_trade_count_15m": [10] * 4,
                "binance_taker_imbalance_15m": imbalance,
            }
        )
    return pd.DataFrame(values)


def test_equal_weight_score_forces_one_side_per_clock() -> None:
    decisions, census = build_decisions(
        parent(),
        signals("kraken"),
        signals("binance"),
        config(),
        enforce_frozen_census=False,
    )
    assert len(decisions) == 4
    assert np.allclose(
        decisions["multivenue_flow_score"],
        [0.3, -0.3, -0.1, 0.1],
    )
    assert decisions["flow_side"].tolist() == [
        "LONG",
        "SHORT",
        "SHORT",
        "LONG",
    ]
    assert census["eligible_day_exact_four_coverage"] == 1.0


def test_missing_one_venue_clock_excludes_entire_day() -> None:
    kraken = signals("kraken")
    kraken.loc[0, "kraken_flow_valid"] = False
    decisions, census = build_decisions(
        parent(),
        kraken,
        signals("binance"),
        config(),
        enforce_frozen_census=False,
    )
    assert decisions.empty
    assert census["eligible_complete_days"] == 0
