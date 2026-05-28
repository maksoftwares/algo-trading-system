from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_VPS_BOOTSTRAP_PACKET.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_VPS_BOOTSTRAP_PACKET.md"
AUTHORITY_NOTE = (
    "This packet is an operational VPS bootstrap handoff only. It does not authorize Phase 2, "
    "demo trading, broker execution, live capital, or paper-mode implementation."
)


@dataclass(frozen=True)
class VpsBootstrapPacketOutput:
    status: str
    json_path: Path
    markdown_path: Path
    phase_count: int


def generate_phase2_vps_bootstrap_packet(root: Path, output_json: Path | None = None) -> VpsBootstrapPacketOutput:
    root = root.resolve()
    report_dir = root / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_REPORT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_REPORT_JSON.name else root / DEFAULT_REPORT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    countdown_path = report_dir / "PHASE2_DEMO_COUNTDOWN.json"
    owner_packet_path = report_dir / "PHASE2_OWNER_ACTION_PACKET.json"
    readiness_path = report_dir / "PHASE2_READINESS_REPORT.md"
    preflight_path = report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md"
    vps_first_day_path = report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md"
    vps_latency_path = report_dir / "PHASE2_VPS_LATENCY_REPORT.md"
    local_network_baseline_path = report_dir / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md"
    status_summary_path = report_dir / "PHASE1_STATUS_SUMMARY.json"
    vps_matrix_path = root / "docs" / "PHASE2_VPS_SELECTION_MATRIX.md"

    countdown = _read_json(countdown_path)
    owner_packet = _read_json(owner_packet_path)
    readiness_gates = _read_gate_table(readiness_path)
    wait_gates = _mapping_rows(countdown.get("wait_gates"))
    owner_actions = _owner_actions(countdown, owner_packet, readiness_gates)
    source_status = {
        "phase2_readiness": _read_markdown_status(readiness_path) or "UNKNOWN",
        "phase2_demo_preflight": _read_markdown_status(preflight_path) or "UNKNOWN",
        "phase2_demo_countdown": str(countdown.get("status") or "UNKNOWN"),
        "phase2_owner_action_packet": str(owner_packet.get("status") or "UNKNOWN"),
        "vps_selection": _gate_status(readiness_gates, "VPS selection")
        or _read_markdown_status(vps_matrix_path)
        or "UNKNOWN",
        "vps_latency": _gate_status(readiness_gates, "VPS latency evidence")
        or _read_markdown_status(vps_latency_path)
        or "UNKNOWN",
        "vps_first_day_verification": _gate_status(readiness_gates, "VPS first-day verification")
        or _read_markdown_status(vps_first_day_path)
        or "UNKNOWN",
        "project_owner_approval": _gate_status(readiness_gates, "Project owner approval") or "UNKNOWN",
    }
    status = _packet_status(
        wait_gates=wait_gates,
        owner_actions=owner_actions,
        readiness_status=source_status["phase2_readiness"],
        preflight_status=source_status["phase2_demo_preflight"],
        owner_approval_status=source_status["project_owner_approval"],
    )
    phases = _bootstrap_phases(root)
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": AUTHORITY_NOTE,
        "paper_mode_authorized": False,
        "demo_trading_authorized": False,
        "broker_execution_authorized": False,
        "live_trading_authorized": False,
        "source_status": source_status,
        "wait_gates": wait_gates,
        "owner_actions_now": owner_actions,
        "runtime_snapshot": _runtime_snapshot(_read_json(status_summary_path), countdown),
        "local_mt5_network_baseline": _read_network_baseline(local_network_baseline_path),
        "bootstrap_phases": phases,
        "commands": _commands(),
        "evidence_paths": _evidence_paths(root),
        "source_reports": {
            "phase2_demo_countdown": str(countdown_path),
            "phase2_owner_action_packet": str(owner_packet_path),
            "phase2_readiness": str(readiness_path),
            "phase2_demo_preflight": str(preflight_path),
            "vps_selection_matrix": str(vps_matrix_path),
            "vps_latency_report": str(vps_latency_path),
            "local_mt5_network_baseline": str(local_network_baseline_path),
            "vps_first_day_verification": str(vps_first_day_path),
            "phase1_status_summary": str(status_summary_path),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return VpsBootstrapPacketOutput(status, output_json, output_md, len(phases))


def _packet_status(
    wait_gates: list[dict[str, Any]],
    owner_actions: list[dict[str, Any]],
    readiness_status: str,
    preflight_status: str,
    owner_approval_status: str,
) -> str:
    if readiness_status == "PASS" and preflight_status == "PASS" and owner_approval_status == "PASS":
        return "VPS_BOOTSTRAP_COMPLETE"
    setup_actions = [action for action in owner_actions if action.get("gate") != "Project owner approval"]
    if setup_actions and any(gate.get("status") != "PASS" for gate in wait_gates):
        return "WAITING_AND_VPS_BOOTSTRAP_PENDING"
    if setup_actions:
        return "VPS_BOOTSTRAP_ACTION_REQUIRED"
    if any(gate.get("status") != "PASS" for gate in wait_gates):
        return "WAIT_GATES_PENDING"
    return "READY_FOR_OWNER_APPROVAL_REVIEW"


def _owner_actions(
    countdown: dict[str, Any],
    owner_packet: dict[str, Any],
    readiness_gates: list[dict[str, str]],
) -> list[dict[str, Any]]:
    actions = _mapping_rows(countdown.get("owner_actions_now")) or _mapping_rows(owner_packet.get("owner_actions_now"))
    if actions:
        return actions
    action_text = {
        "VPS selection": "Owner selects provider/region/plan from PHASE2_VPS_SELECTION_MATRIX.md.",
        "VPS latency evidence": "After VPS is provisioned, run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root.",
        "VPS first-day verification": "After VPS setup, capture NTP, backup, recovery-login, periodic scheduler, MT5 path, compile, startup, decision, and health evidence.",
        "Project owner approval": "Sign PHASE2_OWNER_APPROVAL.md only after all objective gates are PASS.",
    }
    derived: list[dict[str, Any]] = []
    for gate, action in action_text.items():
        status = _gate_status(readiness_gates, gate)
        if status and status != "PASS":
            derived.append({"gate": gate, "status": status, "action": action})
    return derived


def _bootstrap_phases(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "phase": "Before VPS Purchase",
            "objective": "Choose the VPS without touching the local MT5 runtime.",
            "steps": [
                "Keep the local Phase 1 dry-run shell and passive spread logger running.",
                "Fill docs/PHASE2_VPS_SELECTION_MATRIX.md with provider, region, plan, backup, recovery, monitoring, and owner decision fields.",
                "Do not create PHASE2_OWNER_APPROVAL.md until PHASE2_READINESS_REPORT.md is PASS.",
            ],
            "evidence": [
                str(root / "docs" / "PHASE2_VPS_SELECTION_MATRIX.md"),
                str(root / "docs" / "templates" / "phase2_vps_selection_decision.template.md"),
            ],
        },
        {
            "phase": "On VPS First Login",
            "objective": "Capture environment and latency evidence before any paper-mode work.",
            "steps": [
                "Clone or copy the repository to the VPS and keep secrets out of tracked files.",
                "Install or copy MT5 Portable in dry-run configuration only.",
                "Run the 20-sample latency capture against the broker or MT5 endpoint.",
                "Run scripts/prepare_phase2_vps_evidence_workspace.ps1 to create pending evidence files without overwriting verified evidence.",
                "Copy the NTP, backup, RDP recovery, and periodic-task templates into outputs/reports and fill only verified values.",
            ],
            "evidence": [
                str(root / "outputs" / "reports" / "PHASE2_VPS_LATENCY_REPORT.md"),
                str(root / "outputs" / "reports" / "vps_ntp_sync.txt"),
                str(root / "outputs" / "reports" / "vps_backup_config.txt"),
                str(root / "outputs" / "reports" / "vps_rdp_recovery.txt"),
                str(root / "outputs" / "reports" / "vps_periodic_task.txt"),
            ],
        },
        {
            "phase": "After MT5 Dry-Run Deploy",
            "objective": "Prove the VPS can run the dry-run shell safely before demo trading exists.",
            "steps": [
                "Compile the Phase 1 dry-run shell and preserve the compile log.",
                "Start MT5 with dry_run=true and trade_permission=false.",
                "Confirm decision_log.csv receives rows and the dashboard/runtime health remain green.",
                "Generate PHASE2_VPS_FIRST_DAY_VERIFICATION.md from VPS evidence.",
            ],
            "evidence": [
                "C:\\MT5PortableGoldMission\\compile_Phase1DryRunShell.log",
                "C:\\MT5PortableGoldMission\\MQL5\\Files\\decision_log.csv",
                str(root / "outputs" / "reports" / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md"),
            ],
        },
        {
            "phase": "Before Owner Approval",
            "objective": "Confirm objective gates before any paper-mode implementation.",
            "steps": [
                "Run scripts/run_phase1_periodic_checks.py with the VPS MT5 Files directory and passive spread Files directory.",
                "Install or verify the Windows Task Scheduler entry for periodic checks.",
                "Verify PHASE2_READINESS_REPORT.md and PHASE2_DEMO_PREFLIGHT_REPORT.md are PASS.",
                "Verify PHASE2_DEMO_COUNTDOWN.md has zero pending gates.",
                "Only then create outputs/reports/PHASE2_OWNER_APPROVAL.md.",
            ],
            "evidence": [
                str(root / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md"),
                str(root / "outputs" / "reports" / "PHASE2_DEMO_PREFLIGHT_REPORT.md"),
                str(root / "outputs" / "reports" / "PHASE2_DEMO_COUNTDOWN.md"),
                str(root / "outputs" / "reports" / "PHASE2_OWNER_APPROVAL.md"),
                str(root / "scripts" / "install_phase2_periodic_checks_task.ps1"),
            ],
        },
    ]


def _commands() -> dict[str, str]:
    return {
        "refresh_local_readiness": (
            r"..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py "
            r"--files-dir C:\MT5PortableGoldMission\MQL5\Files "
            r"--spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files"
        ),
        "capture_vps_latency": (
            r".\scripts\capture_phase2_vps_latency_evidence.ps1 "
            r'-Provider "<provider>" -Region "<region>" -Endpoint "<broker_or_mt5_endpoint>" -SampleCount 20'
        ),
        "copy_vps_evidence_templates": (
            "Copy-Item docs\\templates\\vps_ntp_sync.template.txt outputs\\reports\\vps_ntp_sync.txt\n"
            "Copy-Item docs\\templates\\vps_backup_config.template.txt outputs\\reports\\vps_backup_config.txt\n"
            "Copy-Item docs\\templates\\vps_rdp_recovery.template.txt outputs\\reports\\vps_rdp_recovery.txt\n"
            "Copy-Item docs\\templates\\vps_periodic_task.template.txt outputs\\reports\\vps_periodic_task.txt"
        ),
        "prepare_vps_evidence_workspace": (
            r".\scripts\prepare_phase2_vps_evidence_workspace.ps1 "
            r"-Phase1Root <phase1_root>"
        ),
        "generate_vps_first_day_verification": (
            r"..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_first_day_verification.py "
            r"--files-dir C:\MT5PortableGoldMission\MQL5\Files "
            r"--compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log "
            r"--scheduler-evidence outputs\reports\vps_periodic_task.txt"
        ),
        "generate_bootstrap_packet": (
            r"..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_bootstrap_packet.py"
        ),
        "install_periodic_checks_task": (
            r".\scripts\install_phase2_periodic_checks_task.ps1 "
            r"-Phase1Root <phase1_root> "
            r"-PythonExe <phase0_python_exe> "
            r"-FilesDir <mt5_files_dir> "
            r"-SpreadFilesDir <spread_logger_files_dir> "
            r"-CompileLog <compile_log_path> "
            r"-IntervalMinutes 60 "
            r"-Provider <selected_provider> "
            r"-Region <selected_region> "
            r"-WriteEvidence "
            r"-WhatIfOnly"
        ),
    }


def _evidence_paths(root: Path) -> dict[str, str]:
    return {
        "vps_selection_matrix": str(root / "docs" / "PHASE2_VPS_SELECTION_MATRIX.md"),
        "vps_selection_decision_template": str(root / "docs" / "templates" / "phase2_vps_selection_decision.template.md"),
        "vps_latency_report": str(root / "outputs" / "reports" / "PHASE2_VPS_LATENCY_REPORT.md"),
        "local_mt5_network_baseline": str(root / "outputs" / "reports" / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md"),
        "vps_first_day_verification": str(root / "outputs" / "reports" / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md"),
        "phase2_readiness": str(root / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md"),
        "phase2_owner_approval": str(root / "outputs" / "reports" / "PHASE2_OWNER_APPROVAL.md"),
    }


def _runtime_snapshot(summary: dict[str, Any], countdown: dict[str, Any]) -> dict[str, Any]:
    countdown_snapshot = _mapping(countdown.get("runtime_snapshot"))
    latest = _mapping(_mapping(summary.get("runtime")).get("latest_row"))
    return {
        "decision_rows": _mapping(summary.get("runtime")).get(
            "decision_rows",
            countdown_snapshot.get("decision_rows", "UNKNOWN"),
        ),
        "latest_bar": latest.get("bar_time", countdown_snapshot.get("latest_bar", "UNKNOWN")),
        "dry_run": latest.get("dry_run", countdown_snapshot.get("dry_run", "UNKNOWN")),
        "trade_permission": latest.get("trade_permission", countdown_snapshot.get("trade_permission", "UNKNOWN")),
        "server_time_status": latest.get(
            "server_time_status",
            countdown_snapshot.get("server_time_status", "UNKNOWN"),
        ),
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 VPS Bootstrap Packet",
            "",
            AUTHORITY_NOTE,
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authority",
            "",
            _table(
                [
                    ("Paper mode authorized", str(payload["paper_mode_authorized"]).lower()),
                    ("Demo trading authorized", str(payload["demo_trading_authorized"]).lower()),
                    ("Broker execution authorized", str(payload["broker_execution_authorized"]).lower()),
                    ("Live trading authorized", str(payload["live_trading_authorized"]).lower()),
                ]
            ),
            "",
            "## Source Status",
            "",
            _table([(key, str(value)) for key, value in payload["source_status"].items()]),
            "",
            "## Runtime Snapshot",
            "",
            _table([(key, str(value)) for key, value in payload["runtime_snapshot"].items()]),
            "",
            "## Local MT5 Network Baseline",
            "",
            _table([(key, str(value)) for key, value in payload["local_mt5_network_baseline"].items()]),
            "",
            "## Wait Gates",
            "",
            _rows_table(payload["wait_gates"], ["gate", "status", "current", "required", "remaining", "unit"]),
            "",
            "## Owner Actions Now",
            "",
            _rows_table(payload["owner_actions_now"], ["gate", "status", "action"]),
            "",
            "## Bootstrap Phases",
            "",
            _phases_markdown(payload["bootstrap_phases"]),
            "",
            "## Commands",
            "",
            _commands_markdown(payload["commands"]),
            "",
            "## Evidence Paths",
            "",
            _rows_table(
                [{"evidence": key, "path": value} for key, value in payload["evidence_paths"].items()],
                ["evidence", "path"],
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


def _phases_markdown(phases: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for phase in phases:
        sections.extend(
            [
                f"### {phase['phase']}",
                "",
                str(phase["objective"]),
                "",
                "Steps:",
                _bullet_list([str(item) for item in phase["steps"]]),
                "",
                "Evidence:",
                _bullet_list([str(item) for item in phase["evidence"]]),
                "",
            ]
        )
    return "\n".join(sections).rstrip()


def _commands_markdown(commands: dict[str, str]) -> str:
    blocks = []
    for name, command in commands.items():
        blocks.extend([f"### {name}", "", "```powershell", command, "```", ""])
    return "\n".join(blocks).rstrip()


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


def _read_network_baseline(path: Path) -> dict[str, str]:
    baseline = {"status": _read_markdown_status(path) or "MISSING"}
    if not path.exists():
        return baseline
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("| Samples | Latest Ping | Median Ping | Best Ping | Worst Ping | Latest Access Point |"):
            if index + 2 >= len(lines):
                break
            values = [part.strip() for part in lines[index + 2].strip("|").split("|")]
            if len(values) >= 6:
                baseline.update(
                    {
                        "samples": values[0],
                        "latest_ping": values[1],
                        "median_ping": values[2],
                        "best_ping": values[3],
                        "worst_ping": values[4],
                        "latest_access_point": values[5],
                    }
                )
            break
    return baseline


def _gate_status(gates: list[dict[str, str]], gate: str) -> str:
    for row in gates:
        if row.get("Gate") == gate:
            return row.get("Status", "")
    return ""


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _mapping_rows(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else []


def _table(rows: list[tuple[str, str]]) -> str:
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _rows_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    output = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        output.append("| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def _bullet_list(rows: list[str]) -> str:
    return "\n".join(f"- {_escape(row)}" for row in rows) if rows else "- None."


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 2 VPS bootstrap packet.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_phase2_vps_bootstrap_packet(root=args.root, output_json=args.json)
    print(f"Phase 2 VPS bootstrap packet: {output.status}")
    print(output.markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
