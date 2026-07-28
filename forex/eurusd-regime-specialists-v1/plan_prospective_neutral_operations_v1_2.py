from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd

import plan_prospective_neutral_operations as base

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_prospective_neutral_operations_planner_v1_2.json"
)
LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_OPERATIONS_PLANNER_V1_2_PREREG_2026_07_28.sha256.json"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_operations_plan_v1_2"


@contextmanager
def _v1_2_contract() -> Iterator[None]:
    original = (base.CONFIG_PATH, base.LOCK_PATH, base.SCHEMA_VERSION)
    base.CONFIG_PATH = CONFIG_PATH
    base.LOCK_PATH = LOCK_PATH
    base.SCHEMA_VERSION = SCHEMA_VERSION
    try:
        yield
    finally:
        base.CONFIG_PATH, base.LOCK_PATH, base.SCHEMA_VERSION = original


def load_config() -> dict[str, Any]:
    return base.json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    with _v1_2_contract():
        checked = base.verify_lock()
    config = load_config()
    superseded = config["supersedes"]
    superseded_path = ROOT / superseded["path"]
    superseded_hash = base.sha256_file(superseded_path)
    if superseded_hash != superseded["sha256"]:
        raise RuntimeError("Superseded operations planner lock drift")
    checked[superseded["path"]] = superseded_hash
    return checked


def _event_date(event: Mapping[str, Any]) -> pd.Timestamp:
    return base._utc(event["event_time_utc"]).normalize()


def _ownership_dates(frame: pd.DataFrame) -> set[pd.Timestamp]:
    if frame.empty:
        return set()
    return {
        base._utc(f"{str(value)[:10]}T00:00:00Z")
        for value in frame["eligible_date"]
    }


def _context_stage(
    *,
    event_date: pd.Timestamp,
    target_event_dates: set[pd.Timestamp],
    available_ownership_dates: set[pd.Timestamp],
    evaluated_at_utc: pd.Timestamp,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    context_date = event_date + pd.Timedelta(days=1)
    due_at = context_date + pd.Timedelta(
        seconds=int(config["safe_lags"]["ownership_after_midnight_seconds"])
    )
    if context_date in available_ownership_dates:
        return {
            "stage": "ORACLE_CONTEXT_OWNERSHIP",
            "context_for_oracle_date": event_date,
            "eligible_date": context_date,
            "status": "COMPLETE",
            "due": False,
            "due_at_utc": None,
            "command": None,
            "reason": "Next-day oracle ownership context is available",
        }
    if context_date in target_event_dates:
        return {
            "stage": "ORACLE_CONTEXT_OWNERSHIP",
            "context_for_oracle_date": event_date,
            "eligible_date": context_date,
            "status": "SHARED_WITH_EVENT_DATE_OWNERSHIP",
            "due": False,
            "due_at_utc": due_at,
            "command": None,
            "reason": "A target event on the next date owns the same context capture",
        }
    is_due = evaluated_at_utc >= due_at
    return {
        "stage": "ORACLE_CONTEXT_OWNERSHIP",
        "context_for_oracle_date": event_date,
        "eligible_date": context_date,
        "status": "DUE" if is_due else "SCHEDULED",
        "due": is_due,
        "due_at_utc": due_at,
        "command": (
            config["commands"]["capture_ownership"].format(
                date=context_date.strftime("%Y-%m-%d"),
            )
            if is_due
            else None
        ),
        "reason": "Capture next-day context required by the oracle evaluator",
    }


def _rebuild_schedule(
    plan: dict[str, Any],
    evaluated_at_utc: pd.Timestamp,
) -> None:
    due: list[dict[str, Any]] = [
        {
            "family": event["family"],
            "event_time_utc": event["event_time_utc"],
            **stage,
        }
        for event in plan["events"]
        for stage in event["stages"]
        if stage["due"]
    ]
    due.extend(
        {
            "family": None,
            "event_time_utc": None,
            **stage,
        }
        for stage in plan["global_actions"]
        if stage["due"]
    )
    priority = {
        "OWNERSHIP_CACHE_PREWARM": 0,
        "NEUTRAL_OWNERSHIP": 1,
        "ORACLE_CONTEXT_OWNERSHIP": 1,
    }
    due.sort(
        key=lambda row: (
            base._utc(row["due_at_utc"]),
            priority.get(str(row["stage"]), 2),
            str(row.get("family")),
        )
    )
    scheduled = [
        base._utc(stage["due_at_utc"])
        for event in plan["events"]
        for stage in event["stages"]
        if stage["due_at_utc"] is not None
        and base._utc(stage["due_at_utc"]) > evaluated_at_utc
    ]
    scheduled.extend(
        base._utc(stage["due_at_utc"])
        for stage in plan["global_actions"]
        if stage["due_at_utc"] is not None
        and base._utc(stage["due_at_utc"]) > evaluated_at_utc
    )
    plan["due_actions"] = due
    plan["next_scheduled_action_utc"] = min(scheduled) if scheduled else None
    plan["status"] = "ACTION_DUE" if due else "WAITING_FOR_NEXT_SAFE_ACTION"


def _add_oracle_context_operations(
    plan: dict[str, Any],
    *,
    evaluated_at_utc: pd.Timestamp,
    roots: Mapping[str, Path],
) -> dict[str, Any]:
    config = load_config()
    ownerships, _ = base.load_ownership_evidence(
        roots["neutral_ownership"],
        evaluated_at_utc=evaluated_at_utc,
    )
    available = _ownership_dates(ownerships)
    event_dates = {_event_date(event) for event in plan["events"]}
    required_dates = event_dates | {
        event_date + pd.Timedelta(days=1) for event_date in event_dates
    }
    missing_dates = sorted(required_dates - available)

    plan["global_actions"] = [
        action
        for action in plan["global_actions"]
        if action["stage"] != "OWNERSHIP_CACHE_PREWARM"
    ]
    ownership_cache_status: dict[str, Any] | None = None
    if missing_dates:
        nearest = missing_dates[0]
        ownership_cache_status = base.prewarm_status(
            nearest,
            roots["neutral_ownership"],
            now_utc=evaluated_at_utc,
        )
        plan["global_actions"].insert(
            0,
            base.plan_ownership_cache_action(
                ownership_cache_status,
                evaluated_at_utc=evaluated_at_utc,
                eligible_date=nearest,
                config=config,
            ),
        )

    for event in plan["events"]:
        event["stages"].append(
            _context_stage(
                event_date=_event_date(event),
                target_event_dates=event_dates,
                available_ownership_dates=available,
                evaluated_at_utc=evaluated_at_utc,
                config=config,
            )
        )
    plan["census"]["ownership_cache"] = ownership_cache_status
    plan["census"]["required_ownership_dates"] = len(required_dates)
    plan["census"]["available_required_ownership_dates"] = len(
        required_dates & available
    )
    plan["census"]["missing_required_ownership_dates"] = len(missing_dates)
    plan["oracle_context_ownership_policy"] = {
        **config["oracle_context_ownership"],
        "required_dates": [date.strftime("%Y-%m-%d") for date in sorted(required_dates)],
        "available_dates": [
            date.strftime("%Y-%m-%d") for date in sorted(required_dates & available)
        ],
        "missing_dates": [date.strftime("%Y-%m-%d") for date in missing_dates],
    }
    _rebuild_schedule(plan, evaluated_at_utc)
    return base._serialize(plan)


def build_operations_plan(
    *,
    evaluated_at_utc: Any,
    roots: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    evaluated = base._utc(evaluated_at_utc)
    resolved = base.DEFAULT_ROOTS if roots is None else roots
    with _v1_2_contract():
        plan = base.build_operations_plan(
            evaluated_at_utc=evaluated,
            roots=resolved,
        )
    return _add_oracle_context_operations(
        plan,
        evaluated_at_utc=evaluated,
        roots=resolved,
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
    print(base.json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
