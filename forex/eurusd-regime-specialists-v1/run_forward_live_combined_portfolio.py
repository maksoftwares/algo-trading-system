from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from forward_combined_frequency_portfolio import (
    load_component_summary,
    load_records,
)
from forward_live_combined_portfolio import (
    load_config,
    process,
    verify_lock,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m15-outcomes", type=Path, required=True)
    parser.add_argument("--m15-summary", type=Path, required=True)
    parser.add_argument("--residual-live-signals", type=Path, required=True)
    parser.add_argument("--residual-live-outcomes", type=Path, required=True)
    parser.add_argument("--residual-selection-parity", type=Path, required=True)
    parser.add_argument("--residual-live-summary", type=Path, required=True)
    parser.add_argument("--feature-csv", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "frozen_forward_live_combined_portfolio_v3.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--enforce-append-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verify_lock()
    config = load_config(args.config)
    components = config["components"]
    m15_records = load_records(args.m15_outcomes)
    live_signals = load_records(args.residual_live_signals)
    live_outcomes = load_records(args.residual_live_outcomes)
    selection_parity = load_records(args.residual_selection_parity)
    m15_summary = load_component_summary(
        args.m15_summary,
        str(components["M15_REGIME"]["campaign_id"]),
    )
    residual_summary = load_component_summary(
        args.residual_live_summary,
        str(components["RESIDUAL_LIVE"]["campaign_id"]),
    )
    ledger, summary = process(
        m15_records,
        m15_summary,
        live_signals,
        live_outcomes,
        selection_parity,
        residual_summary,
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
        f"coverage={admission['weekday_trade_coverage']:.6f} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
