"""Create SHA256 lock sidecars for research hypotheses (pre-run lock step).

Usage: python scripts/lock_lane_b_hypotheses.py [candidate ...]
Defaults to the Lane B candidates when no names are given.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PHASE0_ROOT = Path(__file__).resolve().parents[1]

LANE_B_CANDIDATES = (
    "xau_london_open_expansion_flow_v0",
    "xau_lbma_am_fix_flow_v0",
    "xau_comex_settlement_flow_v0",
)


def main() -> int:
    candidates = tuple(sys.argv[1:]) or LANE_B_CANDIDATES
    for candidate in candidates:
        hypothesis_path = PHASE0_ROOT / "docs" / f"hypothesis_{candidate}.md"
        digest = hashlib.sha256(hypothesis_path.read_bytes()).hexdigest()
        lock = {
            "candidate_id": candidate,
            "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "sha256_hash": digest,
            "status": "LOCKED",
        }
        lock_path = PHASE0_ROOT / "docs" / f"hypothesis_{candidate}.sha256.json"
        lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{candidate} {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
