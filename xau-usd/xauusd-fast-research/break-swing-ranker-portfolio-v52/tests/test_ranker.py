from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.ranker import select_ranked


def test_ranked_execution_caps_one_open_and_one_per_day() -> None:
    scored = pd.DataFrame(
        {
            "event_id": ["a", "b", "c"],
            "entry_time": pd.to_datetime(
                [
                    "2026-01-05T09:00:00Z",
                    "2026-01-05T10:00:00Z",
                    "2026-01-06T09:00:00Z",
                ],
                utc=True,
            ),
            "exit_time": pd.to_datetime(
                [
                    "2026-01-05T11:00:00Z",
                    "2026-01-05T12:00:00Z",
                    "2026-01-06T10:00:00Z",
                ],
                utc=True,
            ),
            "model_score": [0.5, 0.6, 0.7],
            "score_threshold": [0.4, 0.4, 0.4],
            "regime": ["TREND_UP", "TREND_UP", "TREND_UP"],
            "stress_net_r": [1.0, 1.0, -1.0],
            "risk_usd": [3.0, 3.0, 3.0],
        }
    )
    result = select_ranked(
        scored,
        {
            "minimum_model_score": 0.0,
            "reject_unsafe_shock": True,
            "weekdays_only": True,
            "maximum_concurrent_positions": 1,
            "maximum_trades_per_utc_weekday": 1,
        },
    )
    assert result["event_id"].tolist() == ["a", "c"]


def test_ranked_execution_rejects_shock_weekend_and_low_score() -> None:
    scored = pd.DataFrame(
        {
            "event_id": ["low", "shock", "weekend"],
            "entry_time": pd.to_datetime(
                [
                    "2026-01-05T09:00:00Z",
                    "2026-01-06T09:00:00Z",
                    "2026-01-10T09:00:00Z",
                ],
                utc=True,
            ),
            "exit_time": pd.to_datetime(
                [
                    "2026-01-05T10:00:00Z",
                    "2026-01-06T10:00:00Z",
                    "2026-01-10T10:00:00Z",
                ],
                utc=True,
            ),
            "model_score": [0.2, 0.6, 0.7],
            "score_threshold": [0.4, 0.4, 0.4],
            "regime": ["TREND_UP", "UNSAFE_SHOCK", "TREND_UP"],
            "stress_net_r": [1.0, 1.0, 1.0],
            "risk_usd": [3.0, 3.0, 3.0],
        }
    )
    result = select_ranked(
        scored,
        {
            "minimum_model_score": 0.0,
            "reject_unsafe_shock": True,
            "weekdays_only": True,
            "maximum_concurrent_positions": 1,
            "maximum_trades_per_utc_weekday": 1,
        },
    )
    assert result.empty


def test_config_fixes_action_and_preserves_frequency_gate() -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads(
        (root / "config/break_swing_ranker_portfolio_v52.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["addon_policy"]["action_id"] == "SWING_2R_36H"
    assert config["addon_policy"]["maximum_concurrent_positions"] == 1
    assert config["gates"]["final_exam"]["minimum_combined_trades_per_weekday"] == 1.0
    assert config["research_controls"]["broker_action_authorized"] is False


def test_preregistration_disclaims_holdout_and_execution() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "no pristine-holdout claim" in text
    assert "broker action" in text
