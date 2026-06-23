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


def test_c30_deploys_safe_passive_broker_shadow_presets(tmp_path: Path) -> None:
    from ml.a3_meta_v1.broker_shadow_preset_deploy import deploy_broker_shadow_presets

    root = _root(tmp_path)

    output = deploy_broker_shadow_presets(root, deploy=True)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "DEPLOYED_SAFE_PASSIVE_PRESETS"
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c30_broker_shadow_preset_deploy_status"] == "DEPLOYED_SAFE_PASSIVE_PRESETS"
    assert payload["deployed_presets"]
    for item in payload["deployed_presets"]:
        text = Path(item["target_path"]).read_text(encoding="utf-8")
        assert "InpDryRunOnly=true" in text
        assert "InpBrokerActionAllowed=false" in text
        assert "InpMlShadowReadEnabled=true" in text
        assert "InpMlHandoffFileName=A3_ML_EA_HANDOFF.csv" in text
        assert item["account_scope"] in text


def test_c30_blocks_when_required_safety_input_is_missing(tmp_path: Path) -> None:
    from ml.a3_meta_v1.broker_shadow_preset_deploy import deploy_broker_shadow_presets

    root = _root(tmp_path, missing_broker_action_input=True)

    output = deploy_broker_shadow_presets(root, deploy=True)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert payload["authorization"]["broker_shadow_preset_deploy_attempted"] is False
    assert any(
        item["check"] == "source_supports_safe_inputs_Phase2ExperimentalDemoExecutor.mq5" and not item["passed"]
        for item in payload["validations"]
    )
    assert not list((tmp_path / "A1" / "MQL5" / "Presets").glob("*.set"))


def test_c30_script_loads() -> None:
    module = load_script("c30_deploy_broker_shadow_presets")

    assert hasattr(module, "main")


def _root(tmp_path: Path, *, missing_broker_action_input: bool = False) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    experts = root / "mt5" / "Experts"
    include = root / "mt5" / "Include"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    experts.mkdir(parents=True)
    include.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "A3_ML_BROKER_SHADOW_CONSUMER_DEPLOY_STATUS.json", {"status": "DEPLOYED_COMPILED_SHADOW_CONSUMERS"})
    (include / "A3MlShadowTap.mqh").write_text(
        "\n".join(
            [
                "input bool InpMlShadowReadEnabled = true;",
                "input string InpMlHandoffFileName = \"A3_ML_EA_HANDOFF.csv\";",
                "input string InpMlShadowLogFileName = \"a3_ml_broker_shadow_tap.csv\";",
            ]
        ),
        encoding="utf-8",
    )
    for source_name in sorted({name for names in ACCOUNT_SOURCES.values() for name in names}):
        omit_broker_action = missing_broker_action_input and source_name == "Phase2ExperimentalDemoExecutor.mq5"
        (experts / source_name).write_text(_source_text(omit_broker_action=omit_broker_action), encoding="utf-8")
    for label in ("A1", "A2", "A3"):
        (tmp_path / label / "MQL5" / "Presets").mkdir(parents=True)
    return root


def _source_text(*, omit_broker_action: bool) -> str:
    lines = [
        "#include <A3MlShadowTap.mqh>",
        'input string InpRunId = "test";',
        "input bool InpDryRunOnly = true;",
    ]
    if not omit_broker_action:
        lines.append("input bool InpBrokerActionAllowed = false;")
    lines.extend(
        [
            'input string InpTargetSymbol = "XAUUSD";',
            'input string InpExpectedServerMarker = "Demo";',
            'input string InpAllowedAccountLoginsCsv = "";',
        ]
    )
    return "\n".join(lines)


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
