from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c32_generates_safe_operator_launch_kit(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_operator_launch_kit import generate_demo_operator_launch_kit

    root = _root(tmp_path, c31_status="WAITING_FOR_MANUAL_ATTACH")

    output = generate_demo_operator_launch_kit(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    script_path = Path(payload["outputs"]["operator_kit_script"])
    script = script_path.read_text(encoding="utf-8")

    assert payload["status"] == "READY_OPERATOR_ATTACH_KIT"
    assert payload["authorization"]["broker_action_authorized"] is False
    assert script_path.exists()
    assert "A3 ML demo attach kit" in script
    assert "A3MlPredictionObserver" in script
    assert "A1Executor.A1.a3_ml_shadow_readonly.set" in script
    assert "c31_watch_demo_attach.py" in script
    assert "c28_wait_for_demo_shadow_post_attach.py" in script
    for forbidden in ("OrderSend", "CTrade", "TRADE_ACTION_", "AllowLiveTrading=1", "Start-Process", "Stop-Process"):
        assert forbidden not in script


def test_c32_reports_ready_to_run_c28_when_c31_is_complete(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_operator_launch_kit import generate_demo_operator_launch_kit

    root = _root(tmp_path, c31_status="ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS")

    output = generate_demo_operator_launch_kit(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "ATTACH_FILES_READY_RUN_C28"
    assert "post_attach_demo_shadow_wait" in payload["commands"]


def test_c32_script_loads() -> None:
    module = load_script("c32_generate_demo_operator_launch_kit")

    assert hasattr(module, "main")


def _root(tmp_path: Path, *, c31_status: str) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "A3_ML_READINESS_GAP_REPORT.json", {"status": "GAP_REMAINS", "gate_gaps": []})
    _write_json(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json", _c15_payload(tmp_path))
    _write_json(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json", _c25_payload(tmp_path))
    _write_json(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json", {"status": "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED"})
    _write_json(reports / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json", {"status": "WAITING_FOR_MT5_RUNTIME_ATTACH"})
    _write_json(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json", {"status": "DEPLOYED_SAFE_PASSIVE_PRESETS"})
    _write_json(reports / "A3_ML_DEMO_ATTACH_WATCH_STATUS.json", {"status": c31_status})
    return root


def _c15_payload(tmp_path: Path) -> dict:
    return {
        "status": "MANUAL_ATTACH_REQUIRED",
        "accounts": [
            {
                "account_label": label,
                "account_scope": scope,
                "terminal_exe": str(tmp_path / label / "terminal64.exe"),
                "startup_log_exists": False,
                "prediction_log_exists": False,
                "expert_exists": True,
                "preset_exists": True,
                "preset_path": str(tmp_path / label / "MQL5" / "Presets" / "A3MlPredictionObserver.passive_xauusd.set"),
                "handoff_exists": True,
            }
            for scope, label in (("1025742", "A1"), ("1033030", "A2"), ("1033669", "A3"))
        ],
        "authorization": {"manual_attach_required": True, "broker_action_authorized": False},
    }


def _c25_payload(tmp_path: Path) -> dict:
    return {
        "status": "MANUAL_ATTACH_REQUIRED",
        "accounts": [
            {
                "account_label": label,
                "account_scope": scope,
                "handoff_exists": True,
                "broker_shadow_tap_exists": False,
                "recommended_experts": [f"{label}Executor"],
                "safe_preset_deployed_all": True,
                "safe_preset_names": [f"{label}Executor.{label}.a3_ml_shadow_readonly.set"],
                "safe_preset_paths": [str(tmp_path / label / "MQL5" / "Presets" / f"{label}Executor.{label}.a3_ml_shadow_readonly.set")],
                "broker_shadow_tap_path": str(tmp_path / label / "MQL5" / "Files" / "a3_ml_broker_shadow_tap.csv"),
            }
            for scope, label in (("1025742", "A1"), ("1033030", "A2"), ("1033669", "A3"))
        ],
        "authorization": {"manual_attach_required": True, "broker_action_authorized": False},
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
