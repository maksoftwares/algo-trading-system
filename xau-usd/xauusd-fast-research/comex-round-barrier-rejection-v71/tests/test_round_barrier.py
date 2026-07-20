from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from round_barrier import (  # noqa: E402
    build_barrier_features,
    generate_candidates,
    policy_grid,
)


def rule() -> dict[str, object]:
    return {
        "family": "ROUND_BARRIER_REJECTION",
        "instrument_warmup_seconds": 0,
        "current_flow_seconds": 5,
        "maximum_initial_level_distance_fraction": 0.5,
        "level_spacing_usd_grid": [5.0],
        "lookback_seconds_grid": [5],
        "minimum_materialized_probe_usd": 0.0,
        "minimum_materialized_rejection_usd": 0.2,
        "minimum_materialized_opposite_flow_imbalance": 0.1,
    }


def policy() -> dict[str, object]:
    return {
        "level_spacing_usd": 5.0,
        "lookback_seconds": 5,
        "minimum_probe_usd": 0.1,
        "minimum_rejection_usd": 0.4,
        "minimum_opposite_flow_imbalance": 0.1,
    }


def upward_rejection_trades() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts_event": pd.to_datetime(
                [
                    "2025-01-02T11:59:59.100Z",
                    "2025-01-02T12:00:04.100Z",
                    "2025-01-02T12:00:04.500Z",
                ],
                utc=True,
            ),
            "instrument_id": [1, 1, 1],
            "side": ["B", "B", "A"],
            "price": [2004.8, 2005.2, 2004.4],
            "size": [1, 1, 10],
        }
    )


def test_upward_round_level_probe_rejects_to_short() -> None:
    features = build_barrier_features(upward_rejection_trades(), rule=rule())
    candidates = generate_candidates(features, policy=policy(), rule=rule())
    assert len(candidates) == 1
    assert candidates["direction"].iloc[0] == "SHORT"
    assert candidates["barrier_level"].iloc[0] == 2005.0
    assert candidates["probe_usd"].iloc[0] == pytest.approx(0.2)
    assert candidates["rejection_usd"].iloc[0] == pytest.approx(0.6)


def test_features_use_only_events_strictly_before_decision() -> None:
    features = build_barrier_features(upward_rejection_trades(), rule=rule())
    assert (features["last_event_utc"] < features["feature_time_utc"]).all()


def test_candidate_router_keeps_first_event_per_utc_date() -> None:
    first = build_barrier_features(upward_rejection_trades(), rule=rule())
    second = first.copy()
    second["feature_time_utc"] += pd.Timedelta(minutes=1)
    selected = generate_candidates(
        pd.concat([first, second], ignore_index=True), policy=policy(), rule=rule()
    )
    assert len(selected) == 1
    assert selected["feature_time_utc"].iloc[0] == first["feature_time_utc"].min()


def test_policy_grid_contains_exactly_one_thousand_rules() -> None:
    config = {
        "calibration": {
            "level_spacing_usd_grid": [1.0, 2.0, 5.0, 10.0, 20.0],
            "lookback_seconds_grid": [10, 20, 30, 60, 120],
            "minimum_probe_usd_grid": [0.0, 0.1, 0.2, 0.3, 0.4],
            "minimum_rejection_usd_grid": [0.2, 0.4, 0.6, 0.8],
            "minimum_opposite_flow_imbalance_grid": [0.1, 0.25],
        }
    }
    assert len(policy_grid(config)) == 1000


def test_directional_flow_must_confirm_the_rejection() -> None:
    features = build_barrier_features(upward_rejection_trades(), rule=rule())
    features["current_flow_imbalance"] = 0.9
    assert generate_candidates(features, policy=policy(), rule=rule()).empty
