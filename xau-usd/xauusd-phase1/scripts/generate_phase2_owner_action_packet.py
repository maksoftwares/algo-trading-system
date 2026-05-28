from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_OWNER_ACTION_PACKET.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_OWNER_ACTION_PACKET.md"
AUTHORITY_NOTE = (
    "This packet is an owner handoff only. It does not authorize Phase 2, demo trading, "
    "broker execution, live capital, or any paper-mode implementation."
)


@dataclass(frozen=True)
class OwnerActionPacketOutput:
    status: str
    json_path: Path
    markdown_path: Path
    owner_action_count: int


def generate_phase2_owner_action_packet(root: Path, output_json: Path | None = None) -> OwnerActionPacketOutput:
    root = root.resolve()
    report_dir = root / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_REPORT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_REPORT_JSON.name else root / DEFAULT_REPORT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    countdown_path = report_dir / "PHASE2_DEMO_COUNTDOWN.json"
    readiness_path = report_dir / "PHASE2_READINESS_REPORT.md"
    first_day_path = report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md"
    preflight_path = report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md"
    vps_bootstrap_path = report_dir / "PHASE2_VPS_BOOTSTRAP_PACKET.md"
    vps_matrix_path = root / "docs" / "PHASE2_VPS_SELECTION_MATRIX.md"
    owner_draft_path = root / "docs" / "PHASE2_OWNER_APPROVAL_DRAFT.md"
    owner_live_path = report_dir / "PHASE2_OWNER_APPROVAL.md"

    countdown = _read_json(countdown_path)
    wait_gates = _wait_gates(countdown)
    readiness_gates = _read_gate_table(readiness_path)
    owner_actions = _owner_actions(countdown, readiness_gates)
    readiness_status = _read_markdown_status(readiness_path) or "UNKNOWN"
    preflight_status = _read_markdown_status(preflight_path) or "UNKNOWN"
    first_day_status = (
        _gate_status(readiness_gates, "VPS first-day verification")
        or _read_markdown_status(first_day_path)
        or "UNKNOWN"
    )
    vps_matrix_status = _gate_status(readiness_gates, "VPS selection") or _read_markdown_status(vps_matrix_path) or "UNKNOWN"
    vps_latency_status = _gate_status(readiness_gates, "VPS latency evidence") or "UNKNOWN"
    owner_live_status = _gate_status(readiness_gates, "Project owner approval") or (
        _read_markdown_status(owner_live_path) if owner_live_path.exists() else "MISSING"
    )

    checklist = _build_owner_checklist(
        root=root,
        owner_actions=owner_actions,
        wait_gates=wait_gates,
        readiness_status=readiness_status,
        first_day_status=first_day_status,
        vps_matrix_status=vps_matrix_status,
        owner_live_status=owner_live_status,
    )
    status = _packet_status(wait_gates, owner_actions, readiness_status, preflight_status, owner_live_status)
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": AUTHORITY_NOTE,
        "phase2_readiness_status": readiness_status,
        "phase2_demo_preflight_status": preflight_status,
        "vps_selection_status": vps_matrix_status,
        "vps_latency_status": vps_latency_status,
        "vps_first_day_verification_status": first_day_status,
        "owner_approval_status": owner_live_status,
        "paper_mode_authorized": False,
        "demo_trading_authorized": False,
        "broker_execution_authorized": False,
        "live_trading_authorized": False,
        "wait_gates": wait_gates,
        "owner_actions_now": owner_actions,
        "owner_checklist": checklist,
        "commands": _commands(),
        "owner_templates": {
            "vps_selection_decision": str(root / "docs" / "templates" / "phase2_vps_selection_decision.template.md"),
            "vps_ntp_sync": str(root / "docs" / "templates" / "vps_ntp_sync.template.txt"),
            "vps_backup_config": str(root / "docs" / "templates" / "vps_backup_config.template.txt"),
            "vps_rdp_recovery": str(root / "docs" / "templates" / "vps_rdp_recovery.template.txt"),
            "vps_periodic_task": str(root / "docs" / "templates" / "vps_periodic_task.template.txt"),
        },
        "source_reports": {
            "phase2_demo_countdown": str(countdown_path),
            "phase2_readiness": str(readiness_path),
            "phase2_demo_preflight": str(preflight_path),
            "phase2_vps_bootstrap": str(vps_bootstrap_path),
            "vps_first_day_verification": str(first_day_path),
            "vps_selection_matrix": str(vps_matrix_path),
            "owner_approval_draft": str(owner_draft_path),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return OwnerActionPacketOutput(status, output_json, output_md, len(owner_actions))


def _packet_status(
    wait_gates: list[dict[str, Any]],
    owner_actions: list[dict[str, Any]],
    readiness_status: str,
    preflight_status: str,
    owner_live_status: str,
) -> str:
    if readiness_status == "PASS" and preflight_status == "PASS" and owner_live_status == "PASS":
        return "PHASE2_OWNER_PACKET_COMPLETE"
    if owner_actions and any(gate.get("status") != "PASS" for gate in wait_gates):
        return "WAITING_AND_OWNER_ACTION_REQUIRED"
    if owner_actions:
        return "OWNER_ACTION_REQUIRED"
    if any(gate.get("status") != "PASS" for gate in wait_gates):
        return "WAIT_GATES_PENDING"
    return "READY_FOR_OWNER_APPROVAL_REVIEW"


def _build_owner_checklist(
    root: Path,
    owner_actions: list[dict[str, Any]],
    wait_gates: list[dict[str, Any]],
    readiness_status: str,
    first_day_status: str,
    vps_matrix_status: str,
    owner_live_status: str,
) -> list[dict[str, str]]:
    waiting = any(gate.get("status") != "PASS" for gate in wait_gates)
    actions = {str(item.get("gate", "")): str(item.get("status", "")) for item in owner_actions}
    return [
        {
            "step": "1",
            "title": "Keep local evidence collectors running",
            "status": "PENDING" if waiting else "PASS",
            "detail": "Do not stop the Phase 1 dry-run terminal or passive spread logger while wait gates mature.",
        },
        {
            "step": "2",
            "title": "Select VPS provider, region, and plan",
            "status": "PASS" if vps_matrix_status == "PASS" else "PENDING",
            "detail": "Fill the decision record in docs/PHASE2_VPS_SELECTION_MATRIX.md with provider, region, plan, backup, recovery, monitoring, and owner acceptance.",
        },
        {
            "step": "3",
            "title": "Capture VPS latency evidence",
            "status": "PASS" if actions.get("VPS latency evidence", "PASS") == "PASS" else "PENDING",
            "detail": "Run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root after the VPS is provisioned.",
        },
        {
            "step": "4",
            "title": "Fill first-day VPS verification evidence",
            "status": "PASS" if first_day_status == "PASS" else "PENDING",
            "detail": "Copy docs/templates/vps_*.template.txt into outputs/reports, fill verified keys, then regenerate PHASE2_VPS_FIRST_DAY_VERIFICATION.md.",
        },
        {
            "step": "5",
            "title": "Review objective Phase 2 readiness",
            "status": "PASS" if readiness_status == "PASS" else "PENDING",
            "detail": "Use outputs/reports/PHASE2_READINESS_REPORT.md as the sole readiness authority.",
        },
        {
            "step": "6",
            "title": "Sign owner approval only after all objective gates pass",
            "status": "PASS" if owner_live_status == "PASS" else "PENDING",
            "detail": f"Create {root / 'outputs' / 'reports' / 'PHASE2_OWNER_APPROVAL.md'} only after readiness is PASS.",
        },
    ]


def _commands() -> dict[str, str]:
    return {
        "refresh_readiness": (
            r"..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py "
            r"--files-dir C:\MT5PortableGoldMission\MQL5\Files "
            r"--spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files"
        ),
        "copy_vps_evidence_templates": (
            "Copy-Item docs\\templates\\vps_ntp_sync.template.txt outputs\\reports\\vps_ntp_sync.txt\n"
            "Copy-Item docs\\templates\\vps_backup_config.template.txt outputs\\reports\\vps_backup_config.txt\n"
            "Copy-Item docs\\templates\\vps_rdp_recovery.template.txt outputs\\reports\\vps_rdp_recovery.txt\n"
            "Copy-Item docs\\templates\\vps_periodic_task.template.txt outputs\\reports\\vps_periodic_task.txt"
        ),
        "generate_vps_first_day_verification": (
            r"..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_first_day_verification.py "
            r"--files-dir C:\MT5PortableGoldMission\MQL5\Files "
            r"--compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log "
            r"--scheduler-evidence outputs\reports\vps_periodic_task.txt"
        ),
        "capture_vps_latency": (
            r".\scripts\capture_phase2_vps_latency_evidence.ps1 "
            r'-Provider "<provider>" -Region "<region>" -Endpoint "<broker_or_mt5_endpoint>" -SampleCount 20'
        ),
        "install_periodic_checks_task_dry_run": (
            r".\scripts\install_phase2_periodic_checks_task.ps1 "
            r"-Phase1Root <phase1_root> "
            r"-PythonExe <phase0_python_exe> "
            r"-FilesDir <mt5_files_dir> "
            r"-SpreadFilesDir <spread_logger_files_dir> "
            r"-CompileLog <compile_log_path> "
            r"-IntervalMinutes 60 "
            r"-WhatIfOnly"
        ),
    }


def _owner_actions(countdown: dict[str, Any], readiness_gates: list[dict[str, str]]) -> list[dict[str, Any]]:
    value = countdown.get("owner_actions_now")
    if isinstance(value, list) and value:
        return value
    actions = []
    action_text = {
        "VPS selection": "Owner selects provider/region/plan from PHASE2_VPS_SELECTION_MATRIX.md.",
        "VPS latency evidence": "After VPS is provisioned, run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root.",
        "VPS first-day verification": "After VPS setup, capture NTP, backup, recovery-login, periodic scheduler, MT5 path, compile, startup, decision, and health evidence.",
        "Project owner approval": "Sign PHASE2_OWNER_APPROVAL.md only after all objective gates are PASS.",
    }
    for gate, action in action_text.items():
        status = _gate_status(readiness_gates, gate)
        if status and status != "PASS":
            actions.append({"gate": gate, "status": status, "action": action})
    return actions


def _wait_gates(countdown: dict[str, Any]) -> list[dict[str, Any]]:
    value = countdown.get("wait_gates")
    return value if isinstance(value, list) else []


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


def _read_gate_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    in_gates = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            in_gates = line.strip() == "## Gates"
            continue
        if not in_gates or not line.startswith("| ") or line.startswith("| ---") or line.startswith("| Gate |"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 3:
            rows.append({"Gate": parts[0], "Status": parts[1], "Evidence": parts[2]})
    return rows


def _gate_status(gates: list[dict[str, str]], gate: str) -> str:
    for row in gates:
        if row.get("Gate") == gate:
            return row.get("Status", "")
    return ""


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 Owner Action Packet",
            "",
            AUTHORITY_NOTE,
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authority",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Paper mode authorized | {str(payload['paper_mode_authorized']).lower()} |",
            f"| Demo trading authorized | {str(payload['demo_trading_authorized']).lower()} |",
            f"| Broker execution authorized | {str(payload['broker_execution_authorized']).lower()} |",
            f"| Live trading authorized | {str(payload['live_trading_authorized']).lower()} |",
            "",
            "## Current Status",
            "",
            _table(
                [
                    ("Phase 2 readiness", str(payload["phase2_readiness_status"])),
                    ("Phase 2 demo preflight", str(payload["phase2_demo_preflight_status"])),
                    ("VPS selection", str(payload["vps_selection_status"])),
                    ("VPS latency", str(payload["vps_latency_status"])),
                    ("VPS first-day verification", str(payload["vps_first_day_verification_status"])),
                    ("Owner approval", str(payload["owner_approval_status"])),
                ]
            ),
            "",
            "## Wait Gates",
            "",
            _rows_table(payload["wait_gates"], ["gate", "status", "current", "required", "remaining", "unit"]),
            "",
            "## Owner Checklist",
            "",
            _rows_table(payload["owner_checklist"], ["step", "title", "status", "detail"]),
            "",
            "## Immediate Owner Actions",
            "",
            _rows_table(payload["owner_actions_now"], ["gate", "status", "action"]),
            "",
            "## Commands",
            "",
            _commands_markdown(payload["commands"]),
            "",
            "## Owner Templates",
            "",
            _rows_table(
                [{"template": key, "path": value} for key, value in payload["owner_templates"].items()],
                ["template", "path"],
            ),
            "",
            "## Source Reports",
            "",
            _rows_table(
                [{"report": key, "path": value} for key, value in payload["source_reports"].items()],
                ["report", "path"],
            ),
            "",
        ]
    )


def _commands_markdown(commands: dict[str, str]) -> str:
    blocks = []
    for name, command in commands.items():
        blocks.extend([f"### {name}", "", "```powershell", command, "```", ""])
    return "\n".join(blocks).rstrip()


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


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 2 owner action packet.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_phase2_owner_action_packet(root=args.root, output_json=args.json)
    print(f"Phase 2 owner action packet: {output.status}")
    print(output.markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
