from __future__ import annotations

import pandas as pd

from fx_consensus import build_consensus_features, generate_candidates, policy_grid


def quotes(times: list[int], mids: list[float], spread: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_ms": times,
            "bid": [value - spread / 2 for value in mids],
            "ask": [value + spread / 2 for value in mids],
            "mid": mids,
        }
    )


def feature_inputs() -> tuple[pd.Timestamp, int, dict[str, object], dict[str, object]]:
    date = pd.Timestamp("2023-01-03T00:00:00Z")
    event = int(pd.Timestamp("2023-01-03T07:00:00Z").timestamp() * 1000)
    rule: dict[str, object] = {
        "session_start_utc": "07:00",
        "session_end_utc": "18:00",
        "maximum_baseline_staleness_ms": 1000,
        "maximum_current_source_staleness_ms": 1000,
        "maximum_current_xau_staleness_ms": 1000,
    }
    prefilter: dict[str, object] = {
        "minimum_leg_move_bps": 0.05,
        "minimum_consensus_sum_bps": 0.1,
        "maximum_signed_xau_response_ratio": 0.75,
        "minimum_source_quote_count": 2,
    }
    return date, event, rule, prefilter


def test_consensus_dollar_weakness_maps_long_and_xau_is_strictly_prior() -> None:
    date, event, rule, prefilter = feature_inputs()
    eurusd = quotes(
        [event - 1000, event - 100, event], [1.0, 1.0, 1.0002], 0.0001
    )
    usdjpy = quotes(
        [event - 1000, event - 100, event], [100.0, 100.0, 99.98], 0.01
    )
    xau = quotes(
        [event - 1000, event - 1, event, event + 100],
        [2000.0, 2000.0, 1900.0, 1800.0],
        0.4,
    )
    result = build_consensus_features(
        date,
        eurusd,
        usdjpy,
        xau,
        horizons_ms=[1000],
        rule=rule,
        prefilter=prefilter,
    )
    assert not result.empty
    assert result.iloc[0]["direction"] == "LONG"
    assert result.iloc[0]["usdjpy_current_timestamp_ms"] <= event
    assert result.iloc[0]["xau_current_timestamp_ms"] < event
    assert result.iloc[0]["xau_move_bps"] == 0.0


def test_disagreeing_fx_legs_abstain() -> None:
    date, event, rule, prefilter = feature_inputs()
    eurusd = quotes(
        [event - 1000, event - 100, event], [1.0, 1.0, 1.0002], 0.0001
    )
    usdjpy = quotes(
        [event - 1000, event - 100, event], [100.0, 100.0, 100.02], 0.01
    )
    xau = quotes([event - 1000, event - 1], [2000.0, 2000.0], 0.4)
    result = build_consensus_features(
        date,
        eurusd,
        usdjpy,
        xau,
        horizons_ms=[1000],
        rule=rule,
        prefilter=prefilter,
    )
    assert result.empty


def test_grid_registers_exactly_one_thousand_policies() -> None:
    calibration = {
        "horizon_ms_grid": [1000, 2000, 5000, 10000, 20000],
        "minimum_leg_move_bps_grid": [0.05, 0.1, 0.15, 0.2, 0.25],
        "minimum_consensus_sum_bps_grid": [0.1, 0.2, 0.3, 0.4, 0.5],
        "maximum_signed_xau_response_ratio_grid": [0, 0.25, 0.5, 0.75],
        "minimum_source_quote_count_grid": [2, 5],
    }
    assert len(policy_grid(calibration)) == 1000


def test_candidate_router_keeps_first_per_date() -> None:
    features = pd.DataFrame(
        {
            "feature_time_utc": pd.to_datetime(
                ["2023-01-03T07:01:00Z", "2023-01-03T07:02:00Z"], utc=True
            ),
            "decision_timestamp_ms": [1, 2],
            "horizon_ms": [1000, 1000],
            "minimum_leg_move_bps": [0.3, 0.4],
            "consensus_sum_bps": [0.7, 0.8],
            "signed_xau_response_ratio": [0.2, 0.1],
            "source_quote_count": [5, 6],
            "direction": ["LONG", "SHORT"],
        }
    )
    policy = {
        "horizon_ms": 1000,
        "minimum_leg_move_bps": 0.05,
        "minimum_consensus_sum_bps": 0.1,
        "maximum_signed_xau_response_ratio": 0.75,
        "minimum_source_quote_count": 2,
    }
    result = generate_candidates(features, policy=policy, family="TEST")
    assert len(result) == 1
    assert result.iloc[0]["direction"] == "LONG"
    assert str(result.iloc[0]["candidate_id"]).startswith("V78:")
