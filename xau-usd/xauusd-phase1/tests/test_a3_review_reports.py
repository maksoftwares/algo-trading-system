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


def _load_module():
    path = ROOT / "scripts" / "generate_a3_review_reports.py"
    spec = importlib.util.spec_from_file_location("generate_a3_review_reports", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_a3_review_reports"] = module
    spec.loader.exec_module(module)
    return module
