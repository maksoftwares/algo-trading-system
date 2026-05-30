from __future__ import annotations

from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "raw" / "risk" / "FRED_VXVCLS.csv"
SOURCE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VXVCLS"


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
        OUTPUT_PATH.write_bytes(response.read())
    print(f"VIX term-structure proxy written: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
