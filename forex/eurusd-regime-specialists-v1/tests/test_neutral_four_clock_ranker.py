from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_four_clock_ranker import (  # noqa: E402
    build_paired_points,
    fit_ranker,
    purged_training_points,
    route_predictions,
)


def config() -> dict:
    return {
        "strategy": {
            "entry_hour_utc": 0,
            "entry_minutes_utc": [0, 15, 30, 45],
            "required_trades_per_eligible_day": 4,
        },
        "features": {
            "contrast_columns": ["aligned_return_1_atr"],
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
        "execution": {
            "risk_per_trade_portfolio_r": 0.25,
        },
        "training_period": [
            "2019-01-01T00:00:00Z",
            "2020-12-31T23:59:59Z",
        ],
        "evaluation_windows": {
            "test": [
                "2021-01-01T00:00:00Z",
                "2021-12-31T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
    }


def source(
    *,
    date: str = "2021-01-04",
    complete: bool = True,
    include_outcomes: bool = True,
) -> pd.DataFrame:
    minutes = [0, 15, 30, 45] if complete else [0, 15, 30]
    records: list[dict] = []
    for minute in minutes:
        entry = pd.Timestamp(f"{date}T00:{minute:02d}:00Z")
        signal = entry - pd.Timedelta(minutes=5)
        for side in ("LONG", "SHORT"):
            long = side == "LONG"
            row = {
                "side": side,
                "signal_time_utc": signal,
                "completion_time_utc": entry,
                "entry_time_utc": entry,
                "aligned_return_1_atr": 1.0 if long else -1.0,
            }
            if include_outcomes:
                target = (minute // 15) % 2 == 0
                target_first = target if long else not target
                row.update(
                    {
                        "exit_time_utc": entry
                        + pd.Timedelta(hours=1),
                        "entry_price": 1.1001 if long else 1.1000,
                        "stop_price": 1.0997 if long else 1.1004,
                        "target_price": 1.1007 if long else 1.0994,
                        "exit_price": 1.10069 if long else 1.09941,
                        "exit_reason": (
                            "TARGET" if target_first else "STOP"
                        ),
                        "risk_distance": 0.0004,
                        "risk_pips": 4.0,
                        "outcome_r": 1.475 if target_first else -1.025,
                        "target_first": target_first,
                        "fixed_0p01_lot_usd": (
                            0.59 if target_first else -0.41
                        ),
                        "oracle_member": int(target_first),
                    }
                )
            records.append(row)
    return pd.DataFrame(records)


def test_builds_four_paired_contrasts() -> None:
    points, census = build_paired_points(
        source(include_outcomes=False),
        config(),
        include_outcomes=False,
        enforce_frozen_census=False,
    )
    assert len(points) == 4
    assert points["contrast_aligned_return_1_atr"].eq(2.0).all()
    assert census["eligible_day_exact_four_coverage"] == 1.0


def test_incomplete_day_is_excluded() -> None:
    points, census = build_paired_points(
        source(complete=False, include_outcomes=False),
        config(),
        include_outcomes=False,
        enforce_frozen_census=False,
    )
    assert points.empty
    assert census["eligible_complete_days"] == 0


def test_purge_requires_label_known_before_cutoff() -> None:
    points, _ = build_paired_points(
        source(date="2020-12-31"),
        config(),
        include_outcomes=True,
        enforce_frozen_census=False,
    )
    cutoff = pd.Timestamp("2020-12-31T00:30:00Z")
    training = purged_training_points(points, cutoff)
    assert training.empty


def test_ranker_and_router_force_one_side_per_clock() -> None:
    training_sources = pd.concat(
        [
            source(date="2019-01-07"),
            source(date="2019-01-08"),
        ],
        ignore_index=True,
    )
    training, _ = build_paired_points(
        training_sources,
        config(),
        include_outcomes=True,
        enforce_frozen_census=False,
    )
    inference, _ = build_paired_points(
        source(date="2021-01-04"),
        config(),
        include_outcomes=True,
        enforce_frozen_census=False,
    )
    probabilities, coefficients = fit_ranker(
        training, inference, config()
    )
    trades, predicted = route_predictions(
        inference, probabilities, config()
    )
    assert len(coefficients) == 1
    assert len(trades) == 4
    assert len(predicted) == 4
    assert trades["entry_time_utc"].nunique() == 4
    assert np.isfinite(probabilities).all()
    assert abs(
        trades["portfolio_r"].sum()
        - 0.25 * trades["r"].sum()
    ) < 1e-12
