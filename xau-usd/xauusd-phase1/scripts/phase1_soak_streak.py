from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from phase1_gap_classifier import classify_gap, is_active_market_row, is_expected_pause_row


DEFAULT_REQUIRED_STREAK_HOURS = 72.0
DEFAULT_REQUIRED_CODE_FREEZE_HOURS = 96.0
DEFAULT_MAX_BAR_GAP_MINUTES = 15.0
CODE_FREEZE_MARKER_NAME = "phase1_code_freeze_started_at.txt"
WEEKEND_POLICY = "expected_market_breaks_pause_active_market_streak"


@dataclass(frozen=True)
class SoakStreakSummary:
    current_streak_hours: float
    longest_streak_hours: float
    required_uninterrupted_streak_hours: float
    active_market_streak_hours: float
    restart_count_during_current_streak: int
    last_restart_utc: str
    weekend_policy: str
    process_uptime_streak_hours: float
    code_freeze_started_at: str
    code_freeze_hours: float
    required_code_freeze_hours: float
    code_freeze_pass: bool
    process_code_freeze_pass: bool
    uninterrupted_soak_pass: bool
    current_streak_bar_count: int
    longest_streak_bar_count: int
    max_bar_gap_minutes: float


def calculate_soak_streak(
    rows: list[dict[str, str]],
    required_hours: float = DEFAULT_REQUIRED_STREAK_HOURS,
    max_bar_gap_minutes: float = DEFAULT_MAX_BAR_GAP_MINUTES,
    code_freeze_started_at: str = "",
    now: datetime | None = None,
    required_code_freeze_hours: float = DEFAULT_REQUIRED_CODE_FREEZE_HOURS,
) -> SoakStreakSummary:
    if now is None:
        now = datetime.now(timezone.utc)
    now_utc = _coerce_utc(now)
    max_gap_seconds = max_bar_gap_minutes * 60
    current_start: datetime | None = None
    current_end: datetime | None = None
    current_run_id = ""
    current_seconds = 0.0
    current_bars = 0
    longest_hours = 0.0
    longest_bars = 0
    restart_count = 0
    previous_good_row: dict[str, str] | None = None

    for row in rows:
        bar_time = _parse_mt5_datetime(row.get("bar_time", ""))
        if bar_time is None:
            current_start = None
            current_end = None
            current_run_id = ""
            current_seconds = 0.0
            current_bars = 0
            restart_count = 0
            previous_good_row = None
            continue

        if not is_active_market_row(row):
            if current_start is not None and is_expected_pause_row(row):
                continue
            current_start = None
            current_end = None
            current_run_id = ""
            current_seconds = 0.0
            current_bars = 0
            restart_count = 0
            previous_good_row = None
            continue

        run_id = row.get("run_id", "")
        needs_new_segment = current_start is None
        if current_run_id and run_id and run_id != current_run_id:
            needs_new_segment = True
        gap_seconds_to_count = 0.0
        if current_end is not None and not needs_new_segment:
            gap_seconds = (bar_time - current_end).total_seconds()
            if gap_seconds > max_gap_seconds:
                classification = classify_gap(
                    current_end,
                    bar_time,
                    previous_good_row,
                    row,
                    max_bar_gap_minutes=max_bar_gap_minutes,
                )
                if classification.resets_active_market_streak:
                    needs_new_segment = True
                else:
                    # Expected broker/weekend pauses preserve continuity but do not add closed-market time.
                    gap_seconds_to_count = 0.0
            else:
                gap_seconds_to_count = max(gap_seconds, 0.0)

        if needs_new_segment:
            current_start = bar_time
            current_end = bar_time
            current_run_id = run_id
            current_seconds = 0.0
            current_bars = 1
            restart_count = 0
            previous_good_row = row
        elif current_end is not None:
            if bar_time > current_end:
                current_end = bar_time
                current_seconds += gap_seconds_to_count
                current_bars += 1
                previous_good_row = row

        segment_hours = current_seconds / 3600
        if segment_hours >= longest_hours:
            longest_hours = segment_hours
            longest_bars = current_bars

    current_hours = current_seconds / 3600 if current_start is not None else 0.0
    latest_run_id = rows[-1].get("run_id", "") if rows else ""
    last_restart_utc = _latest_run_start_utc(rows, latest_run_id)
    process_uptime_hours = _process_uptime_hours(rows, latest_run_id, now_utc)
    normalized_code_freeze_started_at = _normalize_code_freeze_started_at(code_freeze_started_at)
    code_freeze_hours = _code_freeze_hours(normalized_code_freeze_started_at, now_utc)
    code_freeze_pass = code_freeze_hours >= required_code_freeze_hours
    process_code_freeze_pass = (
        process_uptime_hours >= required_code_freeze_hours and code_freeze_pass
    )
    return SoakStreakSummary(
        current_streak_hours=round(current_hours, 2),
        longest_streak_hours=round(longest_hours, 2),
        required_uninterrupted_streak_hours=required_hours,
        active_market_streak_hours=round(longest_hours, 2),
        restart_count_during_current_streak=restart_count if current_hours > 0 else 0,
        last_restart_utc=last_restart_utc,
        weekend_policy=WEEKEND_POLICY,
        process_uptime_streak_hours=round(process_uptime_hours, 2),
        code_freeze_started_at=normalized_code_freeze_started_at,
        code_freeze_hours=round(code_freeze_hours, 2),
        required_code_freeze_hours=required_code_freeze_hours,
        code_freeze_pass=code_freeze_pass,
        process_code_freeze_pass=process_code_freeze_pass,
        uninterrupted_soak_pass=longest_hours >= required_hours,
        current_streak_bar_count=current_bars if current_hours > 0 else 0,
        longest_streak_bar_count=longest_bars,
        max_bar_gap_minutes=max_bar_gap_minutes,
    )


def read_code_freeze_marker(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        value = line.strip().lstrip("\ufeff")
        if value:
            return value
    return ""


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


def _process_uptime_hours(rows: list[dict[str, str]], latest_run_id: str, now: datetime) -> float:
    if not latest_run_id:
        return 0.0
    for row in rows:
        if row.get("run_id", "") != latest_run_id:
            continue
        started = _parse_mt5_datetime(row.get("timestamp_utc", ""))
        if started is None:
            return 0.0
        started_utc = started.replace(tzinfo=timezone.utc)
        return max((now - started_utc).total_seconds() / 3600, 0.0)
    return 0.0


def _normalize_code_freeze_started_at(value: str) -> str:
    parsed = _parse_iso_datetime(value)
    if parsed is None:
        return ""
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _code_freeze_hours(started_at: str, now: datetime) -> float:
    started = _parse_iso_datetime(started_at)
    if started is None:
        return 0.0
    return max((now - started).total_seconds() / 3600, 0.0)


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_mt5_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None
