from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
import re
from typing import Iterable, Mapping
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import pandas as pd


STATEMENT_PATTERN = re.compile(
    r"(?:monetary)?(?P<date>\d{8})a\.htm$", re.IGNORECASE
)
REGULAR_MEETING_PATTERN = re.compile(r"\bMeeting\s*-\s*(?P<year>\d{4})\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class StatementLink:
    meeting_heading: str
    statement_date: date
    href: str


def _clean(value: str) -> str:
    return " ".join(value.split())


class HistoricalPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current_heading = ""
        self._heading_depth = 0
        self._heading_parts: list[str] = []
        self._anchor_href: str | None = None
        self._anchor_parts: list[str] = []
        self.statement_links: list[StatementLink] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "h5":
            self._heading_depth = 1
            self._heading_parts = []
        elif self._heading_depth:
            self._heading_depth += 1
        if tag.lower() == "a":
            self._anchor_href = attributes.get("href")
            self._anchor_parts = []

    def handle_endtag(self, tag: str) -> None:
        if self._heading_depth:
            self._heading_depth -= 1
            if self._heading_depth == 0:
                self.current_heading = _clean("".join(self._heading_parts))
        if tag.lower() != "a" or self._anchor_href is None:
            return
        text = _clean("".join(self._anchor_parts))
        match = STATEMENT_PATTERN.search(self._anchor_href)
        heading_match = REGULAR_MEETING_PATTERN.search(self.current_heading)
        if text.lower() == "statement" and match and heading_match:
            parsed = datetime.strptime(match.group("date"), "%Y%m%d").date()
            if parsed.year != int(heading_match.group("year")):
                raise ValueError("Statement date and historical heading year disagree")
            self.statement_links.append(
                StatementLink(self.current_heading, parsed, self._anchor_href)
            )
        self._anchor_href = None
        self._anchor_parts = []

    def handle_data(self, data: str) -> None:
        if self._heading_depth:
            self._heading_parts.append(data)
        if self._anchor_href is not None:
            self._anchor_parts.append(data)


def parse_regular_statement_links(html: str) -> list[StatementLink]:
    parser = HistoricalPageParser()
    parser.feed(html)
    parser.close()
    values = sorted(parser.statement_links, key=lambda item: item.statement_date)
    dates = [item.statement_date for item in values]
    if dates != sorted(set(dates)):
        raise ValueError("Duplicate regular FOMC statement date")
    return values


def release_clock(
    statement_date: date, settings: Mapping[str, object]
) -> tuple[str, str]:
    switch = date.fromisoformat(str(settings["modern_clock_first_date"]))
    if statement_date < switch:
        return str(settings["legacy_release_clock_et"]), "LEGACY_1415_ET"
    return str(settings["modern_release_clock_et"]), "MODERN_1400_ET"


def build_calendar(
    links: Iterable[StatementLink],
    settings: Mapping[str, object],
    start_utc: pd.Timestamp,
    end_exclusive_utc: pd.Timestamp,
) -> pd.DataFrame:
    timezone = ZoneInfo(str(settings["timezone"]))
    base_url = str(settings["statement_base_url"])
    rows: list[dict[str, object]] = []
    for item in links:
        clock, rule = release_clock(item.statement_date, settings)
        hour, minute = (int(value) for value in clock.split(":"))
        local = datetime(
            item.statement_date.year,
            item.statement_date.month,
            item.statement_date.day,
            hour,
            minute,
            tzinfo=timezone,
        )
        event_time = pd.Timestamp(local).tz_convert("UTC")
        if not start_utc <= event_time < end_exclusive_utc:
            continue
        rows.append(
            {
                "event_id": f"FOMC_{item.statement_date.isoformat()}",
                "event_type": "FOMC",
                "date": item.statement_date.isoformat(),
                "event_time_utc": event_time,
                "release_clock_et": clock,
                "release_time_rule": rule,
                "meeting_heading": item.meeting_heading,
                "source_kind": "FEDERAL_RESERVE_OFFICIAL_HISTORICAL_ARCHIVE",
                "source_url": urljoin(base_url, item.href),
            }
        )
    calendar = pd.DataFrame(rows).sort_values("event_time_utc", kind="mergesort")
    calendar = calendar.reset_index(drop=True)
    if calendar.empty:
        raise ValueError("Official FOMC calendar is empty")
    if calendar["event_id"].duplicated().any():
        raise ValueError("Duplicate official FOMC event ID")
    return calendar
