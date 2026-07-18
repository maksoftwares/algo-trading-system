from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proxy_data import (  # noqa: E402
    SourceValidationError,
    acquisition_hours,
    acquire_hour,
    build_pressure_frame,
    decode_hour,
    validate_official_url,
)


def _payload(hour: datetime) -> bytes:
    start = int(hour.timestamp() * 1000)
    return json.dumps(
        {
            "timestamp": start,
            "bid": 100.0,
            "ask": 100.02,
            "multiplier": 0.001,
            "times": [0, 60_000, 14 * 60_000, 1],
            "bids": [0, 1, 2, -1],
            "asks": [0, 1, 2, -1],
            "bidVolumes": [1.0, 1.0, 1.0, 1.0],
            "askVolumes": [1.0, 1.0, 1.0, 1.0],
        }
    ).encode("ascii")


def test_decode_hour_uses_last_tick_midpoint_per_bucket() -> None:
    hour = datetime(2018, 6, 1, 14, tzinfo=UTC)
    result = decode_hour(_payload(hour), hour)
    assert result.tick_count == 4
    assert len(result.m15_rows) == 2
    assert result.m15_rows[0]["tick_count"] == 2
    assert result.m15_rows[0]["mid_close"] == pytest.approx(100.011)
    assert result.m15_rows[1]["mid_close"] == pytest.approx(100.012)


def test_decode_rejects_tick_outside_requested_hour() -> None:
    hour = datetime(2018, 6, 1, 14, tzinfo=UTC)
    payload = json.loads(_payload(hour))
    payload["times"][-1] = 3_600_000
    with pytest.raises(SourceValidationError):
        decode_hour(json.dumps(payload).encode("ascii"), hour)


def test_declared_invalid_hour_is_retained_as_quarantine(tmp_path: Path) -> None:
    hour = datetime(2018, 6, 1, 14, tzinfo=UTC)
    payload = json.loads(_payload(hour))
    payload["bids"][2] = 1000
    raw = json.dumps(payload).encode("ascii")

    def fetcher(url: str, timeout: int):
        return raw, {}, 200

    row = acquire_hour(
        tmp_path,
        "https://jetta.dukascopy.com/v1",
        "DOLLARIDXUSD",
        "DOLLAR.IDX-USD",
        hour,
        10,
        True,
        fetcher,
    )
    assert row["status"] == "SOURCE_INVALID_HOUR_QUARANTINED"
    assert row["m15_rows"] == 0
    assert (tmp_path / row["path"]).is_file()


def test_acquisition_hours_are_weekdays_and_declared_hours_only() -> None:
    values = acquisition_hours(
        datetime(2024, 1, 5, tzinfo=UTC),
        datetime(2024, 1, 9, tzinfo=UTC),
        [13, 20],
    )
    assert [(value.weekday(), value.hour) for value in values] == [
        (4, 13),
        (4, 20),
        (0, 13),
        (0, 20),
    ]


def test_official_url_validation_rejects_other_hosts() -> None:
    with pytest.raises(SourceValidationError):
        validate_official_url(
            "https://example.com/v1/ticks/TLT.US-USD/2018/6/1/14",
            "https://jetta.dukascopy.com/v1",
        )


def _cache(rows: int = 240) -> pd.DataFrame:
    timestamps = pd.date_range("2018-01-02T13:15:00Z", periods=rows, freq="15min")
    values = []
    for symbol, drift in (("DOLLARIDXUSD", 0.01), ("TLTUSD", 0.02)):
        values.append(
            pd.DataFrame(
                {
                    "timestamp_utc": timestamps,
                    "symbol": symbol,
                    "mid_close": 100.0 + np.arange(rows) * drift,
                    "tick_count": 1,
                }
            )
        )
    return pd.concat(values, ignore_index=True)


def _settings() -> dict:
    return {
        "return_bars": 4,
        "return_elapsed_minutes": 60,
        "scale_elapsed_hours": 48,
        "minimum_prior_observations": 20,
        "dxy_pressure_sign": -1.0,
        "bond_pressure_sign": 1.0,
    }


def test_pressure_features_are_causal() -> None:
    source = _cache()
    original = build_pressure_frame(source, "TLTUSD", _settings())
    cutoff = pd.Timestamp("2018-01-04T12:00:00Z")
    changed = source.copy()
    changed.loc[changed["timestamp_utc"].ge(cutoff), "mid_close"] *= 1.5
    revised = build_pressure_frame(changed, "TLTUSD", _settings())
    pd.testing.assert_frame_equal(
        original.loc[original["timestamp_utc"].lt(cutoff)].reset_index(drop=True),
        revised.loc[revised["timestamp_utc"].lt(cutoff)].reset_index(drop=True),
    )


def test_noncontiguous_h1_return_is_rejected() -> None:
    source = _cache(80)
    missing = source["timestamp_utc"].drop_duplicates().iloc[20]
    source = source.loc[source["timestamp_utc"].ne(missing)].reset_index(drop=True)
    result = build_pressure_frame(source, "TLTUSD", _settings())
    after_gap = missing + pd.Timedelta(minutes=15)
    row = result.loc[result["timestamp_utc"].eq(after_gap)]
    assert len(row) == 1
    assert np.isnan(row["dxy_pressure_H1_D2"].iat[0])
