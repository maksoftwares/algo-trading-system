from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "verify_dynamic_v6_boundary.py"


def load_script():
    spec = importlib.util.spec_from_file_location("dynamic_v6_boundary_test", SCRIPT)
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
        "prospective_contract_sha256": contract_hash,
        "evidence_chain": {"status": "VERIFIED", "records": 0},
        "forward_comparison": {
            "sampled_equity": {"status": "VERIFIED", "marks": 0}
        },
        "broker_action_authorized": False,
        "deployment_authorized": False,
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
            "terminal_process_ids": [3],
            "workers": [
                {
                    "id": "V60_DYNAMIC_V6_PROSPECTIVE",
                    "running": True,
                    "process_ids": [1],
                },
                {"id": "V60_PORTFOLIO", "running": True, "process_ids": [2]},
                *[
                    {"id": f"worker-{index}", "running": True, "process_ids": []}
                    for index in range(6)
                ],
            ],
        },
    }
    exact = {
        "decision": "NOT_READY_NO_RESOLVED_TRADES",
        "deployment_authorized": False,
    }
    goal = {
        "runtime": {
            "deployed_v60_process_ids": [2],
            "terminal_process_ids": [3],
        }
    }
    return contract_hash, prospective, observer, supervisor_config, supervisor, exact, goal


def test_clean_preboundary_state_passes() -> None:
    module = load_script()
    values = fixtures()
    result = module.evaluate_readiness(
        values[1],
        values[0],
        values[2],
        values[3],
        values[4],
        values[5],
        values[6],
        evidence_chain_size=0,
        equity_marks_size=0,
        now=datetime(2026, 8, 25, 12, tzinfo=UTC),
    )
    assert result["decision"] == "READY_FOR_CLEAN_READ_ONLY_COLLECTION"
    assert all(result["checks"].values())
    assert result["deployment_authorized"] is False


def test_contract_mismatch_or_preboundary_record_fails() -> None:
    module = load_script()
    values = fixtures()
    result = module.evaluate_readiness(
        values[1],
        "b" * 64,
        values[2],
        values[3],
        values[4],
        values[5],
        values[6],
        evidence_chain_size=1,
        equity_marks_size=0,
        now=datetime(2026, 8, 25, 12, tzinfo=UTC),
    )
    assert result["decision"] == "NOT_READY_FIX_BEFORE_BOUNDARY"
    assert not result["checks"]["contract_hash_matches_observer_status"]
    assert not result["checks"]["evidence_chain_is_verified_and_empty"]
