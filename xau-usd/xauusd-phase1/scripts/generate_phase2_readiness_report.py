from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE2_READINESS_REPORT.md"
DEFAULT_OWNER_APPROVAL = Path("outputs") / "reports" / "PHASE2_OWNER_APPROVAL.md"
OWNER_APPROVAL_TOKEN = "PHASE2_PAPER_PREP_APPROVED"


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
        _status_gate("Phase 1 acceptance", report_dir / "PHASE1_ACCEPTANCE_REPORT.md", required="PASS"),
        _status_gate("Phase 1 review index", report_dir / "PHASE1_REVIEW_INDEX.md", required="PASS"),
        _summary_health_gate(status_fields, summary_path),
        _soak_progress_gate(soak),
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
    if OWNER_APPROVAL_TOKEN in text:
        return Phase2ReadinessItem("Project owner approval", "PASS", f"Approval token found in `{path}`.")
    return Phase2ReadinessItem("Project owner approval", "PENDING", f"Approval token missing in `{path}`.")


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
