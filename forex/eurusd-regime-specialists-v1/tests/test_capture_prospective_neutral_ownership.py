from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from capture_prospective_neutral_ownership import (
    build_h1_bar,
    capture_ownership,
    classify_ownership_from_h1,
    decode_ticks,
    official_tick_url,
    ownership_capture_ready,
    required_hours,
    synthetic_dry_run,
    write_immutable,
)


def _payload(hour: str, *, initial: float, multiplier: float) -> bytes:
    start = pd.Timestamp(hour)
    return json.dumps(
        {
            "timestamp": int(start.timestamp() * 1000),
            "multiplier": multiplier,
            "bid": initial,
            "ask": initial + 10 * multiplier,
            "times": [0, 300000, 300000],
            "bids": [0, 1, -1],
            "asks": [0, 1, -1],
            "bidVolumes": [1.0, 1.0, 1.0],
            "askVolumes": [1.0, 1.0, 1.0],
        }
    ).encode("utf-8")


def _bars(day: str, rows: int = 600) -> dict[str, pd.DataFrame]:
    state_time = pd.Timestamp(day) - pd.Timedelta(hours=1)
    index = pd.date_range(
        state_time - pd.Timedelta(hours=rows - 1),
        state_time,
        freq="h",
    )
    angle = np.linspace(0.0, 30.0 * math.pi, rows)
    offsets = {
        "EURUSD": 1.1,
        "GBPUSD": 1.3,
        "USDJPY": 150.0,
        "DOLLARIDXUSD": 100.0,
        "USTBONDTRUSD": 110.0,
    }
    scales = {
        "EURUSD": 0.002,
        "GBPUSD": 0.002,
        "USDJPY": 0.2,
        "DOLLARIDXUSD": 0.2,
        "USTBONDTRUSD": 0.2,
    }
    result = {}
    for symbol, offset in offsets.items():
        close = offset + scales[symbol] * np.sin(angle)
        width = scales[symbol] * 0.2
        result[symbol] = pd.DataFrame(
            {
                "open": close,
                "high": close + width,
                "low": close - width,
                "close": close,
            },
            index=index,
        )
    return result


def _hashes() -> dict[str, str]:
    return {
        "EURUSD": "1" * 64,
        "GBPUSD": "2" * 64,
        "USDJPY": "3" * 64,
        "DOLLARIDXUSD": "4" * 64,
        "USTBONDTRUSD": "5" * 64,
    }


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            default=lambda item: (
                item.isoformat()
                if isinstance(item, pd.Timestamp)
                else str(item)
            ),
        )
        + "\n"
    ).encode()


def _write_existing_ownership(tmp_path: Path) -> tuple[Path, Path]:
    record, _ = classify_ownership_from_h1(
        _bars("2026-08-07T00:00:00Z"),
        "2026-08-07",
        "2026-08-07T00:02:00Z",
        _hashes(),
    )
    record_bytes = _json_bytes(record)
    record_hash = hashlib.sha256(record_bytes).hexdigest()
    evidence_hash = record["ownership_evidence_sha256"]
    record_relative = (
        "records/2026-08-07_" + evidence_hash[:16] + ".json"
    )
    record_path = tmp_path / record_relative
    record_path.parent.mkdir(parents=True)
    record_path.write_bytes(record_bytes)
    manifest = {
        "eligible_date": "2026-08-07T00:00:00+00:00",
        "ownership_record": {
            "relative_path": record_relative,
            "sha256": record_hash,
            "ownership_evidence_sha256": evidence_hash,
            "is_neutral": record["is_neutral"],
        },
    }
    manifest_bytes = _json_bytes(manifest)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_path = (
        tmp_path
        / "manifests"
        / f"MANIFEST_2026-08-07_{manifest_hash[:16]}.json"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_bytes(manifest_bytes)
    return record_path, manifest_path


def test_all_five_official_urls_use_frozen_source_codes() -> None:
    hour = "2026-07-27T12:00:00Z"
    assert "/EUR-USD/" in official_tick_url("EURUSD", hour)
    assert "/GBP-USD/" in official_tick_url("GBPUSD", hour)
    assert "/USD-JPY/" in official_tick_url("USDJPY", hour)
    assert "/DOLLAR.IDX-USD/" in official_tick_url(
        "DOLLARIDXUSD", hour
    )
    assert "/USTBOND.TR-USD/" in official_tick_url(
        "USTBONDTRUSD", hour
    )


def test_decoder_and_h1_bar_respect_symbol_scale_and_completion() -> None:
    hour = "2026-07-27T12:00:00Z"
    ticks = decode_ticks(
        _payload(hour, initial=150.000, multiplier=0.001),
        "USDJPY",
        hour,
    )
    assert ticks["bid"].tolist() == [150.0, 150.001, 150.0]
    bar = build_h1_bar(
        ticks,
        hour,
        "2026-07-27T13:00:00Z",
    )
    assert len(bar) == 1
    with pytest.raises(ValueError, match="before bar completion"):
        build_h1_bar(
            ticks,
            hour,
            "2026-07-27T12:59:59Z",
        )


def test_required_window_ends_at_prior_23h_and_has_sixty_days() -> None:
    hours = required_hours(
        "2026-08-07",
        lookback_calendar_days=60,
    )
    assert hours[0] == pd.Timestamp("2026-06-08T00:00:00Z")
    assert hours[-1] == pd.Timestamp("2026-08-06T23:00:00Z")
    assert len(hours) == 60 * 24


def test_early_capture_makes_no_network_request(tmp_path) -> None:
    calls = []

    def fetcher(symbol, hour):
        calls.append((symbol, hour))
        raise AssertionError("Fetcher must not be called")

    result = capture_ownership(
        "2026-08-07",
        tmp_path,
        now_utc="2026-08-07T00:00:59Z",
        fetcher=fetcher,
    )
    assert result["status"] == "WAITING_FOR_PRIOR_H1_COMPLETION"
    assert result["network_requests_made"] == 0
    assert calls == []
    assert ownership_capture_ready(
        "2026-08-07",
        "2026-08-07T00:01:00Z",
    )


def test_classifier_uses_latest_common_state_and_finite_lookbacks() -> None:
    bars = _bars("2026-08-07T00:00:00Z")
    record, evidence = classify_ownership_from_h1(
        bars,
        "2026-08-07",
        "2026-08-07T00:02:00Z",
        _hashes(),
    )
    assert record["state_timestamp_utc"] == pd.Timestamp(
        "2026-08-06T23:00:00Z"
    )
    assert record["state_staleness_hours"] == 0.0
    assert evidence["common_h1_rows_through_state"] == 600
    assert len(evidence["terminal_features_sha256"]) == 64
    assert "oracle_member" not in record
    assert "outcome_r" not in record


def test_classifier_uses_backward_asof_when_latest_markets_end_early() -> None:
    bars = {
        symbol: frame.iloc[:-3]
        for symbol, frame in _bars("2026-08-07T00:00:00Z").items()
    }
    record, evidence = classify_ownership_from_h1(
        bars,
        "2026-08-07",
        "2026-08-07T00:02:00Z",
        _hashes(),
    )
    expected = pd.Timestamp("2026-08-06T20:00:00Z")
    assert record["state_timestamp_utc"] == expected
    assert record["state_staleness_hours"] == 3.0
    assert evidence["state_timestamp_utc"] == expected
    assert evidence["state_staleness_hours"] == 3.0


def test_future_bar_cannot_change_prior_23h_ownership() -> None:
    bars = _bars("2026-08-07T00:00:00Z")
    first, _ = classify_ownership_from_h1(
        bars,
        "2026-08-07",
        "2026-08-07T00:02:00Z",
        _hashes(),
    )
    future_time = pd.Timestamp("2026-08-07T00:00:00Z")
    altered = {}
    for symbol, frame in bars.items():
        future = pd.DataFrame(
            {
                "open": [9999.0],
                "high": [10000.0],
                "low": [1.0],
                "close": [9999.0],
            },
            index=[future_time],
        )
        altered[symbol] = pd.concat([frame, future])
    second, _ = classify_ownership_from_h1(
        altered,
        "2026-08-07",
        "2026-08-07T00:02:00Z",
        _hashes(),
    )
    assert first["ownership_evidence_sha256"] == (
        second["ownership_evidence_sha256"]
    )


def test_insufficient_common_history_stays_cash_by_error() -> None:
    with pytest.raises(RuntimeError, match="Insufficient common H1"):
        classify_ownership_from_h1(
            _bars("2026-08-07T00:00:00Z", rows=519),
            "2026-08-07",
            "2026-08-07T00:02:00Z",
            _hashes(),
        )


def test_synthetic_dry_run_is_network_free() -> None:
    result = synthetic_dry_run("2026-08-07")
    assert result["status"] == "SYNTHETIC_DRY_RUN_COMPLETE"
    assert result["common_h1_rows_through_state"] == 600
    assert result["network_requests_made"] == 0
    assert result["historical_pnl_loaded"] is False
    assert result["broker_action_allowed"] is False


def test_immutable_writer_rejects_changed_evidence(tmp_path) -> None:
    path = tmp_path / "record.json"
    write_immutable(path, b"first")
    write_immutable(path, b"first")
    with pytest.raises(RuntimeError, match="Refusing to overwrite"):
        write_immutable(path, b"changed")


def test_existing_record_requires_and_returns_immutable_manifest(
    tmp_path,
) -> None:
    _write_existing_ownership(tmp_path)

    def fetcher(symbol, hour):
        raise AssertionError(f"Unexpected fetch for {symbol} {hour}")

    result = capture_ownership(
        "2026-08-07",
        tmp_path,
        now_utc="2026-08-07T00:02:00Z",
        fetcher=fetcher,
    )
    assert result["network_requests_made"] == 0
    assert result["manifest_relative_path"].startswith("manifests/")


def test_tampered_or_duplicate_existing_record_is_rejected(tmp_path) -> None:
    record_path, _ = _write_existing_ownership(tmp_path)
    record = json.loads(record_path.read_text())
    record["state_staleness_hours"] = 999.0
    record_path.write_bytes(_json_bytes(record))
    with pytest.raises(ValueError, match="evidence hash mismatch"):
        capture_ownership(
            "2026-08-07",
            tmp_path,
            now_utc="2026-08-07T00:02:00Z",
        )

    record_path.write_bytes(
        _json_bytes(
            classify_ownership_from_h1(
                _bars("2026-08-07T00:00:00Z"),
                "2026-08-07",
                "2026-08-07T00:02:00Z",
                _hashes(),
            )[0]
        )
    )
    duplicate = record_path.with_name("2026-08-07_duplicate.json")
    duplicate.write_bytes(record_path.read_bytes())
    with pytest.raises(RuntimeError, match="Multiple ownership records"):
        capture_ownership(
            "2026-08-07",
            tmp_path,
            now_utc="2026-08-07T00:02:00Z",
        )
