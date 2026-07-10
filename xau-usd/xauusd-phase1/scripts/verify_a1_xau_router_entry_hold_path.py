from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from analyze_a1_xau_router_entry_hold_path import (
    CLASSIFIER_INPUT_FIELDS,
    CLASSIFIER_SCHEMA_FIELD_NAMES,
    PROHIBITED_CLASSIFIER_FIELDS,
    SCHEMA_VERSION,
    analyze_evidence,
    canonical_json_bytes,
)


class VerificationError(ValueError):
    pass


def verify_analysis(evidence: Mapping[str, Any], candidate: Mapping[str, Any]) -> list[str]:
    """Recompute the audit offline and return every deterministic mismatch."""

    errors: list[str] = []
    expected = analyze_evidence(evidence)
    if candidate.get("schema_version") != SCHEMA_VERSION:
        errors.append("analysis schema version mismatch")
    reported_fields = set(candidate.get("classifier_input_fields", []))
    if reported_fields != set(CLASSIFIER_INPUT_FIELDS):
        errors.append("classifier input field manifest mismatch")
    if reported_fields.intersection(PROHIBITED_CLASSIFIER_FIELDS):
        errors.append("classifier schema exposes prohibited outcome fields")
    reported_schema_names = set(candidate.get("classifier_schema_field_names", []))
    if reported_schema_names != set(CLASSIFIER_SCHEMA_FIELD_NAMES):
        errors.append("nested classifier schema field manifest mismatch")
    if reported_schema_names.intersection(PROHIBITED_CLASSIFIER_FIELDS):
        errors.append("nested classifier schema exposes prohibited outcome fields")
    if candidate.get("outcomes_unsealed_after_class_lock") is not True:
        errors.append("outcome-sealing assertion is absent")
    if canonical_json_bytes(candidate) != canonical_json_bytes(expected):
        errors.append("analysis does not reproduce from immutable evidence")
    assignments = candidate.get("assignments", [])
    if len(assignments) != candidate.get("trade_count"):
        errors.append("assignment count does not equal trade count")
    trade_ids = [str(row.get("trade_id", "")) for row in assignments if isinstance(row, Mapping)]
    if not all(trade_ids) or len(set(trade_ids)) != len(trade_ids):
        errors.append("assignment trade IDs are empty or duplicated")
    class_count_total = sum(int(value) for value in candidate.get("class_counts", {}).values())
    if class_count_total != candidate.get("trade_count"):
        errors.append("class-count total does not equal trade count")
    return list(dict.fromkeys(errors))


def require_verified(evidence: Mapping[str, Any], candidate: Mapping[str, Any]) -> None:
    errors = verify_analysis(evidence, candidate)
    if errors:
        raise VerificationError("; ".join(errors))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only verifier for the A1 XAU Router V1 path audit")
    parser.add_argument("--input-json", type=Path, required=True, help="immutable normalized audit evidence")
    parser.add_argument("--analysis-json", type=Path, required=True, help="candidate analyzer output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    evidence = json.loads(args.input_json.read_text(encoding="utf-8"))
    candidate = json.loads(args.analysis_json.read_text(encoding="utf-8"))
    errors = verify_analysis(evidence, candidate)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("A1 XAU router entry/hold-path audit verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
