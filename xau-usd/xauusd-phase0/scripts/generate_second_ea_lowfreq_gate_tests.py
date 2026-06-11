from __future__ import annotations

import sys
from pathlib import Path


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.second_ea_lowfreq_gate_report import (
    LOWFREQ_GATE_TEST_PATHS,
    SECOND_EA_FOCUSED_TEST_PATHS,
    run_pytest_verification,
    write_low_frequency_gate_test_report,
)


def main() -> int:
    verifications = [
        run_pytest_verification(PHASE0_ROOT, "Low-frequency gate and safety subset", LOWFREQ_GATE_TEST_PATHS),
        run_pytest_verification(PHASE0_ROOT, "Second-EA focused suite", SECOND_EA_FOCUSED_TEST_PATHS),
    ]
    report_path = write_low_frequency_gate_test_report(PHASE0_ROOT, verifications)
    status = "PASS" if all(result.status == "PASS" for result in verifications) else "FAIL"
    print(f"SECOND_EA_LOW_FREQ_GATE_TESTS_{status} report={report_path}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
