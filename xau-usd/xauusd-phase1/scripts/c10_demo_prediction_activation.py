from __future__ import annotations

import argparse
from pathlib import Path
import sys


def _default_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "config" / "ml" / "mt5_accounts.yaml").exists():
        return cwd
    phase1 = cwd / "xau-usd" / "xauusd-phase1"
    if (phase1 / "config" / "ml" / "mt5_accounts.yaml").exists():
        return phase1
    return cwd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the A3 ML demo prediction activation gate.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--no-run-pipeline", action="store_true", help="Only inspect existing reports.")
    parser.add_argument("--refresh-live-readonly", action="store_true", help="Run C08 live read-only refresh before activation evaluation.")
    parser.add_argument("--requested-start-utc")
    parser.add_argument("--max-tick-days", type=int)
    parser.add_argument("--publish", action="store_true", help="Publish C06 handoff only if upstream gates are ready.")
    parser.add_argument("--deploy-observer", action="store_true", help="Deploy/redeploy the passive observer files through C09.")
    parser.add_argument("--no-compile-observer", action="store_true", help="Skip C09 scratch compile when --deploy-observer is used.")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.demo_activation import run_demo_prediction_activation  # noqa: PLC0415

    output = run_demo_prediction_activation(
        root,
        report_json=args.report_json,
        run_pipeline=not args.no_run_pipeline,
        refresh_live_readonly=args.refresh_live_readonly,
        requested_start_utc=args.requested_start_utc,
        max_tick_days=args.max_tick_days,
        publish=args.publish,
        deploy_observer=args.deploy_observer,
        compile_observer=not args.no_compile_observer,
    )
    print(f"A3 ML demo prediction activation status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
