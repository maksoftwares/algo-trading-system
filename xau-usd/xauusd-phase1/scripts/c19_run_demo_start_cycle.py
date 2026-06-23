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
    parser = argparse.ArgumentParser(description="Run the safe A3 ML demo-start cycle.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--no-run-pipeline", action="store_true", help="Only inspect current reports before rehearsal/final summary.")
    parser.add_argument("--refresh-live-readonly", action="store_true", help="Attempt read-only MT5 data refresh through the existing C08/C10 gates.")
    parser.add_argument("--requested-start-utc")
    parser.add_argument("--max-tick-days", type=int)
    parser.add_argument("--auto-publish", action="store_true", help="Publish C06 handoff only if C10 first reaches READY_TO_PUBLISH_HANDOFF.")
    parser.add_argument("--no-rehearsal", action="store_true", help="Skip C18 research-only training rehearsal.")
    parser.add_argument("--no-runtime-audit", action="store_true", help="Skip C20 MT5 Files runtime evidence audit.")
    parser.add_argument("--no-runtime-diagnostic", action="store_true", help="Skip C21 MT5 launch/journal diagnostic.")
    parser.add_argument("--no-post-attach-monitor", action="store_true", help="Skip C22 post-attach runtime monitor.")
    parser.add_argument("--post-attach-timeout-seconds", type=int, default=0, help="How long C22 should wait for runtime evidence.")
    parser.add_argument("--post-attach-poll-seconds", type=int, default=5, help="How often C22 should poll for runtime evidence.")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.demo_start_cycle import run_demo_start_cycle  # noqa: PLC0415

    output = run_demo_start_cycle(
        root,
        report_json=args.report_json,
        run_pipeline=not args.no_run_pipeline,
        refresh_live_readonly=args.refresh_live_readonly,
        requested_start_utc=args.requested_start_utc,
        max_tick_days=args.max_tick_days,
        auto_publish=args.auto_publish,
        run_rehearsal=not args.no_rehearsal,
        run_runtime_audit=not args.no_runtime_audit,
        run_runtime_diagnostic=not args.no_runtime_diagnostic,
        run_post_attach_monitor=not args.no_post_attach_monitor,
        post_attach_timeout_seconds=args.post_attach_timeout_seconds,
        post_attach_poll_seconds=args.post_attach_poll_seconds,
    )
    print(f"A3 ML demo start cycle status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
