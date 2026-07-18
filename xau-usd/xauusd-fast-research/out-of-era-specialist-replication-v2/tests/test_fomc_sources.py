from __future__ import annotations

from datetime import date
import importlib.util
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "fomc_sources.py"
SPEC = importlib.util.spec_from_file_location("out_of_era_fomc_sources_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


SETTINGS = {
    "statement_base_url": "https://www.federalreserve.gov",
    "modern_clock_first_date": "2013-03-20",
    "legacy_release_clock_et": "14:15",
    "modern_release_clock_et": "14:00",
    "timezone": "America/New_York",
}


def test_parser_accepts_meetings_and_excludes_conference_calls() -> None:
    html = """
    <h5 class="panel-heading">January 25-26 Meeting - 2011</h5>
    <p><a href="/newsevents/pressreleases/monetary20110126a.htm">Statement</a></p>
    <h5 class="panel-heading">August 1 Conference Call - 2011</h5>
    <p><a href="/newsevents/pressreleases/monetary20110801a.htm">Statement</a></p>
    """
    links = MODULE.parse_regular_statement_links(html)
    assert len(links) == 1
    assert links[0].statement_date == date(2011, 1, 26)


def test_parser_accepts_legacy_2010_statement_path() -> None:
    html = """
    <h5>January 26-27 Meeting - 2010</h5>
    <p><a href="/newsevents/press/monetary/20100127a.htm">Statement</a></p>
    """
    links = MODULE.parse_regular_statement_links(html)
    assert len(links) == 1
    assert links[0].statement_date == date(2010, 1, 27)


def test_release_clock_switch_is_exact() -> None:
    assert MODULE.release_clock(date(2013, 1, 30), SETTINGS) == (
        "14:15",
        "LEGACY_1415_ET",
    )
    assert MODULE.release_clock(date(2013, 3, 20), SETTINGS) == (
        "14:00",
        "MODERN_1400_ET",
    )


def test_calendar_converts_new_york_dst_without_future_fields() -> None:
    links = [
        MODULE.StatementLink("January 24-25 Meeting - 2012", date(2012, 1, 25), "/newsevents/pressreleases/monetary20120125a.htm"),
        MODULE.StatementLink("March 19-20 Meeting - 2013", date(2013, 3, 20), "/newsevents/pressreleases/monetary20130320a.htm"),
    ]
    calendar = MODULE.build_calendar(
        links,
        SETTINGS,
        pd.Timestamp("2010-01-01T00:00:00Z"),
        pd.Timestamp("2016-07-01T00:00:00Z"),
    )
    assert calendar.loc[0, "event_time_utc"] == pd.Timestamp("2012-01-25T19:15:00Z")
    assert calendar.loc[1, "event_time_utc"] == pd.Timestamp("2013-03-20T18:00:00Z")
    assert not any("pnl" in column.lower() for column in calendar.columns)
