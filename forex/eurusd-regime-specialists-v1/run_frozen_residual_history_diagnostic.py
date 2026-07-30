from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.frozen_residual_history_diagnostic import (
    run,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "frozen_residual_history_diagnostic",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, result, combined, monthly = run()
    write_outputs(records, result, combined, monthly, args.output_dir)
    full = result["combined_portfolio"]["full"]
    print(
        f"{result['status']} "
        f"trades={full['trades']} "
        f"frequency={full['trades_per_weekday']:.6f} "
        f"coverage={full['weekday_coverage']:.6f} "
        f"pf={full['profit_factor']:.6f} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
