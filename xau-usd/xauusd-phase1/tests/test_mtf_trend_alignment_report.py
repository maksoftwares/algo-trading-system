from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mtf_trend_alignment_tags_with_and_against_trend(tmp_path: Path):
    module = _load_module()
    actual_trades = tmp_path / "outputs" / "reports" / "PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv"
    bars_dir = tmp_path / "outputs" / "reports" / "m5_replay_bars"
    output_doc = tmp_path / "docs" / "MULTI_TIMEFRAME_TREND_ALIGNMENT_REPORT_2026_06_13.md"
    output_json = tmp_path / "outputs" / "reports" / "MULTI_TIMEFRAME_TREND_ALIGNMENT_REPORT_2026_06_13.json"
    _write_actual_trades(actual_trades)
    _write_bars(bars_dir, "H1", hours=1, rows=110)
    _write_bars(bars_dir, "H4", hours=4, rows=35)

    output = module.generate_mtf_trend_alignment_report(
        tmp_path,
        actual_trades_csv=actual_trades,
        bars_dir=bars_dir,
        output_doc=output_doc,
        output_json=output_json,
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    alignments = {
        (row["timeframe"], row["trend_alignment"]): row
        for row in payload["overall_by_timeframe_alignment"]
    }
    markdown = output.markdown_path.read_text(encoding="utf-8")

    assert output.status == "TREND_ALIGNMENT_READY"
    assert output.closed_kept_rows == 2
    assert output.resolved_tags == 4
    assert ("H1", "WITH_TREND") in alignments
    assert ("H1", "AGAINST_TREND") in alignments
    assert "latest completed bar at entry time" in markdown
    assert "No EA code change is implied" in markdown


def test_mtf_trend_alignment_has_no_runtime_mt5_calls():
    text = (ROOT / "scripts" / "generate_mtf_trend_alignment_report.py").read_text(encoding="utf-8")
    for forbidden in ("MetaTrader5", "mt5.initialize", "OrderSend", "PositionClose"):
        assert forbidden not in text


def _write_actual_trades(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        _trade("2026-06-05 12:30:00", "symbol_normalized_round_retest_v0", "XAUUSD", "BUY", 10.0, "1"),
        _trade("2026-06-05 12:35:00", "session_extreme_retest_v0", "XAUUSD", "SELL", -5.0, "2"),
        _trade(
            "2026-06-05 12:40:00",
            "round_number_retest_v0",
            "XAUUSD",
            "BUY",
            1.0,
            "3",
            duplicate=True,
        ),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_bars(path: Path, timeframe: str, *, hours: int, rows: int) -> None:
    path.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 6, 1, 0, 0, 0)
    output_rows = []
    for index in range(rows):
        bar_start = start + timedelta(hours=hours * index)
        bar_end = bar_start + timedelta(hours=hours)
        close = 100.0 + index
        output_rows.append(
            {
                "bar_start_utc": bar_start.strftime("%Y-%m-%d %H:%M:%S"),
                "bar_end_utc": bar_end.strftime("%Y-%m-%d %H:%M:%S"),
                "close": f"{close:.2f}",
                "symbol": "XAUUSD",
                "timeframe": timeframe,
            }
        )
    with (path / f"XAUUSD_{timeframe}_20260601_to_latest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)


def _trade(
    entry_time: str,
    candidate: str,
    symbol: str,
    direction: str,
    pnl: float,
    ticket: str,
    *,
    duplicate: bool = False,
) -> dict[str, str]:
    return {
        "entry_time": entry_time,
        "exit_time": entry_time,
        "candidate": candidate,
        "status": "ACCEPTED",
        "symbol": symbol,
        "direction": direction,
        "volume": "0.01",
        "entry_price": "100.0",
        "exit_price": "101.0",
        "sl": "99.0",
        "tp": "102.0",
        "state": "CLOSED",
        "profit_aed": str(pnl),
        "position_ticket": ticket,
        "duplicate_key": ticket,
        "duplicate_role": "duplicate" if duplicate else "unique",
        "is_duplicate": "true" if duplicate else "false",
    }


def _load_module():
    path = ROOT / "scripts" / "generate_mtf_trend_alignment_report.py"
    spec = importlib.util.spec_from_file_location("generate_mtf_trend_alignment_report", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_mtf_trend_alignment_report"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
