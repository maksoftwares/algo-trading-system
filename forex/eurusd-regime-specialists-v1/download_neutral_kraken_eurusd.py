from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_ROOT = Path(
    "D:/AlgoTradingData/research/"
    "eurusd-neutral-kraken-eurusd-flow-v1"
)
BASE_URL = "https://api.kraken.com/0/public/Trades"
PAIR = "EURUSD"
RESULT_KEY = "EUR/USD"
FIRST_COMPLETE_DATE = "2020-03-13"
LAST_DATE = "2026-06-30"
PAGE_COUNT = 1000
WINDOW_LEAD_MINUTES = 15
WINDOW_END_MINUTES = 45
TRADE_COLUMNS = [
    "price",
    "base_volume",
    "trade_time_epoch",
    "reported_side",
    "order_type",
    "misc",
    "trade_id",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def eligible_dates(
    start_date: str = FIRST_COMPLETE_DATE,
    end_date: str = LAST_DATE,
) -> list[str]:
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    from eurusd_regime_specialists.neutral_four_clock_ranker import (
        build_paired_points,
        load_config,
        load_source,
    )

    cfg = load_config()
    source = load_source(cfg, include_outcomes=False)
    points, _ = build_paired_points(
        source,
        cfg,
        include_outcomes=False,
        enforce_frozen_census=True,
    )
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    dates = (
        points[
            points["entry_time_utc"].ge(start)
            & points["entry_time_utc"].lt(end)
        ]["eligible_date"]
        .drop_duplicates()
        .sort_values()
    )
    return dates.tolist()


def date_window(date: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    midnight = pd.Timestamp(date, tz="UTC")
    return (
        midnight - pd.Timedelta(minutes=WINDOW_LEAD_MINUTES),
        midnight + pd.Timedelta(minutes=WINDOW_END_MINUTES),
    )


def request_url(since: str) -> str:
    query = urllib.parse.urlencode(
        {
            "pair": PAIR,
            "since": since,
            "count": PAGE_COUNT,
            "assetVersion": 1,
        }
    )
    return f"{BASE_URL}?{query}"


def fetch_bytes(
    url: str,
    *,
    maximum_attempts: int = 6,
) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "EURUSD-causal-research/1.0",
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, maximum_attempts + 1):
        try:
            with urllib.request.urlopen(
                request, timeout=60
            ) as response:
                return response.read(), {
                    "date": response.headers.get("Date", ""),
                    "content_type": response.headers.get(
                        "Content-Type", ""
                    ),
                }
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
        ) as exc:
            last_error = exc
            if attempt < maximum_attempts:
                time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"Unable to download {url}") from last_error


def parse_page(payload: bytes) -> tuple[pd.DataFrame, str]:
    decoded = json.loads(payload)
    if decoded.get("error") != []:
        raise RuntimeError(f"Kraken API error: {decoded.get('error')!r}")
    result = decoded.get("result", {})
    if RESULT_KEY not in result or "last" not in result:
        raise RuntimeError("Unexpected Kraken Trades response schema")
    rows = result[RESULT_KEY]
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Kraken Trades response contained no rows")
    if any(len(row) != len(TRADE_COLUMNS) for row in rows):
        raise RuntimeError("Unexpected Kraken trade row schema")
    frame = pd.DataFrame(rows, columns=TRADE_COLUMNS)
    frame["price"] = pd.to_numeric(frame["price"], errors="raise")
    frame["base_volume"] = pd.to_numeric(
        frame["base_volume"], errors="raise"
    )
    frame["trade_time_epoch"] = pd.to_numeric(
        frame["trade_time_epoch"], errors="raise"
    )
    frame["trade_id"] = pd.to_numeric(
        frame["trade_id"], errors="raise"
    ).astype("int64")
    frame["trade_time_utc"] = pd.to_datetime(
        frame["trade_time_epoch"], unit="s", utc=True
    )
    if not frame["reported_side"].isin(["b", "s"]).all():
        raise RuntimeError("Unexpected Kraken reported trade side")
    if not frame["order_type"].isin(["l", "m"]).all():
        raise RuntimeError("Unexpected Kraken order type")
    if not (
        frame["price"].gt(0) & frame["base_volume"].gt(0)
    ).all():
        raise RuntimeError("Invalid Kraken price or volume")
    if frame["trade_id"].duplicated().any():
        raise RuntimeError("Duplicate trade IDs within Kraken page")
    if not frame["trade_id"].is_monotonic_increasing:
        raise RuntimeError("Kraken trade IDs are not increasing")
    if not frame["trade_time_utc"].is_monotonic_increasing:
        raise RuntimeError("Kraken timestamps are not increasing")
    cursor = str(result["last"])
    if not cursor.isdigit():
        raise RuntimeError("Invalid Kraken continuation cursor")
    return frame, cursor


def filter_window(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    return (
        trades[
            trades["trade_time_utc"].ge(start)
            & trades["trade_time_utc"].lt(end)
        ]
        .sort_values(["trade_time_utc", "trade_id"])
        .drop_duplicates("trade_id")
        .reset_index(drop=True)
    )


def aggregate_m5(trades: pd.DataFrame) -> pd.DataFrame:
    frame = trades.copy()
    frame["open_time_utc"] = frame["trade_time_utc"].dt.floor("5min")
    frame["quote_volume"] = frame["price"] * frame["base_volume"]
    frame["reported_buy_base_volume"] = np.where(
        frame["reported_side"].eq("b"), frame["base_volume"], 0.0
    )
    frame["reported_sell_base_volume"] = np.where(
        frame["reported_side"].eq("s"), frame["base_volume"], 0.0
    )
    frame["reported_buy_quote_volume"] = np.where(
        frame["reported_side"].eq("b"), frame["quote_volume"], 0.0
    )
    frame["reported_sell_quote_volume"] = np.where(
        frame["reported_side"].eq("s"), frame["quote_volume"], 0.0
    )
    frame["market_order_count"] = frame["order_type"].eq("m").astype(int)
    grouped = frame.groupby("open_time_utc", sort=True)
    output = grouped.agg(
        open=("price", "first"),
        high=("price", "max"),
        low=("price", "min"),
        close=("price", "last"),
        base_volume=("base_volume", "sum"),
        quote_volume=("quote_volume", "sum"),
        reported_buy_base_volume=(
            "reported_buy_base_volume",
            "sum",
        ),
        reported_sell_base_volume=(
            "reported_sell_base_volume",
            "sum",
        ),
        reported_buy_quote_volume=(
            "reported_buy_quote_volume",
            "sum",
        ),
        reported_sell_quote_volume=(
            "reported_sell_quote_volume",
            "sum",
        ),
        trade_count=("trade_id", "count"),
        market_order_count=("market_order_count", "sum"),
        first_trade_id=("trade_id", "first"),
        last_trade_id=("trade_id", "last"),
    ).reset_index()
    output["close_time_utc"] = (
        output["open_time_utc"] + pd.Timedelta(minutes=5)
    )
    output["reported_side_imbalance"] = (
        output["reported_buy_quote_volume"]
        - output["reported_sell_quote_volume"]
    ) / output["quote_volume"]
    return output[
        [
            "open_time_utc",
            "close_time_utc",
            "open",
            "high",
            "low",
            "close",
            "base_volume",
            "quote_volume",
            "reported_buy_base_volume",
            "reported_sell_base_volume",
            "reported_buy_quote_volume",
            "reported_sell_quote_volume",
            "reported_side_imbalance",
            "trade_count",
            "market_order_count",
            "first_trade_id",
            "last_trade_id",
        ]
    ]


def acquire_date(
    date: str,
    raw_root: Path,
    *,
    force: bool,
    minimum_request_interval_seconds: float,
    last_request_at: float | None,
) -> tuple[pd.DataFrame, dict[str, Any], float | None]:
    start, end = date_window(date)
    cursor = str(start.value - 1)
    frames: list[pd.DataFrame] = []
    pages: list[dict[str, Any]] = []
    page_number = 0
    while True:
        page_path = raw_root / date / f"page_{page_number:03d}.json"
        url = request_url(cursor)
        cached = page_path.exists() and not force
        if cached:
            payload = page_path.read_bytes()
            headers: dict[str, str] = {}
        else:
            if last_request_at is not None:
                delay = (
                    minimum_request_interval_seconds
                    - (time.monotonic() - last_request_at)
                )
                if delay > 0:
                    time.sleep(delay)
            payload, headers = fetch_bytes(url)
            last_request_at = time.monotonic()
            atomic_write(page_path, payload)
        frame, next_cursor = parse_page(payload)
        if int(next_cursor) <= int(cursor):
            raise RuntimeError("Kraken cursor did not advance")
        frames.append(frame)
        pages.append(
            {
                "page": page_number,
                "url": url,
                "path": str(page_path),
                "bytes": len(payload),
                "sha256": sha256_bytes(payload),
                "rows": int(len(frame)),
                "first_trade_utc": frame[
                    "trade_time_utc"
                ].iloc[0].isoformat(),
                "last_trade_utc": frame[
                    "trade_time_utc"
                ].iloc[-1].isoformat(),
                "first_trade_id": int(frame["trade_id"].iloc[0]),
                "last_trade_id": int(frame["trade_id"].iloc[-1]),
                "cursor_in": cursor,
                "cursor_out": next_cursor,
            }
        )
        if frame["trade_time_utc"].iloc[-1] >= end:
            break
        cursor = next_cursor
        page_number += 1
        if page_number >= 100:
            raise RuntimeError(f"Excessive pagination for {date}")
    trades = filter_window(
        pd.concat(frames, ignore_index=True), start, end
    )
    manifest = {
        "date": date,
        "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(),
        "pages": pages,
        "page_count": len(pages),
        "window_trades": int(len(trades)),
        "first_window_trade_utc": (
            trades["trade_time_utc"].iloc[0].isoformat()
            if len(trades)
            else None
        ),
        "last_window_trade_utc": (
            trades["trade_time_utc"].iloc[-1].isoformat()
            if len(trades)
            else None
        ),
    }
    return trades, manifest, last_request_at


def acquire(
    output_root: Path,
    start_date: str,
    end_date: str,
    *,
    force: bool,
    minimum_request_interval_seconds: float,
) -> dict[str, Any]:
    dates = eligible_dates(start_date, end_date)
    if not dates:
        raise RuntimeError("No outcome-blind Neutral dates requested")
    raw_root = output_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    all_trades: list[pd.DataFrame] = []
    date_manifests: list[dict[str, Any]] = []
    last_request_at: float | None = None
    for index, date in enumerate(dates, start=1):
        trades, manifest, last_request_at = acquire_date(
            date,
            raw_root,
            force=force,
            minimum_request_interval_seconds=(
                minimum_request_interval_seconds
            ),
            last_request_at=last_request_at,
        )
        all_trades.append(trades)
        date_manifests.append(manifest)
        if index == 1 or index % 25 == 0 or index == len(dates):
            print(
                f"Kraken EUR/USD {index}/{len(dates)} dates; "
                f"latest={date}; pages={manifest['page_count']}",
                file=sys.stderr,
                flush=True,
            )
    trades = (
        pd.concat(all_trades, ignore_index=True)
        .sort_values(["trade_time_utc", "trade_id"])
        .drop_duplicates("trade_id")
        .reset_index(drop=True)
    )
    if trades["trade_id"].duplicated().any():
        raise RuntimeError("Cross-date duplicate Kraken trade IDs")
    m5 = aggregate_m5(trades)
    parquet_path = output_root / "KRAKEN_EURUSD_M5_EXECUTED_FLOW.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    m5.to_parquet(parquet_path, index=False, compression="zstd")
    raw_chain = hashlib.sha256()
    for date_manifest in date_manifests:
        for page in date_manifest["pages"]:
            raw_chain.update(bytes.fromhex(page["sha256"]))
    expected_grid = pd.DatetimeIndex(
        [
            value
            for date in dates
            for value in pd.date_range(
                date_window(date)[0],
                date_window(date)[1],
                freq="5min",
                inclusive="left",
            )
        ]
    )
    actual_grid = pd.DatetimeIndex(m5["open_time_utc"])
    missing = expected_grid.difference(actual_grid)
    complete_dates = 0
    for date in dates:
        start, end = date_window(date)
        count = m5["open_time_utc"].between(
            start, end, inclusive="left"
        ).sum()
        complete_dates += int(count == 12)
    manifest = {
        "source": "Kraken Spot REST public Trades endpoint",
        "documentation": (
            "https://docs.kraken.com/api-reference/"
            "market-data/get-recent-trades"
        ),
        "rate_limit_documentation": (
            "https://support.kraken.com/articles/"
            "206548367-what-are-the-api-rate-limits-"
        ),
        "authentication_required": False,
        "pair": RESULT_KEY,
        "first_complete_date": dates[0],
        "last_date": dates[-1],
        "requested_dates": len(dates),
        "required_window": (
            "23:45 UTC previous date through 00:45 UTC entry date"
        ),
        "minimum_request_interval_seconds": (
            minimum_request_interval_seconds
        ),
        "date_manifests": date_manifests,
        "raw_pages": int(
            sum(value["page_count"] for value in date_manifests)
        ),
        "raw_page_chain_sha256": raw_chain.hexdigest(),
        "window_trades": int(len(trades)),
        "first_trade_utc": trades["trade_time_utc"].min().isoformat(),
        "last_trade_utc": trades["trade_time_utc"].max().isoformat(),
        "first_trade_id": int(trades["trade_id"].min()),
        "last_trade_id": int(trades["trade_id"].max()),
        "normalized_m5_rows": int(len(m5)),
        "complete_twelve_bar_dates": int(complete_dates),
        "missing_required_m5_bars": int(len(missing)),
        "first_missing_m5_open_utc": (
            missing[0].isoformat() if len(missing) else None
        ),
        "normalized_path": str(parquet_path),
        "normalized_bytes": parquet_path.stat().st_size,
        "normalized_sha256": sha256_file(parquet_path),
    }
    manifest_path = output_root / "MANIFEST.json"
    atomic_write(
        manifest_path,
        json.dumps(manifest, indent=2).encode("utf-8"),
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_ROOT,
    )
    parser.add_argument("--start-date", default=FIRST_COMPLETE_DATE)
    parser.add_argument("--end-date", default=LAST_DATE)
    parser.add_argument(
        "--minimum-request-interval-seconds",
        type=float,
        default=1.05,
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = acquire(
        args.output_root,
        args.start_date,
        args.end_date,
        force=bool(args.force),
        minimum_request_interval_seconds=float(
            args.minimum_request_interval_seconds
        ),
    )
    summary = {
        key: value
        for key, value in manifest.items()
        if key != "date_manifests"
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
