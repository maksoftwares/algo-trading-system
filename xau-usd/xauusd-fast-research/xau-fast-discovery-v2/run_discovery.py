from __future__ import annotations

import argparse
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
sys.path.insert(0, str(LANE / "src"))

from xau_fast_discovery.pipeline import run_stage_a


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen XAUUSD Fast Discovery V2 research runner")
    parser.add_argument("command", choices=["stage-a"])
    parser.add_argument("--concurrency", type=int, default=4, choices=range(1, 5))
    parser.add_argument("--skip-acquisition", action="store_true")
    args = parser.parse_args()
    if args.command == "stage-a":
        run_stage_a(LANE, concurrency=args.concurrency, skip_acquisition=args.skip_acquisition)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
