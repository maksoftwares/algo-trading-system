from __future__ import annotations

import argparse
import sys
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1]
if str(PHASE1_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE1_ROOT))

from ml.a3_meta_v1.intraday_macro_source import run_intraday_macro_source  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acquire and validate the preregistered intraday macro source V1."
    )
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--month", action="append", default=None)
    parser.add_argument("--skip-acquisition", action="store_true")
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--concurrency", type=int)
    arguments = parser.parse_args()
    print(
        run_intraday_macro_source(
            PHASE1_ROOT,
            arguments.contract,
            months=arguments.month,
            skip_acquisition=arguments.skip_acquisition,
            source_only=arguments.source_only,
            concurrency=arguments.concurrency,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
