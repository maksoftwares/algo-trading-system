from __future__ import annotations

import argparse
import json

from eurusd_regime_specialists.neutral_rates_dollar_sign_consensus_h4 import (
    run_census,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen Neutral rates/dollar H4 research stages."
    )
    parser.add_argument("stage", choices=["census"])
    args = parser.parse_args()
    if args.stage == "census":
        result = run_census()
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
