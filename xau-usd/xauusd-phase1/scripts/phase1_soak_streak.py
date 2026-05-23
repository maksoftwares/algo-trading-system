from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


DEFAULT_REQUIRED_STREAK_HOURS = 72.0
DEFAULT_MAX_BAR_GAP_MINUTES = 15.0


@dataclass(frozen=True)
class SoakStreakSummary:
    current_streak_hours: float
    longest_streak_hours: float
    required_uninterrupted_streak_hours: float
    restart_count_during_current_streak: int
    last_restart_utc: str
    uninterrupted_soak_pass: bool
    current_streak_bar_count: int
    longest_streak_bar_count: int
    max_bar_gap_minutes: float


def calculate_soak_streak(
    rows: list[dict[str, str]],
    required_hours: float = DEFAULT_REQUIRED_STREAK_HOURS,
    max_bar_gap_minutes: float = DEFAULT_MAX_BAR_GAP_MINUTES,
) -> SoakStreakSummary:
    max_gap_seconds = max_bar_gap_minutes * 60
    current_start: datetime | None = None
    current_end: datetime | None = None
    current_run_id = ""
    current_bars = 0
    longest_hours = 0.0
    longest_bars = 0

    for row in rows:
        bar_time = _parse_mt5_datetime(row.get("bar_time", ""))
        if bar_time is None or not _is_good_soak_row(row):
            current_start = None
            current_end = None
            current_run_id = ""
            current_bars = 0
            continue

        run_id = row.get("run_id", "")
        needs_new_segment = current_start is None or run_id != current_run_id
        if current_end is not None and (bar_time - current_end).total_seconds() > max_gap_seconds:
            needs_new_segment = True

        if needs_new_segment:
            current_start = bar_time
            current_end = bar_time
            current_run_id = run_id
            current_bars = 1
        elif current_end is not None and bar_time > current_end:
            current_end = bar_time
            current_bars += 1

        segment_hours = _segment_hours(current_start, current_end)
        if segment_hours >= longest_hours:
            longest_hours = segment_hours
            longest_bars = current_bars

    current_hours = _segment_hours(current_start, current_end)
    latest_run_id = rows[-1].get("run_id", "") if rows else ""
    return SoakStreakSummary(
        current_streak_hours=round(current_hours, 2),
        longest_streak_hours=round(longest_hours, 2),
        required_uninterrupted_streak_hours=required_hours,
        restart_count_during_current_streak=0 if current_hours > 0 else 0,
        last_restart_utc=_latest_run_start_utc(rows, latest_run_id),
        uninterrupted_soak_pass=longest_hours >= required_hours,
        current_streak_bar_count=current_bars if current_hours > 0 else 0,
        longest_streak_bar_count=longest_bars,
        max_bar_gap_minutes=max_bar_gap_minutes,
    )


def _segment_hours(start: datetime | None, end: datetime | None) -> float:
    if start is None or end is None:
        return 0.0
    return max((end - start).total_seconds() / 3600, 0.0)


def _is_good_soak_row(row: dict[str, str]) -> bool:
    if row.get("lifecycle_state", "") != "DRY_RUN":
        return False
    if row.get("dry_run", "").lower() != "true":
        return False
    if row.get("trade_permission", "").lower() != "false":
        return False
    if row.get("server_time_status", "") != "CLOCK_OK":
        return False
    magic = row.get("magic_namespace_ok", "")
    return magic == "" or magic.lower() == "true"


def _latest_run_start_utc(rows: list[dict[str, str]], latest_run_id: str) -> str:
    if not latest_run_id:
        return ""
    for row in rows:
        if row.get("run_id", "") == latest_run_id:
            parsed = _parse_mt5_datetime(row.get("timestamp_utc", ""))
            if parsed is not None:
                return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
            return row.get("timestamp_utc", "")
    return ""


def _parse_mt5_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None
