from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


CONFIG_SUFFIXES = {".set", ".ini", ".chr", ".args", ".env", ".json"}
EXECUTABLE_SUFFIXES = {".py", ".ps1", ".bat", ".cmd", ".yaml", ".yml", ".toml", ".cfg"}
SCAN_SUFFIXES = CONFIG_SUFFIXES | EXECUTABLE_SUFFIXES
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
A3_SCRIPT_ARMING_MARKERS = (
    "1033669",
    "A3",
    "Account3",
    "933200",
    "933300",
    "933400",
)
SCRIPT_ARMING_PATTERNS = (
    "InpDryRunOnly=false",
    "InpBrokerActionAllowed=true",
    "InpManageActionAllowed=true",
    '"InpDryRunOnly": "false"',
    '"InpBrokerActionAllowed": "true"',
    '"InpManageActionAllowed": "true"',
    "'InpDryRunOnly': 'false'",
    "'InpBrokerActionAllowed': 'true'",
    "'InpManageActionAllowed': 'true'",
)
SCRIPT_POLICY_REQUIREMENTS = {
    "default_verify_or_dry_run": ("if not args.apply", "mode: Mode = \"verify-only\"", "default=DEFAULT_MODE"),
    "explicit_apply_flag": ("--apply",),
    "owner_packet_path_required": ("owner_packet", "owner-packet"),
    "owner_packet_hash_required": ("owner_packet_sha256", "owner-packet-sha256"),
    "review_hash_required": ("review_hash", "review-hash"),
    "zero_exposure_check_required": (
        "zero_exposure",
        "broker_a3_exposure_state",
        "a3_exposure_zero",
        "broker_exposure_absent",
    ),
    "profile_backup_required": ("backup_profile", "profile_backup"),
    "current_a3_pause_ack_required": ("acknowledge_current_a3_pause", "A3_ENTRY_LANES_PAUSED"),
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
        if path.suffix.lower() in EXECUTABLE_SUFFIXES:
            findings.extend(_find_script_policy_findings(path))
        else:
            findings.extend(_find_armed_artifact_lines(path))
    return findings


def _find_script_policy_findings(path: Path) -> list[ArmingFinding]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not _is_a3_deployment_script(path) or not _contains_a3_arming_material(text):
        return []
    findings: list[ArmingFinding] = []
    for requirement, markers in SCRIPT_POLICY_REQUIREMENTS.items():
        if any(marker in text for marker in markers):
            continue
        findings.append(
            ArmingFinding(
                path=path,
                line_number=1,
                term=f"script_policy_missing:{requirement}",
                line="A3 executable arming material must be policy-gated before commit.",
            )
        )
    return findings


def _contains_a3_arming_material(text: str) -> bool:
    return any(marker in text for marker in A3_SCRIPT_ARMING_MARKERS) and any(pattern in text for pattern in SCRIPT_ARMING_PATTERNS)


def _is_a3_deployment_script(path: Path) -> bool:
    name = path.name.lower()
    return name.startswith(("attach_a3", "apply_a3", "deploy_a3"))


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
    tracked = _git_tracked_paths(root)
    if tracked:
        return tracked
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


def _git_tracked_paths(root: Path) -> list[Path]:
    try:
        repo_root = Path(
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        )
        lines = subprocess.check_output(
            ["git", "ls-files", "--", str(root.resolve())],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    root = root.resolve()
    paths: list[Path] = []
    for line in lines:
        path = (repo_root / line).resolve()
        if (
            path.is_file()
            and _is_relative_to(path, root)
            and path.suffix.lower() in SCAN_SUFFIXES
            and any(part in SCAN_ROOT_PARTS for part in path.relative_to(root).parts)
            and not any(part in IGNORED_PARTS for part in path.parts)
        ):
            paths.append(path)
    return sorted(paths)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


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
