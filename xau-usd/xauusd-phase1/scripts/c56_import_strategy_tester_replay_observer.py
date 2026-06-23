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
    parser = argparse.ArgumentParser(description="Import Strategy Tester replay rows as quarantined observer-only evidence.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--c53-json", type=Path)
    parser.add_argument("--c54-json", type=Path)
    parser.add_argument("--c55-json", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.strategy_tester_replay_observer_import import (  # noqa: PLC0415
        import_strategy_tester_replay_observer_evidence,
    )

    output = import_strategy_tester_replay_observer_evidence(
        root,
        report_json=args.report_json,
        c53_json=args.c53_json,
        c54_json=args.c54_json,
        c55_json=args.c55_json,
    )
    print(f"A3 ML replay observer import status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
