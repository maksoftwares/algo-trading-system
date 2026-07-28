from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.prospective_neutral_campaign_orchestration import (
    attach_completed_oracle_labels,
    load_actual_evidence,
    load_complete_paths,
    load_market_evidence,
    load_oracle_evidence,
    load_ownership_evidence,
    process_campaign,
    route_operational_signals,
)
from eurusd_regime_specialists.prospective_neutral_campaign_orchestration import (
    load_config as load_campaign_config,
)
from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    build_signal_ledger,
)
from eurusd_regime_specialists.prospective_neutral_validation import (
    evaluate_validation,
    verify_lock,
)


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return timestamp.tz_convert("UTC").as_unit("ns")


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def build_validation_status(*, evaluated_at_utc: Any) -> dict[str, Any]:
    """Build a local, immutable-evidence-only validation snapshot."""
    verify_lock()
    evaluated = _utc(evaluated_at_utc)
    roots = {
        name: Path(path)
        for name, path in load_campaign_config()["evidence_roots"].items()
    }
    campaign = process_campaign(
        evaluated_at_utc=evaluated,
        roots=roots,
        persist=False,
    )
    actuals, actual_census = load_actual_evidence(
        roots["consensus_and_actual"],
        evaluated_at_utc=evaluated,
    )
    markets, market_census = load_market_evidence(
        roots["event_market"],
        evaluated_at_utc=evaluated,
    )
    ownerships, ownership_census = load_ownership_evidence(
        roots["neutral_ownership"],
        evaluated_at_utc=evaluated,
    )
    paths, path_census = load_complete_paths(
        roots["trade_path"],
        evaluated_at_utc=evaluated,
    )
    oracle, completed_dates, oracle_census = load_oracle_evidence(
        roots["oracle_evaluation"],
        roots["neutral_ownership"],
        evaluated_at_utc=evaluated,
    )
    signals, signal_census = build_signal_ledger(actuals, markets, ownerships)
    routed = route_operational_signals(signals, paths)
    evaluated_routed = attach_completed_oracle_labels(
        routed,
        oracle,
        completed_dates,
        evaluated_at_utc=evaluated,
    )
    validation = evaluate_validation(
        evaluated_routed,
        paths,
        oracle,
        completed_dates,
        evaluated_at_utc=evaluated,
    )
    return _serialize(
        {
            "schema_version": "eurusd_neutral_prospective_validation_status_v1",
            "evaluated_at_utc": evaluated,
            "status": validation["status"],
            "campaign_status": campaign["status"],
            "validation": validation,
            "evidence_census": {
                **actual_census,
                **market_census,
                **ownership_census,
                **path_census,
                **oracle_census,
                **signal_census,
            },
            "evidence_inventory_sha256": campaign[
                "evidence_inventory_sha256"
            ],
            "ledger_inventory_sha256": campaign["ledger_inventory_sha256"],
            "historical_pnl_loaded": False,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    )


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
