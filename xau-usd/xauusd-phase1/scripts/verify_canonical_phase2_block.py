from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from generate_phase2_blocker_summary import generate_phase2_blocker_summary


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2_CANONICAL_BLOCK_VERIFICATION.json"
DEFAULT_MD = Path("outputs") / "reports" / "PHASE2_CANONICAL_BLOCK_VERIFICATION.md"


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    evidence: str


def verify_canonical_phase2_block(root: Path, output_json: Path | None = None) -> int:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)
    blocker = generate_phase2_blocker_summary(root)
    blocker_json = json.loads(blocker.json_path.read_text(encoding="utf-8"))
    readiness_status = _read_markdown_status(reports / "PHASE2_READINESS_REPORT.md")
    checks = [
        Check(
            "canonical_phase2_blocked_by_measured_cost",
            "PASS" if blocker_json.get("canonical_phase2_status") == "BLOCKED_BY_MEASURED_COST" else "FAIL",
            f"canonical_phase2_status={blocker_json.get('canonical_phase2_status')}",
        ),
        Check(
            "phase2_readiness_not_pass",
            "PASS" if readiness_status != "PASS" else "FAIL",
            f"PHASE2_READINESS_REPORT status={readiness_status or 'MISSING'}",
        ),
        Check(
            "demo_not_phase2_evidence",
            "PASS" if blocker_json.get("demo_execution_as_phase2_evidence") is False else "FAIL",
            f"demo_execution_as_phase2_evidence={blocker_json.get('demo_execution_as_phase2_evidence')}",
        ),
        Check(
            "live_trading_not_authorized",
            "PASS" if blocker_json.get("live_trading_authorized") is False else "FAIL",
            f"live_trading_authorized={blocker_json.get('live_trading_authorized')}",
        ),
    ]
    status = "PASS" if all(check.status == "PASS" for check in checks) else "FAIL"
    payload = {"status": status, "checks": [check.__dict__ for check in checks]}
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render(status, checks), encoding="utf-8")
    return 0 if status == "PASS" else 1


def _render(status: str, checks: list[Check]) -> str:
    lines = [
        "# Canonical Phase 2 Block Verification",
        "",
        f"Overall status: {status}",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        lines.append(f"| {check.name} | {check.status} | {_escape(check.evidence)} |")
    lines.extend(["", "A PASS here means the canonical block is preserved, not that Phase 2 is approved.", ""])
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify canonical Phase 2 remains blocked by measured-cost failure.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    result = verify_canonical_phase2_block(args.root, args.output_json)
    print("Canonical Phase 2 block verification: " + ("PASS" if result == 0 else "FAIL"))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
