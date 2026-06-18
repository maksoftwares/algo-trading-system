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

    phase1_reports = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    quarantine_report = phase1_reports / "XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.json"
    a3_attachment_report = phase1_reports / "A3_TIER1_COMPAT_BROKER_ACTION_ATTACHMENT_2026_06_17.json"

    quarantine = _read_json(quarantine_report)
    a3_attachment = _read_json(a3_attachment_report)
    repo = _repo_state(repo_root)
    profile_backup = quarantine.get("terminal", {}).get("profile_backup_dir", "")

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
        "schema_version": "project_status_summary_v1",
        "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "repo": repo,
        "source_artifacts": {
            "status_html": "status.html",
            "status_summary_json": "status_summary.json",
            "status_summary_md": "status_summary.md",
            "round_quarantine_applied": _rel(repo_root, quarantine_report),
            "a3_tier1_attachment": _rel(repo_root, a3_attachment_report),
            "a3_governance_override": "xau-usd/xauusd-phase1/docs/A3_TIER1_COMPAT_GOVERNANCE_OVERRIDE_2026_06_17.md",
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
                "tier1_compat_demo_broker_action": _a3_broker_action_status(a3_attachment),
                "tier1_compat_attachment_status": a3_attachment.get("status", "MISSING"),
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
            "owner_authorized_demo_broker_action": _a3_broker_action_status(a3_attachment) == "OWNER_AUTHORIZED_DEMO_BROKER_ACTION",
            "governance_note": "Owner explicitly overrode the reviewer observer-first recommendation for demo-only broker action.",
            "lane": a3_attachment.get("lane", {}),
        },
        "authorization": {
            "canonical_phase2_pass": False,
            "live_trading_authorized": False,
            "real_capital_authorized": False,
            "broad_afternoon_ban_authorized": False,
            "direction_only_rule_authorized": False,
            "cost_threshold_runtime_rule_authorized": False,
            "a3_tier1_demo_broker_action": _a3_broker_action_status(a3_attachment),
        },
        "next_evidence_required": [
            "XAUUSD_ROUND_FAMILY_FORWARD_WEEK_IMPACT_2026_06_xx.md",
            "XAUUSD_PROTECTED_BREAKOUT_CORE_FORWARD_WEEK_2026_06_xx.md",
            "XAUUSD_NON_ROUND_AFTERNOON_RESIDUAL_2026_06_xx.md",
            "A1/A2/A3 direct-history reconciliation after the forward week",
            "A3 Tier-1 compat order delta, PnL, and shadow trend-guard report",
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
        f"Commit: `{summary['repo']['commit']}`",
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
