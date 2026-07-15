from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.macro_futures_foundation import run_macro_futures_foundation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--refresh-sources", action="store_true")
    args = parser.parse_args()
    report = run_macro_futures_foundation(ROOT, args.contract, refresh_sources=args.refresh_sources)
    print(report)


if __name__ == "__main__":
    main()
