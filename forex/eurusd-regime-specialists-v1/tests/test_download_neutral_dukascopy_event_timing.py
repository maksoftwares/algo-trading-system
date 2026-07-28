from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from download_neutral_dukascopy_event_timing import (  # noqa: E402
    event_url,
    normalize_events,
    parse_jsonp,
    quarterly_windows,
)


def test_quarterly_windows_are_contiguous_and_bounded() -> None:
    windows = quarterly_windows("2024-01-01", "2024-06-30")
    assert [key for _, _, key in windows] == ["2024-Q1", "2024-Q2"]
    assert windows[0][0] == pd.Timestamp("2024-01-01T00:00:00Z")
    assert windows[0][1] == pd.Timestamp("2024-03-31T00:00:00Z")
    assert windows[1][0] == pd.Timestamp("2024-04-01T00:00:00Z")
    assert windows[1][1] == pd.Timestamp("2024-06-30T00:00:00Z")


def test_jsonp_parser_and_normalizer() -> None:
    payload = (
        b'jsonp([{"id":"1","date":"2024-01-05T13:30:00+0000",'
        b'"country":"US","currency":"USD","title":"Nonfarm Payrolls",'
        b'"impact":"2","tag":"US_NonPay","forecast":"170K"}])'
    )
    rows = parse_jsonp(payload)
    frame = normalize_events(
        rows,
        pd.Timestamp("2024-01-01T00:00:00Z"),
        pd.Timestamp("2024-03-31T00:00:00Z"),
    )
    assert frame["event_id"].tolist() == ["1"]
    assert frame["event_time_utc"].tolist() == [
        pd.Timestamp("2024-01-05T13:30:00Z")
    ]
    assert frame["forecast"].tolist() == ["170K"]


def test_event_url_uses_epoch_milliseconds() -> None:
    url = event_url(
        pd.Timestamp("2024-01-01T00:00:00Z"),
        pd.Timestamp("2024-03-31T00:00:00Z"),
    )
    assert "since=1704067200000" in url
    assert "until=1711929599999" in url
