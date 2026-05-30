from __future__ import annotations

import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "raw" / "macro" / "FRED_DEXCHUS.csv"
SOURCE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXCHUS"


def main() -> int:
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "phase0-research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(payload)
    print(f"Wrote {len(payload)} bytes to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
