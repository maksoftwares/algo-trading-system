from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE2_READINESS_REPORT.md"
DEFAULT_OWNER_APPROVAL = Path("outputs") / "reports" / "PHASE2_OWNER_APPROVAL.md"
OWNER_APPROVAL_TOKEN = "PHASE2_PAPER_PREP_APPROVED"
OWNER_APPROVAL_TRUE_FIELDS = (
    "single_edge_risk_ack",
    "no_live_capital_ack",
    "measured_cost_ack",
)
OWNER_APPROVAL_REQUIRED_FIELDS = (
    "owner",
    "decision_date_utc",
    "decision",
    "scope",
    "minimum_net_expectancy_r",
    *OWNER_APPROVAL_TRUE_FIELDS,
)
MIN_PHASE2_NET_EXPECTANCY_R = 0.15


@dataclass(frozen=True)
class Phase2ReadinessItem:
    gate: str
    status: str
    evidence: str


@dataclass(frozen=True)
class Phase2ReadinessOutput:
    status: str
    report_path: Path
    items: tuple[Phase2ReadinessItem, ...]


def generate_phase2_readiness_report(
    root: Path,
    report_path: Path | None = None,
    owner_approval_path: Path | None = None,
) -> Phase2ReadinessOutput:
    root = root.resolve()
    if report_path is None:
        report_path = root / DEFAULT_REPORT
    if owner_approval_path is None:
        owner_approval_path = root / DEFAULT_OWNER_APPROVAL
    report_path = report_path.resolve()
    owner_approval_path = owner_approval_path.resolve()

    report_dir = root / "outputs" / "reports"
    summary_path = report_dir / "PHASE1_STATUS_SUMMARY.json"
    summary = _read_json(summary_path)
    latest = _mapping(_mapping(summary.get("runtime")).get("latest_row"))
    soak = _mapping(summary.get("soak"))
    would_signal = _mapping(summary.get("would_signal"))
    status_fields = _mapping(summary.get("status"))

    items = [
        _file_gate("Phase 2 preparation spec", root / "docs" / "PHASE2_DRY_RUN_TO_PAPER_PREP_SPEC.md"),
        _status_gate(
            "Paper ledger schema preflight",
            report_dir / "PHASE2_PAPER_LEDGER_SCHEMA_REPORT.md",
            required="PASS",
        ),
        _file_contains_gate(
            "Phase 2 cost-measurement protocol",
            root / "docs" / "PHASE2_COST_MEASUREMENT_PROTOCOL.md",
            ("MIN_NET_EXPECTANCY_R_AFTER_MEASURED_COST = +0.15R", "cost-measurement experiment"),
        ),
        _file_contains_gate(
            "Single-edge risk plan",
            root / "docs" / "PHASE2_SINGLE_EDGE_RISK_PLAN.md",
            ("single-edge", "same-family", "+0.15R", "observer-only"),
        ),
        _file_contains_gate(
            "Phase 2 operations prep",
            root / "docs" / "PHASE2_OPERATIONS_PREP.md",
            ("External Health Monitor Spec", "Disaster Recovery Runbook", "Capital Allocation Ladder"),
        ),
        _status_or_pending_gate(
            "VPS selection",
            root / "docs" / "PHASE2_VPS_SELECTION_MATRIX.md",
            required="PASS",
        ),
        _file_gate("Cost reporting policy", _phase0_root(root) / "docs" / "COST_REPORTING_POLICY.md"),
        _status_or_pending_gate(
            "Fixed-notional reporting",
            _phase0_root(root) / "outputs" / "reports" / "FIXED_NOTIONAL_REPORT.md",
            required="PASS",
        ),
        _file_contains_gate(
            "D2 fixed-notional R-series canonicalization",
            _phase0_root(root) / "docs" / "PHASE0_INDEPENDENT_VALIDATION.md",
            ("Canonical fixed-notional monthly R", "superseded"),
        ),
        _status_or_pending_gate(
            "Frequency-normalized concentration audit",
            _phase0_root(root) / "outputs" / "reports" / "PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md",
            required="PASS",
        ),
        _file_contains_gate(
            "Non-level H4/D1 candidate plan",
            _phase0_root(root) / "docs" / "CANDIDATE_RESEARCH_BACKLOG.md",
            (
                "d1_compression_h4_expansion_v0",
                "h4_real_yield_proxy_momentum_v0",
                "d1_multi_day_exhaustion_reversion_v0",
            ),
        ),
        _status_or_pending_gate(
            "Measured cost model",
            _phase0_root(root) / "outputs" / "reports" / "MEASURED_COST_MODEL.md",
            required="PASS",
        ),
        _status_or_pending_gate(
            "Measured-cost revalidation",
            _phase0_root(root) / "outputs" / "reports" / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md",
            required="PASS",
        ),
        _status_gate("Phase 1 acceptance", report_dir / "PHASE1_ACCEPTANCE_REPORT.md", required="PASS"),
        _status_gate("Phase 1 review index", report_dir / "PHASE1_REVIEW_INDEX.md", required="PASS"),
        _summary_health_gate(status_fields, summary_path),
        _soak_progress_gate(soak),
        _active_market_soak_gate(soak),
        _process_code_freeze_gate(soak),
        _latest_boundary_gate(latest),
        _would_signal_gate(would_signal),
        _owner_approval_gate(owner_approval_path),
    ]
    status = _overall_status(items)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(status, root, items, summary), encoding="utf-8")
    return Phase2ReadinessOutput(status, report_path, tuple(items))


def _file_gate(gate: str, path: Path) -> Phase2ReadinessItem:
    if path.exists() and path.stat().st_size > 0:
        return Phase2ReadinessItem(gate, "PASS", f"Found `{path}`.")
    return Phase2ReadinessItem(gate, "FAIL", f"Missing or empty `{path}`.")


def _file_contains_gate(gate: str, path: Path, required_tokens: tuple[str, ...]) -> Phase2ReadinessItem:
    if not path.exists() or path.stat().st_size == 0:
        return Phase2ReadinessItem(gate, "FAIL", f"Missing or empty `{path}`.")
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [token for token in required_tokens if token not in text]
    if missing:
        return Phase2ReadinessItem(
            gate,
            "FAIL",
            f"`{path}` is missing required token(s): {', '.join(missing)}.",
        )
    return Phase2ReadinessItem(gate, "PASS", f"`{path}` contains required Phase 2 controls.")


def _status_or_pending_gate(gate: str, path: Path, required: str) -> Phase2ReadinessItem:
    if not path.exists():
        return Phase2ReadinessItem(gate, "PENDING", f"Missing `{path}`; required before Phase 2 authorization.")
    status = _read_markdown_status(path)
    if status == required:
        return Phase2ReadinessItem(gate, "PASS", f"`{path}` status is {status}.")
    if status in {"PENDING", "WARN", "REVIEW", ""}:
        return Phase2ReadinessItem(gate, "PENDING", f"`{path}` status is {status or 'unclear'}; required {required}.")
    return Phase2ReadinessItem(gate, "FAIL", f"`{path}` status is {status}; required {required}.")


def _phase0_root(phase1_root: Path) -> Path:
    return phase1_root.parent / "xauusd-phase0"


def _status_gate(gate: str, path: Path, required: str) -> Phase2ReadinessItem:
    if not path.exists():
        return Phase2ReadinessItem(gate, "FAIL", f"Missing `{path}`.")
    status = _read_markdown_status(path)
    if status == required:
        return Phase2ReadinessItem(gate, "PASS", f"`{path}` status is {status}.")
    if status in {"PENDING", "WARN"}:
        return Phase2ReadinessItem(gate, "PENDING", f"`{path}` status is {status}; required {required}.")
    if status == "FAIL":
        return Phase2ReadinessItem(gate, "FAIL", f"`{path}` status is FAIL.")
    return Phase2ReadinessItem(gate, "WARN", f"`{path}` status is unclear.")


def _summary_health_gate(status_fields: dict[str, Any], summary_path: Path) -> Phase2ReadinessItem:
    if not summary_path.exists():
        return Phase2ReadinessItem("Phase 1 summary health", "FAIL", f"Missing `{summary_path}`.")
    required = ("log_verification", "soak_analysis", "runtime_health")
    bad = [name for name in required if status_fields.get(name) != "PASS"]
    if bad:
        return Phase2ReadinessItem("Phase 1 summary health", "FAIL", "Non-pass status fields: " + ", ".join(bad))
    return Phase2ReadinessItem("Phase 1 summary health", "PASS", f"Core summary checks are PASS in `{summary_path}`.")


def _soak_progress_gate(soak: dict[str, Any]) -> Phase2ReadinessItem:
    progress = _to_float(soak.get("progress_pct"))
    observed = _to_float(soak.get("observed_days"))
    required = _to_float(soak.get("required_days")) or 5.0
    if progress is None:
        return Phase2ReadinessItem("Five trading day soak", "FAIL", "Soak progress missing from status summary.")
    evidence = f"Progress {progress:.2f}%; observed {observed if observed is not None else 'n/a'} of {required:.2f} required days."
    if progress >= 100.0:
        return Phase2ReadinessItem("Five trading day soak", "PASS", evidence)
    return Phase2ReadinessItem("Five trading day soak", "PENDING", evidence)


def _active_market_soak_gate(soak: dict[str, Any]) -> Phase2ReadinessItem:
    required = _to_float(soak.get("required_uninterrupted_streak_hours")) or 72.0
    longest = _to_float(soak.get("active_market_streak_hours")) or _to_float(soak.get("longest_streak_hours"))
    current = _to_float(soak.get("current_streak_hours"))
    passed = soak.get("uninterrupted_soak_pass") is True
    if longest is None:
        return Phase2ReadinessItem("Active-market 72-hour soak", "FAIL", "Streak fields missing from status summary.")
    evidence = (
        f"Longest active streak {longest:.2f}h; current active streak "
        f"{current if current is not None else 'n/a'}h; required {required:.0f}h; "
        f"weekend policy {soak.get('weekend_policy', 'n/a')}."
    )
    if passed and longest >= required:
        return Phase2ReadinessItem("Active-market 72-hour soak", "PASS", evidence)
    return Phase2ReadinessItem("Active-market 72-hour soak", "PENDING", evidence)


def _process_code_freeze_gate(soak: dict[str, Any]) -> Phase2ReadinessItem:
    required = _to_float(soak.get("required_code_freeze_hours")) or 96.0
    process_uptime = _to_float(soak.get("process_uptime_streak_hours"))
    code_freeze_hours = _to_float(soak.get("code_freeze_hours"))
    passed = soak.get("process_code_freeze_pass") is True
    if process_uptime is None or code_freeze_hours is None:
        return Phase2ReadinessItem(
            "Process/code-freeze 96-hour gate",
            "FAIL",
            "Process/code-freeze fields missing from status summary.",
        )
    evidence = (
        f"Process uptime streak {process_uptime:.2f}h; code-freeze {code_freeze_hours:.2f}h; "
        f"required {required:.0f}h; marker {soak.get('code_freeze_started_at') or 'missing'}."
    )
    if passed and process_uptime >= required and code_freeze_hours >= required:
        return Phase2ReadinessItem("Process/code-freeze 96-hour gate", "PASS", evidence)
    return Phase2ReadinessItem("Process/code-freeze 96-hour gate", "PENDING", evidence)


def _latest_boundary_gate(latest: dict[str, Any]) -> Phase2ReadinessItem:
    dry_run = str(latest.get("dry_run", "")).lower()
    permission = str(latest.get("trade_permission", "")).lower()
    server_time = str(latest.get("server_time_status", ""))
    if dry_run == "true" and permission == "false" and server_time == "CLOCK_OK":
        return Phase2ReadinessItem(
            "Latest dry-run boundary",
            "PASS",
            (
                f"bar_time={latest.get('bar_time', 'n/a')}; "
                f"dry_run={dry_run}; permission={permission}; server_time={server_time}."
            ),
        )
    return Phase2ReadinessItem(
        "Latest dry-run boundary",
        "FAIL",
        f"Unexpected latest state: dry_run={dry_run or 'blank'}, permission={permission or 'blank'}, server_time={server_time or 'blank'}.",
    )


def _would_signal_gate(would_signal: dict[str, Any]) -> Phase2ReadinessItem:
    rows = _to_int(would_signal.get("rows"))
    clusters = _to_int(would_signal.get("clusters"))
    if rows and clusters:
        return Phase2ReadinessItem("Would-signal evidence", "PASS", f"Rows: {rows}; clusters: {clusters}.")
    return Phase2ReadinessItem("Would-signal evidence", "WARN", "No would-signal clusters found yet.")


def _owner_approval_gate(path: Path) -> Phase2ReadinessItem:
    if not path.exists():
        return Phase2ReadinessItem(
            "Project owner approval",
            "PENDING",
            f"No approval file found at `{path}`.",
        )
    text = path.read_text(encoding="utf-8", errors="replace")
    if OWNER_APPROVAL_TOKEN not in text:
        return Phase2ReadinessItem("Project owner approval", "PENDING", f"Approval token missing in `{path}`.")
    fields = _parse_approval_fields(text)
    missing = [name for name in OWNER_APPROVAL_REQUIRED_FIELDS if not fields.get(name)]
    if missing:
        return Phase2ReadinessItem(
            "Project owner approval",
            "PENDING",
            f"`{path}` is missing owner approval field(s): {', '.join(missing)}.",
        )
    bad_true_fields = [name for name in OWNER_APPROVAL_TRUE_FIELDS if fields.get(name, "").lower() != "true"]
    if bad_true_fields:
        return Phase2ReadinessItem(
            "Project owner approval",
            "PENDING",
            f"`{path}` must set acknowledgement field(s) to true: {', '.join(bad_true_fields)}.",
        )
    decision = fields.get("decision", "").upper()
    if "APPROVED" not in decision:
        return Phase2ReadinessItem("Project owner approval", "PENDING", f"`{path}` decision is not APPROVED.")
    scope = fields.get("scope", "").lower()
    if "paper" not in scope:
        return Phase2ReadinessItem(
            "Project owner approval",
            "PENDING",
            f"`{path}` scope must be paper-mode only.",
        )
    minimum_net = _to_float(fields.get("minimum_net_expectancy_r"))
    if minimum_net is None or minimum_net < MIN_PHASE2_NET_EXPECTANCY_R:
        return Phase2ReadinessItem(
            "Project owner approval",
            "PENDING",
            f"`{path}` minimum_net_expectancy_r must be at least {MIN_PHASE2_NET_EXPECTANCY_R:.2f}.",
        )
    return Phase2ReadinessItem("Project owner approval", "PASS", f"Signed approval fields found in `{path}`.")


def _parse_approval_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized = key.strip().lower().replace(" ", "_").replace("-", "_")
        fields[normalized] = value.strip()
    return fields


def _overall_status(items: list[Phase2ReadinessItem]) -> str:
    if any(item.status == "FAIL" for item in items):
        return "FAIL"
    if any(item.status in {"WARN", "PENDING"} for item in items):
        return "PENDING"
    return "PASS"


def _render_report(
    status: str,
    root: Path,
    items: list[Phase2ReadinessItem],
    summary: dict[str, Any],
) -> str:
    runtime = _mapping(summary.get("runtime"))
    latest = _mapping(runtime.get("latest_row"))
    soak = _mapping(summary.get("soak"))
    return "\n".join(
        [
            "# Phase 2 Readiness Report",
            "",
            f"Overall status: {status}",
            "",
            "## Decision",
            "",
            _decision_text(status),
            "",
            "## Gates",
            "",
            _markdown_table(
                [{"Gate": item.gate, "Status": item.status, "Evidence": item.evidence} for item in items],
                ["Gate", "Status", "Evidence"],
            ),
            "",
            "## Current Runtime",
            "",
            _markdown_table(
                [
                    {
                        "Decision Rows": _cell(runtime.get("decision_rows")),
                        "Latest Bar": _cell(latest.get("bar_time")),
                        "Dry Run": _cell(latest.get("dry_run")),
                        "Permission": _cell(latest.get("trade_permission")),
                        "Server Time": _cell(latest.get("server_time_status")),
                        "Soak Progress": f"{_cell(soak.get('progress_pct'))}%",
                    }
                ],
                ["Decision Rows", "Latest Bar", "Dry Run", "Permission", "Server Time", "Soak Progress"],
            ),
            "",
            "## Boundary",
            "",
            "- This report does not authorize Phase 2 implementation.",
            "- Preparation remains documentation, interfaces, and evidence only.",
            "- Paper-mode implementation still requires all gates above to pass.",
            f"- Workspace root: `{root}`",
            "",
        ]
    )


def _decision_text(status: str) -> str:
    if status == "PASS":
        return "Phase 2 implementation can be proposed for the approved paper-mode scope."
    if status == "FAIL":
        return "Phase 2 implementation is blocked by at least one failing readiness gate."
    return "Phase 2 preparation may continue, but implementation is not authorized yet."


def _read_markdown_status(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith("Overall status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
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
    parser = argparse.ArgumentParser(description="Generate the Phase 2 readiness/preflight report.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Phase 1 workspace root.",
    )
    parser.add_argument("--report", type=Path, default=None, help="Markdown report path.")
    parser.add_argument(
        "--owner-approval",
        type=Path,
        default=None,
        help="Optional owner approval file containing the required approval token.",
    )
    args = parser.parse_args(argv)

    output = generate_phase2_readiness_report(args.root, args.report, args.owner_approval)
    print(f"Phase 2 readiness report: {output.status}")
    print(output.report_path)
    for item in output.items:
        print(f"{item.status}: {item.gate} - {item.evidence}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
