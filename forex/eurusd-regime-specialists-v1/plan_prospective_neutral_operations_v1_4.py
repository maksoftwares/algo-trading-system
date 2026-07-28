from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

import plan_prospective_neutral_operations as base
import plan_prospective_neutral_operations_v1_2 as schedule
import plan_prospective_neutral_operations_v1_3 as prior

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_prospective_neutral_operations_planner_v1_4.json"
)
LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_OPERATIONS_PLANNER_V1_4_PREREG_2026_07_28.sha256.json"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_operations_plan_v1_4"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    prior.verify_lock()
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("Operations planner V1.4 is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = base.sha256_file(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Operations planner V1.4 lock mismatch: {relative}")
        checked[relative] = actual
    config = load_config()
    superseded = config["supersedes"]
    superseded_hash = base.sha256_file(ROOT / superseded["path"])
    if superseded_hash != superseded["sha256"]:
        raise RuntimeError("Superseded operations planner V1.3 lock drift")
    checked[superseded["path"]] = superseded_hash
    return checked


def _clamp_forecast_deadlines(
    plan: dict[str, Any],
    *,
    evaluated_at_utc: pd.Timestamp,
) -> dict[str, Any]:
    config = load_config()
    seconds = int(
        config["forecast_deadline_gate"][
            "forecast_deadline_seconds_before_release"
        ]
    )
    forecast_command = schedule.load_config()["commands"]["capture_forecast"]
    clamped = 0
    for event in plan["events"]:
        event_time = base._utc(event["event_time_utc"])
        deadline = event_time - pd.Timedelta(seconds=seconds)
        for stage in event["stages"]:
            if stage["stage"] != "PRE_RELEASE_FORECAST":
                continue
            if stage["status"] not in {"SCHEDULED", "DUE"}:
                continue
            due_at = base._utc(stage["due_at_utc"])
            if due_at <= deadline:
                continue
            is_due = evaluated_at_utc >= deadline
            stage["due_at_utc"] = deadline
            stage["due"] = is_due
            stage["status"] = "DUE" if is_due else "SCHEDULED"
            stage["command"] = forecast_command if is_due else None
            stage["reason"] = (
                "Final admissible poll clamped to the frozen forecast deadline"
            )
            clamped += 1
    plan["schema_version"] = SCHEMA_VERSION
    plan["forecast_deadline_gate"] = {
        **config["forecast_deadline_gate"],
        "clamped_event_stages": clamped,
    }
    schedule._rebuild_schedule(plan, evaluated_at_utc)
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
    return _clamp_forecast_deadlines(
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
