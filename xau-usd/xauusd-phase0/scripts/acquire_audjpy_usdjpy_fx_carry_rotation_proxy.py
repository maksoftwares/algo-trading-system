from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "reference" / "fx" / "audjpy_usdjpy_daily_yahoo_2015_2025.csv"
SOURCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
SOURCE_SYMBOLS = {
    "audjpy": "AUDJPY=X",
    "usdjpy": "JPY=X",
}


def main() -> int:
    acquired_at = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
    series = {name: _download_symbol(symbol) for name, symbol in SOURCE_SYMBOLS.items()}
    by_date: dict[str, dict[str, object]] = {}
    for name, rows in series.items():
        for row in rows:
            date = str(row["date_utc"])
            target = by_date.setdefault(
                date,
                {
                    "timestamp_utc": row["timestamp_utc"],
                    "date_utc": date,
                    "source": "Yahoo Finance chart API; public non-primary AUDJPY/USDJPY daily FX proxy",
                    "acquired_at_utc": acquired_at,
                },
            )
            target[f"{name}_open"] = row["open"]
            target[f"{name}_high"] = row["high"]
            target[f"{name}_low"] = row["low"]
            target[f"{name}_close"] = row["close"]

    required_columns = {
        "audjpy_open",
        "audjpy_high",
        "audjpy_low",
        "audjpy_close",
        "usdjpy_open",
        "usdjpy_high",
        "usdjpy_low",
        "usdjpy_close",
    }
    rows = [
        row
        for row in by_date.values()
        if required_columns.issubset(row)
        and row["audjpy_close"] is not None
        and row["usdjpy_close"] is not None
    ]
    rows.sort(key=lambda item: str(item["timestamp_utc"]))
    if len(rows) < 1800:
        raise RuntimeError(f"Expected at least 1800 usable merged AUDJPY/USDJPY daily rows, got {len(rows)}.")

    fieldnames = [
        "timestamp_utc",
        "date_utc",
        "audjpy_open",
        "audjpy_high",
        "audjpy_low",
        "audjpy_close",
        "usdjpy_open",
        "usdjpy_high",
        "usdjpy_low",
        "usdjpy_close",
        "source",
        "acquired_at_utc",
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")
    time.sleep(0.1)
    return 0


def _download_symbol(symbol: str) -> list[dict[str, object]]:
    period1 = int(datetime(2015, 1, 1, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(2025, 7, 1, tzinfo=timezone.utc).timestamp())
    query = urllib.parse.urlencode(
        {
            "period1": period1,
            "period2": period2,
            "interval": "1d",
            "events": "history",
        }
    )
    url = f"{SOURCE_URL.format(symbol=urllib.parse.quote(symbol, safe=''))}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "phase0-research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    result = payload["chart"]["result"][0]
    timestamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    rows: list[dict[str, object]] = []
    for index, epoch in enumerate(timestamps):
        close = quote["close"][index]
        if close is None:
            continue
        timestamp = datetime.fromtimestamp(int(epoch), tz=timezone.utc)
        rows.append(
            {
                "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
                "date_utc": timestamp.date().isoformat(),
                "open": quote["open"][index],
                "high": quote["high"][index],
                "low": quote["low"][index],
                "close": close,
            }
        )
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
