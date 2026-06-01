from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2_READINESS_CONSISTENCY.json"
DEFAULT_MD = Path("outputs") / "reports" / "PHASE2_READINESS_CONSISTENCY.md"


@dataclass(frozen=True)
class ConsistencyCheck:
    name: str
    status: str
    evidence: str


@dataclass(frozen=True)
class ConsistencyOutput:
    status: str
    json_path: Path
    markdown_path: Path
    checks: tuple[ConsistencyCheck, ...]


def verify_readiness_consistency(root: Path, output_json: Path | None = None) -> ConsistencyOutput:
    root = root.resolve()
    report_dir = root / "outputs" / "reports"
    phase0_reports = root.parent / "xauusd-phase0" / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    summary_path = report_dir / "PHASE1_STATUS_SUMMARY.json"
    acceptance_path = report_dir / "PHASE1_ACCEPTANCE_REPORT.md"
    readiness_path = report_dir / "PHASE2_READINESS_REPORT.md"
    countdown_path = report_dir / "PHASE2_DEMO_COUNTDOWN.json"
    preflight_path = report_dir / "PHASE2_DEMO_PREFLIGHT.json"
    demo_isolation_path = report_dir / "PHASE2_DEMO_ACCOUNT_ISOLATION.json"
    owner_approval_path = report_dir / "PHASE2_OWNER_APPROVAL.md"

    summary = _read_json(summary_path)
    countdown = _read_json(countdown_path)
    preflight = _read_json(preflight_path)
    demo_isolation = _read_json(demo_isolation_path)
    readiness_gates = _read_gate_table(readiness_path)
    acceptance_status = _read_markdown_status(acceptance_path)
    readiness_status = _read_markdown_status(readiness_path)
    soak = _mapping(summary.get("soak"))

    checks = [
        _acceptance_status_consistency(summary, acceptance_status, summary_path, acceptance_path),
        _active_market_owner_acceptance_consistency(soak, acceptance_path, readiness_gates),
        _code_freeze_semantics_consistency(soak, readiness_gates),
        _measured_cost_consistency(readiness_gates, phase0_reports),
        _demo_authorization_boundary_consistency(readiness_status, countdown, preflight, demo_isolation),
        _owner_approval_consistency(readiness_gates, owner_approval_path),
        _phase2_authority_source_consistency(readiness_path),
    ]
    status = _overall_status(checks)
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "phase2_readiness_status": readiness_status or "UNKNOWN",
        "phase1_acceptance_status": acceptance_status or "UNKNOWN",
        "checks": [check.__dict__ for check in checks],
        "source_reports": {
            "phase1_status_summary": str(summary_path),
            "phase1_acceptance": str(acceptance_path),
            "phase2_readiness": str(readiness_path),
            "phase2_demo_countdown": str(countdown_path),
            "phase2_demo_preflight": str(preflight_path),
            "phase2_demo_account_isolation": str(demo_isolation_path),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return ConsistencyOutput(status, output_json, output_md, tuple(checks))


def _acceptance_status_consistency(
    summary: dict[str, Any],
    acceptance_status: str,
    summary_path: Path,
    acceptance_path: Path,
) -> ConsistencyCheck:
    summary_acceptance = str(_mapping(summary.get("status")).get("acceptance", "UNKNOWN"))
    if summary_acceptance == acceptance_status == "PASS":
        return ConsistencyCheck("phase1_acceptance_status", "PASS", "Phase 1 acceptance status is PASS in summary and report.")
    if summary_acceptance == acceptance_status:
        return ConsistencyCheck(
            "phase1_acceptance_status",
            "PASS",
            f"`{summary_path}` and `{acceptance_path}` both report {summary_acceptance}.",
        )
    return ConsistencyCheck(
        "phase1_acceptance_status",
        "FAIL",
        f"`{summary_path}` has {summary_acceptance}; `{acceptance_path}` has {acceptance_status or 'missing'}.",
    )


def _active_market_owner_acceptance_consistency(
    soak: dict[str, Any],
    acceptance_path: Path,
    readiness_gates: list[dict[str, str]],
) -> ConsistencyCheck:
    owner_accepted = soak.get("owner_accepted_active_market_soak_pass") is True
    if not owner_accepted:
        return ConsistencyCheck("active_market_owner_acceptance", "PASS", "No owner-accepted active-market threshold is active.")
    original = _to_float(soak.get("original_active_market_target_hours") or soak.get("original_required_uninterrupted_streak_hours"))
    accepted = _to_float(soak.get("owner_accepted_active_market_target_hours") or soak.get("active_market_owner_accepted_hours"))
    observed = _to_float(soak.get("observed_longest_active_market_hours") or soak.get("active_market_streak_hours"))
    status = str(soak.get("phase1_active_market_acceptance_status", ""))
    gate = _gate_any(readiness_gates, ("Active-market soak (owner-accepted 56h)", "Active-market 72-hour soak"))
    acceptance_text = _read_text(acceptance_path)
    missing = []
    if original != 72.0:
        missing.append("original_active_market_target_hours=72")
    if accepted != 56.0:
        missing.append("owner_accepted_active_market_target_hours=56")
    if observed is None or observed < 56.0:
        missing.append("observed_longest_active_market_hours>=56")
    if status != "PASS_OWNER_ACCEPTED_THRESHOLD":
        missing.append("phase1_active_market_acceptance_status=PASS_OWNER_ACCEPTED_THRESHOLD")
    if gate.get("Status") != "PASS":
        missing.append("readiness active-market gate PASS")
    if "owner-accepted 56h threshold" not in acceptance_text and "owner-accepted Phase 1 threshold: 56h" not in acceptance_text:
        missing.append("acceptance report owner-accepted 56h wording")
    if "original 72h target waived for Phase 1 dry-run closure only" not in gate.get("Evidence", ""):
        missing.append("readiness report waiver wording")
    if missing:
        return ConsistencyCheck("active_market_owner_acceptance", "FAIL", "Missing: " + ", ".join(missing))
    return ConsistencyCheck(
        "active_market_owner_acceptance",
        "PASS",
        "Active-market soak is consistently recorded as PASS via owner-accepted 56h threshold; original 72h target is waived only for Phase 1 dry-run closure.",
    )


def _code_freeze_semantics_consistency(soak: dict[str, Any], gates: list[dict[str, str]]) -> ConsistencyCheck:
    code_freeze_pass = soak.get("code_freeze_pass") is True
    process_pass = soak.get("process_code_freeze_pass") is True
    process_hours = _to_float(soak.get("process_uptime_streak_hours")) or 0.0
    gate = _gate(gates, "Code-freeze 96-hour gate")
    evidence = gate.get("Evidence", "")
    if code_freeze_pass and not process_pass and process_hours < (_to_float(soak.get("required_code_freeze_hours")) or 96.0):
        if gate.get("Status") == "PASS" and "process uptime after restart is informational" in evidence:
            return ConsistencyCheck(
                "code_freeze_semantics",
                "PASS",
                "Code-freeze PASS is marker-age based; restarted process uptime is informational and VPS first-day evidence remains separate.",
            )
        return ConsistencyCheck(
            "code_freeze_semantics",
            "FAIL",
            "Code-freeze marker PASS with restarted process uptime must explicitly state process uptime is informational.",
        )
    return ConsistencyCheck("code_freeze_semantics", "PASS", "Code-freeze/process uptime semantics are internally consistent.")


def _measured_cost_consistency(gates: list[dict[str, str]], phase0_reports: Path) -> ConsistencyCheck:
    names = {
        "Measured cost model": phase0_reports / "MEASURED_COST_MODEL.md",
        "Measured-cost revalidation": phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md",
        "Measured-cost assumption delta": phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md",
    }
    mismatches = []
    for gate_name, path in names.items():
        source = _read_markdown_status(path) or "PENDING"
        gate = _gate(gates, gate_name).get("Status", "UNKNOWN")
        if gate != source:
            mismatches.append(f"{gate_name}: readiness={gate}; source={source}")
    if mismatches:
        return ConsistencyCheck("measured_cost_statuses", "FAIL", "; ".join(mismatches))
    return ConsistencyCheck("measured_cost_statuses", "PASS", "Measured-cost readiness gates match their source reports.")


def _demo_authorization_boundary_consistency(
    readiness_status: str,
    countdown: dict[str, Any],
    preflight: dict[str, Any],
    demo_isolation: dict[str, Any],
) -> ConsistencyCheck:
    unsafe = []
    if readiness_status != "PASS" and preflight.get("paper_mode_implementation_authorized") is True:
        unsafe.append("preflight authorizes paper implementation while readiness is not PASS")
    for name, report in (
        ("countdown", countdown),
        ("demo_account_isolation", demo_isolation),
    ):
        for key in ("paper_mode_authorized", "demo_trading_authorized", "live_trading_authorized", "broker_execution_authorized"):
            if report.get(key) is not False and report:
                unsafe.append(f"{name}.{key}={report.get(key)!r}")
    if unsafe:
        return ConsistencyCheck("demo_authorization_boundary", "FAIL", "; ".join(unsafe))
    return ConsistencyCheck("demo_authorization_boundary", "PASS", "Countdown, preflight, and demo-isolation artifacts keep authorization false while Phase 2 is pending.")


def _owner_approval_consistency(gates: list[dict[str, str]], owner_approval_path: Path) -> ConsistencyCheck:
    owner_gate = _gate(gates, "Project owner approval")
    objective_blockers = [row["Gate"] for row in gates if row.get("Gate") != "Project owner approval" and row.get("Status") != "PASS"]
    if owner_approval_path.exists() and objective_blockers and owner_gate.get("Status") == "PASS":
        return ConsistencyCheck(
            "owner_approval_ordering",
            "FAIL",
            "Owner approval cannot be PASS while objective blockers remain: " + ", ".join(objective_blockers[:8]),
        )
    return ConsistencyCheck("owner_approval_ordering", "PASS", "Owner approval is absent/pending until objective gates pass.")


def _phase2_authority_source_consistency(readiness_path: Path) -> ConsistencyCheck:
    if not readiness_path.exists():
        return ConsistencyCheck("phase2_authority_source", "FAIL", f"`{readiness_path}` is missing.")
    return ConsistencyCheck("phase2_authority_source", "PASS", "`PHASE2_READINESS_REPORT.md` exists and remains the sole readiness authority.")


def _overall_status(checks: list[ConsistencyCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    return "PASS"


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 Readiness Consistency",
            "",
            "This report checks cross-report status alignment. `PHASE2_READINESS_REPORT.md` remains the sole real readiness authority.",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Checks",
            "",
            _rows_table(_mapping_rows(payload.get("checks")), ["name", "status", "evidence"]),
            "",
            "## Source Reports",
            "",
            _table([(key, str(value)) for key, value in _mapping(payload.get("source_reports")).items()]),
            "",
        ]
    )


def _read_gate_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    in_gates = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            in_gates = line.strip() == "## Gates"
            continue
        if not in_gates or not line.startswith("| ") or line.startswith("| ---") or line.startswith("| Gate |"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 3:
            rows.append({"Gate": parts[0], "Status": parts[1], "Evidence": parts[2]})
    return rows


def _gate(gates: list[dict[str, str]], name: str) -> dict[str, str]:
    return next((row for row in gates if row.get("Gate") == name), {})


def _gate_any(gates: list[dict[str, str]], names: tuple[str, ...]) -> dict[str, str]:
    return next((row for row in gates if row.get("Gate") in names), {})


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _mapping_rows(value: Any) -> list[dict[str, Any]]:
    return [item for item in value] if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return "No rows."
    body = ["| Field | Value |", "| --- | --- |"]
    body.extend(f"| {key} | {value} |" for key, value in rows)
    return "\n".join(body)


def _rows_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    body = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    body.extend("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |" for row in rows)
    return "\n".join(body)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Phase 2 readiness cross-report consistency.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args(argv)

    output = verify_readiness_consistency(args.root, args.output_json)
    print(f"Phase 2 readiness consistency: {output.markdown_path}")
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
