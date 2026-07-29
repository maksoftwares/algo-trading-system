from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import plan_prospective_neutral_operations_v1_4 as planner

ROOT = Path(__file__).resolve().parent
OPERATIONS_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_MACRO_OPERATIONS_"
    "2026_07_29.sha256.json"
)
FORECAST_NETWORK_SAFETY_LEAD_SECONDS = 15
RETRY_SECONDS = 30

UV_PREFIX = (
    "uv run --offline --with pandas --with numpy --with pyarrow "
    "--with scikit-learn python "
)
COMMAND_PATTERNS = {
    "OWNERSHIP_CACHE_PREWARM": re.compile(
        rf"^{UV_PREFIX}prewarm_prospective_neutral_ownership\.py capture "
        r"--eligible-date \d{4}-\d{2}-\d{2} --max-new-requests 120$"
    ),
    "PRE_RELEASE_FORECAST": re.compile(
        rf"^{UV_PREFIX}capture_prospective_tradingview_consensus\.py "
        r"capture --days-ahead 60$"
    ),
    "NEUTRAL_OWNERSHIP": re.compile(
        rf"^{UV_PREFIX}capture_prospective_neutral_ownership\.py capture "
        r"--eligible-date \d{4}-\d{2}-\d{2}$"
    ),
    "ORACLE_CONTEXT_OWNERSHIP": re.compile(
        rf"^{UV_PREFIX}capture_prospective_neutral_ownership\.py capture "
        r"--eligible-date \d{4}-\d{2}-\d{2}$"
    ),
    "POST_RELEASE_ACTUAL": re.compile(
        rf"^{UV_PREFIX}capture_prospective_tradingview_actuals\.py capture$"
    ),
    "EVENT_MARKET": re.compile(
        rf"^{UV_PREFIX}capture_prospective_dukascopy_event_m5\.py capture "
        r"--event-time \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    ),
    "CAMPAIGN_PROCESS": re.compile(
        rf"^{UV_PREFIX}run_prospective_neutral_campaign_v1\.py process "
        r"--as-of \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    ),
    "TRADE_PATH": re.compile(
        rf"^{UV_PREFIX}capture_prospective_eurusd_trade_path\.py capture "
        r"--signal-id [A-Za-z0-9_.:-]+ --entry-time "
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    ),
    "ORACLE_EVALUATION": re.compile(
        rf"^{UV_PREFIX}capture_prospective_neutral_oracle_day\.py capture "
        r"--oracle-date \d{4}-\d{2}-\d{2}$"
    ),
}


@dataclass(frozen=True)
class PlannedOperation:
    due_at_utc: datetime
    execute_at_utc: datetime
    stage: str
    family: str | None
    event_time_utc: datetime | None
    command: str


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Macro operations require timezone-aware UTC")
    return parsed.astimezone(timezone.utc)


def verify_operations_lock() -> dict[str, Any]:
    lock = json.loads(OPERATIONS_LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_first_future_operation") is not True
        or lock.get("strategy_or_signal_logic_changed") is not False
        or lock.get("historical_pnl_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Macro operations lock is incomplete")
    for relative, expected in lock["files"].items():
        if _sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"Macro operations drift: {relative}")
    reference = lock["frozen_planner_contract"]
    if _sha256_file(ROOT / reference["path"]) != reference["sha256"]:
        raise RuntimeError("Frozen operations planner reference drift")
    planner.verify_lock()
    return lock


def _validate_command(stage: str, command: str) -> list[str]:
    pattern = COMMAND_PATTERNS.get(stage)
    if pattern is None or pattern.fullmatch(command) is None:
        raise RuntimeError(f"Rejected non-frozen macro operation: {stage}")
    return shlex.split(command, posix=True)


def _command_for_scheduled_stage(
    stage: Mapping[str, Any],
    *,
    event: Mapping[str, Any] | None,
    plan: Mapping[str, Any],
) -> str | None:
    config = planner.schedule.load_config()
    name = str(stage["stage"])
    if name == "OWNERSHIP_CACHE_PREWARM":
        eligible = plan["ownership_dependency_gate"][
            "earliest_missing_ownership_date"
        ]
        return config["commands"]["prewarm_ownership"].format(date=eligible)
    if name == "PRE_RELEASE_FORECAST":
        return config["commands"]["capture_forecast"]
    if name in {"NEUTRAL_OWNERSHIP", "ORACLE_CONTEXT_OWNERSHIP"}:
        eligible = _utc(stage["eligible_date"]).strftime("%Y-%m-%d")
        return config["commands"]["capture_ownership"].format(date=eligible)
    if name == "POST_RELEASE_ACTUAL":
        return config["commands"]["capture_actual"]
    if name == "EVENT_MARKET" and event is not None:
        event_time = _utc(event["event_time_utc"]).strftime("%Y-%m-%dT%H:%M:%SZ")
        return config["commands"]["capture_event_market"].format(
            event_time=event_time
        )
    if name == "ORACLE_EVALUATION" and event is not None:
        oracle_date = _utc(event["event_time_utc"]).strftime("%Y-%m-%d")
        return config["commands"]["capture_oracle"].format(date=oracle_date)
    return None


def next_planned_operation(plan: Mapping[str, Any]) -> PlannedOperation | None:
    candidates: list[tuple[Mapping[str, Any], Mapping[str, Any] | None]] = []
    for stage in plan["global_actions"]:
        candidates.append((stage, None))
    for event in plan["events"]:
        for stage in event["stages"]:
            candidates.append((stage, event))
    scheduled = [
        (stage, event)
        for stage, event in candidates
        if stage.get("status") == "SCHEDULED"
        and stage.get("due_at_utc") is not None
    ]
    if not scheduled:
        return None
    earliest = min(_utc(stage["due_at_utc"]) for stage, _event in scheduled)
    priority = {
        "OWNERSHIP_CACHE_PREWARM": 0,
        "NEUTRAL_OWNERSHIP": 1,
        "ORACLE_CONTEXT_OWNERSHIP": 1,
    }
    at_clock = [
        (stage, event)
        for stage, event in scheduled
        if _utc(stage["due_at_utc"]) == earliest
    ]
    at_clock.sort(
        key=lambda pair: (
            priority.get(str(pair[0]["stage"]), 2),
            str(pair[1].get("family") if pair[1] else ""),
        )
    )
    for stage, event in at_clock:
        command = _command_for_scheduled_stage(stage, event=event, plan=plan)
        if command is None:
            continue
        name = str(stage["stage"])
        _validate_command(name, command)
        event_time = (
            None if event is None else _utc(event["event_time_utc"])
        )
        execute_at = earliest
        if name == "PRE_RELEASE_FORECAST":
            execute_at -= timedelta(seconds=FORECAST_NETWORK_SAFETY_LEAD_SECONDS)
        return PlannedOperation(
            due_at_utc=earliest,
            execute_at_utc=execute_at,
            stage=name,
            family=None if event is None else str(event["family"]),
            event_time_utc=event_time,
            command=command,
        )
    return None


def execute_operation(
    operation: PlannedOperation,
    *,
    now_utc: Any | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    verify_operations_lock()
    observed = datetime.now(timezone.utc) if now_utc is None else _utc(now_utc)
    if operation.stage == "PRE_RELEASE_FORECAST":
        assert operation.event_time_utc is not None
        deadline = operation.event_time_utc - timedelta(seconds=60)
        if observed > deadline:
            return {
                "schema_version": "eurusd_neutral_macro_operation_v1",
                "planned_operation": _safe(asdict(operation)),
                "executed_at_utc": observed.isoformat(),
                "status": "SKIPPED_LATE_FORECAST_NO_BACKFILL",
                "network_request_made": False,
                "historical_pnl_loaded": False,
                "broker_action_allowed": False,
            }
    tokens = _validate_command(operation.stage, operation.command)
    completed = runner(
        tokens,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Macro operation failed ({completed.returncode}): "
            f"{completed.stderr[-2000:]}"
        )
    return {
        "schema_version": "eurusd_neutral_macro_operation_v1",
        "planned_operation": _safe(asdict(operation)),
        "executed_at_utc": observed.isoformat(),
        "status": "OPERATION_COMPLETED_REPLAN_REQUIRED",
        "command_sha256": hashlib.sha256(
            operation.command.encode("utf-8")
        ).hexdigest(),
        "stdout": completed.stdout[-10000:],
        "stderr": completed.stderr[-2000:],
        "historical_pnl_loaded": False,
        "broker_action_allowed": False,
    }


def _safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    return value


def _operation_from_due_action(action: Mapping[str, Any]) -> PlannedOperation:
    stage = str(action["stage"])
    command = str(action["command"])
    _validate_command(stage, command)
    due = _utc(action["due_at_utc"])
    event_time = (
        None
        if action.get("event_time_utc") is None
        else _utc(action["event_time_utc"])
    )
    return PlannedOperation(
        due_at_utc=due,
        execute_at_utc=due,
        stage=stage,
        family=(
            None if action.get("family") is None else str(action["family"])
        ),
        event_time_utc=event_time,
        command=command,
    )


def main() -> int:
    lock = verify_operations_lock()
    print(
        json.dumps(
            {
                "status": "MACRO_OPERATIONS_HELPER_STARTED",
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "operations_lock_sha256": _sha256_file(OPERATIONS_LOCK_PATH),
                "operations_locked_at_utc": lock["locked_at_utc"],
                "historical_pnl_allowed": False,
                "broker_action_allowed": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    while True:
        try:
            plan = planner.build_operations_plan(
                evaluated_at_utc=datetime.now(timezone.utc)
            )
            due = list(plan["due_actions"])
            if due:
                operation = _operation_from_due_action(due[0])
            else:
                operation = next_planned_operation(plan)
            print(
                json.dumps(
                    {
                        "status": plan["status"],
                        "evaluated_at_utc": plan["evaluated_at_utc"],
                        "next_operation": (
                            None if operation is None else _safe(asdict(operation))
                        ),
                        "historical_pnl_loaded": False,
                        "broker_action_allowed": False,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            if operation is None:
                time.sleep(RETRY_SECONDS)
                continue
            while True:
                remaining = (
                    operation.execute_at_utc - datetime.now(timezone.utc)
                ).total_seconds()
                if remaining <= 0:
                    break
                time.sleep(min(remaining, 30.0))
            result = execute_operation(operation)
            print(json.dumps(result, sort_keys=True), flush=True)
        except Exception as exc:  # noqa: BLE001
            print(
                json.dumps(
                    {
                        "status": "MACRO_OPERATION_FAILED_CONTINUING",
                        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "historical_pnl_loaded": False,
                        "broker_action_allowed": False,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            time.sleep(RETRY_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
