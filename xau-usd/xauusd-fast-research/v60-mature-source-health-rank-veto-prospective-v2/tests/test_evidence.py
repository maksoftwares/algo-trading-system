from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.evidence import (
    add_forward_comparison,
    annotate_decision_timing,
    attach_execution_details,
    build_equity_mark,
    load_chain,
    update_equity_marks,
    update_evidence_chain,
)


def candidate(
    candidate_id: str,
    pnl: float,
    *,
    would_veto: bool,
    rank: float = 0.05,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "event_id": candidate_id,
        "source_id": "R1_PULLBACK",
        "entry_time_utc": f"2026-08-26T0{candidate_id}:00:00Z",
        "baseline_executed": True,
        "causal_score": 0.25,
        "causal_rank": rank,
        "prior_source_executed_count": 75,
        "prior_health_window_count": 20,
        "prior_executed_profit_factor": 0.7,
        "would_veto": would_veto,
        "prospective_decision_timing_valid": True,
        "prospective_veto_effective": would_veto,
        "broker_outcome_resolved": True,
        "broker_exit_time_utc": f"2026-08-26T1{candidate_id}:00:00Z",
        "broker_pnl_usd": pnl,
        "broker_exit_fills": [
            {
                "deal_ticket": 1000 + int(candidate_id),
                "exit_time_utc": f"2026-08-26T1{candidate_id}:00:00Z",
                "volume_lots": 0.01,
                "exit_price": 4702.0,
                "pnl_usd": pnl,
            }
        ],
        "broker_execution": {
            "ticket": int(candidate_id),
            "broker_entry_time_utc": f"2026-08-26T0{candidate_id}:00:01Z",
            "direction": "LONG",
            "volume_lots": 0.01,
            "entry_price": 4700.0,
            "entry_cost_usd": 0.0,
        },
    }


def test_evidence_chain_is_idempotent_and_rejects_decision_drift(tmp_path) -> None:
    resolved_row = candidate("1", -10.0, would_veto=True)
    open_row = dict(
        resolved_row,
        broker_outcome_resolved=False,
        broker_exit_time_utc=None,
        broker_pnl_usd=None,
    )
    open_row.pop("broker_exit_fills")
    rows = [open_row]
    first_observation = datetime(2026, 8, 26, 1, 1, tzinfo=UTC)
    first = update_evidence_chain(tmp_path, rows, observed_at=first_observation)
    assert first["records"] == 3
    assert first["new_records"] == 3
    assert len(load_chain(tmp_path / "EVIDENCE_CHAIN.jsonl")) == 3

    timing = annotate_decision_timing(
        tmp_path, rows, maximum_delay_seconds=120
    )
    assert timing["valid_executed_candidates"] == 1
    assert rows[0]["prospective_decision_timing_valid"] is True
    assert rows[0]["prospective_veto_effective"] is True

    second = update_evidence_chain(
        tmp_path, rows, observed_at=first_observation
    )
    assert second["records"] == 3
    assert second["new_records"] == 0
    assert second["head_sha256"] == first["head_sha256"]

    resolved = update_evidence_chain(
        tmp_path,
        [resolved_row],
        observed_at=datetime(2026, 8, 26, 12, 1, tzinfo=UTC),
    )
    assert resolved["records"] == 4
    assert resolved["new_records"] == 1
    assert [
        row["event_type"] for row in load_chain(tmp_path / "EVIDENCE_CHAIN.jsonl")
    ] == [
        "SCORE_DECISION",
        "BASELINE_EXECUTION_DECISION",
        "BROKER_EXECUTION",
        "BROKER_OUTCOME",
    ]

    changed = [dict(resolved_row, causal_rank=0.06)]
    with pytest.raises(ValueError, match="Immutable prospective evidence changed"):
        update_evidence_chain(
            tmp_path,
            changed,
            observed_at=datetime(2026, 8, 26, 12, 2, tzinfo=UTC),
        )


def test_late_reconstructed_decision_is_fail_safe_retained(tmp_path) -> None:
    open_row = dict(
        candidate("1", -10.0, would_veto=True),
        broker_outcome_resolved=False,
        broker_exit_time_utc=None,
        broker_pnl_usd=None,
    )
    open_row.pop("broker_exit_fills")
    rows = [open_row]
    update_evidence_chain(
        tmp_path,
        rows,
        observed_at=datetime(2026, 8, 26, 1, 7, tzinfo=UTC),
    )
    audit = annotate_decision_timing(
        tmp_path, rows, maximum_delay_seconds=360
    )
    assert audit["valid_executed_candidates"] == 0
    assert rows[0]["prospective_decision_timing_valid"] is False
    assert rows[0]["prospective_veto_effective"] is False
    assert (
        rows[0]["prospective_decision_timing_reason"]
        == "RECORDED_AFTER_MAXIMUM_DELAY"
    )


def test_evidence_rejects_a_broker_outcome_observed_before_exit(tmp_path) -> None:
    rows = [candidate("1", -10.0, would_veto=True)]
    with pytest.raises(ValueError, match="observed before its exit time"):
        update_evidence_chain(
            tmp_path,
            rows,
            observed_at=datetime(2026, 8, 26, 1, 1, tzinfo=UTC),
        )


def test_forward_comparison_measures_whole_resolved_portfolio() -> None:
    rows = [
        candidate("1", -10.0, would_veto=True),
        candidate("2", 20.0, would_veto=False),
        candidate("3", -5.0, would_veto=False),
    ]
    status = {"counts": {}, "gates": {"existing": True}}
    acceptance = {
        "minimum_scored_executed_candidates": 3,
        "minimum_resolved_baseline_executions": 3,
        "minimum_resolved_vetoes": 1,
        "minimum_resolved_rank_coverage": 1.0,
        "minimum_resolved_prospective_timing_coverage": 1.0,
        "minimum_resolved_execution_detail_coverage": 1.0,
        "minimum_trade_retention": 0.60,
        "maximum_veto_broker_profit_factor_exclusive": 0.8,
        "minimum_avoided_broker_pnl_usd_exclusive": 0.0,
    }
    add_forward_comparison(status, rows, acceptance)

    comparison = status["forward_comparison"]
    assert comparison["baseline_v60"]["net_pnl_usd"] == 5.0
    assert comparison["challenger_v2"]["net_pnl_usd"] == 15.0
    assert comparison["delta_net_pnl_usd"] == 10.0
    assert comparison["baseline_v60"]["closed_drawdown_usd"] == 10.0
    assert comparison["challenger_v2"]["closed_drawdown_usd"] == 5.0
    assert comparison["trade_retention"] == pytest.approx(2 / 3)
    assert all(status["gates"].values())
    assert status["decision"] == "PROSPECTIVE_CONFIRMATION_PASSES_REVIEW_REQUIRED"


def test_execution_details_are_derived_from_broker_entry_deals() -> None:
    rows = [candidate("1", 2.0, would_veto=False)]
    rows[0].pop("broker_execution")
    state = {"positions": {"1": {"ticket": 101}}}
    deals = [
        {
            "position_id": 101,
            "entry": 0,
            "type": 0,
            "volume": 0.004,
            "price": 4700.0,
            "profit": 0.0,
            "commission": -0.2,
            "swap": 0.0,
            "fee": 0.0,
            "time_msc": 1787731201000,
        },
        {
            "position_id": 101,
            "entry": 0,
            "type": 0,
            "volume": 0.006,
            "price": 4710.0,
            "profit": 0.0,
            "commission": -0.3,
            "swap": 0.0,
            "fee": 0.0,
            "time_msc": 1787731202000,
        },
        {
            "ticket": 201,
            "position_id": 101,
            "entry": 1,
            "type": 1,
            "volume": 0.004,
            "price": 4712.0,
            "profit": 1.0,
            "commission": 0.0,
            "swap": 0.0,
            "fee": 0.0,
            "time_msc": 1787763600000,
        },
        {
            "ticket": 202,
            "position_id": 101,
            "entry": 1,
            "type": 1,
            "volume": 0.006,
            "price": 4713.0,
            "profit": 1.5,
            "commission": 0.0,
            "swap": 0.0,
            "fee": 0.0,
            "time_msc": 1787763601000,
        },
    ]
    attach_execution_details(
        rows, state, deals, account_currency_per_usd=1.0
    )
    execution = rows[0]["broker_execution"]
    assert execution["direction"] == "LONG"
    assert execution["volume_lots"] == pytest.approx(0.01)
    assert execution["entry_price"] == pytest.approx(4706.0)
    assert execution["entry_cost_usd"] == pytest.approx(-0.5)
    assert len(rows[0]["broker_exit_fills"]) == 2
    assert sum(fill["pnl_usd"] for fill in rows[0]["broker_exit_fills"]) == 2.5


def test_equity_marks_include_open_pnl_and_measure_sampled_drawdown(tmp_path) -> None:
    rows = [
        dict(
            candidate("1", 0.0, would_veto=True),
            broker_outcome_resolved=False,
            broker_exit_time_utc=None,
            broker_pnl_usd=None,
        ),
        dict(
            candidate("2", 0.0, would_veto=False),
            broker_outcome_resolved=False,
            broker_exit_time_utc=None,
            broker_pnl_usd=None,
        ),
    ]
    state = {"positions": {"1": {"ticket": 101}, "2": {"ticket": 102}}}
    deals = [
        {"position_id": 101, "profit": 0.0, "commission": -1.0, "swap": 0.0, "fee": 0.0},
        {"position_id": 102, "profit": 0.0, "commission": -1.0, "swap": 0.0, "fee": 0.0},
    ]
    positions = [
        {"ticket": 101, "profit": -9.0, "swap": 0.0},
        {"ticket": 102, "profit": 21.0, "swap": 0.0},
    ]
    first_time = datetime(2026, 8, 26, 12, tzinfo=UTC)
    first = build_equity_mark(
        rows,
        state,
        deals,
        positions,
        account_currency_per_usd=1.0,
        observed_at=first_time,
    )
    assert first["baseline_v60_equity_pnl_usd"] == 10.0
    assert first["challenger_v2_equity_pnl_usd"] == 20.0

    first_audit = update_equity_marks(
        tmp_path,
        first,
        boundary=datetime(2026, 8, 26, tzinfo=UTC),
        minimum_marks=2,
    )
    assert first_audit["marks"] == 1
    assert first_audit["minimum_marks_gate"] is False

    second = dict(
        first,
        observed_at_utc="2026-08-26T12:05:00Z",
        baseline_v60_equity_pnl_usd=-5.0,
        challenger_v2_equity_pnl_usd=15.0,
        delta_equity_pnl_usd=20.0,
    )
    second_audit = update_equity_marks(
        tmp_path,
        second,
        boundary=datetime(2026, 8, 26, tzinfo=UTC),
        minimum_marks=2,
    )
    assert second_audit["marks"] == 2
    assert second_audit["baseline_v60_sampled_equity_drawdown_usd"] == 15.0
    assert second_audit["challenger_v2_sampled_equity_drawdown_usd"] == 5.0
    assert second_audit["minimum_marks_gate"] is True
    assert second_audit["challenger_drawdown_not_worse_gate"] is True
