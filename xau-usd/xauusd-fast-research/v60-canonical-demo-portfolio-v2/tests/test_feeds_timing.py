from __future__ import annotations

import time

import pandas as pd

from feeds import _run_feed_group, normalize_utc_datetime_columns


def test_feed_group_records_each_runner_duration() -> None:
    def runner(_config):
        time.sleep(0.01)
        return {"ready": True}

    result = _run_feed_group(
        {"account": {"expected_login": 1033030}}, [("TEST", runner)]
    )
    observed = result["feeds"]["TEST"]
    assert observed["ok"] is True
    assert observed["status"] == {"ready": True}
    assert observed["duration_seconds"] >= 0.01


def test_feed_group_times_failures() -> None:
    def runner(_config):
        raise RuntimeError("boom")

    result = _run_feed_group(
        {"account": {"expected_login": 1033030}}, [("TEST", runner)]
    )
    observed = result["feeds"]["TEST"]
    assert observed["ok"] is False
    assert observed["duration_seconds"] >= 0.0
    assert observed["error"] == "RuntimeError: boom"


def test_datetime_normalization_prevents_mixed_unit_object_fallback() -> None:
    seconds = pd.DataFrame(
        {"bar_start_utc": pd.Series([pd.Timestamp("2026-01-01T00:00:00Z")], dtype="datetime64[s, UTC]")}
    )
    milliseconds = pd.DataFrame(
        {"bar_start_utc": pd.Series([pd.Timestamp("2026-01-01T00:05:00Z")], dtype="datetime64[ms, UTC]")}
    )
    combined = pd.concat(
        [
            normalize_utc_datetime_columns(seconds),
            normalize_utc_datetime_columns(milliseconds),
        ],
        ignore_index=True,
    )
    assert str(combined["bar_start_utc"].dtype) == "datetime64[ns, UTC]"
