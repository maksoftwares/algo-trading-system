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
    parser = argparse.ArgumentParser(description="Generate an approval-gated A3 ML contract-expansion config proposal.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--config-json", type=Path)
    parser.add_argument("--allowed-family", action="append", default=[])
    parser.add_argument("--review-reference", default="")
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--write-config", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.contract_expansion_config_proposal import (  # noqa: PLC0415
        generate_contract_expansion_config_proposal,
    )

    output = generate_contract_expansion_config_proposal(
        root,
        report_json=args.report_json,
        allowed_families=tuple(args.allowed_family),
        review_reference=args.review_reference,
        authorize=args.authorize,
        write_config=args.write_config,
        config_json=args.config_json,
    )
    print(f"A3 ML contract expansion config proposal status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
