from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c06_refuses_when_shadow_bridge_disabled(tmp_path: Path) -> None:
    from ml.a3_meta_v1.ea_handoff import generate_ea_handoff_report

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_registry(config / "mt5_accounts.yaml", tmp_path)
    _write_contract(config / "a3_ml_ea_handoff_contract.json")
    predictions = reports / "A3_ML_SHADOW_PREDICTIONS.csv"
    _write_predictions(predictions, [_prediction_row("1025742", "A1", "ABSTAIN")])
    _write_json(
        reports / "A3_ML_SHADOW_BRIDGE_STATUS.json",
        _bridge_status("DISABLED_FAIL_CLOSED", predictions, ea_authorized=False),
    )
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})

    output = generate_ea_handoff_report(root, publish=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "REFUSED_NOT_READY"
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["mt5_file_publish_attempted"] is False
    assert payload["outputs"]["published_files"] == []


def test_c06_ready_dry_run_stages_per_account_files(tmp_path: Path) -> None:
    from ml.a3_meta_v1.ea_handoff import generate_ea_handoff_report

    root, reports, config = _ready_root(tmp_path)

    output = generate_ea_handoff_report(root, publish=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_DRY_RUN"
    assert payload["authorization"]["ea_consumption_authorized"] is True
    assert payload["authorization"]["mt5_file_publish_attempted"] is False
    assert len(payload["outputs"]["staged_files"]) == 3
    assert payload["outputs"]["published_files"] == []
    assert Path(payload["outputs"]["staged_files"][0]["path"]).exists()


def test_c06_publish_copies_only_after_ready_gate(tmp_path: Path) -> None:
    from ml.a3_meta_v1.ea_handoff import generate_ea_handoff_report

    root, reports, config = _ready_root(tmp_path)

    output = generate_ea_handoff_report(root, publish=True)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PUBLISHED_TO_MT5_FILES"
    assert payload["authorization"]["mt5_file_publish_attempted"] is True
    assert len(payload["outputs"]["published_files"]) == 3
    for item in payload["outputs"]["published_files"]:
        target = Path(item["target_path"])
        assert target.exists()
        assert target.name == "A3_ML_EA_HANDOFF.csv"


def test_c06_script_loads() -> None:
    module = load_script("c06_publish_ea_handoff")

    assert hasattr(module, "main")


def _ready_root(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_registry(config / "mt5_accounts.yaml", tmp_path)
    _write_contract(config / "a3_ml_ea_handoff_contract.json")
    predictions = reports / "A3_ML_SHADOW_PREDICTIONS.csv"
    _write_predictions(
        predictions,
        [
            _prediction_row("1025742", "A1", "TAKE"),
            _prediction_row("1033030", "A2", "SKIP"),
            _prediction_row("1033669", "A3", "SKIP"),
        ],
    )
    _write_json(reports / "A3_ML_SHADOW_BRIDGE_STATUS.json", _bridge_status("READY_SHADOW_ONLY", predictions, ea_authorized=True))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    return root, reports, config


def _write_registry(path: Path, tmp_path: Path) -> None:
    _write_json(
        path,
        {
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
                "A1": _account("1025742", "A1", tmp_path / "A1" / "MQL5" / "Files"),
                "A2": _account("1033030", "A2", tmp_path / "A2" / "MQL5" / "Files"),
                "A3": _account("1033669", "A3", tmp_path / "A3" / "MQL5" / "Files"),
            },
        },
    )


def _account(scope: str, label: str, files_root: Path) -> dict:
    return {
        "account_scope": scope,
        "account_label": label,
        "expected_login": scope,
        "terminal_exe": f"C:/{label}/terminal64.exe",
        "expected_data_path": f"C:/{label}",
        "portable": label != "A1",
        "role": "test",
        "symbol": "XAUUSD",
        "files_roots": [str(files_root)],
        "log_catalog": f"config/ml/log_catalog_{label.lower()}.yaml",
    }


def _write_contract(path: Path) -> None:
    _write_json(
        path,
        {
            "schema_version": "a3_ml_ea_handoff_contract_v1",
            "registry_path": "config/ml/mt5_accounts.yaml",
            "shadow_bridge_status_json": "outputs/reports/A3_ML_SHADOW_BRIDGE_STATUS.json",
            "shadow_predictions_csv": "outputs/reports/A3_ML_SHADOW_PREDICTIONS.csv",
            "status_report_json": "outputs/reports/A3_ML_EA_HANDOFF_STATUS.json",
            "staging_dir": "outputs/reports/ea_handoff",
            "terminal_file_name": "A3_ML_EA_HANDOFF.csv",
            "allowed_accounts": ["1025742", "1033030", "1033669"],
            "allowed_actions": ["TAKE", "SKIP", "ABSTAIN"],
        },
    )


def _bridge_status(status: str, predictions: Path, *, ea_authorized: bool) -> dict:
    return {
        "status": status,
        "dataset_version": "TEST",
        "authorization": {
            "python_demo_predictions_authorized": ea_authorized,
            "ea_consumption_authorized": ea_authorized,
            "broker_action_authorized": False,
        },
        "outputs": {
            "predictions_csv": str(predictions),
            "predictions_sha256": _sha256_file(predictions),
            "rows": 1,
        },
    }


def _prediction_row(account: str, label: str, action: str) -> dict[str, str]:
    return {
        "schema_version": "a3_ml_shadow_predictions_v1",
        "generated_at_utc": "2026-06-21T00:00:00Z",
        "expires_at_utc": "2026-06-21T00:15:00Z",
        "dataset_version": "TEST",
        "readiness_status": "PASS",
        "account_scope": account,
        "account_label": label,
        "symbol": "XAUUSD",
        "signal_id": "",
        "exact_signal_id": f"{account}-sig",
        "setup_group_id": "g1",
        "decision_time_utc": "2026-06-21T00:00:00Z",
        "direction": "LONG",
        "p_win_raw": "0.8",
        "p_win_calibrated": "0.8",
        "threshold": "0.5",
        "action": action,
        "reason": "test",
        "model_id": "m0",
        "model_hash": "hash",
        "feature_schema_hash": "schema",
        "drift_status": "OK",
        "python_demo_predictions_authorized": "true",
        "ea_consumption_authorized": "true",
        "broker_action_authorized": "false",
    }


def _write_predictions(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(_prediction_row("1025742", "A1", "ABSTAIN").keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
