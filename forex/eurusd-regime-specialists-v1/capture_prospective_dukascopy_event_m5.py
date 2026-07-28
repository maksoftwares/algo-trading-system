from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd


DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-macro-crossasset-agreement-v1/market"
)
OFFICIAL_ORIGIN = "https://jetta.dukascopy.com/v1"
OBSERVATION_BARS = 3
MINIMUM_CAPTURE_LAG_SECONDS = 60
SYMBOLS = {
    "EURUSD": {"source_code": "EUR-USD", "price_scale": 5},
    "DOLLARIDXUSD": {
        "source_code": "DOLLAR.IDX-USD",
        "price_scale": 3,
    },
    "USTBONDTRUSD": {
        "source_code": "USTBOND.TR-USD",
        "price_scale": 3,
    },
}
FEATURE_COLUMNS = [
    "event_time_utc",
    "observation_start_utc",
    "observation_completed_at_utc",
    "market_observed_at_utc",
    "eurusd_pre_mid",
    "eurusd_post_mid",
    "eurusd_observation_mid_high",
    "eurusd_observation_mid_low",
    "dxy_pre_mid",
    "dxy_post_mid",
    "treasury_pre_mid",
    "treasury_post_mid",
    "capture_semantics",
]


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return timestamp.tz_convert("UTC").as_unit("ns")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {
            str(key): _serialize(item) for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise RuntimeError(
                f"Refusing to overwrite immutable market evidence: {path}"
            )


def observation_window(
    event_time_utc: Any,
) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    event = _utc(event_time_utc)
    baseline_start = event.floor("5min") - pd.Timedelta(minutes=5)
    observation_start = event.ceil("5min")
    completed_at = observation_start + pd.Timedelta(
        minutes=5 * OBSERVATION_BARS
    )
    return baseline_start, observation_start, completed_at


def capture_ready(
    event_time_utc: Any,
    observed_at_utc: Any,
    *,
    minimum_lag_seconds: int = MINIMUM_CAPTURE_LAG_SECONDS,
) -> bool:
    _, _, completed_at = observation_window(event_time_utc)
    observed = _utc(observed_at_utc)
    return observed >= completed_at + pd.Timedelta(
        seconds=minimum_lag_seconds
    )


def required_hours(event_time_utc: Any) -> list[pd.Timestamp]:
    baseline, _, completed_at = observation_window(event_time_utc)
    first = baseline.floor("h")
    last = (completed_at - pd.Timedelta(nanoseconds=1)).floor("h")
    return list(pd.date_range(first, last, freq="h"))


def official_tick_url(symbol: str, hour_utc: Any) -> str:
    if symbol not in SYMBOLS:
        raise ValueError(f"Unsupported symbol: {symbol}")
    hour = _utc(hour_utc)
    source_code = SYMBOLS[symbol]["source_code"]
    return (
        f"{OFFICIAL_ORIGIN}/ticks/{source_code}/"
        f"{hour.year}/{hour.month}/{hour.day}/{hour.hour}"
    )


def _round_source_price(value: float, scale: int) -> float:
    factor = 10**scale
    return math.floor(value * factor + 0.5 + 1e-9) / factor


def decode_ticks(
    raw_payload: bytes,
    symbol: str,
    hour_utc: Any,
) -> pd.DataFrame:
    if symbol not in SYMBOLS:
        raise ValueError(f"Unsupported symbol: {symbol}")
    payload = json.loads(raw_payload)
    if not isinstance(payload, dict):
        raise RuntimeError("Dukascopy payload is not an object")
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    required = ("timestamp", "multiplier", "bid", "ask", *arrays)
    if any(key not in payload for key in required):
        raise RuntimeError("Dukascopy payload lacks required fields")
    lengths = {
        key: len(payload[key]) if isinstance(payload[key], list) else -1
        for key in arrays
    }
    if len(set(lengths.values())) != 1 or min(lengths.values()) < 0:
        raise RuntimeError("Dukascopy tick arrays are inconsistent")
    count = lengths["times"]
    if count == 0:
        return pd.DataFrame(
            columns=["timestamp_utc", "bid", "ask", "mid"]
        )
    timestamp_ms = int(payload["timestamp"])
    multiplier = float(payload["multiplier"])
    bid = float(payload["bid"])
    ask = float(payload["ask"])
    if multiplier <= 0:
        raise RuntimeError("Dukascopy multiplier must be positive")
    scale = int(SYMBOLS[symbol]["price_scale"])
    hour = _utc(hour_utc)
    hour_start_ms = int(hour.timestamp() * 1000)
    hour_end_ms = hour_start_ms + 3_600_000
    rows: list[dict[str, Any]] = []
    previous_timestamp = -1
    for index in range(count):
        timestamp_ms += int(payload["times"][index])
        bid = _round_source_price(
            bid + float(payload["bids"][index]) * multiplier,
            scale,
        )
        ask = _round_source_price(
            ask + float(payload["asks"][index]) * multiplier,
            scale,
        )
        if timestamp_ms < previous_timestamp:
            raise RuntimeError("Dukascopy timestamps are not monotonic")
        if not (hour_start_ms <= timestamp_ms < hour_end_ms):
            raise RuntimeError("Decoded tick is outside requested hour")
        if not (bid > 0 and ask >= bid):
            raise RuntimeError("Dukascopy price or spread is invalid")
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
        previous_timestamp = timestamp_ms
    return pd.DataFrame(rows)


def build_completed_m5(
    ticks: pd.DataFrame,
    observed_at_utc: Any,
) -> pd.DataFrame:
    if ticks.empty:
        return pd.DataFrame(
            columns=[
                "timestamp_utc",
                "bid_open",
                "bid_high",
                "bid_low",
                "bid_close",
                "ask_open",
                "ask_high",
                "ask_low",
                "ask_close",
                "mid_open",
                "mid_high",
                "mid_low",
                "mid_close",
                "tick_count",
            ]
        )
    observed = _utc(observed_at_utc)
    frame = ticks.copy().sort_values("timestamp_utc")
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_utc"], utc=True
    )
    frame["bar_start"] = frame["timestamp_utc"].dt.floor("5min")
    grouped = frame.groupby("bar_start", sort=True)
    bars = grouped.agg(
        bid_open=("bid", "first"),
        bid_high=("bid", "max"),
        bid_low=("bid", "min"),
        bid_close=("bid", "last"),
        ask_open=("ask", "first"),
        ask_high=("ask", "max"),
        ask_low=("ask", "min"),
        ask_close=("ask", "last"),
        mid_open=("mid", "first"),
        mid_high=("mid", "max"),
        mid_low=("mid", "min"),
        mid_close=("mid", "last"),
        tick_count=("mid", "size"),
    ).reset_index(names="timestamp_utc")
    complete = (
        bars["timestamp_utc"] + pd.Timedelta(minutes=5)
    ).le(observed)
    return bars[complete].reset_index(drop=True)


def empty_feature() -> pd.DataFrame:
    return pd.DataFrame(columns=FEATURE_COLUMNS)


def extract_event_feature(
    bars_by_symbol: dict[str, pd.DataFrame],
    event_time_utc: Any,
    market_observed_at_utc: Any,
) -> tuple[pd.DataFrame, str]:
    baseline, observation_start, completed_at = observation_window(
        event_time_utc
    )
    expected_observation = list(
        pd.date_range(
            observation_start, periods=OBSERVATION_BARS, freq="5min"
        )
    )
    selected: dict[str, tuple[pd.Series, pd.DataFrame]] = {}
    for symbol in SYMBOLS:
        bars = bars_by_symbol.get(symbol, pd.DataFrame()).copy()
        if bars.empty or "timestamp_utc" not in bars:
            return empty_feature(), f"{symbol}_BARS_MISSING"
        bars["timestamp_utc"] = pd.to_datetime(
            bars["timestamp_utc"], utc=True
        )
        indexed = bars.set_index("timestamp_utc")
        required = [baseline, *expected_observation]
        if any(timestamp not in indexed.index for timestamp in required):
            return empty_feature(), f"{symbol}_REQUIRED_M5_MISSING"
        selected[symbol] = (
            indexed.loc[baseline],
            indexed.loc[expected_observation],
        )
    eurusd_pre, eurusd_observation = selected["EURUSD"]
    dxy_pre, dxy_observation = selected["DOLLARIDXUSD"]
    bond_pre, bond_observation = selected["USTBONDTRUSD"]
    row = {
        "event_time_utc": _utc(event_time_utc),
        "observation_start_utc": observation_start,
        "observation_completed_at_utc": completed_at,
        "market_observed_at_utc": _utc(market_observed_at_utc),
        "eurusd_pre_mid": float(eurusd_pre["mid_close"]),
        "eurusd_post_mid": float(
            eurusd_observation.iloc[-1]["mid_close"]
        ),
        "eurusd_observation_mid_high": float(
            eurusd_observation["mid_high"].max()
        ),
        "eurusd_observation_mid_low": float(
            eurusd_observation["mid_low"].min()
        ),
        "dxy_pre_mid": float(dxy_pre["mid_close"]),
        "dxy_post_mid": float(
            dxy_observation.iloc[-1]["mid_close"]
        ),
        "treasury_pre_mid": float(bond_pre["mid_close"]),
        "treasury_post_mid": float(
            bond_observation.iloc[-1]["mid_close"]
        ),
        "capture_semantics": (
            "ONLY_FULLY_COMPLETED_M5_BARS_ENTRY_BAR_EXCLUDED"
        ),
    }
    return pd.DataFrame([row])[FEATURE_COLUMNS], "COMPLETE"


def fetch_hour(
    symbol: str,
    hour_utc: pd.Timestamp,
) -> tuple[bytes, dict[str, Any]]:
    url = official_tick_url(symbol, hour_utc)
    started = pd.Timestamp.now(tz="UTC").as_unit("ns")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "eurusd-neutral-prospective-market-capture/1.0"
            ),
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
        http_date_header = response.headers.get("Date")
        http_date = (
            _utc(parsedate_to_datetime(http_date_header))
            if http_date_header
            else None
        )
        headers = {
            "date": http_date_header,
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        }
    finished = pd.Timestamp.now(tz="UTC").as_unit("ns")
    observed_candidates = [finished]
    if http_date is not None:
        observed_candidates.append(http_date)
    observed = max(observed_candidates)
    decode_ticks(payload, symbol, hour_utc)
    return payload, {
        "symbol": symbol,
        "hour_utc": hour_utc,
        "url": url,
        "request_started_utc": started,
        "request_finished_utc": finished,
        "http_date_utc": http_date,
        "observed_at_utc": observed,
        "response_headers": headers,
    }


def market_evidence_chain(output_root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted(
        [
            *output_root.glob("raw/**/*.json"),
            *output_root.glob("metadata/**/*.json"),
            *output_root.glob("normalized/*.parquet"),
        ],
        key=lambda path: path.relative_to(output_root).as_posix(),
    )
    for path in paths:
        relative = path.relative_to(output_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def capture_event(
    event_time_utc: Any,
    output_root: Path,
    *,
    now_utc: Any | None = None,
    fetcher: Callable[
        [str, pd.Timestamp], tuple[bytes, dict[str, Any]]
    ] = fetch_hour,
) -> dict[str, Any]:
    event = _utc(event_time_utc)
    now = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _utc(now_utc)
    )
    if not capture_ready(event, now):
        _, _, completed_at = observation_window(event)
        return _serialize(
            {
                "status": "WAITING_FOR_COMPLETED_OBSERVATION_WINDOW",
                "event_time_utc": event,
                "earliest_capture_utc": completed_at
                + pd.Timedelta(
                    seconds=MINIMUM_CAPTURE_LAG_SECONDS
                ),
                "network_request_made": False,
                "broker_action_allowed": False,
            }
        )

    all_ticks: dict[str, list[pd.DataFrame]] = {
        symbol: [] for symbol in SYMBOLS
    }
    raw_records: list[dict[str, Any]] = []
    for symbol in SYMBOLS:
        for hour in required_hours(event):
            payload, metadata = fetcher(symbol, hour)
            observed = _utc(metadata["observed_at_utc"])
            raw_hash = sha256_bytes(payload)
            stem = (
                f"{event:%Y%m%dT%H%M%SZ}_"
                f"{observed:%Y%m%dT%H%M%SZ}_"
                f"{symbol}_{hour:%Y%m%d%H}_{raw_hash[:16]}"
            )
            raw_relative = (
                Path("raw") / symbol / f"{stem}.json"
            )
            metadata_relative = (
                Path("metadata") / symbol / f"{stem}.json"
            )
            raw_path = output_root / raw_relative
            metadata_path = output_root / metadata_relative
            write_immutable(raw_path, payload)
            stored_metadata = {
                **metadata,
                "event_time_utc": event,
                "raw_relative_path": raw_relative,
                "raw_sha256": raw_hash,
                "broker_action_allowed": False,
            }
            write_immutable(
                metadata_path,
                (
                    json.dumps(
                        _serialize(stored_metadata), indent=2
                    )
                    + "\n"
                ).encode("utf-8"),
            )
            ticks = decode_ticks(payload, symbol, hour)
            all_ticks[symbol].append(ticks)
            raw_records.append(
                {
                    "symbol": symbol,
                    "hour_utc": hour,
                    "observed_at_utc": observed,
                    "raw_relative_path": raw_relative,
                    "raw_sha256": raw_hash,
                    "metadata_relative_path": metadata_relative,
                    "metadata_sha256": sha256_file(metadata_path),
                    "tick_count": int(len(ticks)),
                }
            )
    market_observed = max(
        record["observed_at_utc"] for record in raw_records
    )
    bars_by_symbol: dict[str, pd.DataFrame] = {}
    for symbol, frames in all_ticks.items():
        ticks = (
            pd.concat(frames, ignore_index=True)
            if frames
            else pd.DataFrame()
        )
        bars_by_symbol[symbol] = build_completed_m5(
            ticks, market_observed
        )
    feature, coverage = extract_event_feature(
        bars_by_symbol, event, market_observed
    )
    raw_inventory_hash = sha256_bytes(
        json.dumps(
            _serialize(raw_records),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    normalized_stem = (
        f"{event:%Y%m%dT%H%M%SZ}_"
        f"{market_observed:%Y%m%dT%H%M%SZ}_"
        f"{raw_inventory_hash[:16]}"
    )
    normalized_relative = (
        Path("normalized") / f"{normalized_stem}.parquet"
    )
    normalized_path = output_root / normalized_relative
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    if normalized_path.exists():
        existing = pd.read_parquet(normalized_path)
        pd.testing.assert_frame_equal(
            existing.reset_index(drop=True),
            feature.reset_index(drop=True),
            check_dtype=False,
        )
    else:
        feature.to_parquet(
            normalized_path, index=False, compression="zstd"
        )
    chain = market_evidence_chain(output_root)
    manifest = {
        "schema_version": (
            "eurusd_neutral_prospective_event_market_m5_v1"
        ),
        "event_time_utc": event,
        "market_observed_at_utc": market_observed,
        "coverage": coverage,
        "required_hours_utc": required_hours(event),
        "raw_snapshots": raw_records,
        "raw_inventory_sha256": raw_inventory_hash,
        "normalized_snapshot": {
            "relative_path": normalized_relative,
            "sha256": sha256_file(normalized_path),
            "rows": int(len(feature)),
        },
        "market_evidence_chain_sha256": chain,
        "causality": {
            "only_completed_m5_bars": True,
            "entry_bar_excluded": True,
            "minimum_post_observation_lag_seconds": (
                MINIMUM_CAPTURE_LAG_SECONDS
            ),
        },
        "broker_action_allowed": False,
    }
    manifest_relative = (
        Path("manifests")
        / f"MANIFEST_{normalized_stem}_{chain[:12]}.json"
    )
    manifest_path = output_root / manifest_relative
    write_immutable(
        manifest_path,
        (
            json.dumps(_serialize(manifest), indent=2) + "\n"
        ).encode("utf-8"),
    )
    return _serialize(
        {
            "status": (
                "EVENT_MARKET_FEATURE_CAPTURED"
                if len(feature)
                else "EVENT_MARKET_BARS_INCOMPLETE"
            ),
            "event_time_utc": event,
            "coverage": coverage,
            "feature_rows": int(len(feature)),
            "manifest_relative_path": manifest_relative,
            "manifest_sha256": sha256_file(manifest_path),
            "market_evidence_chain_sha256": chain,
            "network_request_made": True,
            "broker_action_allowed": False,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture",))
    parser.add_argument("--event-time", required=True)
    parser.add_argument(
        "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = capture_event(args.event_time, args.output_root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
