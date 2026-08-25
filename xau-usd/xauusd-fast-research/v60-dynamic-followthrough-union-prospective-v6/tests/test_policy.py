from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.policy import apply_dynamic_union, refresh_status


V2 = {
    "minimum_prior_source_closed_trades": 50,
    "lookback_closed_trades": 20,
    "maximum_prior_profit_factor_exclusive": 1.0,
    "maximum_causal_rank_exclusive": 0.1,
}
ANTI = {
    "source_id": "V57",
    "direction": "LONG",
    "minimum_prior_source_closed_trades": 50,
    "maximum_causal_rank_exclusive": 0.1,
    "minimum_atr_ratio_inclusive": 1.2,
    "maximum_distance_to_24h_high_atr_exclusive": 1.0,
    "minimum_ret_24h_exclusive": 0.0,
    "maximum_ret_4h_to_ret_24h_exclusive": 0.7,
}


def warm_start():
    return {
        "retained_history_counts_by_source": {"V57": 50},
        "rows": [
            {
                "candidate_id": f"warm-{index}",
                "source_id": "V57",
                "closed_at_utc": f"2026-06-{index + 1:02d}T00:00:00Z",
                "pnl_usd": 1.0,
            }
            for index in range(20)
        ],
    }


def row(candidate_id: str, entry: str, pnl: float):
    return {
        "candidate_id": candidate_id,
        "event_id": candidate_id,
        "source_id": "V57",
        "entry_time_utc": entry,
        "baseline_executed": True,
        "broker_outcome_resolved": True,
        "broker_pnl_usd": pnl,
    }


def decision(*, weak: bool):
    return {
        "reason": "SCORE_COMPLETE",
        "rank": 0.09,
        "score": 1.0,
        "candidate_direction": "LONG",
        "feature_bar_time_utc": "2026-08-26T00:55:00Z",
        "atr_ratio": 1.3,
        "dist_hi_24h": 0.2,
        "ret_4h": 6.0 if weak else 8.0,
        "ret_24h": 10.0,
        "rv_1h": 1.0,
        "rv_24h": 1.0,
        "slope_atr": 1.0,
        "ret_1h": 1.0,
        "dist_lo_24h": 1.0,
    }


def outcome(candidate_id: str, opened: str, closed: str, pnl: float):
    return {
        "source_id": "V57",
        "opened_at_utc": opened,
        "closed_at_utc": closed,
        "pnl_usd": pnl,
    }


def test_vetoed_outcome_is_excluded_from_future_dynamic_state() -> None:
    rows = [
        row("a", "2026-08-26T01:00:00Z", -5.0),
        row("b", "2026-08-26T02:00:00Z", 2.0),
    ]
    decisions = {"a": decision(weak=True), "b": decision(weak=False)}
    outcomes = {
        "a": outcome("a", "2026-08-26T01:00:01Z", "2026-08-26T01:30:00Z", -5.0),
        "b": outcome("b", "2026-08-26T02:00:01Z", "2026-08-26T02:30:00Z", 2.0),
    }
    apply_dynamic_union(
        rows,
        decisions,
        warm_start=warm_start(),
        broker_outcomes=outcomes,
        boundary=__import__("datetime").datetime.fromisoformat("2026-08-26T00:00:00+00:00"),
        v2_policy=V2,
        anti_rule=ANTI,
    )
    assert rows[0]["anti_chase_veto_proposal"]
    assert rows[0]["would_veto"]
    assert rows[1]["prior_source_executed_count"] == 50


def test_retained_closed_outcome_enters_future_dynamic_state() -> None:
    rows = [
        row("a", "2026-08-26T01:00:00Z", 2.0),
        row("b", "2026-08-26T02:00:00Z", 2.0),
    ]
    decisions = {"a": decision(weak=False), "b": decision(weak=False)}
    outcomes = {
        "a": outcome("a", "2026-08-26T01:00:01Z", "2026-08-26T01:30:00Z", 2.0),
        "b": outcome("b", "2026-08-26T02:00:01Z", "2026-08-26T02:30:00Z", 2.0),
    }
    apply_dynamic_union(
        rows,
        decisions,
        warm_start=warm_start(),
        broker_outcomes=outcomes,
        boundary=__import__("datetime").datetime.fromisoformat("2026-08-26T00:00:00+00:00"),
        v2_policy=V2,
        anti_rule=ANTI,
    )
    assert not rows[0]["would_veto"]
    assert rows[1]["prior_source_executed_count"] == 51


def component_acceptance():
    return {
        "minimum_scored_executed_candidates": 20,
        "minimum_resolved_vetoes": 20,
        "minimum_resolved_v2_vetoes": 10,
        "minimum_resolved_anti_chase_vetoes": 10,
        "maximum_veto_broker_profit_factor_exclusive": 0.8,
        "minimum_avoided_broker_pnl_usd_exclusive": 0.0,
        "maximum_v2_veto_broker_profit_factor_exclusive": 0.8,
        "minimum_v2_avoided_broker_pnl_usd_exclusive": 0.0,
        "maximum_anti_chase_veto_broker_profit_factor_exclusive": 0.8,
        "minimum_anti_chase_avoided_broker_pnl_usd_exclusive": 0.0,
    }


def resolved_component_row(index: int, component: str):
    return {
        "candidate_id": f"resolved-{index}",
        "baseline_executed": True,
        "causal_rank": 0.01,
        "would_veto": True,
        "v2_veto_proposal": component == "V2",
        "anti_chase_veto_proposal": component == "ANTI_CHASE",
        "broker_outcome_resolved": True,
        "broker_pnl_usd": -1.0,
    }


def test_component_gates_require_independent_v2_and_antichase_evidence() -> None:
    rows = [
        *[resolved_component_row(index, "V2") for index in range(10)],
        *[
            resolved_component_row(index + 10, "ANTI_CHASE")
            for index in range(10)
        ],
    ]
    status = {"counts": {}, "gates": {}}

    refresh_status(status, rows, component_acceptance())

    assert status["counts"]["resolved_v2_vetoes"] == 10
    assert status["counts"]["resolved_anti_chase_vetoes"] == 10
    assert status["gates"]["minimum_resolved_v2_vetoes"]
    assert status["gates"]["minimum_resolved_anti_chase_vetoes"]
    assert status["gates"]["positive_v2_avoided_broker_pnl"]
    assert status["gates"]["positive_anti_chase_avoided_broker_pnl"]


def test_union_cannot_pass_without_antichase_component_evidence() -> None:
    rows = [resolved_component_row(index, "V2") for index in range(20)]
    status = {"counts": {}, "gates": {}}

    refresh_status(status, rows, component_acceptance())

    assert status["gates"]["minimum_resolved_vetoes"]
    assert status["gates"]["minimum_resolved_v2_vetoes"]
    assert not status["gates"]["minimum_resolved_anti_chase_vetoes"]
    assert not status["gates"]["anti_chase_veto_broker_profit_factor"]
    assert not status["gates"]["positive_anti_chase_avoided_broker_pnl"]
