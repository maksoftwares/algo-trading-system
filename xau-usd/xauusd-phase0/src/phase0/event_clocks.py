from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

from phase0.config import ConfigError
from phase0.constants import SECOND_EA_LANE_B_CANDIDATES


EVENT_CLOCKS_RELATIVE_PATH = Path("config/event_clocks.yaml")
EVENT_CLOCK_REPORT_RELATIVE_PATH = Path("outputs/reports/EVENT_CLOCK_VALIDATION_REPORT.md")
REQUIRED_FIELDS = (
    "event_id",
    "market_timezone",
    "canonical_local_time",
    "utc_conversion_rule",
    "server_time_conversion_rule",
    "dst_handling_note",
    "source_rationale_note",
)
SAMPLE_DATES = {
    "normal_month": date(2025, 1, 15),
    "us_dst_only_divergence_window": date(2025, 3, 17),
    "uk_dst_active_window": date(2025, 6, 18),
    "post_november_overlap_window": date(2025, 11, 12),
}
EXPECTED_OFFSETS = {
    ("Europe/London", "normal_month"): "+00:00",
    ("Europe/London", "us_dst_only_divergence_window"): "+00:00",
    ("Europe/London", "uk_dst_active_window"): "+01:00",
    ("Europe/London", "post_november_overlap_window"): "+00:00",
    ("America/New_York", "normal_month"): "-05:00",
    ("America/New_York", "us_dst_only_divergence_window"): "-04:00",
    ("America/New_York", "uk_dst_active_window"): "-04:00",
    ("America/New_York", "post_november_overlap_window"): "-05:00",
}


@dataclass(frozen=True)
class EventClock:
    event_id: str
    market_timezone: str
    canonical_local_time: str
    utc_conversion_rule: str
    server_time_conversion_rule: str
    dst_handling_note: str
    source_rationale_note: str
    source_url: str
    linked_candidate_id: str


@dataclass(frozen=True)
class EventClockSample:
    event_id: str
    sample_name: str
    local_date: str
    local_time: str
    market_timezone: str
    utc_time: str
    utc_offset: str
    status: str
    message: str


@dataclass(frozen=True)
class EventClockValidation:
    status: str
    config_path: Path
    report_path: Path
    event_count: int
    sample_count: int
    samples: tuple[EventClockSample, ...]
    messages: tuple[str, ...]


def generate_event_clock_validation(root: Path) -> EventClockValidation:
    config_path = root / EVENT_CLOCKS_RELATIVE_PATH
    report_path = root / EVENT_CLOCK_REPORT_RELATIVE_PATH
    event_clocks = load_event_clocks(config_path)
    samples: list[EventClockSample] = []
    messages: list[str] = []

    for clock in event_clocks:
        samples.extend(_validate_clock_samples(clock))

    if not any(sample.sample_name == "us_dst_only_divergence_window" for sample in samples):
        messages.append("Missing US-DST-only divergence sample.")
    if not any(sample.sample_name == "uk_dst_active_window" for sample in samples):
        messages.append("Missing UK-DST-active sample.")
    if not any(sample.sample_name == "post_november_overlap_window" for sample in samples):
        messages.append("Missing post-November overlap sample.")

    failing = [sample for sample in samples if sample.status != "PASS"]
    status = "PASS" if not failing and not messages else "FAIL"
    validation = EventClockValidation(
        status=status,
        config_path=config_path,
        report_path=report_path,
        event_count=len(event_clocks),
        sample_count=len(samples),
        samples=tuple(samples),
        messages=tuple(messages),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_event_clock_validation_report(validation), encoding="utf-8")
    return validation


def load_event_clocks(path: Path) -> tuple[EventClock, ...]:
    if not path.exists():
        raise ConfigError(f"Event clock config not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_clocks = payload.get("event_clocks")
    if not isinstance(raw_clocks, list) or not raw_clocks:
        raise ConfigError("event_clocks.yaml must define a non-empty event_clocks list.")

    clocks: list[EventClock] = []
    seen_event_ids: set[str] = set()
    for index, raw_clock in enumerate(raw_clocks, start=1):
        if not isinstance(raw_clock, dict):
            raise ConfigError(f"event_clocks[{index}] must be a mapping.")
        missing = [field for field in REQUIRED_FIELDS if not str(raw_clock.get(field, "")).strip()]
        if missing:
            raise ConfigError(f"event_clocks[{index}] missing required field(s): {', '.join(missing)}")
        event_id = str(raw_clock["event_id"])
        if event_id in seen_event_ids:
            raise ConfigError(f"event_clocks[{index}].event_id is duplicated: {event_id}")
        seen_event_ids.add(event_id)
        _validate_schema_text(index, raw_clock)
        _parse_time(str(raw_clock["canonical_local_time"]))
        try:
            ZoneInfo(str(raw_clock["market_timezone"]))
        except ZoneInfoNotFoundError as exc:
            raise ConfigError(
                f"event_clocks[{index}].market_timezone is not an IANA timezone: "
                f"{raw_clock['market_timezone']}"
            ) from exc
        clocks.append(
            EventClock(
                event_id=event_id,
                market_timezone=str(raw_clock["market_timezone"]),
                canonical_local_time=str(raw_clock["canonical_local_time"]),
                utc_conversion_rule=str(raw_clock["utc_conversion_rule"]),
                server_time_conversion_rule=str(raw_clock["server_time_conversion_rule"]),
                dst_handling_note=str(raw_clock["dst_handling_note"]),
                source_rationale_note=str(raw_clock["source_rationale_note"]),
                source_url=str(raw_clock.get("source_url", "")),
                linked_candidate_id=str(raw_clock.get("linked_candidate_id", "")),
            )
        )
    return tuple(clocks)


def _validate_schema_text(index: int, raw_clock: dict[str, Any]) -> None:
    utc_rule = str(raw_clock["utc_conversion_rule"]).lower()
    server_rule = str(raw_clock["server_time_conversion_rule"]).lower()
    dst_note = str(raw_clock["dst_handling_note"]).lower()
    linked_candidate = str(raw_clock.get("linked_candidate_id", "")).strip()
    if "utc" not in utc_rule or "iana" not in utc_rule:
        raise ConfigError(
            f"event_clocks[{index}].utc_conversion_rule must mention UTC and IANA timezone rules."
        )
    if "utc-normalized" not in server_rule or "no mt5" not in server_rule or "runtime" not in server_rule:
        raise ConfigError(
            f"event_clocks[{index}].server_time_conversion_rule must require UTC-normalized offline timestamps and no MT5 runtime."
        )
    if "utc" not in dst_note:
        raise ConfigError(f"event_clocks[{index}].dst_handling_note must describe UTC offset behavior.")
    if linked_candidate not in SECOND_EA_LANE_B_CANDIDATES:
        raise ConfigError(
            f"event_clocks[{index}].linked_candidate_id must reference a Lane B campaign candidate."
        )


def render_event_clock_validation_report(validation: EventClockValidation) -> str:
    sample_rows = [
        {
            "Event": sample.event_id,
            "Sample": sample.sample_name,
            "Local date": sample.local_date,
            "Local time": sample.local_time,
            "Timezone": sample.market_timezone,
            "UTC time": sample.utc_time,
            "UTC offset": sample.utc_offset,
            "Status": sample.status,
            "Message": sample.message,
        }
        for sample in validation.samples
    ]
    messages = list(validation.messages) or ["All configured event clocks round-trip through UTC."]
    return "\n".join(
        [
            "# Event Clock Validation Report",
            "",
            f"Status: {validation.status}",
            f"Config: `{validation.config_path}`",
            f"Event clocks: {validation.event_count}",
            f"Samples: {validation.sample_count}",
            "",
            "## Boundary",
            "",
            "This is an offline calendar validation only. It does not authorize Lane B hypotheses, matrix runs, observer deployment, demo execution, live execution, MT5 runtime access, or broker action.",
            "",
            "## Schema Checks",
            "",
            "- Required fields are present for every event clock.",
            "- Event IDs are unique.",
            "- UTC conversion rules explicitly reference UTC and IANA timezone rules.",
            "- Server-time rules require UTC-normalized offline timestamps and no MT5 runtime.",
            "- DST notes describe UTC offset behavior.",
            "- Linked candidates are the configured Lane B campaign candidates.",
            "",
            "## DST Samples",
            "",
            _markdown_table(sample_rows, ["Event", "Sample", "Local date", "Local time", "Timezone", "UTC time", "UTC offset", "Status", "Message"]),
            "",
            "## Notes",
            "",
            *[f"- {message}" for message in messages],
            "",
            "Lane B remains blocked until Lane A completes or owner override is explicit.",
            "",
        ]
    )


def _validate_clock_samples(clock: EventClock) -> list[EventClockSample]:
    parsed_time = _parse_time(clock.canonical_local_time)
    zone = ZoneInfo(clock.market_timezone)
    samples: list[EventClockSample] = []
    for sample_name, sample_date in SAMPLE_DATES.items():
        local_dt = datetime.combine(sample_date, parsed_time, tzinfo=zone)
        utc_dt = local_dt.astimezone(timezone.utc)
        roundtrip = utc_dt.astimezone(zone)
        offset = _format_offset(local_dt)
        expected_offset = EXPECTED_OFFSETS.get((clock.market_timezone, sample_name))
        status = "PASS"
        messages: list[str] = []
        if roundtrip.replace(fold=0) != local_dt.replace(fold=0):
            status = "FAIL"
            messages.append("UTC round-trip changed local event time.")
        if expected_offset is not None and offset != expected_offset:
            status = "FAIL"
            messages.append(f"Expected offset {expected_offset}, observed {offset}.")
        if not messages:
            messages.append("UTC conversion matches configured timezone rules.")
        samples.append(
            EventClockSample(
                event_id=clock.event_id,
                sample_name=sample_name,
                local_date=sample_date.isoformat(),
                local_time=clock.canonical_local_time,
                market_timezone=clock.market_timezone,
                utc_time=utc_dt.isoformat().replace("+00:00", "Z"),
                utc_offset=offset,
                status=status,
                message=" ".join(messages),
            )
        )
    return samples


def _parse_time(raw: str) -> time:
    try:
        return time.fromisoformat(raw)
    except ValueError as exc:
        raise ConfigError(f"canonical_local_time must be HH:MM or HH:MM:SS, got {raw!r}") from exc


def _format_offset(local_dt: datetime) -> str:
    offset = local_dt.utcoffset()
    if offset is None:
        return "UNKNOWN"
    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _markdown_table(rows: list[dict[str, Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)
