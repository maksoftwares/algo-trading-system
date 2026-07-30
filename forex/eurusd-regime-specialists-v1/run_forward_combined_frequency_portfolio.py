from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from forward_combined_frequency_portfolio import (
    load_component_summary,
    load_config,
    load_records,
    process,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m15-outcomes", type=Path, required=True)
    parser.add_argument("--m15-summary", type=Path, required=True)
    parser.add_argument("--daily-decisions", type=Path, required=True)
    parser.add_argument("--daily-summary", type=Path, required=True)
    parser.add_argument("--feature-csv", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "frozen_forward_combined_frequency_portfolio_v1.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--enforce-append-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    m15_config = config["components"]["M15_REGIME"]
    daily_config = config["components"]["DAILY_CROSSPAIR"]
    m15_records = load_records(args.m15_outcomes)
    daily_records = load_records(args.daily_decisions)
    m15_summary = load_component_summary(
        args.m15_summary,
        str(m15_config["campaign_id"]),
    )
    daily_summary = load_component_summary(
        args.daily_summary,
        str(daily_config["campaign_id"]),
    )
    ledger, summary = process(
        m15_records,
        m15_summary,
        daily_records,
        daily_summary,
        args.feature_csv,
        config,
    )
    write_outputs(
        ledger,
        summary,
        args.output_dir,
        enforce_append_only=args.enforce_append_only,
    )
    admission = summary["admission"]
    print(
        f"{admission['status']} "
        f"days={admission['complete_validation_weekdays']} "
        f"trades={admission['combined_trades']} "
        f"frequency={admission['trades_per_complete_weekday']:.6f} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
