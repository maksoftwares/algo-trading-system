from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c08_preflight_does_not_attempt_mt5(tmp_path: Path) -> None:
    from ml.a3_meta_v1.live_refresh_orchestrator import run_live_refresh_or_preflight

    root = tmp_path / "phase1"
    _write_minimal_root(root)

    output = run_live_refresh_or_preflight(root, execute_live_readonly=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_READY"
    assert payload["mode"] == "PREFLIGHT_ONLY"
    assert payload["boundary"]["mt5_connection_attempted"] is False
    assert payload["boundary"]["data_export_attempted"] is False
    assert payload["boundary"]["broker_action_authorized"] is False


def test_c08_preflight_blocks_missing_files_root(tmp_path: Path) -> None:
    from ml.a3_meta_v1.live_refresh_orchestrator import run_live_refresh_or_preflight

    root = tmp_path / "phase1"
    _write_minimal_root(root, a3_files_roots=[])

    output = run_live_refresh_or_preflight(root, execute_live_readonly=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert any(item["step"] == "all_accounts_have_files_roots" and item["status"] == "BLOCKED" for item in payload["steps"])


def test_c08_render_mentions_live_execution_boundary() -> None:
    from ml.a3_meta_v1.live_refresh_orchestrator import render_live_refresh_status_md

    report = render_live_refresh_status_md(
        {
            "status": "PREFLIGHT_READY",
            "mode": "PREFLIGHT_ONLY",
            "requested_start_utc": "2026-06-01T00:00:00Z",
            "publish_requested": False,
            "steps": [{"step": "registry_exists", "status": "PASS", "detail": "ok"}],
            "summary": {"c03": {"status": "NO_GO", "checks": []}},
            "boundary": {
                "mt5_connection_attempted": False,
                "data_export_attempted": False,
                "ea_file_drop_authorized": False,
            },
            "next_allowed_stage": "Run later.",
        }
    )

    assert "Overall status: PREFLIGHT_READY" in report
    assert "MT5 connection attempted: false." in report
    assert "Data export attempted: false." in report
    assert "Broker action authorized: false." in report


def test_c08_script_loads() -> None:
    module = load_script("c08_live_refresh_pipeline")

    assert hasattr(module, "main")


def _write_minimal_root(root: Path, *, a3_files_roots: list[str] | None = None) -> None:
    reports = root / "outputs" / "reports"
    scripts = root / "scripts"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    scripts.mkdir(parents=True)
    config.mkdir(parents=True)
    for script in (
        "c02_verify_mt5_accounts.py",
        "c02_export_mt5_market_data.py",
        "c02_snapshot_history_logs.py",
        "c07_run_ml_readiness_pipeline.py",
    ):
        (scripts / script).write_text("# test\n", encoding="utf-8")
    _write_json(reports / "C02_DATASET_POINTER.json", {"requested_start_utc": "2026-06-01T00:00:00Z"})
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", {"status": "NO_GO", "checks": []})
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
                "A1": _account("1025742", "A1", ["C:/A1/MQL5/Files"]),
                "A2": _account("1033030", "A2", ["C:/A2/MQL5/Files"]),
                "A3": _account("1033669", "A3", ["C:/A3/MQL5/Files"] if a3_files_roots is None else a3_files_roots),
            },
        },
    )


def _account(scope: str, label: str, files_roots: list[str]) -> dict:
    return {
        "account_scope": scope,
        "account_label": label,
        "expected_login": scope,
        "terminal_exe": f"C:/{label}/terminal64.exe",
        "expected_data_path": f"C:/{label}",
        "portable": label != "A1",
        "role": "test",
        "symbol": "XAUUSD",
        "files_roots": files_roots,
        "log_catalog": f"config/ml/log_catalog_{label.lower()}.yaml",
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
