from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta
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

    assert summary.weekend_policy == "expected_market_breaks_pause_active_market_streak"
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


def test_thirteen_m5_bars_count_as_one_active_hour():
    module = _load_module()
    rows = _rows_at_cadence(datetime(2026, 5, 21, 12, 0), 13)

    summary = module.calculate_soak_streak(
        rows,
        now=datetime(2026, 5, 21, 13, 5),
    )

    assert summary.current_streak_hours == 1.0
    assert summary.longest_streak_hours == 1.0
    assert summary.current_streak_bar_count == 13


def test_eight_hundred_sixty_five_m5_bars_count_as_seventy_two_active_hours():
    module = _load_module()
    rows = _rows_at_cadence(datetime(2026, 5, 18, 0, 0), 865)

    summary = module.calculate_soak_streak(
        rows,
        now=datetime(2026, 5, 21, 0, 5),
    )

    assert summary.current_streak_hours == 72.0
    assert summary.longest_streak_hours == 72.0
    assert summary.uninterrupted_soak_pass is True
    assert summary.current_streak_bar_count == 865


def test_configured_daily_broker_break_pauses_without_resetting_streak():
    module = _load_module()
    rows = [
        _row("2026.05.26 20:50:00", run_id="phase1-a"),
        _row("2026.05.26 20:55:00", run_id="phase1-a"),
        _row("2026.05.26 22:00:00", run_id="phase1-a"),
        _row("2026.05.26 22:05:00", run_id="phase1-a"),
    ]

    summary = module.calculate_soak_streak(
        rows,
        max_bar_gap_minutes=15.0,
        now=datetime(2026, 5, 26, 22, 10),
    )

    assert summary.current_streak_hours == 0.17
    assert summary.restart_count_during_current_streak == 0
    assert summary.current_streak_bar_count == 4


def test_expected_weekend_gap_pauses_without_adding_closed_market_time():
    module = _load_module()
    rows = [
        _row("2026.05.29 20:50:00", run_id="phase1-a"),
        _row("2026.05.29 20:55:00", run_id="phase1-a"),
        _row("2026.06.01 00:00:00", run_id="phase1-a"),
        _row("2026.06.01 00:05:00", run_id="phase1-a"),
    ]

    summary = module.calculate_soak_streak(
        rows,
        max_bar_gap_minutes=15.0,
        now=datetime(2026, 6, 1, 0, 10),
    )

    assert summary.current_streak_hours == 0.17
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


def test_dry_run_lock_violation_resets_active_market_streak():
    module = _load_module()
    rows = [
        _row("2026.05.21 12:00:00"),
        _row("2026.05.21 12:05:00", dry_run="false"),
        _row("2026.05.21 12:10:00"),
        _row("2026.05.21 12:15:00"),
    ]

    summary = module.calculate_soak_streak(
        rows,
        now=datetime(2026, 5, 21, 12, 20),
    )

    assert summary.current_streak_hours == 0.08
    assert summary.current_streak_bar_count == 2


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


def test_code_freeze_and_process_uptime_are_separate_from_active_market_streak():
    module = _load_module()
    rows = _rows_at_cadence(datetime(2026, 5, 21, 12, 0), 13)

    summary = module.calculate_soak_streak(
        rows,
        code_freeze_started_at="2026-05-17T00:00:00Z",
        now=datetime(2026, 5, 21, 13, 5),
    )

    assert summary.current_streak_hours == 1.0
    assert summary.code_freeze_hours == 109.08
    assert summary.code_freeze_pass is True
    assert summary.process_code_freeze_pass is False


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


def _rows_at_cadence(start: datetime, count: int, run_id: str = "phase1-dry-run-v0.7") -> list[dict[str, str]]:
    return [_row((start + timedelta(minutes=5 * index)).strftime("%Y.%m.%d %H:%M:%S"), run_id=run_id) for index in range(count)]


def _row(
    bar_time: str,
    session: str = "LONDON",
    execution_state: str = "EXECUTION_OK",
    run_id: str = "phase1-dry-run-v0.7",
    trade_permission: str = "false",
    dry_run: str = "true",
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
        "dry_run": dry_run,
        "server_time_status": server_time_status,
        "magic_namespace_ok": "true",
    }
