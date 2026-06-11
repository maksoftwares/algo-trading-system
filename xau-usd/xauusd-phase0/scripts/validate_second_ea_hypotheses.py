from __future__ import annotations

import sys
from pathlib import Path


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.second_ea_hypotheses import validate_second_ea_campaign_hypotheses


def main() -> int:
    validation = validate_second_ea_campaign_hypotheses(PHASE0_ROOT)
    print(f"SECOND_EA_HYPOTHESIS_VALIDATION_{validation.status} report={validation.report_path}")
    return 0 if validation.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
