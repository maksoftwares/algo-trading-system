from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c34_reports_out_of_scope_backfill_without_authorizing_import(tmp_path: Path) -> None:
    from ml.a3_meta_v1.decision_backfill_audit import generate_decision_backfill_audit

    root = _root_with_accounts(tmp_path)
    a1_files = tmp_path / "A1" / "MQL5" / "Files"
    _write_signal_csv(
        a1_files / "experimental_demo_executor_signal_log_round_number_retest_v0_xauusd.csv",
        "round_number_retest",
        "2026-05-20 10:00:00",
    )

    output = generate_decision_backfill_audit(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND"
    assert payload["summary"]["uncataloged_current_scope_files"] == 0
    assert payload["summary"]["out_of_scope_would_signal_rows"] == 1
    assert payload["authorization"]["training_authorized"] is False
    assert pointer["c34_decision_backfill_audit_status"] == "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c34_reports_uncataloged_current_scope_candidate(tmp_path: Path) -> None:
    from ml.a3_meta_v1.decision_backfill_audit import generate_decision_backfill_audit

    root = _root_with_accounts(tmp_path)
    a2_files = tmp_path / "A2" / "MQL5" / "Files"
    _write_signal_csv(
        a2_files / "new_breakout_retest_signal_log_xauusd.csv",
        "breakout_retest",
        "2026-05-20 10:00:00",
    )

    output = generate_decision_backfill_audit(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "CURRENT_SCOPE_UNCATALOGED_BACKFILL_FOUND"
    assert payload["summary"]["uncataloged_current_scope_files"] == 1
    assert payload["uncataloged_current_scope_candidates"][0]["filename"] == "new_breakout_retest_signal_log_xauusd.csv"
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c34_script_loads() -> None:
    module = load_script("c34_audit_decision_backfill_candidates")

    assert hasattr(module, "main")


def _root_with_accounts(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "DATASET_A"})
    for label in ("A1", "A2", "A3"):
        files = tmp_path / label / "MQL5" / "Files"
        files.mkdir(parents=True)
        _write_json(
            config / f"log_catalog_{label.lower()}.yaml",
            {
                "schema_version": "c02_log_catalog_v1",
                "account_label": label,
                "entries": [
                    {
                        "logical_source_name": f"{label.lower()}_cataloged_signal",
                        "source_type": "observer_signal_log",
                        "filename": f"{label.lower()}_cataloged_signal_log.csv",
                        "schema_version": "csv_runtime_log_v1",
                        "family": "breakout_retest",
                        "append_active": False,
                    }
                ],
            },
        )
        _write_signal_csv(files / f"{label.lower()}_cataloged_signal_log.csv", "breakout_retest", "2026-06-20 10:00:00")
    return root


def _write_signal_csv(path: Path, candidate: str, timestamp: str) -> None:
    path.write_text(
        "\n".join(
            [
                "timestamp_utc,symbol,candidate,direction,would_signal,level_price,entry_price",
                f"{timestamp},XAUUSD,{candidate},LONG,true,2410.50,2410.50",
                "",
            ]
        ),
        encoding="utf-8",
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
