from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _default_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "config" / "ml" / "mt5_accounts.yaml").exists():
        return cwd
    phase1 = cwd / "xau-usd" / "xauusd-phase1"
    if (phase1 / "config" / "ml" / "mt5_accounts.yaml").exists():
        return phase1
    return cwd


def main() -> int:
    parser = argparse.ArgumentParser(description="C02-01 read-only MT5 account verification.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--accounts", default="A1,A2,A3", help="Comma-separated account labels.")
    parser.add_argument("--worker-account", help="Internal worker mode for one account label.")
    args = parser.parse_args()

    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from ml.a3_meta_v1.account_verification import (  # noqa: PLC0415
        generate_account_verification_matrix,
        verify_account_read_only,
    )

    registry = (args.registry or root / "config" / "ml" / "mt5_accounts.yaml").resolve()
    if args.worker_account:
        record = verify_account_read_only(root, registry, args.worker_account)
        print(json.dumps(record, indent=2))
        return 0 if record.get("status") == "PASS" else 2

    labels = tuple(label.strip() for label in args.accounts.split(",") if label.strip())
    output = generate_account_verification_matrix(
        root,
        registry_path=registry,
        output_json=args.output_json,
        account_labels=labels,
        python_executable=sys.executable,
        worker_script=Path(__file__),
    )
    print(f"C02 account verification matrix: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
