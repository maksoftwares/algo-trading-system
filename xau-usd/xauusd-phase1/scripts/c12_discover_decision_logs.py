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
    parser = argparse.ArgumentParser(description="Discover compatible A3 ML decision/signal logs in configured MT5 Files roots.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.decision_log_discovery import generate_decision_log_discovery_report  # noqa: PLC0415

    output = generate_decision_log_discovery_report(root, report_json=args.report_json)
    print(f"A3 ML decision log discovery report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
