from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replay frozen R1/R2 XAUUSD specialists on complete Dukascopy Bid/Ask ticks."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    sys.path.insert(0, str(root))
    from ml.a3_meta_v1.dukascopy_r1_r2_portability import run_r1_r2_portability

    output = run_r1_r2_portability(root, args.contract)
    print(f"A3 ML R1/R2 Dukascopy portability: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
