from __future__ import annotations

import json

import pandas as pd
import pytest

from capture_prospective_tradingview_actuals import (
    build_post_release_rows,
    mature_forecasts,
    persist_post_release_snapshot,
)


def _forecast(observed_at: str = "2026-08-07T11:30:00Z") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "family": ["NFP"],
            "event_time_utc": pd.to_datetime(
                ["2026-08-07T12:30:00Z"], utc=True
            ),
            "forecast_value": [150000.0],
            "previous_value": [147000.0],
            "tradingview_event_id": ["396495"],
            "tradingview_ticker": ["ECONOMICS:USNFP"],
            "observed_at_utc": pd.to_datetime(
                [observed_at], utc=True
            ),
            "lead_seconds": [3600.0],
            "raw_snapshot_relative_path": ["raw/pre.json"],
            "raw_snapshot_sha256": ["a" * 64],
        }
    )


def _actual_payload(actual: float | None = 175000.0) -> dict:
    return {
        "status": "ok",
        "result": [
            {
                "id": "396495",
                "date": "2026-08-07T12:30:00Z",
                "ticker": "ECONOMICS:USNFP",
                "actualRaw": actual,
                "forecastRaw": 150000,
            }
        ],
    }


def test_actual_links_to_strict_pre_release_forecast() -> None:
    rows, excluded = build_post_release_rows(
        _actual_payload(),
        pd.Timestamp("2026-08-07T12:32:00Z"),
        _forecast(),
        "post_release_raw/post.json",
        "b" * 64,
    )
    assert len(rows) == 1
    assert rows["surprise_value"].iloc[0] == 25000.0
    assert rows["macro_side"].iloc[0] == "SHORT"
    assert rows["forecast_observed_at_utc"].iloc[0] < (
        rows["event_time_utc"].iloc[0]
    )
    assert excluded["actual_missing"] == 0


def test_actual_before_post_release_margin_is_excluded() -> None:
    rows, excluded = build_post_release_rows(
        _actual_payload(),
        pd.Timestamp("2026-08-07T12:30:30Z"),
        _forecast(),
        "post_release_raw/post.json",
        "b" * 64,
    )
    assert rows.empty
    assert excluded["not_strictly_post_release"] == 1


def test_missing_actual_is_not_linked() -> None:
    rows, excluded = build_post_release_rows(
        _actual_payload(None),
        pd.Timestamp("2026-08-07T12:32:00Z"),
        _forecast(),
        "post_release_raw/post.json",
        "b" * 64,
    )
    assert rows.empty
    assert excluded["actual_missing"] == 1


def test_forecast_observed_after_event_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="pre-release lead"):
        build_post_release_rows(
            _actual_payload(),
            pd.Timestamp("2026-08-07T12:32:00Z"),
            _forecast("2026-08-07T12:31:00Z"),
            "post_release_raw/post.json",
            "b" * 64,
        )


def test_forecast_inside_sixty_second_margin_is_rejected() -> None:
    forecast = _forecast("2026-08-07T12:29:30Z")
    forecast["lead_seconds"] = 30.0
    with pytest.raises(RuntimeError, match="pre-release lead"):
        build_post_release_rows(
            _actual_payload(),
            pd.Timestamp("2026-08-07T12:32:00Z"),
            forecast,
            "post_release_raw/post.json",
            "b" * 64,
        )


def test_only_mature_forecasts_request_network() -> None:
    forecasts = _forecast()
    early = mature_forecasts(
        forecasts, pd.Timestamp("2026-08-07T12:30:30Z")
    )
    mature = mature_forecasts(
        forecasts, pd.Timestamp("2026-08-07T12:31:00Z")
    )
    assert early.empty
    assert len(mature) == 1


def test_post_release_snapshots_are_idempotent_and_append_only(
    tmp_path,
) -> None:
    metadata = {
        "url": "https://example.invalid/calendar",
        "requested_window": [
            pd.Timestamp("2026-08-07T00:00:00Z"),
            pd.Timestamp("2026-08-08T00:00:00Z"),
        ],
        "request_started_utc": pd.Timestamp(
            "2026-08-07T12:32:00Z"
        ),
        "request_finished_utc": pd.Timestamp(
            "2026-08-07T12:32:01Z"
        ),
        "http_date_utc": pd.Timestamp("2026-08-07T12:32:01Z"),
        "observed_at_utc": pd.Timestamp("2026-08-07T12:32:01Z"),
        "response_headers": {},
    }
    first_payload = json.dumps(_actual_payload()).encode("utf-8")
    first_manifest, first_rows = persist_post_release_snapshot(
        tmp_path, first_payload, metadata, _forecast()
    )
    repeated_manifest, repeated_rows = persist_post_release_snapshot(
        tmp_path, first_payload, metadata, _forecast()
    )
    assert first_manifest["manifest_sha256"] == (
        repeated_manifest["manifest_sha256"]
    )
    pd.testing.assert_frame_equal(first_rows, repeated_rows)
    assert len(list(tmp_path.glob("post_release_raw/*.json"))) == 1

    revised = _actual_payload(176000.0)
    second_payload = json.dumps(revised).encode("utf-8")
    second_manifest, second_rows = persist_post_release_snapshot(
        tmp_path, second_payload, metadata, _forecast()
    )
    assert second_manifest["manifest_sha256"] != (
        first_manifest["manifest_sha256"]
    )
    assert second_rows["actual_value"].iloc[0] == 176000.0
    assert first_rows["actual_value"].iloc[0] == 175000.0
    assert len(list(tmp_path.glob("post_release_raw/*.json"))) == 2
    assert len(
        list(tmp_path.glob("post_release_normalized/*.parquet"))
    ) == 2
