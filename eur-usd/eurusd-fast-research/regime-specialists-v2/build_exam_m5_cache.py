from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

STORAGE = Path("C:/DukascopyTickDataFoundationV1")
RAW = STORAGE / "raw" / "EURUSD"
CACHE = STORAGE / "research" / "eurusd-regime-specialists-v2" / "EURUSD_M5_BIDASK_2024_07_2026_06.csv.gz"
METADATA = CACHE.with_suffix("").with_suffix(".metadata.json")
START = pd.Timestamp("2024-07-01T00:00:00Z")
END = pd.Timestamp("2026-07-01T00:00:00Z")


def decode(path: Path) -> list[dict]:
    payload = json.loads(path.read_bytes())
    count = len(payload.get("times", []))
    if count == 0:
        return []
    multiplier = float(payload["multiplier"])
    bid = float(payload["bid"]) + np.cumsum(np.asarray(payload["bids"], dtype=float)) * multiplier
    ask = float(payload["ask"]) + np.cumsum(np.asarray(payload["asks"], dtype=float)) * multiplier
    if np.any(ask < bid):
        raise ValueError(f"Crossed quote payload: {path}")
    times = int(payload["timestamp"]) + np.cumsum(np.asarray(payload["times"], dtype=np.int64))
    buckets = times // 300_000
    starts = np.flatnonzero(np.r_[True, buckets[1:] != buckets[:-1]])
    ends = np.r_[starts[1:], len(buckets)]
    rows = []
    for start, end in zip(starts, ends):
        rows.append(
            {
                "timestamp": pd.Timestamp(int(buckets[start]) * 300_000, unit="ms", tz="UTC"),
                "bid_open": bid[start],
                "bid_high": float(np.max(bid[start:end])),
                "bid_low": float(np.min(bid[start:end])),
                "bid_close": bid[end - 1],
                "ask_open": ask[start],
                "ask_high": float(np.max(ask[start:end])),
                "ask_low": float(np.min(ask[start:end])),
                "ask_close": ask[end - 1],
                "ticks": end - start,
            }
        )
    return rows


def main() -> None:
    if CACHE.is_file() and METADATA.is_file():
        metadata = json.loads(METADATA.read_text(encoding="utf-8"))
        if hashlib.sha256(CACHE.read_bytes()).hexdigest() == metadata["cache_sha256"]:
            print(json.dumps(metadata, indent=2))
            return
    files = []
    for path in RAW.glob("year=*/month=*/*.json"):
        if path.name.startswith("_"):
            continue
        timestamp = pd.Timestamp(
            datetime.strptime(path.stem[:10], "%Y%m%d%H").replace(tzinfo=timezone.utc)
        )
        if START <= timestamp < END:
            files.append(path)
    files.sort()
    rows = []
    for number, path in enumerate(files, 1):
        rows.extend(decode(path))
        if number % 5000 == 0:
            print(f"decoded {number:,}/{len(files):,} raw hours")
    frame = pd.DataFrame(rows).sort_values("timestamp").drop_duplicates("timestamp")
    frame = frame[(frame["timestamp"] >= START) & (frame["timestamp"] < END)]
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        CACHE,
        index=False,
        compression={"method": "gzip", "compresslevel": 6, "mtime": 0},
        float_format="%.8f",
        lineterminator="\n",
    )
    metadata = {
        "schema": "EURUSD_M5_BIDASK_V1",
        "start_utc": START.isoformat(),
        "end_exclusive_utc": END.isoformat(),
        "raw_hour_files": len(files),
        "m5_rows": len(frame),
        "first_bar": frame["timestamp"].iloc[0].isoformat(),
        "last_bar": frame["timestamp"].iloc[-1].isoformat(),
        "known_quarantine": ["2024-10-09T23:00:00Z/2024-10-10T01:00:00Z"],
        "cache_sha256": hashlib.sha256(CACHE.read_bytes()).hexdigest(),
        "cache_bytes": CACHE.stat().st_size,
    }
    METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
