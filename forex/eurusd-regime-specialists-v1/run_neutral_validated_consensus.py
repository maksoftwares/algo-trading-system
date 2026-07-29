from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_validated_consensus import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "frozen_neutral_validated_consensus_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "neutral_validated_consensus",
    )
    args = parser.parse_args()
    result = run(args.config, args.output_dir)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
