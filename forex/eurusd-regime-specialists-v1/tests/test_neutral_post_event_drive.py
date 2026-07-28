from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_post_event_drive import (  # noqa: E402
    build_candidates,
)


def config() -> dict:
    return {
        "strategy": {
            "observation_bars": 3,
            "observation_minutes": 15,
        },
        "structure_risk": {
            "stop_buffer_pips": 0.5,
            "minimum_risk_pips": 4.0,
            "maximum_risk_pips": 25.0,
        },
        "execution": {
            "minimum_retail_spread_pips": 0.7,
            "extra_slippage_pips_per_side": 0.1,
            "target_r": 1.5,
        },
        "windows": {
            "test": [
                "2024-01-01T00:00:00Z",
                "2024-12-31T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
    }


def parent() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2024-01-05T00:00:00Z"], utc=True
            ),
            "eligible_date": ["2024-01-05"],
            "decision_id": ["A"],
            "clock_minute": [0],
        }
    )


def events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": ["1", "2"],
            "event_time_utc": pd.to_datetime(
                [
                    "2024-01-05T10:00:00Z",
                    "2024-01-05T13:30:00Z",
                ],
                utc=True,
            ),
            "currency": ["EUR", "USD"],
            "title": ["ECB event", "Nonfarm Payrolls"],
            "tag": ["EU_ECB", "US_NonPay"],
        }
    )


def m5() -> pd.DataFrame:
    index = pd.to_datetime(
        [
            "2024-01-05T13:30:00Z",
            "2024-01-05T13:35:00Z",
            "2024-01-05T13:40:00Z",
            "2024-01-05T13:45:00Z",
        ],
        utc=True,
    )
    return pd.DataFrame(
        {
            "bid_open": [1.1000, 1.1002, 1.1005, 1.1008],
            "bid_high": [1.1004, 1.1007, 1.1009, 1.1010],
            "bid_low": [1.0998, 1.1000, 1.1003, 1.1006],
            "bid_close": [1.1002, 1.1005, 1.1008, 1.1009],
            "ask_open": [1.1001, 1.1003, 1.1006, 1.1009],
            "ask_high": [1.1005, 1.1008, 1.1010, 1.1011],
            "ask_low": [1.0999, 1.1001, 1.1004, 1.1007],
            "ask_close": [1.1003, 1.1006, 1.1009, 1.1010],
        },
        index=index,
    )


def test_latest_event_and_completed_observation_drive() -> None:
    candidates, census = build_candidates(
        parent(),
        m5(),
        events(),
        config(),
        enforce_frozen_census=False,
    )
    assert len(candidates) == 1
    candidate = candidates.iloc[0]
    assert candidate["event_ids"] == "2"
    assert candidate["entry_time_utc"] == pd.Timestamp(
        "2024-01-05T13:45:00Z"
    )
    assert candidate["momentum_side"] == "LONG"
    assert candidate["reversal_side"] == "SHORT"
    assert candidate["impulse_pips"] == pytest.approx(8.0)
    assert 4.0 <= candidate["risk_pips_long"] <= 25.0
    assert 4.0 <= candidate["risk_pips_short"] <= 25.0
    assert census["event_candidates"] == 1


def test_missing_observation_bar_is_cash() -> None:
    candidates, census = build_candidates(
        parent(),
        m5().drop(pd.Timestamp("2024-01-05T13:35:00Z")),
        events(),
        config(),
        enforce_frozen_census=False,
    )
    assert candidates.empty
    assert (
        census["cash_reasons"]["observation_or_entry_bar_missing"]
        == 1
    )
