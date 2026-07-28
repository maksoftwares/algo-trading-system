from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    evaluate_admission,
    load_config,
    verify_lock,
)


def _rows(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        total += len(pd.read_parquet(path))
    return total


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {
            str(key): _serialize(item) for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def operational_status(as_of_utc: Any) -> dict[str, Any]:
    verify_lock()
    cfg = load_config()
    roots = {
        name: Path(path)
        for name, path in cfg["evidence_roots"].items()
    }
    consensus = roots["consensus_and_actual"]
    market = roots["event_market"]
    ownership = roots["neutral_ownership"]
    path = roots["trade_path"]
    ledger = roots["ledger"]
    inventories = {
        "pre_release_snapshot_files": len(
            list(consensus.glob("normalized/*.parquet"))
        ),
        "pre_release_rows": _rows(
            list(consensus.glob("normalized/*.parquet"))
        ),
        "post_release_snapshot_files": len(
            list(
                consensus.glob(
                    "post_release_normalized/*.parquet"
                )
            )
        ),
        "post_release_rows": _rows(
            list(
                consensus.glob(
                    "post_release_normalized/*.parquet"
                )
            )
        ),
        "event_market_snapshot_files": len(
            list(market.glob("normalized/*.parquet"))
        ),
        "event_market_rows": _rows(
            list(market.glob("normalized/*.parquet"))
        ),
        "neutral_ownership_records": len(
            [
                *ownership.glob("*.json"),
                *ownership.glob("*.parquet"),
            ]
        ),
        "trade_path_snapshot_files": len(
            list(path.glob("normalized/*.parquet"))
        ),
        "signal_ledger_files": len(
            list(ledger.glob("signals/*.parquet"))
        ),
        "trade_ledger_files": len(
            list(ledger.glob("trades/*.parquet"))
        ),
    }
    trade_frames = [
        pd.read_parquet(item)
        for item in sorted(ledger.glob("trades/*.parquet"))
    ]
    routed = (
        pd.concat(trade_frames, ignore_index=True)
        if trade_frames
        else pd.DataFrame(
            columns=[
                "signal_id",
                "status",
                "entry_time_utc",
                "exit_time_utc",
                "side",
                "r",
                "extra_half_pip_stress_r",
                "path_evidence_sha256",
            ]
        )
    )
    admission = evaluate_admission(
        routed,
        evaluated_at_utc=as_of_utc,
    )
    if inventories["post_release_rows"] == 0:
        next_action = (
            "WAIT_FOR_FIRST_LINKED_POST_RELEASE_ACTUAL; "
            "NO MARKET OR PATH REQUEST IS DUE"
        )
    elif inventories["event_market_rows"] == 0:
        next_action = "CAPTURE_COMPLETE_EVENT_MARKET_REACTION"
    elif inventories["neutral_ownership_records"] == 0:
        next_action = "CAPTURE_PRIOR_H1_NEUTRAL_OWNERSHIP"
    else:
        next_action = "BUILD_IMMUTABLE_SIGNAL_LEDGER"
    return {
        "schema_version": (
            "eurusd_neutral_prospective_execution_status_v2"
        ),
        "as_of_utc": pd.Timestamp(as_of_utc),
        "campaign_id": cfg["campaign_id"],
        "prospective_start_utc": cfg["prospective_start_utc"],
        "historical_pnl_loaded": False,
        "network_request_made": False,
        "inventories": inventories,
        "admission": admission,
        "next_action": next_action,
        "broker_action_allowed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status",))
    parser.add_argument("--as-of")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    as_of = (
        pd.Timestamp.now(tz="UTC")
        if args.as_of is None
        else pd.Timestamp(args.as_of)
    )
    if as_of.tzinfo is None:
        raise ValueError("--as-of must be timezone-aware")
    result = operational_status(as_of)
    print(json.dumps(_serialize(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
