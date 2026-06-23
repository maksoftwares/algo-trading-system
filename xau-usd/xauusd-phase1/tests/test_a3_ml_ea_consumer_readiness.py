from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c16_reports_gap_when_active_executors_do_not_read_handoff(tmp_path: Path) -> None:
    from ml.a3_meta_v1.ea_consumer_readiness import audit_ea_ml_consumers

    root = _root_with_accounts(tmp_path, executor_reads_handoff=False)

    output = audit_ea_ml_consumers(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "BROKER_EXECUTOR_CONSUMER_GAP"
    assert payload["authorization"]["passive_observer_ml_consumer_ready"] is True
    assert payload["authorization"]["broker_executor_ml_consumer_ready"] is False
    assert any(item["check"] == "active_broker_executor_consumers_ready" and not item["passed"] for item in payload["validations"])
    assert all(item["active_broker_executors"] for item in payload["accounts"])


def test_c16_reports_ready_when_active_executors_read_handoff(tmp_path: Path) -> None:
    from ml.a3_meta_v1.ea_consumer_readiness import audit_ea_ml_consumers

    root = _root_with_accounts(tmp_path, executor_reads_handoff=True)

    output = audit_ea_ml_consumers(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "BROKER_EXECUTOR_CONSUMERS_READY"
    assert payload["authorization"]["broker_executor_ml_consumer_ready"] is True
    assert all(item["can_consume_ml_handoff"] for account in payload["accounts"] for item in account["active_broker_executors"])


def test_c16_resolves_handoff_reader_through_shared_include(tmp_path: Path) -> None:
    from ml.a3_meta_v1.ea_consumer_readiness import audit_ea_ml_consumers

    root = _root_with_accounts(tmp_path, executor_reads_handoff=False)
    for label in ("A1", "A2", "A3"):
        data_root = tmp_path / label
        (data_root / "MQL5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5").write_text(
            "#property strict\n#include <A3MlShadowTap.mqh>\nvoid OnTick() {}\n",
            encoding="utf-8",
        )
        (data_root / "MQL5" / "Include" / "A3MlShadowTap.mqh").write_text(
            "#include <A3MlEaHandoff.mqh>\nvoid Tap(){A3MlEaHandoffDecision d; A3MlEaHandoffReadLatest(d, _Symbol, \"A3_ML_EA_HANDOFF.csv\");}\n",
            encoding="utf-8",
        )

    output = audit_ea_ml_consumers(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "BROKER_EXECUTOR_CONSUMERS_READY"
    assert all(item["can_consume_ml_handoff"] for account in payload["accounts"] for item in account["active_broker_executors"])


def test_c16_blocks_when_observer_is_missing(tmp_path: Path) -> None:
    from ml.a3_meta_v1.ea_consumer_readiness import audit_ea_ml_consumers

    root = _root_with_accounts(tmp_path, executor_reads_handoff=True)
    (tmp_path / "A2" / "MQL5" / "Experts" / "A3MlPredictionObserver.ex5").unlink()

    output = audit_ea_ml_consumers(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert any(item["check"] == "passive_observer_consumer_ready_all_accounts" and not item["passed"] for item in payload["validations"])


def test_c16_script_loads() -> None:
    module = load_script("c16_audit_ea_ml_consumers")

    assert hasattr(module, "main")


def _root_with_accounts(tmp_path: Path, *, executor_reads_handoff: bool) -> Path:
    root = tmp_path / "phase1"
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    repo_experts = root / "mt5" / "Experts"
    repo_experts.mkdir(parents=True)
    (repo_experts / "A3MlPredictionObserver.mq5").write_text(_observer_source(), encoding="utf-8")
    (repo_experts / "Phase2ExperimentalDemoExecutor.mq5").write_text(_executor_source(executor_reads_handoff), encoding="utf-8")
    for label in ("A1", "A2", "A3"):
        data_root = tmp_path / label
        experts = data_root / "MQL5" / "Experts"
        include = data_root / "MQL5" / "Include"
        files = data_root / "MQL5" / "Files"
        profiles = data_root / "MQL5" / "Profiles" / "Charts" / "Default"
        experts.mkdir(parents=True)
        include.mkdir(parents=True)
        files.mkdir(parents=True)
        profiles.mkdir(parents=True)
        (experts / "A3MlPredictionObserver.mq5").write_text(_observer_source(), encoding="utf-8")
        (experts / "A3MlPredictionObserver.ex5").write_text("compiled\n", encoding="utf-8")
        (experts / "Phase2ExperimentalDemoExecutor.mq5").write_text(_executor_source(executor_reads_handoff), encoding="utf-8")
        (experts / "Phase2ExperimentalDemoExecutor.ex5").write_text("compiled\n", encoding="utf-8")
        (include / "A3MlEaHandoff.mqh").write_text("#define A3_ML_EA_HANDOFF_DEFAULT_FILE \"A3_ML_EA_HANDOFF.csv\"\n", encoding="utf-8")
        (files / "A3_ML_EA_HANDOFF.csv").write_text("schema_version\n", encoding="utf-8")
        profile_encoding = "utf-16" if label == "A2" else "utf-8"
        (profiles / "chart01.chr").write_text(_chart_profile("Phase2ExperimentalDemoExecutor"), encoding=profile_encoding)
    return root


def _observer_source() -> str:
    return "\n".join(
        [
            "#property strict",
            "#include <A3MlEaHandoff.mqh>",
            "void OnTick() {",
            "  A3MlEaHandoffDecision decision;",
            "  A3MlEaHandoffReadLatest(decision, _Symbol, \"A3_ML_EA_HANDOFF.csv\");",
            "}",
        ]
    )


def _executor_source(reads_handoff: bool) -> str:
    if not reads_handoff:
        return "#property strict\nvoid OnTick() {}\n"
    return "\n".join(
        [
            "#property strict",
            "#include <A3MlEaHandoff.mqh>",
            "void OnTick() {",
            "  A3MlEaHandoffDecision decision;",
            "  A3MlEaHandoffReadLatest(decision, _Symbol, \"A3_ML_EA_HANDOFF.csv\");",
            "}",
        ]
    )


def _chart_profile(expert_name: str) -> str:
    return "\n".join(
        [
            "<expert>",
            f"name={expert_name}",
            f"path=Experts\\{expert_name}.ex5",
            "expertmode=1",
            "</expert>",
        ]
    )


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
