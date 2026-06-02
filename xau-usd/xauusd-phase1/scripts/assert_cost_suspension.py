from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_JSON = Path("outputs") / "reports" / "COST_SUSPENSION_ENFORCEMENT_REPORT.json"
DEFAULT_MD = Path("outputs") / "reports" / "COST_SUSPENSION_ENFORCEMENT_REPORT.md"
FAMILY = "breakout_retest_family"
SUSPENDED_STATE = "COST_SUSPENDED_CANONICAL"
SAME_FAMILY = (
    "breakout_retest",
    "swing_breakout_retest_v0",
    "symbol_normalized_round_retest_v0",
    "quarter_round_retest_v0",
    "session_extreme_retest_v0",
    "round_number_retest_v0",
)
AUTHORIZATION_TRUE_KEYS = (
    "paper_mode_authorized",
    "paper_mode_implementation_authorized",
    "demo_trading_authorized",
    "broker_execution_authorized",
    "broker_action_code_allowed",
    "live_trading_authorized",
    "live_trading_allowed",
)


@dataclass(frozen=True)
class CostSuspensionCheck:
    check: str
    status: str
    evidence: str


@dataclass(frozen=True)
class CostSuspensionOutput:
    status: str
    json_path: Path
    markdown_path: Path
    failed_count: int


def assert_cost_suspension(root: Path, output_json: Path | None = None) -> CostSuspensionOutput:
    root = root.resolve()
    repo_root = root.parents[1]
    phase0_root = root.parent / "xauusd-phase0"
    report_dir = root / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    checks = _checks(root, repo_root, phase0_root)
    failed = [check for check in checks if check.status != "PASS"]
    status = "PASS" if not failed else "FAIL"
    payload = {
        "status": status,
        "family": FAMILY,
        "required_state": SUSPENDED_STATE,
        "authority": (
            "This report enforces the cost-suspension boundary. It does not authorize Phase 2, "
            "demo execution, broker execution, or live capital."
        ),
        "checks": [check.__dict__ for check in checks],
        "failed_count": len(failed),
        "source_reports": {
            "phase2_readiness": str(report_dir / "PHASE2_READINESS_REPORT.md"),
            "phase2_demo_preflight": str(report_dir / "PHASE2_DEMO_PREFLIGHT.json"),
            "cost_revalidation": str(phase0_root / "outputs" / "reports" / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md"),
            "cost_assumption_delta": str(phase0_root / "outputs" / "reports" / "MEASURED_COST_ASSUMPTION_DELTA.md"),
            "cost_suspension_lock": str(root / "docs" / "COST_SUSPENSION_LOCK.md"),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return CostSuspensionOutput(status, output_json, output_md, len(failed))


def _checks(root: Path, repo_root: Path, phase0_root: Path) -> list[CostSuspensionCheck]:
    report_dir = root / "outputs" / "reports"
    phase0_reports = phase0_root / "outputs" / "reports"
    lock = root / "docs" / "COST_SUSPENSION_LOCK.md"
    lifecycle = root / "docs" / "EXPERT_LIFECYCLE.md"
    single_edge = root / "docs" / "PHASE2_SINGLE_EDGE_RISK_PLAN.md"
    readiness = report_dir / "PHASE2_READINESS_REPORT.md"
    owner_approval = report_dir / "PHASE2_OWNER_APPROVAL.md"
    cost_revalidation = phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md"
    assumption_delta = phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md"
    checks = [
        _file_contains("cost_suspension_lock_active", lock, (FAMILY, SUSPENDED_STATE, "measured-cost revalidation failed")),
        _same_family_lifecycle_check(lifecycle),
        _same_family_single_edge_check(single_edge),
        _readiness_cost_gate_check(readiness, cost_revalidation),
        _owner_approval_absent_check(owner_approval, cost_revalidation),
        _authorization_false_check(report_dir / "PHASE2_DEMO_PREFLIGHT.json"),
        _authorization_false_check(report_dir / "PHASE2_OWNER_ACTION_PACKET.json"),
        _authorization_false_check(report_dir / "PHASE2_DEMO_COUNTDOWN.json"),
        _authorization_false_check(report_dir / "PHASE2_VPS_BOOTSTRAP_PACKET.json"),
        _authorization_false_check(report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.json"),
        _phase3_authorization_false_check(repo_root / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports" / "PHASE3_EXPERIMENTAL_STATUS.json"),
        _measured_cost_status_check("measured_cost_revalidation_still_fail", cost_revalidation, expected="FAIL"),
        _measured_cost_status_check("measured_cost_assumption_delta_still_fail", assumption_delta, expected="FAIL"),
    ]
    return checks


def _file_contains(check: str, path: Path, tokens: tuple[str, ...]) -> CostSuspensionCheck:
    if not path.exists():
        return CostSuspensionCheck(check, "FAIL", f"Missing `{path}`.")
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    missing = [token for token in tokens if token.lower() not in lowered]
    if missing:
        return CostSuspensionCheck(check, "FAIL", "Missing token(s): " + ", ".join(missing))
    return CostSuspensionCheck(check, "PASS", f"`{path}` contains required lock language.")


def _same_family_lifecycle_check(path: Path) -> CostSuspensionCheck:
    if not path.exists():
        return CostSuspensionCheck("same_family_lifecycle_suspended", "FAIL", f"Missing `{path}`.")
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [
        expert
        for expert in SAME_FAMILY
        if f"| `{expert}` | `{SUSPENDED_STATE}` |" not in text
    ]
    if missing:
        return CostSuspensionCheck("same_family_lifecycle_suspended", "FAIL", "Missing suspended lifecycle row(s): " + ", ".join(missing))
    return CostSuspensionCheck("same_family_lifecycle_suspended", "PASS", "All same-family rows are cost-suspended.")


def _same_family_single_edge_check(path: Path) -> CostSuspensionCheck:
    if not path.exists():
        return CostSuspensionCheck("same_family_not_execution_eligible", "FAIL", f"Missing `{path}`.")
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [expert for expert in SAME_FAMILY if expert not in text]
    bad_tokens = [
        token for token in ("execution-eligible stream", "paper fills", "diversification")
        if token not in text
    ]
    if missing or bad_tokens:
        return CostSuspensionCheck(
            "same_family_not_execution_eligible",
            "FAIL",
            f"missing_experts={missing}; missing_boundary_tokens={bad_tokens}",
        )
    return CostSuspensionCheck("same_family_not_execution_eligible", "PASS", "Single-edge plan preserves same-family execution lock.")


def _readiness_cost_gate_check(readiness: Path, cost_revalidation: Path) -> CostSuspensionCheck:
    readiness_status = _read_markdown_status(readiness)
    cost_status = _read_markdown_status(cost_revalidation)
    if readiness_status == "PASS" and cost_status == "FAIL":
        return CostSuspensionCheck(
            "phase2_readiness_cannot_pass_when_cost_revalidation_fails",
            "FAIL",
            f"readiness={readiness_status}; cost_revalidation={cost_status}",
        )
    return CostSuspensionCheck(
        "phase2_readiness_cannot_pass_when_cost_revalidation_fails",
        "PASS",
        f"readiness={readiness_status or 'missing'}; cost_revalidation={cost_status or 'missing'}",
    )


def _owner_approval_absent_check(owner_approval: Path, cost_revalidation: Path) -> CostSuspensionCheck:
    cost_status = _read_markdown_status(cost_revalidation)
    if owner_approval.exists() and cost_status == "FAIL":
        return CostSuspensionCheck(
            "owner_approval_absent_while_cost_revalidation_fails",
            "FAIL",
            f"`{owner_approval}` exists while measured-cost revalidation is FAIL.",
        )
    return CostSuspensionCheck(
        "owner_approval_absent_while_cost_revalidation_fails",
        "PASS",
        f"owner_approval_exists={owner_approval.exists()}; cost_revalidation={cost_status or 'missing'}",
    )


def _authorization_false_check(path: Path) -> CostSuspensionCheck:
    if not path.exists():
        return CostSuspensionCheck(f"{path.name}_authorization_false", "PASS", f"`{path}` not present.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    true_fields = [key for key in AUTHORIZATION_TRUE_KEYS if payload.get(key) is True]
    if true_fields:
        return CostSuspensionCheck(f"{path.name}_authorization_false", "FAIL", "true authorization field(s): " + ", ".join(true_fields))
    return CostSuspensionCheck(f"{path.name}_authorization_false", "PASS", "No true paper/demo/broker/live authorization fields.")


def _phase3_authorization_false_check(path: Path) -> CostSuspensionCheck:
    if not path.exists():
        return CostSuspensionCheck("phase3_authorization_false", "PASS", f"`{path}` not present.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    true_fields = [
        key
        for key in ("authorized_for_deployment", "broker_action_code_allowed", "mt5_runtime_touched")
        if payload.get(key) is True
    ]
    if true_fields:
        return CostSuspensionCheck("phase3_authorization_false", "FAIL", "true Phase 3 field(s): " + ", ".join(true_fields))
    return CostSuspensionCheck("phase3_authorization_false", "PASS", "Phase 3 remains non-authorizing.")


def _measured_cost_status_check(check: str, path: Path, expected: str) -> CostSuspensionCheck:
    status = _read_markdown_status(path)
    if status != expected:
        return CostSuspensionCheck(check, "FAIL", f"`{path}` status is {status or 'missing'}; expected {expected}.")
    return CostSuspensionCheck(check, "PASS", f"`{path}` status is {status}.")


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _render_markdown(payload: dict[str, object]) -> str:
    checks = payload["checks"]
    assert isinstance(checks, list)
    lines = [
        "# Cost Suspension Enforcement Report",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["authority"]),
        "",
        f"Family: `{payload['family']}`",
        f"Required state: `{payload['required_state']}`",
        f"Failed checks: {payload['failed_count']}",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        assert isinstance(check, dict)
        lines.append(f"| {check['check']} | {check['status']} | {_escape(str(check['evidence']))} |")
    lines.extend(["", "## Boundary", "", "A PASS here preserves the measured-cost suspension. It does not authorize Phase 2.", ""])
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assert cost-suspension invariants for the breakout-retest family.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = assert_cost_suspension(args.root, args.output_json)
    print(f"Cost suspension enforcement: {output.status}")
    print(output.markdown_path)
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
