from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE3_PROXY_NON_AUTHORITATIVE_VERIFICATION.json"
DEFAULT_MD = Path("outputs") / "reports" / "PHASE3_PROXY_NON_AUTHORITATIVE_VERIFICATION.md"

FORBIDDEN_PROXY_AUTH_PATTERNS = (
    re.compile(r"\bPHASE2_READINESS_REPORT\s*=\s*PASS\b", re.IGNORECASE),
    re.compile(r"\bPHASE2_OWNER_APPROVAL\s*=\s*PASS\b", re.IGNORECASE),
    re.compile(r"\bcanonical_phase2_authorized\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bpaper_mode_execution_allowed\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bphase2_readiness_override\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bdemo_execution_as_phase2_evidence\s*[:=]\s*true\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    evidence: str


def verify_phase3_proxy_non_authoritative(root: Path, output_json: Path | None = None) -> int:
    root = root.resolve()
    repo_root = root.parents[1]
    phase3_reports = repo_root / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports"
    phase2_readiness = root / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md"
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    phase3_violations = _scan_phase3_reports(phase3_reports)
    readiness_status = _read_markdown_status(phase2_readiness)
    readiness_text = phase2_readiness.read_text(encoding="utf-8", errors="replace") if phase2_readiness.exists() else ""
    readiness_uses_phase3 = readiness_status == "PASS" and ("PHASE3" in readiness_text or "Phase 3" in readiness_text)
    checks = [
        Check(
            "phase3_reports_exist",
            "PASS" if phase3_reports.exists() else "WARN",
            f"phase3_reports={phase3_reports}",
        ),
        Check(
            "phase3_proxy_no_authorization_tokens",
            "PASS" if not phase3_violations else "FAIL",
            "No proxy authorization leakage found." if not phase3_violations else "; ".join(phase3_violations[:20]),
        ),
        Check(
            "phase2_readiness_not_passed_by_phase3_proxy",
            "PASS" if not readiness_uses_phase3 else "FAIL",
            f"PHASE2_READINESS_REPORT status={readiness_status or 'MISSING'}; uses_phase3={readiness_uses_phase3}",
        ),
    ]
    status = "PASS" if all(check.status != "FAIL" for check in checks) else "FAIL"
    payload = {
        "status": status,
        "created_at_utc": _now(),
        "phase2_readiness_status": readiness_status or "MISSING",
        "phase3_proxy_non_authoritative": True,
        "canonical_phase2_authorized": False,
        "paper_mode_execution_allowed": False,
        "violations": phase3_violations,
        "checks": [check.__dict__ for check in checks],
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render(status, checks), encoding="utf-8")
    return 0 if status == "PASS" else 1


def _scan_phase3_reports(path: Path) -> list[str]:
    if not path.exists():
        return []
    violations: list[str] = []
    for file_path in sorted(path.rglob("*")):
        if file_path.suffix.lower() not in {".md", ".json", ".csv", ".txt"}:
            continue
        text = file_path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _line_is_explicit_negative(line):
                continue
            for pattern in FORBIDDEN_PROXY_AUTH_PATTERNS:
                if pattern.search(line):
                    violations.append(f"{file_path}:{lineno}: {line.strip()[:180]}")
    return violations


def _line_is_explicit_negative(line: str) -> bool:
    lowered = line.lower()
    return (
        "false" in lowered
        or "no-go" in lowered
        or "not authorize" in lowered
        or "does not authorize" in lowered
        or "non-authoritative" in lowered
    )


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _render(status: str, checks: list[Check]) -> str:
    lines = [
        "# Phase 3 Proxy Non-Authoritative Verification",
        "",
        f"Overall status: {status}",
        "",
        "This validator ensures Phase 3 proxy reports cannot set Phase 2 readiness, owner approval, paper-mode execution, or canonical authorization.",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        lines.append(f"| {check.name} | {check.status} | {_escape(check.evidence)} |")
    lines.extend(["", "A PASS means proxy evidence remains research-only.", ""])
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Phase 3 proxy evidence remains non-authoritative.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    result = verify_phase3_proxy_non_authoritative(args.root, args.output_json)
    print("Phase 3 proxy non-authoritative verification: " + ("PASS" if result == 0 else "FAIL"))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
