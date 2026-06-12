from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_impulse_veto_blocks_weak_family_counter_impulse_only(tmp_path: Path):
    module = _load_module()
    reports = tmp_path / "outputs" / "reports"
    trades = reports / "actual.csv"
    bars_dir = reports / "m5_replay_bars"
    output_json = reports / "impulse.json"
    _write_trades(trades)
    _write_uptrend_bars(bars_dir / "XAUUSD_M5_20260601_to_latest.csv")

    output = module.generate_phase2_impulse_veto_shadow_report(
        tmp_path,
        actual_trades_csv=trades,
        bars_dir=bars_dir,
        output_json=output_json,
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(output.rows_csv_path.open("r", encoding="utf-8", newline="")))
    by_ticket = {row["position_ticket"]: row for row in rows}

    assert output.status == "SHADOW_READY"
    assert payload["row_counts"]["resolved_closed_rows"] == 3
    assert by_ticket["1"]["impulse_bucket"] == "hard_against_lt_-1_5"
    assert by_ticket["1"]["lt_neg_1_5_shadow_action"] == "BLOCK"
    assert by_ticket["2"]["family"] == "breakout_retest_family"
    assert by_ticket["2"]["impulse_bucket"] == "hard_against_lt_-1_5"
    assert by_ticket["2"]["lt_neg_1_5_shadow_action"] == "KEEP"
    assert by_ticket["3"]["impulse_bucket"] == "extended_with_gt_1_5"
    assert by_ticket["3"]["lt_neg_1_5_shadow_action"] == "KEEP"

    threshold = next(row for row in payload["threshold_scoreboard"] if row["threshold"] == -1.5)
    assert threshold["baseline"]["closed"] == 2
    assert threshold["blocked"]["closed"] == 1
    assert threshold["kept"]["closed"] == 1
    assert threshold["shadow_net_delta_aed"] == "10.0000"

    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert "Shadow-only analysis" in markdown
    assert "breakout_retest_family" in markdown


def test_impulse_veto_report_has_no_runtime_mt5_dependency():
    script = ROOT / "scripts" / "generate_phase2_impulse_veto_shadow_report.py"
    text = script.read_text(encoding="utf-8")

    for forbidden in ("MetaTrader5", "mt5.initialize", "history_deals_get", "positions_get", "orders_get"):
        assert forbidden not in text


def _write_trades(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "entry_time",
        "exit_time",
        "candidate",
        "status",
        "symbol",
        "direction",
        "volume",
        "state",
        "profit_aed",
        "position_ticket",
        "is_duplicate",
        "time_bucket",
    ]
    rows = [
        _trade("2026-06-01 02:00:01", "round_number_retest_v0", "SELL", -10.0, "1"),
        _trade("2026-06-01 02:00:01", "breakout_retest", "SELL", 20.0, "2"),
        _trade("2026-06-01 02:05:01", "session_extreme_retest_v0", "BUY", 12.0, "3"),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _trade(entry_time: str, candidate: str, direction: str, pnl: float, ticket: str) -> dict[str, str]:
    return {
        "entry_time": entry_time,
        "exit_time": entry_time,
        "candidate": candidate,
        "status": "PROVISIONAL",
        "symbol": "XAUUSD",
        "direction": direction,
        "volume": "0.01",
        "state": "CLOSED",
        "profit_aed": str(pnl),
        "position_ticket": ticket,
        "is_duplicate": "false",
        "time_bucket": "Night 20:00-05:59",
    }


def _write_uptrend_bars(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "bar_start_utc",
        "bar_end_utc",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
        "real_volume",
        "symbol",
        "timeframe",
        "source_terminal",
    ]
    start = datetime(2026, 6, 1, 0, 0, 0)
    rows = []
    for index in range(40):
        bar_start = start + timedelta(minutes=5 * index)
        close = 100.0 + index
        rows.append(
            {
                "bar_start_utc": bar_start.strftime("%Y-%m-%d %H:%M:%S"),
                "bar_end_utc": (bar_start + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                "open": f"{close - 0.2:.2f}",
                "high": f"{close + 0.5:.2f}",
                "low": f"{close - 0.5:.2f}",
                "close": f"{close:.2f}",
                "tick_volume": "100",
                "spread": "50",
                "real_volume": "0",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "source_terminal": "test",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_module():
    path = ROOT / "scripts" / "generate_phase2_impulse_veto_shadow_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_impulse_veto_shadow_report", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_impulse_veto_shadow_report"] = module
    spec.loader.exec_module(module)
    return module
