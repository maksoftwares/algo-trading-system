from __future__ import annotations

import argparse
import sys
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1]
if str(PHASE1_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE1_ROOT))

from ml.a3_meta_v1.dukascopy_event_census import run_event_census  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the preregistered Dukascopy event census V1."
    )
    parser.add_argument("--contract", type=Path)
    arguments = parser.parse_args()
    print(run_event_census(PHASE1_ROOT, arguments.contract))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
