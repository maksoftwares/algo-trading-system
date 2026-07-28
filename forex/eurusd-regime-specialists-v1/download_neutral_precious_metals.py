from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.research import sha256_file  # noqa: E402


EXTERNAL_ROOT = Path(
    "D:/AlgoTradingData/research/eurusd-neutral-precious-metals-v1"
)
SHARED_RAW_ROOT = Path(
    "D:/AlgoTradingData/C_DRIVE/"
    "DukascopyTickDataFoundationV1/raw"
)
OUTPUT_PATH = EXTERNAL_ROOT / "PRECIOUS_METALS_FIRST_HOUR_M5.parquet"
MANIFEST_PATH = EXTERNAL_ROOT / "MANIFEST.json"
SYMBOLS = {
    "XAUUSD": "XAU-USD",
    "XAGUSD": "XAG-USD",
}
EXPECTED_ARRAYS = ("times", "bids", "asks", "bidVolumes", "askVolumes")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        nargs="?",
        choices=("download", "rebuild"),
        default="download",
    )
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def required_hours(eligible_dates: Iterable[str]) -> list[pd.Timestamp]:
    hours = set()
    for raw_date in eligible_dates:
        midnight = pd.Timestamp(raw_date, tz="UTC")
        hours.update(
            {
                midnight - pd.Timedelta(hours=2),
                midnight - pd.Timedelta(hours=1),
                midnight,
            }
        )
    return sorted(hours)


def _shared_path(symbol: str, hour: pd.Timestamp) -> Path:
    return (
        SHARED_RAW_ROOT
        / symbol
        / f"year={hour.year:04d}"
        / f"month={hour.month:02d}"
        / f"{hour:%Y%m%d%H}.json"
    )


def _download_path(symbol: str, hour: pd.Timestamp) -> Path:
    return (
        EXTERNAL_ROOT
        / "raw"
        / symbol
        / f"year={hour.year:04d}"
        / f"month={hour.month:02d}"
        / f"{hour:%Y%m%d%H}.json"
    )


def _url(symbol: str, hour: pd.Timestamp) -> str:
    instrument = SYMBOLS[symbol]
    return (
        "https://jetta.dukascopy.com/v1/ticks/"
        f"{instrument}/{hour.year}/{hour.month}/{hour.day}/{hour.hour}"
    )


def validate_payload(raw: bytes, expected_hour: pd.Timestamp) -> dict[str, Any]:
    payload = json.loads(raw)
    required = {
        "timestamp",
        "multiplier",
        "ask",
        "bid",
        *EXPECTED_ARRAYS,
    }
    missing = required - set(payload)
    if missing:
        raise ValueError(f"Missing Dukascopy fields: {sorted(missing)}")
    expected_ms = int(expected_hour.timestamp() * 1000)
    if int(payload["timestamp"]) != expected_ms:
        raise ValueError(
            f"Unexpected source hour {payload['timestamp']} != {expected_ms}"
        )
    lengths = {len(payload[column]) for column in EXPECTED_ARRAYS}
    if len(lengths) != 1:
        raise ValueError("Inconsistent Dukascopy tick arrays")
    if len(payload["times"]) and (
        payload["bid"] is None or payload["ask"] is None
    ):
        raise ValueError("Nonempty payload has null base price")
    return payload


def _round_to_multiplier(values: np.ndarray, multiplier: float) -> np.ndarray:
    scale = max(0, int(round(-math.log10(multiplier))))
    factor = 10**scale
    return np.floor(values * factor + 0.5 + 1e-9) / factor


def decode_to_m5(raw: bytes, expected_hour: pd.Timestamp) -> pd.DataFrame:
    payload = validate_payload(raw, expected_hour)
    count = len(payload["times"])
    columns = [
        "timestamp_utc",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
        "tick_count",
    ]
    if count == 0:
        return pd.DataFrame(columns=columns)
    multiplier = float(payload["multiplier"])
    bids = float(payload["bid"]) + np.cumsum(
        np.asarray(payload["bids"], dtype=np.float64)
    ) * multiplier
    asks = float(payload["ask"]) + np.cumsum(
        np.asarray(payload["asks"], dtype=np.float64)
    ) * multiplier
    bids = _round_to_multiplier(bids, multiplier)
    asks = _round_to_multiplier(asks, multiplier)
    if np.any(bids <= 0.0) or np.any(asks < bids):
        raise ValueError("Invalid decoded Dukascopy prices")
    offsets = np.cumsum(
        np.asarray(payload["times"], dtype=np.int64)
    )
    if offsets[-1] >= 3_600_000:
        raise ValueError("Tick offset exceeds source hour")
    ticks = pd.DataFrame(
        {
            "timestamp_utc": expected_hour
            + pd.to_timedelta(offsets, unit="ms"),
            "bid": bids,
            "ask": asks,
        }
    ).set_index("timestamp_utc")
    bid = ticks["bid"].resample("5min").ohlc()
    ask = ticks["ask"].resample("5min").ohlc()
    size = ticks["bid"].resample("5min").size().rename("tick_count")
    frame = pd.concat(
        [
            bid.add_prefix("bid_"),
            ask.add_prefix("ask_"),
            size,
        ],
        axis=1,
    ).dropna(subset=["bid_open", "ask_open"])
    return frame.reset_index()[columns]


def _download_one(symbol: str, hour: pd.Timestamp) -> tuple[str, str, int]:
    destination = _download_path(symbol, hour)
    if destination.exists():
        raw = destination.read_bytes()
        validate_payload(raw, hour)
        return symbol, hour.isoformat(), len(raw)
    url = _url(symbol, hour)
    last_error: Exception | None = None
    for attempt in range(8):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "eurusd-neutral-research/1.0"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
            validate_payload(raw, hour)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
            return symbol, hour.isoformat(), len(raw)
        except (OSError, ValueError, urllib.error.URLError) as error:
            last_error = error
            if attempt < 7:
                retry_after = None
                if isinstance(error, urllib.error.HTTPError):
                    retry_after = error.headers.get("Retry-After")
                wait = (
                    float(retry_after)
                    if retry_after is not None
                    else min(30.0, 2.0**attempt)
                )
                time.sleep(wait)
    raise RuntimeError(f"Failed {symbol} {hour}: {last_error}")


def ensure_sources(
    hours: list[pd.Timestamp], *, allow_network: bool, workers: int
) -> None:
    missing = []
    for symbol in SYMBOLS:
        for hour in hours:
            if not _shared_path(symbol, hour).exists() and not _download_path(
                symbol, hour
            ).exists():
                missing.append((symbol, hour))
    if missing and not allow_network:
        preview = ", ".join(
            f"{symbol}:{hour.isoformat()}"
            for symbol, hour in missing[:5]
        )
        raise RuntimeError(
            f"Cache-only rebuild missing {len(missing)} sources: {preview}"
        )
    if not missing:
        return
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_download_one, symbol, hour)
            for symbol, hour in missing
        ]
        for index, future in enumerate(as_completed(futures), start=1):
            future.result()
            if index % 100 == 0:
                print(f"downloaded {index}/{len(futures)}", flush=True)


def build_source(hours: list[pd.Timestamp]) -> tuple[pd.DataFrame, dict[str, Any]]:
    records = []
    source_digest = hashlib.sha256()
    source_counts = {
        symbol: {
            "required_hours": len(hours),
            "shared_raw_hours": 0,
            "downloaded_raw_hours": 0,
            "empty_hours": 0,
            "populated_hours": 0,
            "m5_rows": 0,
        }
        for symbol in SYMBOLS
    }
    for symbol in SYMBOLS:
        for hour in hours:
            shared = _shared_path(symbol, hour)
            downloaded = _download_path(symbol, hour)
            path = shared if shared.exists() else downloaded
            raw = path.read_bytes()
            validate_payload(raw, hour)
            source_digest.update(
                f"{symbol}|{hour.isoformat()}".encode("utf-8")
            )
            source_digest.update(hashlib.sha256(raw).digest())
            source_type = (
                "shared_raw_hours" if path == shared else "downloaded_raw_hours"
            )
            source_counts[symbol][source_type] += 1
            frame = decode_to_m5(raw, hour)
            if frame.empty:
                source_counts[symbol]["empty_hours"] += 1
                continue
            source_counts[symbol]["populated_hours"] += 1
            source_counts[symbol]["m5_rows"] += len(frame)
            frame.insert(0, "symbol", symbol)
            records.append(frame)
    if not records:
        raise RuntimeError("No precious-metals M5 rows built")
    output = (
        pd.concat(records, ignore_index=True)
        .sort_values(["symbol", "timestamp_utc"])
        .drop_duplicates(["symbol", "timestamp_utc"], keep="last")
        .reset_index(drop=True)
    )
    EXTERNAL_ROOT.mkdir(parents=True, exist_ok=True)
    output.to_parquet(OUTPUT_PATH, index=False, compression="zstd")
    manifest = {
        "campaign_source": "eurusd-neutral-precious-metals-v1",
        "provider": "Dukascopy public Jetta tick endpoint",
        "authentication_required": False,
        "symbols": SYMBOLS,
        "required_hour_rule": (
            "For each locked Neutral date: prior UTC date 22:00 and 23:00, "
            "plus current UTC date 00:00"
        ),
        "required_distinct_hours_each_symbol": len(hours),
        "first_required_hour_utc": hours[0].isoformat(),
        "last_required_hour_utc": hours[-1].isoformat(),
        "source_chain_sha256": source_digest.hexdigest(),
        "source_counts": source_counts,
        "output_path": str(OUTPUT_PATH),
        "output_rows": int(len(output)),
        "output_first_utc": output["timestamp_utc"].min().isoformat(),
        "output_last_utc": output["timestamp_utc"].max().isoformat(),
        "output_sha256": sha256_file(OUTPUT_PATH),
        "timestamp_semantics": (
            "M5 bar start; row is usable only five minutes after timestamp"
        ),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return output, manifest


def main() -> int:
    from eurusd_regime_specialists.neutral_binance_eurusdt_flow import (
        load_parent_points,
    )

    args = parse_args()
    parent = load_parent_points(include_outcomes=False)
    dates = sorted(parent["eligible_date"].astype(str).unique())
    hours = required_hours(dates)
    ensure_sources(
        hours,
        allow_network=args.command == "download",
        workers=max(1, int(args.workers)),
    )
    _, manifest = build_source(hours)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
