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
    parser = argparse.ArgumentParser(description="Generate fail-closed A3 ML shadow bridge outputs.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.shadow_bridge import generate_shadow_bridge_outputs  # noqa: PLC0415

    output = generate_shadow_bridge_outputs(root, contract_path=args.contract)
    print(f"A3 ML shadow bridge status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
