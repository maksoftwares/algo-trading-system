from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_contract_is_disarmed_and_boundary_is_frozen() -> None:
    config = json.loads((ROOT / "config" / "prospective.json").read_text())
    assert config["authorization"]["read_only_mt5"]
    assert not any(
        config["authorization"][name]
        for name in ("broker_actions", "runtime_changes", "demo_deployment", "live_deployment")
    )
    assert config["lock"]["evidence_start_inclusive_utc"] == "2026-08-26T00:00:00Z"


def test_runtime_sources_match_locked_hashes() -> None:
    config = json.loads((ROOT / "config" / "prospective.json").read_text())
    locks = config["lock"]
    paths = {
        "policy_source_sha256": ROOT / "src" / "policy.py",
        "observer_runner_sha256": ROOT / "run_observer.py",
        "evidence_recorder_sha256": ROOT / "src" / "evidence.py",
        "tick_replay_sha256": ROOT / "src" / "tick_replay.py",
        "tick_replay_runner_sha256": ROOT / "run_exact_tick_equity_replay.py",
        "research_config_sha256": REPO_ROOT / locks["research_config"],
        "shared_observer_sha256": REPO_ROOT / locks["shared_observer"],
    }
    for key, path in paths.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == locks[key]


def test_acceptance_requires_full_coverage_and_retention() -> None:
    config = json.loads((ROOT / "config" / "prospective.json").read_text())
    acceptance = config["acceptance"]
    assert acceptance["minimum_trade_retention"] == 0.99
    assert acceptance["minimum_resolved_rank_coverage"] == 1.0
    assert acceptance["minimum_resolved_causal_feature_coverage"] == 1.0
    assert acceptance["minimum_resolved_prospective_timing_coverage"] == 1.0
    assert acceptance["minimum_resolved_execution_detail_coverage"] == 1.0


def test_authorization_sample_is_consistent_with_veto_and_retention_gates() -> None:
    config = json.loads((ROOT / "config" / "prospective.json").read_text())
    checkpoint = config["monitoring_checkpoint"]
    acceptance = config["acceptance"]
    implied_minimum = math.ceil(
        acceptance["minimum_resolved_vetoes"]
        / (1.0 - acceptance["minimum_trade_retention"])
    )

    assert checkpoint["review_scope"] == "DIAGNOSTIC_ONLY"
    assert checkpoint["deployment_authorization"] is False
    assert acceptance["minimum_resolved_baseline_executions"] >= implied_minimum
    assert acceptance["minimum_scored_executed_candidates"] >= implied_minimum
    assert acceptance["minimum_resolved_v2_vetoes"] >= 10
    assert acceptance["minimum_resolved_anti_chase_vetoes"] >= 10
    assert acceptance["minimum_resolved_vetoes"] >= (
        acceptance["minimum_resolved_v2_vetoes"]
        + acceptance["minimum_resolved_anti_chase_vetoes"]
    )


def test_august_improvement_cannot_override_preservation_or_forward_proof() -> None:
    config = json.loads((ROOT / "config" / "prospective.json").read_text())
    eligibility = config["pre_forward_eligibility"]
    assert eligibility["august_2026_net_pnl_above_v60"]
    assert eligibility["august_2026_profit_factor_above_v60"]
    assert eligibility["august_2026_closed_drawdown_not_worse"]
    assert eligibility["nominal_long_run_edge_preserved"]
    assert eligibility["every_calendar_year_preserved"]
    assert eligibility["recent_3m_6m_12m_windows_preserved"]
    assert eligibility["minimum_99_percent_trade_retention_passed"]
    assert eligibility[
        "full_dynamic_additional_cost_0_10_all_comparative_gates_passed"
    ]
    assert not eligibility[
        "full_dynamic_additional_cost_0_20_all_comparative_gates_passed"
    ]
    assert not eligibility[
        "veto_only_common_path_additional_cost_0_10_all_comparative_gates_passed"
    ]
    assert not eligibility[
        "veto_only_common_path_additional_cost_0_20_all_comparative_gates_passed"
    ]
    assert not eligibility["forward_observer_validates_replacement_capacity_trades"]
    assert config["authorization"]["demo_deployment"] is False


def test_contract_hash_is_reported_and_written_into_immutable_decisions() -> None:
    runner = (ROOT / "run_observer.py").read_text(encoding="utf-8")
    evidence = (ROOT / "src" / "evidence.py").read_text(encoding="utf-8")
    assert 'status["prospective_contract_sha256"]' in runner
    assert 'row["prospective_contract_sha256"]' in runner
    assert evidence.count('"prospective_contract_sha256"') >= 2
