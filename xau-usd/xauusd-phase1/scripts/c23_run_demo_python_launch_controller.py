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
    parser = argparse.ArgumentParser(description="Run the safe A3 ML demo Python launch controller.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--run-pipeline", action="store_true", help="Run C19 with its upstream pipeline instead of inspecting current reports.")
    parser.add_argument("--refresh-live-readonly", action="store_true", help="Attempt read-only MT5 data refresh through C19/C10.")
    parser.add_argument("--requested-start-utc")
    parser.add_argument("--max-tick-days", type=int)
    parser.add_argument("--auto-publish", action="store_true", help="Publish C06 handoff only if activation reaches READY_TO_PUBLISH_HANDOFF.")
    parser.add_argument("--post-attach-timeout-seconds", type=int, default=0)
    parser.add_argument("--post-attach-poll-seconds", type=int, default=5)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.demo_python_launch_controller import run_demo_python_launch_controller  # noqa: PLC0415

    output = run_demo_python_launch_controller(
        root,
        report_json=args.report_json,
        run_pipeline=args.run_pipeline,
        refresh_live_readonly=args.refresh_live_readonly,
        requested_start_utc=args.requested_start_utc,
        max_tick_days=args.max_tick_days,
        auto_publish=args.auto_publish,
        post_attach_timeout_seconds=args.post_attach_timeout_seconds,
        post_attach_poll_seconds=args.post_attach_poll_seconds,
    )
    print(f"A3 ML demo Python launch controller status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
