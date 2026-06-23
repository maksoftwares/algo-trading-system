from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c10_waits_for_data_when_c03_no_go(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_activation import run_demo_prediction_activation

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "NO_GO",
            "checks": [{"gate": "active_weeks", "passed": False, "observed": "1.53", "required": ">=8"}],
            "authorization": {"broker_action_authorized": False},
            "boundary": {"broker_action_authorized": False},
        },
    )
    _write_json(reports / "A3_ML_TRAINING_STATUS.json", _stage("REFUSED_NOT_READY"))
    _write_json(reports / "A3_ML_SHADOW_BRIDGE_STATUS.json", _stage("DISABLED_FAIL_CLOSED"))
    _write_json(reports / "A3_ML_EA_HANDOFF_STATUS.json", _stage("REFUSED_NOT_READY"))
    _write_json(reports / "A3_ML_OBSERVER_DEPLOY_STATUS.json", _stage("DEPLOYED_PASSIVE_OBSERVER", deployed_files=_observer_files(tmp_path)))

    output = run_demo_prediction_activation(root, run_pipeline=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_DATA"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert any(item["check"] == "c03_readiness_pass" and not item["passed"] for item in payload["validations"])


def test_c10_ready_to_publish_when_chain_ready_but_handoff_not_published(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_activation import run_demo_prediction_activation

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    _write_ready_reports(reports, tmp_path, c06_status="READY_DRY_RUN")

    output = run_demo_prediction_activation(root, run_pipeline=False, publish=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_TO_PUBLISH_HANDOFF"
    assert payload["authorization"]["python_demo_predictions_authorized"] is True
    assert payload["authorization"]["ea_consumption_authorized"] is False


def test_c10_ready_for_passive_consumption_when_handoff_files_exist(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_activation import run_demo_prediction_activation

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    _write_ready_reports(reports, tmp_path, c06_status="PUBLISHED_TO_MT5_FILES")

    output = run_demo_prediction_activation(root, run_pipeline=False, publish=True)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_FOR_PASSIVE_EA_CONSUMPTION"
    assert payload["authorization"]["python_demo_predictions_authorized"] is True
    assert payload["authorization"]["ea_consumption_authorized"] is True
    assert payload["boundary"]["broker_action_authorized"] is False


def test_c10_render_mentions_boundaries() -> None:
    from ml.a3_meta_v1.demo_activation import render_demo_prediction_activation_status_md

    report = render_demo_prediction_activation_status_md(
        {
            "status": "WAITING_FOR_DATA",
            "dataset_version": "TEST",
            "summary": {"stage_statuses": {"C03 readiness": "NO_GO"}},
            "actions": [],
            "validations": [{"check": "c03_readiness_pass", "passed": False, "detail": "active_weeks"}],
            "blockers": ["c03_readiness_pass: active_weeks"],
            "authorization": {
                "python_demo_predictions_authorized": False,
                "ea_consumption_authorized": False,
                "handoff_publish_requested": False,
            },
            "boundary": {
                "mt5_connection_attempted": False,
                "data_export_attempted": False,
                "ea_file_drop_authorized": False,
            },
            "next_allowed_stage": "Collect data.",
        }
    )

    assert "Overall status: WAITING_FOR_DATA" in report
    assert "MT5 connection attempted: false." in report
    assert "Broker action authorized: false." in report


def test_c10_script_loads() -> None:
    module = load_script("c10_demo_prediction_activation")

    assert hasattr(module, "main")


def _write_ready_reports(reports: Path, tmp_path: Path, *, c06_status: str) -> None:
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", _stage("PASS"))
    _write_json(reports / "A3_ML_TRAINING_STATUS.json", _stage("TRAINED_SHADOW_ONLY"))
    _write_json(
        reports / "A3_ML_SHADOW_BRIDGE_STATUS.json",
        _stage("READY_SHADOW_ONLY", authorization={"python_demo_predictions_authorized": True, "broker_action_authorized": False}),
    )
    _write_json(reports / "A3_ML_EA_HANDOFF_STATUS.json", _stage(c06_status, published_files=_handoff_files(tmp_path) if c06_status == "PUBLISHED_TO_MT5_FILES" else []))
    _write_json(reports / "A3_ML_OBSERVER_DEPLOY_STATUS.json", _stage("DEPLOYED_PASSIVE_OBSERVER", deployed_files=_observer_files(tmp_path)))
    _write_json(
        reports / "A3_ML_EA_CONSUMER_READINESS_STATUS.json",
        _stage(
            "BROKER_EXECUTOR_CONSUMERS_READY",
            authorization={
                "passive_observer_ml_consumer_ready": True,
                "broker_executor_ml_consumer_ready": True,
                "broker_action_authorized": False,
            },
        ),
    )
    _write_json(reports / "A3_ML_RUNTIME_EVIDENCE_STATUS.json", _stage("RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS"))
    _write_json(reports / "A3_ML_RUNTIME_LAUNCH_DIAGNOSTIC_STATUS.json", _stage("RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS"))


def _stage(
    status: str,
    *,
    authorization: dict | None = None,
    deployed_files: list[dict] | None = None,
    published_files: list[dict] | None = None,
) -> dict:
    auth = {"broker_action_authorized": False}
    if authorization:
        auth.update(authorization)
    return {
        "status": status,
        "authorization": auth,
        "boundary": {"broker_action_authorized": False},
        "outputs": {
            "deployed_files": deployed_files or [],
            "published_files": published_files or [],
        },
        "checks": [],
    }


def _observer_files(tmp_path: Path) -> list[dict]:
    rows = []
    for account in ("A1", "A2", "A3"):
        for artifact in ("observer_source", "handoff_include", "passive_preset", "compiled_ex5"):
            path = tmp_path / account / f"{artifact}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("ok\n", encoding="utf-8")
            rows.append({"account_label": account, "artifact": artifact, "target_path": str(path)})
    return rows


def _handoff_files(tmp_path: Path) -> list[dict]:
    rows = []
    for account in ("A1", "A2", "A3"):
        path = tmp_path / account / "A3_ML_EA_HANDOFF.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("schema_version\n", encoding="utf-8")
        rows.append({"account_label": account, "target_path": str(path)})
    return rows


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
