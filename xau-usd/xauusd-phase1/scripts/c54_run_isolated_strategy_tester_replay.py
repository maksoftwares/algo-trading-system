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
    parser = argparse.ArgumentParser(description="Run one bounded isolated Strategy Tester replay launch.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--c53-json", type=Path)
    parser.add_argument("--approval-token", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--allow-isolated-account-context", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.isolated_strategy_tester_replay_launch import run_isolated_strategy_tester_replay_launch  # noqa: PLC0415

    output = run_isolated_strategy_tester_replay_launch(
        root,
        report_json=args.report_json,
        c53_json=args.c53_json,
        approval_token=args.approval_token,
        timeout_seconds=args.timeout_seconds,
        allow_isolated_account_context=args.allow_isolated_account_context,
    )
    print(f"A3 ML isolated Strategy Tester replay launch status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
