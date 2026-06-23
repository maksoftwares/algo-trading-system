from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c09_preflight_ready_without_mt5_or_terminal_changes(tmp_path: Path) -> None:
    from ml.a3_meta_v1.observer_deploy import prepare_observer_deploy

    root = tmp_path / "phase1"
    _write_minimal_root(root, tmp_path)

    output = prepare_observer_deploy(root, compile_scratch=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_READY"
    assert payload["mode"] == "PREFLIGHT_ONLY"
    assert payload["authorization"]["passive_observer_deploy_attempted"] is False
    assert payload["boundary"]["mt5_connection_attempted"] is False
    assert payload["boundary"]["ea_source_deploy_attempted"] is False
    assert payload["boundary"]["broker_action_authorized"] is False
    assert len(payload["targets"]) == 3


def test_c09_deploy_copies_passive_files_to_all_three_accounts(tmp_path: Path) -> None:
    from ml.a3_meta_v1.observer_deploy import prepare_observer_deploy

    root = tmp_path / "phase1"
    _write_minimal_root(root, tmp_path)

    output = prepare_observer_deploy(root, deploy=True, compile_scratch=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "DEPLOYED_PASSIVE_OBSERVER"
    assert payload["authorization"]["passive_observer_deploy_attempted"] is True
    assert len(payload["outputs"]["deployed_files"]) == 9
    for item in payload["outputs"]["deployed_files"]:
        assert Path(item["target_path"]).exists()
    assert not any(item["artifact"] == "compiled_ex5" for item in payload["outputs"]["deployed_files"])


def test_c09_blocks_missing_terminal_data_root(tmp_path: Path) -> None:
    from ml.a3_meta_v1.observer_deploy import prepare_observer_deploy

    root = tmp_path / "phase1"
    _write_minimal_root(root, tmp_path, a3_data_root=None)

    output = prepare_observer_deploy(root, compile_scratch=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert any(item["check"] == "all_accounts_have_data_roots" and not item["passed"] for item in payload["validations"])


def test_c09_render_mentions_passive_boundaries() -> None:
    from ml.a3_meta_v1.observer_deploy import render_observer_deploy_status_md

    report = render_observer_deploy_status_md(
        {
            "status": "PREFLIGHT_READY",
            "mode": "PREFLIGHT_ONLY",
            "authorization": {
                "passive_observer_deploy_requested": False,
                "passive_observer_deploy_attempted": False,
            },
            "targets": [],
            "compile": {"attempted": False, "passed": True},
            "validations": [{"check": "registry_exists", "passed": True, "detail": "ok"}],
            "outputs": {"deployed_files": []},
            "boundary": {"ea_source_deploy_attempted": False},
            "next_allowed_stage": "Run later.",
        }
    )

    assert "Overall status: PREFLIGHT_READY" in report
    assert "MT5 connection attempted: false." in report
    assert "Profile or chart change authorized: false." in report
    assert "Broker action authorized: false." in report


def test_c09_script_loads() -> None:
    module = load_script("c09_prepare_ml_observer_deploy")

    assert hasattr(module, "main")


def _write_minimal_root(root: Path, tmp_path: Path, *, a3_data_root: Path | None | bool = True) -> None:
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    experts = root / "mt5" / "Experts"
    include = root / "mt5" / "Include"
    presets = root / "mt5" / "Presets"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    experts.mkdir(parents=True)
    include.mkdir(parents=True)
    presets.mkdir(parents=True)
    (experts / "A3MlPredictionObserver.mq5").write_text(
        "#property strict\n#include <A3MlEaHandoff.mqh>\nvoid OnTick() {}\n",
        encoding="utf-8",
    )
    (include / "A3MlEaHandoff.mqh").write_text("#define A3_ML_EA_HANDOFF_DEFAULT_FILE \"A3_ML_EA_HANDOFF.csv\"\n", encoding="utf-8")
    (presets / "A3MlPredictionObserver.passive_xauusd.set").write_text(
        "InpDryRunOnly=true\nInpTargetSymbol=XAUUSD\nInpAllowedAccountLoginsCsv=1025742,1033030,1033669\n",
        encoding="utf-8",
    )
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(
        config / "mt5_accounts.yaml",
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
                "A1": _account("1025742", "A1", tmp_path / "A1"),
                "A2": _account("1033030", "A2", tmp_path / "A2"),
                "A3": _account("1033669", "A3", None if a3_data_root is None else tmp_path / "A3"),
            },
        },
    )


def _account(scope: str, label: str, data_root: Path | None) -> dict:
    files_root = data_root / "MQL5" / "Files" if data_root else Path(f"C:/{label}/MQL5/Files")
    return {
        "account_scope": scope,
        "account_label": label,
        "expected_login": scope,
        "terminal_exe": f"C:/{label}/terminal64.exe",
        "expected_data_path": str(data_root) if data_root else None,
        "portable": label != "A1",
        "role": "test",
        "symbol": "XAUUSD",
        "files_roots": [str(files_root)],
        "log_catalog": f"config/ml/log_catalog_{label.lower()}.yaml",
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
