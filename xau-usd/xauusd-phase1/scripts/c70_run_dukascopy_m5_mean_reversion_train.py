from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the preregistered Dukascopy XAU M5 mean-reversion train campaign."
    )
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from ml.a3_meta_v1.dukascopy_m5_mean_reversion import (
        run_dukascopy_m5_mean_reversion_train,
    )

    output = run_dukascopy_m5_mean_reversion_train(root, args.contract)
    print(f"A3 ML Dukascopy M5 mean reversion train: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
