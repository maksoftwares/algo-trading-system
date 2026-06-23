from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c45_generates_sendable_bundle_without_authorization(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_submission_bundle import generate_reviewer_submission_bundle

    root = _root_with_review_artifacts(tmp_path)

    output = generate_reviewer_submission_bundle(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "READY_TO_SEND_TO_REVIEWER"
    assert all(item["exists"] for item in payload["artifact_manifest"])
    assert "Please review the attached A3 ML decision packet" in payload["reviewer_submission_text"]
    assert "round_number_retest" in payload["reviewer_submission_text"]
    assert "C48 latest dataset repair" in payload["reviewer_submission_text"]
    assert payload["supporting_statuses"]["c46_status"] == "COLLECTING_LIVE_PROGRESS_TRACKED"
    assert payload["supporting_statuses"]["c48_status"] == "DATASET_COMPLETE_NO_REPAIR_NEEDED"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c45_reviewer_submission_bundle_status"] == "READY_TO_SEND_TO_REVIEWER"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c45_reports_missing_artifacts_fail_closed(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_submission_bundle import generate_reviewer_submission_bundle

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "DATASET_A"})

    output = generate_reviewer_submission_bundle(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "MISSING_REVIEWER_ARTIFACTS"
    assert payload["authorization"]["broker_action_authorized"] is False
    assert any(not item["exists"] for item in payload["artifact_manifest"])


def test_c45_script_loads() -> None:
    module = load_script("c45_generate_reviewer_submission_bundle")

    assert hasattr(module, "main")


def _root_with_review_artifacts(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "DATASET_A"})
    c41 = {
        "status": "REVIEWER_DECISION_REQUIRED",
        "dataset_version": "DATASET_A",
        "readiness_summary": {
            "c03_status": "NO_GO",
            "c05_status": "REFUSED_NOT_READY",
            "c23_status": "WAITING_FOR_DATA",
            "c40_status": "WAITING_FOR_DATA_AND_REVIEW",
            "active_weeks_observed": "3.37",
            "market_setup_groups_observed": "223",
            "feature_budget_observed": "0",
            "slippage_readiness_observed": "INSUFFICIENT",
        },
        "label_promotion_evidence": {"mature_labels": 457},
        "contract_expansion_evidence": {
            "out_of_scope_would_signal_rows": 2455,
            "out_of_scope_estimated_groups": 1127,
            "candidate_families": [
                {"family": "round_number_retest", "would_signal_rows": 2455, "estimated_groups": 1127, "files": 7}
            ],
        },
    }
    _write_json(reports / "A3_ML_REVIEWER_DECISION_PACKET_STATUS.json", c41)
    (reports / "A3_ML_REVIEWER_DECISION_PACKET_STATUS.md").write_text("# C41\n", encoding="utf-8")
    _write_json(reports / "A3_ML_REVIEWER_DECISION_TEMPLATE_STATUS.json", {"status": "TEMPLATE_READY_FOR_REVIEWER_EDIT"})
    (reports / "A3_ML_REVIEWER_DECISION_TEMPLATE_STATUS.md").write_text("# C44\n", encoding="utf-8")
    _write_json(
        reports / "A3_ML_REVIEWER_DECISION_TEMPLATE.json",
        {
            "schema_version": "a3_ml_reviewer_decision_v1",
            "review_reference": "",
            "label_promotion": {"approved": False},
            "contract_expansion": {"approved": False},
            "demo_prediction_conditions": {
                "requires_c03_c05_c04_c06_c10_c23_pass": True,
                "broker_action_authorized": False,
            },
        },
    )
    _write_json(
        reports / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json",
        {
            "status": "COLLECTING_LIVE_PROGRESS_TRACKED",
            "completeness_warnings": [],
            "regression_warnings": [],
        },
    )
    (reports / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.md").write_text("# C46\n", encoding="utf-8")
    _write_json(reports / "A3_ML_GATE_CLOSURE_PLAN_STATUS.json", {"status": "WAITING_FOR_REVIEWER_AND_MARKET_DATA"})
    (reports / "A3_ML_GATE_CLOSURE_PLAN_STATUS.md").write_text("# C47\n", encoding="utf-8")
    _write_json(reports / "A3_ML_LATEST_DATASET_REPAIR_STATUS.json", {"status": "DATASET_COMPLETE_NO_REPAIR_NEEDED", "repair_attempted": False})
    (reports / "A3_ML_LATEST_DATASET_REPAIR_STATUS.md").write_text("# C48\n", encoding="utf-8")
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
