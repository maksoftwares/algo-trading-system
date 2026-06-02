from __future__ import annotations

from phase0r.candidate_registry import CANDIDATES, Candidate
from phase0r.cost_feasibility import (
    DEFAULT_SPREAD_ASSUMPTIONS,
    evaluate_candidate_cost,
    projected_cost_r,
    run_cost_feasibility,
)


def test_default_measured_p95_spread_is_75_points():
    assert DEFAULT_SPREAD_ASSUMPTIONS.measured_p95_spread_points == 75.0


def test_tight_stop_candidate_is_structural_cost_risk():
    candidate = Candidate(
        candidate_id="tight_stop_research_only_v0",
        version="v0",
        status="DRAFT",
        mechanic_family="research-only tight stop control",
        decision_timeframe="M5",
        entry_timeframe="M5",
        expected_median_hold_hours="1-4",
        expected_decisions_per_week="many",
        expected_trades_per_year="many",
        expected_median_stop_points=200.0,
        same_family_as_breakout_retest=True,
        timeframe_diversification_qualifies=False,
        hypothesis_filename="hypothesis_tight_stop_research_only_v0.md",
    )

    result = evaluate_candidate_cost(candidate)

    assert result.status == "STRUCTURAL_COST_RISK"
    assert result.projected_cost_r_p95 == 0.375
    assert not result.cost_feasible


def test_registered_candidates_have_structural_cost_precheck_results():
    results = run_cost_feasibility("all")

    assert {result.candidate_id for result in results} == {candidate.candidate_id for candidate in CANDIDATES}
    assert all(result.status in {"PASS_PREFERRED", "PASS_ACCEPTABLE"} for result in results)
    assert projected_cost_r(75, 375) == 0.2
