from __future__ import annotations

import argparse
import sys
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1]
if str(PHASE1_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE1_ROOT))

from ml.a3_meta_v1.dukascopy_confirmed_event_specialists import (  # noqa: E402
    run_confirmed_event_specialists,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the preregistered Dukascopy confirmed-event specialist campaign."
    )
    parser.add_argument("--contract", type=Path)
    arguments = parser.parse_args()
    report = run_confirmed_event_specialists(PHASE1_ROOT, arguments.contract)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
