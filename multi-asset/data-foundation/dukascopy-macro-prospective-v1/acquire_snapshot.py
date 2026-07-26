from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

from src.snapshot import completed_hour_floor, parse_utc, run


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire completed macro tick hours")
    parser.add_argument("--end-exclusive", help="UTC hour; defaults to completed hour")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    end = (
        parse_utc(args.end_exclusive)
        if args.end_exclusive
        else completed_hour_floor(datetime.now(UTC))
    )
    print(json.dumps(run(ROOT, end, args.concurrency), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
