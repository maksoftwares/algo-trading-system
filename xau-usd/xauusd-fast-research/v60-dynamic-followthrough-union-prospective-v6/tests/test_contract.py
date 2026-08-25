from __future__ import annotations

import hashlib
import json
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
    assert eligibility["additional_cost_0_10_all_comparative_gates_passed"]
    assert not eligibility["additional_cost_0_20_all_comparative_gates_passed"]
    assert config["authorization"]["demo_deployment"] is False


def test_contract_hash_is_reported_and_written_into_immutable_decisions() -> None:
    runner = (ROOT / "run_observer.py").read_text(encoding="utf-8")
    evidence = (ROOT / "src" / "evidence.py").read_text(encoding="utf-8")
    assert 'status["prospective_contract_sha256"]' in runner
    assert 'row["prospective_contract_sha256"]' in runner
    assert evidence.count('"prospective_contract_sha256"') >= 2
