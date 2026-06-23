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
    parser = argparse.ArgumentParser(description="Train or refuse the gated A3 ML shadow model artifact.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.model_training import train_or_refuse_model  # noqa: PLC0415

    output = train_or_refuse_model(root, contract_path=args.contract)
    print(f"A3 ML training status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
