from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.forward_learner_history_diagnostic import (
    run,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "forward_learner_history_diagnostic",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, result = run()
    write_outputs(records, result, args.output_dir)
    primary = result["primary"]
    print(
        f"{result['status']} "
        f"trades={primary['trades']} "
        f"frequency={primary['trades_per_validation_weekday']:.6f} "
        f"pf={primary['profit_factor']:.6f} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
