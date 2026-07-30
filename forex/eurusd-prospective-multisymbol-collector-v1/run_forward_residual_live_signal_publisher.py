from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from src.forward_residual_live_signal_publisher import (
    load_json_list,
    load_publisher_config,
    process_once,
    verify_lock,
    write_outputs,
)
from src.forward_residual_regime_specialist import (
    load_config as load_strategy_config,
)
from src.forward_residual_regime_specialist import load_upstream_owned_dates
from src.forward_selective_learner import load_forward_bars

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-csv", type=Path, required=True)
    parser.add_argument("--residual-decisions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verify_lock()
    strategy_config = load_strategy_config()
    publisher_config = load_publisher_config()
    grouped = load_forward_bars(args.feature_csv, strategy_config)
    prior_records = load_json_list(args.residual_decisions)
    upstream_dates = load_upstream_owned_dates(strategy_config)
    decisions_path = (
        args.output_dir / "FORWARD_RESIDUAL_LIVE_SIGNALS.json"
    )
    existing = load_json_list(decisions_path)
    records, summary = process_once(
        grouped,
        prior_records,
        upstream_dates,
        existing,
        datetime.now(UTC),
        strategy_config,
        publisher_config,
    )
    write_outputs(records, summary, args.output_dir)
    print(
        f"{summary['status']} "
        f"decisions={summary['published_decisions']} "
        f"eligible={summary['eligible_signals']} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
