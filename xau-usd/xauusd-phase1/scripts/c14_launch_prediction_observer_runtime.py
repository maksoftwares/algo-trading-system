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
    parser = argparse.ArgumentParser(description="Launch passive A3 ML prediction observers through MT5 startup configs.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--launch", action="store_true", help="Ask each configured terminal to open XAUUSD M5 with the passive observer.")
    parser.add_argument("--wait-seconds", type=int, default=45)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.observer_runtime_attach import launch_prediction_observer_runtime  # noqa: PLC0415

    output = launch_prediction_observer_runtime(
        root,
        report_json=args.report_json,
        launch=args.launch,
        wait_seconds=args.wait_seconds,
    )
    print(f"A3 ML observer runtime attach status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
