from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ACCOUNT_SOURCES = {
    "A1": ("Phase2ExperimentalDemoExecutor.mq5", "Phase2ExperimentalDemoRepairExecutor.mq5"),
    "A2": ("Phase2ExperimentalDemoExecutor.mq5",),
    "A3": (
        "Account3BreakoutImprovedExecutor.mq5",
        "Account3BreakoutPlainExecutor.mq5",
        "Account3BreakoutTier1CompatExecutor.mq5",
        "Account3SoftRetestExecutor.mq5",
    ),
}


def test_c25_reports_manual_attach_required_when_broker_taps_missing(tmp_path: Path) -> None:
    from ml.a3_meta_v1.broker_shadow_manual_attach_packet import generate_broker_shadow_manual_attach_packet

    root = _root_with_accounts(tmp_path, tap_logs=False)

    output = generate_broker_shadow_manual_attach_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "MANUAL_ATTACH_REQUIRED"
    assert payload["authorization"]["manual_attach_required"] is True
    assert payload["authorization"]["broker_action_authorized"] is False
    assert all(item["expected_compiled_ex5_all_exist"] for item in payload["accounts"])
    assert all(item["safe_preset_deployed_all"] for item in payload["accounts"])
    assert any("InpBrokerActionAllowed=false" in step for step in payload["manual_attach_steps"])
    assert any("C30 safe preset" in step for step in payload["manual_attach_steps"])
    assert any("C28" in step for step in payload["manual_attach_steps"])


def test_c25_reports_runtime_present_when_all_broker_taps_exist(tmp_path: Path) -> None:
    from ml.a3_meta_v1.broker_shadow_manual_attach_packet import generate_broker_shadow_manual_attach_packet

    root = _root_with_accounts(tmp_path, tap_logs=True)

    output = generate_broker_shadow_manual_attach_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "BROKER_SHADOW_RUNTIME_PRESENT_ALL_ACCOUNTS"
    assert payload["runtime_evidence"]["broker_shadow_tap_runtime_all_accounts"] is True
    assert all(item["broker_shadow_tap_exists"] for item in payload["accounts"])


def test_c25_blocks_when_active_broker_consumers_are_missing(tmp_path: Path) -> None:
    from ml.a3_meta_v1.broker_shadow_manual_attach_packet import generate_broker_shadow_manual_attach_packet

    root = _root_with_accounts(tmp_path, tap_logs=False, active_broker_consumers=False)

    output = generate_broker_shadow_manual_attach_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert any(
        item["check"] == "A1_active_broker_executor_consumers_ready" and not item["passed"]
        for item in payload["validations"]
    )


def test_c25_script_loads() -> None:
    module = load_script("c25_generate_broker_shadow_manual_attach_packet")

    assert hasattr(module, "main")


def _root_with_accounts(
    tmp_path: Path,
    *,
    tap_logs: bool,
    active_broker_consumers: bool = True,
    c17_status: str = "DEPLOYED_COMPILED_SHADOW_CONSUMERS",
) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    for label in ("A1", "A2", "A3"):
        data_root = tmp_path / label
        files = data_root / "MQL5" / "Files"
        experts = data_root / "MQL5" / "Experts"
        include = data_root / "MQL5" / "Include"
        presets = data_root / "MQL5" / "Presets"
        files.mkdir(parents=True)
        experts.mkdir(parents=True)
        include.mkdir(parents=True)
        presets.mkdir(parents=True)
        (files / "A3_ML_EA_HANDOFF.csv").write_text("schema_version\na3_ml_ea_handoff_v1\n", encoding="utf-8")
        (include / "A3MlShadowTap.mqh").write_text("#include <A3MlEaHandoff.mqh>\n", encoding="utf-8")
        (include / "A3MlEaHandoff.mqh").write_text("bool A3MlEaHandoffReadLatest(){return false;}\n", encoding="utf-8")
        for source_name in ACCOUNT_SOURCES[label]:
            source = experts / source_name
            source.write_text("#include <A3MlShadowTap.mqh>\n", encoding="utf-8")
            source.with_suffix(".ex5").write_text("compiled\n", encoding="utf-8")
            (presets / f"{Path(source_name).stem}.{label}.a3_ml_shadow_readonly.set").write_text(
                "\n".join(
                    [
                        "InpDryRunOnly=true",
                        "InpBrokerActionAllowed=false",
                        "InpMlShadowReadEnabled=true",
                        "InpMlHandoffFileName=A3_ML_EA_HANDOFF.csv",
                        "InpMlShadowLogFileName=a3_ml_broker_shadow_tap.csv",
                        "InpTargetSymbol=XAUUSD",
                        "InpExpectedServerMarker=Demo",
                        f"InpAllowedAccountLoginsCsv={_scope(label)}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
        if tap_logs:
            (files / "a3_ml_broker_shadow_tap.csv").write_text("event_source,ml_action\nSTARTUP,ABSTAIN\n", encoding="utf-8")
    _write_json(reports / "A3_ML_EA_CONSUMER_READINESS_STATUS.json", _c16_status(tmp_path, active_broker_consumers))
    _write_json(reports / "A3_ML_BROKER_SHADOW_CONSUMER_DEPLOY_STATUS.json", {"status": c17_status, "deployed_files": []})
    _write_json(reports / "A3_ML_RUNTIME_EVIDENCE_STATUS.json", _c20_status(tap_logs))
    _write_json(reports / "A3_ML_BROKER_SHADOW_PRESET_DEPLOY_STATUS.json", _c30_status(tmp_path))
    return root


def _c16_status(tmp_path: Path, active_broker_consumers: bool) -> dict:
    accounts = []
    for label in ("A1", "A2", "A3"):
        expert_name = Path(ACCOUNT_SOURCES[label][0]).stem
        active = (
            [
                {
                    "expert_name": expert_name,
                    "source_found": True,
                    "can_consume_ml_handoff": True,
                    "detail": "uses A3 ML handoff reader",
                }
            ]
            if active_broker_consumers
            else []
        )
        accounts.append(
            {
                "account_label": label,
                "files_root": str(tmp_path / label / "MQL5" / "Files"),
                "active_broker_executors": active,
                "attached_profiles": [
                    {
                        "expert_name": expert_name,
                        "enabled": True,
                        "role": "broker_executor_candidate",
                    }
                ]
                if active_broker_consumers
                else [],
            }
        )
    return {
        "status": "BROKER_EXECUTOR_CONSUMERS_READY" if active_broker_consumers else "OBSERVER_ONLY_CONSUMER_READY",
        "accounts": accounts,
    }


def _c20_status(tap_logs: bool) -> dict:
    return {
        "status": "RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS" if tap_logs else "WAITING_FOR_MT5_RUNTIME_LOGS",
        "accounts": [
            {
                "account_label": label,
                "handoff": {"exists": True},
                "broker_shadow_tap": {"exists": tap_logs, "csv_rows": 1 if tap_logs else 0},
            }
            for label in ("A1", "A2", "A3")
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


def _c30_status(tmp_path: Path) -> dict:
    return {
        "status": "DEPLOYED_SAFE_PASSIVE_PRESETS",
        "targets": [
            {
                "account_label": label,
                "account_scope": _scope(label),
                "presets_dir": str(tmp_path / label / "MQL5" / "Presets"),
                "presets": [
                    {
                        "source_name": source_name,
                        "expert_name": Path(source_name).stem,
                        "preset_name": f"{Path(source_name).stem}.{label}.a3_ml_shadow_readonly.set",
                        "target_path": str(tmp_path / label / "MQL5" / "Presets" / f"{Path(source_name).stem}.{label}.a3_ml_shadow_readonly.set"),
                        "content_safe": True,
                    }
                    for source_name in ACCOUNT_SOURCES[label]
                ],
            }
            for label in ("A1", "A2", "A3")
        ],
    }


def _scope(label: str) -> str:
    return {"A1": "1025742", "A2": "1033030", "A3": "1033669"}[label]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
