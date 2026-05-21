from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_would_signal_report_passes_when_permission_locked(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_decision_log(files_dir / "decision_log.csv")

    output = module.generate_phase1_would_signal_report(files_dir, tmp_path / "would.md")

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PASS"
    assert output.signal_count == 2
    assert output.cluster_count == 2
    assert output.csv_path.exists()
    assert "Would-Signal Rows" in report
    assert "Setup Clusters" in report
    assert "previous_weekly_low" in report
    with output.csv_path.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 2
    assert {row["cluster_id"] for row in csv_rows} == {"WS001", "WS002"}
    assert any(check.name == "would_signal_permission_lock" and check.status == "PASS" for check in output.checks)


def test_would_signal_report_warns_when_no_signal_rows(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_decision_log(files_dir / "decision_log.csv", include_signals=False)

    output = module.generate_phase1_would_signal_report(files_dir, tmp_path / "would.md")

    assert output.status == "WARN"
    assert output.signal_count == 0
    assert output.cluster_count == 0
    assert output.csv_path.exists()
    assert any(check.name == "would_signal_rows" and check.status == "WARN" for check in output.checks)


def test_would_signal_report_fails_when_permission_not_locked(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_decision_log(files_dir / "decision_log.csv", force_permission="true")

    output = module.generate_phase1_would_signal_report(files_dir, tmp_path / "would.md")

    assert output.status == "FAIL"
    assert any(check.name == "would_signal_permission_lock" and check.status == "FAIL" for check in output.checks)


def _load_module():
    path = ROOT / "scripts" / "generate_phase1_would_signal_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase1_would_signal_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase1_would_signal_report"] = module
    spec.loader.exec_module(module)
    return module


def _write_decision_log(path: Path, include_signals: bool = True, force_permission: str = "false") -> None:
    fieldnames = [
        "timestamp_broker",
        "bar_time",
        "run_id",
        "lifecycle_state",
        "symbol",
        "spread_points",
        "risk_state",
        "execution_state",
        "br_stage",
        "br_direction",
        "br_would_signal",
        "br_level_kind",
        "br_level_price",
        "br_entry_price",
        "br_stop_loss",
        "br_take_profit",
        "trade_permission",
        "dry_run",
    ]
    rows = [
        _row("2026.05.21 12:00:00", "WAIT_LEVEL_BREAK_RETEST", "SHORT", "false", "previous_weekly_low", "false"),
    ]
    if include_signals:
        rows.append(_row("2026.05.21 12:05:00", "WOULD_SIGNAL", "SHORT", "true", "previous_weekly_low", force_permission))
        rows.append(_row("2026.05.21 12:10:00", "WOULD_SIGNAL", "LONG", "true", "latest_swing_high", "false"))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _row(
    timestamp: str,
    stage: str,
    direction: str,
    would_signal: str,
    level_kind: str,
    permission: str,
) -> dict[str, str]:
    return {
        "timestamp_broker": timestamp,
        "bar_time": timestamp,
        "run_id": "phase1-dry-run-v0.5",
        "lifecycle_state": "DRY_RUN",
        "symbol": "XAUUSD",
        "spread_points": "50.00",
        "risk_state": "NORMAL",
        "execution_state": "EXECUTION_OK",
        "br_stage": stage,
        "br_direction": direction,
        "br_would_signal": would_signal,
        "br_level_kind": level_kind,
        "br_level_price": "4511.36",
        "br_entry_price": "4510.00",
        "br_stop_loss": "4512.00",
        "br_take_profit": "4507.00",
        "trade_permission": permission,
        "dry_run": "true",
    }
