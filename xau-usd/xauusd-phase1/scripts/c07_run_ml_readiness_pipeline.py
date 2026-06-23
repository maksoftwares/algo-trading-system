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
    parser = argparse.ArgumentParser(description="Run the offline A3 ML readiness chain through EA handoff validation.")
    parser.add_argument("--root", type=Path, default=_default_root())
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--publish", action="store_true", help="Allow C06 to publish only if all gates are ready.")
    args = parser.parse_args()
    root = args.root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ml.a3_meta_v1.pipeline_orchestrator import run_offline_prediction_readiness_pipeline  # noqa: PLC0415

    output = run_offline_prediction_readiness_pipeline(root, report_json=args.report_json, publish=args.publish)
    print(f"A3 ML pipeline run status: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
