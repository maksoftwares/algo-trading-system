from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PHASE1_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from analyze_a1_momentum_daily_state_guard_search import apply_state_guard  # noqa: E402


def trade(name: str, entry: str, exit_: str, profit: float) -> dict[str, object]:
    entry_time = datetime.strptime(entry, "%Y.%m.%d %H:%M:%S")
    exit_time = datetime.strptime(exit_, "%Y.%m.%d %H:%M:%S")
    return {
        "variant": name,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "entry_date": entry_time.date().isoformat(),
        "entry_hour": entry_time.hour,
        "entry_session": "test",
        "direction": "LONG",
        "profit": profit,
    }


def run_guard(rows: list[dict[str, object]], *, target: float | None = None, cooldown: int = 0) -> list[str]:
    kept, stats = apply_state_guard(
        rows,
        state_rule="none",
        profit_target_usd=target,
        loss_stop_usd=None,
        max_trades_per_day=None,
        max_losses_per_day=None,
        cooldown_after_loss_minutes=cooldown,
        early_trade_count=2,
        early_pnl_threshold=0.0,
    )
    assert stats["guard_model"] == "event_time_causal_v2"
    return [str(row["variant"]) for row in kept]


def test_loss_cooldown_starts_after_exit_not_entry() -> None:
    rows = [
        trade("loss_closes_later", "2026.07.01 09:00:00", "2026.07.01 10:00:00", -10.0),
        trade("entered_before_loss_known", "2026.07.01 09:30:00", "2026.07.01 09:45:00", 5.0),
        trade("entered_after_loss_cooldown", "2026.07.01 10:05:00", "2026.07.01 10:20:00", 5.0),
    ]

    assert run_guard(rows, cooldown=10) == ["loss_closes_later", "entered_before_loss_known"]


def test_profit_target_starts_after_exit_not_entry() -> None:
    rows = [
        trade("winner_closes_later", "2026.07.01 09:00:00", "2026.07.01 10:00:00", 100.0),
        trade("entered_before_target_known", "2026.07.01 09:30:00", "2026.07.01 09:45:00", -5.0),
        trade("entered_after_target_known", "2026.07.01 10:05:00", "2026.07.01 10:20:00", 5.0),
    ]

    assert run_guard(rows, target=75.0) == ["winner_closes_later", "entered_before_target_known"]
