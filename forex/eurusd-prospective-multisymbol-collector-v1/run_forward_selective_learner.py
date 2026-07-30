from __future__ import annotations

import argparse
from pathlib import Path

from src.forward_selective_learner import (
    load_config,
    load_forward_bars,
    process,
    write_outputs,
)


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-csv", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "frozen_forward_selective_learner_v1.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    grouped = load_forward_bars(args.feature_csv, config)
    records, summary = process(grouped, config)
    write_outputs(records, summary, args.output_dir)
    print(
        f"{summary['status']} "
        f"resolved={summary['resolved_training_days']} "
        f"eligible={summary['admission']['eligible_trades']}"
    )


if __name__ == "__main__":
    main()
