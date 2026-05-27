from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path


DEFAULT_MAX_BAR_GAP_MINUTES = 15.0
DEFAULT_EXPECTED_BREAKS = Path(__file__).resolve().parents[1] / "PHASE1_EXPECTED_MARKET_BREAKS.yaml"
WEEKDAY_INDEX = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}


@dataclass(frozen=True)
class GapClassification:
    reason: str
    resets_active_market_streak: bool
    counts_as_runtime_warning: bool
    counts_toward_process_uptime: bool

    @property
    def is_expected_pause(self) -> bool:
        return not self.resets_active_market_streak and not self.counts_as_runtime_warning


def classify_gap(
    left: datetime,
    right: datetime,
    left_row: dict[str, str] | None = None,
    right_row: dict[str, str] | None = None,
    max_bar_gap_minutes: float = DEFAULT_MAX_BAR_GAP_MINUTES,
    expected_breaks_path: Path = DEFAULT_EXPECTED_BREAKS,
) -> GapClassification:
    left_row = left_row or {}
    right_row = right_row or {}
    minutes = (right - left).total_seconds() / 60
    if minutes <= max_bar_gap_minutes:
        return GapClassification("NORMAL_M5_CADENCE", False, False, True)

    if _is_weekend_stale_resume_gap(right_row) or _spans_weekend_market_break(left, right):
        return GapClassification("EXPECTED_WEEKEND_BREAK", False, False, True)

    configured_reason = _configured_break_reason(left, right, expected_breaks_path)
    if configured_reason:
        return GapClassification(configured_reason, False, False, True)

    if _is_rollover_gap(left, right, right_row):
        return GapClassification("EXPECTED_ROLLOVER_BREAK", False, False, True)

    return GapClassification("UNEXPECTED_BAR_GAP", True, True, True)


def is_active_market_row(row: dict[str, str]) -> bool:
    if row.get("lifecycle_state", "") != "DRY_RUN":
        return False
    if row.get("dry_run", "").lower() != "true":
        return False
    if row.get("trade_permission", "").lower() != "false":
        return False
    if row.get("server_time_status", "") != "CLOCK_OK":
        return False
    if row.get("session", "").upper() == "WEEKEND":
        return False
    if row.get("execution_state", "").upper() in {"MARKET_CLOSED", "STALE_TICK"}:
        return False
    magic = row.get("magic_namespace_ok", "")
    return magic == "" or magic.lower() == "true"


def is_expected_pause_row(row: dict[str, str]) -> bool:
    if row.get("lifecycle_state", "") != "DRY_RUN":
        return False
    if row.get("dry_run", "").lower() != "true":
        return False
    if row.get("trade_permission", "").lower() != "false":
        return False
    if row.get("server_time_status", "") != "CLOCK_OK":
        return False
    if row.get("session", "").upper() == "WEEKEND":
        timestamp = parse_mt5_datetime(row.get("timestamp_broker", "")) or parse_mt5_datetime(row.get("bar_time", ""))
        return timestamp is not None and timestamp.weekday() in {5, 6}
    execution_state = row.get("execution_state", "").upper()
    return execution_state == "MARKET_CLOSED" and row.get("session", "").upper() == "ROLLOVER"


def _is_weekend_stale_resume_gap(row: dict[str, str]) -> bool:
    if row.get("session", "").upper() != "WEEKEND":
        return False
    if row.get("execution_state", "").upper() not in {"STALE_TICK", "MARKET_CLOSED"}:
        return False
    timestamp_broker = parse_mt5_datetime(row.get("timestamp_broker", "")) or parse_mt5_datetime(
        row.get("bar_time", "")
    )
    if timestamp_broker is None:
        return False
    return timestamp_broker.weekday() in {5, 6}


def _spans_weekend_market_break(left: datetime, right: datetime) -> bool:
    if right <= left:
        return False
    hours = (right - left).total_seconds() / 3600
    if hours > 96:
        return False
    day = left.date()
    end_day = right.date()
    while day <= end_day:
        if day.weekday() in {5, 6}:
            return True
        day += timedelta(days=1)
    return False


def _configured_break_reason(left: datetime, right: datetime, path: Path) -> str:
    minutes = int((right - left).total_seconds() / 60)
    for item in _load_expected_market_breaks(path):
        max_gap = _to_int(item.get("max_gap_minutes")) or 0
        if max_gap <= 0 or minutes > max_gap:
            continue
        weekdays = _weekday_indexes(item.get("weekdays", ""))
        start = _parse_time(item.get("start_utc", ""))
        end = _parse_time(item.get("end_utc", ""))
        if start is None or end is None:
            continue
        for day_offset in range((right.date() - left.date()).days + 1):
            day = left.date() + timedelta(days=day_offset)
            if weekdays and day.weekday() not in weekdays:
                continue
            start_at = datetime.combine(day, start)
            end_at = datetime.combine(day, end)
            if end_at <= start_at:
                end_at += timedelta(days=1)
            if left < end_at and right > start_at:
                return _configured_reason_code(item.get("label", ""))
    return ""


def _configured_reason_code(label: str) -> str:
    normalized = label.upper()
    if "DAILY" in normalized or "MAINTENANCE" in normalized:
        return "EXPECTED_DAILY_BROKER_BREAK"
    if "ROLLOVER" in normalized:
        return "EXPECTED_ROLLOVER_BREAK"
    return "EXPECTED_CONFIGURED_MARKET_BREAK"


def _is_rollover_gap(left: datetime, right: datetime, right_row: dict[str, str]) -> bool:
    minutes = int((right - left).total_seconds() / 60)
    if minutes > 90:
        return False
    right_session = right_row.get("session", "")
    left_minute = left.hour * 60 + left.minute
    right_minute = right.hour * 60 + right.minute
    crosses_known_gold_break = left_minute <= 21 * 60 <= right_minute or left_minute <= 22 * 60 <= right_minute
    return right_session == "ROLLOVER" and crosses_known_gold_break


def _load_expected_market_breaks(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("expected_breaks:"):
            continue
        if line.startswith("- "):
            if current:
                rows.append(current)
            current = {}
            line = line[2:].strip()
            if line:
                _assign_yaml_scalar(current, line)
        elif current is not None:
            _assign_yaml_scalar(current, line)
    if current:
        rows.append(current)
    return rows


def _assign_yaml_scalar(target: dict[str, str], line: str) -> None:
    if ":" not in line:
        return
    key, value = line.split(":", 1)
    target[key.strip()] = value.strip().strip('"').strip("'")


def _weekday_indexes(value: str) -> set[int]:
    cleaned = value.strip().strip("[]")
    names = [item.strip().strip('"').strip("'") for item in cleaned.split(",") if item.strip()]
    return {WEEKDAY_INDEX[name.upper()] for name in names if name.upper() in WEEKDAY_INDEX}


def _parse_time(value: str) -> time | None:
    try:
        hour, minute = value.split(":", 1)
        return time(int(hour), int(minute))
    except (ValueError, TypeError):
        return None


def _to_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def parse_mt5_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None
