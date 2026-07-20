from __future__ import annotations

import pandas as pd

from retracement import (
    build_pattern_rows,
    generate_candidates,
    select_source_events,
    timing_policy_grid,
)


def source_features(event_ms: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feature_time_utc": pd.to_datetime([event_ms, event_ms + 10], unit="ms", utc=True),
            "decision_timestamp_ms": [event_ms, event_ms + 10],
            "horizon_ms": [1000, 1000],
            "minimum_leg_move_bps": [0.3, 0.3],
            "consensus_sum_bps": [0.7, 0.7],
            "signed_xau_response_ratio": [-0.1, -0.1],
            "source_quote_count": [6, 6],
            "direction": ["LONG", "LONG"],
            "eurusd_move_bps": [0.35, 0.35],
            "usdjpy_move_bps": [-0.35, -0.35],
        }
    )


def locked_source_policy() -> dict[str, float | int]:
    return {
        "horizon_ms": 1000,
        "minimum_leg_move_bps": 0.25,
        "minimum_consensus_sum_bps": 0.5,
        "maximum_signed_xau_response_ratio": 0.0,
        "minimum_source_quote_count": 5,
    }


def test_source_selector_keeps_all_qualifying_events() -> None:
    selected = select_source_events(source_features(1000), policy=locked_source_policy())
    assert len(selected) == 2
    assert selected["source_event_id"].is_unique


def test_pattern_requires_transmission_then_retracement() -> None:
    event = 1_000_000
    selected = select_source_events(
        source_features(event).iloc[[0]].copy(), policy=locked_source_policy()
    )
    xau = pd.DataFrame(
        {
            "timestamp_ms": [event - 1, event + 100, event + 200, event + 300],
            "mid": [100.0, 100.01, 100.02, 100.01],
        }
    )
    patterns = build_pattern_rows(
        selected,
        xau,
        transmission_bps_grid=[1.0],
        retracement_fraction_grid=[0.5],
        maximum_pattern_seconds=1,
    )
    assert len(patterns) == 1
    assert int(patterns.iloc[0]["decision_timestamp_ms"]) == event + 300
    assert int(patterns.iloc[0]["transmission_delay_ms"]) == 100
    assert round(float(patterns.iloc[0]["favorable_peak_bps"]), 6) == 2.0


def test_timing_grid_registers_exactly_one_hundred_policies() -> None:
    calibration = {
        "transmission_bps_grid": [0.25, 0.5, 0.75, 1.0, 1.5],
        "retracement_fraction_grid": [0.25, 0.4, 0.5, 0.6, 0.75],
        "maximum_pattern_seconds_grid": [10, 20, 30, 60],
    }
    assert len(timing_policy_grid(calibration)) == 100


def test_candidate_router_uses_earliest_completed_pattern_per_date() -> None:
    patterns = pd.DataFrame(
        {
            "source_event_id": ["a", "b"],
            "source_event_timestamp_ms": [1, 2],
            "decision_timestamp_ms": [100, 200],
            "feature_time_utc": pd.to_datetime(
                ["2023-01-03T07:01:00Z", "2023-01-03T07:02:00Z"], utc=True
            ),
            "direction": ["LONG", "SHORT"],
            "transmission_bps": [1.0, 1.0],
            "retracement_fraction": [0.5, 0.5],
            "pattern_delay_ms": [9000, 9000],
        }
    )
    policy = {
        "transmission_bps": 1.0,
        "retracement_fraction": 0.5,
        "maximum_pattern_seconds": 10,
    }
    candidates = generate_candidates(patterns, policy=policy, family="TEST")
    assert len(candidates) == 1
    assert candidates.iloc[0]["direction"] == "LONG"
    assert str(candidates.iloc[0]["candidate_id"]).startswith("V80:")
