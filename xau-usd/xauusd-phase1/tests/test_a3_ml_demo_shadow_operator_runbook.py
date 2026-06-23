from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c29_reports_manual_attach_action_when_runtime_missing(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_shadow_operator_runbook import generate_demo_shadow_operator_runbook

    root = _root(tmp_path, confirmed=False)

    output = generate_demo_shadow_operator_runbook(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "ACTION_REQUIRED_MANUAL_ATTACH"
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["commands"]["post_attach_demo_shadow_wait"]
    assert payload["commands"]["deploy_broker_shadow_safe_presets"]
    assert payload["commands"]["demo_attach_watch"]
    assert payload["commands"]["generate_operator_launch_kit"]
    assert payload["commands"]["run_operator_launch_kit"]
    assert any("C28" in step for step in payload["operator_steps"])
    assert any("C30 safe preset" in step for step in payload["operator_steps"])
    md = output.with_suffix(".md").read_text(encoding="utf-8")
    assert "Exact Attach Matrix" in md
    assert "A1Executor.A1.a3_ml_shadow_readonly.set" in md
    assert len(payload["accounts"]) == 3


def test_c29_reports_confirmed_waiting_for_data_after_c28_passes(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_shadow_operator_runbook import generate_demo_shadow_operator_runbook

    root = _root(tmp_path, confirmed=True)

    output = generate_demo_shadow_operator_runbook(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "DEMO_SHADOW_RUNTIME_CONFIRMED_WAITING_FOR_DATA"
    assert pointer["c29_demo_shadow_operator_runbook_status"] == "DEMO_SHADOW_RUNTIME_CONFIRMED_WAITING_FOR_DATA"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False


def test_c29_script_loads() -> None:
    module = load_script("c29_generate_demo_shadow_operator_runbook")

    assert hasattr(module, "main")


def _root(tmp_path: Path, *, confirmed: bool) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(
        reports / "A3_ML_READINESS_GAP_REPORT.json",
        {
            "status": "GAP_REMAINS",
            "gate_gaps": [{"gate": "active_weeks", "passed": False, "gap_text": "need more weeks"}],
        },
    )
    _write_json(reports / "A3_ML_OBSERVER_MANUAL_ATTACH_PACKET.json", _c15_payload(tmp_path, confirmed))
    _write_json(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json", _c25_payload(tmp_path, confirmed))
    _write_json(reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json", {"status": "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED"})
    _write_json(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json", {"status": "DEPLOYED_SAFE_PASSIVE_PRESETS"})
    _write_json(
        reports / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json",
        {"status": "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS" if confirmed else "WAITING_FOR_MT5_RUNTIME_ATTACH"},
    )
    return root


def _c15_payload(tmp_path: Path, confirmed: bool) -> dict:
    return {
        "status": "RUNTIME_LOGS_PRESENT_ALL_ACCOUNTS" if confirmed else "MANUAL_ATTACH_REQUIRED",
        "accounts": [
            {
                "account_label": label,
                "account_scope": scope,
                "terminal_exe": str(tmp_path / label / "terminal64.exe"),
                "startup_log_exists": confirmed,
                "prediction_log_exists": confirmed,
                "expert_exists": True,
                "preset_exists": True,
                "preset_path": str(tmp_path / label / "MQL5" / "Presets" / "A3MlPredictionObserver.passive_xauusd.set"),
                "handoff_exists": True,
            }
            for scope, label in (("1025742", "A1"), ("1033030", "A2"), ("1033669", "A3"))
        ],
        "authorization": {"manual_attach_required": not confirmed, "broker_action_authorized": False},
    }


def _c25_payload(tmp_path: Path, confirmed: bool) -> dict:
    return {
        "status": "BROKER_SHADOW_RUNTIME_PRESENT_ALL_ACCOUNTS" if confirmed else "MANUAL_ATTACH_REQUIRED",
        "accounts": [
            {
                "account_label": label,
                "account_scope": scope,
                "handoff_exists": True,
                "broker_shadow_tap_exists": confirmed,
                "recommended_experts": [f"{label}Executor"],
                "safe_preset_deployed_all": True,
                "safe_preset_names": [f"{label}Executor.{label}.a3_ml_shadow_readonly.set"],
                "safe_preset_paths": [str(tmp_path / label / "MQL5" / "Presets" / f"{label}Executor.{label}.a3_ml_shadow_readonly.set")],
                "broker_shadow_tap_path": str(tmp_path / label / "MQL5" / "Files" / "a3_ml_broker_shadow_tap.csv"),
            }
            for scope, label in (("1025742", "A1"), ("1033030", "A2"), ("1033669", "A3"))
        ],
        "authorization": {"manual_attach_required": not confirmed, "broker_action_authorized": False},
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
