from __future__ import annotations

import sys
from pathlib import Path


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.second_ea_campaign_status import generate_second_ea_campaign_status


def main() -> int:
    report = generate_second_ea_campaign_status(PHASE0_ROOT)
    print(f"SECOND_EA_CAMPAIGN_STATUS_{report.status} report={report.report_path}")
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
