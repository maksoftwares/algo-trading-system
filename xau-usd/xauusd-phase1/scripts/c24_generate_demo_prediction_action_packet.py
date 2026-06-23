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
    parser = argparse.ArgumentParser(description="Generate the A3 ML demo prediction action packet.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--refresh-live-readonly", action="store_true", help="Attempt read-only MT5 data refresh through C23/C19/C10.")
    parser.add_argument("--requested-start-utc")
    parser.add_argument("--max-tick-days", type=int)
    parser.add_argument("--post-attach-timeout-seconds", type=int, default=0)
    parser.add_argument("--post-attach-poll-seconds", type=int, default=5)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.demo_prediction_action_packet import generate_demo_prediction_action_packet  # noqa: PLC0415

    output = generate_demo_prediction_action_packet(
        root,
        report_json=args.report_json,
        refresh_live_readonly=args.refresh_live_readonly,
        requested_start_utc=args.requested_start_utc,
        max_tick_days=args.max_tick_days,
        post_attach_timeout_seconds=args.post_attach_timeout_seconds,
        post_attach_poll_seconds=args.post_attach_poll_seconds,
    )
    print(f"A3 ML demo prediction action packet: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
