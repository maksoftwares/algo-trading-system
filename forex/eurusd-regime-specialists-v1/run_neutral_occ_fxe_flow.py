from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_occ_fxe_flow import (  # noqa: E402
    OUTPUT_ROOT,
    run_census,
    run_neutral_occ_fxe_flow,
    verify_lock,
    write_json,
)
from eurusd_regime_specialists.research import serialize  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        nargs="?",
        choices=("census", "backtest"),
        default="backtest",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "census":
        print(json.dumps(serialize(run_census()), indent=2))
        return 0
    verify_lock()
    result, artifacts = run_neutral_occ_fxe_flow()
    write_json(OUTPUT_ROOT / "RESULT.json", result)
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)
    print(json.dumps(serialize(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
