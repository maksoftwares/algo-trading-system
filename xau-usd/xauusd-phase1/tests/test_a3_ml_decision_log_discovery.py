from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c12_finds_uncataloged_compatible_logs(tmp_path: Path) -> None:
    from ml.a3_meta_v1.decision_log_discovery import generate_decision_log_discovery_report

    root = tmp_path / "phase1"
    files_root = tmp_path / "A1" / "MQL5" / "Files"
    files_root.mkdir(parents=True)
    _write_registry(root / "config" / "ml" / "mt5_accounts.yaml", files_root)
    _write_catalog(root / "config" / "ml" / "log_catalog_a1.yaml", "cataloged_signal.csv")
    _write_catalog(root / "config" / "ml" / "log_catalog_a2.yaml", "none.csv")
    _write_catalog(root / "config" / "ml" / "log_catalog_a3.yaml", "none.csv")
    _write_signal(files_root / "uncataloged_breakout_signal.csv", "2026.06.01 12:00:00")
    _write_signal(files_root / "cataloged_signal.csv", "2026.06.09 12:00:00")
    (root / "outputs" / "reports").mkdir(parents=True)
    (root / "outputs" / "reports" / "C02_DATASET_POINTER.json").write_text("{}", encoding="utf-8")

    output = generate_decision_log_discovery_report(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "UNCATALOGED_COMPATIBLE_LOGS_FOUND"
    assert payload["summary"]["uncataloged_compatible_signal_logs"] == 1
    assert payload["recommended_catalog_additions"][0]["filename"] == "uncataloged_breakout_signal.csv"


def test_c12_script_loads() -> None:
    module = load_script("c12_discover_decision_logs")

    assert hasattr(module, "main")


def _write_signal(path: Path, timestamp: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp_utc", "symbol", "candidate", "would_signal"])
        writer.writeheader()
        writer.writerow({"timestamp_utc": timestamp, "symbol": "XAUUSD", "candidate": "breakout_retest", "would_signal": "true"})


def _write_catalog(path: Path, filename: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "c02_log_catalog_v1",
                "account_label": path.stem[-2:].upper(),
                "entries": [{"logical_source_name": filename, "source_type": "observer_signal_log", "filename": filename}],
            }
        ),
        encoding="utf-8",
    )


def _write_registry(path: Path, files_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
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
            "A1": _account("1025742", "A1", files_root),
            "A2": _account("1033030", "A2", tmp_files(files_root, "A2")),
            "A3": _account("1033669", "A3", tmp_files(files_root, "A3")),
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def tmp_files(files_root: Path, label: str) -> Path:
    path = files_root.parent.parent.parent / label / "MQL5" / "Files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _account(scope: str, label: str, files_root: Path) -> dict:
    return {
        "account_scope": scope,
        "account_label": label,
        "expected_login": scope,
        "terminal_exe": f"C:/{label}/terminal64.exe",
        "expected_data_path": f"C:/{label}",
        "portable": label != "A1",
        "role": "test",
        "symbol": "XAUUSD",
        "files_roots": [str(files_root)],
        "log_catalog": f"config/ml/log_catalog_{label.lower()}.yaml",
    }
