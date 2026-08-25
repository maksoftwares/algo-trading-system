from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
PROSPECTIVE_ROOT = ROOT.parent / "v60-dynamic-followthrough-union-prospective-v6"
PROSPECTIVE_CONFIG = PROSPECTIVE_ROOT / "config" / "prospective.json"
SUPERVISOR_CONFIG = (
    REPO_ROOT
    / "xau-usd"
    / "operations"
    / "v60-prospective-supervisor-v1"
    / "config"
    / "runtime_supervisor_v1.json"
)
OBSERVER_RUNTIME = Path(
    "D:/AlgoTradingData/prospective/v60-dynamic-followthrough-union-v6"
)
SUPERVISOR_RUNTIME = Path(
    "D:/AlgoTradingData/prospective/v60-prospective-supervisor-v1"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp is not timezone-aware: {value}")
    return parsed.astimezone(UTC)


def dynamic_health_source(supervisor_status: Mapping[str, Any]) -> Mapping[str, Any]:
    matches = [
        item
        for item in supervisor_status.get("health_sources", [])
        if item.get("id") == "V60_DYNAMIC_V6_PROSPECTIVE_STATUS"
    ]
    if len(matches) != 1:
        return {}
    return matches[0]


def worker(supervisor_status: Mapping[str, Any], worker_id: str) -> Mapping[str, Any]:
    matches = [
        item
        for item in supervisor_status.get("process_state", {}).get("workers", [])
        if item.get("id") == worker_id
    ]
    if len(matches) != 1:
        return {}
    return matches[0]


def expected_contract_hash(supervisor_config: Mapping[str, Any]) -> str | None:
    matches = [
        item
        for item in supervisor_config.get("health_sources", [])
        if item.get("id") == "V60_DYNAMIC_V6_PROSPECTIVE_STATUS"
    ]
    if len(matches) != 1:
        return None
    return matches[0].get("required_values", {}).get(
        "prospective_contract_sha256"
    )


def evaluate_readiness(
    prospective_config: Mapping[str, Any],
    prospective_config_sha256: str,
    observer_status: Mapping[str, Any],
    supervisor_config: Mapping[str, Any],
    supervisor_status: Mapping[str, Any],
    exact_replay: Mapping[str, Any],
    goal_result: Mapping[str, Any],
    *,
    evidence_chain_size: int,
    equity_marks_size: int,
    now: datetime,
) -> dict[str, Any]:
    boundary = utc_time(
        prospective_config["lock"]["evidence_start_inclusive_utc"]
    )
    dynamic_health = dynamic_health_source(supervisor_status)
    dynamic_worker = worker(supervisor_status, "V60_DYNAMIC_V6_PROSPECTIVE")
    v60_worker = worker(supervisor_status, "V60_PORTFOLIO")
    expected_v60_pids = sorted(map(int, goal_result["runtime"]["deployed_v60_process_ids"]))
    expected_terminal_pids = sorted(map(int, goal_result["runtime"]["terminal_process_ids"]))
    actual_v60_pids = sorted(map(int, v60_worker.get("process_ids", [])))
    actual_terminal_pids = sorted(
        map(
            int,
            supervisor_status.get("process_state", {}).get(
                "terminal_process_ids", []
            ),
        )
    )
    authorization = prospective_config["authorization"]
    checks = {
        "clock_is_before_clean_boundary": now < boundary,
        "observer_is_strictly_read_only": bool(authorization["read_only_mt5"])
        and not any(
            bool(authorization[name])
            for name in (
                "broker_actions",
                "runtime_changes",
                "demo_deployment",
                "live_deployment",
            )
        ),
        "contract_hash_matches_observer_status": observer_status.get(
            "prospective_contract_sha256"
        )
        == prospective_config_sha256,
        "contract_hash_matches_supervisor_anchor": expected_contract_hash(
            supervisor_config
        )
        == prospective_config_sha256,
        "evidence_chain_is_verified_and_empty": observer_status.get(
            "evidence_chain", {}
        ).get("status")
        == "VERIFIED"
        and int(observer_status.get("evidence_chain", {}).get("records", -1)) == 0
        and evidence_chain_size == 0,
        "equity_chain_is_verified_and_empty": observer_status.get(
            "forward_comparison", {}
        )
        .get("sampled_equity", {})
        .get("status")
        == "VERIFIED"
        and int(
            observer_status.get("forward_comparison", {})
            .get("sampled_equity", {})
            .get("marks", -1)
        )
        == 0
        and equity_marks_size == 0,
        "exact_replay_has_no_preboundary_trades": exact_replay.get("decision")
        == "NOT_READY_NO_RESOLVED_TRADES"
        and exact_replay.get("deployment_authorized") is False,
        "supervisor_and_dynamic_worker_are_healthy": supervisor_status.get(
            "status"
        )
        == "READY"
        and supervisor_status.get("healthy") is True
        and len(supervisor_status.get("process_state", {}).get("workers", [])) == 8
        and dynamic_health.get("healthy") is True
        and dynamic_worker.get("running") is True,
        "v60_and_terminal_process_identity_unchanged": actual_v60_pids
        == expected_v60_pids
        and actual_terminal_pids == expected_terminal_pids,
        "no_broker_or_risk_change_added": supervisor_status.get(
            "broker_action_added"
        )
        is False
        and supervisor_status.get("strategy_or_risk_parameters_changed") is False
        and observer_status.get("broker_action_authorized") is False
        and observer_status.get("deployment_authorized") is False,
    }
    ready = all(checks.values())
    return {
        "schema_version": "v60_dynamic_v6_preboundary_readiness_v1",
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "decision": (
            "READY_FOR_CLEAN_READ_ONLY_COLLECTION"
            if ready
            else "NOT_READY_FIX_BEFORE_BOUNDARY"
        ),
        "evidence_start_inclusive_utc": boundary.isoformat().replace(
            "+00:00", "Z"
        ),
        "prospective_contract_sha256": prospective_config_sha256,
        "checks": checks,
        "runtime": {
            "supervisor_status": supervisor_status.get("status"),
            "worker_count": len(
                supervisor_status.get("process_state", {}).get("workers", [])
            ),
            "dynamic_worker_process_ids": dynamic_worker.get("process_ids", []),
            "v60_process_ids": actual_v60_pids,
            "terminal_process_ids": actual_terminal_pids,
            "evidence_records": observer_status.get("evidence_chain", {}).get(
                "records"
            ),
            "equity_marks": observer_status.get("forward_comparison", {})
            .get("sampled_equity", {})
            .get("marks"),
        },
        "broker_action_authorized": False,
        "deployment_authorized": False,
    }


def main() -> int:
    config_bytes = PROSPECTIVE_CONFIG.read_bytes()
    config = json.loads(config_bytes)
    observer_status = read_json(OBSERVER_RUNTIME / "STATUS.json")
    supervisor_config = read_json(SUPERVISOR_CONFIG)
    supervisor_status = read_json(SUPERVISOR_RUNTIME / "status.json")
    exact_replay = read_json(OBSERVER_RUNTIME / "EXACT_TICK_EQUITY_REPLAY.json")
    goal_result = read_json(ROOT / "GOAL_RESULT.json")
    evidence_path = OBSERVER_RUNTIME / "EVIDENCE_CHAIN.jsonl"
    equity_path = OBSERVER_RUNTIME / "EQUITY_MARKS.jsonl"
    result = evaluate_readiness(
        config,
        hashlib.sha256(config_bytes).hexdigest(),
        observer_status,
        supervisor_config,
        supervisor_status,
        exact_replay,
        goal_result,
        evidence_chain_size=evidence_path.stat().st_size if evidence_path.exists() else 0,
        equity_marks_size=equity_path.stat().st_size if equity_path.exists() else 0,
        now=datetime.now(UTC),
    )
    output_json = ROOT / "PRE_BOUNDARY_DYNAMIC_V6_READINESS_20260825.json"
    output_md = ROOT / "PRE_BOUNDARY_DYNAMIC_V6_READINESS_20260825.md"
    output_json.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Dynamic V6 Pre-Boundary Readiness",
        "",
        f"Decision: **{result['decision']}**",
        "",
        f"Boundary: `{result['evidence_start_inclusive_utc']}`",
        f"Contract: `{result['prospective_contract_sha256']}`",
        "",
    ]
    lines.extend(
        f"- {name}: **{'PASS' if passed else 'FAIL'}**"
        for name, passed in result["checks"].items()
    )
    lines.extend(
        [
            "",
            "This authorizes read-only evidence collection only. It does not authorize deployment.",
        ]
    )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "READY_FOR_CLEAN_READ_ONLY_COLLECTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
