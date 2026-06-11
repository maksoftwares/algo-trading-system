from __future__ import annotations

import json
import re
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase0.config import ConfigError
from phase0.constants import SECOND_EA_CAMPAIGN_CANDIDATES, SECOND_EA_LANE_B_CANDIDATES
from phase0.hashing import sha256_file
from phase0.low_frequency_gates import structural_cost_precheck


REPORT_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_HYPOTHESIS_VALIDATION_REPORT.md")
JSON_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_HYPOTHESIS_VALIDATION_REPORT.json")
REQUIRED_SECOND_EA_FIELDS = (
    "candidate_id",
    "candidate_version",
    "mechanic_family",
    "same_family_as_breakout_retest",
    "entry_decision_timeframe",
    "execution_timeframe",
    "expected_median_hold_hours",
    "expected_decisions_per_week",
    "expected_trades_per_year",
    "expected_median_stop_points",
    "expected_cost_R_at_measured_50_75_spread",
    "market_behavior_thesis",
    "participants_or_flow_mechanism",
    "mechanical_entry_rules",
    "mechanical_exit_rules",
    "stop_model",
    "target_model",
    "risk_model",
    "forbidden_filters",
    "falsification_criteria",
    "data_window",
    "true_holdout_exclusion",
    "expected_failure_modes",
    "D2_family_label",
    "author",
    "created_utc",
    "sha256_hash",
    "status",
)
OPTIONAL_SECOND_EA_FIELDS = ("event_clock_id", "ancestry_comparison")
PLACEHOLDER_PATTERNS = (
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"(?<!no\s)\blater\b", re.IGNORECASE),
    re.compile(r"\boptimi[sz]e\b", re.IGNORECASE),
    re.compile(r"\bmaybe\s+tune\b", re.IGNORECASE),
)
NUMERIC_VALUE_PATTERN = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")


@dataclass(frozen=True)
class SecondEaHypothesisValidation:
    status: str
    candidate_id: str
    hypothesis_path: Path
    lock_path: Path | None
    errors: tuple[str, ...]


@dataclass(frozen=True)
class SecondEaCampaignHypothesisValidation:
    status: str
    generated_at_utc: str
    report_path: Path
    json_path: Path
    candidate_results: tuple[SecondEaHypothesisValidation, ...]


def validate_second_ea_campaign_hypotheses(root: Path) -> SecondEaCampaignHypothesisValidation:
    report_path = root / REPORT_RELATIVE_PATH
    json_path = root / JSON_RELATIVE_PATH
    results = tuple(
        validate_second_ea_hypothesis(
            root / "docs" / f"hypothesis_{candidate}.md",
            root / "docs" / f"hypothesis_{candidate}.sha256.json",
        )
        for candidate in SECOND_EA_CAMPAIGN_CANDIDATES
    )
    status = "PASS" if all(result.status == "PASS" for result in results) else "BLOCKED"
    validation = SecondEaCampaignHypothesisValidation(
        status=status,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        report_path=report_path,
        json_path=json_path,
        candidate_results=results,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_campaign_hypothesis_validation_report(validation), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "status": validation.status,
                "generated_at_utc": validation.generated_at_utc,
                "candidate_results": [
                    {
                        **asdict(result),
                        "hypothesis_path": str(result.hypothesis_path),
                        "lock_path": "" if result.lock_path is None else str(result.lock_path),
                    }
                    for result in validation.candidate_results
                ],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return validation


def render_campaign_hypothesis_validation_report(
    validation: SecondEaCampaignHypothesisValidation,
) -> str:
    rows = []
    for result in validation.candidate_results:
        rows.append(
            {
                "Candidate": result.hypothesis_path.stem.removeprefix("hypothesis_"),
                "Status": result.status,
                "Hypothesis": result.hypothesis_path.as_posix(),
                "Lock": "" if result.lock_path is None else result.lock_path.as_posix(),
                "Errors": "; ".join(result.errors) if result.errors else "none",
            }
        )
    return "\n".join(
        [
            "# Second EA Hypothesis Validation Report",
            "",
            f"Status: {validation.status}",
            f"Generated at UTC: {validation.generated_at_utc}",
            "",
            "## Boundary",
            "",
            "This report validates hypothesis-file completeness, G9A pre-run structural cost feasibility, Lane B event-clock/ancestry requirements, and hash-lock readiness only. It does not authorize candidate matrix runs, observer deployment, demo execution, live execution, MT5 runtime access, or broker action.",
            "",
            "## Candidate Checks",
            "",
            _markdown_table(rows, ["Candidate", "Status", "Hypothesis", "Lock", "Errors"]),
            "",
            "All six campaign hypotheses must be `PASS` before M3/M7 can be considered hypothesis-lock complete.",
            "",
        ]
    )


def validate_second_ea_hypothesis(
    hypothesis_path: Path,
    lock_path: Path | None = None,
    raise_on_error: bool = False,
) -> SecondEaHypothesisValidation:
    errors: list[str] = []
    if not hypothesis_path.exists():
        errors.append(f"hypothesis file not found: {hypothesis_path}")
        validation = SecondEaHypothesisValidation("FAIL", "", hypothesis_path, lock_path, tuple(errors))
        if raise_on_error:
            raise ConfigError(_format_errors(validation))
        return validation

    text = hypothesis_path.read_text(encoding="utf-8")
    fields = _parse_fields(text)
    candidate_id = fields.get("candidate_id", "")
    for field in REQUIRED_SECOND_EA_FIELDS:
        value = fields.get(field)
        if value is None:
            errors.append(f"missing required field: {field}")
        elif not value.strip():
            errors.append(f"required field is empty: {field}")

    if candidate_id and hypothesis_path.stem != f"hypothesis_{candidate_id}":
        errors.append(
            f"candidate_id {candidate_id!r} does not match file name {hypothesis_path.name!r}"
        )

    if fields.get("same_family_as_breakout_retest") not in {"yes", "no"}:
        errors.append("same_family_as_breakout_retest must be yes or no")
    if fields.get("true_holdout_exclusion") not in {"true", "yes"}:
        errors.append("true_holdout_exclusion must be true/yes")
    if fields.get("status") != "LOCKED":
        errors.append("status must be LOCKED")
    errors.extend(_structural_cost_fragility_errors(fields))
    errors.extend(_lane_b_requirement_errors(candidate_id, fields))

    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            errors.append(f"placeholder/prohibited planning text remains: {pattern.pattern}")

    if lock_path is not None:
        errors.extend(_lock_errors(hypothesis_path, lock_path, fields))

    validation = SecondEaHypothesisValidation(
        status="PASS" if not errors else "FAIL",
        candidate_id=candidate_id,
        hypothesis_path=hypothesis_path,
        lock_path=lock_path,
        errors=tuple(errors),
    )
    if errors and raise_on_error:
        raise ConfigError(_format_errors(validation))
    return validation


def _lock_errors(hypothesis_path: Path, lock_path: Path, fields: dict[str, str]) -> list[str]:
    if not lock_path.exists():
        return [f"lock file not found: {lock_path}"]
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [f"lock file is invalid JSON: {lock_path}"]

    current_hash = sha256_file(hypothesis_path)
    locked_hash = str(payload.get("sha256_hash") or payload.get("sha256") or "")
    errors: list[str] = []
    if payload.get("status") != "LOCKED":
        errors.append("lock status must be LOCKED")
    if locked_hash != current_hash:
        errors.append("lock SHA256 does not match current hypothesis file")
    document_hash = fields.get("sha256_hash")
    if document_hash and document_hash not in {current_hash, "SELF_HASH_EXCLUDED"}:
        errors.append("document sha256_hash must match current file hash or SELF_HASH_EXCLUDED")
    return errors


def _structural_cost_fragility_errors(fields: dict[str, str]) -> list[str]:
    stop_field = "expected_median_stop_points"
    cost_field = "expected_cost_R_at_measured_50_75_spread"
    if not fields.get(stop_field) or not fields.get(cost_field):
        return []

    errors: list[str] = []
    stop = _parse_numeric_field(stop_field, fields[stop_field], errors)
    cost_r = _parse_numeric_field(cost_field, fields[cost_field], errors)
    if stop is None or cost_r is None:
        return errors

    result = structural_cost_precheck(stop, cost_r)
    if result.status == "BLOCKED_COST_FRAGILE_BY_DESIGN":
        errors.append(
            "G9A_pre_run_structural_cost: BLOCKED_COST_FRAGILE_BY_DESIGN "
            f"expected_median_stop_points={result.expected_median_stop_points:g} "
            "minimum=250 preferred=375; "
            f"expected_cost_R_at_measured_50_75_spread={result.expected_cost_r:g} "
            "maximum=0.30 preferred=0.15"
        )
    return errors


def _parse_numeric_field(field: str, value: str, errors: list[str]) -> float | None:
    match = NUMERIC_VALUE_PATTERN.search(value)
    if match is None:
        errors.append(f"{field} must include a numeric value for G9A structural cost precheck")
        return None
    return float(match.group(0))


def _lane_b_requirement_errors(candidate_id: str, fields: dict[str, str]) -> list[str]:
    if candidate_id not in SECOND_EA_LANE_B_CANDIDATES:
        return []

    errors: list[str] = []
    if not fields.get("event_clock_id", "").strip():
        errors.append("Lane B candidates require event_clock_id before hypothesis lock")
    if not fields.get("ancestry_comparison", "").strip():
        errors.append(
            "Lane B candidates require ancestry_comparison against rejected candidates before hypothesis lock"
        )

    entry_timeframe = fields.get("entry_decision_timeframe", "").upper()
    execution_timeframe = fields.get("execution_timeframe", "").upper()
    allowed_decision_timeframes = {"H1", "H4", "D1", "W1", "MN1"}
    if entry_timeframe and entry_timeframe not in allowed_decision_timeframes:
        errors.append("Lane B entry_decision_timeframe must be H1 or higher")
    if execution_timeframe in {"M1", "M5"}:
        errors.append("Lane B execution_timeframe must not use an M1/M5 entry trigger")
    return errors


def _parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    allowed = {field.lower(): field for field in (*REQUIRED_SECOND_EA_FIELDS, *OPTIONAL_SECOND_EA_FIELDS)}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        canonical = allowed.get(key.strip().lower())
        if canonical and canonical not in fields:
            fields[canonical] = value.strip().strip("`")
    return fields


def _format_errors(validation: SecondEaHypothesisValidation) -> str:
    return (
        f"Second-EA hypothesis validation failed for {validation.hypothesis_path}:\n"
        + "\n".join(validation.errors)
    )


def _markdown_table(rows: list[dict[str, Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)
