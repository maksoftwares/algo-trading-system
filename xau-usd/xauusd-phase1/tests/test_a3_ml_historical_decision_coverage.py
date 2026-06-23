from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c39_reports_no_older_compatible_decisions(tmp_path: Path) -> None:
    from ml.a3_meta_v1.historical_decision_coverage import generate_historical_decision_coverage_report

    root = _root_with_accounts(tmp_path, first_decision="2026-05-29T09:39:56Z")
    _write_signal_csv(tmp_path / "A1" / "MQL5" / "Files" / "a1_breakout_signal_log.csv", "breakout_retest", "2026-06-01 10:00:00")

    output = generate_historical_decision_coverage_report(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "NO_OLDER_COMPATIBLE_DECISIONS_FOUND"
    assert payload["summary"]["older_compatible_current_scope_would_signal_rows"] == 0
    assert pointer["c39_historical_decision_coverage_status"] == "NO_OLDER_COMPATIBLE_DECISIONS_FOUND"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c39_reports_older_compatible_current_scope_decisions(tmp_path: Path) -> None:
    from ml.a3_meta_v1.historical_decision_coverage import generate_historical_decision_coverage_report

    root = _root_with_accounts(tmp_path, first_decision="2026-05-29T09:39:56Z")
    _write_signal_csv(tmp_path / "A2" / "MQL5" / "Files" / "a2_breakout_retest_signal_log.csv", "breakout_retest", "2026-05-20 10:00:00")

    output = generate_historical_decision_coverage_report(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "OLDER_COMPATIBLE_DECISIONS_FOUND"
    assert payload["summary"]["older_compatible_current_scope_would_signal_rows"] == 1
    assert payload["older_compatible_records"][0]["filename"] == "a2_breakout_retest_signal_log.csv"
    assert payload["authorization"]["older_decision_import_authorized"] is False


def test_c39_reports_older_only_out_of_scope_decisions(tmp_path: Path) -> None:
    from ml.a3_meta_v1.historical_decision_coverage import generate_historical_decision_coverage_report

    root = _root_with_accounts(tmp_path, first_decision="2026-05-29T09:39:56Z")
    _write_signal_csv(
        tmp_path / "A3" / "MQL5" / "Files" / "a3_round_number_retest_signal_log.csv",
        "round_number_retest",
        "2026-05-20 10:00:00",
    )

    output = generate_historical_decision_coverage_report(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "OLDER_ONLY_OUT_OF_SCOPE_DECISIONS_FOUND"
    assert payload["summary"]["older_compatible_current_scope_would_signal_rows"] == 0
    assert payload["summary"]["older_out_of_scope_would_signal_rows"] == 1
    assert payload["authorization"]["training_authorized"] is False


def test_c39_script_loads() -> None:
    module = load_script("c39_probe_historical_decision_coverage")

    assert hasattr(module, "main")


def _root_with_accounts(tmp_path: Path, *, first_decision: str) -> Path:
    root = tmp_path / "phase1"
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {"dataset_version": "DATASET_A", "c02_labeled_decisions_csv": str(reports / "C02_LABELED_DECISIONS.csv")},
    )
    _write_json(
        reports / "A3_ML_READINESS_GAP_REPORT.json",
        {"decision_coverage": {"min_decision_utc": first_decision}},
    )
    for label in ("A1", "A2", "A3"):
        files = tmp_path / label / "MQL5" / "Files"
        files.mkdir(parents=True)
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
