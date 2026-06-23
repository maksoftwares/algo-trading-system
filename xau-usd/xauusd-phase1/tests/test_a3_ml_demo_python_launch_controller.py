from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c23_reports_waiting_for_attach_and_data(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_python_launch_controller import run_demo_python_launch_controller

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    _write_common_root(root, tmp_path, runtime_logs=False)
    _write_no_go_reports(reports)

    output = run_demo_python_launch_controller(root, post_attach_timeout_seconds=0)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_MANUAL_ATTACH_AND_DATA"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["readiness"]["data_ready"] is False
    assert payload["readiness"]["post_attach_monitor_ready"] is False


def test_c23_reports_ready_for_demo_python_predictions(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_python_launch_controller import run_demo_python_launch_controller

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    _write_common_root(root, tmp_path, runtime_logs=True)
    _write_ready_reports(reports, tmp_path)

    output = run_demo_python_launch_controller(root, post_attach_timeout_seconds=0)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((reports / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    assert payload["authorization"]["python_demo_predictions_authorized"] is True
    assert payload["authorization"]["ea_consumption_authorized"] is True
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c23_demo_python_launch_controller_status"] == "READY_FOR_DEMO_PYTHON_PREDICTIONS"


def test_c23_script_loads() -> None:
    module = load_script("c23_run_demo_python_launch_controller")

    assert hasattr(module, "main")


def _write_common_root(root: Path, tmp_path: Path, *, runtime_logs: bool) -> None:
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST", "requested_start_utc": "2026-06-01T00:00:00Z"})
    _write_json(
        config / "a3_ml_training_contract.json",
        {
            "schema_version": "a3_ml_training_contract_v1",
            "readiness_report_json": "outputs/reports/C03_TRAINING_READINESS_REPORT.json",
            "data_audit_json": "outputs/reports/C02_C01_DATA_AUDIT.json",
            "snapshot_csv": "outputs/reports/A3_ML_C01_SNAPSHOT_ROWS.csv",
        },
    )
    _write_snapshot(
        reports / "A3_ML_C01_SNAPSHOT_ROWS.csv",
        [
            _snapshot_row("1025742", "A1", "LONG", "1"),
            _snapshot_row("1025742", "A1", "SHORT", "0"),
            _snapshot_row("1033030", "A2", "LONG", "1"),
            _snapshot_row("1033669", "A3", "SHORT", "0"),
        ],
    )
    _write_json(
        reports / "C02_C01_DATA_AUDIT.json",
        {
            "status": "PIPELINE_ONLY",
            "selected_features": [],
            "feature_availability": [],
            "training_decision": {"supervised_training_allowed": False, "reason": "feature_budget=0"},
            "raw_source_row_counts": {"snapshot_rows": 4},
        },
    )
    _write_json(reports / "A3_ML_OBSERVER_RUNTIME_ATTACH_STATUS.json", {"status": "LAUNCH_SENT_WAITING_FOR_LOGS", "authorization": {"runtime_launch_attempted": True}})
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
    for label in ("A1", "A2", "A3"):
        data_root = tmp_path / label
        files = data_root / "MQL5" / "Files"
        files.mkdir(parents=True)
        (data_root / "Config").mkdir(parents=True)
        (data_root / "Logs").mkdir(parents=True)
        (data_root / "MQL5" / "Logs").mkdir(parents=True)
        (data_root / "Config" / "a3_ml_prediction_observer_startup.ini").write_text(
            "\n".join(
                [
                    "AllowLiveTrading=0",
                    "Expert=A3MlPredictionObserver",
                    "ExpertParameters=A3MlPredictionObserver.passive_xauusd.set",
                    "Symbol=XAUUSD",
                    "Period=M5",
                ]
            ),
            encoding="utf-8",
        )
        (data_root / "Logs" / "20260621.log").write_text("ordinary terminal line\n", encoding="utf-8")
        (files / "A3_ML_EA_HANDOFF.csv").write_text("schema_version\na3_ml_ea_handoff_v1\n", encoding="utf-8")
        if runtime_logs:
            (files / "a3_ml_prediction_observer_startup.csv").write_text("event\nstarted\n", encoding="utf-8")
            (files / "a3_ml_prediction_observer_log.csv").write_text("action\nABSTAIN\n", encoding="utf-8")
            (files / "a3_ml_broker_shadow_tap.csv").write_text("event_source,ml_action\nstartup,ABSTAIN\n", encoding="utf-8")


def _write_no_go_reports(reports: Path) -> None:
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "NO_GO",
            "checks": [{"gate": "active_weeks", "passed": False, "observed": "3.0", "required": ">=8"}],
            "authorization": {"broker_action_authorized": False},
            "boundary": {"broker_action_authorized": False},
        },
    )
    _write_json(reports / "A3_ML_TRAINING_STATUS.json", _stage("REFUSED_NOT_READY"))
    _write_json(reports / "A3_ML_SHADOW_BRIDGE_STATUS.json", _stage("DISABLED_FAIL_CLOSED", authorization={"python_demo_predictions_authorized": False, "broker_action_authorized": False}))
    _write_json(reports / "A3_ML_EA_HANDOFF_STATUS.json", _stage("REFUSED_NOT_READY"))


def _write_ready_reports(reports: Path, tmp_path: Path) -> None:
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", _stage("PASS"))
    _write_json(reports / "A3_ML_TRAINING_STATUS.json", _stage("TRAINED_SHADOW_ONLY"))
    _write_json(
        reports / "A3_ML_SHADOW_BRIDGE_STATUS.json",
        _stage("READY_SHADOW_ONLY", authorization={"python_demo_predictions_authorized": True, "broker_action_authorized": False}),
    )
    _write_json(
        reports / "A3_ML_EA_HANDOFF_STATUS.json",
        _stage("PUBLISHED_TO_MT5_FILES", published_files=_handoff_files(tmp_path)),
    )


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


def _snapshot_row(account: str, label: str, direction: str, y_win: str) -> dict[str, str]:
    return {
        "account_scope": account,
        "account_label": label,
        "symbol": "XAUUSD",
        "source_signal_id": f"{account}-{direction}-{y_win}",
        "setup_group_id": f"G-{account}-{direction}-{y_win}",
        "decision_time_utc": "2026-06-01T00:00:00Z",
        "direction": direction,
        "regime": "FALLING",
        "session_bucket": "Morning",
        "candidate_trainable": "false",
        "y_win_expected": y_win,
    }


def _write_snapshot(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(_snapshot_row("1025742", "A1", "LONG", "1").keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


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
        path = tmp_path / account / "MQL5" / "Files" / "A3_ML_EA_HANDOFF.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("schema_version\n", encoding="utf-8")
        rows.append({"account_label": account, "target_path": str(path)})
    return rows


def _registry(tmp_path: Path) -> dict:
    return {
        "schema_version": "mt5_multi_account_registry_v1",
        "common": {
            "symbol": "XAUUSD",
            "expected_server_regex": "^Capital\\.ComMena-Demo$",
            "require_demo_trade_mode": True,
            "require_existing_terminal_process": True,
            "allow_mt5_login_call": False,
            "allow_symbol_select_call": False,
            "export_timezone": "UTC",
            "snapshot_safety_lag_minutes": 5,
        },
        "accounts": {
            "A1": _account("1025742", "A1", tmp_path / "A1"),
            "A2": _account("1033030", "A2", tmp_path / "A2"),
            "A3": _account("1033669", "A3", tmp_path / "A3"),
        },
    }


def _account(scope: str, label: str, data_root: Path) -> dict:
    return {
        "account_scope": scope,
        "account_label": label,
        "expected_login": scope,
        "terminal_exe": str(data_root / "terminal64.exe"),
        "expected_data_path": str(data_root),
        "portable": label != "A1",
        "role": "test",
        "symbol": "XAUUSD",
        "files_roots": [str(data_root / "MQL5" / "Files")],
        "log_catalog": f"config/ml/log_catalog_{label.lower()}.yaml",
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
