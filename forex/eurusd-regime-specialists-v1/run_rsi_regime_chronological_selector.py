from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.rsi_regime_chronological_selector import (
    run,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "rsi_regime_chronological_selector",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result, table, combined, monthly = run()
    write_outputs(result, table, combined, monthly, args.output_dir)
    validation = result["locked_validation"]["combined"]
    print(
        f"{result['status']} "
        f"regimes={len(result['selected_regimes_from_development_only'])} "
        f"trades={validation['trades']} "
        f"frequency={validation['trades_per_weekday']:.6f} "
        f"coverage={validation['weekday_coverage']:.6f} "
        f"pf={validation['profit_factor']:.6f} "
        f"stress_pf={validation['plus_0_5_pip_profit_factor']:.6f} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
