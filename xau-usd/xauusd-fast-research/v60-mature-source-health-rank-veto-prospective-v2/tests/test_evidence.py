from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.evidence import (
    add_forward_comparison,
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
        "broker_outcome_resolved": True,
        "broker_exit_time_utc": f"2026-08-26T1{candidate_id}:00:00Z",
        "broker_pnl_usd": pnl,
    }


def test_evidence_chain_is_idempotent_and_rejects_decision_drift(tmp_path) -> None:
    rows = [candidate("1", -10.0, would_veto=True)]
    now = datetime(2026, 8, 26, 12, tzinfo=UTC)
    first = update_evidence_chain(tmp_path, rows, observed_at=now)
    assert first["records"] == 3
    assert first["new_records"] == 3
    assert len(load_chain(tmp_path / "EVIDENCE_CHAIN.jsonl")) == 3

    second = update_evidence_chain(tmp_path, rows, observed_at=now)
    assert second["records"] == 3
    assert second["new_records"] == 0
    assert second["head_sha256"] == first["head_sha256"]

    changed = [dict(rows[0], causal_rank=0.06)]
    with pytest.raises(ValueError, match="Immutable prospective evidence changed"):
        update_evidence_chain(tmp_path, changed, observed_at=now)


def test_forward_comparison_measures_whole_resolved_portfolio() -> None:
    rows = [
        candidate("1", -10.0, would_veto=True),
        candidate("2", 20.0, would_veto=False),
        candidate("3", -5.0, would_veto=False),
    ]
    status = {"counts": {}, "gates": {"existing": True}}
    acceptance = {
        "minimum_resolved_baseline_executions": 3,
        "minimum_resolved_rank_coverage": 1.0,
        "minimum_trade_retention": 0.60,
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
