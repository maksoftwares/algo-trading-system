from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c41_generates_reviewer_packet_without_authorizing_anything(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_decision_packet import generate_reviewer_decision_packet

    root = _root_with_reports(tmp_path)

    output = generate_reviewer_decision_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "REVIEWER_DECISION_REQUIRED"
    assert payload["dataset_version"] == "DATASET_A"
    assert payload["readiness_summary"]["c03_status"] == "NO_GO"
    assert payload["label_promotion_evidence"]["mature_labels"] == 452
    assert payload["label_promotion_evidence"]["candidate_trainable_groups"] == 0
    assert payload["contract_expansion_evidence"]["out_of_scope_would_signal_rows"] == 2747
    assert payload["historical_coverage"]["older_compatible_current_scope_would_signal_rows"] == 0
    assert "label-promotion policy" in payload["reviewer_prompt"]
    assert "contract-expansion policy" in payload["reviewer_prompt"]
    assert "Reviewer approval alone must not authorize training" in payload["approval_alone_not_sufficient_warning"]
    assert payload["authorization"]["training_authorized"] is False
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c41_reviewer_decision_packet_status"] == "REVIEWER_DECISION_REQUIRED"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c41_includes_current_config_decision_state(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_decision_packet import generate_reviewer_decision_packet

    root = _root_with_reports(tmp_path)

    output = generate_reviewer_decision_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    requests = {item["decision"]: item for item in payload["decision_requests"]}

    assert requests["label_promotion"]["current_authorized"] is False
    assert requests["contract_expansion"]["current_authorized"] is False
    assert requests["demo_prediction_conditions"]["must_not_authorize_python"] is True
    assert payload["label_promotion_evidence"]["require_slippage_adequate"] is True
    assert payload["contract_expansion_evidence"]["allowed_families_now"] == []


def test_c41_handles_ready_state_as_review_not_required_but_still_fail_closed(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_decision_packet import generate_reviewer_decision_packet

    root = _root_with_reports(tmp_path, ready=True)

    output = generate_reviewer_decision_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "REVIEW_NOT_REQUIRED"
    assert payload["authorization"]["reviewer_packet_authorizes_training"] is False
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c41_script_loads() -> None:
    module = load_script("c41_generate_reviewer_decision_packet")

    assert hasattr(module, "main")


def _root_with_reports(tmp_path: Path, *, ready: bool = False) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_A",
            "python_demo_predictions_authorized": ready,
            "ea_consumption_authorized": ready,
            "broker_action_authorized": False,
        },
    )
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "PASS" if ready else "NO_GO",
            "checks": [
                _check("market_setup_groups", ready, "223", ">=300"),
                _check("active_weeks", ready, "3.37", ">=8"),
                _check("at_least_two_regimes", ready, "FALLING", ">=2 non-UNKNOWN regimes"),
                _check("feature_budget", ready, "0", ">=6"),
                _check("slippage_readiness", ready, "INSUFFICIENT", "ADEQUATE"),
            ],
        },
    )
    _write_json(reports / "A3_ML_TRAINING_STATUS.json", {"status": "TRAINED_SHADOW_ONLY" if ready else "REFUSED_NOT_READY"})
    _write_json(
        reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json",
        {"status": "READY_FOR_DEMO_PYTHON_PREDICTIONS" if ready else "WAITING_FOR_DATA"},
    )
    _write_json(
        reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json",
        {"collection_health": {"all_accounts_collecting": True}},
    )
    _write_json(
        reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json",
        {
            "status": "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND",
            "summary": {
                "current_scope_would_signal_rows": 574,
                "uncataloged_current_scope_files": 0,
                "out_of_scope_would_signal_rows": 2747,
                "out_of_scope_estimated_groups": 1381,
            },
            "family_summary": [
                {"family": "round_number_retest", "would_signal_rows": 2747, "estimated_groups": 1381, "files": 13}
            ],
        },
    )
    _write_json(reports / "A3_ML_CONTRACT_EXPANSION_PACKET_STATUS.json", {"status": "CONTRACT_EXPANSION_REVIEW_REQUIRED"})
    _write_json(
        reports / "A3_ML_CONTRACT_EXPANSION_IMPACT_ESTIMATE_STATUS.json",
        {
            "status": "APPROVAL_ALONE_NOT_SUFFICIENT",
            "summary": {"candidate_files": 13},
            "approval_alone_result": "Approval alone is not enough for demo Python predictions.",
        },
    )
    _write_json(
        reports / "A3_ML_LABEL_TRAINABILITY_BLOCKER_STATUS.json",
        {
            "status": "LABEL_PROMOTION_REVIEW_REQUIRED_SLIPPAGE_BLOCKED",
            "summary": {
                "c02_mature_labels": 452,
                "c02_positive_labels": 180,
                "c02_negative_labels": 272,
                "c01_candidate_trainable_rows": 0,
                "c01_candidate_trainable_groups": 0,
                "c01_global_feature_budget": 0,
                "slippage_status": "INSUFFICIENT",
            },
            "slippage_deficits": [
                _slippage_account("A1", "ADEQUATE", 0, 0, 0, 0),
                _slippage_account("A2", "INSUFFICIENT", 188, 92, 46, 188),
                _slippage_account("A3", "INSUFFICIENT", 125, 46, 29, 176),
            ],
            "blockers": ["C02 labels are explicitly diagnostic-only."],
        },
    )
    _write_json(
        reports / "A3_ML_HISTORICAL_DECISION_COVERAGE_STATUS.json",
        {
            "status": "NO_OLDER_COMPATIBLE_DECISIONS_FOUND",
            "summary": {
                "older_compatible_current_scope_would_signal_rows": 0,
                "older_out_of_scope_rows": 0,
                "scanned_decision_like_files": 24,
            },
        },
    )
    _write_json(
        reports / "A3_ML_DEMO_READINESS_WORK_ORDER.json",
        {
            "status": "READY_FOR_DEMO_PYTHON_PREDICTIONS" if ready else "WAITING_FOR_DATA_AND_REVIEW",
            "summary": {"estimated_active_weeks_pass_date_utc": "2026-07-24T10:10:22Z"},
        },
    )
    _write_json(
        config / "a3_ml_label_promotion.json",
        {
            "label_promotion_authorized": False,
            "review_reference": "",
            "allowed_label_statuses": ["TP", "SL", "TIMEOUT_POSITIVE", "TIMEOUT_NEGATIVE", "TIMEOUT_FLAT"],
            "minimum_mature_labels": 300,
            "minimum_minority_labels": 90,
            "require_slippage_adequate": True,
        },
    )
    _write_json(
        config / "a3_ml_contract_expansion.json",
        {
            "contract_expansion_authorized": False,
            "review_reference": "",
            "allowed_families": [],
            "accounts": {},
        },
    )
    return root


def _check(gate: str, passed: bool, observed: str, required: str) -> dict:
    return {"gate": gate, "passed": passed, "observed": observed, "required": required}


def _slippage_account(label: str, status: str, entry: int, sl: int, tp: int, request: int) -> dict:
    return {
        "account_label": label,
        "slippage_status": status,
        "entry_fills_deficit": entry,
        "sl_exits_deficit": sl,
        "tp_exits_deficit": tp,
        "request_price_resolved_deficit": request,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
