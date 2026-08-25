from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_retrospective_fragility_is_supportive_but_never_authorizing() -> None:
    result = json.loads((ROOT / "GOAL_RESULT.json").read_text(encoding="utf-8"))
    challenger = result["best_historical_challenger"]
    fragility = challenger["retrospective_veto_fragility"]

    assert fragility["beneficial_vetoes"] == 12
    assert fragility["executed_vetoes"] == 13
    assert fragility["beneficial_months"] == fragility["active_months"] == 9
    assert fragility["avoided_pnl_after_removing_largest_benefit_usd"] > 0.0
    assert fragility["selection_adjusted"] is False
    assert fragility["deployment_evidence"] is False
    assert challenger["deployment_authorized"] is False
    assert result["decision"] == (
        "KEEP_V60_DEPLOYED_COLLECT_DYNAMIC_V6_FORWARD_EVIDENCE"
    )


def test_forward_union_requires_evidence_for_each_component() -> None:
    result = json.loads((ROOT / "GOAL_RESULT.json").read_text(encoding="utf-8"))
    forward = result["forward_observer"]

    assert forward["minimum_resolved_vetoes"] == 20
    assert forward["minimum_resolved_v2_vetoes"] == 10
    assert forward["minimum_resolved_anti_chase_vetoes"] == 10
    assert forward["minimum_resolved_baseline_executions"] >= 2000
    assert forward["requires_component_specific_positive_avoided_pnl"]
    assert forward["requires_component_specific_veto_profit_factor_below_0_8"]
    assert forward["component_evidence_requires_effective_immutable_timing"]
    horizon = forward["component_evidence_horizon"]
    assert horizon["anti_chase_expected_years_to_10_events_at_historical_rate"] > 50
    assert horizon["pooled_anti_chase_estimate_selection_contaminated"]
    assert horizon["planning_action"].startswith("KEEP_V6_FROZEN")
    assert forward["deployment_authorized"] is False


def test_august_improvement_cannot_sacrifice_established_edge() -> None:
    result = json.loads((ROOT / "GOAL_RESULT.json").read_text(encoding="utf-8"))
    research = result["higher_support_august_research"]

    assert research["hard_objective"] == (
        "IMPROVE_AUGUST_WITHOUT_HARMING_ESTABLISHED_EDGE"
    )
    assert research["best_retrospective_candidate_remains"] == (
        "v60-dynamic-followthrough-union-v6"
    )
    assert research["v9_rank_independent"]["decision"] == "REJECT"
    assert research["v9_rank_independent"]["antichase_avoided_pnl_usd"] < 0.0
    assert research["v10_dual_extension"]["decision"] == "REJECT"
    assert research["v10_dual_extension"]["nominal_2023_delta_pnl_usd"] < 0.0
    assert not research["v9_rank_independent"]["preserved_frozen_v6_edge"]
    assert not research["v10_dual_extension"]["preserved_frozen_v6_edge"]
    assert research["conclusion"] == (
        "KEEP_V6_FROZEN_AND_REQUIRE_CLEAN_FORWARD_CONFIRMATION"
    )
