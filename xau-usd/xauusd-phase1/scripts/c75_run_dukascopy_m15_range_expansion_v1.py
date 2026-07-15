from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen Dukascopy M15 range-expansion campaign.")
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from ml.a3_meta_v1.dukascopy_m15_range_expansion import run_m15_range_expansion

    output = run_m15_range_expansion(root, args.contract)
    print(f"A3 ML Dukascopy M15 range expansion: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
