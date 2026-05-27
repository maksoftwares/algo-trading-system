from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class SafetyFinding:
    path: Path
    line_number: int
    term: str
    line: str


def audit_phase3_tree(root: Path) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    for path in _scan_paths(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for term in FORBIDDEN_TERMS:
                if term in line:
                    findings.append(SafetyFinding(path, line_number, term, line.strip()))
    return findings


def _scan_paths(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in SCAN_SUFFIXES
        and not any(part in IGNORED_PARTS for part in path.parts)
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = audit_phase3_tree(root)
    if findings:
        for finding in findings:
            rel = finding.path.relative_to(root)
            print(f"{rel}:{finding.line_number}: {finding.term}: {finding.line}")
        return 1
    print("Phase 3 experimental safety audit OK: no broker-action calls found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
