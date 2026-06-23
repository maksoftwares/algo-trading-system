from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c20_waits_when_handoff_exists_but_runtime_logs_missing(tmp_path: Path) -> None:
    from ml.a3_meta_v1.runtime_evidence import audit_runtime_evidence

    root = _root_with_accounts(tmp_path, observer_logs=False, broker_tap=False)

    output = audit_runtime_evidence(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_MT5_RUNTIME_LOGS"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["runtime_evidence"]["handoff_files_all_accounts"] is True
    assert payload["runtime_evidence"]["passive_observer_runtime_all_accounts"] is False
    assert payload["runtime_evidence"]["broker_shadow_tap_runtime_all_accounts"] is False


def test_c20_detects_all_runtime_evidence(tmp_path: Path) -> None:
    from ml.a3_meta_v1.runtime_evidence import audit_runtime_evidence

    root = _root_with_accounts(tmp_path, observer_logs=True, broker_tap=True)

    output = audit_runtime_evidence(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS"
    assert payload["runtime_evidence"]["passive_observer_runtime_all_accounts"] is True
    assert payload["runtime_evidence"]["broker_shadow_tap_runtime_all_accounts"] is True
    assert all(item["observer_startup"]["csv_rows"] == 1 for item in payload["accounts"])
    assert pointer["c20_runtime_evidence_status"] == "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c20_reports_partial_runtime_evidence(tmp_path: Path) -> None:
    from ml.a3_meta_v1.runtime_evidence import audit_runtime_evidence

    root = _root_with_accounts(tmp_path, observer_logs=False, broker_tap=False)
    files = tmp_path / "A1" / "MQL5" / "Files"
    (files / "a3_ml_prediction_observer_startup.csv").write_text("event\nstarted\n", encoding="utf-8")

    output = audit_runtime_evidence(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PARTIAL_RUNTIME_EVIDENCE_PRESENT"
    assert payload["runtime_evidence"]["any_runtime_evidence"] is True


def test_c20_blocks_missing_handoff_file(tmp_path: Path) -> None:
    from ml.a3_meta_v1.runtime_evidence import audit_runtime_evidence

    root = _root_with_accounts(tmp_path, observer_logs=True, broker_tap=True)
    (tmp_path / "A3" / "MQL5" / "Files" / "A3_ML_EA_HANDOFF.csv").unlink()

    output = audit_runtime_evidence(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert any(item["check"] == "A3_handoff_file_exists" and not item["passed"] for item in payload["validations"])


def test_c20_script_loads() -> None:
    module = load_script("c20_audit_runtime_evidence")

    assert hasattr(module, "main")


def _root_with_accounts(tmp_path: Path, *, observer_logs: bool, broker_tap: bool) -> Path:
    root = tmp_path / "phase1"
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    for label in ("A1", "A2", "A3"):
        files = tmp_path / label / "MQL5" / "Files"
        files.mkdir(parents=True)
        (files / "A3_ML_EA_HANDOFF.csv").write_text("schema_version\na3_ml_ea_handoff_v1\n", encoding="utf-8")
        if observer_logs:
            (files / "a3_ml_prediction_observer_startup.csv").write_text("event\nstarted\n", encoding="utf-8")
            (files / "a3_ml_prediction_observer_log.csv").write_text("action\nABSTAIN\n", encoding="utf-8")
        if broker_tap:
            (files / "a3_ml_broker_shadow_tap.csv").write_text("event_source,ml_action\nstartup,ABSTAIN\n", encoding="utf-8")
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
