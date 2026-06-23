from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c31_reports_waiting_with_exact_missing_paths(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_attach_watch import watch_demo_attach

    root = _root(tmp_path, runtime_files=False)

    output = watch_demo_attach(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))
    md = output.with_suffix(".md").read_text(encoding="utf-8")

    assert payload["status"] == "WAITING_FOR_MANUAL_ATTACH"
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c31_demo_attach_watch_status"] == "WAITING_FOR_MANUAL_ATTACH"
    assert all("broker_shadow_tap" in item["missing_runtime_artifacts"] for item in payload["accounts"])
    assert "Exact Missing Paths" in md
    assert "a3_ml_broker_shadow_tap.csv" in md


def test_c31_reports_ready_for_c28_when_runtime_files_exist(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_attach_watch import watch_demo_attach

    root = _root(tmp_path, runtime_files=True)

    output = watch_demo_attach(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS"
    assert payload["runtime_evidence"]["observer_runtime_files_all_accounts"] is True
    assert payload["runtime_evidence"]["broker_shadow_tap_all_accounts"] is True
    assert all(item["ready_for_c28"] for item in payload["accounts"])


def test_c31_script_loads() -> None:
    module = load_script("c31_watch_demo_attach")

    assert hasattr(module, "main")


def _root(tmp_path: Path, *, runtime_files: bool) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json", _c15_payload(tmp_path))
    _write_json(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json", _c25_payload(tmp_path))
    _write_json(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json", _c30_payload(tmp_path))
    for scope, label in (("1025742", "A1"), ("1033030", "A2"), ("1033669", "A3")):
        data_root = tmp_path / label
        files = data_root / "MQL5" / "Files"
        presets = data_root / "MQL5" / "Presets"
        files.mkdir(parents=True)
        presets.mkdir(parents=True)
        (files / "A3_ML_EA_HANDOFF.csv").write_text("schema_version\na3_ml_ea_handoff_v1\n", encoding="utf-8")
        (presets / "A3MlPredictionObserver.passive_xauusd.set").write_text("InpDryRunOnly=true\n", encoding="utf-8")
        (presets / f"{label}Executor.{label}.a3_ml_shadow_readonly.set").write_text(
            "InpDryRunOnly=true\nInpBrokerActionAllowed=false\nInpMlShadowReadEnabled=true\n",
            encoding="utf-8",
        )
        if runtime_files:
            (files / "a3_ml_prediction_observer_startup.csv").write_text("event\nSTARTUP\n", encoding="utf-8")
            (files / "a3_ml_prediction_observer_log.csv").write_text("action\nABSTAIN\n", encoding="utf-8")
            (files / "a3_ml_broker_shadow_tap.csv").write_text("event_source,ml_action\nSTARTUP,ABSTAIN\n", encoding="utf-8")
    return root


def _c15_payload(tmp_path: Path) -> dict:
    return {
        "status": "MANUAL_ATTACH_REQUIRED",
        "accounts": [
            {
                "account_label": label,
                "account_scope": scope,
                "preset_path": str(tmp_path / label / "MQL5" / "Presets" / "A3MlPredictionObserver.passive_xauusd.set"),
            }
            for scope, label in (("1025742", "A1"), ("1033030", "A2"), ("1033669", "A3"))
        ],
    }


def _c25_payload(tmp_path: Path) -> dict:
    return {
        "status": "MANUAL_ATTACH_REQUIRED",
        "accounts": [
            {
                "account_label": label,
                "account_scope": scope,
                "recommended_experts": [f"{label}Executor"],
                "safe_preset_names": [f"{label}Executor.{label}.a3_ml_shadow_readonly.set"],
                "safe_preset_paths": [str(tmp_path / label / "MQL5" / "Presets" / f"{label}Executor.{label}.a3_ml_shadow_readonly.set")],
            }
            for scope, label in (("1025742", "A1"), ("1033030", "A2"), ("1033669", "A3"))
        ],
    }


def _c30_payload(tmp_path: Path) -> dict:
    return {
        "status": "DEPLOYED_SAFE_PASSIVE_PRESETS",
        "targets": [
            {
                "account_label": label,
                "account_scope": scope,
                "presets": [
                    {
                        "preset_name": f"{label}Executor.{label}.a3_ml_shadow_readonly.set",
                        "target_path": str(tmp_path / label / "MQL5" / "Presets" / f"{label}Executor.{label}.a3_ml_shadow_readonly.set"),
                    }
                ],
            }
            for scope, label in (("1025742", "A1"), ("1033030", "A2"), ("1033669", "A3"))
        ],
    }


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
