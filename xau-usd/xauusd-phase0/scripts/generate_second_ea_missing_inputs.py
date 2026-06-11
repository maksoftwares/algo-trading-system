from __future__ import annotations

import sys
from pathlib import Path


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.second_ea_missing_inputs import generate_missing_inputs_report


def main() -> int:
    report = generate_missing_inputs_report(PHASE0_ROOT)
    print(
        "SECOND_EA_MISSING_INPUTS_"
        f"{report.status} missing={len(report.missing_documents)} report={report.report_path}"
    )
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
