from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path(
    "D:/AlgoTradingData/research/"
    "eurusd-neutral-futures-participation-v1"
)
SYMBOLS = {
    "EURO_FX": "6E=F",
    # Yahoo does not expose a stable continuous ICE Dollar Index futures
    # history. UUP is used as a transparent exchange-traded dollar-bull
    # participation proxy; its direction is inverted for EURUSD.
    "DOLLAR_ETF": "UUP",
}


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
        prefix=f".{path.name}.", dir=path.parent
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


def utc_epoch(date_text: str) -> int:
    value = datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc)
    return int(value.timestamp())


def chart_url(
    symbol: str, start_date: str, end_exclusive: str
) -> str:
    # Yahoo's chart router accepts the literal futures suffix ("=F") in
    # the path but returns 404 when the equals sign is percent-encoded.
    encoded = urllib.parse.quote(symbol, safe="=")
    query = urllib.parse.urlencode(
        {
            "period1": utc_epoch(start_date),
            "period2": utc_epoch(end_exclusive),
            "interval": "1d",
            "events": "history",
        }
    )
    return (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{encoded}?{query}"
    )


def fetch(url: str) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 EURUSD-causal-research/1.0"
            ),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
            headers = {
                "content_type": response.headers.get(
                    "Content-Type", ""
                ),
                "etag": response.headers.get("ETag", ""),
                "last_modified": response.headers.get(
                    "Last-Modified", ""
                ),
                "transport": "python_urllib",
            }
        return payload, headers
    except urllib.error.HTTPError as error:
        if error.code not in {403, 404, 429}:
            raise

    # On Windows, the endpoint sometimes applies a different transient
    # throttle to Python's HTTP stack while accepting the standard
    # PowerShell web client. This is a single transparent fallback against
    # the same public URL; it does not change identity, credentials, or IP.
    helper = Path(__file__).resolve().parent / "fetch_public_chart.ps1"
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(helper),
            "-Url",
            url,
        ],
        capture_output=True,
        check=False,
        timeout=90,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "PowerShell source fallback failed: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    payload = completed.stdout.lstrip(b"\xef\xbb\xbf\r\n\t ")
    if not payload.startswith(b"{"):
        raise RuntimeError(
            "PowerShell fallback returned non-JSON data: "
            f"{payload[:80]!r}"
        )
    return payload, {
        "content_type": "application/json",
        "etag": "",
        "last_modified": "",
        "transport": "powershell_invoke_webrequest_fallback",
    }


def normalize(payload: bytes, expected_symbol: str) -> tuple[
    pd.DataFrame, dict[str, Any]
]:
    document = json.loads(payload)
    error = document.get("chart", {}).get("error")
    if error:
        raise RuntimeError(f"Chart source error: {error}")
    results = document.get("chart", {}).get("result") or []
    if len(results) != 1:
        raise RuntimeError("Expected exactly one chart result")
    result = results[0]
    meta = result["meta"]
    if meta.get("symbol") != expected_symbol:
        raise RuntimeError(
            f"Unexpected symbol {meta.get('symbol')!r}"
        )
    timestamps = result.get("timestamp") or []
    quotes = result["indicators"]["quote"]
    if len(quotes) != 1:
        raise RuntimeError("Expected exactly one quote array")
    quote = quotes[0]
    lengths = {
        len(timestamps),
        *(
            len(quote.get(column) or [])
            for column in ("open", "high", "low", "close", "volume")
        ),
    }
    if len(lengths) != 1:
        raise RuntimeError(f"Mismatched source arrays: {lengths}")
    frame = pd.DataFrame(
        {
            "source_timestamp_utc": pd.to_datetime(
                timestamps, unit="s", utc=True
            ),
            "open": quote["open"],
            "high": quote["high"],
            "low": quote["low"],
            "close": quote["close"],
            "volume": quote["volume"],
        }
    )
    exchange_tz = str(meta["exchangeTimezoneName"])
    frame["trade_date"] = (
        frame["source_timestamp_utc"]
        .dt.tz_convert(exchange_tz)
        .dt.date.astype(str)
    )
    frame["symbol"] = expected_symbol
    frame = frame[
        [
            "symbol",
            "trade_date",
            "source_timestamp_utc",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ].sort_values("source_timestamp_utc")
    frame = frame.drop_duplicates("trade_date", keep="last")
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    valid = frame[
        ["open", "high", "low", "close", "volume"]
    ].notna().all(axis=1)
    frame["source_row_valid"] = (
        valid
        & frame["open"].gt(0)
        & frame["high"].gt(0)
        & frame["low"].gt(0)
        & frame["close"].gt(0)
        & frame["volume"].gt(0)
    )
    return frame.reset_index(drop=True), {
        "currency": meta.get("currency"),
        "exchange_name": meta.get("exchangeName"),
        "full_exchange_name": meta.get("fullExchangeName"),
        "instrument_type": meta.get("instrumentType"),
        "exchange_timezone": exchange_tz,
        "data_granularity": meta.get("dataGranularity"),
    }


def acquire(
    output_root: Path,
    start_date: str,
    end_exclusive: str,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    manifests: dict[str, Any] = {}
    for name, symbol in SYMBOLS.items():
        url = chart_url(symbol, start_date, end_exclusive)
        payload, headers = fetch(url)
        raw_path = output_root / f"{name}_RAW.json"
        atomic_write(raw_path, payload)
        frame, metadata = normalize(payload, symbol)
        parquet_path = output_root / f"{name}_DAILY.parquet"
        frame.to_parquet(parquet_path, index=False)
        manifests[name] = {
            "symbol": symbol,
            "url": url,
            "raw_path": str(raw_path),
            "raw_bytes": len(payload),
            "raw_sha256": sha256_bytes(payload),
            "normalized_path": str(parquet_path),
            "normalized_sha256": sha256_file(parquet_path),
            "rows": int(len(frame)),
            "valid_rows": int(frame["source_row_valid"].sum()),
            "first_trade_date": frame["trade_date"].min(),
            "last_trade_date": frame["trade_date"].max(),
            "response_headers": headers,
            "metadata": metadata,
        }
    manifest = {
        "campaign": "eurusd-neutral-futures-participation-v1",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_start_date": start_date,
        "requested_end_exclusive": end_exclusive,
        "source": (
            "Yahoo Finance public chart endpoint; third-party "
            "continuous futures research snapshot"
        ),
        "credentials_used": False,
        "cost_usd": 0.0,
        "revision_warning": (
            "The upstream continuous-contract history may be revised. "
            "Only the hash-pinned local snapshot is admissible."
        ),
        "symbols": manifests,
    }
    manifest_path = output_root / "MANIFEST.json"
    atomic_write(
        manifest_path,
        json.dumps(manifest, indent=2).encode("utf-8"),
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["manifest_sha256"] = sha256_file(manifest_path)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root", type=Path, default=DEFAULT_ROOT
    )
    parser.add_argument("--start-date", default="2018-01-01")
    parser.add_argument(
        "--end-exclusive", default="2026-07-01"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = acquire(
        args.output_root, args.start_date, args.end_exclusive
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
