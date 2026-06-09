from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_ea_improvement_week1_comparison import compute_metrics, load_actual_control_trades, write_report


def _write_actual(path: Path) -> None:
    rows = [
        {
            "entry_time": "2026-06-09 16:00:00",
            "exit_time": "2026-06-09 16:20:00",
            "candidate": "breakout_retest",
            "symbol": "XAUUSD",
            "direction": "BUY",
            "volume": "0.01",
            "entry_price": "4300.00",
            "exit_price": "4303.00",
            "sl": "4298.00",
            "state": "CLOSED",
            "profit_aed": "30.0",
            "magic": "920101",
            "duplicate_key": "2026-06-09 16:00|XAUUSD|BUY|0.01",
            "duplicate_role": "unique",
            "is_duplicate": "false",
        },
        {
            "entry_time": "2026-06-09 17:00:00",
            "exit_time": "2026-06-09 17:20:00",
            "candidate": "session_extreme_retest_v0",
            "symbol": "XAUUSD",
            "direction": "SELL",
            "volume": "0.01",
            "entry_price": "4310.00",
            "exit_price": "4312.00",
            "sl": "4311.00",
            "state": "CLOSED",
            "profit_aed": "-20.0",
            "magic": "920501",
            "duplicate_key": "2026-06-09 17:00|XAUUSD|SELL|0.01",
            "duplicate_role": "unique",
            "is_duplicate": "false",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_comparison_loads_controls_and_applies_sample_gate(tmp_path: Path) -> None:
    actual = tmp_path / "actual.csv"
    _write_actual(actual)

    trades = load_actual_control_trades(actual, measured_cost_r=0.15)
    metrics = {item.stream: item for item in compute_metrics(trades)}

    assert metrics["full_diluted_portfolio"].trades == 2
    assert metrics["breakout_retest_only"].trades == 1
    assert metrics["breakout_retest_only"].win_rate == 1.0
    assert metrics["breakout_retest_only"].verdict.startswith("CHECKPOINT_ONLY_SAMPLE_LT_150")


def test_comparison_report_contains_precommitted_logic(tmp_path: Path) -> None:
    actual = tmp_path / "actual.csv"
    _write_actual(actual)
    metrics = compute_metrics(load_actual_control_trades(actual, measured_cost_r=0.15))
    output = tmp_path / "report.md"

    write_report(metrics, output, "2026_06_09")

    text = output.read_text(encoding="utf-8")
    assert "Primary KPI: net R after measured cost" in text
    assert "No promotion is possible before 150 fresh closed trades" in text
    assert "WideStop 1.2R" in text
    assert "| WideStop 1.2R | n/a | n/a | NO_DATA |" in text
