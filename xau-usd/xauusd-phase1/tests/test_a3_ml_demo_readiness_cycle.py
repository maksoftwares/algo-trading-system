from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c43_runs_safe_cycle_and_keeps_authorization_false(tmp_path: Path, monkeypatch) -> None:
    import ml.a3_meta_v1.demo_readiness_cycle as cycle

    root = _root_with_pointer(tmp_path, python_ready=False, ea_ready=False)
    calls: list[str] = []
    _patch_steps(monkeypatch, cycle, calls, c33_status="COLLECTING_LIVE_WAITING_FOR_DATA")

    output = cycle.run_demo_readiness_cycle(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_REVIEWER_DECISION_AND_DATA"
    assert payload["requested_actions"]["refresh_live_readonly"] is False
    assert payload["requested_actions"]["publish_research_preview"] is True
    assert calls[0] == "c23"
    assert calls[1:4] == ["c16", "c06", "c10"]
    assert "c26" in calls
    assert "c44" in calls
    assert "c45" in calls
    assert "c49" in calls
    assert "c46" in calls
    assert "c47" in calls
    assert "c48" in calls
    assert "c50" in calls
    assert "c51" in calls
    assert "c52" in calls
    assert "c53" in calls
    assert "c55" in calls
    assert "c42" in calls
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c43_demo_readiness_cycle_status"] == "WAITING_FOR_REVIEWER_DECISION_AND_DATA"
    assert pointer["broker_action_authorized"] is False


def test_c43_reports_collection_restore_when_c33_stale(tmp_path: Path, monkeypatch) -> None:
    import ml.a3_meta_v1.demo_readiness_cycle as cycle

    root = _root_with_pointer(tmp_path, python_ready=False, ea_ready=False)
    calls: list[str] = []
    _patch_steps(monkeypatch, cycle, calls, c33_status="STALE_OR_PARTIAL_COLLECTION")

    output = cycle.run_demo_readiness_cycle(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "RESTORE_COLLECTION_HEALTH"
    assert "Republish C26" in payload["next_allowed_stage"]


def test_c43_preserves_future_ready_python_authorization_but_never_broker_action(tmp_path: Path, monkeypatch) -> None:
    import ml.a3_meta_v1.demo_readiness_cycle as cycle

    root = _root_with_pointer(tmp_path, python_ready=True, ea_ready=True)
    calls: list[str] = []
    _patch_steps(monkeypatch, cycle, calls, c33_status="COLLECTING_LIVE_WAITING_FOR_DATA")

    output = cycle.run_demo_readiness_cycle(root, refresh_live_readonly=True, publish_research_preview=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    assert payload["requested_actions"]["refresh_live_readonly"] is True
    assert payload["requested_actions"]["publish_research_preview"] is False
    assert "c26" not in calls
    assert payload["authorization"]["python_demo_predictions_authorized"] is True
    assert payload["authorization"]["ea_consumption_authorized"] is True
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c43_script_loads() -> None:
    module = load_script("c43_run_demo_readiness_cycle")

    assert hasattr(module, "main")


def _root_with_pointer(tmp_path: Path, *, python_ready: bool, ea_ready: bool) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_A",
            "python_demo_predictions_authorized": python_ready,
            "ea_consumption_authorized": ea_ready,
            "broker_action_authorized": False,
        },
    )
    return root


def _patch_steps(monkeypatch, cycle, calls: list[str], *, c33_status: str) -> None:
    def writer(name: str, filename: str, status: str):
        def fake(root: Path, *args, **kwargs) -> Path:
            calls.append(name)
            path = root / "outputs" / "reports" / filename
            _write_json(path, {"status": status, "dataset_version": "DATASET_A"})
            return path

        return fake

    monkeypatch.setattr(cycle, "run_demo_python_launch_controller", writer("c23", "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json", "WAITING_FOR_DATA"))
    monkeypatch.setattr(cycle, "generate_readiness_gap_report", writer("c11", "A3_ML_READINESS_GAP_REPORT.json", "GAP_REMAINS"))
    monkeypatch.setattr(cycle, "generate_decision_backfill_audit", writer("c34", "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json", "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND"))
    monkeypatch.setattr(cycle, "generate_contract_expansion_packet", writer("c35", "A3_ML_CONTRACT_EXPANSION_PACKET_STATUS.json", "CONTRACT_EXPANSION_REVIEW_REQUIRED"))
    monkeypatch.setattr(cycle, "generate_contract_expansion_config_proposal", writer("c36", "A3_ML_CONTRACT_EXPANSION_CONFIG_PROPOSAL_STATUS.json", "WAITING_FOR_REVIEW_APPROVAL"))
    monkeypatch.setattr(cycle, "generate_contract_expansion_impact_estimate", writer("c37", "A3_ML_CONTRACT_EXPANSION_IMPACT_ESTIMATE_STATUS.json", "APPROVAL_ALONE_NOT_SUFFICIENT"))
    monkeypatch.setattr(cycle, "generate_label_trainability_blocker_audit", writer("c38", "A3_ML_LABEL_TRAINABILITY_BLOCKER_STATUS.json", "LABEL_PROMOTION_REVIEW_REQUIRED_SLIPPAGE_BLOCKED"))
    monkeypatch.setattr(cycle, "generate_historical_decision_coverage_report", writer("c39", "A3_ML_HISTORICAL_DECISION_COVERAGE_STATUS.json", "NO_OLDER_COMPATIBLE_DECISIONS_FOUND"))
    monkeypatch.setattr(cycle, "audit_ea_ml_consumers", writer("c16", "A3_ML_EA_CONSUMER_READINESS_STATUS.json", "BROKER_EXECUTOR_CONSUMERS_READY"))
    monkeypatch.setattr(cycle, "generate_ea_handoff_report", writer("c06", "A3_ML_EA_HANDOFF_STATUS.json", "REFUSED_NOT_READY"))
    monkeypatch.setattr(cycle, "run_demo_prediction_activation", writer("c10", "A3_ML_DEMO_PREDICTION_ACTIVATION_STATUS.json", "WAITING_FOR_DATA"))
    monkeypatch.setattr(cycle, "publish_research_preview_handoff_rehearsal", writer("c26", "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json", "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED"))
    monkeypatch.setattr(cycle, "verify_research_preview_runtime_read_path", writer("c27", "A3_ML_RESEARCH_PREVIEW_RUNTIME_VERIFIER_STATUS.json", "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS"))
    monkeypatch.setattr(cycle, "check_demo_shadow_collection_health", writer("c33", "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json", c33_status))
    monkeypatch.setattr(cycle, "repair_latest_dataset_if_needed", writer("c48", "A3_ML_LATEST_DATASET_REPAIR_STATUS.json", "DATASET_COMPLETE_NO_REPAIR_NEEDED"))
    monkeypatch.setattr(cycle, "generate_demo_readiness_work_order", writer("c40", "A3_ML_DEMO_READINESS_WORK_ORDER.json", "WAITING_FOR_DATA_AND_REVIEW"))
    monkeypatch.setattr(cycle, "generate_reviewer_decision_packet", writer("c41", "A3_ML_REVIEWER_DECISION_PACKET_STATUS.json", "REVIEWER_DECISION_REQUIRED"))
    monkeypatch.setattr(cycle, "generate_reviewer_decision_template", writer("c44", "A3_ML_REVIEWER_DECISION_TEMPLATE_STATUS.json", "TEMPLATE_READY_FOR_REVIEWER_EDIT"))
    monkeypatch.setattr(cycle, "generate_reviewer_submission_bundle", writer("c45", "A3_ML_REVIEWER_SUBMISSION_BUNDLE_STATUS.json", "READY_TO_SEND_TO_REVIEWER"))
    monkeypatch.setattr(cycle, "package_reviewer_handoff", writer("c49", "A3_ML_REVIEWER_HANDOFF_PACKAGE_STATUS.json", "READY_TO_SEND_REVIEWER_HANDOFF_PACKAGE"))
    monkeypatch.setattr(cycle, "generate_readiness_progress_tracker", writer("c46", "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json", "COLLECTING_LIVE_PROGRESS_TRACKED"))
    monkeypatch.setattr(cycle, "generate_gate_closure_plan", writer("c47", "A3_ML_GATE_CLOSURE_PLAN_STATUS.json", "WAITING_FOR_REVIEWER_AND_MARKET_DATA"))
    monkeypatch.setattr(cycle, "generate_historical_backfill_replay_plan", writer("c50", "A3_ML_HISTORICAL_BACKFILL_REPLAY_PLAN_STATUS.json", "HISTORICAL_BACKFILL_REPLAY_PLAN_READY"))
    monkeypatch.setattr(cycle, "generate_strategy_tester_replay_packet", writer("c51", "A3_ML_STRATEGY_TESTER_REPLAY_PACKET_STATUS.json", "STRATEGY_TESTER_REPLAY_PACKET_READY"))
    monkeypatch.setattr(cycle, "prepare_isolated_strategy_tester_workspace", writer("c52", "A3_ML_ISOLATED_STRATEGY_TESTER_WORKSPACE_STATUS.json", "ISOLATED_STRATEGY_TESTER_WORKSPACE_READY"))
    monkeypatch.setattr(cycle, "prepare_isolated_strategy_tester_terminal_root", writer("c53", "A3_ML_ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_STATUS.json", "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_READY"))
    monkeypatch.setattr(cycle, "generate_strategy_tester_account_context_decision", writer("c55", "A3_ML_STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_STATUS.json", "STRATEGY_TESTER_ACCOUNT_CONTEXT_PENDING_REPLAY_EVIDENCE"))
    monkeypatch.setattr(cycle, "process_reviewer_decision", writer("c42", "A3_ML_REVIEWER_DECISION_INTAKE_STATUS.json", "WAITING_FOR_REVIEWER_DECISION"))
    monkeypatch.setattr(cycle, "generate_demo_prediction_action_packet", writer("c24", "A3_ML_DEMO_PREDICTION_ACTION_PACKET.json", "WAITING_FOR_DATA"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
