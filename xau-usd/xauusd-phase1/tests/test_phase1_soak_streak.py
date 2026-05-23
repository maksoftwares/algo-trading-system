from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_weekend_and_stale_tick_rows_break_active_market_streak():
    module = _load_module()
    rows = [
        _row("2026.05.21 12:00:00"),
        _row("2026.05.21 12:05:00"),
        _row("2026.05.21 12:10:00", session="WEEKEND", execution_state="STALE_TICK"),
        _row("2026.05.21 12:15:00"),
    ]

    summary = module.calculate_soak_streak(
        rows,
        now=datetime(2026, 5, 21, 12, 20),
    )

    assert summary.weekend_policy == "weekend_breaks_active_market_streak"
    assert summary.longest_streak_hours == 0.08
    assert summary.current_streak_hours == 0.0
    assert summary.current_streak_bar_count == 0


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "phase1_soak_streak.py"
    spec = importlib.util.spec_from_file_location("phase1_soak_streak", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase1_soak_streak"] = module
    spec.loader.exec_module(module)
    return module


def _row(
    bar_time: str,
    session: str = "LONDON",
    execution_state: str = "EXECUTION_OK",
) -> dict[str, str]:
    return {
        "timestamp_local": bar_time,
        "timestamp_utc": bar_time,
        "run_id": "phase1-dry-run-v0.6",
        "lifecycle_state": "DRY_RUN",
        "bar_time": bar_time,
        "session": session,
        "execution_state": execution_state,
        "trade_permission": "false",
        "dry_run": "true",
        "server_time_status": "CLOCK_OK",
        "magic_namespace_ok": "true",
    }
