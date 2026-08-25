from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v19_boundary_audit", ROOT / "verify_boundary.py"
)
assert spec is not None and spec.loader is not None
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


BOUNDARY = "2026-08-26T00:00:00Z"


def hashed(record: dict, field: str) -> dict:
    record[field] = audit.canonical_sha256(record)
    return record


def fixtures(status_time: str, decision: str) -> dict:
    config = {
        "authorization": {
            "read_only_inputs": True,
            "broker_actions": False,
            "runtime_changes": False,
            "demo_deployment": False,
            "live_deployment": False,
        },
        "boundary": {"evidence_start_inclusive_utc": BOUNDARY},
    }
    lock = {
        "contract_sha256": audit.EXPECTED_CONTRACT,
        "locked_at_utc": "2026-08-25T21:04:25Z",
        "aggregate_economics_present_at_lock": False,
    }
    state = hashed(
        {
            "boundary_utc": BOUNDARY,
            "contract_sha256": audit.EXPECTED_CONTRACT,
            "updated_at_utc": status_time,
            "run_sequence": 1,
        },
        "state_sha256",
    )
    status = hashed(
        {
            "contract_sha256": audit.EXPECTED_CONTRACT,
            "generated_at_utc": status_time,
            "decision": decision,
            "broker_action_authorized": False,
            "deployment_authorized": False,
            "runtime_changes_authorized": False,
        },
        "status_sha256",
    )
    supervisor_config = {
        "health_sources": [
            {
                "id": "V60_DYNAMIC_CAPACITY_TWIN_V19_STATUS",
                "required_values": {
                    "contract_sha256": audit.EXPECTED_CONTRACT
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
            {
                "id": "V60_DYNAMIC_CAPACITY_TWIN_V19_STATUS",
                "healthy": True,
            },
            {
                "id": "V60_STATUS",
                "healthy": True,
                "reported_status": "ACTIVE_DEMO_BROKER_ACTION",
            },
        ],
        "process_state": {
            "all_workers_running": True,
            "workers": [
                {
                    "id": "V60_DYNAMIC_CAPACITY_TWIN_V19",
                    "running": True,
                    "process_ids": [1, 2],
                }
            ],
        },
    }
    return {
        "config": config,
        "root_lock": lock,
        "runtime_lock": dict(lock),
        "state": state,
        "status": status,
        "resolutions": [],
        "events": [],
        "supervisor_config": supervisor_config,
        "supervisor": supervisor,
        "locked_files_valid": True,
        "locked_file_failures": [],
    }


def test_healthy_preboundary_state_waits() -> None:
    data = fixtures("2026-08-25T23:00:00Z", "AWAITING_PROSPECTIVE_BOUNDARY")
    result = audit.evaluate(
        **data, now=datetime(2026, 8, 25, 23, 30, tzinfo=UTC)
    )
    assert result["decision"] == "WAIT_FOR_CLEAN_BOUNDARY"
    assert result["deployment_authorized"] is False


def test_first_healthy_postboundary_cycle_opens_collection() -> None:
    data = fixtures(
        "2026-08-26T00:01:00Z", "CONTINUE_PROSPECTIVE_CAPACITY_COLLECTION"
    )
    result = audit.evaluate(
        **data, now=datetime(2026, 8, 26, 0, 2, tzinfo=UTC)
    )
    assert result["decision"] == "CLEAN_BOUNDARY_OPENED_READ_ONLY_COLLECTION_ACTIVE"
    assert all(result["checks"].values())


def test_hourly_worker_receives_grace_for_first_postboundary_cycle() -> None:
    data = fixtures("2026-08-25T23:59:00Z", "AWAITING_PROSPECTIVE_BOUNDARY")
    result = audit.evaluate(
        **data, now=datetime(2026, 8, 26, 0, 30, tzinfo=UTC)
    )
    assert result["decision"] == "WAIT_FOR_FIRST_POSTBOUNDARY_CYCLE"


def test_stale_worker_after_grace_fails_review_closed() -> None:
    data = fixtures("2026-08-25T23:59:00Z", "AWAITING_PROSPECTIVE_BOUNDARY")
    result = audit.evaluate(
        **data, now=datetime(2026, 8, 26, 1, 11, tzinfo=UTC)
    )
    assert result["decision"] == "BOUNDARY_INTEGRITY_FAILED_REVIEW_REQUIRED"


def test_preboundary_resolution_fails_even_before_opening() -> None:
    data = fixtures("2026-08-25T23:00:00Z", "AWAITING_PROSPECTIVE_BOUNDARY")
    data["resolutions"] = [
        {"scheduled_entry_time_utc": "2026-08-25T23:59:59Z"}
    ]
    result = audit.evaluate(
        **data, now=datetime(2026, 8, 25, 23, 30, tzinfo=UTC)
    )
    assert result["decision"] == "BOUNDARY_INTEGRITY_FAILED_REVIEW_REQUIRED"


def test_lock_file_mismatch_fails_review_closed() -> None:
    data = fixtures("2026-08-25T23:00:00Z", "AWAITING_PROSPECTIVE_BOUNDARY")
    data["locked_files_valid"] = False
    data["locked_file_failures"] = ["package:run_evaluation.py"]
    result = audit.evaluate(
        **data, now=datetime(2026, 8, 25, 23, 30, tzinfo=UTC)
    )
    assert result["decision"] == "BOUNDARY_INTEGRITY_FAILED_REVIEW_REQUIRED"
    assert result["locked_file_failures"] == ["package:run_evaluation.py"]
