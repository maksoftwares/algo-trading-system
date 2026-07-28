from __future__ import annotations

import json
from typing import Any

from . import prospective_neutral_validation_v1_1 as prior
from .research import PACKAGE_ROOT, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_validation_v1_2.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_VALIDATION_V1_2_PREREG_2026_07_28.sha256.json"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_validation_result_v1_2"
TEMPORAL_CHECKS = {
    "oracle_one_to_one_dates_complete",
    "oracle_exact_temporal_null_valid",
    "oracle_one_to_one_temporal_precision",
    "oracle_temporal_precision_lift",
    "oracle_uniform_time_and_side_test",
}


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    prior.verify_lock()
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("Prospective validation V1.2 is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Prospective validation V1.2 lock mismatch: {relative}"
            )
        checked[relative] = actual
    superseded = load_config()["supersedes"]
    actual = sha256_file(PACKAGE_ROOT / superseded["path"])
    if actual != superseded["sha256"]:
        raise RuntimeError("Superseded prospective validation V1.1 drift")
    checked[superseded["path"]] = actual
    return checked


def classify_validation_result(result: dict[str, Any]) -> dict[str, Any]:
    classified = dict(result)
    checks = dict(classified["gate_results"])
    economic_checks = {
        key: value for key, value in checks.items() if not key.startswith("oracle_")
    }
    same_day_checks = {
        key: value for key, value in checks.items() if key not in TEMPORAL_CHECKS
    }
    economic_passed = bool(economic_checks and all(economic_checks.values()))
    same_day_passed = bool(same_day_checks and all(same_day_checks.values()))
    temporal_passed = bool(checks and all(checks.values()))
    immature = classified["status"] in {
        "WAITING_FOR_PROSPECTIVE_START",
        "ACCUMULATING_PROSPECTIVE_EVIDENCE",
    }
    if immature:
        status = classified["status"]
    elif temporal_passed:
        status = "INDEPENDENT_FULL_ORACLE_IMITATION_REVIEW_REQUIRED"
    elif same_day_passed:
        status = "INDEPENDENT_SAME_DAY_REGIME_REVIEW_REQUIRED"
    elif economic_passed:
        status = "INDEPENDENT_PROFITABILITY_REVIEW_REQUIRED"
    else:
        status = "REJECTED_WITHOUT_RETUNING"
    classified.update(
        {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "economic_and_robustness_gate_results": economic_checks,
            "same_day_regime_gate_results": same_day_checks,
            "economic_and_robustness_gates_passed": economic_passed,
            "same_day_regime_resemblance_gates_passed": same_day_passed,
            "full_temporal_oracle_imitation_gates_passed": temporal_passed,
            "profitability_review_allowed": economic_passed,
            "same_day_regime_review_allowed": same_day_passed,
            "oracle_imitation_claim_allowed": temporal_passed,
            "all_gates_passed": temporal_passed,
            "research_review_allowed": economic_passed,
            "controlled_demo_ready": False,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    )
    return classified


__all__ = [
    "CONFIG_PATH",
    "LOCK_PATH",
    "classify_validation_result",
    "load_config",
    "verify_lock",
]
