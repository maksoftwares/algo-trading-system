from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_JSON = Path("status_summary.json")
DEFAULT_MD = Path("status_summary.md")


def generate_project_status_summary(
    repo_root: Path,
    output_json: Path | None = None,
    output_md: Path | None = None,
    now: datetime | None = None,
) -> tuple[Path, Path]:
    repo_root = repo_root.resolve()
    output_json = (output_json or repo_root / DEFAULT_JSON).resolve()
    output_md = (output_md or repo_root / DEFAULT_MD).resolve()
    now = now or datetime.now(timezone.utc)

    phase1_root = repo_root / "xau-usd" / "xauusd-phase1"
    phase1_reports = phase1_root / "outputs" / "reports"
    quarantine_report = phase1_reports / "XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.json"
    a3_attachment_report = phase1_reports / "A3_TIER1_COMPAT_BROKER_ACTION_ATTACHMENT_2026_06_17.json"
    a3_review_followup_report = phase1_reports / "A3_REVIEW_FOLLOWUP_STATUS_2026_06_18.json"
    a3_pause_report = phase1_reports / "A3_EMERGENCY_PAUSE_APPLIED_2026_06_18.json"

    quarantine = _read_json(quarantine_report)
    a3_attachment = _read_json(a3_attachment_report)
    a3_review_followup = _read_json(a3_review_followup_report)
    a3_pause = _read_json(a3_pause_report)
    repo = _repo_state(repo_root)
    profile_backup = quarantine.get("terminal", {}).get("profile_backup_dir", "")
    historical_a3_authorization = _a3_historical_owner_authorization(a3_attachment)
    current_a3_runtime = _a3_current_runtime_state(a3_review_followup, a3_pause)
    effective_a3_authorization = current_a3_runtime.get("effective_runtime_authorization", "MISSING")
    a3_artifact_integrity = a3_review_followup.get("artifact_integrity_status", a3_pause.get("artifact_integrity_status", "MISSING"))
    a3_runtime_performance = a3_review_followup.get("runtime_performance_status", a3_pause.get("runtime_performance_status", "MISSING"))
    test_suite_status = _test_suite_status(phase1_reports)
    shadow_hypothesis_status = _shadow_hypothesis_status(phase1_root)

    target_charts = _chart_summary(quarantine.get("after_target_charts", quarantine.get("target_charts", [])))
    protected_charts = _chart_summary(quarantine.get("after_protected_charts", quarantine.get("protected_charts", [])))
    target_candidates = sorted(
        {
            str(item.get("candidate", ""))
            for item in quarantine.get("after_target_charts", quarantine.get("target_charts", []))
            if item.get("candidate")
        }
    ) or quarantine.get("scope", {}).get("target_candidates", [])
    protected_candidates = sorted(
        {
            str(item.get("candidate", ""))
            for item in quarantine.get("after_protected_charts", quarantine.get("protected_charts", []))
            if item.get("candidate")
        }
    ) or ["breakout_retest", "swing_breakout_retest_v0"]

    summary: dict[str, Any] = {
        "schema_version": "project_status_summary_v2",
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "repo": repo,
        "source_artifacts": {
            "status_html": "status.html",
            "status_summary_json": "status_summary.json",
            "status_summary_md": "status_summary.md",
            "round_quarantine_applied": _rel(repo_root, quarantine_report),
            "a3_tier1_attachment": _rel(repo_root, a3_attachment_report),
            "a3_governance_override": "xau-usd/xauusd-phase1/docs/A3_TIER1_COMPAT_GOVERNANCE_OVERRIDE_2026_06_17.md",
            "a3_review_followup": _rel(repo_root, a3_review_followup_report),
            "a3_emergency_pause": _rel(repo_root, a3_pause_report),
            "final_review_c9889cb": "FINAL_REVIEW_C9889CB_A3_FOLLOWUP_2026_06_18.md",
            "final_review_b7ea982": "FINAL_REVIEW_B7EA982_A3_REPAIR_IMPLEMENTATION_PLAN_2026_06_18.md",
            "final_review_response": "xau-usd/xauusd-phase1/outputs/reports/FINAL_REVIEW_D5DD2DE_RESPONSE_2026_06_18.md",
            "phase1_test_failure_triage": "xau-usd/xauusd-phase1/outputs/reports/PHASE1_TEST_FAILURE_TRIAGE_2026_06_18.md",
            "phase1_test_failure_closure": "xau-usd/xauusd-phase1/outputs/reports/PHASE1_TEST_FAILURE_CLOSURE_2026_06_18.md",
        },
        "accounts": {
            "A1": {
                "login": "1025742",
                "server": "Capital.ComMena-Demo",
                "role": "standard/noisy demo account",
                "round_quarantine_active": _is_quarantine_active(target_charts),
                "touched_by_round_quarantine": True,
                "target_charts": target_charts,
                "protected_charts": protected_charts,
            },
            "A2": {
                "login": "1033030",
                "server": "Capital.ComMena-Demo",
                "role": "Tier-1 clean breakout account",
                "round_quarantine_active": False,
                "touched_by_round_quarantine": False,
            },
            "A3": {
                "login": "1033669",
                "server": "Capital.ComMena-Demo",
                "role": "repair / Tier-1 compatibility demo account",
                "round_quarantine_active": False,
                "touched_by_round_quarantine": False,
                "historical_owner_authorization": historical_a3_authorization,
                "current_runtime_state": current_a3_runtime,
                "effective_runtime_authorization": effective_a3_authorization,
                "tier1_compat_demo_broker_action": historical_a3_authorization["933400_demo_broker_action"],
                "tier1_compat_attachment_status": a3_attachment.get("status", "MISSING"),
                "review_followup_status": a3_review_followup.get("status", "MISSING"),
                "artifact_integrity_status": a3_artifact_integrity,
                "runtime_performance_status": a3_runtime_performance,
                "runtime_authorization_status": effective_a3_authorization,
                "review_followup_summary": a3_review_followup.get("summary", {}),
                "plain_933200_stopped": _a3_lane_paused(a3_review_followup, "933200"),
                "improved_933300_paused": _a3_lane_paused(a3_review_followup, "933300"),
                "tier1_933400_paused": _a3_lane_paused(a3_review_followup, "933400"),
                "profit_lock_dryrun_disarmed": _profit_lock_disarmed(a3_review_followup),
                "emergency_pause_status": a3_pause.get("status", "MISSING"),
                "emergency_pause_report": _rel(repo_root, a3_pause_report),
                "evidence_window_start_utc": a3_review_followup.get("window_start_utc", ""),
                "evidence_window_end_utc": a3_review_followup.get("window_end_utc", ""),
                "runtime_snapshot_at_utc": current_a3_runtime.get("verified_at_utc", ""),
                "artifact_generation_base_commit": repo.get("commit", ""),
                "artifact_commit_or_release_id": repo.get("commit", ""),
                "source_runtime_parity_status": _source_runtime_parity_status(a3_review_followup, a3_pause),
                "test_suite_status": test_suite_status,
                "family_mutex_status": "NOT_IMPLEMENTED",
                "containment_status": "NOT_IMPLEMENTED",
                "shadow_hypothesis_status": shadow_hypothesis_status,
                "reactivation_gate_status": "BLOCKED",
                "next_allowed_transition": "Shadow-only A3 signal-quality hypothesis registration; no broker action.",
            },
        },
        "quarantine": {
            "status": quarantine.get("status", "MISSING"),
            "scope": "A1 XAUUSD round-family only",
            "target_candidates": target_candidates,
            "target_charts": target_charts,
            "protected_candidates": protected_candidates,
            "protected_charts": protected_charts,
            "profile_backup_path": profile_backup,
            "rollback_backup_exists": bool(profile_backup),
            "keep_active_through_forward_week": True,
            "rollback_required_now": False,
        },
        "a3_tier1": {
            "status": a3_attachment.get("status", "MISSING"),
            "historical_owner_authorization": historical_a3_authorization,
            "owner_authorized_demo_broker_action": (
                historical_a3_authorization["933400_demo_broker_action"] == "OWNER_AUTHORIZED_DEMO_BROKER_ACTION"
            ),
            "governance_note": "Historical owner override is preserved as audit evidence only; current runtime authorization is paused.",
            "current_runtime_state": current_a3_runtime,
            "effective_runtime_authorization": effective_a3_authorization,
            "review_followup_summary": a3_review_followup.get("summary", {}),
            "runtime_authorization_status": effective_a3_authorization,
            "emergency_pause_status": a3_pause.get("status", "MISSING"),
            "family_mutex_status": "NOT_IMPLEMENTED",
            "containment_status": "NOT_IMPLEMENTED",
            "shadow_hypothesis_status": shadow_hypothesis_status,
            "reactivation_gate_status": "BLOCKED",
        },
        "authorization": {
            "canonical_phase2_pass": False,
            "live_trading_authorized": False,
            "real_capital_authorized": False,
            "broad_afternoon_ban_authorized": False,
            "direction_only_rule_authorized": False,
            "cost_threshold_runtime_rule_authorized": False,
            "a3_tier1_demo_broker_action": historical_a3_authorization["933400_demo_broker_action"],
            "a3_current_runtime_authorization": effective_a3_authorization,
            "a3_effective_runtime_authorization": effective_a3_authorization,
        },
        "next_evidence_required": [
            "XAUUSD_ROUND_FAMILY_FORWARD_WEEK_IMPACT_2026_06_xx.md",
            "XAUUSD_PROTECTED_BREAKOUT_CORE_FORWARD_WEEK_2026_06_xx.md",
            "XAUUSD_NON_ROUND_AFTERNOON_RESIDUAL_2026_06_xx.md",
            "A1/A2/A3 direct-history reconciliation after the forward week",
            "PHASE1_TEST_FAILURE_TRIAGE_2026_06_18.md review/cleanup",
            "A3_PER_MAGIC_ATTRIBUTION_2026_06_18.md reviewer follow-up",
            "A3 shadow-only signal-quality hypothesis with account-wide family mutex before any reactivation",
        ],
    }

    output_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(_render_markdown(summary), encoding="utf-8")
    return output_json, output_md


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _repo_state(repo_root: Path) -> dict[str, str]:
    return {
        "branch": _git(repo_root, "branch", "--show-current"),
        "commit": _git(repo_root, "rev-parse", "HEAD"),
        "main_remote_commit": _git(repo_root, "ls-remote", "origin", "refs/heads/main").split()[0]
        if _git(repo_root, "ls-remote", "origin", "refs/heads/main")
        else "",
    }


def _git(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo_root, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _chart_summary(charts: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for chart in charts:
        output.append(
            {
                "chart": str(chart.get("chart", "")),
                "symbol": str(chart.get("symbol", "")),
                "candidate": str(chart.get("candidate", "")),
                "dry_run": str(chart.get("dry_run", chart.get("dry_run_only", ""))).lower(),
                "broker_action_allowed": str(chart.get("broker_action_allowed", "")).lower(),
                "candidate_status": str(chart.get("candidate_status", "")),
            }
        )
    return output


def _is_quarantine_active(charts: list[dict[str, str]]) -> bool:
    return bool(charts) and all(
        chart.get("dry_run") == "true" and chart.get("broker_action_allowed") == "false" for chart in charts
    )


def _a3_broker_action_status(report: dict[str, Any]) -> str:
    lane = report.get("lane", {})
    if (
        str(report.get("status", "")).upper() == "PASS"
        and str(lane.get("account_login", "")) == "1033669"
        and str(lane.get("broker_action_allowed", "")).lower() == "true"
        and str(lane.get("dry_run", "")).lower() == "false"
    ):
        return "OWNER_AUTHORIZED_DEMO_BROKER_ACTION"
    return "PENDING_OR_NOT_VISIBLE"


def _a3_historical_owner_authorization(report: dict[str, Any]) -> dict[str, Any]:
    lane = report.get("lane", {})
    return {
        "933400_demo_broker_action": _a3_broker_action_status(report),
        "authorized_at_source": "A3_TIER1_COMPAT_BROKER_ACTION_OWNER_AUTHORIZATION_2026_06_17.md",
        "attachment_status": report.get("status", "MISSING"),
        "lane": {
            "magic": str(lane.get("magic", "")),
            "symbol": str(lane.get("symbol", "")),
            "dry_run_at_attachment": str(lane.get("dry_run", "")).lower(),
            "broker_action_allowed_at_attachment": str(lane.get("broker_action_allowed", "")).lower(),
            "fixed_lot": str(lane.get("fixed_lot", "")),
        },
        "current_permission": "SUPERSEDED_BY_EMERGENCY_PAUSE",
    }


def _a3_current_runtime_state(review: dict[str, Any], pause: dict[str, Any]) -> dict[str, Any]:
    after_broker = _mapping(pause.get("after_broker"))
    return {
        "effective_runtime_authorization": review.get(
            "runtime_authorization_status",
            pause.get("runtime_authorization_status", "MISSING"),
        ),
        "verified_at_utc": review.get("created_at_utc", pause.get("created_at_utc", "")),
        "open_positions": _to_int(after_broker.get("a3_positions_total")) or 0,
        "pending_orders": _to_int(after_broker.get("a3_orders_total")) or 0,
        "lanes": {
            "933200": _a3_lane_runtime_state(review, "933200"),
            "933300": _a3_lane_runtime_state(review, "933300"),
            "933400": _a3_lane_runtime_state(review, "933400"),
            "profit_lock": _profit_lock_runtime_state(review),
        },
    }


def _a3_lane_runtime_state(report: dict[str, Any], magic: str) -> str:
    for row in report.get("per_magic", []):
        if str(row.get("magic", "")) != magic:
            continue
        dry_run = str(row.get("dry_run_now", "")).lower()
        broker_action = str(row.get("broker_action_allowed_now", "")).lower()
        if dry_run == "true" and broker_action == "false":
            return "PAUSED"
        if dry_run == "false" and broker_action == "true":
            return "BROKER_ACTION_ENABLED"
        return f"UNKNOWN_DRY_RUN_{dry_run}_BROKER_{broker_action}"
    return "MISSING"


def _profit_lock_runtime_state(report: dict[str, Any]) -> str:
    for row in report.get("chart_state", {}).values():
        if row.get("expert") != "Account3ProfitLockExitManager":
            continue
        dry_run = str(row.get("dry_run", "")).lower()
        manage_action = str(row.get("manage_action_allowed", "")).lower()
        if dry_run == "true" and manage_action == "false":
            return "DRY_RUN_DISARMED"
        if dry_run == "false" and manage_action == "true":
            return "ARMED"
        return f"UNKNOWN_DRY_RUN_{dry_run}_MANAGE_{manage_action}"
    return "MISSING"


def _a3_lane_paused(report: dict[str, Any], magic: str) -> bool:
    for row in report.get("per_magic", []):
        if str(row.get("magic", "")) == magic:
            return str(row.get("dry_run_now", "")).lower() == "true" and str(row.get("broker_action_allowed_now", "")).lower() == "false"
    return False


def _profit_lock_disarmed(report: dict[str, Any]) -> bool:
    for row in report.get("chart_state", {}).values():
        if row.get("expert") == "Account3ProfitLockExitManager":
            return str(row.get("dry_run", "")).lower() == "true" and str(row.get("manage_action_allowed", "")).lower() == "false"
    return False


def _test_suite_status(report_dir: Path) -> dict[str, Any]:
    closure = report_dir / "PHASE1_TEST_FAILURE_CLOSURE_2026_06_18.md"
    if not closure.exists():
        return {"status": "UNKNOWN", "passed": None, "failed": None, "source": ""}
    text = closure.read_text(encoding="utf-8", errors="replace")
    passed = None
    failed = None
    for line in text.splitlines():
        if "passed" in line and "failed" in line:
            parts = line.replace("`", "").replace(",", "").split()
            for index, part in enumerate(parts):
                if part == "passed" and index > 0:
                    passed = _to_int(parts[index - 1])
                if part == "failed" and index > 0:
                    failed = _to_int(parts[index - 1])
            if passed is not None and failed is not None:
                break
    status = "PASS" if failed == 0 and passed else "FAIL" if failed else "UNKNOWN"
    return {
        "status": status,
        "passed": passed,
        "failed": failed,
        "source": "xau-usd/xauusd-phase1/outputs/reports/PHASE1_TEST_FAILURE_CLOSURE_2026_06_18.md",
    }


def _shadow_hypothesis_status(phase1_root: Path) -> str:
    doc = phase1_root / "docs" / "A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md"
    manifest = phase1_root / "outputs" / "manifests" / "A3_SIGNAL_QUALITY_HYPOTHESES_V1.sha256.json"
    if doc.exists() and manifest.exists():
        return "REGISTERED_LOCKED"
    return "NOT_REGISTERED"


def _source_runtime_parity_status(review: dict[str, Any], pause: dict[str, Any]) -> str:
    if review.get("artifact_integrity_status") == "PASS" and pause.get("status") == "PASS":
        return "PASS"
    if not review and not pause:
        return "MISSING"
    return "REVIEW_REQUIRED"


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _rel(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _render_markdown(summary: dict[str, Any]) -> str:
    accounts = summary["accounts"]
    quarantine = summary["quarantine"]
    auth = summary["authorization"]
    lines = [
        "# Project Status Summary",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        f"Artifact generation base commit: `{summary['repo']['commit']}`",
        f"Branch: `{summary['repo']['branch']}`",
        "",
        "This small file is the audit-friendly companion to the large `status.html` dashboard.",
        "",
        "## Accounts",
        "",
        "| Account | Login | Role | Round quarantine active | Touched by round quarantine |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for key, account in accounts.items():
        lines.append(
            f"| {key} | `{account['login']}` | {account['role']} | "
            f"`{str(account['round_quarantine_active']).lower()}` | "
            f"`{str(account['touched_by_round_quarantine']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## A1 Round-Family Quarantine",
            "",
            f"Status: `{quarantine['status']}`",
            f"Scope: `{quarantine['scope']}`",
            f"Keep active through forward week: `{str(quarantine['keep_active_through_forward_week']).lower()}`",
            f"Rollback required now: `{str(quarantine['rollback_required_now']).lower()}`",
            "",
            "| Chart | Candidate | Dry run | Broker action | Status |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for chart in quarantine["target_charts"]:
        lines.append(
            f"| `{chart['chart']}` | `{chart['candidate']}` | `{chart['dry_run']}` | "
            f"`{chart['broker_action_allowed']}` | `{chart['candidate_status']}` |"
        )
    lines.extend(
        [
            "",
            "## Protected Breakout Core",
            "",
            "| Chart | Candidate | Dry run | Broker action | Status |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for chart in quarantine["protected_charts"]:
        lines.append(
            f"| `{chart['chart']}` | `{chart['candidate']}` | `{chart['dry_run']}` | "
            f"`{chart['broker_action_allowed']}` | `{chart['candidate_status']}` |"
        )
    a3 = accounts["A3"]
    a3_summary = a3.get("review_followup_summary", {})
    runtime_state = a3.get("current_runtime_state", {})
    runtime_lanes = runtime_state.get("lanes", {}) if isinstance(runtime_state, dict) else {}
    historical_authorization = a3.get("historical_owner_authorization", {})
    test_suite = a3.get("test_suite_status", {})
    lines.extend(
        [
            "",
            "## A3 Runtime Decision",
            "",
            f"Effective runtime authorization: `{a3.get('effective_runtime_authorization', 'MISSING')}`",
            f"Runtime snapshot UTC: `{a3.get('runtime_snapshot_at_utc', 'MISSING')}`",
            f"Open positions: `{runtime_state.get('open_positions', 'n/a') if isinstance(runtime_state, dict) else 'n/a'}`",
            f"Pending orders: `{runtime_state.get('pending_orders', 'n/a') if isinstance(runtime_state, dict) else 'n/a'}`",
            f"Artifact integrity: `{a3.get('artifact_integrity_status', 'MISSING')}`",
            f"Runtime performance: `{a3.get('runtime_performance_status', 'MISSING')}`",
            f"Emergency pause report: `{a3.get('emergency_pause_status', 'MISSING')}`",
            f"Test suite: `{test_suite.get('status', 'UNKNOWN')}` ({test_suite.get('passed', 'n/a')} passed, {test_suite.get('failed', 'n/a')} failed)",
            f"Family mutex: `{a3.get('family_mutex_status', 'MISSING')}`",
            f"Containment: `{a3.get('containment_status', 'MISSING')}`",
            f"Shadow hypothesis: `{a3.get('shadow_hypothesis_status', 'MISSING')}`",
            f"Reactivation gate: `{a3.get('reactivation_gate_status', 'MISSING')}`",
            "",
            "| Runtime lane | Current state |",
            "| --- | --- |",
            f"| `933200` plain | `{runtime_lanes.get('933200', 'MISSING')}` |",
            f"| `933300` improved | `{runtime_lanes.get('933300', 'MISSING')}` |",
            f"| `933400` Tier1 compat | `{runtime_lanes.get('933400', 'MISSING')}` |",
            f"| Profit-lock manager | `{runtime_lanes.get('profit_lock', 'MISSING')}` |",
            "",
            "## A3 Historical Authorization",
            "",
            f"Tier1 `933400` owner authorization: `{historical_authorization.get('933400_demo_broker_action', 'MISSING')}`",
            f"Current permission of that authorization: `{historical_authorization.get('current_permission', 'MISSING')}`",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Closed trades | `{a3_summary.get('closed_trades', 'n/a')}` |",
            f"| Wins | `{a3_summary.get('wins', 'n/a')}` |",
            f"| Losses | `{a3_summary.get('losses', 'n/a')}` |",
            f"| Net PnL AED | `{a3_summary.get('net_pnl_aed', 'n/a')}` |",
            f"| Duplicate events | `{a3_summary.get('duplicate_event_count', 'n/a')}` |",
            f"| Profit-lock actions | `{a3_summary.get('profit_lock_actions', 'n/a')}` |",
        ]
    )
    lines.extend(
        [
            "",
            "## Authorization Boundary",
            "",
            "| Item | Value |",
            "| --- | --- |",
            f"| Canonical Phase 2 PASS | `{str(auth['canonical_phase2_pass']).lower()}` |",
            f"| Live trading authorized | `{str(auth['live_trading_authorized']).lower()}` |",
            f"| Real capital authorized | `{str(auth['real_capital_authorized']).lower()}` |",
            f"| A3 Tier-1 demo broker action | `{auth['a3_tier1_demo_broker_action']}` |",
            f"| A3 current runtime authorization | `{auth['a3_current_runtime_authorization']}` |",
            "",
            "## Next Evidence Required",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["next_evidence_required"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a small audit-friendly project status summary.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    args = parser.parse_args(argv)
    json_path, md_path = generate_project_status_summary(args.repo_root, args.output_json, args.output_md)
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
