from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


BROKER_ACTION_TERMS = (
    "OrderSend",
    "OrderSendAsync",
    "CTrade",
    "trade.Buy",
    "trade.Sell",
    "PositionOpen",
    "PositionModify",
    "PositionClose",
    "TRADE_ACTION_DEAL",
    "TRADE_ACTION_PENDING",
)

OBSERVED_EA_PATHS = (
    "xau-usd/xauusd-phase1/mt5/Experts/Phase1DryRunShell.mq5",
    "xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5",
)

KNOWN_PREEXISTING_QUARANTINED_PATHS = {
    "xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5"
}


@dataclass
class BoundaryFinding:
    path: str
    term: str
    line: int
    decision: str
    detail: str


@dataclass
class BoundaryAudit:
    findings: list[BoundaryFinding]
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _normalize(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_wr50_broker_action_allowed(rel_path: str) -> bool:
    return (
        rel_path.startswith("xau-usd/xauusd-wr50-experimental/mt5/Experts/")
        or rel_path == "xau-usd/xauusd-wr50-experimental/mt5/Include/WR50_OrderExecutor.mqh"
    )


def _iter_mql_files(root: Path) -> list[Path]:
    return [path for suffix in ("*.mq5", "*.mqh") for path in root.rglob(suffix)]


def scan_broker_action_terms(root: Path) -> tuple[list[BoundaryFinding], list[str], list[str]]:
    findings: list[BoundaryFinding] = []
    errors: list[str] = []
    warnings: list[str] = []
    term_regex = re.compile("|".join(re.escape(term) for term in BROKER_ACTION_TERMS))
    for path in _iter_mql_files(root):
        rel_path = _normalize(path, root)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in term_regex.finditer(line):
                term = match.group(0)
                if _is_wr50_broker_action_allowed(rel_path):
                    decision = "PASS"
                    detail = "allowed WR50 experimental broker-action path"
                elif rel_path in KNOWN_PREEXISTING_QUARANTINED_PATHS:
                    decision = "WARN"
                    detail = "known pre-existing quarantined experimental executor; not part of WR50"
                    warnings.append(f"{rel_path}:{line_number}: known pre-existing {term}")
                else:
                    decision = "FAIL"
                    detail = "broker-action term outside WR50 allowlist"
                    errors.append(f"{rel_path}:{line_number}: {term} outside WR50 allowlist")
                findings.append(BoundaryFinding(rel_path, term, line_number, decision, detail))
    return findings, errors, warnings


def validate_wr50_docs(root: Path) -> list[str]:
    errors: list[str] = []
    docs = [
        root / "xau-usd" / "xauusd-wr50-experimental" / "README.md",
        root / "xau-usd" / "xauusd-wr50-experimental" / "docs" / "WR50_EXPERIMENTAL_LANE_RULES.md",
        root / "xau-usd" / "xauusd-wr50-experimental" / "docs" / "WR50_PHASE_BOUNDARY.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8", errors="ignore").lower() for path in docs if path.exists())
    required_phrases = [
        "demo",
        "do not authorize canonical phase 2",
        "do not authorize live trading",
        "cost_suspended_canonical",
    ]
    for phrase in required_phrases:
        if phrase not in combined:
            errors.append(f"WR50 docs missing boundary phrase: {phrase}")
    return errors


def validate_wr50_magic_files(root: Path) -> list[str]:
    errors: list[str] = []
    wr50_root = root / "xau-usd" / "xauusd-wr50-experimental"
    for path in [*wr50_root.rglob("*.mq5"), *wr50_root.rglob("*.mqh"), *wr50_root.rglob("*.md"), *wr50_root.rglob("*.csv")]:
        rel_path = _normalize(path, root)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for value in re.findall(r"\b93\d{4}\b", text):
            magic = int(value)
            if not (930000 <= magic <= 930999):
                errors.append(f"{rel_path}: WR50-like magic {magic} outside 930000-930999")
    return errors


def validate_observed_eas_not_modified(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--", *OBSERVED_EA_PATHS],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError:
        return errors
    if result.returncode != 0:
        return errors
    for line in result.stdout.splitlines():
        if line.strip():
            errors.append(f"observed EA path modified in worktree: {line}")
    return errors


def run_audit(root: Path) -> BoundaryAudit:
    findings, errors, warnings = scan_broker_action_terms(root)
    errors.extend(validate_wr50_docs(root))
    errors.extend(validate_wr50_magic_files(root))
    errors.extend(validate_observed_eas_not_modified(root))
    return BoundaryAudit(findings, errors, warnings)


def write_report(audit: BoundaryAudit, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if audit.ok else "FAIL"
    lines = [
        "# WR50 Boundary Audit",
        "",
        f"Overall status: {status}",
        "",
        "## Broker-Action Terms",
        "",
        "| Path | Line | Term | Decision | Detail |",
        "| --- | ---: | --- | --- | --- |",
    ]
    if audit.findings:
        for finding in audit.findings:
            lines.append(
                f"| {finding.path} | {finding.line} | `{finding.term}` | {finding.decision} | {finding.detail} |"
            )
    else:
        lines.append("| None |  |  | PASS | No MQL broker-action terms found. |")
    lines.extend(["", "## Errors", ""])
    lines.extend([f"- {error}" for error in audit.errors] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {warning}" for warning in audit.warnings] or ["- None"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This audit is path-aware for the WR50 experimental lane and records the existing quarantined Phase 1 experimental executor as a pre-existing exception when unmodified.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    root = default_repo_root()
    parser = argparse.ArgumentParser(description="Audit WR50 broker-action boundaries.")
    parser.add_argument("--repo-root", type=Path, default=root)
    parser.add_argument(
        "--report",
        type=Path,
        default=root / "xau-usd" / "xauusd-wr50-experimental" / "outputs" / "reports" / "WR50_BOUNDARY_AUDIT.md",
    )
    args = parser.parse_args(argv)

    audit = run_audit(args.repo_root)
    write_report(audit, args.report)
    print(f"WR50 boundary audit: {'PASS' if audit.ok else 'FAIL'}")
    print(f"Report: {args.report}")
    return 0 if audit.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

