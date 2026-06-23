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
    parser = argparse.ArgumentParser(description="Check A3 ML demo shadow collection health across MT5 accounts.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--max-stale-seconds", type=int, default=24 * 60 * 60)
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.demo_shadow_collection_health import check_demo_shadow_collection_health  # noqa: PLC0415

    output = check_demo_shadow_collection_health(
        root,
        report_json=args.report_json,
        max_stale_seconds=args.max_stale_seconds,
    )
    print(f"A3 ML demo shadow collection health status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
