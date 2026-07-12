"""R6-C2 structural validators; no real-evidence generation surface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from build_a1_xau_r6_distribution_break_failed_reclaim_census import TERMINAL_STATUSES


FORBIDDEN_FIELDS = {
    "exit_time", "target", "profit", "pnl", "net_r", "win", "loss", "mfe", "mae",
    "drawdown", "equity", "balance", "h4_exposure", "portfolio",
}
FORBIDDEN_FIELD_TOKENS = ("profit", "pnl", "exit", "target", "mfe", "mae", "drawdown", "equity", "balance", "portfolio", "exposure")
ALLOWED_C2_FILES = {
    "scripts/build_a1_xau_r6_distribution_break_failed_reclaim_census.py",
    "scripts/validate_a1_xau_r6_outcome_blind_census.py",
    "tests/test_a1_xau_r6_distribution_break_failed_reclaim_definition.py",
    "tests/test_a1_xau_r6_census_outcome_blind.py",
    "tests/test_a1_xau_r6_census_contract_risk.py",
    "tests/test_a1_xau_r6_census_manifest.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_closed_schema(schema: dict[str, Any]) -> None:
    if schema.get("additionalProperties") is not False:
        raise ValueError("row schema must be closed")
    properties = set(schema.get("properties", {}))
    required = set(schema.get("required", []))
    if required != properties:
        raise ValueError("every closed row property must be required")
    lowered = {field.lower() for field in properties}
    token_violation = any(
        token in field and field not in {"risk_exit_price"}
        for field in lowered
        for token in FORBIDDEN_FIELD_TOKENS
    )
    if lowered & FORBIDDEN_FIELDS or token_violation:
        raise ValueError("forbidden outcome field")
    if schema["properties"]["availability_status"].get("const") != "RAW_OPPORTUNITY_AVAILABLE":
        raise ValueError("partial exclusion rows are forbidden")


def validate_row(row: dict[str, Any], schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    if set(row) != set(properties):
        raise ValueError("row keys do not equal closed schema")
    if row["availability_status"] != "RAW_OPPORTUNITY_AVAILABLE" or row["exclusion_reason"] != "":
        raise ValueError("row is not a raw available opportunity")
    if row["entry_ask"] < row["entry_bid"] or row["structural_stop"] <= row["entry_ask"]:
        raise ValueError("invalid price relation")
    if row["risk_exit_price"] <= row["structural_stop"]:
        raise ValueError("conservative tick missing")
    if row["reference_risk_feasible"] != (row["minimum_contract_risk_usd"] <= 25.0):
        raise ValueError("reference risk flag mismatch")
    if row["deployment_risk_feasible"] != (row["minimum_contract_risk_usd"] <= 2.5):
        raise ValueError("deployment risk flag mismatch")


def validate_funnel(funnel: dict[str, int], rows: Sequence[dict[str, Any]]) -> None:
    if set(funnel) != set(TERMINAL_STATUSES) or any(value < 0 for value in funnel.values()):
        raise ValueError("invalid terminal funnel")
    if funnel["RAW_OPPORTUNITY_AVAILABLE"] != len(rows):
        raise ValueError("raw funnel count mismatch")


def validate_prefix_invariance(
    prefix_rows: Sequence[dict[str, Any]], extended_rows: Sequence[dict[str, Any]],
) -> None:
    """All previously emitted identities and fields must survive an appended market suffix."""
    by_id = {row["candidate_id"]: row for row in extended_rows}
    for row in prefix_rows:
        if by_id.get(row["candidate_id"]) != row:
            raise ValueError("prefix invariance failure")


def validate_lock_manifest(root: Path, manifest: Path) -> None:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    for relative, expected in payload["artifacts"].items():
        path = root / relative
        if sha256(path) != expected["sha256"] or path.stat().st_size != expected["size_bytes"]:
            raise ValueError(f"lock manifest mismatch: {relative}")
    if any(payload["boundary"].get(key) for key in (
        "broker_action_authorized", "census_output_authorized_in_this_commit",
        "detector_code_authorized_in_this_commit", "h4_or_portfolio_join_authorized",
        "mt5_execution_authorized", "pnl_authorized",
    )):
        raise ValueError("lock boundary is not fail closed")


def validate_changed_files(paths: Sequence[str]) -> None:
    normalized = {path.replace("\\", "/") for path in paths}
    trimmed = {path.split("xau-usd/xauusd-phase1/", 1)[-1] for path in normalized}
    if not trimmed <= ALLOWED_C2_FILES:
        raise ValueError("R6-C2 touched a file outside the six-file boundary")
