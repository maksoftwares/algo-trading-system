from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from m15_regime_forward_adjudicator import (
    load_config,
    load_eurusd_bars,
    load_signals,
    process,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signal-csv", type=Path, required=True)
    parser.add_argument("--feature-csv", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT
        / "config"
        / "frozen_m15_regime_forward_adjudication_v1.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--enforce-append-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    signals = load_signals(args.signal_csv, config)
    bars = load_eurusd_bars(args.feature_csv, config)
    records, summary = process(signals, bars, config)
    write_outputs(
        records,
        summary,
        args.output_dir,
        enforce_append_only=args.enforce_append_only,
    )
    print(
        f"{summary['admission']['status']} "
        f"signals={summary['signals']} "
        f"resolved={summary['admission']['resolved_trades']} "
        f"pending={summary['admission']['pending_signals']} "
        "demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
