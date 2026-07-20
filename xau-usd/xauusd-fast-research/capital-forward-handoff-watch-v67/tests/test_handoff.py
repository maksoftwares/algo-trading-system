from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from handoff import (  # noqa: E402
    AUTHORITY_FLAGS,
    canonical_hash,
    failure_status,
    healthy_status,
    inventory_summary,
    verify_self_hash,
)
from run_watch import child_command, load_v27_state  # noqa: E402


def test_healthy_status_is_self_hashed_and_has_no_authority() -> None:
    v27 = {
        "decision": "V27_WAITING_FOR_COMPONENT_VALIDATION",
        "evidence_kind": "STATUS",
        "evidence_sha256": "abc123",
    }
    status = healthy_status(
        contract_sha256="contract",
        child_exit_code=0,
        child_duration_seconds=1.23456,
        v27_state=v27,
        inventories={"V24_1": {"available": True}},
    )
    assert status["status"] == "HANDOFF_HEALTHY"
    assert status["v27_decision"] == v27["decision"]
    assert status["v27_evidence_kind"] == "STATUS"
    assert status["child_duration_seconds"] == 1.235
    assert status["status_sha256"] == canonical_hash(status, "status_sha256")
    assert all(status[key] is value for key, value in AUTHORITY_FLAGS.items())


def test_failure_status_is_fail_closed() -> None:
    status = failure_status("contract", RuntimeError("child failed"))
    assert status["status"] == "FAILED_CLOSED"
    assert "child failed" in status["error"]
    assert status["status_sha256"] == canonical_hash(status, "status_sha256")
    assert all(status[key] is value for key, value in AUTHORITY_FLAGS.items())


def test_inventory_summary_uses_only_operational_metadata(tmp_path: Path) -> None:
    path = tmp_path / "inventory.json"
    path.write_text(
        json.dumps(
            {
                "updated_at_utc": "2026-07-20T12:00:00Z",
                "candidate_count_all_loaded_forward_data": 4,
                "eligible_full_weekday_count": 0,
                "eligible_full_weekdays": [],
                "source_audit": {"raw_rows": 100, "unique_rows": 98},
                "secret_outcome": 999,
            }
        ),
        encoding="utf-8",
    )
    result = inventory_summary(path)
    assert result == {
        "available": True,
        "updated_at_utc": "2026-07-20T12:00:00Z",
        "candidate_count_all_loaded_forward_data": 4,
        "eligible_full_weekday_count": 0,
        "eligible_full_weekdays": [],
        "source_raw_rows": 100,
        "source_unique_rows": 98,
    }


def test_child_command_uses_current_interpreter_and_no_strategy_arguments() -> None:
    runner = Path("C:/research/v27/run_portfolio_evaluation.py")
    assert child_command(runner) == [sys.executable, str(runner)]


def test_latest_v27_state_prefers_terminal_stage_audit(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    status = {
        "contract_sha256": "contract",
        "decision": "V27_WAITING_FOR_COMPONENT_VALIDATION",
        "waiting_for_stage": "VALIDATION",
    }
    status["status_sha256"] = canonical_hash(status, "status_sha256")
    (outputs / "status.json").write_text(json.dumps(status), encoding="utf-8")
    validation = {
        "contract_sha256": "contract",
        "decision": "V27_VALIDATION_PORTFOLIO_FAIL_TERMINAL",
    }
    validation["audit_sha256"] = canonical_hash(validation, "audit_sha256")
    (outputs / "validation.json").write_text(json.dumps(validation), encoding="utf-8")
    config = {
        "v27": {
            "contract_sha256": "contract",
            "status": "outputs/status.json",
            "validation_audit": "outputs/validation.json",
            "confirmation_audit": "outputs/confirmation.json",
        }
    }
    assert load_v27_state(config, tmp_path) == {
        "decision": "V27_VALIDATION_PORTFOLIO_FAIL_TERMINAL",
        "evidence_kind": "VALIDATION_AUDIT",
        "evidence_sha256": validation["audit_sha256"],
    }


def test_self_hash_rejects_mutation() -> None:
    payload = {"value": 1}
    payload["status_sha256"] = canonical_hash(payload, "status_sha256")
    verify_self_hash(payload, "status_sha256", "status")
    payload["value"] = 2
    try:
        verify_self_hash(payload, "status_sha256", "status")
    except ValueError as exc:
        assert "self-hash changed" in str(exc)
    else:
        raise AssertionError("mutated status was accepted")
