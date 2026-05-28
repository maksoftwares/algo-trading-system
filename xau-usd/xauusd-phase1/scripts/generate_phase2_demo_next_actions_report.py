from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_NEXT_ACTIONS.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_DEMO_NEXT_ACTIONS.md"
AUTHORITY_NOTE = (
    "This report is an operational next-action aid only. PHASE2_READINESS_REPORT.md remains "
    "the sole real readiness authority; this report does not authorize paper mode, demo trading, "
    "broker execution, live capital, or MT5 runtime changes."
)


@dataclass(frozen=True)
class DemoNextActionsOutput:
    status: str
    json_path: Path
    markdown_path: Path
    do_now_count: int


def generate_phase2_demo_next_actions_report(root: Path, output_json: Path | None = None) -> DemoNextActionsOutput:
    root = root.resolve()
    report_dir = root / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_REPORT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_REPORT_JSON.name else root / DEFAULT_REPORT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    countdown_path = report_dir / "PHASE2_DEMO_COUNTDOWN.json"
    owner_packet_path = report_dir / "PHASE2_OWNER_ACTION_PACKET.json"
    bootstrap_path = report_dir / "PHASE2_VPS_BOOTSTRAP_PACKET.json"
    vps_selection_check_path = report_dir / "PHASE2_VPS_SELECTION_DECISION_CHECK.json"
    readiness_path = report_dir / "PHASE2_READINESS_REPORT.md"
    preflight_path = report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md"

    countdown = _read_json(countdown_path)
    owner_packet = _read_json(owner_packet_path)
    bootstrap = _read_json(bootstrap_path)
    vps_selection_check = _read_json(vps_selection_check_path)
    owner_sheet = _mapping(owner_packet.get("one_screen_vps_decision_sheet"))
    wait_gates = _mapping_rows(countdown.get("wait_gates"))
    owner_actions = _mapping_rows(countdown.get("owner_actions_now")) or _mapping_rows(owner_packet.get("owner_actions_now"))
    pending_gates = _mapping_rows(countdown.get("pending_gates"))
    created_at = datetime.now(timezone.utc)
    target_base = _parse_utc(str(countdown.get("created_at_utc", ""))) or created_at
    do_now = _do_now_actions(wait_gates, owner_actions, owner_sheet, vps_selection_check)
    after_vps = _after_vps_actions(owner_sheet, bootstrap, vps_selection_check)
    after_wait = _after_wait_actions(wait_gates, pending_gates)
    owner_signature = _owner_signature_actions(countdown, owner_packet)
    earliest_targets = _earliest_gate_targets(target_base, wait_gates)
    gate_closure_map = _gate_closure_map(root, pending_gates, wait_gates, owner_actions)

    payload = {
        "status": _status(countdown, do_now, wait_gates),
        "created_at_utc": _format_utc(created_at),
        "authority": AUTHORITY_NOTE,
        "phase2_readiness_status": _read_markdown_status(readiness_path) or countdown.get("phase2_readiness_status") or "UNKNOWN",
        "phase2_demo_preflight_status": _read_markdown_status(preflight_path) or "UNKNOWN",
        "phase2_demo_countdown_status": countdown.get("status", "UNKNOWN"),
        "pending_gate_count": countdown.get("pending_gate_count", len(pending_gates)),
        "paper_mode_authorized": False,
        "demo_trading_authorized": False,
        "broker_execution_authorized": False,
        "live_trading_authorized": False,
        "do_now": do_now,
        "after_vps_is_provisioned": after_vps,
        "after_wait_gates_pass": after_wait,
        "earliest_gate_targets": earliest_targets,
        "gate_closure_map": gate_closure_map,
        "owner_signature_sequence": owner_signature,
        "wait_gates": wait_gates,
        "owner_decision_sheet": owner_sheet,
        "vps_selection_decision_check": vps_selection_check,
        "forbidden_until_ready": countdown.get("forbidden_until_ready", []),
        "source_reports": {
            "phase2_demo_countdown": str(countdown_path),
            "phase2_owner_action_packet": str(owner_packet_path),
            "phase2_vps_bootstrap_packet": str(bootstrap_path),
            "phase2_vps_selection_decision_check": str(vps_selection_check_path),
            "phase2_readiness": str(readiness_path),
            "phase2_demo_preflight": str(preflight_path),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return DemoNextActionsOutput(payload["status"], output_json, output_md, len(do_now))


def _status(countdown: dict[str, Any], do_now: list[dict[str, str]], wait_gates: list[dict[str, Any]]) -> str:
    if countdown.get("status") == "DEMO_READY_TO_REQUEST_OWNER_APPROVAL":
        return "READY_FOR_OWNER_APPROVAL_REVIEW"
    if do_now and any(str(action.get("status", "")).upper() != "PASS" for action in do_now):
        return "OWNER_ACTION_AND_WAIT_GATES_PENDING"
    if any(str(gate.get("status", "")).upper() != "PASS" for gate in wait_gates):
        return "WAIT_GATES_PENDING"
    return "TRANSITION_REVIEW_REQUIRED"


def _do_now_actions(
    wait_gates: list[dict[str, Any]],
    owner_actions: list[dict[str, Any]],
    owner_sheet: dict[str, Any],
    vps_selection_check: dict[str, Any],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = [
        {
            "step": "keep_collectors_running",
            "status": "PENDING" if _has_pending_wait_gates(wait_gates) else "PASS",
            "action": "Keep Phase 1 dry-run MT5 and passive spread logging running while wait gates mature.",
        }
    ]
    for item in owner_actions:
        gate = str(item.get("gate", ""))
        if gate == "Project owner approval":
            continue
        actions.append(
            {
                "step": _slug(gate),
                "status": str(item.get("status", "UNKNOWN")),
                "action": str(item.get("action", "")),
            }
        )
    if owner_sheet:
        actions.append(
            {
                "step": "use_one_screen_vps_decision_sheet",
                "status": str(owner_sheet.get("status", "WAITING_OWNER_SELECTION")),
                "action": "Use the one-screen VPS decision sheet in PHASE2_OWNER_ACTION_PACKET.md before provisioning.",
            }
        )
    if vps_selection_check:
        actions.append(
            {
                "step": "run_vps_selection_decision_check",
                "status": str(vps_selection_check.get("status", "PENDING")),
                "action": (
                    "Run generate_phase2_vps_selection_decision_check.py after filling the VPS matrix; "
                    "it must PASS before the VPS selection gate can close."
                ),
            }
        )
    return actions


def _after_vps_actions(
    owner_sheet: dict[str, Any],
    bootstrap: dict[str, Any],
    vps_selection_check: dict[str, Any],
) -> list[dict[str, str]]:
    actions = [
        {
            "step": "prepare_vps_evidence_workspace",
            "status": "PENDING",
            "action": "Run prepare_phase2_vps_evidence_workspace.ps1 to create pending evidence files without overwriting verified evidence.",
        },
        {
            "step": "capture_vps_latency",
            "status": "PENDING",
            "action": "Run capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root after the VPS exists.",
        },
        {
            "step": "rerun_vps_selection_decision_check",
            "status": str(vps_selection_check.get("status", "PENDING")) if vps_selection_check else "PENDING",
            "action": "Rerun PHASE2_VPS_SELECTION_DECISION_CHECK after latency evidence is generated and the matrix is filled.",
        },
        {
            "step": "fill_vps_evidence_templates",
            "status": "PENDING",
            "action": "Fill NTP, backup, RDP recovery, and periodic-task evidence templates with verified values only.",
        },
        {
            "step": "run_vps_dry_run_only",
            "status": "PENDING",
            "action": "Compile and run the Phase 1 shell on VPS with dry_run=true and trade_permission=false.",
        },
        {
            "step": "regenerate_vps_first_day_verification",
            "status": "PENDING",
            "action": "Regenerate PHASE2_VPS_FIRST_DAY_VERIFICATION.md and PHASE2_READINESS_REPORT.md.",
        },
    ]
    sheet_actions = owner_sheet.get("after_vps_is_provisioned")
    if isinstance(sheet_actions, list) and sheet_actions:
        actions.append(
            {
                "step": "owner_sheet_after_vps_sequence",
                "status": str(owner_sheet.get("status", "PENDING")),
                "action": "One-screen sheet after-VPS sequence is populated and should be followed.",
            }
        )
    if bootstrap.get("status"):
        actions.append(
            {
                "step": "bootstrap_packet_status",
                "status": str(bootstrap.get("status")),
                "action": "Use PHASE2_VPS_BOOTSTRAP_PACKET.md as the VPS sequence authority.",
            }
        )
    return actions


def _after_wait_actions(wait_gates: list[dict[str, Any]], pending_gates: list[dict[str, Any]]) -> list[dict[str, str]]:
    actions = []
    for gate in wait_gates:
        actions.append(
            {
                "step": _slug(str(gate.get("gate", ""))),
                "status": str(gate.get("status", "UNKNOWN")),
                "action": (
                    f"Wait for {gate.get('gate', 'gate')} to reach {gate.get('required', 'required')} "
                    f"{gate.get('unit', '')}; current {gate.get('current', 'n/a')}, remaining {gate.get('remaining', 'n/a')}."
                ),
            }
        )
    objective_pending = [row for row in pending_gates if row.get("Gate") != "Project owner approval"]
    if objective_pending:
        actions.append(
            {
                "step": "regenerate_readiness_after_objective_gates",
                "status": "PENDING",
                "action": "After all objective gates are PASS, rerun periodic checks and verify PHASE2_READINESS_REPORT.md.",
            }
        )
    return actions


def _earliest_gate_targets(created_at: datetime, wait_gates: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for gate in wait_gates:
        name = str(gate.get("gate", ""))
        status = str(gate.get("status", "UNKNOWN"))
        unit = str(gate.get("unit", ""))
        remaining = _to_float(gate.get("remaining"))
        row = {
            "gate": name,
            "status": status,
            "current": str(gate.get("current", "n/a")),
            "remaining": str(gate.get("remaining", "n/a")),
            "unit": unit,
            "earliest_target_utc": "",
            "condition": "",
        }
        if status.upper() == "PASS":
            row["earliest_target_utc"] = "already_passed"
            row["condition"] = "No wait remaining."
        elif remaining is not None and unit == "hours":
            row["earliest_target_utc"] = _format_utc(created_at + timedelta(hours=remaining))
            row["condition"] = "Assumes no restart, no code-freeze reset, and no unexpected market-data gaps."
        elif remaining is not None and unit == "fresh_market_days":
            row["condition"] = (
                f"Needs {remaining:g} additional fresh market day(s) from the passive spread logger; "
                "legacy rows without tick_fresh do not count."
            )
        else:
            row["condition"] = "Target cannot be estimated from current report fields."
        rows.append(row)
    return rows


def _gate_closure_map(
    root: Path,
    pending_gates: list[dict[str, Any]],
    wait_gates: list[dict[str, Any]],
    owner_actions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    wait_by_name = {str(gate.get("gate", "")): gate for gate in wait_gates}
    owner_action_by_gate = {str(action.get("gate", "")): str(action.get("action", "")) for action in owner_actions}
    rows: list[dict[str, str]] = []
    for gate in pending_gates:
        name = str(gate.get("Gate", ""))
        status = str(gate.get("Status", "UNKNOWN"))
        classification = _gate_classification(name)
        wait = wait_by_name.get(name, {})
        rows.append(
            {
                "gate": name,
                "status": status,
                "category": classification["category"],
                "owner": classification["owner"],
                "why_required": _gate_why_required(name),
                "proof_artifact": _gate_proof_artifact(root, name),
                "closure_action": owner_action_by_gate.get(name) or _gate_closure_action(name, wait),
                "pass_condition": _gate_pass_condition(name, wait),
                "verification_command": _gate_verification_command(name),
            }
        )
    return rows


def _gate_classification(name: str) -> dict[str, str]:
    if name in {"VPS selection", "Project owner approval"}:
        return {"category": "OWNER_DECISION", "owner": "Project owner"}
    if name in {"VPS latency evidence", "VPS first-day verification"}:
        return {"category": "OWNER_AFTER_VPS", "owner": "Project owner + operator"}
    if name in {"Active-market 72-hour soak", "Process/code-freeze 96-hour gate", "Measured cost model"}:
        return {"category": "WALL_CLOCK_EVIDENCE", "owner": "System clock + running collectors"}
    if name in {"Measured-cost revalidation", "Measured-cost assumption delta"}:
        return {"category": "SYSTEM_AFTER_COST_PASS", "owner": "Codex/operator after measured-cost PASS"}
    if name in {"Phase 1 acceptance", "Phase 1 review index"}:
        return {"category": "SYSTEM_VERIFICATION", "owner": "Codex/operator after objective gates mature"}
    return {"category": "READINESS_GATE", "owner": "Project"}


def _gate_proof_artifact(root: Path, name: str) -> str:
    report_dir = root / "outputs" / "reports"
    phase0_reports = root.parent / "xauusd-phase0" / "outputs" / "reports"
    docs = root / "docs"
    mapping = {
        "VPS selection": docs / "PHASE2_VPS_SELECTION_MATRIX.md",
        "VPS latency evidence": report_dir / "PHASE2_VPS_LATENCY_REPORT.md",
        "VPS first-day verification": report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md",
        "Measured cost model": phase0_reports / "MEASURED_COST_MODEL.md",
        "Measured-cost revalidation": phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md",
        "Measured-cost assumption delta": phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md",
        "Phase 1 acceptance": report_dir / "PHASE1_ACCEPTANCE_REPORT.md",
        "Phase 1 review index": report_dir / "PHASE1_REVIEW_INDEX.md",
        "Active-market 72-hour soak": report_dir / "PHASE1_SOAK_DRIFT_REPORT.md",
        "Process/code-freeze 96-hour gate": report_dir / "PHASE1_STATUS_SUMMARY.json",
        "Project owner approval": report_dir / "PHASE2_OWNER_APPROVAL.md",
    }
    return str(mapping.get(name, report_dir / "PHASE2_READINESS_REPORT.md"))


def _gate_why_required(name: str) -> str:
    reasons = {
        "VPS selection": (
            "Proves the paper/demo environment has an explicit owner-approved host, region, cost, "
            "backup, monitoring, and recovery plan before any remote runtime work begins."
        ),
        "VPS latency evidence": (
            "Proves the selected host can reach the broker endpoint with acceptable latency and no "
            "packet-loss evidence before paper-mode cost measurement depends on it."
        ),
        "VPS first-day verification": (
            "Proves the VPS can compile, run, log, recover, keep time, and refresh reports in the same "
            "dry-run-only posture as the local Phase 1 shell."
        ),
        "Measured cost model": (
            "Proves the strategy is being evaluated with fresh observed broker spread behavior, not "
            "legacy logs or assumptions."
        ),
        "Measured-cost revalidation": (
            "Proves the approved breakout-retest family still clears its economic floor after the "
            "fresh measured-cost model is applied."
        ),
        "Measured-cost assumption delta": (
            "Proves the gap between assumed and measured cost is understood before paper/demo work "
            "relies on the historical edge estimate."
        ),
        "Phase 1 acceptance": (
            "Proves the dry-run shell has survived the required runtime, safety, logging, soak, and "
            "permission-lock checks before any paper-mode implementation."
        ),
        "Phase 1 review index": (
            "Proves the reviewer packet points to current canonical artifacts and no required Phase 1 "
            "evidence is missing."
        ),
        "Active-market 72-hour soak": (
            "Proves the shell can observe live active-market bars continuously without unsafe rows, "
            "unexpected gaps, or restarts resetting the active-market streak."
        ),
        "Process/code-freeze 96-hour gate": (
            "Proves the deployed runtime and code have stayed stable long enough that acceptance is not "
            "being earned by a freshly changed or restarted system."
        ),
        "Project owner approval": (
            "Proves the owner has reviewed every objective PASS artifact and explicitly authorizes the "
            "next paper-only implementation step."
        ),
    }
    return reasons.get(name, "Proves the named readiness condition with its canonical evidence artifact.")


def _gate_closure_action(name: str, wait: dict[str, Any]) -> str:
    if name == "Measured cost model":
        return "Keep passive spread logger running until fresh observed market days reach the requirement."
    if name == "Measured-cost revalidation":
        return "After MEASURED_COST_MODEL.md is PASS, rerun measured-cost revalidation and periodic checks."
    if name == "Measured-cost assumption delta":
        return "After measured-cost revalidation is generated, rerun the measured-cost assumption delta report."
    if name == "Phase 1 acceptance":
        return "After soak/code-freeze gates pass, regenerate Phase 1 acceptance."
    if name == "Phase 1 review index":
        return "After Phase 1 acceptance passes, regenerate the review index."
    if name == "Active-market 72-hour soak":
        return "Keep Phase 1 dry-run running without restarts or unsafe rows until the active-market streak reaches 72h."
    if name == "Process/code-freeze 96-hour gate":
        return "Do not redeploy or modify runtime code; keep process and code-freeze clocks running to 96h."
    if name == "Project owner approval":
        return "Create/sign PHASE2_OWNER_APPROVAL.md only after every objective gate is PASS."
    if wait:
        return (
            f"Wait until {wait.get('gate', name)} reaches {wait.get('required', 'required')} "
            f"{wait.get('unit', '')}."
        )
    return "Close this gate in PHASE2_READINESS_REPORT.md using its required proof artifact."


def _gate_pass_condition(name: str, wait: dict[str, Any]) -> str:
    if wait:
        return (
            f"status=PASS with current at least {wait.get('required', 'required')} {wait.get('unit', '')}; "
            f"current={wait.get('current', 'n/a')}, remaining={wait.get('remaining', 'n/a')}."
        )
    conditions = {
        "VPS selection": "Decision record has no placeholders and PHASE2_VPS_SELECTION_DECISION_CHECK.md is PASS.",
        "VPS latency evidence": "PHASE2_VPS_LATENCY_REPORT.md is PASS with selected provider/region evidence.",
        "VPS first-day verification": "PHASE2_VPS_FIRST_DAY_VERIFICATION.md is PASS with verified NTP, backup, recovery, scheduler, MT5, compile, startup, log, health, and status evidence.",
        "Measured-cost revalidation": "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md is PASS after measured-cost model PASS.",
        "Measured-cost assumption delta": "MEASURED_COST_ASSUMPTION_DELTA.md is PASS after measured-cost model PASS.",
        "Phase 1 acceptance": "PHASE1_ACCEPTANCE_REPORT.md is PASS.",
        "Phase 1 review index": "PHASE1_REVIEW_INDEX.md is PASS.",
        "Project owner approval": "PHASE2_OWNER_APPROVAL.md exists only after objective gates pass and preserves paper-only/no-live/no-broker-execution boundary.",
    }
    return conditions.get(name, "Gate row is PASS in PHASE2_READINESS_REPORT.md.")


def _gate_verification_command(name: str) -> str:
    commands = {
        "VPS selection": (
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
            "scripts\\generate_phase2_vps_selection_decision_check.py"
        ),
        "VPS latency evidence": (
            ".\\scripts\\capture_phase2_vps_latency_evidence.ps1 "
            "-Provider PROVIDER -Region REGION -Endpoint BROKER_OR_MT5_ENDPOINT -SampleCount 20"
        ),
        "VPS first-day verification": (
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
            "scripts\\generate_phase2_vps_first_day_verification.py "
            "--files-dir C:\\MT5PortableGoldMission\\MQL5\\Files "
            "--compile-log C:\\MT5PortableGoldMission\\compile_Phase1DryRunShell.log "
            "--ntp-evidence outputs\\reports\\vps_ntp_sync.txt "
            "--backup-evidence outputs\\reports\\vps_backup_config.txt "
            "--recovery-evidence outputs\\reports\\vps_rdp_recovery.txt "
            "--scheduler-evidence outputs\\reports\\vps_periodic_task.txt"
        ),
        "Measured cost model": (
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
            "scripts\\run_phase1_periodic_checks.py "
            "--files-dir C:\\MT5PortableGoldMission\\MQL5\\Files "
            "--spread-files-dir C:\\MT5PortableSpreadLogger\\MQL5\\Files"
        ),
        "Measured-cost revalidation": (
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
            "scripts\\run_phase1_periodic_checks.py "
            "--files-dir C:\\MT5PortableGoldMission\\MQL5\\Files "
            "--spread-files-dir C:\\MT5PortableSpreadLogger\\MQL5\\Files"
        ),
        "Measured-cost assumption delta": (
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
            "scripts\\run_phase1_periodic_checks.py "
            "--files-dir C:\\MT5PortableGoldMission\\MQL5\\Files "
            "--spread-files-dir C:\\MT5PortableSpreadLogger\\MQL5\\Files"
        ),
        "Phase 1 acceptance": (
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
            "scripts\\run_phase1_periodic_checks.py "
            "--files-dir C:\\MT5PortableGoldMission\\MQL5\\Files "
            "--spread-files-dir C:\\MT5PortableSpreadLogger\\MQL5\\Files"
        ),
        "Phase 1 review index": (
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
            "scripts\\generate_phase1_review_index.py"
        ),
        "Active-market 72-hour soak": (
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
            "scripts\\run_phase1_periodic_checks.py "
            "--files-dir C:\\MT5PortableGoldMission\\MQL5\\Files "
            "--spread-files-dir C:\\MT5PortableSpreadLogger\\MQL5\\Files"
        ),
        "Process/code-freeze 96-hour gate": (
            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
            "scripts\\run_phase1_periodic_checks.py "
            "--files-dir C:\\MT5PortableGoldMission\\MQL5\\Files "
            "--spread-files-dir C:\\MT5PortableSpreadLogger\\MQL5\\Files"
        ),
        "Project owner approval": "No command before all objective gates pass; owner creates PHASE2_OWNER_APPROVAL.md.",
    }
    return commands.get(name, "Regenerate PHASE2_READINESS_REPORT.md through run_phase1_periodic_checks.py.")


def _owner_signature_actions(countdown: dict[str, Any], owner_packet: dict[str, Any]) -> list[dict[str, str]]:
    readiness = _mapping(owner_packet.get("owner_approval_readiness"))
    return [
        {
            "step": "verify_zero_pending_objective_gates",
            "status": str(readiness.get("status", "NOT_READY_TO_SIGN")),
            "action": "Owner may sign only after every objective gate except Project owner approval is PASS.",
        },
        {
            "step": "create_owner_approval_file",
            "status": "PENDING",
            "action": "Create PHASE2_OWNER_APPROVAL.md only after PHASE2_READINESS_REPORT.md is PASS.",
        },
        {
            "step": "keep_authorization_boundary",
            "status": "PASS" if countdown.get("paper_mode_authorized") is False else "FAIL",
            "action": "Do not implement paper mode or broker-side execution before owner approval and a separate implementation phase.",
        },
    ]


def _has_pending_wait_gates(wait_gates: list[dict[str, Any]]) -> bool:
    return any(str(gate.get("status", "")).upper() != "PASS" for gate in wait_gates)


def _to_float(value: Any) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 Demo Next Actions",
            "",
            AUTHORITY_NOTE,
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Summary",
            "",
            _table(
                [
                    ("Phase 2 readiness", str(payload.get("phase2_readiness_status", "UNKNOWN"))),
                    ("Phase 2 demo preflight", str(payload.get("phase2_demo_preflight_status", "UNKNOWN"))),
                    ("Demo countdown", str(payload.get("phase2_demo_countdown_status", "UNKNOWN"))),
                    ("Pending gates", str(payload.get("pending_gate_count", "UNKNOWN"))),
                    ("Paper mode authorized", str(payload.get("paper_mode_authorized", False)).lower()),
                    ("Demo trading authorized", str(payload.get("demo_trading_authorized", False)).lower()),
                    ("Broker execution authorized", str(payload.get("broker_execution_authorized", False)).lower()),
                    ("Live trading authorized", str(payload.get("live_trading_authorized", False)).lower()),
                ]
            ),
            "",
            "## Do Now",
            "",
            _rows_table(_mapping_rows(payload.get("do_now")), ["step", "status", "action"]),
            "",
            "## After VPS Is Provisioned",
            "",
            _rows_table(_mapping_rows(payload.get("after_vps_is_provisioned")), ["step", "status", "action"]),
            "",
            "## After Wait Gates Pass",
            "",
            _rows_table(_mapping_rows(payload.get("after_wait_gates_pass")), ["step", "status", "action"]),
            "",
            "## Earliest Gate Targets",
            "",
            _rows_table(
                _mapping_rows(payload.get("earliest_gate_targets")),
                ["gate", "status", "current", "remaining", "unit", "earliest_target_utc", "condition"],
            ),
            "",
            "## Gate Closure Map",
            "",
            _rows_table(
                _mapping_rows(payload.get("gate_closure_map")),
                [
                    "gate",
                    "status",
                    "category",
                    "owner",
                    "why_required",
                    "proof_artifact",
                    "closure_action",
                    "pass_condition",
                    "verification_command",
                ],
            ),
            "",
            "## Owner Signature Sequence",
            "",
            _rows_table(_mapping_rows(payload.get("owner_signature_sequence")), ["step", "status", "action"]),
            "",
            "## Wait Gates",
            "",
            _rows_table(_mapping_rows(payload.get("wait_gates")), ["gate", "status", "current", "required", "remaining", "unit"]),
            "",
            "## Forbidden Until Ready",
            "",
            _bullet_list([str(item) for item in payload.get("forbidden_until_ready", [])]),
            "",
        ]
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _mapping_rows(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else []


def _slug(value: str) -> str:
    return "_".join(part for part in value.lower().replace("-", " ").split() if part)


def _table(rows: list[tuple[str, str]]) -> str:
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _rows_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(str(row.get(column, ""))) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _bullet_list(rows: list[str]) -> str:
    return "\n".join(f"- {_escape(row)}" for row in rows) if rows else "- None."


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 2 demo next-actions report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_phase2_demo_next_actions_report(root=args.root, output_json=args.json)
    print(f"Phase 2 demo next actions: {output.status}")
    print(output.markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
