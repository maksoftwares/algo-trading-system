from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c48_noops_when_latest_dataset_is_complete(tmp_path: Path, monkeypatch) -> None:
    import ml.a3_meta_v1.latest_dataset_repair as repair

    root = _root(tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(repair, "generate_readiness_progress_tracker", _tracker_writer(calls, ["COLLECTING_LIVE_PROGRESS_TRACKED"]))
    monkeypatch.setattr(repair, "run_offline_prediction_readiness_pipeline", _pipeline_writer(calls, "NOT_READY"))

    output = repair.repair_latest_dataset_if_needed(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "DATASET_COMPLETE_NO_REPAIR_NEEDED"
    assert payload["repair_attempted"] is False
    assert calls == ["c46"]
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c48_reports_required_when_repair_disabled(tmp_path: Path, monkeypatch) -> None:
    import ml.a3_meta_v1.latest_dataset_repair as repair

    root = _root(tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(repair, "generate_readiness_progress_tracker", _tracker_writer(calls, ["DATASET_ARTIFACTS_INCOMPLETE"]))
    monkeypatch.setattr(repair, "run_offline_prediction_readiness_pipeline", _pipeline_writer(calls, "NOT_READY"))

    output = repair.repair_latest_dataset_if_needed(root, auto_repair=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "REPAIR_REQUIRED_NOT_RUN"
    assert payload["repair_attempted"] is False
    assert calls == ["c46"]


def test_c48_repairs_incomplete_dataset_with_offline_pipeline(tmp_path: Path, monkeypatch) -> None:
    import ml.a3_meta_v1.latest_dataset_repair as repair

    root = _root(tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(
        repair,
        "generate_readiness_progress_tracker",
        _tracker_writer(calls, ["DATASET_ARTIFACTS_INCOMPLETE", "COLLECTING_LIVE_PROGRESS_TRACKED"]),
    )
    monkeypatch.setattr(repair, "run_offline_prediction_readiness_pipeline", _pipeline_writer(calls, "NOT_READY"))

    output = repair.repair_latest_dataset_if_needed(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "REPAIRED_BY_OFFLINE_PIPELINE"
    assert payload["repair_attempted"] is True
    assert calls == ["c46", "c07", "c46"]
    assert payload["before"]["complete"] is False
    assert payload["after"]["complete"] is True
    assert payload["pipeline"]["publish_requested"] is False
    assert pointer["c48_latest_dataset_repair_status"] == "REPAIRED_BY_OFFLINE_PIPELINE"
    assert pointer["broker_action_authorized"] is False


def test_c48_script_loads() -> None:
    module = load_script("c48_repair_latest_dataset_if_needed")

    assert hasattr(module, "main")


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_A",
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    return root


def _tracker_writer(calls: list[str], statuses: list[str]):
    def fake(root: Path, *args, **kwargs) -> Path:
        calls.append("c46")
        status = statuses[min(calls.count("c46") - 1, len(statuses) - 1)]
        complete = status != "DATASET_ARTIFACTS_INCOMPLETE"
        path = root / "outputs" / "reports" / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json"
        _write_json(
            path,
            {
                "status": status,
                "dataset_version": "DATASET_A",
                "latest_dataset_completeness": {
                    "complete": complete,
                    "missing_artifacts": [] if complete else ["diagnostic_labels"],
                },
                "completeness_warnings": [] if complete else ["Latest dataset is missing required artifacts: diagnostic_labels"],
                "outputs": {
                    "status_report_json": str(path),
                    "status_report_md": str(path.with_suffix(".md")),
                },
            },
        )
        return path

    return fake


def _pipeline_writer(calls: list[str], status: str):
    def fake(root: Path, *args, **kwargs) -> Path:
        calls.append("c07")
        path = root / "outputs" / "reports" / "A3_ML_PIPELINE_RUN_STATUS.json"
        _write_json(path, {"status": status, "publish_requested": False})
        return path

    return fake


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
