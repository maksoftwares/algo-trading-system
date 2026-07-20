from __future__ import annotations

import pandas as pd

from same_direction_lead import (
    build_same_direction_features,
    generate_candidates,
    policy_grid,
)


def quotes(times: list[int], mids: list[float], spread: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_ms": times,
            "bid": [value - spread / 2 for value in mids],
            "ask": [value + spread / 2 for value in mids],
            "mid": mids,
        }
    )


def test_bond_up_maps_to_long_and_uses_strict_prior_xau() -> None:
    date = pd.Timestamp("2025-01-02T00:00:00Z")
    event = int(pd.Timestamp("2025-01-02T07:00:00Z").timestamp() * 1000)
    bond = quotes(
        [event - 1000, event - 100, event, event + 1000],
        [100.0, 100.0, 100.02, 100.03],
        0.02,
    )
    xau = quotes(
        [event - 1000, event - 1, event, event + 500],
        [2000.0, 2000.0, 1900.0, 1800.0],
        0.4,
    )
    rule = {
        "session_start_utc": "07:00",
        "session_end_utc": "18:00",
        "maximum_baseline_staleness_ms": 1000,
        "maximum_current_xau_staleness_ms": 1000,
    }
    prefilter = {
        "minimum_absolute_source_move_bps": 0.1,
        "minimum_directional_innovation_bps": 0.1,
        "maximum_signed_xau_response_ratio": 0.75,
        "minimum_source_quote_count": 2,
    }
    result = build_same_direction_features(
        date, bond, xau, horizons_ms=[1000], rule=rule, prefilter=prefilter
    )
    assert not result.empty
    assert result.iloc[0]["direction"] == "LONG"
    assert (
        result.iloc[0]["xau_current_timestamp_ms"]
        < result.iloc[0]["decision_timestamp_ms"]
    )
    assert result.iloc[0]["xau_move_bps"] == 0.0


def test_grid_registers_exactly_one_thousand_policies() -> None:
    calibration = {
        "horizon_ms_grid": [1000, 2000, 5000, 10000, 20000],
        "minimum_absolute_source_move_bps_grid": [0.1, 0.2, 0.3, 0.4, 0.5],
        "minimum_directional_innovation_bps_grid": [0.1, 0.2, 0.3, 0.4, 0.5],
        "maximum_signed_xau_response_ratio_grid": [0, 0.25, 0.5, 0.75],
        "minimum_source_quote_count_grid": [2, 5],
    }
    assert len(policy_grid(calibration)) == 1000


def test_candidate_router_keeps_first_per_date() -> None:
    features = pd.DataFrame(
        {
            "feature_time_utc": pd.to_datetime(
                ["2025-01-02T07:01:00Z", "2025-01-02T07:02:00Z"], utc=True
            ),
            "decision_timestamp_ms": [1, 2],
            "horizon_ms": [1000, 1000],
            "source_move_bps": [1.0, -1.2],
            "directional_innovation_bps": [0.7, 0.8],
            "signed_xau_response_ratio": [0.2, 0.1],
            "source_quote_count": [5, 6],
            "direction": ["LONG", "SHORT"],
        }
    )
    policy = {
        "horizon_ms": 1000,
        "minimum_absolute_source_move_bps": 0.1,
        "minimum_directional_innovation_bps": 0.1,
        "maximum_signed_xau_response_ratio": 0.75,
        "minimum_source_quote_count": 2,
    }
    result = generate_candidates(features, policy=policy, family="TEST")
    assert len(result) == 1
    assert result.iloc[0]["direction"] == "LONG"
    assert str(result.iloc[0]["candidate_id"]).startswith("V76:")
