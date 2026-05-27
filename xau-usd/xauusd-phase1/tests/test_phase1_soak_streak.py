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


def test_same_run_id_continuous_bars_accumulate_active_streak():
    module = _load_module()
    rows = [
        _row("2026.05.21 12:00:00", run_id="phase1-a"),
        _row("2026.05.21 12:05:00", run_id="phase1-a"),
        _row("2026.05.21 12:10:00", run_id="phase1-a"),
        _row("2026.05.21 12:15:00", run_id="phase1-a"),
    ]

    summary = module.calculate_soak_streak(
        rows,
        now=datetime(2026, 5, 21, 12, 20),
    )

    assert summary.current_streak_hours == 0.25
    assert summary.restart_count_during_current_streak == 0
    assert summary.current_streak_bar_count == 4


def test_run_id_change_resets_active_market_streak_even_without_bar_gap():
    module = _load_module()
    rows = [
        _row("2026.05.21 12:00:00", run_id="phase1-a"),
        _row("2026.05.21 12:05:00", run_id="phase1-a"),
        _row("2026.05.21 12:10:00", run_id="phase1-b"),
        _row("2026.05.21 12:15:00", run_id="phase1-b"),
    ]

    summary = module.calculate_soak_streak(
        rows,
        now=datetime(2026, 5, 21, 12, 20),
    )

    assert summary.current_streak_hours == 0.08
    assert summary.restart_count_during_current_streak == 0
    assert summary.current_streak_bar_count == 2


def test_active_market_gap_over_threshold_resets_streak():
    module = _load_module()
    rows = [
        _row("2026.05.21 12:00:00"),
        _row("2026.05.21 12:05:00"),
        _row("2026.05.21 12:25:00"),
        _row("2026.05.21 12:30:00"),
    ]

    summary = module.calculate_soak_streak(
        rows,
        max_bar_gap_minutes=15.0,
        now=datetime(2026, 5, 21, 12, 35),
    )

    assert summary.current_streak_hours == 0.08
    assert summary.current_streak_bar_count == 2


def test_bad_safety_row_resets_active_market_streak():
    module = _load_module()
    rows = [
        _row("2026.05.21 12:00:00"),
        _row("2026.05.21 12:05:00"),
        _row("2026.05.21 12:10:00", trade_permission="true"),
        _row("2026.05.21 12:15:00"),
    ]

    summary = module.calculate_soak_streak(
        rows,
        now=datetime(2026, 5, 21, 12, 20),
    )

    assert summary.current_streak_hours == 0.0
    assert summary.current_streak_bar_count == 0


def test_bad_server_time_resets_active_market_streak():
    module = _load_module()
    rows = [
        _row("2026.05.21 12:00:00"),
        _row("2026.05.21 12:05:00", server_time_status="CLOCK_DRIFT"),
        _row("2026.05.21 12:10:00"),
        _row("2026.05.21 12:15:00"),
    ]

    summary = module.calculate_soak_streak(
        rows,
        now=datetime(2026, 5, 21, 12, 20),
    )

    assert summary.current_streak_hours == 0.08
    assert summary.current_streak_bar_count == 2


def test_process_uptime_uses_timestamp_utc():
    module = _load_module()
    row = _row("2026.05.21 12:00:00")
    row["timestamp_utc"] = "2026.05.21 08:00:00"
    row["timestamp_local"] = "2026.05.21 20:00:00"

    summary = module.calculate_soak_streak(
        [row],
        now=datetime(2026, 5, 21, 10, 0),
    )

    assert summary.process_uptime_streak_hours == 2.0


def test_code_freeze_marker_reader_ignores_utf8_bom(tmp_path: Path):
    module = _load_module()
    marker = tmp_path / "phase1_code_freeze_started_at.txt"
    marker.write_text("\ufeff2026-05-27T10:41:50Z\n", encoding="utf-8")

    assert module.read_code_freeze_marker(marker) == "2026-05-27T10:41:50Z"


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
    run_id: str = "phase1-dry-run-v0.7",
    trade_permission: str = "false",
    server_time_status: str = "CLOCK_OK",
) -> dict[str, str]:
    return {
        "timestamp_local": bar_time,
        "timestamp_utc": bar_time,
        "run_id": run_id,
        "lifecycle_state": "DRY_RUN",
        "bar_time": bar_time,
        "session": session,
        "execution_state": execution_state,
        "trade_permission": trade_permission,
        "dry_run": "true",
        "server_time_status": server_time_status,
        "magic_namespace_ok": "true",
    }
