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
    parser = argparse.ArgumentParser(description="Compile and deploy broker-EA shadow ML handoff consumers.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--deploy", action="store_true", help="Copy compiled shadow-consumer EAs and includes to configured MT5 data roots.")
    parser.add_argument("--no-compile", action="store_true", help="Skip scratch MetaEditor compile.")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.broker_shadow_consumer_deploy import deploy_broker_shadow_consumers  # noqa: PLC0415

    output = deploy_broker_shadow_consumers(
        root,
        report_json=args.report_json,
        deploy=args.deploy,
        compile_scratch=not args.no_compile,
    )
    print(f"A3 ML broker shadow consumer deploy status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
