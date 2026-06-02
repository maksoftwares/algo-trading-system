from __future__ import annotations

import argparse
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
    "History" + "Order" + "Send",
    "Order" + "Send" + "Result",
)
SCAN_SUFFIXES = {".mq5", ".mqh"}


@dataclass(frozen=True)
class SafetyFinding:
    path: Path
    line_number: int
    term: str
    line: str


@dataclass(frozen=True)
class AuditOutput:
    status: str
    report_path: Path
    summary_path: Path
    findings_count: int


def audit_observer_tree(root: Path) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    mt5_root = root / "mt5"
    for path in _scan_paths(mt5_root):
        code_lines = strip_mql_comments(path.read_text(encoding="utf-8", errors="replace"))
        for line_number, line in code_lines:
            for term in FORBIDDEN_TERMS:
                if term in line:
                    findings.append(SafetyFinding(path, line_number, term, line.strip()))
    return findings


def strip_mql_comments(text: str) -> list[tuple[int, str]]:
    output: list[tuple[int, str]] = []
    in_block = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        index = 0
        code = ""
        while index < len(line):
            if in_block:
                end = line.find("*/", index)
                if end == -1:
                    index = len(line)
                else:
                    in_block = False
                    index = end + 2
                continue
            line_comment = line.find("//", index)
            block_comment = line.find("/*", index)
            if line_comment != -1 and (block_comment == -1 or line_comment < block_comment):
                code += line[index:line_comment]
                break
            if block_comment != -1:
                code += line[index:block_comment]
                in_block = True
                index = block_comment + 2
                continue
            code += line[index:]
            break
        output.append((line_number, code))
    return output


def generate_safety_report(root: Path, output_dir: Path | None = None) -> AuditOutput:
    root = root.resolve()
    output_dir = (output_dir or root / "outputs" / "reports").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    findings = audit_observer_tree(root)
    status = "PASS" if not findings else "FAIL"
    summary = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scan_root": str(root / "mt5"),
        "scan_suffixes": sorted(SCAN_SUFFIXES),
        "comments_ignored": True,
        "docs_ignored": True,
        "broker_action_code_allowed": False,
        "findings_count": len(findings),
        "findings": [_finding_to_json(root, finding) for finding in findings],
    }
    report_path = output_dir / "PHASE2B_OBSERVER_SAFETY_AUDIT.md"
    summary_path = output_dir / "PHASE2B_OBSERVER_SAFETY_AUDIT.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    return AuditOutput(status, report_path, summary_path, len(findings))


def _scan_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix in SCAN_SUFFIXES)


def _finding_to_json(root: Path, finding: SafetyFinding) -> dict[str, object]:
    try:
        relative = finding.path.relative_to(root)
    except ValueError:
        relative = finding.path
    return {
        "path": str(relative).replace("\\", "/"),
        "line_number": finding.line_number,
        "term": finding.term,
        "line": finding.line,
    }


def _render_report(summary: dict[str, object]) -> str:
    findings = summary.get("findings", [])
    lines = [
        "# Phase 2B Observer Safety Audit",
        "",
        f"Overall status: {summary['status']}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Scan root | {summary['scan_root']} |",
        f"| Comments ignored | {str(summary['comments_ignored']).lower()} |",
        f"| Docs ignored | {str(summary['docs_ignored']).lower()} |",
        f"| Broker-action code allowed | {str(summary['broker_action_code_allowed']).lower()} |",
        f"| Findings | {summary['findings_count']} |",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("No forbidden broker-action terms found in executable MQL5 observer code.")
    else:
        lines.extend(["| Path | Line | Term |", "| --- | ---: | --- |"])
        for item in findings:
            if isinstance(item, dict):
                lines.append(f"| {item['path']} | {item['line_number']} | {item['term']} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Audit the Phase 2B passive observer safety boundary.")
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_safety_report(args.root, args.output_dir)
    print(f"Phase 2B observer safety audit: {output.status}")
    print(output.report_path)
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
