from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c44_generates_template_with_safe_incomplete_review_reference(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_decision_template import generate_reviewer_decision_template

    root = _root_with_c41(tmp_path)

    output = generate_reviewer_decision_template(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    template_path = Path(payload["outputs"]["reviewer_decision_template_json"])
    template = json.loads(template_path.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "TEMPLATE_READY_FOR_REVIEWER_EDIT"
    assert payload["template_valid_without_reviewer_edit"] is False
    assert template["schema_version"] == "a3_ml_reviewer_decision_v1"
    assert template["review_reference"] == ""
    assert template["label_promotion"]["approved"] is False
    assert template["contract_expansion"]["approved"] is False
    assert template["demo_prediction_conditions"]["requires_c03_c05_c04_c06_c10_c23_pass"] is True
    assert template["demo_prediction_conditions"]["broker_action_authorized"] is False
    assert "round_number_retest" in template["contract_expansion"]["candidate_families_to_consider"]
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert pointer["c44_reviewer_decision_template_status"] == "TEMPLATE_READY_FOR_REVIEWER_EDIT"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c44_template_becomes_valid_for_c42_after_reviewer_reference_is_filled(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_decision_intake import process_reviewer_decision
    from ml.a3_meta_v1.reviewer_decision_template import generate_reviewer_decision_template

    root = _root_with_c41(tmp_path)

    output = generate_reviewer_decision_template(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    template_path = Path(payload["outputs"]["reviewer_decision_template_json"])

    invalid_output = process_reviewer_decision(root, decision_json=template_path)
    invalid = json.loads(invalid_output.read_text(encoding="utf-8"))
    assert invalid["status"] == "INVALID_REVIEWER_DECISION"
    assert "review_reference is required" in invalid["validation_errors"]

    template = json.loads(template_path.read_text(encoding="utf-8"))
    template["review_reference"] = "Reviewer rejects approval but confirms gates for C44 test"
    template_path.write_text(json.dumps(template, indent=2), encoding="utf-8")

    valid_output = process_reviewer_decision(root, decision_json=template_path)
    valid = json.loads(valid_output.read_text(encoding="utf-8"))
    assert valid["status"] == "VALID_REVIEW_READY_TO_APPLY"
    assert valid["authorization"]["python_demo_predictions_authorized"] is False


def test_c44_script_loads() -> None:
    module = load_script("c44_generate_reviewer_decision_template")

    assert hasattr(module, "main")


def _root_with_c41(tmp_path: Path) -> Path:
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
        reports / "A3_ML_REVIEWER_DECISION_PACKET_STATUS.json",
        {
            "status": "REVIEWER_DECISION_REQUIRED",
            "dataset_version": "DATASET_A",
            "outputs": {"status_report_json": str(reports / "A3_ML_REVIEWER_DECISION_PACKET_STATUS.json")},
            "readiness_summary": {
                "c03_status": "NO_GO",
                "c05_status": "REFUSED_NOT_READY",
                "c23_status": "WAITING_FOR_DATA",
                "c40_status": "WAITING_FOR_DATA_AND_REVIEW",
                "active_weeks_observed": "3.37",
                "market_setup_groups_observed": "223",
            },
            "label_promotion_evidence": {
                "allowed_label_statuses": ["TP", "SL"],
                "minimum_mature_labels": 300,
                "minimum_minority_labels": 90,
                "require_slippage_adequate": True,
                "mature_labels": 457,
                "positive_labels": 185,
                "negative_labels": 272,
                "slippage_status": "INSUFFICIENT",
            },
            "contract_expansion_evidence": {
                "out_of_scope_would_signal_rows": 2455,
                "out_of_scope_estimated_groups": 1127,
                "approval_alone_result": "Approval alone is not enough.",
                "candidate_families": [
                    {"family": "round_number_retest", "would_signal_rows": 2455, "estimated_groups": 1127, "files": 7}
                ],
            },
        },
    )
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
