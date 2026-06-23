from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c15_reports_manual_attach_required_when_logs_are_missing(tmp_path: Path) -> None:
    from ml.a3_meta_v1.observer_manual_attach_packet import generate_observer_manual_attach_packet

    root = _root_with_accounts(tmp_path, logs=False)

    output = generate_observer_manual_attach_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "MANUAL_ATTACH_REQUIRED"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["validations"][0]["passed"] is True
    assert any("A3MlPredictionObserver" in step for step in payload["manual_attach_steps"])
    assert any("C28" in step for step in payload["manual_attach_steps"])


def test_c15_reports_runtime_logs_present_when_all_accounts_log(tmp_path: Path) -> None:
    from ml.a3_meta_v1.observer_manual_attach_packet import generate_observer_manual_attach_packet

    root = _root_with_accounts(tmp_path, logs=True)

    output = generate_observer_manual_attach_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "RUNTIME_LOGS_PRESENT_ALL_ACCOUNTS"
    assert all(item["startup_log_exists"] for item in payload["accounts"])
    assert all(item["prediction_log_exists"] for item in payload["accounts"])


def test_c15_blocks_when_handoff_file_is_missing(tmp_path: Path) -> None:
    from ml.a3_meta_v1.observer_manual_attach_packet import generate_observer_manual_attach_packet

    root = _root_with_accounts(tmp_path, logs=False)
    (tmp_path / "A3" / "MQL5" / "Files" / "A3_ML_EA_HANDOFF.csv").unlink()

    output = generate_observer_manual_attach_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert any(item["check"] == "A3_handoff_exists" and not item["passed"] for item in payload["validations"])


def test_c15_script_loads() -> None:
    module = load_script("c15_generate_observer_manual_attach_packet")

    assert hasattr(module, "main")


def _root_with_accounts(tmp_path: Path, *, logs: bool) -> Path:
    root = tmp_path / "phase1"
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "A3_ML_OBSERVER_DEPLOY_STATUS.json", {"status": "DEPLOYED_PASSIVE_OBSERVER"})
    _write_json(reports / "A3_ML_FAIL_CLOSED_HANDOFF_REHEARSAL_STATUS.json", {"status": "PUBLISHED_FAIL_CLOSED_REHEARSAL"})
    _write_json(reports / "A3_ML_OBSERVER_RUNTIME_ATTACH_STATUS.json", {"status": "LAUNCH_SENT_WAITING_FOR_LOGS"})
    for label in ("A1", "A2", "A3"):
        data_root = tmp_path / label
        files = data_root / "MQL5" / "Files"
        (data_root / "MQL5" / "Experts").mkdir(parents=True)
        (data_root / "MQL5" / "Presets").mkdir(parents=True)
        files.mkdir(parents=True)
        (data_root / "MQL5" / "Experts" / "A3MlPredictionObserver.ex5").write_text("compiled\n", encoding="utf-8")
        (data_root / "MQL5" / "Presets" / "A3MlPredictionObserver.passive_xauusd.set").write_text(
            "InpDryRunOnly=true\n",
            encoding="utf-8",
        )
        (files / "A3_ML_EA_HANDOFF.csv").write_text("schema_version\n", encoding="utf-8")
        if logs:
            (files / "a3_ml_prediction_observer_startup.csv").write_text("startup\n", encoding="utf-8")
            (files / "a3_ml_prediction_observer_log.csv").write_text("log\n", encoding="utf-8")
    return root


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
