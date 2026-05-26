from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pandas as pd


EXPERT_NAME = "h1_macro_event_aftershock_v0"
MACRO_EVENT_FRAME_KEY = "macro_event_calendar"


def load_macro_event_calendar_context(
    config: object,
    required_start: object,
    required_end: object,
) -> pd.DataFrame:
    del config
    start = _utc_timestamp(required_start) - pd.Timedelta(days=10)
    end = _utc_timestamp(required_end) + pd.Timedelta(days=10)
    calendar = build_standard_us_macro_event_calendar(start, end)
    if calendar.empty:
        raise ValueError(f"{EXPERT_NAME} generated no macro event slots for requested window.")
    return calendar


def build_standard_us_macro_event_calendar(start: object, end: object) -> pd.DataFrame:
    start_ts = _utc_timestamp(start)
    end_ts = _utc_timestamp(end)
    rows: list[dict[str, object]] = []
    for year in range(start_ts.year - 1, end_ts.year + 2):
        for month in range(1, 13):
            nfp_day = _nth_weekday(year, month, weekday=4, occurrence=1)
            rows.append(_event_row(nfp_day, hour=8, minute=30, event_type="NFP_FIRST_FRIDAY"))

            cpi_day = _nth_weekday(year, month, weekday=2, occurrence=2)
            rows.append(_event_row(cpi_day, hour=8, minute=30, event_type="CPI_SECOND_WEDNESDAY"))

        for month in (1, 3, 5, 6, 7, 9, 11, 12):
            fomc_day = _nth_weekday(year, month, weekday=2, occurrence=3)
            rows.append(_event_row(fomc_day, hour=14, minute=0, event_type="FOMC_THIRD_WEDNESDAY"))

    frame = pd.DataFrame(rows)
    frame = frame.sort_values("timestamp_utc").reset_index(drop=True)
    frame = frame[(frame["timestamp_utc"] >= start_ts) & (frame["timestamp_utc"] <= end_ts)]
    return frame.reset_index(drop=True)


def _event_row(local_day: date, hour: int, minute: int, event_type: str) -> dict[str, object]:
    timestamp_utc = _eastern_wall_time_to_utc(local_day, hour, minute)
    return {
        "timestamp_utc": timestamp_utc,
        "event_type": event_type,
        "source_rule": event_type,
        "local_date": local_day.isoformat(),
        "local_time_et": f"{hour:02d}:{minute:02d}",
    }


def _nth_weekday(year: int, month: int, weekday: int, occurrence: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (occurrence - 1))


def _eastern_wall_time_to_utc(local_day: date, hour: int, minute: int) -> pd.Timestamp:
    utc_offset_hours = 4 if _is_us_dst(local_day) else 5
    utc_dt = datetime(
        local_day.year,
        local_day.month,
        local_day.day,
        hour,
        minute,
        tzinfo=timezone.utc,
    ) + timedelta(hours=utc_offset_hours)
    return pd.Timestamp(utc_dt)


def _is_us_dst(local_day: date) -> bool:
    dst_start = _nth_weekday(local_day.year, 3, weekday=6, occurrence=2)
    dst_end = _nth_weekday(local_day.year, 11, weekday=6, occurrence=1)
    return dst_start <= local_day < dst_end


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
