from __future__ import annotations

import argparse
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
sys.path.insert(0, str(LANE / "src"))

from xau_continuation.research import finalize_evidence, run_stage_a  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-a", action="store_true")
    parser.add_argument("--acquire-only", action="store_true")
    parser.add_argument("--skip-acquisition", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--test-result", default="")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    if args.finalize:
        finalize_evidence(LANE, args.test_result)
    elif args.stage_a or args.acquire_only:
        run_stage_a(LANE, args.concurrency, args.acquire_only, args.skip_acquisition)
    else:
        parser.error("choose --stage-a, --acquire-only, or --finalize")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
