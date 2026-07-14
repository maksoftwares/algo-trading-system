from __future__ import annotations

import json
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dukascopy_tick_foundation.foundation import (
    CLASSIFICATIONS,
    END_UTC,
    INSTRUMENTS,
    NORMALIZED_COLUMNS,
    OFFICIAL_ORIGIN,
    PHASE,
    PRICE_BASES,
    START_UTC,
    STORAGE_ENV,
    TIMEFRAMES_MINUTES,
    CorruptRawFileError,
    FoundationError,
    SourceValidationError,
    StorageConfigurationError,
    Tick,
    acquire_hour,
    acquire_month,
    aggregate_bars,
    assert_no_forbidden_output_fields,
    bar_schema,
    build_source_contract,
    canonical_json_bytes,
    classify,
    compare_run_hashes,
    decode_payload,
    freeze_raw_month,
    hours_in_month,
    month_keys,
    normalize_month,
    normalized_schema,
    official_instrument_url,
    official_tick_url,
    raw_hour_path,
    resolve_storage_root,
    sha256_bytes,
    sha256_file,
    storage_preflight,
    timeframe_start_ms,
    validate_hour_payload,
    validate_month_acquisition_manifest,
    validate_official_url,
    validate_payload_shape,
    write_csv,
    write_json,
    write_month_acquisition_manifest,
)
from dukascopy_tick_foundation.pipeline import OUTPUT_NAMES


FIXTURE = Path(__file__).parent / "fixtures" / "official-EURUSD-2024010212.json"
FIXTURE_SHA256 = "20ce8dbbc808508c1c752ead21ea1ea0250fe95253575145435d16bca6067205"
FIXTURE_HOUR = datetime(2024, 1, 2, 12, tzinfo=UTC)


def tiny_payload(hour: datetime = FIXTURE_HOUR) -> bytes:
    return canonical_json_bytes({
        "multiplier": 0.00001,
        "timestamp": int(hour.timestamp() * 1000),
        "bid": 1.1,
        "ask": 1.1002,
        "times": [100, 100],
        "bids": [0, 1],
        "asks": [0, 1],
        "bidVolumes": [1.0, 1.5],
        "askVolumes": [2.0, 2.5],
    })


@pytest.mark.parametrize("symbol", sorted(INSTRUMENTS))
def test_instrument_mapping_is_locked(symbol):
    spec = INSTRUMENTS[symbol]
    assert spec["source_code"] == f"{symbol[:3]}-{symbol[3:]}"
    assert spec["pip_size"] > 0
    assert spec["price_scale"] in {3, 5}


@pytest.mark.parametrize("symbol", sorted(INSTRUMENTS))
@pytest.mark.parametrize("hour", [0, 6, 12, 23])
def test_official_tick_url_is_calendar_exact(symbol, hour):
    value = official_tick_url(symbol, datetime(2016, 7, 1, hour, tzinfo=UTC))
    assert value == f"{OFFICIAL_ORIGIN}/ticks/{INSTRUMENTS[symbol]['source_code']}/2016/7/1/{hour}"


@pytest.mark.parametrize("symbol", sorted(INSTRUMENTS))
def test_official_instrument_url(symbol):
    assert official_instrument_url(symbol).startswith("https://jetta.dukascopy.com/v1/instruments/")


@pytest.mark.parametrize("url", [
    "https://jetta.dukascopy.com/v1/ticks/EUR-USD/2024/1/2/12",
    "https://widgets.dukascopy.com/en/historical-data-export",
    "https://www.dukascopy.com/wiki/en/development/strategy-api/historical-data/history-ticks/",
])
def test_official_urls_are_accepted(url):
    validate_official_url(url)


@pytest.mark.parametrize("url", [
    "http://jetta.dukascopy.com/v1/ticks/EUR-USD/2024/1/2/12",
    "https://example.com/dukascopy.json",
    "file:///tmp/fake.json",
    "https://dukascopy.example.com/data",
])
def test_mirror_synthetic_or_insecure_urls_are_rejected(url):
    with pytest.raises(SourceValidationError):
        validate_official_url(url)


def test_locked_period_has_exactly_120_months():
    months = month_keys()
    assert len(months) == 120
    assert months[0] == "2016-07"
    assert months[-1] == "2026-06"


@pytest.mark.parametrize("month", range(1, 13))
def test_calendar_month_partition_hours(month):
    expected = 24 * (29 if month == 2 else 30 if month in {4, 6, 9, 11} else 31)
    assert len(hours_in_month(2024, month)) == expected
    assert hours_in_month(2024, month)[0].tzinfo is UTC


@pytest.mark.parametrize("timeframe", list(TIMEFRAMES_MINUTES))
@pytest.mark.parametrize("minute", [0, 7, 59])
def test_utc_epoch_bar_alignment(timeframe, minute):
    stamp = int(datetime(2024, 1, 2, 13, minute, 42, 123000, tzinfo=UTC).timestamp() * 1000)
    start = timeframe_start_ms(stamp, timeframe)
    width = TIMEFRAMES_MINUTES[timeframe] * 60_000
    assert start % width == 0
    assert start <= stamp < start + width


@pytest.mark.parametrize("missing", ["timestamp", "multiplier", "bid", "ask", "times", "bids", "asks", "bidVolumes", "askVolumes"])
def test_payload_missing_required_field_fails(missing):
    payload = json.loads(tiny_payload())
    del payload[missing]
    with pytest.raises(SourceValidationError):
        validate_payload_shape(payload)


@pytest.mark.parametrize("array", ["times", "bids", "asks", "bidVolumes", "askVolumes"])
def test_inconsistent_source_array_fails(array):
    payload = json.loads(tiny_payload())
    payload[array].append(0)
    with pytest.raises(SourceValidationError):
        validate_payload_shape(payload)


def test_invalid_json_fails_closed():
    with pytest.raises(SourceValidationError):
        decode_payload(b"not-json", "EURUSD", "bad")


def test_official_closed_market_empty_payload_is_valid():
    payload = {
        "multiplier": 1,
        "timestamp": int(FIXTURE_HOUR.timestamp() * 1000),
        "bid": None,
        "ask": None,
        "times": [],
        "bids": [],
        "asks": [],
        "bidVolumes": [],
        "askVolumes": [],
    }
    assert decode_payload(canonical_json_bytes(payload), "EURUSD", "closed") == []
    assert validate_hour_payload(canonical_json_bytes(payload), "EURUSD", FIXTURE_HOUR, "closed") == 0


def test_negative_spread_fails_closed():
    payload = json.loads(tiny_payload())
    payload["ask"] = 1.0
    with pytest.raises(SourceValidationError):
        decode_payload(canonical_json_bytes(payload), "EURUSD", "bad")


def test_backwards_timestamp_fails_closed():
    payload = json.loads(tiny_payload())
    payload["times"] = [100, -200]
    with pytest.raises(SourceValidationError):
        decode_payload(canonical_json_bytes(payload), "EURUSD", "bad")


def test_out_of_hour_timestamp_fails_closed():
    payload = json.loads(tiny_payload())
    payload["times"] = [3_600_000, 1]
    with pytest.raises(SourceValidationError):
        validate_hour_payload(canonical_json_bytes(payload), "EURUSD", FIXTURE_HOUR, "bad")


def test_official_fixture_known_hash():
    assert FIXTURE.is_file()
    assert sha256_file(FIXTURE) == FIXTURE_SHA256


def test_official_fixture_decodes_expected_tick_count():
    ticks = decode_payload(FIXTURE.read_bytes(), "EURUSD", "official-fixture")
    assert len(ticks) == 5056
    assert ticks[0].timestamp_ms >= int(FIXTURE_HOUR.timestamp() * 1000)
    assert ticks[-1].timestamp_ms < int(FIXTURE_HOUR.timestamp() * 1000) + 3_600_000
    assert all(tick.ask >= tick.bid > 0 for tick in ticks)


def test_source_order_and_identifiers_preserved():
    ticks = decode_payload(tiny_payload(), "EURUSD", "fixture-id")
    assert [tick.source_row_index for tick in ticks] == [0, 1]
    assert all(tick.source_file_id == "fixture-id" for tick in ticks)
    assert ticks[0].timestamp_ms < ticks[1].timestamp_ms


def test_same_timestamp_rows_are_preserved():
    payload = json.loads(tiny_payload())
    payload["times"] = [100, 0]
    ticks = decode_payload(canonical_json_bytes(payload), "EURUSD", "same-time")
    assert len(ticks) == 2
    assert ticks[0].timestamp_ms == ticks[1].timestamp_ms


def test_storage_env_is_required(tmp_path):
    with pytest.raises(StorageConfigurationError):
        resolve_storage_root({}, tmp_path)


def test_storage_must_be_external(tmp_path):
    lane = tmp_path / "lane"
    lane.mkdir()
    with pytest.raises(StorageConfigurationError):
        resolve_storage_root({STORAGE_ENV: str(lane / "bulk")}, lane)


def test_external_storage_is_created(tmp_path):
    lane = tmp_path / "lane"
    lane.mkdir()
    root = resolve_storage_root({STORAGE_ENV: str(tmp_path / "external")}, lane)
    assert root.is_dir()


def test_storage_preflight_uses_one_point_five_headroom(tmp_path):
    report = storage_preflight(tmp_path, 1000)
    assert report["required_free_bytes"] == 1500
    assert isinstance(report["passes"], bool)


def test_retry_occurs_exactly_once_then_succeeds(tmp_path):
    calls = []
    def fetcher(url, timeout):
        calls.append(url)
        return (b"broken" if len(calls) == 1 else tiny_payload(), {}, 200)
    row = acquire_hour(tmp_path, "EURUSD", FIXTURE_HOUR, fetcher=fetcher)
    assert row["status"] == "DOWNLOADED_VALID"
    assert row["attempts"] == 2
    assert len(calls) == 2
    assert not path_with_part_suffix(tmp_path, "EURUSD", FIXTURE_HOUR).exists()


def path_with_part_suffix(root, symbol, hour):
    return raw_hour_path(root, symbol, hour).with_suffix(".json.part")


def test_retry_stops_after_two_attempts(tmp_path):
    calls = []
    def fetcher(url, timeout):
        calls.append(url)
        return b"broken", {}, 200
    row = acquire_hour(tmp_path, "EURUSD", FIXTURE_HOUR, fetcher=fetcher)
    assert row["status"] == "FAILED_AFTER_ONE_RETRY"
    assert row["attempts"] == 2
    assert len(calls) == 2


def test_resumable_valid_raw_file_avoids_network(tmp_path):
    path = raw_hour_path(tmp_path, "EURUSD", FIXTURE_HOUR)
    path.parent.mkdir(parents=True)
    path.write_bytes(tiny_payload())
    def fail_fetch(url, timeout):
        raise AssertionError("network should not be called")
    row = acquire_hour(tmp_path, "EURUSD", FIXTURE_HOUR, fetcher=fail_fetch)
    assert row["status"] == "RESUMED_VALID"
    assert row["attempts"] == 0


@pytest.mark.parametrize("concurrency", [0, 5, 99])
def test_concurrency_above_locked_bound_rejected(tmp_path, concurrency):
    with pytest.raises(ValueError):
        acquire_month(tmp_path, "EURUSD", 2016, 7, concurrency=concurrency)


def test_raw_freeze_manifest_marks_incomplete_without_faking_completeness(tmp_path):
    path = raw_hour_path(tmp_path, "EURUSD", datetime(2016, 7, 1, tzinfo=UTC))
    path.parent.mkdir(parents=True)
    path.write_bytes(tiny_payload(datetime(2016, 7, 1, tzinfo=UTC)))
    manifest = freeze_raw_month(tmp_path, "EURUSD", 2016, 7)
    assert manifest["frozen"] is True
    assert manifest["complete"] is False
    assert manifest["observed_hour_files"] == 1
    assert path.stat().st_mode & stat.S_IWRITE == 0
    second = freeze_raw_month(tmp_path, "EURUSD", 2016, 7)
    assert second == manifest


@pytest.mark.parametrize("basis", PRICE_BASES)
def test_bar_ohlc_uses_selected_price_basis(basis):
    ticks = decode_payload(tiny_payload(), "EURUSD", "bar")
    bars = aggregate_bars(ticks, "M1", basis)
    values = [tick.bid if basis == "Bid" else tick.ask if basis == "Ask" else (tick.bid + tick.ask) / 2 for tick in ticks]
    assert bars[0]["open"] == values[0]
    assert bars[0]["close"] == values[-1]
    assert bars[0]["high"] == max(values)
    assert bars[0]["low"] == min(values)
    assert bars[0]["tick_count"] == 2


def test_empty_tick_sequence_produces_no_bars():
    assert aggregate_bars([], "H1", "Mid") == []


def test_unknown_price_basis_rejected():
    with pytest.raises(ValueError):
        aggregate_bars(decode_payload(tiny_payload(), "EURUSD", "bar"), "M1", "Last")


@pytest.mark.parametrize("source_ok,integrity_bad,complete,expected,deterministic,answer", [
    (False, False, 0, 480, True, "INVALID"),
    (True, True, 4, 480, True, "INVALID"),
    (True, False, 4, 480, False, "INVALID"),
    (True, False, 4, 480, True, "PARTIAL_NOT_READY"),
    (True, False, 479, 480, True, "PARTIAL_NOT_READY"),
    (True, False, 480, 480, True, "READY"),
])
def test_classification_precedence(source_ok, integrity_bad, complete, expected, deterministic, answer):
    assert classify(source_ok, integrity_bad, complete, expected, deterministic) == answer
    assert answer in CLASSIFICATIONS


def test_normalized_schema_is_locked():
    assert tuple(normalized_schema().names) == NORMALIZED_COLUMNS


def test_bar_schema_is_utc_millisecond():
    schema = bar_schema()
    assert schema.names == ["timestamp_utc", "timestamp_ms", "open", "high", "low", "close", "volume", "tick_count"]
    assert "timestamp[ms, tz=UTC]" in str(schema.field("timestamp_utc").type)


def test_tiny_normalization_writes_zstd_parquet_and_18_bar_partitions(tmp_path):
    raw = raw_hour_path(tmp_path, "EURUSD", FIXTURE_HOUR)
    raw.parent.mkdir(parents=True)
    raw.write_bytes(tiny_payload())
    write_complete_test_manifest(tmp_path, "EURUSD", 2024, 1, raw)
    result = normalize_month(tmp_path, tmp_path / "run", "EURUSD", 2024, 1)
    assert result["partition"]["tick_count"] == 2
    assert result["partition"]["compression"] == "zstd"
    assert len(result["bars"]) == len(PRICE_BASES) * len(TIMEFRAMES_MINUTES)
    assert all(Path(tmp_path / "run" / row["path"]).is_file() for row in result["bars"])


def test_two_tiny_derivations_are_byte_identical(tmp_path):
    raw = raw_hour_path(tmp_path, "EURUSD", FIXTURE_HOUR)
    raw.parent.mkdir(parents=True)
    raw.write_bytes(tiny_payload())
    write_complete_test_manifest(tmp_path, "EURUSD", 2024, 1, raw)
    normalize_month(tmp_path, tmp_path / "one", "EURUSD", 2024, 1)
    normalize_month(tmp_path, tmp_path / "two", "EURUSD", 2024, 1)
    report = compare_run_hashes(tmp_path / "one", tmp_path / "two")
    assert report["identical"] is True
    assert report["mismatch_count"] == 0
    assert report["file_count_run_one"] == 19


def write_complete_test_manifest(root, symbol, year, month, populated_path):
    rows = []
    for hour in hours_in_month(year, month):
        path = raw_hour_path(root, symbol, hour)
        if path != populated_path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical_json_bytes({
                "multiplier": 1, "timestamp": int(hour.timestamp() * 1000), "bid": None, "ask": None,
                "times": [], "bids": [], "asks": [], "bidVolumes": [], "askVolumes": [],
            }))
        rows.append({
            "symbol": symbol, "hour_utc": hour.isoformat(), "url": official_tick_url(symbol, hour),
            "status": "DOWNLOADED_VALID", "path": str(path.relative_to(root)).replace("\\", "/"),
            "sha256": sha256_file(path),
        })
    write_month_acquisition_manifest(root, symbol, year, month, rows)


def test_cross_symbol_acquisition_manifest_is_rejected(tmp_path):
    raw = raw_hour_path(tmp_path, "EURUSD", datetime(2024, 1, 1, tzinfo=UTC))
    raw.parent.mkdir(parents=True)
    raw.write_bytes(tiny_payload(datetime(2024, 1, 1, tzinfo=UTC)))
    write_complete_test_manifest(tmp_path, "EURUSD", 2024, 1, raw)
    manifest_path = raw.parent / "_ACQUISITION_MANIFEST.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["rows"][0]["url"] = official_tick_url("GBPUSD", datetime(2024, 1, 1, tzinfo=UTC))
    write_json(manifest_path, manifest)
    with pytest.raises(CorruptRawFileError):
        validate_month_acquisition_manifest(tmp_path, "EURUSD", 2024, 1)


def test_raw_checksum_corruption_is_rejected(tmp_path):
    raw = raw_hour_path(tmp_path, "EURUSD", datetime(2024, 1, 1, tzinfo=UTC))
    raw.parent.mkdir(parents=True)
    raw.write_bytes(tiny_payload(datetime(2024, 1, 1, tzinfo=UTC)))
    write_complete_test_manifest(tmp_path, "EURUSD", 2024, 1, raw)
    raw.write_bytes(b"corrupt")
    with pytest.raises(CorruptRawFileError):
        validate_month_acquisition_manifest(tmp_path, "EURUSD", 2024, 1)


def test_determinism_detects_corruption(tmp_path):
    one = tmp_path / "one"
    two = tmp_path / "two"
    one.mkdir(); two.mkdir()
    (one / "x.parquet").write_bytes(b"one")
    (two / "x.parquet").write_bytes(b"two")
    report = compare_run_hashes(one, two)
    assert report["identical"] is False
    assert report["mismatch_count"] == 1


def test_contract_prominent_notices_and_semantics():
    contract = build_source_contract()
    assert contract["notices"] == [
        "OFFICIAL DUKASCOPY HISTORICAL DATA",
        "BID/ASK TICK DATA FOUNDATION",
        "NO STRATEGY SCORING",
        "NO DEPLOYMENT AUTHORIZATION",
    ]
    assert contract["timezone"] == "UTC"
    assert contract["retry_policy"].startswith("one retry only")
    assert contract["concurrency_limit"] == 4


def test_output_set_is_exactly_nineteen_files():
    assert len(OUTPUT_NAMES) == 19
    assert len(set(OUTPUT_NAMES)) == 19
    assert OUTPUT_NAMES[0] == "DUKASCOPY_DATA_SOURCE_CONTRACT.md"
    assert OUTPUT_NAMES[-1] == "DUKASCOPY_FOUNDATION_RESULT.json"


def test_forbidden_top_level_research_fields_fail_closed():
    for key in ["signal", "trade", "entry", "exit", "pnl", "drawdown", "leverage", "account", "risk"]:
        with pytest.raises(FoundationError):
            assert_no_forbidden_output_fields({key: 1})


def test_data_only_audit_fields_are_allowed():
    assert_no_forbidden_output_fields({
        "phase": PHASE,
        "strategy_scoring_authorized": False,
        "broker_action_authorized": False,
        "deployment_authorized": False,
    })


def test_json_and_csv_writers_are_deterministic(tmp_path):
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    write_json(first, {"b": 2, "a": 1})
    write_json(second, {"a": 1, "b": 2})
    assert first.read_bytes() == second.read_bytes()
    csv_path = tmp_path / "x.csv"
    write_csv(csv_path, ["a", "b"], [{"b": 2, "a": 1}])
    assert csv_path.read_text(encoding="utf-8") == "a,b\n1,2\n"


def test_locked_dates_are_exact():
    assert START_UTC.isoformat() == "2016-07-01T00:00:00+00:00"
    assert END_UTC.isoformat(timespec="milliseconds") == "2026-06-30T23:59:59.999+00:00"


def test_no_bulk_storage_absolute_path_in_contract():
    serialized = json.dumps(build_source_contract())
    assert "C:\\Users\\" not in serialized
    assert STORAGE_ENV in serialized
