from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flow_transition import (  # noqa: E402
    build_transition_features,
    generate_candidates,
    policy_grid,
    select_policy,
)


RULE = {
    "family": "flow_exhaustion_flip",
    "tick_size": 0.1,
    "instrument_warmup_seconds": 0,
    "prior_window_seconds": 30,
    "current_window_seconds": 5,
    "minimum_current_acceleration": 0.1,
    "minimum_current_directional_impulse_ticks": 1.0,
    "cooldown_minutes": 45,
}
POLICY = {
    "minimum_prior_volume": 20,
    "minimum_absolute_prior_imbalance": 0.5,
    "maximum_prior_directional_impact_efficiency": 0.1,
    "minimum_current_volume": 5,
    "minimum_absolute_current_imbalance": 0.5,
}


def _events(include_future: bool = False) -> pd.DataFrame:
    start = pd.Timestamp("2024-01-02T13:20:00Z")
    rows = []
    for second in range(0, 26):
        rows.append(
            {
                "ts_event": start + pd.Timedelta(seconds=second),
                "instrument_id": 7,
                "side": "B",
                "price": 2050.0,
                "size": 2,
            }
        )
    for offset, second in enumerate(range(31, 36), start=1):
        rows.append(
            {
                "ts_event": start + pd.Timedelta(seconds=second),
                "instrument_id": 7,
                "side": "A",
                "price": 2050.0 - offset * 0.1,
                "size": 2,
            }
        )
    if include_future:
        rows.append(
            {
                "ts_event": start + pd.Timedelta(seconds=50),
                "instrument_id": 7,
                "side": "B",
                "price": 2100.0,
                "size": 100,
            }
        )
    return pd.DataFrame(rows)


def test_completed_flow_flip_generates_short_candidate() -> None:
    features = build_transition_features(_events(), rule=RULE)
    candidates = generate_candidates(features, policy=POLICY, rule=RULE)
    assert len(candidates) == 1
    row = candidates.iloc[0]
    assert row["direction"] == "SHORT"
    assert row["last_event_utc"] < row["feature_time_utc"]
    assert row["prior_imbalance_30s"] > 0
    assert row["current_imbalance_5s"] < 0
    assert row["current_directional_impulse_ticks"] >= 1.0


def test_future_event_does_not_change_first_causal_candidate() -> None:
    first = generate_candidates(
        build_transition_features(_events(), rule=RULE), policy=POLICY, rule=RULE
    )
    with_future = generate_candidates(
        build_transition_features(_events(include_future=True), rule=RULE),
        policy=POLICY,
        rule=RULE,
    )
    assert first.iloc[0]["candidate_id"] == with_future.iloc[0]["candidate_id"]


def test_registered_grid_contains_exactly_one_thousand_policies() -> None:
    config = {
        "calibration": {
            "minimum_prior_volume_grid": [60, 100, 140, 180, 220],
            "minimum_absolute_prior_imbalance_grid": [0.15, 0.25, 0.35, 0.45, 0.55],
            "maximum_prior_directional_impact_efficiency_grid": [0.0, 0.02, 0.05, 0.1],
            "minimum_current_volume_grid": [10, 20, 30, 40, 50],
            "minimum_absolute_current_imbalance_grid": [0.2, 0.4],
        }
    }
    assert len(policy_grid(config)) == 1000


def test_selector_uses_density_and_prefers_stricter_policy() -> None:
    rows = [
        {
            **POLICY,
            "policy_id": "loose",
            "candidates_per_full_weekday": 2.8,
            "selection_eligible": True,
        },
        {
            **POLICY,
            "policy_id": "strict",
            "minimum_prior_volume": 100,
            "candidates_per_full_weekday": 3.0,
            "selection_eligible": True,
        },
    ]
    selected = select_policy(rows, {"target_candidates_per_full_weekday": 2.9})
    assert selected is not None
    assert selected["policy_id"] == "strict"
    assert not any("pnl" in key or "profit" in key for key in rows[0])
