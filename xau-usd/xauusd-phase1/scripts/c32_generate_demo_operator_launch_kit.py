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
    parser = argparse.ArgumentParser(description="Generate the A3 ML demo operator attach/watch launch kit.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--kit-script", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.demo_operator_launch_kit import generate_demo_operator_launch_kit  # noqa: PLC0415

    output = generate_demo_operator_launch_kit(root, report_json=args.report_json, kit_script=args.kit_script)
    print(f"A3 ML demo operator launch kit status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
