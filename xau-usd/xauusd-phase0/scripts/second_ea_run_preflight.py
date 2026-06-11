from __future__ import annotations

import sys
from pathlib import Path


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.second_ea_preflight import evaluate_second_ea_preflight, render_preflight_report


REPORT_PATH = PHASE0_ROOT / "outputs" / "reports" / "SECOND_EA_RUN_PREFLIGHT.md"


def main() -> int:
    result = evaluate_second_ea_preflight(PHASE0_ROOT)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_preflight_report(result), encoding="utf-8")
    print(f"SECOND_EA_RUN_PREFLIGHT_{result.status} report={REPORT_PATH}")
    return 0 if result.matrix_runs_allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
