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
    parser = argparse.ArgumentParser(description="Preflight or run the A3 ML live read-only refresh through EA handoff validation.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--requested-start-utc")
    parser.add_argument("--max-tick-days", type=int)
    parser.add_argument("--execute-live-readonly", action="store_true", help="Run read-only MT5 verification/export/history before C07.")
    parser.add_argument("--publish", action="store_true", help="Allow C06 publish only if every upstream gate is ready.")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.live_refresh_orchestrator import run_live_refresh_or_preflight  # noqa: PLC0415

    output = run_live_refresh_or_preflight(
        root,
        report_json=args.report_json,
        execute_live_readonly=args.execute_live_readonly,
        requested_start_utc=args.requested_start_utc,
        max_tick_days=args.max_tick_days,
        publish=args.publish,
    )
    print(f"A3 ML live refresh status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
