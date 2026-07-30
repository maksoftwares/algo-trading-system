from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.dense_residual_family import (
    run,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "dense_residual_family",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result, candidates, trades, monthly = run()
    write_outputs(result, candidates, trades, monthly, args.output_dir)
    combined = result["combined_broker_window"]["full"]
    print(
        f"{result['status']} "
        f"trades={combined['trades']} "
        f"frequency={combined['trades_per_weekday']:.6f} "
        f"coverage={combined['weekday_coverage']:.6f} "
        f"pf={combined['profit_factor']:.6f} "
        f"stress_pf={combined['stressed_profit_factor']:.6f} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
