from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c21_reports_launch_sent_without_observer_journal_evidence(tmp_path: Path) -> None:
    from ml.a3_meta_v1.runtime_launch_diagnostic import diagnose_runtime_launch

    root = _root_with_accounts(tmp_path, observer_mentions=False)

    output = diagnose_runtime_launch(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "LAUNCH_SENT_NO_OBSERVER_JOURNAL_EVIDENCE"
    assert payload["diagnostic_summary"]["startup_configs_safe_all_accounts"] is True
    assert payload["diagnostic_summary"]["observer_log_mentions_any_account"] is False
    assert payload["authorization"]["python_demo_predictions_authorized"] is False


def test_c21_reports_partial_journal_evidence(tmp_path: Path) -> None:
    from ml.a3_meta_v1.runtime_launch_diagnostic import diagnose_runtime_launch

    root = _root_with_accounts(tmp_path, observer_mentions=True)

    output = diagnose_runtime_launch(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "LAUNCH_SENT_WITH_PARTIAL_JOURNAL_EVIDENCE"
    assert payload["diagnostic_summary"]["observer_log_mentions_any_account"] is True


def test_c21_blocks_unsafe_startup_config(tmp_path: Path) -> None:
    from ml.a3_meta_v1.runtime_launch_diagnostic import diagnose_runtime_launch

    root = _root_with_accounts(tmp_path, observer_mentions=False)
    (tmp_path / "A2" / "Config" / "a3_ml_prediction_observer_startup.ini").write_text(
        "AllowLiveTrading=1\nExpert=A3MlPredictionObserver\n",
        encoding="utf-8",
    )

    output = diagnose_runtime_launch(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert any(item["check"] == "A2_startup_config_safe_passive" and not item["passed"] for item in payload["validations"])


def test_c21_script_loads() -> None:
    module = load_script("c21_diagnose_runtime_launch")

    assert hasattr(module, "main")


def _root_with_accounts(tmp_path: Path, *, observer_mentions: bool) -> Path:
    root = tmp_path / "phase1"
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(
        reports / "A3_ML_OBSERVER_RUNTIME_ATTACH_STATUS.json",
        {"status": "LAUNCH_SENT_WAITING_FOR_LOGS", "authorization": {"runtime_launch_attempted": True}},
    )
    _write_json(reports / "A3_ML_RUNTIME_EVIDENCE_STATUS.json", {"status": "WAITING_FOR_MT5_RUNTIME_LOGS"})
    for label in ("A1", "A2", "A3"):
        data_root = tmp_path / label
        (data_root / "Config").mkdir(parents=True)
        (data_root / "Logs").mkdir(parents=True)
        (data_root / "MQL5" / "Logs").mkdir(parents=True)
        (data_root / "Config" / "a3_ml_prediction_observer_startup.ini").write_text(
            "\n".join(
                [
                    "AllowLiveTrading=0",
                    "Expert=A3MlPredictionObserver",
                    "ExpertParameters=A3MlPredictionObserver.passive_xauusd.set",
                    "Symbol=XAUUSD",
                    "Period=M5",
                ]
            ),
            encoding="utf-8",
        )
        log_line = "A3MlPredictionObserver started" if observer_mentions and label == "A1" else "ordinary terminal line"
        (data_root / "Logs" / "20260621.log").write_text(log_line + "\n", encoding="utf-8")
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
