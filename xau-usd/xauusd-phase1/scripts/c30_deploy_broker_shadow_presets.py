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
    parser = argparse.ArgumentParser(description="Deploy safe passive broker-shadow MT5 presets for A3 ML read-path checks.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--deploy", action="store_true", help="Write safe passive .set files into configured MT5 MQL5/Presets folders.")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.broker_shadow_preset_deploy import deploy_broker_shadow_presets  # noqa: PLC0415

    output = deploy_broker_shadow_presets(root, report_json=args.report_json, deploy=args.deploy)
    print(f"A3 ML broker shadow preset deploy status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
