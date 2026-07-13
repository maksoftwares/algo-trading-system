from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the preregistered one-account XAUUSD specialist replay.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("config/ml/a3_ml_shared_account_replay.json"),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    contract = args.contract if args.contract.is_absolute() else root / args.contract
    sys.path.insert(0, str(root))
    from ml.a3_meta_v1.shared_account_replay import run_shared_account_replay

    output = run_shared_account_replay(root, contract)
    print(f"A3 ML shared-account replay status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
