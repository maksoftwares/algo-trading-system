from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

import plan_prospective_neutral_operations as base
import plan_prospective_neutral_operations_v1_2 as prior

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_prospective_neutral_operations_planner_v1_3.json"
)
LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_OPERATIONS_PLANNER_V1_3_PREREG_2026_07_28.sha256.json"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_operations_plan_v1_3"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    prior.verify_lock()
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("Operations planner V1.3 is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = base.sha256_file(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Operations planner V1.3 lock mismatch: {relative}")
        checked[relative] = actual
    config = load_config()
    superseded = config["supersedes"]
    superseded_hash = base.sha256_file(ROOT / superseded["path"])
    if superseded_hash != superseded["sha256"]:
        raise RuntimeError("Superseded operations planner V1.2 lock drift")
    checked[superseded["path"]] = superseded_hash
    return checked


def _eligible_date(
    event: Mapping[str, Any],
    stage: Mapping[str, Any],
) -> pd.Timestamp:
    if stage["stage"] == "NEUTRAL_OWNERSHIP":
        return base._utc(event["event_time_utc"]).normalize()
    return base._utc(stage["eligible_date"])


def _gate_ownership_dependencies(
    plan: dict[str, Any],
    *,
    evaluated_at_utc: pd.Timestamp,
) -> dict[str, Any]:
    policy = plan["oracle_context_ownership_policy"]
    missing_dates = [
        base._utc(f"{value}T00:00:00Z") for value in policy["missing_dates"]
    ]
    earliest = missing_dates[0] if missing_dates else None
    cache = plan["census"].get("ownership_cache")
    cache_ready = bool(
        cache is not None and int(cache["missing_safe_symbol_hours"]) == 0
    )
    blocked_pending_cache = 0
    blocked_earlier_date = 0

    for event in plan["events"]:
        for stage in event["stages"]:
            if stage["stage"] not in {
                "NEUTRAL_OWNERSHIP",
                "ORACLE_CONTEXT_OWNERSHIP",
            } or stage["status"] in {
                "COMPLETE",
                "SHARED_WITH_EVENT_DATE_OWNERSHIP",
            }:
                continue
            eligible = _eligible_date(event, stage)
            stage["eligible_date"] = eligible
            due_at = (
                None
                if stage["due_at_utc"] is None
                else base._utc(stage["due_at_utc"])
            )
            if due_at is None or evaluated_at_utc < due_at:
                continue
            if earliest is not None and eligible != earliest:
                stage["status"] = "BLOCKED_EARLIER_OWNERSHIP_DATE"
                stage["due"] = False
                stage["command"] = None
                stage["reason"] = (
                    "Capture earlier required ownership dates before this date"
                )
                blocked_earlier_date += 1
                continue
            if earliest is not None and not cache_ready:
                stage["status"] = "BLOCKED_PENDING_OWNERSHIP_CACHE"
                stage["due"] = False
                stage["command"] = None
                stage["reason"] = (
                    "Complete the bounded zero-gap ownership cache first"
                )
                blocked_pending_cache += 1

    plan["schema_version"] = SCHEMA_VERSION
    plan["ownership_dependency_gate"] = {
        **load_config()["dependency_gate"],
        "earliest_missing_ownership_date": (
            earliest.strftime("%Y-%m-%d") if earliest is not None else None
        ),
        "earliest_date_cache_ready": cache_ready,
        "blocked_pending_cache": blocked_pending_cache,
        "blocked_earlier_date": blocked_earlier_date,
    }
    prior._rebuild_schedule(plan, evaluated_at_utc)
    return base._serialize(plan)


def build_operations_plan(
    *,
    evaluated_at_utc: Any,
    roots: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    evaluated = base._utc(evaluated_at_utc)
    plan = prior.build_operations_plan(
        evaluated_at_utc=evaluated,
        roots=roots,
    )
    return _gate_ownership_dependencies(
        plan,
        evaluated_at_utc=evaluated,
    )


def main() -> int:
    args = base.parse_args()
    verify_lock()
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if args.as_of is None
        else base._utc(args.as_of)
    )
    result = build_operations_plan(evaluated_at_utc=evaluated)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
