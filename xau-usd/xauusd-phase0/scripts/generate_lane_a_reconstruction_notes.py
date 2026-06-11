from __future__ import annotations

import sys
from pathlib import Path


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.lane_a_reconstruction import generate_lane_a_reconstruction_notes


def main() -> int:
    notes = generate_lane_a_reconstruction_notes(PHASE0_ROOT)
    print(f"LANE_A_RULE_RECONSTRUCTION_{notes.status} report={notes.report_path}")
    return 0 if notes.status == "BLOCKED_M1_PRE_RECONSTRUCTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
