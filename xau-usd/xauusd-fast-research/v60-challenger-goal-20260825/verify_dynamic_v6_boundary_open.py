from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
PROSPECTIVE_ROOT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "v60-dynamic-followthrough-union-prospective-v6"
)
SUPERVISOR_ROOT = (
    REPO_ROOT / "xau-usd" / "operations" / "v60-prospective-supervisor-v1"
)
RUNTIME = Path("D:/AlgoTradingData/prospective/v60-dynamic-followthrough-union-v6")
SUPERVISOR_RUNTIME = Path(
    "D:/AlgoTradingData/prospective/v60-prospective-supervisor-v1"
)
OUTPUT_JSON = ROOT / "BOUNDARY_OPEN_DYNAMIC_V6_20260826.json"
OUTPUT_MD = ROOT / "BOUNDARY_OPEN_DYNAMIC_V6_20260826.md"


def utc_time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp is not timezone-aware: {value}")
    return parsed.astimezone(UTC)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def supervisor_anchor(config: Mapping[str, Any]) -> str | None:
    for source in config["health_sources"]:
        if source["id"] == "V60_DYNAMIC_V6_PROSPECTIVE_STATUS":
            return source["required_values"].get("prospective_contract_sha256")
    return None


def dynamic_health(supervisor: Mapping[str, Any]) -> bool:
    return any(
        source.get("id") == "V60_DYNAMIC_V6_PROSPECTIVE_STATUS"
        and bool(source.get("healthy"))
        for source in supervisor.get("health_sources", [])
    )


def event_contracts_match(
    records: Sequence[Mapping[str, Any]], contract_hash: str
) -> bool:
    decisions = [
        record
        for record in records
        if record.get("event_type")
        in {"SCORE_DECISION", "BASELINE_EXECUTION_DECISION"}
    ]
    return all(
        record.get("payload", {}).get("prospective_contract_sha256") == contract_hash
        for record in decisions
    )


def no_preboundary_records(
    records: Sequence[Mapping[str, Any]], boundary: datetime
) -> bool:
    return all(
        utc_time(record["payload"]["entry_time_utc"]) >= boundary
        and utc_time(record["observed_at_utc"]) >= boundary
        for record in records
    )


def no_preboundary_equity(
    records: Sequence[Mapping[str, Any]], boundary: datetime
) -> bool:
    return all(
        utc_time(record["observed_at_utc"]) >= boundary
        and utc_time(record["payload"]["observed_at_utc"]) >= boundary
        for record in records
    )


def evaluate_boundary_opening(
    prospective: Mapping[str, Any],
    contract_hash: str,
    observer: Mapping[str, Any],
    supervisor_config: Mapping[str, Any],
    supervisor: Mapping[str, Any],
    evidence_records: Sequence[Mapping[str, Any]],
    equity_records: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    goal: Mapping[str, Any],
    *,
    evidence_chain_verified: bool,
    equity_chain_verified: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = (now or datetime.now(UTC)).astimezone(UTC)
    boundary = utc_time(prospective["lock"]["evidence_start_inclusive_utc"])
    grace_end = boundary + timedelta(minutes=5)
    authorization = prospective["authorization"]
    expected_v60 = sorted(int(value) for value in goal["runtime"]["deployed_v60_process_ids"])
    expected_terminal = sorted(int(value) for value in goal["runtime"]["terminal_process_ids"])
    workers = {row["id"]: row for row in supervisor["process_state"]["workers"]}
    actual_v60 = sorted(int(value) for value in workers["V60_PORTFOLIO"]["process_ids"])
    actual_terminal = sorted(
        int(value) for value in supervisor["process_state"]["terminal_process_ids"]
    )
    candidate_boundary_ok = all(
        utc_time(row["entry_time_utc"]) >= boundary for row in candidates
    )
    candidate_contract_ok = all(
        row.get("prospective_contract_sha256") == contract_hash for row in candidates
    )
    observer_generated = utc_time(observer["generated_at_utc"])
    checks = {
        "clock_reached_clean_boundary": now >= boundary,
        "observer_is_strictly_read_only": bool(authorization["read_only_mt5"])
        and not any(
            bool(authorization[name])
            for name in (
                "broker_actions",
                "runtime_changes",
                "demo_deployment",
                "live_deployment",
            )
        )
        and not bool(observer["broker_action_authorized"])
        and not bool(observer["deployment_authorized"]),
        "contract_hash_matches_observer_status": observer.get(
            "prospective_contract_sha256"
        )
        == contract_hash,
        "contract_hash_matches_supervisor_anchor": supervisor_anchor(
            supervisor_config
        )
        == contract_hash,
        "supervisor_and_dynamic_worker_are_healthy": supervisor.get("status")
        == "READY"
        and bool(supervisor.get("healthy"))
        and bool(supervisor["process_state"]["all_workers_running"])
        and dynamic_health(supervisor),
        "no_broker_or_risk_change_added": not bool(
            supervisor.get("broker_action_added")
        )
        and not bool(supervisor.get("strategy_or_risk_parameters_changed")),
        "v60_and_terminal_process_identity_unchanged": actual_v60 == expected_v60
        and actual_terminal == expected_terminal,
        "observer_completed_postboundary_cycle": observer_generated >= boundary,
        "evidence_chain_verified": evidence_chain_verified
        and observer.get("evidence_chain", {}).get("status") == "VERIFIED",
        "equity_chain_verified": equity_chain_verified
        and observer.get("forward_comparison", {})
        .get("sampled_equity", {})
        .get("status")
        == "VERIFIED",
        "evidence_has_no_preboundary_records": no_preboundary_records(
            evidence_records, boundary
        ),
        "equity_has_no_preboundary_marks": no_preboundary_equity(
            equity_records, boundary
        ),
        "candidate_snapshot_has_no_preboundary_rows": candidate_boundary_ok,
        "immutable_decisions_use_locked_contract": event_contracts_match(
            evidence_records, contract_hash
        ),
        "candidate_snapshot_uses_locked_contract": candidate_contract_ok,
        "first_postboundary_equity_mark_exists": len(equity_records) > 0,
    }
    opening_checks = {
        key: value
        for key, value in checks.items()
        if key != "clock_reached_clean_boundary"
    }
    if now < boundary:
        decision = "WAIT_FOR_CLEAN_BOUNDARY"
    elif now < grace_end and not all(opening_checks.values()):
        decision = "WAIT_FOR_FIRST_POSTBOUNDARY_CYCLE"
    elif all(checks.values()):
        decision = "CLEAN_BOUNDARY_OPENED_READ_ONLY_COLLECTION_ACTIVE"
    else:
        decision = "BOUNDARY_OPENING_FAILED_REVIEW_REQUIRED"
    return {
        "schema_version": "v60_dynamic_v6_boundary_opening_v1",
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "evidence_start_inclusive_utc": boundary.isoformat().replace(
            "+00:00", "Z"
        ),
        "prospective_contract_sha256": contract_hash,
        "decision": decision,
        "deployment_authorized": False,
        "broker_action_authorized": False,
        "checks": checks,
        "runtime": {
            "evidence_records": len(evidence_records),
            "equity_marks": len(equity_records),
            "candidate_rows": len(candidates),
            "v60_process_ids": actual_v60,
            "terminal_process_ids": actual_terminal,
            "worker_count": len(workers),
        },
    }


def load_verified_chain(path: Path) -> tuple[list[dict[str, Any]], bool]:
    source = (
        REPO_ROOT
        / "xau-usd"
        / "xauusd-fast-research"
        / "v60-mature-source-health-rank-veto-prospective-v2"
        / "src"
        / "evidence.py"
    )
    spec = importlib.util.spec_from_file_location("dynamic_v6_boundary_chain", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load chain verifier: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    try:
        return module.load_chain(path), True
    except (ValueError, json.JSONDecodeError):
        return [], False


def write_outputs(result: Mapping[str, Any]) -> None:
    OUTPUT_JSON.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Dynamic V6 Clean-Boundary Opening Audit",
        "",
        f"Decision: **{result['decision']}**",
        "",
        f"Boundary: `{result['evidence_start_inclusive_utc']}`",
        f"Contract: `{result['prospective_contract_sha256']}`",
        "",
        *[
            f"- {name}: **{'PASS' if passed else 'WAIT/FAIL'}**"
            for name, passed in result["checks"].items()
        ],
        "",
        "This audit never authorizes deployment.",
        "",
    ]
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    prospective_path = PROSPECTIVE_ROOT / "config" / "prospective.json"
    prospective = load_json(prospective_path)
    evidence_records, evidence_verified = load_verified_chain(
        RUNTIME / "EVIDENCE_CHAIN.jsonl"
    )
    equity_records, equity_verified = load_verified_chain(
        RUNTIME / "EQUITY_MARKS.jsonl"
    )
    result = evaluate_boundary_opening(
        prospective,
        sha256_file(prospective_path),
        load_json(RUNTIME / "STATUS.json"),
        load_json(SUPERVISOR_ROOT / "config" / "runtime_supervisor_v1.json"),
        load_json(SUPERVISOR_RUNTIME / "status.json"),
        evidence_records,
        equity_records,
        load_jsonl(RUNTIME / "CANDIDATES.jsonl"),
        load_json(ROOT / "GOAL_RESULT.json"),
        evidence_chain_verified=evidence_verified,
        equity_chain_verified=equity_verified,
    )
    write_outputs(result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] != "BOUNDARY_OPENING_FAILED_REVIEW_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
