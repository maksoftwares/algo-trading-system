from __future__ import annotations

import argparse
import json
from typing import Any

import pandas as pd

import run_prospective_neutral_validation_v1_1 as prior
from eurusd_regime_specialists.prospective_neutral_validation_v1_2 import (
    classify_validation_result,
    verify_lock,
)


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return timestamp.tz_convert("UTC").as_unit("ns")


def build_validation_status(*, evaluated_at_utc: Any) -> dict[str, Any]:
    verify_lock()
    result = prior.build_validation_status(
        evaluated_at_utc=evaluated_at_utc
    )
    result["schema_version"] = (
        "eurusd_neutral_prospective_validation_status_v1_2"
    )
    result["validation"] = classify_validation_result(result["validation"])
    result["status"] = result["validation"]["status"]
    result["historical_pnl_loaded"] = False
    result["network_request_made"] = False
    result["broker_action_allowed"] = False
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status"])
    parser.add_argument("--as-of")
    return parser


def main() -> None:
    args = _parser().parse_args()
    evaluated = (
        pd.Timestamp.now(tz="UTC")
        if args.as_of is None
        else _utc(args.as_of)
    )
    result = build_validation_status(evaluated_at_utc=evaluated)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
