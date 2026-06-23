from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c42_waits_without_reviewer_decision_and_keeps_authorization_false(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_decision_intake import process_reviewer_decision

    root = _root_with_reports(tmp_path)

    output = process_reviewer_decision(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_REVIEWER_DECISION"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c42_reviewer_decision_intake_status"] == "WAITING_FOR_REVIEWER_DECISION"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c42_rejects_invalid_decision_without_writing_configs(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_decision_intake import process_reviewer_decision

    root = _root_with_reports(tmp_path)
    decision = root / "reviewer_decision.json"
    _write_json(
        decision,
        {
            "schema_version": "a3_ml_reviewer_decision_v1",
            "review_reference": "Reviewer test",
            "label_promotion": {"approved": True, "allowed_label_statuses": ["TP"]},
            "contract_expansion": {"approved": True, "allowed_families": ["round_number_retest"]},
            "demo_prediction_conditions": {
                "requires_c03_c05_c04_c06_c10_c23_pass": True,
                "broker_action_authorized": True,
            },
        },
    )

    output = process_reviewer_decision(root, decision_json=decision, apply_configs=True)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "INVALID_REVIEWER_DECISION"
    assert "broker_action_authorized must be false" in "\n".join(payload["validation_errors"])
    assert payload["config_write_result"]["label_config_written"] is False
    assert not (root / "config" / "ml" / "a3_ml_label_promotion.json").exists()


def test_c42_valid_decision_ready_to_apply_does_not_write_without_apply_flag(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_decision_intake import process_reviewer_decision

    root = _root_with_reports(tmp_path)
    decision = _write_valid_decision(root)

    output = process_reviewer_decision(root, decision_json=decision)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "VALID_REVIEW_READY_TO_APPLY"
    assert payload["decision_summary"]["allowed_label_statuses"] == ["TP", "SL"]
    assert payload["decision_summary"]["allowed_families"] == ["round_number_retest"]
    assert payload["config_write_result"]["label_config_written"] is False
    assert not (root / "config" / "ml" / "a3_ml_label_promotion.json").exists()


def test_c42_applies_valid_decision_configs_but_not_demo_authorization(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_scope import load_contract_scope
    from ml.a3_meta_v1.label_promotion_scope import load_label_promotion_scope
    from ml.a3_meta_v1.reviewer_decision_intake import process_reviewer_decision

    root = _root_with_reports(tmp_path)
    decision = _write_valid_decision(root)

    output = process_reviewer_decision(root, decision_json=decision, apply_configs=True)
    payload = json.loads(output.read_text(encoding="utf-8"))
    label_scope = load_label_promotion_scope(root)
    contract_scope = load_contract_scope(root)

    assert payload["status"] == "APPLIED_REVIEWER_CONFIGS_FAIL_CLOSED"
    assert payload["config_write_result"]["label_config_written"] is True
    assert payload["config_write_result"]["contract_config_written"] is True
    assert label_scope.label_promotion_authorized is True
    assert label_scope.allowed_label_statuses == ("TP", "SL")
    assert contract_scope.active_families == ("breakout_retest", "round_number_retest")
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c42_script_loads() -> None:
    module = load_script("c42_process_reviewer_decision")

    assert hasattr(module, "main")


def _root_with_reports(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_A",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    _write_json(
        reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json",
        {
            "status": "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND",
            "dataset_version": "DATASET_A",
            "out_of_scope_candidates": [
                {
                    "account_label": "A1",
                    "account_scope": "1025742",
                    "filename": "experimental_demo_executor_signal_log_round_number_retest_v0_xauusd.csv",
                    "family": "round_number_retest",
                    "would_signal_rows": 100,
                    "min_signal_utc": "2026-06-01T00:00:00Z",
                    "max_signal_utc": "2026-06-02T00:00:00Z",
                }
            ],
        },
    )
    _write_json(
        reports / "A3_ML_CONTRACT_EXPANSION_PACKET_STATUS.json",
        {"status": "CONTRACT_EXPANSION_REVIEW_REQUIRED", "dataset_version": "DATASET_A"},
    )
    return root


def _write_valid_decision(root: Path) -> Path:
    decision = root / "reviewer_decision.json"
    _write_json(
        decision,
        {
            "schema_version": "a3_ml_reviewer_decision_v1",
            "review_reference": "Reviewer approved C42 test only",
            "label_promotion": {
                "approved": True,
                "allowed_label_statuses": ["TP", "SL"],
                "minimum_mature_labels": 300,
                "minimum_minority_labels": 90,
                "require_slippage_adequate": True,
            },
            "contract_expansion": {"approved": True, "allowed_families": ["round_number_retest"]},
            "demo_prediction_conditions": {
                "requires_c03_c05_c04_c06_c10_c23_pass": True,
                "broker_action_authorized": False,
            },
        },
    )
    return decision


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
