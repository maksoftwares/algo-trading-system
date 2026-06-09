from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repair_candidate_research_classifies_weak_ea_repairs(tmp_path: Path):
    module = _load_module()
    source_csv = tmp_path / "actual_trades.csv"
    output_json = tmp_path / "reports" / "repair.json"
    _write_actual_trades(source_csv)

    output = module.generate_repair_candidate_research(
        tmp_path,
        actual_trades_csv=source_csv,
        output_json=output_json,
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    reports = {report["candidate"]: report for report in payload["repair_candidates"]}
    rules = list(csv.DictReader(output.rules_csv_path.open("r", encoding="utf-8", newline="")))

    assert output.status == "REPAIR_RESEARCH_READY"
    assert output.candidate_count == 3
    assert reports["session_extreme_retest_v0"]["status"] == "REPAIR_CANDIDATE_FOR_OBSERVER_FORWARD_TEST"
    assert reports["symbol_normalized_round_retest_v0"]["status"] == "REPAIR_TOO_NARROW"
    assert reports["round_number_retest_v0"]["status"] == "DUPLICATE_ONLY_REBUILD_REQUIRED"
    assert reports["round_number_retest_v0"]["raw_summary"]["closed"] == 3
    assert reports["round_number_retest_v0"]["duplicate_hidden_summary"]["closed"] == 0
    assert reports["round_number_retest_v0"]["rules"][0]["rule_type"] == "DUPLICATE_ONLY_REBUILD"
    assert all(rule["runtime_action"] == "NONE_SHADOW_ONLY" for rule in rules)

    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert "Research only" in markdown
    assert "DUPLICATE_ONLY_REBUILD_REQUIRED" in markdown
    assert "Raw broker rows exist, but all are duplicate-hidden" in markdown


def test_repair_candidate_research_has_no_runtime_mt5_calls():
    script = ROOT / "scripts" / "generate_phase2_repair_candidate_research.py"
    text = script.read_text(encoding="utf-8")

    for forbidden in ("MetaTrader5", "mt5.initialize", "terminal64", "MetaQuotes"):
        assert forbidden not in text


def _write_actual_trades(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "entry_time",
        "exit_time",
        "candidate",
        "status",
        "symbol",
        "direction",
        "volume",
        "entry_price",
        "exit_price",
        "sl",
        "tp",
        "state",
        "profit_aed",
        "position_ticket",
        "is_duplicate",
    ]
    rows = []
    rows.extend(
        [
            _row("2026-06-08 21:00:00", "session_extreme_retest_v0", "XAUUSD", "SELL", -10, "1"),
            _row("2026-06-08 21:05:00", "session_extreme_retest_v0", "XAUUSD", "SELL", -10, "2"),
            _row("2026-06-08 21:10:00", "session_extreme_retest_v0", "XAUUSD", "SELL", -10, "3"),
            _row("2026-06-08 22:00:00", "session_extreme_retest_v0", "EURUSD", "SELL", 10, "4"),
            _row("2026-06-08 22:05:00", "session_extreme_retest_v0", "EURUSD", "SELL", 10, "5"),
            _row("2026-06-08 22:10:00", "session_extreme_retest_v0", "EURUSD", "SELL", 10, "6"),
        ]
    )
    for index in range(10):
        rows.append(
            _row(
                f"2026-06-08 09:{index:02d}:00",
                "symbol_normalized_round_retest_v0",
                "XAUUSD",
                "BUY",
                -10,
                str(100 + index),
            )
        )
    for index in range(4):
        rows.append(
            _row(
                f"2026-06-08 17:{index:02d}:00",
                "symbol_normalized_round_retest_v0",
                "XAUUSD",
                "SELL",
                20,
                str(200 + index),
            )
        )
    rows.extend(
        [
            _row("2026-06-08 18:00:00", "round_number_retest_v0", "XAUUSD", "BUY", -7, "301", is_duplicate=True),
            _row("2026-06-08 18:05:00", "round_number_retest_v0", "XAUUSD", "BUY", 5, "302", is_duplicate=True),
            _row("2026-06-08 18:10:00", "round_number_retest_v0", "XAUUSD", "BUY", -4, "303", is_duplicate=True),
        ]
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _row(
    entry_time: str,
    candidate: str,
    symbol: str,
    direction: str,
    pnl: float,
    ticket: str,
    *,
    is_duplicate: bool = False,
) -> dict[str, str]:
    return {
        "entry_time": entry_time,
        "exit_time": entry_time,
        "candidate": candidate,
        "status": "PROVISIONAL",
        "symbol": symbol,
        "direction": direction,
        "volume": "0.01",
        "entry_price": "100.00",
        "exit_price": "101.00",
        "sl": "99.00",
        "tp": "102.00",
        "state": "CLOSED",
        "profit_aed": str(pnl),
        "position_ticket": ticket,
        "is_duplicate": "true" if is_duplicate else "false",
    }


def _load_module():
    path = ROOT / "scripts" / "generate_phase2_repair_candidate_research.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_repair_candidate_research", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_repair_candidate_research"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
