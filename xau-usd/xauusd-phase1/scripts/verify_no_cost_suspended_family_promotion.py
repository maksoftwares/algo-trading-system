from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_phase2_blocker_summary import generate_phase2_blocker_summary


DEFAULT_JSON = Path("outputs") / "reports" / "COST_SUSPENDED_PROMOTION_BLOCKER_REPORT.json"
DEFAULT_MD = Path("outputs") / "reports" / "COST_SUSPENDED_PROMOTION_BLOCKER_REPORT.md"

TRUE_FIELD_PATTERNS = (
    re.compile(r"\bcanonical_phase2_authorized\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bcanonical_phase2_evidence\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bphase2_readiness_override\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bdemo_execution_as_phase2_evidence\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bpaper_mode_execution_allowed\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\blive_execution_allowed\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\blive_trading_authorized\s*[:=]\s*true\b", re.IGNORECASE),
)

PROMOTION_PATTERNS = (
    re.compile(r"COST_SUSPENDED_CANONICAL.{0,120}\bexecution eligible\b", re.IGNORECASE),
    re.compile(r"COST_SUSPENDED_CANONICAL.{0,120}\bpaper[- ]mode approved\b", re.IGNORECASE),
    re.compile(r"COST_SUSPENDED_CANONICAL.{0,120}\bdemo evidence approved\b", re.IGNORECASE),
    re.compile(r"COST_SUSPENDED_CANONICAL.{0,120}\blive approved\b", re.IGNORECASE),
    re.compile(r"COST_SUSPENDED_CANONICAL.{0,120}\bdiversification eligible\b", re.IGNORECASE),
)

SCAN_EXTENSIONS = {".md", ".json", ".csv", ".html", ".set", ".ini", ".txt"}
SCAN_DIRS = ("docs", "outputs/reports", "mt5/Presets")


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    evidence: str


def verify_no_cost_suspended_family_promotion(root: Path, output_json: Path | None = None) -> int:
    root = root.resolve()
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    blocker = generate_phase2_blocker_summary(root)
    blocker_payload = json.loads(blocker.json_path.read_text(encoding="utf-8"))
    violations = _scan_for_violations(root)
    checks = [
        _field_check(
            "canonical_phase2_status",
            blocker_payload.get("canonical_phase2_status") == "BLOCKED_BY_MEASURED_COST",
            f"canonical_phase2_status={blocker_payload.get('canonical_phase2_status')}",
        ),
        _field_check(
            "family_cost_suspended",
            blocker_payload.get("breakout_retest_family_status") == "COST_SUSPENDED_CANONICAL",
            f"breakout_retest_family_status={blocker_payload.get('breakout_retest_family_status')}",
        ),
        _field_check(
            "paper_mode_execution_not_allowed",
            blocker_payload.get("paper_mode_execution_allowed") is False,
            f"paper_mode_execution_allowed={blocker_payload.get('paper_mode_execution_allowed')}",
        ),
        _field_check(
            "demo_not_phase2_evidence",
            blocker_payload.get("demo_execution_as_phase2_evidence") is False,
            f"demo_execution_as_phase2_evidence={blocker_payload.get('demo_execution_as_phase2_evidence')}",
        ),
        _field_check(
            "live_trading_not_authorized",
            blocker_payload.get("live_trading_authorized") is False,
            f"live_trading_authorized={blocker_payload.get('live_trading_authorized')}",
        ),
        Check(
            "promotion_scan",
            "PASS" if not violations else "FAIL",
            "No positive promotion leakage found." if not violations else "; ".join(violations[:20]),
        ),
    ]
    status = "PASS" if all(check.status == "PASS" for check in checks) else "FAIL"
    payload = {
        "status": status,
        "created_at_utc": _now(),
        "checks": [check.__dict__ for check in checks],
        "violations": violations,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render(status, checks), encoding="utf-8")
    return 0 if status == "PASS" else 1


def _scan_for_violations(root: Path) -> list[str]:
    repo_root = root.parents[1]
    candidates: list[Path] = []
    for relative in SCAN_DIRS:
        directory = root / relative
        if directory.exists():
            candidates.extend(path for path in directory.rglob("*") if path.suffix.lower() in SCAN_EXTENSIONS)
    for name in ("status.html", "demo-observer-dashboard.html"):
        path = repo_root / name
        if path.exists():
            candidates.append(path)

    violations: list[str] = []
    for path in sorted(set(candidates)):
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            normalized = line.strip()
            if _line_is_allowed_quarantine_context(normalized):
                continue
            for pattern in TRUE_FIELD_PATTERNS:
                if pattern.search(normalized):
                    violations.append(f"{path}:{lineno}: {normalized[:180]}")
            for pattern in PROMOTION_PATTERNS:
                if pattern.search(normalized):
                    violations.append(f"{path}:{lineno}: {normalized[:180]}")
    return violations


def _line_is_allowed_quarantine_context(line: str) -> bool:
    lowered = line.lower()
    if "experimental" in lowered and "quarantine" in lowered:
        return True
    if "canonical_phase2_evidence=false" in lowered or "phase2_readiness_override=false" in lowered:
        return True
    if "canonical phase 2 authorized" in lowered and "false" in lowered:
        return True
    return False


def _field_check(name: str, condition: bool, evidence: str) -> Check:
    return Check(name, "PASS" if condition else "FAIL", evidence)


def _render(status: str, checks: list[Check]) -> str:
    lines = [
        "# Cost-Suspended Family Promotion Blocker Report",
        "",
        f"Overall status: {status}",
        "",
        "This validator fails if cost-suspended breakout-retest family evidence leaks into execution eligibility, paper-mode approval, demo-evidence approval, live approval, or diversification eligibility.",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        lines.append(f"| {check.name} | {check.status} | {_escape(check.evidence)} |")
    lines.extend(["", "A PASS preserves the block. It does not approve Phase 2.", ""])
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify cost-suspended families are not promoted.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    result = verify_no_cost_suspended_family_promotion(args.root, args.output_json)
    print("Cost-suspended family promotion blocker: " + ("PASS" if result == 0 else "FAIL"))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
