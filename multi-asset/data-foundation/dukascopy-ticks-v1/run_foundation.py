from __future__ import annotations

import argparse
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
sys.path.insert(0, str(LANE / "src"))

from dukascopy_tick_foundation.pipeline import run_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Dukascopy tick data foundation")
    parser.add_argument("--month", action="append", default=[], help="Acquisition month YYYY-MM; repeatable")
    parser.add_argument("--all-months", action="store_true", help="Acquire the full locked decade")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--skip-acquisition", action="store_true")
    args = parser.parse_args()
    return run_pipeline(LANE, months=args.month, all_months=args.all_months, concurrency=args.concurrency, skip_acquisition=args.skip_acquisition)


if __name__ == "__main__":
    raise SystemExit(main())
