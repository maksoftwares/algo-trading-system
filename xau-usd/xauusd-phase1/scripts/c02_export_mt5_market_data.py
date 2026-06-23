from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _default_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "config" / "ml" / "mt5_accounts.yaml").exists():
        return cwd
    phase1 = cwd / "xau-usd" / "xauusd-phase1"
    if (phase1 / "config" / "ml" / "mt5_accounts.yaml").exists():
        return phase1
    return cwd


def main() -> int:
    parser = argparse.ArgumentParser(description="C02-02 read-only MT5 bars/ticks export.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--requested-start-utc", required=True)
    parser.add_argument("--snapshot-cutoff-utc")
    parser.add_argument("--dataset-version")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--accounts", default="A1,A2,A3")
    parser.add_argument("--max-tick-days", type=int)
    parser.add_argument("--worker-account")
    args = parser.parse_args()

    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from ml.a3_meta_v1.market_data_export import (  # noqa: PLC0415
        export_account_bars_ticks_read_only,
        generate_bar_tick_export_report,
        parse_utc,
    )

    registry = (args.registry or root / "config" / "ml" / "mt5_accounts.yaml").resolve()
    requested_start = parse_utc(args.requested_start_utc)
    if args.worker_account:
        if not args.snapshot_cutoff_utc or not args.dataset_version:
            raise SystemExit("--snapshot-cutoff-utc and --dataset-version are required in worker mode")
        record = export_account_bars_ticks_read_only(
            root,
            registry,
            args.worker_account,
            requested_start,
            parse_utc(args.snapshot_cutoff_utc),
            args.dataset_version,
            output_root=args.output_root,
            max_tick_days=args.max_tick_days,
        )
        print(json.dumps(record, indent=2))
        return 0 if record.get("status") == "PASS" else 2

    labels = tuple(label.strip() for label in args.accounts.split(",") if label.strip())
    output = generate_bar_tick_export_report(
        root,
        registry_path=registry,
        requested_start_utc=requested_start,
        output_root=args.output_root,
        report_json=args.report_json,
        account_labels=labels,
        max_tick_days=args.max_tick_days,
        python_executable=sys.executable,
        worker_script=Path(__file__),
    )
    print(f"C02 bars/ticks export report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
