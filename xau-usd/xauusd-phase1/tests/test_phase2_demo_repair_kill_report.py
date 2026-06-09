from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_phase2_demo_repair_kill_report import compute_repair_kill_metrics


def _row(candidate: str, profit: str, entry: str, exit_price: str, sl: str) -> dict[str, str]:
    return {
        "entry_time": "2026-06-09 16:00:00",
        "exit_time": "2026-06-09 16:20:00",
        "candidate": candidate,
        "symbol": "XAUUSD",
        "direction": "BUY",
        "entry_price": entry,
        "exit_price": exit_price,
        "sl": sl,
        "state": "CLOSED",
        "profit_aed": profit,
        "duplicate_role": "unique",
        "is_duplicate": "false",
    }


def test_repair_day_3_5_kill_rule_rejects_weak_repair() -> None:
    rows = [
        _row("symbol_normalized_round_retest_v0_repair_v1", "-10", "4300", "4299", "4298"),
        _row("breakout_retest", "40", "4300", "4303", "4298"),
    ]

    metrics = compute_repair_kill_metrics(rows, measured_cost_r=0.15, elapsed_days=3.5)

    assert metrics.repair_closed_trades == 1
    assert metrics.verdict == "REJECT_REPAIR_V1_DAY_3_5_KILL_RULE"
