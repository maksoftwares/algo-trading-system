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
    parser = argparse.ArgumentParser(description="Generate C02 grouping audit and final verdict.")
    parser.add_argument("--root", type=Path, default=_default_root())
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.grouping_verdict import generate_c02_final_verdict, generate_c02_grouping_audit  # noqa: PLC0415

    grouping = generate_c02_grouping_audit(root)
    verdict = generate_c02_final_verdict(root)
    print(f"C02 grouping audit: {grouping}")
    print(f"C02 final verdict: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
