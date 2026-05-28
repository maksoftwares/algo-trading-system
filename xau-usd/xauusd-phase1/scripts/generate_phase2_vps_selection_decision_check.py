from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_phase2_readiness_report import (
    VPS_SELECTION_REQUIRED_FIELDS,
    _is_placeholder_value,
    _parse_decision_record_fields,
    _read_markdown_status,
    _vps_selection_gate,
)


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_VPS_SELECTION_DECISION_CHECK.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_VPS_SELECTION_DECISION_CHECK.md"
AUTHORITY_NOTE = (
    "This report validates the owner VPS-selection record only. It does not authorize Phase 2, "
    "demo trading, broker execution, live capital, or any paper-mode implementation."
)
OWNER_ACCEPTANCE_TOKENS = (
    "paper-mode only",
    "no live capital",
    "no broker execution",
)


@dataclass(frozen=True)
class VpsSelectionDecisionCheckOutput:
    status: str
    json_path: Path
    markdown_path: Path
    check_count: int


def generate_phase2_vps_selection_decision_check(
    root: Path,
    output_json: Path | None = None,
) -> VpsSelectionDecisionCheckOutput:
    root = root.resolve()
    output_json = (output_json or root / DEFAULT_REPORT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_REPORT_JSON.name else root / DEFAULT_REPORT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    matrix_path = root / "docs" / "PHASE2_VPS_SELECTION_MATRIX.md"
    matrix_text = matrix_path.read_text(encoding="utf-8", errors="replace") if matrix_path.exists() else ""
    decision_fields = _parse_decision_record_fields(matrix_text) if matrix_text else {}

    checks = [
        _matrix_gate_check(matrix_path),
        _required_fields_check(decision_fields),
        _placeholder_check(decision_fields),
        _latency_evidence_check(root, decision_fields),
        _latency_selection_consistency_check(root, decision_fields),
        _owner_acceptance_check(decision_fields),
    ]
    status = _overall_status(checks)
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": AUTHORITY_NOTE,
        "matrix_path": str(matrix_path),
        "paper_mode_authorized": False,
        "demo_trading_authorized": False,
        "broker_execution_authorized": False,
        "live_trading_authorized": False,
        "decision_fields": decision_fields,
        "checks": checks,
        "next_action": _next_action(status, checks),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return VpsSelectionDecisionCheckOutput(status, output_json, output_md, len(checks))


def _matrix_gate_check(matrix_path: Path) -> dict[str, str]:
    if not matrix_path.exists():
        return {
            "check": "matrix_readiness_gate",
            "status": "FAIL",
            "evidence": f"Missing VPS selection matrix: `{matrix_path}`.",
        }
    item = _vps_selection_gate(matrix_path)
    return {
        "check": "matrix_readiness_gate",
        "status": item.status,
        "evidence": item.evidence,
    }


def _required_fields_check(decision_fields: dict[str, str]) -> dict[str, str]:
    missing = [field for field in VPS_SELECTION_REQUIRED_FIELDS if not decision_fields.get(field)]
    if missing:
        return {
            "check": "required_decision_fields",
            "status": "PENDING",
            "evidence": "Missing decision field(s): " + ", ".join(missing) + ".",
        }
    return {
        "check": "required_decision_fields",
        "status": "PASS",
        "evidence": "All required VPS decision fields are present.",
    }


def _placeholder_check(decision_fields: dict[str, str]) -> dict[str, str]:
    placeholders = [
        field
        for field in VPS_SELECTION_REQUIRED_FIELDS
        if _is_placeholder_value(decision_fields.get(field, ""))
    ]
    if placeholders:
        return {
            "check": "no_placeholder_values",
            "status": "PENDING",
            "evidence": "Placeholder decision value(s): " + ", ".join(placeholders) + ".",
        }
    if not decision_fields:
        return {
            "check": "no_placeholder_values",
            "status": "PENDING",
            "evidence": "Decision record is not filled yet.",
        }
    return {
        "check": "no_placeholder_values",
        "status": "PASS",
        "evidence": "No placeholder values found in required VPS decision fields.",
    }


def _latency_evidence_check(root: Path, decision_fields: dict[str, str]) -> dict[str, str]:
    raw_path = decision_fields.get("latency_evidence_path", "")
    if not raw_path or _is_placeholder_value(raw_path):
        return {
            "check": "latency_evidence_report",
            "status": "PENDING",
            "evidence": "Latency evidence path is not filled with a real report path yet.",
        }
    path = _resolve_evidence_path(root, raw_path)
    if not path.exists():
        return {
            "check": "latency_evidence_report",
            "status": "PENDING",
            "evidence": f"Latency evidence path is set but the report is missing: `{path}`.",
        }
    status = _read_markdown_status(path)
    if status == "PASS":
        return {
            "check": "latency_evidence_report",
            "status": "PASS",
            "evidence": f"`{path}` status is PASS.",
        }
    if status in {"PENDING", "WARN", "REVIEW", ""}:
        return {
            "check": "latency_evidence_report",
            "status": "PENDING",
            "evidence": f"`{path}` status is {status or 'unclear'}; required PASS before VPS selection can close.",
        }
    return {
        "check": "latency_evidence_report",
        "status": "FAIL",
        "evidence": f"`{path}` status is {status}; required PASS.",
    }


def _latency_selection_consistency_check(root: Path, decision_fields: dict[str, str]) -> dict[str, str]:
    raw_path = decision_fields.get("latency_evidence_path", "")
    path = _resolve_evidence_path(root, raw_path) if raw_path and not _is_placeholder_value(raw_path) else None
    if path is None or not path.exists():
        return {
            "check": "latency_selection_consistency",
            "status": "PENDING",
            "evidence": "Latency evidence report is not available for provider/region consistency checks yet.",
        }
    status = _read_markdown_status(path)
    if status != "PASS":
        return {
            "check": "latency_selection_consistency",
            "status": "PENDING",
            "evidence": f"`{path}` status is {status or 'unclear'}; consistency check waits for latency PASS.",
        }
    candidate = _parse_latency_candidate(path)
    if not candidate:
        return {
            "check": "latency_selection_consistency",
            "status": "FAIL",
            "evidence": f"`{path}` is PASS but does not expose a parseable Provider/Region candidate row.",
        }

    selected_provider = decision_fields.get("selected_provider", "")
    selected_region = decision_fields.get("selected_region", "")
    provider_ok = _loosely_matches(selected_provider, candidate.get("provider", ""))
    region_ok = _loosely_matches(selected_region, candidate.get("region", ""))
    if provider_ok and region_ok:
        return {
            "check": "latency_selection_consistency",
            "status": "PASS",
            "evidence": (
                "Selected provider/region matches latency evidence: "
                f"provider={candidate.get('provider', '')}; region={candidate.get('region', '')}."
            ),
        }
    mismatches = []
    if not provider_ok:
        mismatches.append(
            f"selected_provider={selected_provider!r} vs latency_provider={candidate.get('provider', '')!r}"
        )
    if not region_ok:
        mismatches.append(f"selected_region={selected_region!r} vs latency_region={candidate.get('region', '')!r}")
    return {
        "check": "latency_selection_consistency",
        "status": "FAIL",
        "evidence": "VPS selection and latency evidence mismatch: " + "; ".join(mismatches) + ".",
    }


def _owner_acceptance_check(decision_fields: dict[str, str]) -> dict[str, str]:
    value = decision_fields.get("owner_acceptance", "")
    if not value or _is_placeholder_value(value):
        return {
            "check": "owner_acceptance_boundary",
            "status": "PENDING",
            "evidence": "Owner acceptance field is not filled yet.",
        }
    normalized = value.lower()
    missing = [token for token in OWNER_ACCEPTANCE_TOKENS if token not in normalized]
    if missing:
        return {
            "check": "owner_acceptance_boundary",
            "status": "PENDING",
            "evidence": "Owner acceptance must include: " + ", ".join(missing) + ".",
        }
    return {
        "check": "owner_acceptance_boundary",
        "status": "PASS",
        "evidence": "Owner acceptance preserves paper-only/no-live/no-broker-execution boundary.",
    }


def _resolve_evidence_path(root: Path, value: str) -> Path:
    cleaned = _extract_path_text(value).replace("\\", "/")
    path = Path(cleaned)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def _extract_path_text(value: str) -> str:
    stripped = value.strip()
    if "`" in stripped:
        parts = stripped.split("`")
        if len(parts) >= 3 and parts[1].strip():
            return parts[1].strip()
    return stripped.strip("`").strip()


def _parse_latency_candidate(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        headers = _markdown_cells(line)
        lower_headers = [header.lower() for header in headers]
        if "provider" not in lower_headers or "region" not in lower_headers:
            continue
        provider_index = lower_headers.index("provider")
        region_index = lower_headers.index("region")
        endpoint_index = lower_headers.index("endpoint") if "endpoint" in lower_headers else None
        for row_line in lines[index + 1 :]:
            if not row_line.strip().startswith("|"):
                break
            row = _markdown_cells(row_line)
            if not row or all(set(cell) <= {"-", ":", " "} for cell in row):
                continue
            if len(row) <= max(provider_index, region_index):
                continue
            return {
                "provider": row[provider_index].strip(),
                "region": row[region_index].strip(),
                "endpoint": row[endpoint_index].strip() if endpoint_index is not None and len(row) > endpoint_index else "",
            }
    return {}


def _markdown_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _loosely_matches(selected: str, observed: str) -> bool:
    selected_norm = _normalize_match_text(selected)
    observed_norm = _normalize_match_text(observed)
    if not selected_norm or not observed_norm:
        return False
    return selected_norm == observed_norm or selected_norm in observed_norm or observed_norm in selected_norm


def _normalize_match_text(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def _overall_status(checks: list[dict[str, str]]) -> str:
    if any(check.get("status") == "FAIL" for check in checks):
        return "FAIL"
    if any(check.get("status") != "PASS" for check in checks):
        return "PENDING"
    return "PASS"


def _next_action(status: str, checks: list[dict[str, str]]) -> str:
    if status == "PASS":
        return "VPS selection evidence is ready for the broader Phase 2 readiness report."
    for check in checks:
        if check.get("status") != "PASS":
            return check.get("evidence", "Complete the next pending VPS selection check.")
    return "Complete the next pending VPS selection check."


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 VPS Selection Decision Check",
            "",
            AUTHORITY_NOTE,
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authority",
            "",
            _table(
                [
                    ("Paper mode authorized", str(payload["paper_mode_authorized"]).lower()),
                    ("Demo trading authorized", str(payload["demo_trading_authorized"]).lower()),
                    ("Broker execution authorized", str(payload["broker_execution_authorized"]).lower()),
                    ("Live trading authorized", str(payload["live_trading_authorized"]).lower()),
                ]
            ),
            "",
            "## Decision Record",
            "",
            _table([(key, value) for key, value in payload["decision_fields"].items()]) if payload["decision_fields"] else "No decision record fields found.",
            "",
            "## Checks",
            "",
            _rows_table(payload["checks"], ["check", "status", "evidence"]),
            "",
            "## Next Action",
            "",
            str(payload["next_action"]),
            "",
        ]
    )


def _table(rows: list[tuple[str, str]]) -> str:
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _rows_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(str(row.get(column, ""))) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 2 VPS selection decision check.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_phase2_vps_selection_decision_check(args.root, args.json)
    print(f"Phase 2 VPS selection decision check: {output.status}")
    print(output.markdown_path)
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
