from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SCAN_SUFFIXES = {".set", ".ini", ".chr", ".args", ".env", ".json"}
SCAN_ROOT_PARTS = ("mt5", "scripts", "config", "deployment", "deploy")
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".venv", "outputs", "docs"}

FORBIDDEN_KEY_VALUES = {
    "InpDryRunOnly": "false",
    "InpBrokerActionAllowed": "true",
    "InpManageActionAllowed": "true",
    "InpAllowDemoTrading": "true",
    "InpAllowNonDemoAccounts": "true",
}
TOKEN_KEYS = {
    "InpExperimentalAuthorizationToken",
    "InpCostSuspensionAcknowledgementToken",
}


@dataclass(frozen=True)
class ArmingFinding:
    path: Path
    line_number: int
    term: str
    line: str


def audit_phase1_arming(root: Path) -> list[ArmingFinding]:
    findings: list[ArmingFinding] = []
    for path in _scan_paths(root):
        findings.extend(_find_armed_artifact_lines(path))
    return findings


def _find_armed_artifact_lines(path: Path) -> list[ArmingFinding]:
    findings: list[ArmingFinding] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        parsed = _parse_assignment(raw)
        if parsed is None:
            continue
        key, value = parsed
        normalized = value.strip().strip('"').strip("'").lower()
        if key in FORBIDDEN_KEY_VALUES and normalized == FORBIDDEN_KEY_VALUES[key]:
            findings.append(ArmingFinding(path, line_number, f"{key}={value}", raw.strip()))
            continue
        if key in TOKEN_KEYS and value.strip().strip('"').strip("'"):
            findings.append(ArmingFinding(path, line_number, f"{key}=nonblank", raw.strip()))
    return findings


def _parse_assignment(raw: str) -> tuple[str, str] | None:
    stripped = raw.strip()
    if not stripped or stripped.startswith((";", "#", "//")) or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    return key.strip().strip('"'), value.strip().rstrip(",").strip()


def _scan_paths(root: Path) -> list[Path]:
    roots = [root / part for part in SCAN_ROOT_PARTS if (root / part).exists()]
    if not roots:
        roots = [root]
    return sorted(
        path
        for scan_root in roots
        for path in scan_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SCAN_SUFFIXES
        and not any(part in IGNORED_PARTS for part in path.parts)
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = audit_phase1_arming(root)
    if findings:
        for finding in findings:
            rel = finding.path.relative_to(root) if finding.path.is_relative_to(root) else finding.path
            print(f"{rel}:{finding.line_number}: {finding.term}: {finding.line}")
        return 1
    print("Phase 1 arming audit OK: committed arming/profile artifacts are disarmed and auth tokens are blank.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
