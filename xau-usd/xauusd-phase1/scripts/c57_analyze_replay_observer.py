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
    parser = argparse.ArgumentParser(description="Analyze quarantined Strategy Tester replay observer evidence.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--c56-json", type=Path)
    parser.add_argument("--c03-json", type=Path)
    parser.add_argument("--c01-json", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.replay_observer_analysis import analyze_replay_observer_evidence  # noqa: PLC0415

    output = analyze_replay_observer_evidence(
        root,
        report_json=args.report_json,
        c56_json=args.c56_json,
        c03_json=args.c03_json,
        c01_json=args.c01_json,
    )
    print(f"A3 ML replay observer analysis status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
