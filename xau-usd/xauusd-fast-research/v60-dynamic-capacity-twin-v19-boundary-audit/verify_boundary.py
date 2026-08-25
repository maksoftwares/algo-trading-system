from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V19_ROOT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "v60-dynamic-capacity-twin-prospective-v19"
)
SUPERVISOR_ROOT = (
    REPO_ROOT / "xau-usd" / "operations" / "v60-prospective-supervisor-v1"
)
RUNTIME = Path("D:/AlgoTradingData/prospective/v60-dynamic-capacity-twin-v19")
SUPERVISOR_RUNTIME = Path(
    "D:/AlgoTradingData/prospective/v60-prospective-supervisor-v1"
)
EXPECTED_CONTRACT = "fdabc9e2997592b06568bb5e405154abdb3888b921a61d70620e06bde2cb4905"
OUTPUT_JSON = ROOT / "outputs" / "RESULT.json"
OUTPUT_MD = ROOT / "outputs" / "RESULT.md"


def utc_time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp is not timezone-aware: {value}")
    return parsed.astimezone(UTC)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def self_hash_matches(record: Mapping[str, Any], field: str) -> bool:
    expected = record.get(field)
    payload = {key: value for key, value in record.items() if key != field}
    return isinstance(expected, str) and canonical_sha256(payload) == expected


def locked_files_match(lock: Mapping[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for relative, identity in lock.get("package_files", {}).items():
        path = V19_ROOT / relative
        if (
            not path.is_file()
            or path.stat().st_size != int(identity["bytes"])
            or sha256_file(path) != str(identity["sha256"])
        ):
            failures.append(f"package:{relative}")
    for name, identity in lock.get("input_files", {}).items():
        path = resolve(str(identity["path"]))
        if (
            not path.is_file()
            or path.stat().st_size != int(identity["bytes"])
            or sha256_file(path) != str(identity["sha256"])
        ):
            failures.append(f"input:{name}")
    return not failures, failures


def supervisor_anchor(config: Mapping[str, Any]) -> str | None:
    for source in config.get("health_sources", []):
        if source.get("id") == "V60_DYNAMIC_CAPACITY_TWIN_V19_STATUS":
            return source.get("required_values", {}).get("contract_sha256")
    return None


def health_source(supervisor: Mapping[str, Any], source_id: str) -> Mapping[str, Any]:
    return next(
        (
            source
            for source in supervisor.get("health_sources", [])
            if source.get("id") == source_id
        ),
        {},
    )


def worker(supervisor: Mapping[str, Any], worker_id: str) -> Mapping[str, Any]:
    return next(
        (
            item
            for item in supervisor.get("process_state", {}).get("workers", [])
            if item.get("id") == worker_id
        ),
        {},
    )


def rows_at_or_after(
    rows: Sequence[Mapping[str, Any]], boundary: datetime, fields: Sequence[str]
) -> bool:
    for row in rows:
        value = next((row.get(field) for field in fields if row.get(field)), None)
        if value is None or utc_time(value) < boundary:
            return False
    return True


def evaluate(
    *,
    config: Mapping[str, Any],
    root_lock: Mapping[str, Any],
    runtime_lock: Mapping[str, Any],
    state: Mapping[str, Any],
    status: Mapping[str, Any],
    resolutions: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    supervisor_config: Mapping[str, Any],
    supervisor: Mapping[str, Any],
    locked_files_valid: bool,
    locked_file_failures: Sequence[str],
    now: datetime | None = None,
) -> dict[str, Any]:
    now = (now or datetime.now(UTC)).astimezone(UTC)
    boundary = utc_time(config["boundary"]["evidence_start_inclusive_utc"])
    grace_end = boundary + timedelta(minutes=70)
    authorization = config["authorization"]
    v19_health = health_source(supervisor, "V60_DYNAMIC_CAPACITY_TWIN_V19_STATUS")
    v60_health = health_source(supervisor, "V60_STATUS")
    v19_worker = worker(supervisor, "V60_DYNAMIC_CAPACITY_TWIN_V19")
    checks = {
        "operative_contract_identity": root_lock.get("contract_sha256")
        == EXPECTED_CONTRACT
        and runtime_lock == root_lock
        and status.get("contract_sha256") == EXPECTED_CONTRACT
        and state.get("contract_sha256") == EXPECTED_CONTRACT,
        "contract_was_locked_before_boundary_without_economics": utc_time(
            root_lock["locked_at_utc"]
        )
        < boundary
        and root_lock.get("aggregate_economics_present_at_lock") is False,
        "locked_package_and_inputs_match": locked_files_valid,
        "state_self_hash_and_boundary_match": self_hash_matches(state, "state_sha256")
        and utc_time(state["boundary_utc"]) == boundary,
        "status_self_hash_matches": self_hash_matches(status, "status_sha256"),
        "observer_is_strictly_read_only": authorization
        == {
            "read_only_inputs": True,
            "broker_actions": False,
            "runtime_changes": False,
            "demo_deployment": False,
            "live_deployment": False,
        }
        and status.get("broker_action_authorized") is False
        and status.get("deployment_authorized") is False
        and status.get("runtime_changes_authorized") is False,
        "supervisor_anchor_matches_contract": supervisor_anchor(supervisor_config)
        == EXPECTED_CONTRACT,
        "supervisor_and_v19_worker_are_healthy": supervisor.get("status") == "READY"
        and supervisor.get("healthy") is True
        and supervisor.get("process_state", {}).get("all_workers_running") is True
        and v19_health.get("healthy") is True
        and v19_worker.get("running") is True,
        "deployed_v60_remains_active": v60_health.get("healthy") is True
        and v60_health.get("reported_status") == "ACTIVE_DEMO_BROKER_ACTION",
        "no_broker_or_risk_change_added": supervisor.get("broker_action_added") is False
        and supervisor.get("strategy_or_risk_parameters_changed") is False,
        "resolved_rows_have_no_preboundary_entries": rows_at_or_after(
            resolutions, boundary, ("scheduled_entry_time_utc", "entry_time_utc")
        ),
        "portfolio_events_have_no_preboundary_timestamps": rows_at_or_after(
            events, boundary, ("timestamp_utc", "entry_time_utc")
        ),
        "clock_reached_clean_boundary": now >= boundary,
        "v19_completed_postboundary_cycle": utc_time(status["generated_at_utc"])
        >= boundary
        and utc_time(state["updated_at_utc"]) >= boundary,
        "v19_advanced_from_preboundary_wait_state": status.get("decision")
        != "AWAITING_PROSPECTIVE_BOUNDARY",
    }
    preconditions = {
        name: passed
        for name, passed in checks.items()
        if name
        not in {
            "clock_reached_clean_boundary",
            "v19_completed_postboundary_cycle",
            "v19_advanced_from_preboundary_wait_state",
        }
    }
    opening = {
        name: checks[name]
        for name in (
            "clock_reached_clean_boundary",
            "v19_completed_postboundary_cycle",
            "v19_advanced_from_preboundary_wait_state",
        )
    }
    if not all(preconditions.values()):
        decision = "BOUNDARY_INTEGRITY_FAILED_REVIEW_REQUIRED"
    elif now < boundary:
        decision = "WAIT_FOR_CLEAN_BOUNDARY"
    elif now < grace_end and not all(opening.values()):
        decision = "WAIT_FOR_FIRST_POSTBOUNDARY_CYCLE"
    elif all(checks.values()):
        decision = "CLEAN_BOUNDARY_OPENED_READ_ONLY_COLLECTION_ACTIVE"
    else:
        decision = "BOUNDARY_INTEGRITY_FAILED_REVIEW_REQUIRED"
    return {
        "schema_version": "v60_dynamic_capacity_twin_v19_boundary_audit_v1",
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "evidence_start_inclusive_utc": boundary.isoformat().replace("+00:00", "Z"),
        "contract_sha256": EXPECTED_CONTRACT,
        "decision": decision,
        "deployment_authorized": False,
        "broker_action_authorized": False,
        "checks": checks,
        "locked_file_failures": list(locked_file_failures),
        "runtime": {
            "resolved_candidates": len(resolutions),
            "portfolio_events": len(events),
            "v19_run_sequence": int(state.get("run_sequence", 0)),
            "supervised_workers": len(
                supervisor.get("process_state", {}).get("workers", [])
            ),
            "v19_process_ids": list(v19_worker.get("process_ids", [])),
        },
    }


def render(result: Mapping[str, Any]) -> str:
    lines = [
        "# V19 Clean-Boundary Opening Audit",
        "",
        f"Decision: **{result['decision']}**",
        "",
        f"Boundary: `{result['evidence_start_inclusive_utc']}`",
        f"Contract: `{result['contract_sha256']}`",
        "",
        *[
            f"- {name}: **{'PASS' if passed else 'WAIT/FAIL'}**"
            for name, passed in result["checks"].items()
        ],
        "",
        "This verifier is read-only and never authorizes deployment.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    config = read_json(V19_ROOT / "config" / "prospective.json")
    root_lock = read_json(V19_ROOT / "outputs" / "CONTRACT_LOCK.json")
    runtime_lock = read_json(RUNTIME / config["outputs"]["contract_lock"])
    state = read_json(RUNTIME / config["outputs"]["state"])
    status = read_json(RUNTIME / config["outputs"]["status"])
    locked_files_valid, failures = locked_files_match(root_lock)
    result = evaluate(
        config=config,
        root_lock=root_lock,
        runtime_lock=runtime_lock,
        state=state,
        status=status,
        resolutions=read_jsonl(RUNTIME / config["outputs"]["resolved_candidates"]),
        events=read_jsonl(RUNTIME / config["outputs"]["portfolio_events"]),
        supervisor_config=read_json(
            SUPERVISOR_ROOT / "config" / "runtime_supervisor_v1.json"
        ),
        supervisor=read_json(SUPERVISOR_RUNTIME / "status.json"),
        locked_files_valid=locked_files_valid,
        locked_file_failures=failures,
    )
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    OUTPUT_MD.write_text(render(result), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 1 if result["decision"] == "BOUNDARY_INTEGRITY_FAILED_REVIEW_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
