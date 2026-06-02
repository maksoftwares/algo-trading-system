from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_JSON = Path("outputs") / "reports" / "EXPERIMENTAL_DEMO_QUARANTINE_VERIFICATION.json"
DEFAULT_MD = Path("outputs") / "reports" / "EXPERIMENTAL_DEMO_QUARANTINE_VERIFICATION.md"


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    evidence: str


def verify_experimental_quarantine(root: Path, output_json: Path | None = None) -> int:
    root = root.resolve()
    source = root / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5"
    reports = root / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    checks = [
        _source_default_check(text, "InpCandidateStatus", "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY"),
        _source_default_check(text, "InpFamilyLifecycleStatus", "COST_SUSPENDED_CANONICAL"),
        _source_default_check(text, "InpCostSuspensionAcknowledgementToken", ""),
        _token_check(text, "experimental_quarantine"),
        _token_check(text, "canonical_phase2_evidence"),
        _token_check(text, "phase2_readiness_override"),
        _json_status_check(reports / "EXPERIMENTAL_DEMO_EXECUTOR_SOURCE_GOVERNANCE_PARITY.json", "PASS"),
        _json_status_check(reports / "BROKER_ACTION_FILE_BOUNDARY_AUDIT.json", "PASS"),
    ]
    status = "PASS" if all(check.status == "PASS" for check in checks) else "FAIL"
    payload = {"status": status, "checks": [check.__dict__ for check in checks]}
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render(status, checks), encoding="utf-8")
    return 0 if status == "PASS" else 1


def _source_default_check(text: str, name: str, expected: str) -> Check:
    match = re.search(rf"input\s+string\s+{re.escape(name)}\s*=\s*\"([^\"]*)\"", text)
    if not match:
        return Check(f"{name}_default", "FAIL", "Input not found.")
    actual = match.group(1)
    return Check(
        f"{name}_default",
        "PASS" if actual == expected else "FAIL",
        f"actual={actual!r}; expected={expected!r}",
    )


def _token_check(text: str, token: str) -> Check:
    return Check(
        f"{token}_logged",
        "PASS" if token in text else "FAIL",
        f"token_present={token in text}",
    )


def _json_status_check(path: Path, expected: str) -> Check:
    if not path.exists():
        return Check(path.name, "FAIL", f"Missing {path}.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    actual = payload.get("status")
    return Check(path.name, "PASS" if actual == expected else "FAIL", f"status={actual}; expected={expected}")


def _render(status: str, checks: list[Check]) -> str:
    lines = [
        "# Experimental Demo Quarantine Verification",
        "",
        f"Overall status: {status}",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        lines.append(f"| {check.name} | {check.status} | {_escape(check.evidence)} |")
    lines.extend(
        [
            "",
            "A PASS here confirms only that the experimental executor remains quarantined and non-authoritative.",
            "It does not authorize canonical Phase 2, demo execution as Phase 2 evidence, broker execution, or live capital.",
            "",
        ]
    )
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the experimental demo executor quarantine boundary.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    result = verify_experimental_quarantine(args.root, args.output_json)
    print("Experimental quarantine verification: " + ("PASS" if result == 0 else "FAIL"))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
