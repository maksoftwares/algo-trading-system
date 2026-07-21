from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from src.foundation import (
    BAR_WIDTH_MS,
    SourceTick,
    add_causal_features,
    aggregate_hour_m5,
    decode_source_payload,
    deterministic_gzip,
    expand_gzip,
    read_stored_hour,
    sha256_bytes,
    validate_curated,
    validate_hour_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def source_payload(timestamp: int = 1_000) -> bytes:
    return json.dumps(
        {
            "timestamp": timestamp,
            "multiplier": 0.001,
            "bid": 100.0,
            "ask": 100.2,
            "times": [1, 1],
            "bids": [0, 100],
            "asks": [0, 100],
            "bidVolumes": [2.0, 3.0],
            "askVolumes": [4.0, 5.0],
        },
        separators=(",", ":"),
    ).encode("ascii")


def test_gzip_is_deterministic_and_exactly_recoverable(tmp_path: Path) -> None:
    raw = source_payload()
    first = deterministic_gzip(raw)
    second = deterministic_gzip(raw)
    assert first == second
    assert expand_gzip(first) == raw
    path = tmp_path / "hour.json.gz"
    path.write_bytes(first)
    expanded, ticks = read_stored_hour(
        path,
        datetime(1970, 1, 1, tzinfo=UTC),
        price_scale=3,
        expected_source_sha256=sha256_bytes(raw),
    )
    assert expanded == raw
    assert len(ticks) == 2


def test_decoder_is_side_correct_and_rejects_crossed_quotes() -> None:
    ticks = decode_source_payload(source_payload(), price_scale=3)
    assert ticks[0].bid == pytest.approx(100.0)
    assert ticks[0].ask == pytest.approx(100.2)
    assert ticks[1].bid == pytest.approx(100.1)
    assert ticks[1].ask == pytest.approx(100.3)
    crossed = json.loads(source_payload())
    crossed["asks"] = [0, -500]
    with pytest.raises(ValueError, match="crossed"):
        decode_source_payload(json.dumps(crossed).encode(), price_scale=3)


def test_hour_validation_rejects_ticks_outside_requested_hour() -> None:
    hour = datetime(2024, 1, 1, tzinfo=UTC)
    in_hour = source_payload(int(hour.timestamp() * 1000))
    assert len(validate_hour_payload(in_hour, hour, price_scale=3)) == 2
    with pytest.raises(ValueError, match="outside"):
        validate_hour_payload(in_hour, datetime(2024, 1, 2, tzinfo=UTC), 3)


def test_m5_aggregation_is_side_correct_and_available_at_close() -> None:
    ticks = [
        SourceTick(1_000, 100.0, 100.2, 1.0, 2.0),
        SourceTick(2_000, 100.3, 100.5, 3.0, 4.0),
        SourceTick(BAR_WIDTH_MS + 1_000, 99.9, 100.1, 5.0, 6.0),
    ]
    result = aggregate_hour_m5(ticks, "spx")
    assert len(result) == 2
    assert result.loc[0, "spx_bid_open"] == pytest.approx(100.0)
    assert result.loc[0, "spx_ask_close"] == pytest.approx(100.5)
    assert result.loc[0, "spx_mid_high"] == pytest.approx(100.4)
    assert result.loc[0, "spx_bid_volume_sum"] == pytest.approx(4.0)
    assert result.loc[0, "spx_available_timestamp_ms"] == BAR_WIDTH_MS


def test_causal_returns_do_not_bridge_missing_bars() -> None:
    ticks = [
        SourceTick(1_000, 100.0, 100.2, 1.0, 1.0),
        SourceTick(BAR_WIDTH_MS + 1_000, 100.2, 100.4, 1.0, 1.0),
        SourceTick(3 * BAR_WIDTH_MS + 1_000, 100.4, 100.6, 1.0, 1.0),
    ]
    result = add_causal_features(aggregate_hour_m5(ticks, "spx"), "spx")
    assert pd.notna(result.loc[1, "spx_return_5m"])
    assert pd.isna(result.loc[2, "spx_return_5m"])


def test_curated_validation_rejects_outcomes_duplicates_and_bad_availability() -> None:
    frame = aggregate_hour_m5(
        [SourceTick(1_000, 100.0, 100.2, 1.0, 1.0)], "spx"
    )
    with pytest.raises(ValueError, match="outcome-bearing"):
        validate_curated(frame.assign(pnl=1.0), ["spx"])
    with pytest.raises(ValueError, match="duplicate"):
        validate_curated(pd.concat([frame, frame], ignore_index=True), ["spx"])
    bad = frame.copy()
    bad["spx_available_timestamp_ms"] -= 1
    with pytest.raises(ValueError, match="noncausal"):
        validate_curated(bad, ["spx"])


def test_config_is_source_only_and_uses_exact_official_codes() -> None:
    config = json.loads(
        (ROOT / "config" / "dukascopy_growth_risk_pulse_v1.json").read_text()
    )
    assert config["official_origin"] == "https://jetta.dukascopy.com/v1"
    assert {item["source_code"] for item in config["instruments"]} == {
        "USA500.IDX-USD",
        "COPPER.CMD-USD",
        "USD-CNH",
    }
    assert config["paid_data_authorized"] is False
    assert config["databento_use_authorized"] is False
    assert config["xau_outcomes_authorized"] is False
    assert config["strategy_scoring_authorized"] is False
