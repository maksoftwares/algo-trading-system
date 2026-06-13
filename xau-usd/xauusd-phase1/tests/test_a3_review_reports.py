from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_a3_review_reports_include_evening_pnl_line(tmp_path: Path):
    module = _load_module()
    trades = tmp_path / "trades.csv"
    _write_trades(trades)

    output = module.generate_a3_review_reports(
        tmp_path,
        trades_csv=trades,
        report_date="2026_06_13",
        output_dir=tmp_path / "reports",
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    weekly = output.weekly_markdown.read_text(encoding="utf-8")
    daily = output.daily_markdown.read_text(encoding="utf-8")

    assert payload["evening_session_pnl"]["total_pnl_aed"] == -15.0
    assert "Evening session PnL (16:00-19:59 Dubai): -15.00 AED, status: closed for the day" in weekly
    assert "Evening session PnL (16:00-19:59 Dubai): -15.00 AED, status: closed for the day" in daily


def test_a3_review_reports_summarize_evening_standdown_shadow(tmp_path: Path):
    module = _load_module()
    trades = tmp_path / "trades.csv"
    _write_standdown_trades(trades)

    output = module.generate_a3_review_reports(
        tmp_path,
        trades_csv=trades,
        report_date="2026_06_13",
        output_dir=tmp_path / "reports",
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    shadow = payload["T10_evening_standdown_shadow"]

    assert shadow["reason_code"] == "EVENING_STANDDOWN_WOULD_FIRE"
    assert shadow["would_fire"] is True
    assert shadow["trigger_time"] == "2026-06-13 16:20:00"
    assert shadow["post_trigger_closed_rows"] == 1
    assert shadow["post_trigger_realized_pnl_aed"] == 40.0
    assert "EVENING_STANDDOWN_WOULD_FIRE would fire" in output.daily_markdown.read_text(encoding="utf-8")


def test_a3_review_reports_include_confluence_breakdown(tmp_path: Path):
    module = _load_module()
    trades = tmp_path / "trades.csv"
    reports = tmp_path / "reports"
    _write_trades(trades)
    _write_signal_log(reports / "a3_rdguard_v1_signal_log.csv")

    output = module.generate_a3_review_reports(
        tmp_path,
        trades_csv=trades,
        report_date="2026_06_13",
        output_dir=reports,
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    weekly = output.weekly_markdown.read_text(encoding="utf-8")

    assert payload["confluence_breakdown"] == [
        {"confluence_count": "1", "rows": 1, "families_examples": "ROUND"},
        {"confluence_count": "2", "rows": 1, "families_examples": "BREAKOUT;ROUND"},
    ]
    assert "Confluence Breakdown" in weekly
    assert "| 2 | 1 | BREAKOUT;ROUND |" in weekly


def _write_trades(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["entry_time", "candidate", "symbol", "state", "profit_aed", "magic", "time_bucket"]
    rows = [
        {"entry_time": "2026-06-13 16:10:00", "candidate": "breakout_retest", "symbol": "XAUUSD", "state": "CLOSED", "profit_aed": "-20", "magic": "920101", "time_bucket": "Evening 16:00-19:59"},
        {"entry_time": "2026-06-13 17:10:00", "candidate": "a3_round_retest_guarded_v1", "symbol": "XAUUSD", "state": "CLOSED", "profit_aed": "5", "magic": "933000", "time_bucket": "Evening 16:00-19:59"},
        {"entry_time": "2026-06-13 10:10:00", "candidate": "breakout_retest", "symbol": "XAUUSD", "state": "CLOSED", "profit_aed": "100", "magic": "920101", "time_bucket": "Morning 06:00-11:59"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_standdown_trades(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["entry_time", "candidate", "symbol", "state", "profit_aed", "magic", "time_bucket"]
    rows = [
        {"entry_time": "2026-06-13 16:00:00", "candidate": "round", "symbol": "XAUUSD", "state": "CLOSED", "profit_aed": "-120", "magic": "920301", "time_bucket": "Evening 16:00-19:59"},
        {"entry_time": "2026-06-13 16:20:00", "candidate": "round", "symbol": "XAUUSD", "state": "CLOSED", "profit_aed": "-90", "magic": "920301", "time_bucket": "Evening 16:00-19:59"},
        {"entry_time": "2026-06-13 17:00:00", "candidate": "breakout", "symbol": "XAUUSD", "state": "CLOSED", "profit_aed": "40", "magic": "920101", "time_bucket": "Evening 16:00-19:59"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_signal_log(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["timestamp_utc", "confluence_families", "confluence_count"]
    rows = [
        {"timestamp_utc": "2026-06-13 16:00:00", "confluence_families": "ROUND", "confluence_count": "1"},
        {"timestamp_utc": "2026-06-13 16:05:00", "confluence_families": "BREAKOUT;ROUND", "confluence_count": "2"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_module():
    path = ROOT / "scripts" / "generate_a3_review_reports.py"
    spec = importlib.util.spec_from_file_location("generate_a3_review_reports", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_a3_review_reports"] = module
    spec.loader.exec_module(module)
    return module
