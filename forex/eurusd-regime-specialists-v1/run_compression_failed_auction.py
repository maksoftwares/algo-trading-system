from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.compression_failed_auction import (
    run,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "compression_failed_auction",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result, candidates, trades, monthly = run()
    write_outputs(result, candidates, trades, monthly, args.output_dir)
    capacity = result["outcome_blind_capacity"]["metrics"]
    validation = result["locked_validation"]["metrics"]
    print(
        f"{result['status']} "
        f"candidates={capacity['total']} "
        f"validation_trades={validation['trades']} "
        f"validation_pf={validation['profit_factor']:.6f} "
        f"stress_pf={validation['stressed_profit_factor']:.6f} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
