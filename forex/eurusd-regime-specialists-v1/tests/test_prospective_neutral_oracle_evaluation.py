from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import capture_prospective_neutral_oracle_day as capture_module
from capture_prospective_neutral_oracle_day import capture_oracle_date
from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    build_neutral_ownership_record,
)
from eurusd_regime_specialists.prospective_neutral_oracle_evaluation import (
    build_daily_perfect_oracle,
    load_next_day_context,
    oracle_capture_ready,
    required_oracle_hours,
)
from eurusd_regime_specialists.retrospective_overfit import (
    build_full_calendar_perfect_oracle,
)

ORACLE_DATE = pd.Timestamp("2026-08-03T00:00:00Z")
OBSERVED = pd.Timestamp("2026-08-04T12:01:01Z")
SYMBOLS = (
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "DOLLARIDXUSD",
    "USTBONDTRUSD",
)


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            default=lambda item: (
                item.isoformat() if isinstance(item, pd.Timestamp) else str(item)
            ),
        )
        + "\n"
    ).encode()


def _write(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _neutral_state(
    start: str = "2026-08-01T00:00:00Z",
    periods: int = 120,
) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="h")
    index.name = "timestamp_utc"
    return pd.DataFrame(
        {
            "direction": "NEUTRAL",
            "shock": False,
            "DXY_compressed": False,
            "EURUSD_compressed": False,
        },
        index=index,
    )


def _rising_m5() -> pd.DataFrame:
    index = pd.date_range(
        ORACLE_DATE,
        ORACLE_DATE + pd.Timedelta(hours=60) - pd.Timedelta(minutes=5),
        freq="5min",
    )
    bid = 1.1000 + np.arange(len(index)) * 0.00005
    frame = pd.DataFrame(
        {
            "bid_open": bid,
            "bid_high": bid + 0.00002,
            "bid_low": bid - 0.00002,
            "bid_close": bid,
            "ask_open": bid + 0.00010,
            "ask_high": bid + 0.00012,
            "ask_low": bid + 0.00008,
            "ask_close": bid + 0.00010,
        },
        index=index,
    )
    frame.index.name = "timestamp_utc"
    return frame


def _hour_payload(hour: pd.Timestamp) -> bytes:
    ordinal = int((hour - ORACLE_DATE) / pd.Timedelta(hours=1))
    initial_bid = 1.1000 + ordinal * 0.00060
    return json.dumps(
        {
            "timestamp": int(hour.timestamp() * 1000),
            "multiplier": 0.00001,
            "bid": initial_bid,
            "ask": initial_bid + 0.00010,
            "times": [0, *([300000] * 11)],
            "bids": [0, *([5] * 11)],
            "asks": [0, *([5] * 11)],
            "bidVolumes": [1.0] * 12,
            "askVolumes": [1.0] * 12,
        }
    ).encode()


def _fetcher(calls: list[tuple[str, pd.Timestamp]]):
    def fetch(symbol: str, hour: pd.Timestamp):
        calls.append((symbol, hour))
        return _hour_payload(hour), {
            "symbol": symbol,
            "hour_utc": hour,
            "observed_at_utc": OBSERVED,
            "source_url": f"https://example.invalid/{hour:%Y%m%d%H}",
        }

    return fetch


def _context_payload() -> tuple[pd.DataFrame, dict[str, object]]:
    return _neutral_state(), {
        "eligible_date": ORACLE_DATE + pd.Timedelta(days=1),
        "ownership_observed_at_utc": pd.Timestamp("2026-08-04T00:02:00Z"),
        "ownership_manifest_relative_path": (
            "manifests/MANIFEST_2026-08-04_context.json"
        ),
        "ownership_manifest_sha256": "a" * 64,
        "ownership_record_relative_path": ("records/2026-08-04_context.json"),
        "ownership_record_sha256": "b" * 64,
        "ownership_evidence_sha256": "c" * 64,
    }


def _ownership_bars() -> dict[str, pd.DataFrame]:
    rows = 600
    state_time = pd.Timestamp("2026-08-03T23:00:00Z")
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
    result: dict[str, pd.DataFrame] = {}
    for symbol in SYMBOLS:
        close = offsets[symbol] + scales[symbol] * np.sin(angle)
        width = scales[symbol] * 0.2
        frame = pd.DataFrame(
            {
                "open": close,
                "high": close + width,
                "low": close - width,
                "close": close,
            },
            index=index,
        )
        frame.index.name = "timestamp_utc"
        result[symbol] = frame
    return result


def _write_next_day_context(root: Path) -> Path:
    eligible = ORACLE_DATE + pd.Timedelta(days=1)
    bars = _ownership_bars()
    inventory: dict[str, dict[str, object]] = {}
    source_hashes: dict[str, str] = {}
    for position, symbol in enumerate(SYMBOLS, start=1):
        relative = Path("normalized") / f"{symbol}.parquet"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        bars[symbol].to_parquet(path, compression="zstd")
        normalized_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        source_hashes[symbol] = str(position) * 64
        inventory[symbol] = {
            "requested_hours": len(bars[symbol]),
            "populated_h1_rows": len(bars[symbol]),
            "first_h1_utc": bars[symbol].index.min(),
            "last_h1_utc": bars[symbol].index.max(),
            "source_chain_sha256": source_hashes[symbol],
            "normalized_relative_path": relative.as_posix(),
            "normalized_sha256": normalized_hash,
        }
    record = build_neutral_ownership_record(
        eligible_date=eligible,
        state_timestamp_utc=eligible - pd.Timedelta(hours=1),
        ownership_observed_at_utc=eligible + pd.Timedelta(minutes=2),
        direction="NEUTRAL",
        shock=False,
        dxy_compressed=False,
        eurusd_compressed=False,
        source_hashes=source_hashes,
    )
    record["classifier_terminal_features_sha256"] = "f" * 64
    evidence_hash = record["ownership_evidence_sha256"]
    record_relative = f"records/{eligible:%Y-%m-%d}_{evidence_hash[:16]}.json"
    record_hash = _write(root / record_relative, _json_bytes(record))
    manifest = {
        "schema_version": "eurusd_prospective_neutral_ownership_v1",
        "eligible_date": eligible,
        "ownership_observed_at_utc": eligible + pd.Timedelta(minutes=2),
        "source_inventory": inventory,
        "ownership_record": {
            "relative_path": record_relative,
            "sha256": record_hash,
            "ownership_evidence_sha256": evidence_hash,
            "is_neutral": True,
        },
        "historical_pnl_loaded": False,
        "broker_action_allowed": False,
    }
    manifest_payload = _json_bytes(manifest)
    manifest_hash = hashlib.sha256(manifest_payload).hexdigest()
    manifest_path = (
        root / "manifests" / f"MANIFEST_{eligible:%Y-%m-%d}_{manifest_hash[:16]}.json"
    )
    _write(manifest_path, manifest_payload)
    return manifest_path


def test_oracle_known_time_and_required_window_are_frozen() -> None:
    assert not oracle_capture_ready(ORACLE_DATE, "2026-08-04T12:00:59Z")
    assert oracle_capture_ready(ORACLE_DATE, "2026-08-04T12:01:00Z")
    hours = required_oracle_hours(ORACLE_DATE)
    assert len(hours) == 36
    assert hours[0] == ORACLE_DATE
    assert hours[-1] == pd.Timestamp("2026-08-04T11:00:00Z")


def test_daily_producer_has_exact_historical_oracle_parity() -> None:
    market = _rising_m5()
    state = _neutral_state()
    historical = build_full_calendar_perfect_oracle(
        market,
        state,
        {
            "exit": {
                "minimum_retail_spread_pips": 0.7,
                "extra_slippage_pips_per_side": 0.1,
            }
        },
    )
    daily, census = build_daily_perfect_oracle(market, state, ORACLE_DATE)
    expected = historical[historical["oracle_date"].eq("2026-08-03")].reset_index(
        drop=True
    )
    pd.testing.assert_frame_equal(
        daily.reset_index(drop=True),
        expected,
        check_dtype=False,
    )
    assert census["status"] == "ORACLE_COMPLETE"
    assert census["winner_count"] == 4
    assert census["neutral_winners"] == 4


def test_insufficient_future_path_is_recorded_unavailable() -> None:
    market = _rising_m5().iloc[:1]
    oracle, census = build_daily_perfect_oracle(market, _neutral_state(), ORACLE_DATE)
    assert oracle.empty
    assert census["status"] == ("ORACLE_UNAVAILABLE_INSUFFICIENT_FOUR_WINNERS")
    assert census["winner_count"] == 0


def test_capture_waits_without_network_before_safe_known_time(
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, pd.Timestamp]] = []
    result = capture_oracle_date(
        ORACLE_DATE,
        tmp_path / "oracle",
        tmp_path / "ownership",
        now_utc="2026-08-04T12:00:59Z",
        fetcher=_fetcher(calls),
    )
    assert result["status"] == "WAITING_FOR_ORACLE_DAY_COMPLETION"
    assert result["network_request_made"] is False
    assert calls == []


def test_capture_requires_next_day_context_before_network(
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, pd.Timestamp]] = []
    result = capture_oracle_date(
        ORACLE_DATE,
        tmp_path / "oracle",
        tmp_path / "ownership",
        now_utc=OBSERVED,
        fetcher=_fetcher(calls),
    )
    assert result["status"] == ("WAITING_FOR_NEXT_DAY_OWNERSHIP_CONTEXT")
    assert result["network_request_made"] is False
    assert calls == []


def test_next_day_context_is_hash_checked_and_rebuilt(
    tmp_path: Path,
) -> None:
    manifest_path = _write_next_day_context(tmp_path)
    state, context = load_next_day_context(tmp_path, ORACLE_DATE)
    assert not state.empty
    assert state.index.max() <= pd.Timestamp("2026-08-03T23:00:00Z")
    assert context["eligible_date"] == pd.Timestamp("2026-08-04T00:00:00Z")
    assert context["ownership_observed_at_utc"] == pd.Timestamp("2026-08-04T00:02:00Z")

    manifest = json.loads(manifest_path.read_text())
    first = manifest["source_inventory"]["EURUSD"]
    path = tmp_path / first["normalized_relative_path"]
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="hash drift"):
        load_next_day_context(tmp_path, ORACLE_DATE)


def test_complete_capture_is_append_only_idempotent_and_tamper_evident(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        capture_module,
        "load_next_day_context",
        lambda ownership_root, oracle_date: _context_payload(),
    )
    calls: list[tuple[str, pd.Timestamp]] = []
    oracle_root = tmp_path / "oracle"
    result = capture_oracle_date(
        ORACLE_DATE,
        oracle_root,
        tmp_path / "ownership",
        now_utc=OBSERVED,
        fetcher=_fetcher(calls),
    )
    assert result["status"] == "ORACLE_DATE_COMPLETE"
    assert result["oracle_rows"] == 4
    assert result["neutral_oracle_rows"] == 4
    assert result["oracle_label_known_time_utc"] == OBSERVED.isoformat()
    assert len(calls) == 36
    assert result["historical_pnl_loaded"] is False
    assert result["broker_action_allowed"] is False

    second_calls: list[tuple[str, pd.Timestamp]] = []
    second = capture_oracle_date(
        ORACLE_DATE,
        oracle_root,
        tmp_path / "ownership",
        now_utc=OBSERVED,
        fetcher=_fetcher(second_calls),
    )
    assert second["manifest_sha256"] == result["manifest_sha256"]
    assert second["network_request_made"] is False
    assert second_calls == []

    manifest = json.loads((oracle_root / result["manifest_relative_path"]).read_text())
    labels_path = oracle_root / manifest["oracle_labels"]["relative_path"]
    labels = pd.read_parquet(labels_path)
    labels.loc[0, "side"] = "SHORT"
    labels.to_parquet(labels_path, index=False)
    with pytest.raises(RuntimeError, match="hash drift"):
        capture_oracle_date(
            ORACLE_DATE,
            oracle_root,
            tmp_path / "ownership",
            now_utc=OBSERVED,
            fetcher=_fetcher([]),
        )
