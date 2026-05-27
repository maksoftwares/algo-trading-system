from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "reference" / "futures" / "gc_continuous_daily_yahoo_2015_2025.csv"
SOURCE_SYMBOL = "GC=F"
SOURCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def main() -> int:
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
    url = f"{SOURCE_URL.format(symbol=urllib.parse.quote(SOURCE_SYMBOL, safe=''))}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "phase0-research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    result = payload["chart"]["result"][0]
    timestamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    rows: list[dict[str, object]] = []
    for index, epoch in enumerate(timestamps):
        volume = quote["volume"][index]
        close = quote["close"][index]
        if volume is None or close is None:
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
                "volume": volume,
                "source_symbol": SOURCE_SYMBOL,
                "source": "Yahoo Finance chart API; non-authoritative continuous futures proxy",
                "acquired_at_utc": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        )

    if len(rows) < 1800:
        raise RuntimeError(f"Expected at least 1800 usable GC daily rows, got {len(rows)}.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")
    time.sleep(0.1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
