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
    parser = argparse.ArgumentParser(description="Prepare one isolated Strategy Tester terminal root for A3 ML replay.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--c51-json", type=Path)
    parser.add_argument("--c52-json", type=Path)
    parser.add_argument("--lane-id", default=None)
    parser.add_argument("--terminal-root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.isolated_strategy_tester_terminal_root import prepare_isolated_strategy_tester_terminal_root  # noqa: PLC0415

    output = prepare_isolated_strategy_tester_terminal_root(
        root,
        report_json=args.report_json,
        c51_json=args.c51_json,
        c52_json=args.c52_json,
        lane_id=args.lane_id,
        terminal_root=args.terminal_root,
    )
    print(f"A3 ML isolated Strategy Tester terminal root status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
