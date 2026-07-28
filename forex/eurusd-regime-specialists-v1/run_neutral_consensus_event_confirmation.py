from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_consensus_event_confirmation import (  # noqa: E402
    OUTPUT_ROOT,
    run_backtest,
    run_census,
    verify_lock,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("census", "backtest"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verify_lock()
    if args.command == "census":
        result, candidates = run_census()
        write_json(OUTPUT_ROOT / "CENSUS.json", result)
        candidates.to_csv(
            OUTPUT_ROOT / "CANDIDATES.csv", index=False
        )
        print(json.dumps(result, indent=2))
        return 0
    result, artifacts = run_backtest()
    write_json(OUTPUT_ROOT / "RESULT.json", result)
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
