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
    parser = argparse.ArgumentParser(description="Preflight or deploy the passive A3 ML MT5 observer files.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--deploy", action="store_true", help="Copy passive observer files to all configured MT5 data roots after preflight passes.")
    parser.add_argument("--no-compile", action="store_true", help="Skip scratch MetaEditor compile.")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.observer_deploy import prepare_observer_deploy  # noqa: PLC0415

    output = prepare_observer_deploy(
        root,
        report_json=args.report_json,
        deploy=args.deploy,
        compile_scratch=not args.no_compile,
    )
    print(f"A3 ML observer deploy status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
