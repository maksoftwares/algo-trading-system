from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import urllib.request
from collections.abc import Callable, Mapping
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.ensemble import load_ensemble_config
from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    build_neutral_ownership_record,
    verify_neutral_ownership_record,
)
from eurusd_regime_specialists.research import (
    PACKAGE_ROOT,
    build_state_table,
    sha256_file,
)


CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_ownership_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_OWNERSHIP_PREREG_2026_07_28.sha256.json"
)
DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-macro-crossasset-agreement-v1/ownership"
)
USER_AGENT = "Mozilla/5.0 prospective-eurusd-neutral-research/1.0"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_prospective_start")
        is not True
    ):
        raise RuntimeError("Prospective Neutral ownership is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Prospective ownership lock mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for section, path_key, hash_key in (
        ("execution_contract", "path", "sha256"),
        ("classifier_contract", "path", "sha256"),
        (
            "classifier_contract",
            "source_path",
            "source_sha256",
        ),
    ):
        reference = cfg[section]
        if (
            sha256_file(PACKAGE_ROOT / reference[path_key])
            != reference[hash_key]
        ):
            raise RuntimeError(
                f"Prospective ownership reference drift: {path_key}"
            )
    return checked


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return timestamp.tz_convert("UTC").as_unit("ns")


def _day(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    if timestamp != timestamp.floor("D"):
        raise ValueError("Eligible date must be UTC midnight")
    return timestamp.as_unit("ns")


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {
            str(key): _serialize(item) for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise RuntimeError(
                f"Refusing to overwrite ownership evidence: {path}"
            )


def ownership_capture_ready(
    eligible_date: Any,
    observed_at_utc: Any,
    *,
    minimum_lag_seconds: int = 60,
) -> bool:
    day = _day(eligible_date)
    observed = _utc(observed_at_utc)
    return observed >= day + pd.Timedelta(
        seconds=minimum_lag_seconds
    )


def required_hours(
    eligible_date: Any,
    *,
    lookback_calendar_days: int,
) -> list[pd.Timestamp]:
    day = _day(eligible_date)
    start = day - pd.Timedelta(days=lookback_calendar_days)
    return list(
        pd.date_range(
            start,
            day - pd.Timedelta(hours=1),
            freq="h",
        )
    )


def official_tick_url(symbol: str, hour_utc: Any) -> str:
    cfg = load_config()
    symbols = cfg["provider"]["symbols"]
    if symbol not in symbols:
        raise ValueError(f"Unsupported ownership symbol: {symbol}")
    hour = _utc(hour_utc)
    code = symbols[symbol]["source_code"]
    origin = cfg["provider"]["official_origin"]
    return (
        f"{origin}/ticks/{code}/"
        f"{hour.year}/{hour.month}/{hour.day}/{hour.hour}"
    )


def fetch_hour(
    symbol: str,
    hour_utc: pd.Timestamp,
) -> tuple[bytes, dict[str, Any]]:
    hour = _utc(hour_utc)
    started = pd.Timestamp.now(tz="UTC").as_unit("ns")
    request = urllib.request.Request(
        official_tick_url(symbol, hour),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
        date_header = response.headers.get("Date")
        http_date = (
            _utc(parsedate_to_datetime(date_header))
            if date_header
            else None
        )
        response_headers = {
            "date": date_header,
            "etag": response.headers.get("ETag"),
            "cache_control": response.headers.get("Cache-Control"),
        }
    finished = pd.Timestamp.now(tz="UTC").as_unit("ns")
    observed = max(
        value for value in (finished, http_date) if value is not None
    )
    return payload, {
        "symbol": symbol,
        "hour_utc": hour,
        "url": request.full_url,
        "request_started_utc": started,
        "request_finished_utc": finished,
        "http_date_utc": http_date,
        "observed_at_utc": observed,
        "response_headers": response_headers,
    }


def _round_price(value: float, scale: int) -> float:
    factor = 10**scale
    return math.floor(value * factor + 0.5 + 1e-9) / factor


def decode_ticks(
    payload_bytes: bytes,
    symbol: str,
    hour_utc: Any,
) -> pd.DataFrame:
    cfg = load_config()
    symbols = cfg["provider"]["symbols"]
    if symbol not in symbols:
        raise ValueError(f"Unsupported ownership symbol: {symbol}")
    payload = json.loads(payload_bytes)
    required = (
        "timestamp",
        "multiplier",
        "bid",
        "ask",
        "times",
        "bids",
        "asks",
        "bidVolumes",
        "askVolumes",
    )
    if not isinstance(payload, dict) or any(
        name not in payload for name in required
    ):
        raise RuntimeError("Dukascopy ownership payload schema changed")
    arrays = (
        payload["times"],
        payload["bids"],
        payload["asks"],
        payload["bidVolumes"],
        payload["askVolumes"],
    )
    if any(not isinstance(value, list) for value in arrays):
        raise RuntimeError("Dukascopy ownership arrays are invalid")
    if len({len(value) for value in arrays}) != 1:
        raise RuntimeError("Dukascopy ownership arrays are inconsistent")
    if not arrays[0]:
        return pd.DataFrame(
            columns=["timestamp_utc", "bid", "ask", "mid"]
        )
    hour = _utc(hour_utc)
    hour_start_ms = int(hour.timestamp() * 1000)
    hour_end_ms = hour_start_ms + 3_600_000
    timestamp_ms = int(payload["timestamp"])
    multiplier = float(payload["multiplier"])
    if multiplier <= 0:
        raise RuntimeError("Dukascopy multiplier is invalid")
    bid = float(payload["bid"])
    ask = float(payload["ask"])
    scale = int(symbols[symbol]["price_scale"])
    rows: list[dict[str, Any]] = []
    previous = -1
    for index in range(len(arrays[0])):
        timestamp_ms += int(payload["times"][index])
        bid = _round_price(
            bid + float(payload["bids"][index]) * multiplier,
            scale,
        )
        ask = _round_price(
            ask + float(payload["asks"][index]) * multiplier,
            scale,
        )
        if timestamp_ms < previous:
            raise RuntimeError("Dukascopy timestamps are not monotonic")
        if not (hour_start_ms <= timestamp_ms < hour_end_ms):
            raise RuntimeError("Dukascopy tick is outside requested hour")
        if not (bid > 0 and ask >= bid):
            raise RuntimeError("Dukascopy quote is invalid")
        rows.append(
            {
                "timestamp_utc": pd.Timestamp(
                    timestamp_ms, unit="ms", tz="UTC"
                ),
                "bid": bid,
                "ask": ask,
                "mid": 0.5 * (bid + ask),
            }
        )
        previous = timestamp_ms
    return pd.DataFrame(rows)


def build_h1_bar(
    ticks: pd.DataFrame,
    hour_utc: Any,
    observed_at_utc: Any,
) -> pd.DataFrame:
    hour = _utc(hour_utc)
    observed = _utc(observed_at_utc)
    if observed < hour + pd.Timedelta(hours=1):
        raise ValueError("H1 source was observed before bar completion")
    if ticks.empty:
        return pd.DataFrame(
            columns=["open", "high", "low", "close"]
        )
    timestamps = pd.to_datetime(ticks["timestamp_utc"], utc=True)
    if timestamps.lt(hour).any() or timestamps.ge(
        hour + pd.Timedelta(hours=1)
    ).any():
        raise ValueError("Tick lies outside H1 bar")
    mid = ticks["mid"].astype(float)
    return pd.DataFrame(
        {
            "open": [float(mid.iloc[0])],
            "high": [float(mid.max())],
            "low": [float(mid.min())],
            "close": [float(mid.iloc[-1])],
        },
        index=pd.DatetimeIndex([hour], name="timestamp_utc"),
    )


def _terminal_features(
    row: pd.Series,
) -> dict[str, Any]:
    keys = ("DXY", "BOND", "EURUSD", "GBPUSD", "USDJPY")
    columns = (
        "ema_fast",
        "ema_slow",
        "tr",
        "atr",
        "shock_threshold",
        "range_12_atr",
        "compression_threshold",
    )
    result: dict[str, Any] = {}
    for key in keys:
        for column in columns:
            name = f"{key}_{column}"
            value = float(row[name])
            if not math.isfinite(value):
                raise RuntimeError(
                    f"Terminal classifier feature is not finite: {name}"
                )
            result[name] = value
        result[f"{key}_compressed"] = bool(
            row[f"{key}_compressed"]
        )
    result.update(
        {
            "direction": str(row["direction"]),
            "phase": str(row["phase"]),
            "shock": bool(row["shock"]),
            "volatility": str(row["volatility"]),
        }
    )
    return result


def classify_ownership_from_h1(
    bars_by_symbol: Mapping[str, pd.DataFrame],
    eligible_date: Any,
    ownership_observed_at_utc: Any,
    source_hashes: Mapping[str, str],
    *,
    classifier_cfg: Mapping[str, Any] | None = None,
    minimum_common_h1_rows: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    cfg = load_config()
    symbols = set(cfg["provider"]["symbols"])
    if set(bars_by_symbol) != symbols:
        raise ValueError("Ownership classifier requires all five symbols")
    day = _day(eligible_date)
    latest_allowed_state = day - pd.Timedelta(hours=1)
    classifier = (
        dict(classifier_cfg)
        if classifier_cfg is not None
        else load_ensemble_config()["classifier"]
    )
    minimum_rows = (
        int(minimum_common_h1_rows)
        if minimum_common_h1_rows is not None
        else int(
            cfg["classifier_contract"][
                "minimum_common_h1_rows_through_state"
            ]
        )
    )
    state = build_state_table(
        bars_by_symbol["DOLLARIDXUSD"],
        bars_by_symbol["USTBONDTRUSD"],
        {
            symbol: bars_by_symbol[symbol]
            for symbol in ("EURUSD", "GBPUSD", "USDJPY")
        },
        classifier,
    )
    available = state.loc[state.index <= latest_allowed_state]
    if len(available) < minimum_rows:
        raise RuntimeError(
            "Insufficient common H1 history for frozen classifier"
        )
    selected_state_time = available.index.max()
    row = state.loc[selected_state_time]
    terminal = _terminal_features(row)
    record = build_neutral_ownership_record(
        eligible_date=day,
        state_timestamp_utc=selected_state_time,
        ownership_observed_at_utc=ownership_observed_at_utc,
        direction=terminal["direction"],
        shock=terminal["shock"],
        dxy_compressed=terminal["DXY_compressed"],
        eurusd_compressed=terminal["EURUSD_compressed"],
        source_hashes=source_hashes,
    )
    terminal_bytes = json.dumps(
        _serialize(terminal),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    record["classifier_terminal_features_sha256"] = sha256_bytes(
        terminal_bytes
    )
    return record, {
        "common_h1_rows_through_state": int(len(available)),
        "first_common_h1_utc": available.index.min(),
        "last_common_h1_utc": available.index.max(),
        "state_timestamp_utc": selected_state_time,
        "state_staleness_hours": (
            latest_allowed_state - selected_state_time
        ).total_seconds()
        / 3600.0,
        "terminal_features": terminal,
        "terminal_features_sha256": record[
            "classifier_terminal_features_sha256"
        ],
    }


def _cached_hour(
    output_root: Path,
    symbol: str,
    hour: pd.Timestamp,
) -> tuple[bytes, dict[str, Any]] | None:
    prefix = f"{hour:%Y%m%dT%H0000Z}_"
    matches = sorted(
        (output_root / "raw" / symbol).glob(f"{prefix}*.json")
    )
    candidates: list[tuple[pd.Timestamp, bytes, dict[str, Any]]] = []
    for raw_path in matches:
        metadata_path = (
            output_root
            / "metadata"
            / symbol
            / raw_path.name
        )
        if not metadata_path.exists():
            raise RuntimeError("Cached ownership metadata is missing")
        payload = raw_path.read_bytes()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if sha256_bytes(payload) != metadata["raw_sha256"]:
            raise RuntimeError("Cached ownership raw hash drift")
        candidates.append(
            (
                _utc(metadata["observed_at_utc"]),
                payload,
                metadata,
            )
        )
    if not candidates:
        return None
    _, payload, metadata = min(candidates, key=lambda item: item[0])
    return payload, metadata


def _source_chain(
    records: list[dict[str, Any]],
) -> str:
    digest = hashlib.sha256()
    for row in sorted(records, key=lambda item: item["hour_utc"]):
        digest.update(row["raw_relative_path"].encode("utf-8"))
        digest.update(bytes.fromhex(row["raw_sha256"]))
        digest.update(bytes.fromhex(row["metadata_sha256"]))
    return digest.hexdigest()


def _validated_existing_ownership(
    output_root: Path,
    day: pd.Timestamp,
) -> dict[str, Any] | None:
    records = sorted(
        (output_root / "records").glob(f"{day:%Y-%m-%d}_*.json")
    )
    if not records:
        return None
    if len(records) != 1:
        raise RuntimeError("Multiple ownership records exist for one date")
    record_path = records[0]
    record_payload = record_path.read_bytes()
    record = json.loads(record_payload)
    verify_neutral_ownership_record(record)
    if str(record["eligible_date"]) != day.strftime("%Y-%m-%d"):
        raise RuntimeError("Existing ownership record has the wrong date")
    evidence_hash = str(record["ownership_evidence_sha256"])
    if record_path.name != (
        f"{day:%Y-%m-%d}_{evidence_hash[:16]}.json"
    ):
        raise RuntimeError("Existing ownership record name is invalid")
    classifier_hash = str(
        record.get("classifier_terminal_features_sha256", "")
    )
    if len(classifier_hash) != 64 or any(
        character not in "0123456789abcdef"
        for character in classifier_hash
    ):
        raise RuntimeError("Existing classifier terminal hash is invalid")

    record_relative = record_path.relative_to(output_root).as_posix()
    record_hash = sha256_bytes(record_payload)
    matches: list[tuple[Path, bytes]] = []
    manifests = sorted(
        (output_root / "manifests").glob(
            f"MANIFEST_{day:%Y-%m-%d}_*.json"
        )
    )
    for manifest_path in manifests:
        manifest_payload = manifest_path.read_bytes()
        manifest_hash = sha256_bytes(manifest_payload)
        if manifest_path.name != (
            f"MANIFEST_{day:%Y-%m-%d}_{manifest_hash[:16]}.json"
        ):
            raise RuntimeError("Existing ownership manifest name is invalid")
        manifest = json.loads(manifest_payload)
        reference = manifest.get("ownership_record", {})
        if str(reference.get("relative_path")) != record_relative:
            continue
        if str(reference.get("sha256")) != record_hash:
            raise RuntimeError("Existing ownership record hash drift")
        if (
            str(reference.get("ownership_evidence_sha256"))
            != evidence_hash
        ):
            raise RuntimeError("Existing ownership evidence link drift")
        if bool(reference.get("is_neutral")) != bool(record["is_neutral"]):
            raise RuntimeError("Existing ownership status link drift")
        matches.append((manifest_path, manifest_payload))
    if len(matches) != 1:
        raise RuntimeError(
            "Existing ownership record lacks one immutable manifest"
        )
    manifest_path, manifest_payload = matches[0]
    return {
        "status": (
            "NEUTRAL_OWNED"
            if record["is_neutral"]
            else "DATE_NOT_OWNED"
        ),
        "eligible_date": day,
        "ownership_record_relative_path": record_relative,
        "ownership_record_sha256": record_hash,
        "ownership_evidence_sha256": evidence_hash,
        "manifest_relative_path": manifest_path.relative_to(
            output_root
        ).as_posix(),
        "manifest_sha256": sha256_bytes(manifest_payload),
        "network_requests_made": 0,
        "historical_pnl_loaded": False,
        "broker_action_allowed": False,
    }


def capture_ownership(
    eligible_date: Any,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    now_utc: Any | None = None,
    fetcher: Callable[
        [str, pd.Timestamp], tuple[bytes, dict[str, Any]]
    ] = fetch_hour,
) -> dict[str, Any]:
    cfg = load_config()
    day = _day(eligible_date)
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _utc(now_utc)
    )
    if day < _utc(cfg["prospective_start_utc"]):
        raise ValueError("Ownership date precedes prospective start")
    existing = _validated_existing_ownership(output_root, day)
    if existing is not None:
        return _serialize(existing)
    lag = int(
        cfg["capture"]["minimum_capture_lag_after_midnight_seconds"]
    )
    if not ownership_capture_ready(
        day, observed, minimum_lag_seconds=lag
    ):
        return {
            "status": "WAITING_FOR_PRIOR_H1_COMPLETION",
            "eligible_date": day,
            "earliest_capture_utc": day
            + pd.Timedelta(seconds=lag),
            "network_requests_made": 0,
            "broker_action_allowed": False,
        }

    hours = required_hours(
        day,
        lookback_calendar_days=int(
            cfg["capture"]["lookback_calendar_days"]
        ),
    )
    bars_by_symbol: dict[str, pd.DataFrame] = {}
    source_hashes: dict[str, str] = {}
    source_inventory: dict[str, Any] = {}
    observed_values: list[pd.Timestamp] = []
    network_requests = 0
    for symbol in cfg["provider"]["symbols"]:
        bar_frames: list[pd.DataFrame] = []
        records: list[dict[str, Any]] = []
        for hour in hours:
            cached = _cached_hour(output_root, symbol, hour)
            if cached is None:
                payload, metadata = fetcher(symbol, hour)
                network_requests += 1
                raw_hash = sha256_bytes(payload)
                name = (
                    f"{hour:%Y%m%dT%H0000Z}_{raw_hash[:16]}.json"
                )
                raw_relative = Path("raw") / symbol / name
                metadata_relative = (
                    Path("metadata") / symbol / name
                )
                raw_path = output_root / raw_relative
                metadata_path = output_root / metadata_relative
                write_immutable(raw_path, payload)
                metadata_payload = {
                    "schema_version": (
                        "eurusd_prospective_neutral_hour_v1"
                    ),
                    **metadata,
                    "raw_relative_path": raw_relative,
                    "raw_sha256": raw_hash,
                }
                write_immutable(
                    metadata_path,
                    (
                        json.dumps(
                            _serialize(metadata_payload), indent=2
                        )
                        + "\n"
                    ).encode("utf-8"),
                )
            else:
                payload, metadata = cached
                raw_hash = sha256_bytes(payload)
                raw_relative = Path(
                    str(metadata["raw_relative_path"])
                )
                metadata_relative = (
                    Path("metadata") / symbol / raw_relative.name
                )
                metadata_path = output_root / metadata_relative
            if str(metadata["symbol"]) != symbol:
                raise RuntimeError("Ownership fetch symbol mismatch")
            if _utc(metadata["hour_utc"]) != hour:
                raise RuntimeError("Ownership fetch hour mismatch")
            item_observed = _utc(metadata["observed_at_utc"])
            observed_values.append(item_observed)
            ticks = decode_ticks(payload, symbol, hour)
            bar = build_h1_bar(ticks, hour, item_observed)
            if not bar.empty:
                bar_frames.append(bar)
            records.append(
                {
                    "hour_utc": hour,
                    "raw_relative_path": raw_relative.as_posix(),
                    "raw_sha256": raw_hash,
                    "metadata_sha256": sha256_file(metadata_path),
                    "tick_count": int(len(ticks)),
                    "h1_bar_present": bool(len(bar)),
                }
            )
        bars = (
            pd.concat(bar_frames).sort_index()
            if bar_frames
            else pd.DataFrame(
                columns=["open", "high", "low", "close"]
            )
        )
        bars_by_symbol[symbol] = bars
        source_hashes[symbol] = _source_chain(records)
        normalized_relative = (
            Path("normalized")
            / f"{symbol}_{day:%Y-%m-%d}_{source_hashes[symbol][:16]}.parquet"
        )
        normalized_path = output_root / normalized_relative
        normalized_path.parent.mkdir(parents=True, exist_ok=True)
        if normalized_path.exists():
            existing_frame = pd.read_parquet(normalized_path)
            pd.testing.assert_frame_equal(
                existing_frame,
                bars,
                check_dtype=False,
            )
        else:
            bars.to_parquet(normalized_path, compression="zstd")
        source_inventory[symbol] = {
            "requested_hours": int(len(hours)),
            "populated_h1_rows": int(len(bars)),
            "first_h1_utc": (
                bars.index.min() if len(bars) else None
            ),
            "last_h1_utc": (
                bars.index.max() if len(bars) else None
            ),
            "source_chain_sha256": source_hashes[symbol],
            "normalized_relative_path": normalized_relative,
            "normalized_sha256": sha256_file(normalized_path),
        }
    ownership_observed = max(observed_values)
    record, classifier = classify_ownership_from_h1(
        bars_by_symbol,
        day,
        ownership_observed,
        source_hashes,
    )
    record_relative = (
        Path("records")
        / f"{day:%Y-%m-%d}_{record['ownership_evidence_sha256'][:16]}.json"
    )
    record_path = output_root / record_relative
    write_immutable(
        record_path,
        (
            json.dumps(_serialize(record), indent=2) + "\n"
        ).encode("utf-8"),
    )
    manifest = {
        "schema_version": "eurusd_prospective_neutral_ownership_v1",
        "eligible_date": day,
        "ownership_observed_at_utc": ownership_observed,
        "source_inventory": source_inventory,
        "classifier_contract_sha256": cfg["classifier_contract"][
            "sha256"
        ],
        "classifier": classifier,
        "ownership_record": {
            "relative_path": record_relative,
            "sha256": sha256_file(record_path),
            "ownership_evidence_sha256": record[
                "ownership_evidence_sha256"
            ],
            "is_neutral": record["is_neutral"],
        },
        "network_requests_made": network_requests,
        "historical_pnl_loaded": False,
        "broker_action_allowed": False,
    }
    manifest_bytes = (
        json.dumps(_serialize(manifest), indent=2) + "\n"
    ).encode("utf-8")
    manifest_hash = sha256_bytes(manifest_bytes)
    manifest_relative = (
        Path("manifests")
        / f"MANIFEST_{day:%Y-%m-%d}_{manifest_hash[:16]}.json"
    )
    manifest_path = output_root / manifest_relative
    write_immutable(manifest_path, manifest_bytes)
    return _serialize(
        {
            "status": (
                "NEUTRAL_OWNED"
                if record["is_neutral"]
                else "DATE_NOT_OWNED"
            ),
            "eligible_date": day,
            "ownership_observed_at_utc": ownership_observed,
            "common_h1_rows_through_state": classifier[
                "common_h1_rows_through_state"
            ],
            "ownership_record_relative_path": record_relative,
            "ownership_record_sha256": sha256_file(record_path),
            "ownership_evidence_sha256": record[
                "ownership_evidence_sha256"
            ],
            "manifest_relative_path": manifest_relative,
            "manifest_sha256": sha256_file(manifest_path),
            "network_requests_made": network_requests,
            "historical_pnl_loaded": False,
            "broker_action_allowed": False,
        }
    )


def synthetic_dry_run(eligible_date: Any) -> dict[str, Any]:
    day = _day(eligible_date)
    state_time = day - pd.Timedelta(hours=1)
    index = pd.date_range(
        state_time - pd.Timedelta(hours=599),
        state_time,
        freq="h",
    )
    angle = np.linspace(0.0, 30.0 * math.pi, len(index))
    bars: dict[str, pd.DataFrame] = {}
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
    for symbol, offset in offsets.items():
        close = offset + scales[symbol] * np.sin(angle)
        width = scales[symbol] * 0.2
        bars[symbol] = pd.DataFrame(
            {
                "open": close,
                "high": close + width,
                "low": close - width,
                "close": close,
            },
            index=index,
        )
    hashes = {
        symbol: hashlib.sha256(
            f"synthetic:{symbol}".encode("utf-8")
        ).hexdigest()
        for symbol in bars
    }
    record, evidence = classify_ownership_from_h1(
        bars,
        day,
        day + pd.Timedelta(minutes=2),
        hashes,
    )
    return _serialize(
        {
            "status": "SYNTHETIC_DRY_RUN_COMPLETE",
            "eligible_date": day,
            "ownership_is_neutral": record["is_neutral"],
            "common_h1_rows_through_state": evidence[
                "common_h1_rows_through_state"
            ],
            "terminal_features_sha256": evidence[
                "terminal_features_sha256"
            ],
            "network_requests_made": 0,
            "historical_pnl_loaded": False,
            "broker_action_allowed": False,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture", "dry-run"))
    parser.add_argument("--eligible-date", required=True)
    parser.add_argument(
        "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verify_lock()
    result = (
        capture_ownership(
            args.eligible_date,
            args.output_root,
        )
        if args.command == "capture"
        else synthetic_dry_run(args.eligible_date)
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
