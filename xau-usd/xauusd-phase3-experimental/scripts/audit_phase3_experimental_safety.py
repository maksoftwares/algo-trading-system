from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


FORBIDDEN_TERMS = (
    "Order" + "Send",
    "Order" + "Send" + "Async",
    "C" + "Trade",
    "trade" + ".Buy",
    "trade" + ".Sell",
    "Position" + "Open",
    "Position" + "Modify",
    "Position" + "Close",
)
SCAN_SUFFIXES = {".py", ".mq5", ".mqh"}
IGNORED_PARTS = {"__pycache__", ".pytest_cache", "outputs"}
PHASE2_AUTHORITY_SENTENCE = (
    "This report has no authority over Phase 2 readiness. "
    "PHASE2_READINESS_REPORT.md remains the sole real readiness authority."
)


@dataclass(frozen=True)
class SafetyFinding:
    path: Path
    line_number: int
    term: str
    line: str


@dataclass(frozen=True)
class SafetyReportOutput:
    status: str
    report_path: Path
    summary_path: Path
    findings_count: int


def audit_phase3_tree(root: Path) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    for path in _scan_paths(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for term in FORBIDDEN_TERMS:
                if term in line:
                    findings.append(SafetyFinding(path, line_number, term, line.strip()))
    return findings


def generate_phase3_safety_report(root: Path, output_dir: Path | None = None) -> SafetyReportOutput:
    root = root.resolve()
    output_dir = (output_dir or root / "outputs" / "reports").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    findings = audit_phase3_tree(root)
    boundary_status = _boundary_status(root)
    status = "PASS" if not findings and boundary_status == "PASS" else "FAIL"
    summary = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "scan_root": str(root),
        "boundary_status": boundary_status,
        "mt5_runtime_touched": False,
        "broker_action_code_allowed": False,
        "scan_suffixes": sorted(SCAN_SUFFIXES),
        "ignored_parts": sorted(IGNORED_PARTS),
        "forbidden_term_count": len(FORBIDDEN_TERMS),
        "findings_count": len(findings),
        "findings": [_finding_to_json(root, finding) for finding in findings],
    }
    report_path = output_dir / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.md"
    summary_path = output_dir / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    return SafetyReportOutput(
        status=status,
        report_path=report_path,
        summary_path=summary_path,
        findings_count=len(findings),
    )


def _scan_paths(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in SCAN_SUFFIXES
        and not any(part in IGNORED_PARTS for part in path.parts)
    )


def _boundary_status(root: Path) -> str:
    lower_parts = {part.lower() for part in root.parts}
    if "mt5portablegoldmission" in lower_parts:
        return "FAIL"
    if root.name != "xauusd-phase3-experimental":
        return "WARN_NONSTANDARD_ROOT"
    return "PASS"


def _finding_to_json(root: Path, finding: SafetyFinding) -> dict[str, object]:
    try:
        relative = finding.path.relative_to(root)
    except ValueError:
        relative = finding.path
    return {
        "path": str(relative),
        "line_number": finding.line_number,
        "term": finding.term,
        "line": finding.line,
    }


def _render_report(summary: dict[str, object]) -> str:
    findings = summary.get("findings", [])
    if not isinstance(findings, list):
        findings = []
    return "\n".join(
        [
            "# Phase 3 Experimental Safety Report",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {summary['status']}",
            "",
            "## Boundary",
            "",
            _table(
                [
                    ("Scan root", str(summary["scan_root"])),
                    ("Boundary status", str(summary["boundary_status"])),
                    ("MT5 runtime touched", str(summary["mt5_runtime_touched"])),
                    ("Broker-action code allowed", str(summary["broker_action_code_allowed"])),
                    ("Findings", str(summary["findings_count"])),
                ]
            ),
            "",
            "## Findings",
            "",
            _findings_table(findings),
            "",
        ]
    )


def _findings_table(findings: list[object]) -> str:
    if not findings:
        return "No forbidden broker-action references found in Phase 3 experimental source files."
    rows = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        rows.append((str(item.get("path", "")), str(item.get("line_number", "")), str(item.get("term", ""))))
    body = [f"| {_escape(path)} | {_escape(line)} | {_escape(term)} |" for path, line, term in rows]
    return "\n".join(["| Path | Line | Term |", "| --- | ---: | --- |", *body])


def _table(rows: list[tuple[str, str]]) -> str:
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = generate_phase3_safety_report(root)
    if output.status != "PASS":
        findings = audit_phase3_tree(root)
        for finding in findings:
            rel = finding.path.relative_to(root)
            print(f"{rel}:{finding.line_number}: {finding.term}: {finding.line}")
        print(output.report_path)
        return 1
    print("Phase 3 experimental safety audit OK: no broker-action calls found.")
    print(output.report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
