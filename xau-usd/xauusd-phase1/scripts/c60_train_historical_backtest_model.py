from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the quarantined A3 historical MT5 backtest model.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    sys.path.insert(0, str(root))
    from ml.a3_meta_v1.historical_backtest_training import train_historical_backtest_model

    output = train_historical_backtest_model(root, contract_path=args.contract)
    print(f"A3 ML historical backtest training status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
