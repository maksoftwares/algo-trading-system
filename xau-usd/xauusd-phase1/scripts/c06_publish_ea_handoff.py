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
    parser = argparse.ArgumentParser(description="Validate and optionally publish A3 ML EA handoff files.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--publish", action="store_true", help="Copy gated handoff files into configured MT5 MQL5/Files roots.")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.ea_handoff import generate_ea_handoff_report  # noqa: PLC0415

    output = generate_ea_handoff_report(root, contract_path=args.contract, publish=args.publish)
    print(f"A3 ML EA handoff status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
