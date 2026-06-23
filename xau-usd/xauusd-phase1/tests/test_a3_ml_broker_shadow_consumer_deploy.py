from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c17_preflight_ready_without_compile(tmp_path: Path) -> None:
    from ml.a3_meta_v1.broker_shadow_consumer_deploy import deploy_broker_shadow_consumers

    root = _root_with_sources(tmp_path)

    output = deploy_broker_shadow_consumers(root, compile_scratch=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_READY"
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["boundary"]["profile_or_chart_file_write_attempted"] is False
    assert any(item["check"] == "shadow_tap_include_exists" and item["passed"] for item in payload["validations"])


def test_c17_deploys_source_only_when_compile_skipped(tmp_path: Path) -> None:
    from ml.a3_meta_v1.broker_shadow_consumer_deploy import deploy_broker_shadow_consumers

    root = _root_with_sources(tmp_path)

    output = deploy_broker_shadow_consumers(root, deploy=True, compile_scratch=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "DEPLOYED_SOURCE_ONLY_SHADOW_CONSUMERS"
    assert (tmp_path / "A1" / "MQL5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5").exists()
    assert (tmp_path / "A2" / "MQL5" / "Include" / "A3MlShadowTap.mqh").exists()
    assert (tmp_path / "A3" / "MQL5" / "Experts" / "Account3SoftRetestExecutor.mq5").exists()


def test_c17_script_loads() -> None:
    module = load_script("c17_deploy_broker_shadow_consumers")

    assert hasattr(module, "main")


def _root_with_sources(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    experts = root / "mt5" / "Experts"
    include = root / "mt5" / "Include"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    experts.mkdir(parents=True)
    include.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    for source_name in (
        "Account3BreakoutImprovedExecutor.mq5",
        "Account3BreakoutPlainExecutor.mq5",
        "Account3BreakoutTier1CompatExecutor.mq5",
        "Account3SoftRetestExecutor.mq5",
        "Phase2ExperimentalDemoExecutor.mq5",
        "Phase2ExperimentalDemoRepairExecutor.mq5",
    ):
        (experts / source_name).write_text("#property strict\nvoid OnTick() {}\n", encoding="utf-8")
    (include / "A3MlShadowTap.mqh").write_text("#include <A3MlEaHandoff.mqh>\n", encoding="utf-8")
    (include / "A3MlEaHandoff.mqh").write_text("#define A3_ML_EA_HANDOFF_DEFAULT_FILE \"A3_ML_EA_HANDOFF.csv\"\n", encoding="utf-8")
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
