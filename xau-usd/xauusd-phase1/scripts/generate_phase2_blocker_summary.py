from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2_BLOCKER_SUMMARY.json"
DEFAULT_MD = Path("outputs") / "reports" / "PHASE2_BLOCKER_SUMMARY.md"


@dataclass(frozen=True)
class Phase2BlockerSummaryOutput:
    status: str
    json_path: Path
    markdown_path: Path


def generate_phase2_blocker_summary(root: Path, output_json: Path | None = None) -> Phase2BlockerSummaryOutput:
    root = root.resolve()
    phase0_root = root.parent / "xauusd-phase0"
    phase1_reports = root / "outputs" / "reports"
    phase0_reports = phase0_root / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    measured_cost_model_status = _read_markdown_status(phase0_reports / "MEASURED_COST_MODEL.md")
    measured_cost_revalidation_status = _read_markdown_status(
        phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md"
    )
    measured_cost_assumption_delta_status = _read_markdown_status(
        phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md"
    )
    measured_cost_sanity_status = _read_markdown_status(
        phase0_reports / "MEASURED_COST_REVALIDATION_SANITY_CHECK.md"
    )
    phase1_acceptance_status = _read_markdown_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md")
    phase2_readiness_status = _read_markdown_status(phase1_reports / "PHASE2_READINESS_REPORT.md")
    actual_demo_cost = _read_json(phase1_reports / "PHASE2_ACTUAL_DEMO_COST_RECONCILIATION.json")
    actual_demo_cost_status = str(actual_demo_cost.get("status", "NOT_GENERATED"))
    actual_demo_cost_resolution = str(actual_demo_cost.get("resolution_status", "NOT_GENERATED"))

    canonical_blocked = (
        measured_cost_model_status == "PASS"
        and measured_cost_revalidation_status == "FAIL"
        and measured_cost_assumption_delta_status == "FAIL"
        and measured_cost_sanity_status == "CALCULATION_CONFIRMED"
    )
    canonical_status = "BLOCKED_BY_MEASURED_COST" if canonical_blocked else "REVIEW_REQUIRED"
    payload = {
        "status": canonical_status,
        "created_at_utc": _now(),
        "canonical_phase2_status": canonical_status,
        "breakout_retest_family_status": "COST_SUSPENDED_CANONICAL",
        "measured_cost_model_status": measured_cost_model_status or "UNKNOWN",
        "measured_cost_revalidation_status": measured_cost_revalidation_status or "UNKNOWN",
        "measured_cost_assumption_delta_status": measured_cost_assumption_delta_status or "UNKNOWN",
        "measured_cost_sanity_status": measured_cost_sanity_status or "UNKNOWN",
        "phase1_acceptance_status": phase1_acceptance_status or "UNKNOWN",
        "phase2_readiness_status": phase2_readiness_status or "UNKNOWN",
        "actual_demo_cost_reconciliation_status": actual_demo_cost_status,
        "actual_demo_cost_resolution_status": actual_demo_cost_resolution,
        "actual_demo_cost_current_practical_blocker": actual_demo_cost_status != "PASS",
        "experimental_demo_executor_status": "QUARANTINE_REVIEW_ONLY",
        "demo_execution_as_phase2_evidence": False,
        "live_trading_authorized": False,
        "canonical_broker_side_execution": False,
        "paper_mode_execution_allowed": False,
        "decision": _decision(canonical_blocked, actual_demo_cost_status),
        "source_reports": {
            "measured_cost_model": str(phase0_reports / "MEASURED_COST_MODEL.md"),
            "measured_cost_revalidation": str(phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md"),
            "assumption_delta": str(phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md"),
            "sanity_check": str(phase0_reports / "MEASURED_COST_REVALIDATION_SANITY_CHECK.md"),
            "actual_demo_cost_reconciliation": str(
                phase1_reports / "PHASE2_ACTUAL_DEMO_COST_RECONCILIATION.md"
            ),
            "phase2_readiness": str(phase1_reports / "PHASE2_READINESS_REPORT.md"),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return Phase2BlockerSummaryOutput(canonical_status, output_json, output_md)


def _render_markdown(payload: dict[str, object]) -> str:
    rows = [
        ("Canonical Phase 2 status", payload["canonical_phase2_status"]),
        ("Breakout-retest family status", payload["breakout_retest_family_status"]),
        ("Measured-cost model", payload["measured_cost_model_status"]),
        ("Measured-cost revalidation", payload["measured_cost_revalidation_status"]),
        ("Measured-cost assumption delta", payload["measured_cost_assumption_delta_status"]),
        ("Measured-cost sanity", payload["measured_cost_sanity_status"]),
        ("Actual demo cost reconciliation", payload["actual_demo_cost_reconciliation_status"]),
        ("Actual demo cost resolution", payload["actual_demo_cost_resolution_status"]),
        ("Actual demo cost current practical blocker", str(payload["actual_demo_cost_current_practical_blocker"]).lower()),
        ("Phase 1 acceptance", payload["phase1_acceptance_status"]),
        ("Phase 2 readiness", payload["phase2_readiness_status"]),
        ("Experimental demo executor", payload["experimental_demo_executor_status"]),
        ("Demo execution as Phase 2 evidence", str(payload["demo_execution_as_phase2_evidence"]).lower()),
        ("Live trading authorized", str(payload["live_trading_authorized"]).lower()),
    ]
    return "\n".join(
        [
            "# Phase 2 Blocker Summary",
            "",
            f"Overall status: {payload['status']}",
            f"Generated at UTC: {payload['created_at_utc']}",
            "",
            str(payload["decision"]),
            "",
            _table(rows),
            "",
            "## Boundary",
            "",
            "This summary preserves the current NO-GO state for canonical Phase 2. The actual demo cost reconciliation can remove cost as the current practical demo concern, but it does not authorize canonical Phase 2, demo execution as Phase 2 evidence, broker-side execution, or live capital.",
            "",
        ]
    )


def _decision(canonical_blocked: bool, actual_demo_cost_status: str) -> str:
    if canonical_blocked and actual_demo_cost_status == "PASS":
        return (
            "Canonical Phase 2 is still blocked for the old tight-stop Phase 0 ledger because measured-cost "
            "revalidation and assumption delta are FAIL. However, actual demo cost reconciliation is PASS, "
            "so cost is no longer treated as the current practical blocker for the demo/wider-stop evidence lane; "
            "the active concern shifts to edge quality, win rate, duplicate exposure, sample size, and formal "
            "cost-aware hypothesis promotion."
        )
    if canonical_blocked:
        return (
            "Canonical Phase 2 is blocked because the measured-cost model is PASS but breakout-retest "
            "measured-cost revalidation and assumption delta are FAIL."
        )
    return "Canonical Phase 2 cost status needs review because the measured-cost block signature was not found."


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _table(rows: list[tuple[str, object]]) -> str:
    body = [f"| {key} | {_escape(str(value))} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 2 measured-cost blocker summary.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_phase2_blocker_summary(args.root, args.output_json)
    print(f"Phase 2 blocker summary: {output.status}")
    print(output.markdown_path)
    return 0 if output.status == "BLOCKED_BY_MEASURED_COST" else 1


if __name__ == "__main__":
    raise SystemExit(main())
