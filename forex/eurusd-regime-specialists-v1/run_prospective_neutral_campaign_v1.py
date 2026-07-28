from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.prospective_neutral_campaign_orchestration import (
    process_campaign,
    verify_lock,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status", "process"))
    parser.add_argument("--as-of")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verify_lock()
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if args.as_of is None
        else pd.Timestamp(args.as_of)
    )
    if evaluated.tzinfo is None:
        raise ValueError("--as-of must be timezone-aware")
    result = process_campaign(
        evaluated_at_utc=evaluated,
        persist=args.command == "process",
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
