from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from quote_microburst import (
    build_microburst_features,
    generate_candidates,
    label_candidates,
    policy_grid,
    select_policy,
    session_quality,
)


ROOT = Path(__file__).resolve().parents[1]


def config() -> dict:
    return json.loads(
        (ROOT / "config" / "dukascopy_quote_microburst_continuation_v87.json")
        .read_text()
    )


def quotes() -> pd.DataFrame:
    start = int(pd.Timestamp("2019-01-02T06:59:58Z").timestamp() * 1000)
    times = [start + index * 100 for index in range(260)]
    mid = [1280.0] * 25
    mid += [1280.0 + 0.05 * index for index in range(1, 236)]
    return pd.DataFrame(
        {
            "timestamp_ms": times,
            "bid": [value - 0.10 for value in mid],
            "ask": [value + 0.10 for value in mid],
            "mid": mid,
        }
    )


def policy() -> dict:
    return {
        "lookback_ms": 1000,
        "minimum_nonzero_mid_updates": 5,
        "minimum_absolute_update_imbalance": 0.5,
        "minimum_absolute_displacement_bps": 1.0,
        "maximum_spread_bps": 3.0,
    }


def test_policy_registry_contains_exactly_one_thousand_policies() -> None:
    policies = policy_grid(config()["calibration"])
    assert len(policies) == 1000
    assert len({tuple(sorted(item.items())) for item in policies}) == 1000


def test_candidate_is_causal_and_stable_under_future_append() -> None:
    values = config()
    date = pd.Timestamp("2019-01-02T00:00:00Z")
    frame = quotes()
    features = build_microburst_features(
        date, frame, lookback_ms=1000, rule=values["candidate_rule"]
    )
    candidate = generate_candidates(
        features, policy=policy(), rule=values["candidate_rule"]
    )
    assert len(candidate) == 1
    assert candidate.iloc[0]["direction"] == "LONG"
    cutoff = int(candidate.iloc[0]["decision_timestamp_ms"])
    prefix = frame.loc[frame["timestamp_ms"].le(cutoff)]
    prefix_features = build_microburst_features(
        date, prefix, lookback_ms=1000, rule=values["candidate_rule"]
    )
    prefix_candidate = generate_candidates(
        prefix_features, policy=policy(), rule=values["candidate_rule"]
    )
    columns = ["candidate_id", "decision_timestamp_ms", "direction"]
    pd.testing.assert_frame_equal(
        candidate[columns].reset_index(drop=True),
        prefix_candidate[columns].reset_index(drop=True),
    )


def test_candidate_uses_first_false_to_true_crossing_and_one_daily_event() -> None:
    values = config()
    date = pd.Timestamp("2019-01-02T00:00:00Z")
    features = build_microburst_features(
        date, quotes(), lookback_ms=1000, rule=values["candidate_rule"]
    )
    candidate = generate_candidates(
        features, policy=policy(), rule=values["candidate_rule"]
    )
    assert len(candidate) == 1
    assert candidate["date_utc"].nunique() == 1
    assert float(candidate.iloc[0]["signed_update_imbalance"]) > 0
    assert float(candidate.iloc[0]["displacement_bps"]) > 0


def test_side_correct_label_includes_slippage_and_ticket_cost() -> None:
    values = config()
    values["execution"]["hold_seconds"] = 1
    date = pd.Timestamp("2019-01-02T00:00:00Z")
    frame = quotes()
    features = build_microburst_features(
        date, frame, lookback_ms=1000, rule=values["candidate_rule"]
    )
    candidate = generate_candidates(
        features, policy=policy(), rule=values["candidate_rule"]
    )
    labels = label_candidates(candidate, quotes=frame, config=values)
    assert labels.iloc[0]["status"] == "RESOLVED"
    decision = int(candidate.iloc[0]["decision_timestamp_ms"])
    entry = frame.loc[frame["timestamp_ms"] > decision].iloc[0]
    target = int(entry["timestamp_ms"]) + 1000
    exit_quote = frame.loc[frame["timestamp_ms"] >= target].iloc[0]
    observed = float(exit_quote["bid"] - entry["ask"])
    assert abs(float(labels.iloc[0]["observed_move_usd"]) - observed) < 1e-12
    expected = observed - 0.10 - 0.30
    assert abs(float(labels.iloc[0]["baseline_net_pnl_usd"]) - expected) < 1e-12


def test_density_selection_uses_no_economic_field() -> None:
    calibration = config()["calibration"]
    rows = [
        {
            **policy(),
            "policy_id": "weak",
            "candidates_per_full_weekday": 1.0,
            "selection_eligible": True,
        },
        {
            **{**policy(), "minimum_absolute_displacement_bps": 2.0},
            "policy_id": "strong",
            "candidates_per_full_weekday": 1.0,
            "selection_eligible": True,
        },
    ]
    assert select_policy(rows, calibration)["policy_id"] == "strong"


def test_session_quality_rejects_incomplete_coverage() -> None:
    values = config()
    date = pd.Timestamp("2019-01-02T00:00:00Z")
    quality = session_quality(date, quotes(), values["candidate_rule"])
    assert quality["eligible_full_weekday"] is False
