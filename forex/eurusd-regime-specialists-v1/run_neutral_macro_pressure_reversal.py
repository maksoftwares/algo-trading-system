from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_macro_pressure_reversal import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "frozen_neutral_macro_pressure_reversal_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "neutral_macro_pressure_reversal",
    )
    args = parser.parse_args()
    result = run(args.config, args.output_dir)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
