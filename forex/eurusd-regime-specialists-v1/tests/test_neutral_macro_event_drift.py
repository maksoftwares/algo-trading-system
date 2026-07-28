from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_macro_event_drift import (  # noqa: E402
    build_event_decisions,
    qualifying_events,
)


def config() -> dict:
    return {
        "event_source": {
            "prohibited_strategy_fields": [
                "impact",
                "actual",
                "forecast",
                "previous",
            ]
        },
        "event_filter": {
            "currencies": ["EUR", "USD"],
            "case_insensitive_title_fragments": {
                "EUR": ["ECB", "Harmonized Index of Consumer Prices"],
                "USD": ["Nonfarm Payrolls", "Consumer Price Index"],
            },
        },
        "strategy": {"lookback_hours": 24},
        "windows": {
            "test": [
                "2024-01-01T00:00:00Z",
                "2024-12-31T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
    }


def source() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": ["1", "2", "3"],
            "event_time_utc": pd.to_datetime(
                [
                    "2024-01-05T13:30:00Z",
                    "2024-01-05T13:30:00Z",
                    "2024-01-05T15:00:00Z",
                ],
                utc=True,
            ),
            "currency": ["USD", "USD", "USD"],
            "title": [
                "Nonfarm Payrolls",
                "Average Hourly Earnings",
                "Factory Orders",
            ],
            "tag": ["US_NonPay", "US_AveHouEar", "US_FacOrd"],
        }
    )


def parent() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2024-01-06T00:00:00Z"], utc=True
            ),
            "eligible_date": ["2024-01-06"],
            "decision_id": ["A"],
            "clock_minute": [0],
        }
    )


def m5() -> pd.DataFrame:
    index = pd.to_datetime(
        [
            "2024-01-05T13:25:00Z",
            "2024-01-05T23:55:00Z",
        ],
        utc=True,
    )
    return pd.DataFrame(
        {
            "bid_close": [1.1000, 1.1010],
            "ask_close": [1.1002, 1.1012],
        },
        index=index,
    )


def test_title_filter_ignores_source_impact() -> None:
    frame = source()
    frame["impact"] = ["0", "0", "2"]
    selected = qualifying_events(frame, config())
    assert selected["event_id"].tolist() == ["1"]


def test_latest_qualifying_cluster_and_completed_bars() -> None:
    events = qualifying_events(source(), config())
    decisions, census = build_event_decisions(
        parent(),
        m5(),
        events,
        config(),
        enforce_frozen_census=False,
    )
    assert len(decisions) == 1
    assert decisions.loc[0, "event_ids"] == "1"
    assert decisions.loc[0, "momentum_side"] == "LONG"
    assert decisions.loc[0, "reversal_side"] == "SHORT"
    assert decisions.loc[
        0, "event_to_entry_impulse_pips"
    ] == pytest.approx(10.0)
    assert census["event_candidates"] == 1


def test_missing_pre_event_bar_is_cash() -> None:
    events = qualifying_events(source(), config())
    decisions, census = build_event_decisions(
        parent(),
        m5().drop(pd.Timestamp("2024-01-05T13:25:00Z")),
        events,
        config(),
        enforce_frozen_census=False,
    )
    assert decisions.empty
    assert census["missing_pre_event_completed_bar"] == 1
