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
    parser = argparse.ArgumentParser(description="Repair incomplete latest C02 dataset artifacts through the offline A3 ML pipeline.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--no-repair", action="store_true", help="Only check completeness; do not run the offline repair pipeline.")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.latest_dataset_repair import repair_latest_dataset_if_needed  # noqa: PLC0415

    output = repair_latest_dataset_if_needed(root, report_json=args.report_json, auto_repair=not args.no_repair)
    print(f"A3 ML latest dataset repair status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
