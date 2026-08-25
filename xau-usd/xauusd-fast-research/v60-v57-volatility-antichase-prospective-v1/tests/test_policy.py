from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.policy import apply_policy


POLICY = {
    "minimum_prior_source_closed_trades": 50,
    "anti_chase_direction": "LONG",
    "anti_chase_maximum_causal_rank_exclusive": 0.1,
    "anti_chase_minimum_atr_ratio_inclusive": 1.2,
    "anti_chase_maximum_distance_to_24h_high_atr_exclusive": 1.0,
}


def row(**changes):
    value = {
        "candidate_id": "candidate",
        "baseline_executed": True,
        "broker_outcome_resolved": False,
        "causal_rank": 0.09,
        "prior_source_executed_count": 50,
    }
    value.update(changes)
    return value


def decision(**changes):
    value = {
        "candidate_direction": "LONG",
        "feature_bar_time_utc": "2026-08-26T00:00:00Z",
        "atr_ratio": 1.2,
        "dist_hi_24h": 0.99,
    }
    value.update(changes)
    return value


def test_policy_vetoes_only_complete_mature_strict_match() -> None:
    rows = [row()]
    apply_policy(rows, {"candidate": decision()}, POLICY)
    assert rows[0]["would_veto"] is True


def test_missing_feature_and_boundaries_retain() -> None:
    cases = [
        (row(), decision(atr_ratio=None)),
        (row(causal_rank=0.1), decision()),
        (row(), decision(atr_ratio=1.1999)),
        (row(), decision(dist_hi_24h=1.0)),
        (row(prior_source_executed_count=49), decision()),
    ]
    for candidate, features in cases:
        rows = [candidate]
        apply_policy(rows, {"candidate": features}, POLICY)
        assert rows[0]["would_veto"] is False
