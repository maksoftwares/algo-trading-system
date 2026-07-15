from __future__ import annotations

import argparse
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
sys.path.insert(0, str(LANE / "src"))

from xau_crossasset_residual.pipeline import finalize_evidence, repair_determinism, run_stage_a  # noqa: E402
from xau_crossasset_residual.correction import finalize_correction_evidence, run_corrections  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-a", action="store_true")
    parser.add_argument("--acquire-only", action="store_true")
    parser.add_argument("--skip-acquisition", action="store_true")
    parser.add_argument("--verify-determinism-repair", action="store_true")
    parser.add_argument("--finalize-evidence", action="store_true")
    parser.add_argument("--review-corrections", action="store_true")
    parser.add_argument("--resume-corrections", action="store_true")
    parser.add_argument("--finalize-corrections", action="store_true")
    parser.add_argument("--test-result", default="")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    if args.finalize_corrections:
        finalize_correction_evidence(LANE, args.test_result)
    elif args.review_corrections or args.resume_corrections:
        run_corrections(LANE, resume_completed_run_one=args.resume_corrections)
    elif args.finalize_evidence:
        finalize_evidence(LANE)
    elif args.verify_determinism_repair:
        repair_determinism(LANE)
    elif args.stage_a or args.acquire_only:
        run_stage_a(LANE, concurrency=args.concurrency, acquire_only=args.acquire_only, skip_acquisition=args.skip_acquisition)
    else:
        parser.error("choose --review-corrections, --finalize-corrections, --stage-a, --acquire-only, --verify-determinism-repair or --finalize-evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
