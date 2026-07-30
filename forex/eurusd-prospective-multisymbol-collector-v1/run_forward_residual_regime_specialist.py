from __future__ import annotations

import argparse
from pathlib import Path

from src.forward_residual_regime_specialist import (
    load_config,
    load_upstream_owned_dates,
    process,
    verify_lock,
    write_outputs,
)
from src.forward_selective_learner import load_forward_bars

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-csv", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=(
            ROOT
            / "config"
            / "frozen_forward_residual_regime_specialist_v1.json"
        ),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--enforce-append-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verify_lock()
    config = load_config(args.config)
    grouped = load_forward_bars(args.feature_csv, config)
    upstream_dates = load_upstream_owned_dates(config)
    records, summary = process(grouped, upstream_dates, config)
    write_outputs(
        records,
        summary,
        args.output_dir,
        enforce_append_only=args.enforce_append_only,
    )
    admission = summary["admission"]
    print(
        f"{summary['status']} "
        f"residual={admission['residual_decisions']} "
        f"eligible={admission['eligible_trades']} "
        f"coverage={admission['incremental_weekday_coverage']:.6f} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
