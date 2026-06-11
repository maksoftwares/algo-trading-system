from __future__ import annotations

import sys
from pathlib import Path


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.second_ea_partial_data import render_decision_status, validate_partial_data_decision


REPORT_PATH = PHASE0_ROOT / "outputs" / "reports" / "SECOND_EA_PARTIAL_DATA_OWNER_DECISION_STATUS.md"


def main() -> int:
    decision = validate_partial_data_decision(PHASE0_ROOT)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_decision_status(decision), encoding="utf-8")
    print(f"SECOND_EA_PARTIAL_DATA_DECISION_{decision.status} report={REPORT_PATH}")
    return 0 if decision.status == "OWNER_ACCEPTED_PARTIAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
