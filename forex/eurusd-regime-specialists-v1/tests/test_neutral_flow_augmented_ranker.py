from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_flow_augmented_ranker import (  # noqa: E402
    TRAINING_WINDOW,
    build_campaign_points,
    fit_ranker,
    purged_training_points,
)


def config() -> dict:
    return {
        "strategy": {"required_trades_per_eligible_day": 4},
        "features": {
            "model_columns": [
                "contrast_aligned_return_1_atr",
                "flow_taker_imbalance_15m",
                "flow_return_15m",
            ]
        },
        "model": {
            "minimum_training_one_winner_pairs": 2,
            "penalty": "l2",
            "C": 0.1,
            "solver": "liblinear",
            "max_iter": 2000,
            "class_weight": "balanced",
            "decision_probability": 0.5,
            "random_state": 20260728,
        },
        "training_period": [
            "2020-01-01T00:00:00Z",
            "2021-12-31T23:59:59Z",
        ],
        "evaluation_windows": {
            "test": [
                "2022-01-01T00:00:00Z",
                "2022-12-31T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
    }


def points() -> pd.DataFrame:
    records: list[dict] = []
    for date in ("2020-01-06", "2022-01-03"):
        for minute in (0, 15, 30, 45):
            entry = pd.Timestamp(f"{date}T00:{minute:02d}:00Z")
            preferred_long = minute in (0, 30)
            records.append(
                {
                    "entry_time_utc": entry,
                    "eligible_date": date,
                    "decision_id": entry.strftime("%Y-%m-%dT%H%M"),
                    "contrast_aligned_return_1_atr": (
                        1.0 if preferred_long else -1.0
                    ),
                    "flow_taker_imbalance_15m": (
                        0.2 if preferred_long else -0.2
                    ),
                    "flow_return_15m": (
                        0.001 if preferred_long else -0.001
                    ),
                    "one_winner_label": True,
                    "preferred_long": preferred_long,
                    "pair_label_known_time_utc": (
                        entry + pd.Timedelta(hours=1)
                    ),
                }
            )
    return pd.DataFrame(records)


def source_census() -> dict:
    return {
        "eligible_complete_days": 2,
        "paired_decision_points": 8,
    }


def test_campaign_census_assigns_training_and_evaluation() -> None:
    frame, census = build_campaign_points(
        points(),
        source_census(),
        config(),
        enforce_frozen_census=False,
    )
    assert len(frame) == 8
    assert census["by_window"][TRAINING_WINDOW][
        "forced_trade_candidates"
    ] == 4
    assert census["by_window"]["test"]["forced_trade_candidates"] == 4
    assert census["eligible_day_exact_four_coverage"] == 1.0


def test_flow_features_enter_frozen_ranker() -> None:
    frame, _ = build_campaign_points(
        points(),
        source_census(),
        config(),
        enforce_frozen_census=False,
    )
    cutoff = pd.Timestamp("2022-01-01T00:00:00Z")
    training = purged_training_points(frame, cutoff)
    inference = frame[frame["window"].eq("test")]
    probabilities, coefficients = fit_ranker(
        training, inference, config()
    )
    assert len(training) == 4
    assert np.isfinite(probabilities).all()
    assert set(coefficients["feature"]) == set(
        config()["features"]["model_columns"]
    )


def test_label_known_at_cutoff_is_purged() -> None:
    frame = points()
    frame.loc[0, "pair_label_known_time_utc"] = pd.Timestamp(
        "2022-01-01T00:00:00Z"
    )
    training = purged_training_points(
        frame, pd.Timestamp("2022-01-01T00:00:00Z")
    )
    assert len(training) == 3
