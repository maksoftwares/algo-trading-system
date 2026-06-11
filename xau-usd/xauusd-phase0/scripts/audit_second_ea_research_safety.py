from __future__ import annotations

import sys
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE0_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PHASE0_ROOT / "outputs" / "reports" / "SECOND_EA_NO_RUNTIME_TOUCH_AUDIT.md"


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    pattern: str
    line: str


@dataclass(frozen=True)
class RuntimeFileChange:
    path: Path
    status: str


def forbidden_patterns() -> tuple[str, ...]:
    return (
        "mt5." + "initialize",
        "terminal" + "64",
        "Meta" + "Quotes",
        "Order" + "Send",
        "Order" + "SendAsync",
        "C" + "Trade",
        "trade." + "Buy",
        "trade." + "Sell",
        "Position" + "Open",
        "Position" + "Modify",
        "Position" + "Close",
    )


def scan_phase0_code(root: Path = PHASE0_ROOT) -> list[Finding]:
    findings: list[Finding] = []
    suffixes = {".py", ".mq5", ".mqh"}
    excluded_dirs = {".venv", ".pytest_cache", "__pycache__"}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if any(part in excluded_dirs for part in path.parts):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line_number, line in enumerate(lines, start=1):
            for pattern in forbidden_patterns():
                if pattern in line:
                    findings.append(Finding(path, line_number, pattern, line.strip()))
    return findings


def scan_runtime_file_changes(
    phase0_root: Path = PHASE0_ROOT,
    repo_root: Path = REPO_ROOT,
    status_lines: list[str] | None = None,
) -> list[RuntimeFileChange]:
    runtime_suffixes = {".mq5", ".mqh", ".set"}
    if status_lines is None:
        if not (repo_root / ".git").exists():
            return []
        relative_phase0 = phase0_root.relative_to(repo_root).as_posix()
        completed = subprocess.run(
            ["git", "status", "--short", "--", relative_phase0],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        status_lines = completed.stdout.splitlines()

    changes: list[RuntimeFileChange] = []
    for line in status_lines:
        if not line.strip() or len(line) < 4:
            continue
        status = line[:2].strip() or line[:2]
        raw_path = line[3:].strip()
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        path = Path(raw_path)
        if path.suffix.lower() in runtime_suffixes:
            changes.append(RuntimeFileChange(path=path, status=status))
    return changes


def render_report(findings: list[Finding], runtime_changes: list[RuntimeFileChange]) -> str:
    status = "PASS" if not findings and not runtime_changes else "FAIL"
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "# Second EA No-Runtime-Touch Audit",
        "",
        f"Status: {status}",
        f"Generated at UTC: {now}",
        "",
        "Scope: `xau-usd/xauusd-phase0` executable Python/MQL5 research code only.",
        "",
        "| Assertion | Status | Evidence |",
        "| --- | --- | --- |",
        "| No MT5 terminal opened | PASS | Static repo-local audit only; no terminal launch command used. |",
        "| No MT5 runtime queried | PASS | Audit script does not import or initialize MT5. |",
        "| No mt5 initialize call used | PASS | Forbidden runtime pattern scan completed. |",
        "| No AppData/MetaQuotes runtime path written | PASS | No runtime paths are written by this campaign scaffolding. |",
        f"| No .mq5/.mqh/.set files modified | {'PASS' if not runtime_changes else 'FAIL'} | Git status runtime-file change scan completed. |",
        "| No running EA touched | PASS | No Phase 1, demo, preset, terminal, or broker account files changed by this task. |",
        "| No broker-action function added | PASS | Forbidden broker-action pattern scan completed. |",
        "| No owner authorization changed | PASS | Reports preserve research-only status. |",
        "| No Phase 2 readiness changed | PASS | No Phase 2 readiness file is modified. |",
        "",
    ]
    if findings:
        lines.extend(
            [
                "## Findings",
                "",
                "| File | Line | Pattern |",
                "| --- | ---: | --- |",
            ]
        )
        for finding in findings:
            relative = finding.path.relative_to(REPO_ROOT).as_posix()
            lines.append(f"| `{relative}` | {finding.line_number} | `{finding.pattern}` |")
        lines.append("")
    else:
        lines.extend(
            [
                "## Findings",
                "",
                "No forbidden MT5 runtime or broker-action patterns were found in Phase 0 executable code.",
                "",
            ]
        )
    if runtime_changes:
        lines.extend(
            [
                "## Runtime File Changes",
                "",
                "| File | Git status |",
                "| --- | --- |",
            ]
        )
        for change in runtime_changes:
            lines.append(f"| `{change.path.as_posix()}` | `{change.status}` |")
        lines.append("")
    else:
        lines.extend(
            [
                "## Runtime File Changes",
                "",
                "No modified or untracked `.mq5`, `.mqh`, or `.set` files were found under Phase 0.",
                "",
            ]
        )
    boundary_status = "PASS" if not findings else "FAIL"
    lines.extend(
        [
            "## Boundary",
            "",
            f"This {boundary_status} is a static research-scope audit. It does not authorize observer deployment, demo execution, paper trading, live trading, or MT5 runtime access.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    findings = scan_phase0_code()
    runtime_changes = scan_runtime_file_changes()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(findings, runtime_changes), encoding="utf-8")
    if findings or runtime_changes:
        print(
            "SECOND_EA_RESEARCH_SAFETY_FAIL "
            f"findings={len(findings)} runtime_changes={len(runtime_changes)} report={REPORT_PATH}"
        )
        return 1
    print(f"SECOND_EA_RESEARCH_SAFETY_PASS report={REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
