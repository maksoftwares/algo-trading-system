from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "verify_dynamic_v6_boundary_open.py"
BOUNDARY = datetime(2026, 8, 26, tzinfo=UTC)


def load_script():
    spec = importlib.util.spec_from_file_location("dynamic_v6_boundary_open_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fixtures():
    contract_hash = "a" * 64
    prospective = {
        "authorization": {
            "read_only_mt5": True,
            "broker_actions": False,
            "runtime_changes": False,
            "demo_deployment": False,
            "live_deployment": False,
        },
        "lock": {"evidence_start_inclusive_utc": "2026-08-26T00:00:00Z"},
    }
    observer = {
        "generated_at_utc": "2026-08-26T00:01:00Z",
        "prospective_contract_sha256": contract_hash,
        "broker_action_authorized": False,
        "deployment_authorized": False,
        "evidence_chain": {"status": "VERIFIED"},
        "forward_comparison": {"sampled_equity": {"status": "VERIFIED"}},
    }
    supervisor_config = {
        "health_sources": [
            {
                "id": "V60_DYNAMIC_V6_PROSPECTIVE_STATUS",
                "required_values": {
                    "prospective_contract_sha256": contract_hash
                },
            }
        ]
    }
    supervisor = {
        "status": "READY",
        "healthy": True,
        "broker_action_added": False,
        "strategy_or_risk_parameters_changed": False,
        "health_sources": [
            {"id": "V60_DYNAMIC_V6_PROSPECTIVE_STATUS", "healthy": True}
        ],
        "process_state": {
            "all_workers_running": True,
            "terminal_process_ids": [3],
            "workers": [
                {"id": "V60_PORTFOLIO", "process_ids": [1, 2]},
                *[
                    {"id": f"worker-{value}", "process_ids": []}
                    for value in range(7)
                ],
            ],
        },
    }
    goal = {
        "runtime": {
            "deployed_v60_process_ids": [1, 2],
            "terminal_process_ids": [3],
        }
    }
    equity = [
        {
            "observed_at_utc": "2026-08-26T00:00:30Z",
            "payload": {"observed_at_utc": "2026-08-26T00:00:30Z"},
        }
    ]
    return contract_hash, prospective, observer, supervisor_config, supervisor, goal, equity


def evaluate(*, now: datetime, evidence=None, equity=None, candidates=None):
    module = load_script()
    values = fixtures()
    return module.evaluate_boundary_opening(
        values[1],
        values[0],
        values[2],
        values[3],
        values[4],
        evidence or [],
        values[6] if equity is None else equity,
        candidates or [],
        values[5],
        evidence_chain_verified=True,
        equity_chain_verified=True,
        now=now,
    )


def test_before_boundary_waits_without_claiming_failure() -> None:
    result = evaluate(now=datetime(2026, 8, 25, 23, 59, tzinfo=UTC), equity=[])
    assert result["decision"] == "WAIT_FOR_CLEAN_BOUNDARY"
    assert result["deployment_authorized"] is False


def test_first_clean_postboundary_cycle_opens_collection() -> None:
    result = evaluate(now=datetime(2026, 8, 26, 0, 1, tzinfo=UTC))
    assert result["decision"] == "CLEAN_BOUNDARY_OPENED_READ_ONLY_COLLECTION_ACTIVE"
    assert all(result["checks"].values())


def test_short_grace_waits_for_first_equity_mark() -> None:
    result = evaluate(now=datetime(2026, 8, 26, 0, 1, tzinfo=UTC), equity=[])
    assert result["decision"] == "WAIT_FOR_FIRST_POSTBOUNDARY_CYCLE"


def test_preboundary_evidence_fails_after_grace() -> None:
    evidence = [
        {
            "event_type": "SCORE_DECISION",
            "observed_at_utc": "2026-08-25T23:59:59Z",
            "payload": {
                "entry_time_utc": "2026-08-25T23:59:00Z",
                "prospective_contract_sha256": "a" * 64,
            },
        }
    ]
    result = evaluate(
        now=datetime(2026, 8, 26, 0, 6, tzinfo=UTC), evidence=evidence
    )
    assert result["decision"] == "BOUNDARY_OPENING_FAILED_REVIEW_REQUIRED"
    assert not result["checks"]["evidence_has_no_preboundary_records"]
