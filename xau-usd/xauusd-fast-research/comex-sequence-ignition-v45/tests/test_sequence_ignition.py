from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sequence_ignition import (  # noqa: E402
    build_sequence_features,
    generate_candidates,
    policy_grid,
    select_policy,
)


RULE = {
    "family": "sequence_ignition_continuation",
    "tick_size": 0.1,
    "instrument_warmup_seconds": 0,
    "prior_window_seconds": 30,
    "current_window_seconds": 5,
    "minimum_current_directional_impulse_ticks": 1.0,
    "cooldown_minutes": 45,
}
POLICY = {
    "minimum_current_trade_count": 10,
    "minimum_terminal_run_trades": 5,
    "minimum_same_side_transition_share": 0.5,
    "minimum_absolute_current_imbalance": 0.2,
    "minimum_arrival_acceleration": 1.25,
}


def _events(include_future: bool = False) -> pd.DataFrame:
    start = pd.Timestamp("2024-01-02T13:20:00Z")
    rows = []
    for second in range(0, 26):
        rows.append(
            {
                "ts_event": start + pd.Timedelta(seconds=second),
                "instrument_id": 7,
                "side": "B" if second % 2 == 0 else "A",
                "price": 2050.0,
                "size": 1,
            }
        )
    for second in range(31, 36):
        for event in range(4):
            rows.append(
                {
                    "ts_event": start
                    + pd.Timedelta(seconds=second, microseconds=event * 100_000),
                    "instrument_id": 7,
                    "side": "B",
                    "price": 2050.0 + (second - 30) * 0.1,
                    "size": 1,
                }
            )
    if include_future:
        rows.append(
            {
                "ts_event": start + pd.Timedelta(seconds=50),
                "instrument_id": 7,
                "side": "A",
                "price": 1900.0,
                "size": 100,
            }
        )
    return pd.DataFrame(rows)


def test_persistent_accelerating_sequence_generates_long() -> None:
    features = build_sequence_features(_events(), rule=RULE)
    candidates = generate_candidates(features, policy=POLICY, rule=RULE)
    assert len(candidates) == 1
    row = candidates.iloc[0]
    assert row["direction"] == "LONG"
    assert row["last_event_utc"] < row["feature_time_utc"]
    assert row["terminal_run_trades"] >= 5
    assert row["arrival_acceleration"] >= 1.25
    assert row["current_directional_impulse_ticks"] >= 1.0


def test_future_event_does_not_change_first_candidate() -> None:
    first = generate_candidates(
        build_sequence_features(_events(), rule=RULE), policy=POLICY, rule=RULE
    )
    future = generate_candidates(
        build_sequence_features(_events(include_future=True), rule=RULE),
        policy=POLICY,
        rule=RULE,
    )
    assert first.iloc[0]["candidate_id"] == future.iloc[0]["candidate_id"]


def test_grid_has_exactly_one_thousand_registered_policies() -> None:
    config = {
        "calibration": {
            "minimum_current_trade_count_grid": [10, 20, 30, 40, 50],
            "minimum_terminal_run_trades_grid": [3, 5, 8, 13, 21],
            "minimum_same_side_transition_share_grid": [0.5, 0.6, 0.7, 0.8],
            "minimum_absolute_current_imbalance_grid": [0.2, 0.35, 0.5, 0.65, 0.8],
            "minimum_arrival_acceleration_grid": [1.25, 2.0],
        }
    }
    assert len(policy_grid(config)) == 1000


def test_selector_uses_density_and_strict_tiebreak() -> None:
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
            "minimum_current_trade_count": 20,
            "candidates_per_full_weekday": 3.0,
            "selection_eligible": True,
        },
    ]
    selected = select_policy(rows, {"target_candidates_per_full_weekday": 2.9})
    assert selected is not None
    assert selected["policy_id"] == "strict"
    assert not any("pnl" in key or "profit" in key for key in rows[0])
