from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c49_packages_reviewer_handoff_zip_without_authorization(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_handoff_package import package_reviewer_handoff

    root = _root_with_c45(tmp_path, include_artifacts=True)

    output = package_reviewer_handoff(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "READY_TO_SEND_REVIEWER_HANDOFF_PACKAGE"
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["package"]["zip_exists"] is True
    assert Path(payload["package"]["zip"]).exists()
    assert pointer["c49_reviewer_handoff_package_status"] == "READY_TO_SEND_REVIEWER_HANDOFF_PACKAGE"
    assert pointer["broker_action_authorized"] is False
    with zipfile.ZipFile(payload["package"]["zip"]) as archive:
        names = set(archive.namelist())
    assert "README_REVIEWER_HANDOFF.md" in names
    assert "A3_ML_REVIEWER_SUBMISSION_BUNDLE_STATUS.json" in names
    assert "A3_ML_REVIEWER_DECISION_TEMPLATE.json" in names


def test_c49_reports_missing_inputs_fail_closed(tmp_path: Path) -> None:
    from ml.a3_meta_v1.reviewer_handoff_package import package_reviewer_handoff

    root = _root_with_c45(tmp_path, include_artifacts=False)

    output = package_reviewer_handoff(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "MISSING_REVIEWER_HANDOFF_INPUTS"
    assert payload["package"]["zip"] == ""
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["missing_inputs"]


def test_c49_script_loads() -> None:
    module = load_script("c49_package_reviewer_handoff")

    assert hasattr(module, "main")


def _root_with_c45(tmp_path: Path, *, include_artifacts: bool) -> Path:
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
    artifact_path = reports / "A3_ML_REVIEWER_DECISION_TEMPLATE.json"
    if include_artifacts:
        _write_json(artifact_path, {"schema_version": "a3_ml_reviewer_decision_v1"})
    _write_json(
        reports / "A3_ML_REVIEWER_SUBMISSION_BUNDLE_STATUS.json",
        {
            "status": "READY_TO_SEND_TO_REVIEWER",
            "dataset_version": "DATASET_A",
            "artifact_manifest": [
                {
                    "name": "C44 reviewer decision template JSON",
                    "path": str(artifact_path),
                    "exists": include_artifacts,
                }
            ],
            "reviewer_submission_text": "Please review this packet.",
            "commands_after_reviewer_returns": {
                "validate_reviewer_template": "python scripts/c42_process_reviewer_decision.py --root . --decision-json outputs/reports/A3_ML_REVIEWER_DECISION_TEMPLATE.json"
            },
            "authorization": {
                "python_demo_predictions_authorized": False,
                "ea_consumption_authorized": False,
                "broker_action_authorized": False,
            },
        },
    )
    (reports / "A3_ML_REVIEWER_SUBMISSION_BUNDLE_STATUS.md").write_text("# C45\n", encoding="utf-8")
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
