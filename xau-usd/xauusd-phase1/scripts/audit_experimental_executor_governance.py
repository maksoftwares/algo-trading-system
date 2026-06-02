from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


EA_PATH = Path("mt5") / "Experts" / "Phase2ExperimentalDemoExecutor.mq5"
GOVERNANCE_DOC = Path("docs") / "EXPERIMENTAL_DEMO_EXECUTOR_GOVERNANCE.md"
DEFAULT_JSON = Path("outputs") / "reports" / "EXPERIMENTAL_DEMO_EXECUTOR_SOURCE_GOVERNANCE_PARITY.json"
DEFAULT_MD = Path("outputs") / "reports" / "EXPERIMENTAL_DEMO_EXECUTOR_SOURCE_GOVERNANCE_PARITY.md"


@dataclass(frozen=True)
class GovernanceCheck:
    check: str
    status: str
    evidence: str


@dataclass(frozen=True)
class GovernanceAuditOutput:
    status: str
    json_path: Path
    markdown_path: Path
    failed_count: int


def audit_experimental_executor_governance(root: Path, output_json: Path | None = None) -> GovernanceAuditOutput:
    root = root.resolve()
    source_path = root / EA_PATH
    doc_path = root / GOVERNANCE_DOC
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_JSON.name else root / DEFAULT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    source = _read(source_path)
    governance = _read(doc_path)
    checks = _checks(root, source, governance)
    failed = [check for check in checks if check.status != "PASS"]
    status = "PASS" if not failed else "FAIL"
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": str(source_path),
        "governance_doc": str(doc_path),
        "repo_commit_hash": _git_commit(root),
        "source_file_sha256": _sha256(source_path),
        "governance_doc_sha256": _sha256(doc_path),
        "input_declaration_block": _input_declaration_block(source),
        "authority": (
            "This audit checks experimental demo executor source/governance parity only. "
            "It does not authorize canonical Phase 2, demo execution, broker execution, or live capital."
        ),
        "checks": [check.__dict__ for check in checks],
        "failed_count": len(failed),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return GovernanceAuditOutput(status, output_json, output_md, len(failed))


def _checks(root: Path, source: str, governance: str) -> list[GovernanceCheck]:
    return [
        _source_is_tracked_check(root),
        _source_contains("non_canonical_banner", source, "NON_CANONICAL / EXPERIMENTAL DEMO ONLY / DO NOT DEPLOY AS PHASE2"),
        _contains_both("account_login_whitelist_input", governance, source, "InpAllowedAccountLoginsCsv"),
        _contains_both("experimental_authorization_token_input", governance, source, "InpExperimentalAuthorizationToken"),
        _contains_both("cost_suspension_acknowledgement_token_input", governance, source, "InpCostSuspensionAcknowledgementToken"),
        _input_default_check("candidate_status_default_quarantined", source, "InpCandidateStatus", {"EXPERIMENTAL_QUARANTINE_REVIEW_ONLY"}),
        _input_default_check("family_lifecycle_default_cost_suspended", source, "InpFamilyLifecycleStatus", {"COST_SUSPENDED_CANONICAL"}),
        _contains_both("candidate_runtime_allowlist_input", governance, source, "InpAuthorizedCandidatesCsv"),
        _contains_both("account_daily_order_cap_input", governance, source, "InpMaxAccountOrdersPerDay"),
        _contains_both("account_open_exposure_cap_input", governance, source, "InpMaxAccountOpenPositions"),
        _contains_both("kill_switch_input", governance, source, "InpKillSwitchFileName"),
        _source_contains("globalvariable_account_counter_logic", source, "GlobalVariableSet", "AccountOrdersToday", "IncrementAccountOrdersToday"),
        _source_contains("account_level_exposure_counter_logic", source, "CountOpenExposureForAccount", "IsExperimentalMagic", "PositionsTotal", "OrdersTotal"),
        _source_contains("kill_switch_file_read_logic", source, "KillSwitchActive", "FileOpen", "KILL"),
        _source_contains("candidate_authorization_guard", source, "CandidateExecutionAuthorized", "candidate_not_explicitly_authorized"),
        _source_contains("startup_refuses_blank_or_invalid_token", source, "ExperimentalAuthorizationTokenValid", "valid experimental authorization token"),
        _source_contains("startup_refuses_missing_cost_suspension_ack", source, "CostSuspensionAcknowledgementTokenValid", "cost-suspension acknowledgement token"),
        _source_contains("startup_refuses_unlisted_account", source, "AccountLoginWhitelisted", "not in InpAllowedAccountLoginsCsv"),
        _source_contains("startup_refuses_unauthorized_candidate", source, "CandidateExecutionAuthorized", "not explicitly authorized"),
        _source_contains("startup_refuses_kill_switch", source, "KillSwitchActive", "kill switch is active"),
        _source_contains("no_live_real_server_allowed", source, 'ContainsText(server, "live")', 'ContainsText(server, "real")'),
        _source_contains("cost_r_pre_order_guard", source, "InpMaxEstimatedCostR", "estimated_cost_r_exceeds_threshold", "EstimatedCostRForObservation"),
        _source_contains("spread_pre_order_guard", source, "InpMaxMeasuredSpreadPoints", "measured_spread_points_exceeds_threshold", "CurrentSpreadPoints"),
        _source_contains("order_log_account_order_count", source, "account_orders_today", "AccountOrdersToday()"),
        _source_contains("order_log_account_open_exposure", source, "account_open_exposure", "CountOpenExposureForAccount()"),
        _source_contains("order_log_family_lifecycle_status", source, "family_lifecycle_status", "InpFamilyLifecycleStatus"),
        _source_contains(
            "order_log_non_authoritative_flags",
            source,
            "experimental_quarantine",
            "canonical_phase2_evidence",
            "phase2_readiness_override",
            "candidate_family_status",
        ),
        _source_contains("order_guard_cost_suspension_ack", source, "cost_suspension_acknowledgement_token_missing_or_invalid"),
        _source_contains("order_log_estimated_cost_r", source, "estimated_cost_R", "estimated_cost_r"),
        _source_contains("order_log_mode_truthfulness", source, "order_mode", "MARKET_PROXY"),
        _source_contains("experimental_magic_namespace", source, "magic >= 920000", "magic < 921000"),
        _fixed_lot_check(source),
    ]


def _contains_both(name: str, governance: str, source: str, token: str) -> GovernanceCheck:
    doc_has = token in governance
    source_has = token in source
    status = "PASS" if doc_has and source_has else "FAIL"
    return GovernanceCheck(name, status, f"doc_has={doc_has}; source_has={source_has}; token={token}")


def _source_contains(name: str, source: str, *tokens: str) -> GovernanceCheck:
    missing = [token for token in tokens if token not in source]
    status = "PASS" if not missing else "FAIL"
    evidence = "all required source tokens present" if not missing else "missing: " + ", ".join(missing)
    return GovernanceCheck(name, status, evidence)


def _input_default_check(name: str, source: str, input_name: str, allowed_values: set[str]) -> GovernanceCheck:
    pattern = rf"input\s+string\s+{re.escape(input_name)}\s*=\s*\"([^\"]*)\""
    match = re.search(pattern, source)
    if not match:
        return GovernanceCheck(name, "FAIL", f"{input_name} default not found.")
    value = match.group(1)
    status = "PASS" if value in allowed_values else "FAIL"
    return GovernanceCheck(name, status, f"{input_name}={value}; allowed={','.join(sorted(allowed_values))}")


def _fixed_lot_check(source: str) -> GovernanceCheck:
    match = re.search(r"input\s+double\s+InpFixedLot\s*=\s*([0-9.]+)", source)
    if not match:
        return GovernanceCheck("fixed_lot_default_lte_0_01", "FAIL", "InpFixedLot default not found.")
    value = float(match.group(1))
    status = "PASS" if value <= 0.01 else "FAIL"
    return GovernanceCheck("fixed_lot_default_lte_0_01", status, f"InpFixedLot={value:.2f}")


def _source_is_tracked_check(root: Path) -> GovernanceCheck:
    rel = EA_PATH.as_posix()
    try:
        completed = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return GovernanceCheck("source_file_tracked_by_git", "FAIL", f"git unavailable: {exc}")
    if completed.returncode == 0:
        return GovernanceCheck("source_file_tracked_by_git", "PASS", f"tracked path: {rel}")
    return GovernanceCheck("source_file_tracked_by_git", "FAIL", f"source path is not tracked by git: {rel}")


def _render_markdown(payload: dict[str, object]) -> str:
    checks = payload["checks"]
    assert isinstance(checks, list)
    lines = [
        "# Experimental Demo Executor Source/Governance Parity",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["authority"]),
        "",
        f"Source: `{payload['source']}`",
        f"Governance doc: `{payload['governance_doc']}`",
        f"Repo commit hash: `{payload['repo_commit_hash']}`",
        f"Source SHA256: `{payload['source_file_sha256']}`",
        f"Governance doc SHA256: `{payload['governance_doc_sha256']}`",
        f"Failed checks: {payload['failed_count']}",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for check in checks:
        assert isinstance(check, dict)
        lines.append(f"| {check['check']} | {check['status']} | {_escape(str(check['evidence']))} |")
    lines.extend(
        [
            "",
            "## Input Declaration Block",
            "",
            "```mql5",
            str(payload["input_declaration_block"]).rstrip(),
            "```",
            "",
            "## Boundary",
            "",
            "A PASS here means the quarantined experimental executor source matches the documented guard set. It does not make the executor canonical Phase 2 evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _git_commit(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "UNKNOWN"
    if completed.returncode != 0:
        return "UNKNOWN"
    return completed.stdout.strip()


def _sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_declaration_block(source: str) -> str:
    lines = source.splitlines()
    input_lines = [f"{index}: {line}" for index, line in enumerate(lines, start=1) if line.strip().startswith("input ")]
    if input_lines:
        return "\n".join(input_lines[:80])
    return "\n".join(f"{index}: {line}" for index, line in enumerate(lines[:80], start=1))


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit experimental demo executor source/governance parity.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = audit_experimental_executor_governance(args.root, args.output_json)
    print(f"Experimental executor governance audit: {output.status}")
    print(output.markdown_path)
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
