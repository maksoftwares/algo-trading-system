from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.frequency_edge_frontier import run, write_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "frequency_edge_frontier",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frontier, combined, result = run()
    write_outputs(frontier, combined, result, args.output_dir)
    metrics = result["combined_historical_diagnostic"]["full"]
    print(
        f"{result['status']} "
        f"trades={metrics['trades']} "
        f"frequency={metrics['trades_per_weekday']:.6f} "
        f"coverage={metrics['weekday_coverage']:.6f} "
        f"pf={metrics['profit_factor']:.6f} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
