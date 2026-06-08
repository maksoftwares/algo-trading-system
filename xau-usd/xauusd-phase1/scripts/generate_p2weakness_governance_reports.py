from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


EA_REL = Path("mt5") / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5"
SAFE_PRESET_REL = Path("mt5") / "Presets" / "Phase2WeaknessBreakoutRetestExecutor.demo_xauusd.set"
OWNER_TEMPLATE_REL = Path("mt5") / "Presets" / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.template.set"
RUNTIME_NOTES_REL = Path("docs") / "P2WEAKNESS_BR_V1_RUNTIME_NOTES.md"
REGISTRY_REL = Path("docs") / "MAGIC_NUMBER_EXTERNAL_REGISTRY.md"
DEFAULT_ORDER_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_order_log_xauusd.csv")
DEFAULT_STARTUP_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_startup_xauusd.csv")
DEFAULT_KILL_SWITCH = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_kill_switch.txt")
REPORTS_DIR = Path("outputs") / "reports"
P2_MAGIC_START = 931000
P2_MAGIC_END = 931099
P2_ACTIVE_MAGIC = 931000
WR50_RANGES = ((930000, 930099), (930100, 930199), (930200, 930299))


@dataclass(frozen=True)
class ReportOutput:
    status: str
    paths: tuple[Path, ...]


def generate_p2weakness_governance_reports(
    phase1_root: Path,
    output_dir: Path | None = None,
    order_log: Path = DEFAULT_ORDER_LOG,
    startup_log: Path = DEFAULT_STARTUP_LOG,
    kill_switch: Path = DEFAULT_KILL_SWITCH,
    prove_clean_clone: bool = False,
    clean_clone_repo_url: str | None = None,
    clean_clone_branch: str = "main",
) -> ReportOutput:
    phase1_root = phase1_root.resolve()
    output_dir = (output_dir or phase1_root / REPORTS_DIR).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source = _read(phase1_root / EA_REL)
    safe_preset = _preset(phase1_root / SAFE_PRESET_REL)
    owner_template = _preset(phase1_root / OWNER_TEMPLATE_REL)
    runtime_notes = _read(phase1_root / RUNTIME_NOTES_REL)
    registry = _read(phase1_root / REGISTRY_REL)
    source_inputs = _source_inputs(source)
    created_at = _utc_now()

    parity = _parity_payload(phase1_root, source, source_inputs, safe_preset, owner_template, runtime_notes, registry, created_at)
    magic = _magic_payload(source_inputs, safe_preset, owner_template, registry, order_log, created_at)
    deployment = _deployment_payload(phase1_root, safe_preset, owner_template, created_at)
    clean_clone = (
        _clean_clone_proof_payload(
            phase1_root,
            clean_clone_repo_url or _default_repo_url(phase1_root),
            clean_clone_branch,
            parity,
            magic,
            created_at,
        )
        if prove_clean_clone
        else _clean_clone_payload(phase1_root, parity, magic, created_at)
    )
    daily_risk = _daily_risk_payload(order_log, startup_log, magic, created_at)
    runtime = _runtime_reconciliation_payload(order_log, startup_log, kill_switch, magic, created_at)

    outputs = (
        _write_pair(output_dir, "P2WEAKNESS_BR_V1_SOURCE_GOVERNANCE_PARITY", parity, _render_parity),
        _write_pair(output_dir, "P2WEAKNESS_BR_V1_MAGIC_COLLISION_AUDIT", magic, _render_magic),
        _write_pair(output_dir, "P2WEAKNESS_BR_V1_DEPLOYMENT", deployment, _render_deployment),
        _write_pair(output_dir, "P2WEAKNESS_BR_V1_CLEAN_CLONE_RECONCILIATION", clean_clone, _render_clean_clone),
        _write_pair(output_dir, "P2WEAKNESS_BR_V1_RUNTIME_RECONCILIATION", runtime, _render_runtime_reconciliation),
        _write_pair(output_dir, "EXPERIMENTAL_DEMO_DAILY_RISK_REPORT", daily_risk, _render_daily_risk),
    )
    flat_paths = tuple(path for pair in outputs for path in pair)
    status = "PASS" if parity["status"] == "PASS" and magic["status"] == "PASS" and (not prove_clean_clone or clean_clone["status"] == "PASS") else "FAIL"
    return ReportOutput(status=status, paths=flat_paths)


def _parity_payload(
    phase1_root: Path,
    source: str,
    source_inputs: dict[str, str],
    safe_preset: dict[str, str],
    owner_template: dict[str, str],
    runtime_notes: str,
    registry: str,
    created_at: str,
) -> dict[str, Any]:
    checks = [
        _token_check("non_canonical_banner", source, "NON_CANONICAL / EXPERIMENTAL DEMO ONLY / DO NOT DEPLOY AS PHASE2"),
        _input_check(source_inputs, "InpDryRunOnly", "true"),
        _input_check(source_inputs, "InpBrokerActionAllowed", "false"),
        _input_check(source_inputs, "InpAllowedAccountLoginsCsv", ""),
        _input_check(source_inputs, "InpExperimentalAuthorizationToken", ""),
        _input_check(source_inputs, "InpCostSuspensionAcknowledgementToken", ""),
        _input_check(source_inputs, "InpCandidateStatus", "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY"),
        _input_check(source_inputs, "InpFamilyLifecycleStatus", "COST_SUSPENDED_CANONICAL"),
        _input_check(source_inputs, "InpMagicNumber", str(P2_ACTIVE_MAGIC)),
        _preset_check(safe_preset, "safe_preset_dry_run", "InpDryRunOnly", "true"),
        _preset_check(safe_preset, "safe_preset_broker_action_disabled", "InpBrokerActionAllowed", "false"),
        _preset_check(owner_template, "owner_template_dry_run", "InpDryRunOnly", "true"),
        _preset_check(owner_template, "owner_template_broker_action_disabled", "InpBrokerActionAllowed", "false"),
        _preset_check(owner_template, "owner_template_account_placeholder", "InpAllowedAccountLoginsCsv", "<OWNER_TO_FILL>"),
        _preset_check(owner_template, "owner_template_auth_placeholder", "InpExperimentalAuthorizationToken", "<OWNER_TO_FILL>"),
        _preset_check(owner_template, "owner_template_cost_ack_placeholder", "InpCostSuspensionAcknowledgementToken", "<OWNER_TO_FILL>"),
        _preset_check(owner_template, "owner_template_magic", "InpMagicNumber", str(P2_ACTIVE_MAGIC)),
        _token_check("cost_suspension_ack_guard", source, "CostSuspensionAcknowledgementTokenValid", "cost_suspension_acknowledgement_token_missing_or_invalid"),
        _token_check("kill_switch_present", source, "KillSwitchActive", "InpKillSwitchFileName"),
        _token_check("demo_server_refusal", source, 'ContainsText(server, "live")', 'ContainsText(server, "real")'),
        _token_check("cost_r_guard", source, "InpMaxEstimatedCostR", "estimated_cost_r_exceeds_threshold"),
        _token_check("spread_guard", source, "InpMaxMeasuredSpreadPoints", "measured_spread_points_exceeds_threshold"),
        _token_check("market_proxy_logged", source, "MARKET_PROXY", "order_mode"),
        _token_check("duplicate_family_suppression", source, "SameDirectionFamilyExposureExists", "DuplicateFamilyLockActive"),
        _token_check("startup_safe_default_flags", source, "source_default_safe", "owner_authorized_set_used", "cost_suspension_acknowledged"),
        _token_check("runtime_notes_updated", runtime_notes, "931000-931099", "owner_authorized_demo_xauusd.template.set"),
        _token_check("registry_updated", registry, "P2WEAKNESS_BR_V1", "931000-931099"),
        _fixed_lot_check(source_inputs),
    ]
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        "status": status,
        "created_at_utc": created_at,
        "source": str(phase1_root / EA_REL),
        "safe_preset": str(phase1_root / SAFE_PRESET_REL),
        "owner_authorized_template": str(phase1_root / OWNER_TEMPLATE_REL),
        "source_sha256": _sha256(phase1_root / EA_REL),
        "safe_preset_sha256": _sha256(phase1_root / SAFE_PRESET_REL),
        "owner_authorized_template_sha256": _sha256(phase1_root / OWNER_TEMPLATE_REL),
        "authority": "P2WEAKNESS_BR_V1 governance parity only; no canonical Phase 2, paper-mode, live, or real-capital authorization.",
        "checks": checks,
        "failed_count": sum(1 for check in checks if check["status"] != "PASS"),
        "input_declaration_block": _input_declaration_block(source),
    }


def _magic_payload(
    source_inputs: dict[str, str],
    safe_preset: dict[str, str],
    owner_template: dict[str, str],
    registry: str,
    order_log: Path,
    created_at: str,
) -> dict[str, Any]:
    source_magic = _to_int(source_inputs.get("InpMagicNumber"))
    safe_magic = _to_int(safe_preset.get("InpMagicNumber"))
    owner_magic = _to_int(owner_template.get("InpMagicNumber"))
    runtime_magics = sorted(_runtime_magics(order_log))
    active = {
        "WR50_BreakoutEvening_v0": 930000,
        "WR50_BreakoutQuality_v0": 930100,
        "WR50_BreakoutExit1R_v0": 930200,
        "P2WEAKNESS_BR_V1": P2_ACTIVE_MAGIC,
    }
    duplicate_values = _duplicates(active)
    checks = [
        _range_check("source_magic_in_p2weakness_namespace", source_magic, P2_MAGIC_START, P2_MAGIC_END),
        _range_check("safe_preset_magic_in_p2weakness_namespace", safe_magic, P2_MAGIC_START, P2_MAGIC_END),
        _range_check("owner_template_magic_in_p2weakness_namespace", owner_magic, P2_MAGIC_START, P2_MAGIC_END),
        _equality_check("active_magic_is_931000", source_magic, P2_ACTIVE_MAGIC),
        _bool_check("p2weakness_not_inside_wr50_namespace", not _range_overlaps((P2_MAGIC_START, P2_MAGIC_END), (930000, 930999)), "P2WEAKNESS=931000-931099; WR50=930000-930999"),
        _bool_check("active_magic_values_unique", not duplicate_values, f"duplicates={duplicate_values or 'none'}"),
        _bool_check("registry_mentions_p2weakness_namespace", "931000-931099" in registry and "P2WEAKNESS_BR_V1" in registry, "registry updated"),
    ]
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        "status": status,
        "created_at_utc": created_at,
        "authority": "Magic collision audit for experimental namespaces. PASS does not authorize deployment or trading.",
        "p2weakness_namespace": f"{P2_MAGIC_START}-{P2_MAGIC_END}",
        "p2weakness_active_magic": P2_ACTIVE_MAGIC,
        "source_magic": source_magic,
        "safe_preset_magic": safe_magic,
        "owner_template_magic": owner_magic,
        "known_active_assignments": active,
        "runtime_log_magics_observed": runtime_magics,
        "runtime_previous_magic_warning": 930101 in runtime_magics,
        "checks": checks,
        "failed_count": sum(1 for check in checks if check["status"] != "PASS"),
    }


def _deployment_payload(phase1_root: Path, safe_preset: dict[str, str], owner_template: dict[str, str], created_at: str) -> dict[str, Any]:
    return {
        "status": "REPORT_ONLY_NO_NEW_DEPLOYMENT",
        "created_at_utc": created_at,
        "authority": "Reviewer-requested deployment-boundary summary. No MT5 terminal was closed, restarted, attached, detached, or redeployed by this report generator.",
        "source": str(phase1_root / EA_REL),
        "safe_preset": str(phase1_root / SAFE_PRESET_REL),
        "owner_authorized_template": str(phase1_root / OWNER_TEMPLATE_REL),
        "source_sha256": _sha256(phase1_root / EA_REL),
        "safe_preset_sha256": _sha256(phase1_root / SAFE_PRESET_REL),
        "owner_authorized_template_sha256": _sha256(phase1_root / OWNER_TEMPLATE_REL),
        "safe_preset_broker_action_allowed": safe_preset.get("InpBrokerActionAllowed", ""),
        "owner_template_broker_action_allowed": owner_template.get("InpBrokerActionAllowed", ""),
        "owner_template_dry_run": owner_template.get("InpDryRunOnly", ""),
        "deployment_attempted": False,
        "terminal_closed_or_restarted": False,
        "charts_attached_or_modified": False,
        "profiles_modified": False,
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
    }


def _clean_clone_payload(phase1_root: Path, parity: dict[str, Any], magic: dict[str, Any], created_at: str) -> dict[str, Any]:
    dirty = _git_status(phase1_root)
    status = "PENDING_AFTER_COMMIT_AND_PUSH" if dirty else "READY_FOR_CLEAN_CLONE_RECHECK"
    return {
        "status": status,
        "created_at_utc": created_at,
        "authority": "Clean-clone reconciliation marker for P2WEAKNESS_BR_V1. A true remote clean-clone proof should be regenerated after commit/push.",
        "repo_head": _git_head(phase1_root),
        "working_tree_has_pending_changes": bool(dirty),
        "pending_paths": dirty,
        "local_parity_status": parity["status"],
        "local_magic_collision_status": magic["status"],
        "required_post_push_action": "Clone origin/main after push, rerun this generator, and expect source/magic parity to remain PASS.",
    }


def _clean_clone_proof_payload(
    phase1_root: Path,
    repo_url: str,
    branch: str,
    local_parity: dict[str, Any],
    local_magic: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    repo_root = phase1_root.parents[1]
    temp_parent = Path("C:/") if Path("C:/").exists() else None
    with tempfile.TemporaryDirectory(prefix="p2w-", dir=str(temp_parent) if temp_parent else None) as temp_dir:
        clone_root = Path(temp_dir) / "origin-main-clean-clone"
        _run(["git", "-c", "core.longpaths=true", "clone", "--depth", "1", "--branch", branch, repo_url, str(clone_root)], cwd=Path(temp_dir))
        clone_commit = _run(["git", "rev-parse", "HEAD"], cwd=clone_root).strip()
        clone_status = _run(["git", "status", "--short"], cwd=clone_root).strip()
        clone_phase1 = clone_root / "xau-usd" / "xauusd-phase1"
        clone_source = _read(clone_phase1 / EA_REL)
        clone_safe = _preset(clone_phase1 / SAFE_PRESET_REL)
        clone_template = _preset(clone_phase1 / OWNER_TEMPLATE_REL)
        clone_runtime_notes = _read(clone_phase1 / RUNTIME_NOTES_REL)
        clone_registry = _read(clone_phase1 / REGISTRY_REL)
        clone_inputs = _source_inputs(clone_source)
        clone_parity = _parity_payload(
            clone_phase1,
            clone_source,
            clone_inputs,
            clone_safe,
            clone_template,
            clone_runtime_notes,
            clone_registry,
            created_at,
        )
        clone_magic = _magic_payload(clone_inputs, clone_safe, clone_template, clone_registry, Path(temp_dir) / "missing_order_log.csv", created_at)
        clone_source_sha = _sha256(clone_phase1 / EA_REL)
        clone_safe_sha = _sha256(clone_phase1 / SAFE_PRESET_REL)
        clone_template_sha = _sha256(clone_phase1 / OWNER_TEMPLATE_REL)
        deploy_text = _read(clone_phase1 / "scripts" / "deploy_phase2_weakness_breakout_executor.py")
        setup_text = _read(clone_phase1 / "scripts" / "setup_phase2_weakness_portable_demo_terminal.py")
        dashboard_text = _read(clone_phase1 / "scripts" / "generate_demo_observer_dashboard.py")
        checks = [
            _bool_check("clone_working_tree_clean", clone_status == "", f"git status --short={clone_status!r}"),
            _bool_check("clone_parity_pass", clone_parity["status"] == "PASS", f"clone parity={clone_parity['status']}"),
            _bool_check("clone_magic_pass", clone_magic["status"] == "PASS", f"clone magic={clone_magic['status']}"),
            _bool_check("legacy_owner_authorized_set_absent", not (clone_phase1 / "mt5" / "Presets" / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.set").exists(), "legacy executing preset absent"),
            _bool_check("owner_template_committed_non_executing", clone_template.get("InpDryRunOnly") == "true" and clone_template.get("InpBrokerActionAllowed") == "false", "template dry-run=true; broker action=false"),
            _token_check("deploy_script_report_only_default", deploy_text, "allow_deploy: bool = False", "REPORT_ONLY_NO_NEW_DEPLOYMENT"),
            _token_check("deploy_script_requires_preconditions", deploy_text, "_require_deploy_preconditions", "clean_clone_reconciliation", "owner_authorized_template_not_non_executing"),
            _token_check("portable_setup_no_runtime_defaults", setup_text, "prepare: bool = False", "launch: bool = False", "deploy: bool = False", "--allow-prepare", "--allow-launch", "--allow-deploy"),
            _token_check("dashboard_includes_p2weakness_actual_trades", dashboard_text, "P2WEAKNESS_MAGIC_MIN", "p2weakness_br_v1", "WR50_BreakoutQuality_v0"),
        ]
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        "status": status,
        "created_at_utc": created_at,
        "authority": (
            "Remote clean-clone proof for P2WEAKNESS_BR_V1. This clones the configured branch and validates "
            "the pushed source, presets, scripts, and parser boundaries. It does not deploy, attach charts, "
            "touch MT5 runtime, authorize canonical Phase 2, or authorize real capital."
        ),
        "repo_url": repo_url,
        "branch": branch,
        "clone_commit_hash": clone_commit,
        "local_repo_head": _git_head(phase1_root),
        "local_working_tree_has_pending_changes_after_report_generation": bool(_git_status(phase1_root)),
        "clone_working_tree_status_short": clone_status,
        "local_parity_status": local_parity["status"],
        "local_magic_collision_status": local_magic["status"],
        "clone_parity_status": clone_parity["status"],
        "clone_magic_collision_status": clone_magic["status"],
        "source_path": (Path("xau-usd") / "xauusd-phase1" / EA_REL).as_posix(),
        "source_file_sha256": _sha256(phase1_root / EA_REL),
        "clone_source_file_sha256": clone_source_sha,
        "safe_preset_sha256": _sha256(phase1_root / SAFE_PRESET_REL),
        "clone_safe_preset_sha256": clone_safe_sha,
        "owner_template_sha256": _sha256(phase1_root / OWNER_TEMPLATE_REL),
        "clone_owner_template_sha256": clone_template_sha,
        "source_input_declaration_block": _input_declaration_block(clone_source),
        "checks": checks,
        "failed_count": sum(1 for check in checks if check["status"] != "PASS"),
    }


def _daily_risk_payload(order_log: Path, startup_log: Path, magic: dict[str, Any], created_at: str) -> dict[str, Any]:
    rows = _csv_rows(order_log)
    startup_rows = _csv_rows(startup_log)
    executed = [row for row in rows if row.get("action") == "ORDER_SEND_OK"]
    guard_blocks = [row for row in rows if row.get("action") == "GUARD_BLOCK"]
    costs = [_to_float(row.get("estimated_cost_R")) for row in rows if _to_float(row.get("estimated_cost_R")) is not None]
    costs_clean = [value for value in costs if value is not None]
    latest = rows[-1] if rows else {}
    magics = sorted({row.get("magic", "") for row in rows if row.get("magic")})
    return {
        "status": "REVIEW_ONLY",
        "created_at_utc": created_at,
        "authority": "Experimental demo daily risk report. It does not authorize canonical Phase 2, deployment, live trading, or real capital.",
        "order_log": str(order_log),
        "startup_log": str(startup_log),
        "order_log_exists": order_log.exists(),
        "startup_log_exists": startup_log.exists(),
        "rows": len(rows),
        "executed_orders": len(executed),
        "guard_blocks": len(guard_blocks),
        "open_positions_from_log": _last_int(rows, "family_open_exposure"),
        "account_orders_today_from_log": _last_int(rows, "account_orders_today"),
        "cost_r_min": round(min(costs_clean), 4) if costs_clean else None,
        "cost_r_median": round(median(costs_clean), 4) if costs_clean else None,
        "cost_r_max": round(max(costs_clean), 4) if costs_clean else None,
        "latest_timestamp_broker": latest.get("timestamp_broker", ""),
        "latest_guard_reason": latest.get("guard_reason", ""),
        "latest_action": latest.get("action", ""),
        "magics_observed": magics,
        "runtime_previous_magic_warning": magic.get("runtime_previous_magic_warning", False),
        "startup_rows": len(startup_rows),
        "latest_startup_status": startup_rows[-1].get("startup_status", "") if startup_rows else "",
        "kill_switch_status": "NOT_CHECKED_BY_REPORT_GENERATOR",
        "owner_notes": "New deployments are paused until reviewer-requested governance fixes are reviewed.",
    }


def _runtime_reconciliation_payload(
    order_log: Path,
    startup_log: Path,
    kill_switch: Path,
    magic: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    order_rows = _csv_rows(order_log)
    startup_rows = _csv_rows(startup_log)
    latest_order = order_rows[-1] if order_rows else {}
    latest_startup = startup_rows[-1] if startup_rows else {}
    runtime_magics = sorted(_runtime_magics(order_log))
    return {
        "status": "REVIEW_ONLY_RUNTIME_RECONCILED",
        "created_at_utc": created_at,
        "authority": (
            "Runtime reconciliation for existing P2WEAKNESS_BR_V1 evidence. This report reads CSV/log files only; "
            "it does not attach charts, change presets, deploy files, close terminals, or authorize canonical Phase 2."
        ),
        "new_deployments_paused": True,
        "order_log": str(order_log),
        "startup_log": str(startup_log),
        "kill_switch_file": str(kill_switch),
        "order_log_exists": order_log.exists(),
        "startup_log_exists": startup_log.exists(),
        "kill_switch_exists": kill_switch.exists(),
        "kill_switch_text": _read(kill_switch).strip() if kill_switch.exists() else "",
        "order_rows": len(order_rows),
        "startup_rows": len(startup_rows),
        "latest_order_timestamp_broker": latest_order.get("timestamp_broker", ""),
        "latest_order_action": latest_order.get("action", ""),
        "latest_order_magic": latest_order.get("magic", ""),
        "latest_order_comment": latest_order.get("comment", latest_order.get("order_comment", "")),
        "latest_order_symbol": latest_order.get("symbol", ""),
        "latest_guard_reason": latest_order.get("guard_reason", ""),
        "latest_family_open_exposure": latest_order.get("family_open_exposure", ""),
        "latest_account_orders_today": latest_order.get("account_orders_today", ""),
        "latest_startup_timestamp_broker": latest_startup.get("timestamp_broker", ""),
        "latest_startup_status": latest_startup.get("startup_status", ""),
        "latest_startup_account": latest_startup.get("account_login", latest_startup.get("account", "")),
        "latest_startup_server": latest_startup.get("account_server", latest_startup.get("server", "")),
        "runtime_magics_observed": runtime_magics,
        "runtime_previous_magic_warning": magic.get("runtime_previous_magic_warning", False),
        "current_source_magic": P2_ACTIVE_MAGIC,
        "chart_attachment_observable_from_csv": False,
        "chart_attachment_evidence": "NOT_OBSERVABLE_FROM_CSV_LOGS",
        "runtime_preset_snapshot_observable_from_csv": False,
        "runtime_preset_snapshot_evidence": "NOT_OBSERVABLE_FROM_CSV_LOGS",
        "interpretation": (
            "If runtime logs still show 930101, that is historical/runtime evidence from before the repo hardening; "
            "the committed source and presets now use 931000 and remain non-executing by default."
        ),
    }


def _write_pair(output_dir: Path, stem: str, payload: dict[str, Any], renderer) -> tuple[Path, Path]:
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(renderer(payload), encoding="utf-8")
    return json_path, md_path


def _render_parity(payload: dict[str, Any]) -> str:
    lines = _report_header("P2WEAKNESS BR V1 Source Governance Parity", payload)
    lines.extend([
        f"- Source: `{payload['source']}`",
        f"- Safe preset: `{payload['safe_preset']}`",
        f"- Owner-authorized template: `{payload['owner_authorized_template']}`",
        f"- Failed checks: `{payload['failed_count']}`",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ])
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {_escape(check['evidence'])} |")
    lines.extend(["", "## Input Declaration Block", "", "```mql5", payload["input_declaration_block"].rstrip(), "```", ""])
    return "\n".join(lines)


def _render_magic(payload: dict[str, Any]) -> str:
    lines = _report_header("P2WEAKNESS BR V1 Magic Collision Audit", payload)
    lines.extend([
        f"- P2WEAKNESS namespace: `{payload['p2weakness_namespace']}`",
        f"- Active magic: `{payload['p2weakness_active_magic']}`",
        f"- Runtime previous-magic warning: `{payload['runtime_previous_magic_warning']}`",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ])
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {_escape(check['evidence'])} |")
    lines.extend(["", "## Active Assignments", "", "| EA | Magic |", "|---|---:|"])
    for name, magic in payload["known_active_assignments"].items():
        lines.append(f"| {name} | {magic} |")
    lines.append("")
    return "\n".join(lines)


def _render_deployment(payload: dict[str, Any]) -> str:
    lines = _report_header("P2WEAKNESS BR V1 Deployment Boundary", payload)
    lines.extend([
        f"- Source SHA256: `{payload['source_sha256']}`",
        f"- Safe preset SHA256: `{payload['safe_preset_sha256']}`",
        f"- Owner-authorized template SHA256: `{payload['owner_authorized_template_sha256']}`",
        f"- Owner template dry-run: `{payload['owner_template_dry_run']}`",
        f"- Owner template broker action allowed: `{payload['owner_template_broker_action_allowed']}`",
        f"- Deployment attempted: `{payload['deployment_attempted']}`",
        f"- Terminal closed/restarted: `{payload['terminal_closed_or_restarted']}`",
        f"- Charts attached/modified: `{payload['charts_attached_or_modified']}`",
        f"- Profiles modified: `{payload['profiles_modified']}`",
        f"- Canonical Phase 2 authorized: `{payload['canonical_phase2_authorized']}`",
        f"- Live trading authorized: `{payload['live_trading_authorized']}`",
        "",
    ])
    return "\n".join(lines)


def _render_clean_clone(payload: dict[str, Any]) -> str:
    lines = _report_header("P2WEAKNESS BR V1 Clean-Clone Reconciliation", payload)
    if "clone_commit_hash" in payload:
        lines.extend([
            f"- Repo URL: `{payload['repo_url']}`",
            f"- Branch: `{payload['branch']}`",
            f"- Clean-clone commit hash: `{payload['clone_commit_hash']}`",
            f"- Local repo HEAD: `{payload['local_repo_head']}`",
            f"- Clone working tree status: `{payload['clone_working_tree_status_short']}`",
            f"- Local parity status: `{payload['local_parity_status']}`",
            f"- Local magic collision status: `{payload['local_magic_collision_status']}`",
            f"- Clone parity status: `{payload['clone_parity_status']}`",
            f"- Clone magic collision status: `{payload['clone_magic_collision_status']}`",
            f"- Source path: `{payload['source_path']}`",
            f"- Source SHA256: `{payload['source_file_sha256']}`",
            f"- Clone source SHA256: `{payload['clone_source_file_sha256']}`",
            f"- Owner template SHA256: `{payload['owner_template_sha256']}`",
            f"- Clone owner template SHA256: `{payload['clone_owner_template_sha256']}`",
            f"- Failed checks: `{payload['failed_count']}`",
            "",
            "## Checks",
            "",
            "| Check | Status | Evidence |",
            "|---|---|---|",
        ])
        for check in payload["checks"]:
            lines.append(f"| {check['name']} | {check['status']} | {_escape(check['evidence'])} |")
        lines.extend(
            [
                "",
                "## Input Declaration Block",
                "",
                "```mql5",
                payload["source_input_declaration_block"].rstrip(),
                "```",
                "",
                "## Boundary",
                "",
                "This proof validates the pushed clean clone only. It does not deploy, attach charts, touch MT5 runtime, authorize canonical Phase 2, or authorize real capital.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend([
        f"- Repo HEAD: `{payload['repo_head']}`",
        f"- Working tree has pending changes: `{payload['working_tree_has_pending_changes']}`",
        f"- Local parity status: `{payload['local_parity_status']}`",
        f"- Local magic collision status: `{payload['local_magic_collision_status']}`",
        f"- Required post-push action: {payload['required_post_push_action']}",
        "",
        "## Pending Paths",
        "",
    ])
    for path in payload["pending_paths"]:
        lines.append(f"- `{path}`")
    lines.append("")
    return "\n".join(lines)


def _render_runtime_reconciliation(payload: dict[str, Any]) -> str:
    lines = _report_header("P2WEAKNESS BR V1 Runtime Reconciliation", payload)
    lines.extend([
        f"- New deployments paused: `{payload['new_deployments_paused']}`",
        f"- Order log exists: `{payload['order_log_exists']}`",
        f"- Startup log exists: `{payload['startup_log_exists']}`",
        f"- Kill switch exists: `{payload['kill_switch_exists']}`",
        f"- Order rows: `{payload['order_rows']}`",
        f"- Startup rows: `{payload['startup_rows']}`",
        f"- Latest order broker time: `{payload['latest_order_timestamp_broker']}`",
        f"- Latest order action: `{payload['latest_order_action']}`",
        f"- Latest order symbol: `{payload['latest_order_symbol']}`",
        f"- Latest order magic: `{payload['latest_order_magic']}`",
        f"- Latest guard reason: `{payload['latest_guard_reason']}`",
        f"- Latest family open exposure: `{payload['latest_family_open_exposure']}`",
        f"- Latest account orders today: `{payload['latest_account_orders_today']}`",
        f"- Latest startup status: `{payload['latest_startup_status']}`",
        f"- Latest startup account/server: `{payload['latest_startup_account']}` / `{payload['latest_startup_server']}`",
        f"- Runtime magics observed: `{payload['runtime_magics_observed']}`",
        f"- Runtime previous-magic warning: `{payload['runtime_previous_magic_warning']}`",
        f"- Current committed source magic: `{payload['current_source_magic']}`",
        f"- Chart attachment evidence: `{payload['chart_attachment_evidence']}`",
        f"- Runtime preset snapshot evidence: `{payload['runtime_preset_snapshot_evidence']}`",
        "",
        "## Interpretation",
        "",
        payload["interpretation"],
        "",
    ])
    return "\n".join(lines)


def _render_daily_risk(payload: dict[str, Any]) -> str:
    lines = _report_header("Experimental Demo Daily Risk Report", payload)
    lines.extend([
        f"- Order log exists: `{payload['order_log_exists']}`",
        f"- Startup log exists: `{payload['startup_log_exists']}`",
        f"- Rows: `{payload['rows']}`",
        f"- Executed orders: `{payload['executed_orders']}`",
        f"- Guard blocks: `{payload['guard_blocks']}`",
        f"- Cost R min/median/max: `{payload['cost_r_min']}` / `{payload['cost_r_median']}` / `{payload['cost_r_max']}`",
        f"- Latest action: `{payload['latest_action']}`",
        f"- Latest guard reason: `{payload['latest_guard_reason']}`",
        f"- Runtime previous-magic warning: `{payload['runtime_previous_magic_warning']}`",
        f"- Latest startup status: `{payload['latest_startup_status']}`",
        f"- Owner notes: {payload['owner_notes']}",
        "",
    ])
    return "\n".join(lines)


def _report_header(title: str, payload: dict[str, Any]) -> list[str]:
    return [
        f"# {title}",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"Created at UTC: `{payload['created_at_utc']}`",
        "",
    ]


def _token_check(name: str, text: str, *tokens: str) -> dict[str, str]:
    missing = [token for token in tokens if token not in text]
    return {"name": name, "status": "PASS" if not missing else "FAIL", "evidence": "all required tokens present" if not missing else "missing: " + ", ".join(missing)}


def _input_check(inputs: dict[str, str], name: str, expected: str) -> dict[str, str]:
    actual = inputs.get(name)
    return _bool_check(f"{name}_default", actual == expected, f"actual={actual!r}; expected={expected!r}")


def _preset_check(preset: dict[str, str], check_name: str, key: str, expected: str) -> dict[str, str]:
    actual = preset.get(key)
    return _bool_check(check_name, actual == expected, f"{key}={actual!r}; expected={expected!r}")


def _fixed_lot_check(inputs: dict[str, str]) -> dict[str, str]:
    value = _to_float(inputs.get("InpFixedLot"))
    return _bool_check("fixed_lot_lte_0_01", value is not None and value <= 0.01, f"InpFixedLot={value}")


def _range_check(name: str, value: int | None, low: int, high: int) -> dict[str, str]:
    return _bool_check(name, value is not None and low <= value <= high, f"value={value}; allowed={low}-{high}")


def _equality_check(name: str, value: int | None, expected: int) -> dict[str, str]:
    return _bool_check(name, value == expected, f"value={value}; expected={expected}")


def _bool_check(name: str, ok: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if ok else "FAIL", "evidence": evidence}


def _source_inputs(source: str) -> dict[str, str]:
    values: dict[str, str] = {}
    pattern = re.compile(r"^\s*input\s+\w+\s+(\w+)\s*=\s*(.+?);\s*$")
    for line in source.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        raw = match.group(2).strip()
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        values[match.group(1)] = raw
    return values


def _preset(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _input_declaration_block(source: str) -> str:
    return "\n".join(f"{index}: {line}" for index, line in enumerate(source.splitlines(), start=1) if line.strip().startswith("input "))


def _runtime_magics(order_log: Path) -> set[int]:
    values: set[int] = set()
    for row in _csv_rows(order_log):
        magic = _to_int(row.get("magic"))
        if magic is not None:
            values.add(magic)
    return values


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _last_int(rows: list[dict[str, str]], key: str) -> int | None:
    for row in reversed(rows):
        value = _to_int(row.get(key))
        if value is not None:
            return value
    return None


def _to_int(value: object) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _to_float(value: object) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value))
    except ValueError:
        return None


def _duplicates(values: dict[str, int]) -> dict[int, list[str]]:
    seen: dict[int, list[str]] = {}
    for name, magic in values.items():
        seen.setdefault(magic, []).append(name)
    return {magic: names for magic, names in seen.items() if len(names) > 1}


def _range_overlaps(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] <= right[1] and right[0] <= left[1]


def _git_head(phase1_root: Path) -> str:
    return _run_git(phase1_root.parents[1], ["rev-parse", "HEAD"]) or "UNKNOWN"


def _git_status(phase1_root: Path) -> list[str]:
    status = _run_git(phase1_root.parents[1], ["status", "--short"])
    return [line.strip() for line in status.splitlines() if line.strip()]


def _run_git(repo_root: Path, args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=repo_root, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _default_repo_url(phase1_root: Path) -> str:
    return _run_git(phase1_root.parents[1], ["config", "--get", "remote.origin.url"]) or "https://github.com/maksoftwares/algo-trading-system.git"


def _sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate P2WEAKNESS_BR_V1 governance and daily risk reports.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--order-log", type=Path, default=DEFAULT_ORDER_LOG)
    parser.add_argument("--startup-log", type=Path, default=DEFAULT_STARTUP_LOG)
    parser.add_argument("--kill-switch", type=Path, default=DEFAULT_KILL_SWITCH)
    parser.add_argument("--prove-clean-clone", action="store_true", help="Clone the configured remote branch and generate a real PASS/FAIL clean-clone proof.")
    parser.add_argument("--repo-url", default=None, help="Repository URL for --prove-clean-clone; defaults to remote.origin.url.")
    parser.add_argument("--branch", default="main", help="Remote branch for --prove-clean-clone.")
    args = parser.parse_args(argv)
    output = generate_p2weakness_governance_reports(
        args.phase1_root,
        output_dir=args.output_dir,
        order_log=args.order_log,
        startup_log=args.startup_log,
        kill_switch=args.kill_switch,
        prove_clean_clone=args.prove_clean_clone,
        clean_clone_repo_url=args.repo_url,
        clean_clone_branch=args.branch,
    )
    print(f"P2WEAKNESS governance reports: {output.status}")
    for path in output.paths:
        print(path)
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
