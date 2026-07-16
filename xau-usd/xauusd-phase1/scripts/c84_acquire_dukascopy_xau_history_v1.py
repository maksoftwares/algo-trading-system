from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory or acquire missing full-month Dukascopy XAUUSD Bid/Ask ticks."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--acquire-missing", action="store_true")
    parser.add_argument("--month", action="append", default=[])
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    root = args.root.resolve()
    sys.path.insert(0, str(root))
    from ml.a3_meta_v1.dukascopy_xau_history_inventory import run_history_inventory

    output = run_history_inventory(
        root,
        args.contract,
        acquire_missing=args.acquire_missing,
        concurrency=args.concurrency,
        selected_months=args.month,
    )
    print(f"A3 ML R1/R2 Dukascopy source inventory: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
