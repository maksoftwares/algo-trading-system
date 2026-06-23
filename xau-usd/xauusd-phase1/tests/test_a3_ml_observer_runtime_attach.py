from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c14_preflight_writes_safe_startup_configs(tmp_path: Path) -> None:
    from ml.a3_meta_v1.observer_runtime_attach import launch_prediction_observer_runtime

    root = _root_with_runtime_targets(tmp_path)

    output = launch_prediction_observer_runtime(root, launch=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_READY"
    assert payload["authorization"]["runtime_launch_attempted"] is False
    assert payload["boundary"]["startup_config_write_attempted"] is True
    assert payload["boundary"]["allow_live_trading_in_startup_config"] is False
    assert len(payload["outputs"]["configs_written"]) == 3
    for item in payload["outputs"]["configs_written"]:
        text = Path(item["path"]).read_text(encoding="utf-8")
        assert "Expert=A3MlPredictionObserver" in text
        assert "ExpertParameters=A3MlPredictionObserver.passive_xauusd.set" in text
        assert "AllowLiveTrading=0" in text
        assert "Symbol=XAUUSD" in text
        assert "Period=M5" in text


def test_c14_detects_existing_runtime_logs_without_launch(tmp_path: Path) -> None:
    from ml.a3_meta_v1.observer_runtime_attach import launch_prediction_observer_runtime

    root = _root_with_runtime_targets(tmp_path)
    for files_root in tmp_path.glob("A*/MQL5/Files"):
        (files_root / "a3_ml_prediction_observer_startup.csv").write_text("startup\n", encoding="utf-8")
        (files_root / "a3_ml_prediction_observer_log.csv").write_text("log\n", encoding="utf-8")

    output = launch_prediction_observer_runtime(root, launch=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_READY"
    assert all(item["startup_log_exists"] for item in payload["outputs"]["logs"])
    assert all(item["prediction_log_exists"] for item in payload["outputs"]["logs"])


def test_c14_blocks_missing_handoff_file(tmp_path: Path) -> None:
    from ml.a3_meta_v1.observer_runtime_attach import launch_prediction_observer_runtime

    root = _root_with_runtime_targets(tmp_path)
    (tmp_path / "A2" / "MQL5" / "Files" / "A3_ML_EA_HANDOFF.csv").unlink()

    output = launch_prediction_observer_runtime(root, launch=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert any(item["check"] == "A2_handoff_file_exists" and not item["passed"] for item in payload["validations"])


def test_c14_script_loads() -> None:
    module = load_script("c14_launch_prediction_observer_runtime")

    assert hasattr(module, "main")


def _root_with_runtime_targets(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    for label in ("A1", "A2", "A3"):
        data_root = tmp_path / label
        (data_root / "Config").mkdir(parents=True)
        (data_root / "MQL5" / "Experts").mkdir(parents=True)
        (data_root / "MQL5" / "Presets").mkdir(parents=True)
        (data_root / "MQL5" / "Files").mkdir(parents=True)
        (data_root / "terminal64.exe").write_text("terminal\n", encoding="utf-8")
        (data_root / "MQL5" / "Experts" / "A3MlPredictionObserver.ex5").write_text("compiled\n", encoding="utf-8")
        (data_root / "MQL5" / "Presets" / "A3MlPredictionObserver.passive_xauusd.set").write_text(
            "InpDryRunOnly=true\n",
            encoding="utf-8",
        )
        (data_root / "MQL5" / "Files" / "A3_ML_EA_HANDOFF.csv").write_text("schema_version\n", encoding="utf-8")
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
