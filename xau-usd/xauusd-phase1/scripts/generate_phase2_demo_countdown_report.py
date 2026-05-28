from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_COUNTDOWN.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_DEMO_COUNTDOWN.md"
PHASE2_AUTHORITY_SENTENCE = (
    "This report is a countdown aid only. "
    "PHASE2_READINESS_REPORT.md remains the sole real readiness authority."
)


@dataclass(frozen=True)
class CountdownOutput:
    status: str
    json_path: Path
    markdown_path: Path
    pending_gate_count: int


def generate_phase2_demo_countdown_report(root: Path, output_json: Path | None = None) -> CountdownOutput:
    root = root.resolve()
    report_dir = root / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_REPORT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_REPORT_JSON.name else root / DEFAULT_REPORT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    readiness_path = report_dir / "PHASE2_READINESS_REPORT.md"
    acceptance_path = report_dir / "PHASE1_ACCEPTANCE_REPORT.md"
    summary_path = report_dir / "PHASE1_STATUS_SUMMARY.json"
    measured_cost_path = root.parent / "xauusd-phase0" / "outputs" / "reports" / "MEASURED_COST_MODEL.md"
    revalidation_path = root.parent / "xauusd-phase0" / "outputs" / "reports" / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md"
    delta_path = root.parent / "xauusd-phase0" / "outputs" / "reports" / "MEASURED_COST_ASSUMPTION_DELTA.md"

    summary = _read_json(summary_path)
    soak = _mapping(summary.get("soak"))
    gates = _read_gate_table(readiness_path)
    measured = _read_measured_cost_coverage(measured_cost_path)
    pending_gates = [row for row in gates if row.get("Status") != "PASS"]
    wait_gates = _wait_gates(soak, measured, gates)
    owner_actions = _owner_actions(gates)
    status = "DEMO_READY_TO_REQUEST_OWNER_APPROVAL" if not pending_gates else "DEMO_NOT_READY"
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": PHASE2_AUTHORITY_SENTENCE,
        "boundary": "paper_mode_not_authorized_until_phase2_readiness_pass",
        "paper_mode_authorized": False,
        "broker_execution_authorized": False,
        "live_trading_authorized": False,
        "phase2_readiness_status": _read_markdown_status(readiness_path) or "UNKNOWN",
        "phase1_acceptance_status": _read_markdown_status(acceptance_path) or "UNKNOWN",
        "measured_cost_status": _read_markdown_status(measured_cost_path) or "UNKNOWN",
        "measured_cost_revalidation_status": _read_markdown_status(revalidation_path) or "UNKNOWN",
        "measured_cost_delta_status": _read_markdown_status(delta_path) or "UNKNOWN",
        "pending_gate_count": len(pending_gates),
        "pending_gates": pending_gates,
        "wait_gates": wait_gates,
        "owner_actions_now": owner_actions,
        "runtime_snapshot": {
            "decision_rows": _mapping(summary.get("runtime")).get("decision_rows", "UNKNOWN"),
            "latest_bar": _mapping(_mapping(summary.get("runtime")).get("latest_row")).get("bar_time", "UNKNOWN"),
            "dry_run": _mapping(_mapping(summary.get("runtime")).get("latest_row")).get("dry_run", "UNKNOWN"),
            "trade_permission": _mapping(_mapping(summary.get("runtime")).get("latest_row")).get(
                "trade_permission",
                "UNKNOWN",
            ),
            "server_time_status": _mapping(_mapping(summary.get("runtime")).get("latest_row")).get(
                "server_time_status",
                "UNKNOWN",
            ),
        },
        "measured_cost_coverage": measured,
        "forbidden_until_ready": [
            "paper-mode implementation",
            "MT5 runtime redeployment for trading behavior",
            "broker-side execution paths",
            "live capital",
            "treating Phase 3 experimental PASS as Phase 2 readiness",
        ],
        "next_refresh_command": (
            r".\xau-usd\xauusd-phase0\.venv\Scripts\python.exe "
            r"xau-usd\xauusd-phase1\scripts\run_phase1_periodic_checks.py "
            r"--files-dir C:\MT5PortableGoldMission\MQL5\Files "
            r"--spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files"
        ),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return CountdownOutput(status, output_json, output_md, len(pending_gates))


def _wait_gates(soak: dict[str, Any], measured: dict[str, Any], gates: list[dict[str, str]]) -> list[dict[str, Any]]:
    active_required = _to_float(soak.get("required_uninterrupted_streak_hours")) or 72.0
    active_current = _to_float(soak.get("current_streak_hours")) or 0.0
    freeze_required = _to_float(soak.get("required_code_freeze_hours")) or 96.0
    freeze_current = _to_float(soak.get("code_freeze_hours")) or 0.0
    measured_days = _to_float(measured.get("observed_days")) or 0.0
    required_days = _to_float(measured.get("required_days")) or 5.0
    return [
        {
            "gate": "Active-market 72-hour soak",
            "status": _gate_status(gates, "Active-market 72-hour soak"),
            "current": round(active_current, 2),
            "required": round(active_required, 2),
            "remaining": round(max(active_required - active_current, 0.0), 2),
            "unit": "hours",
        },
        {
            "gate": "Process/code-freeze 96-hour gate",
            "status": _gate_status(gates, "Process/code-freeze 96-hour gate"),
            "current": round(freeze_current, 2),
            "required": round(freeze_required, 2),
            "remaining": round(max(freeze_required - freeze_current, 0.0), 2),
            "unit": "hours",
        },
        {
            "gate": "Measured cost model",
            "status": _gate_status(gates, "Measured cost model"),
            "current": measured_days,
            "required": required_days,
            "remaining": max(required_days - measured_days, 0),
            "unit": "fresh_market_days",
        },
    ]


def _owner_actions(gates: list[dict[str, str]]) -> list[dict[str, str]]:
    actions = []
    for gate in ("VPS selection", "VPS latency evidence", "Project owner approval"):
        status = _gate_status(gates, gate)
        if status == "PASS":
            continue
        action = {
            "VPS selection": "Owner selects provider/region/plan from PHASE2_VPS_SELECTION_MATRIX.md.",
            "VPS latency evidence": "After VPS is provisioned, run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root.",
            "Project owner approval": "Sign PHASE2_OWNER_APPROVAL.md only after all objective gates are PASS.",
        }[gate]
        actions.append({"gate": gate, "status": status, "action": action})
    return actions


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 Demo Countdown",
            "",
            PHASE2_AUTHORITY_SENTENCE,
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Gate Summary",
            "",
            _table(
                [
                    ("Phase 2 readiness", str(payload.get("phase2_readiness_status", "UNKNOWN"))),
                    ("Phase 1 acceptance", str(payload.get("phase1_acceptance_status", "UNKNOWN"))),
                    ("Measured cost model", str(payload.get("measured_cost_status", "UNKNOWN"))),
                    ("Measured-cost revalidation", str(payload.get("measured_cost_revalidation_status", "UNKNOWN"))),
                    ("Measured-cost delta", str(payload.get("measured_cost_delta_status", "UNKNOWN"))),
                    ("Paper mode authorized", str(payload.get("paper_mode_authorized", False)).lower()),
                    ("Broker execution authorized", str(payload.get("broker_execution_authorized", False)).lower()),
                    ("Live trading authorized", str(payload.get("live_trading_authorized", False)).lower()),
                    ("Pending gates", str(payload.get("pending_gate_count", "UNKNOWN"))),
                ]
            ),
            "",
            "## Wait Gates",
            "",
            _rows_table(
                _mapping_rows(payload.get("wait_gates")),
                ["gate", "status", "current", "required", "remaining", "unit"],
            ),
            "",
            "## Owner Actions",
            "",
            _rows_table(_mapping_rows(payload.get("owner_actions_now")), ["gate", "status", "action"]),
            "",
            "## Runtime Snapshot",
            "",
            _table([(key, str(value)) for key, value in _mapping(payload.get("runtime_snapshot")).items()]),
            "",
            "## Forbidden Until Ready",
            "",
            _bullet_list([str(item) for item in payload.get("forbidden_until_ready", [])]),
            "",
            "## Refresh Command",
            "",
            "```powershell",
            str(payload.get("next_refresh_command", "")),
            "```",
            "",
        ]
    )


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
        if len(parts) < 3:
            continue
        rows.append({"Gate": parts[0], "Status": parts[1], "Evidence": parts[2]})
    return rows


def _read_measured_cost_coverage(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"status": _read_markdown_status(path) or "UNKNOWN"}
    if not path.exists():
        return result
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("|") or "Observed Rows" not in line or "Observed Days" not in line:
            continue
        if index + 2 >= len(lines):
            break
        headers = [part.strip().lower().replace(" ", "_") for part in line.strip("|").split("|")]
        values = [part.strip() for part in lines[index + 2].strip("|").split("|")]
        result.update(dict(zip(headers, values)))
        break
    return result


def _gate_status(gates: list[dict[str, str]], gate: str) -> str:
    for row in gates:
        if row.get("Gate") == gate:
            return row.get("Status", "UNKNOWN")
    return "UNKNOWN"


def _read_markdown_status(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _mapping_rows(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else []


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _table(rows: list[tuple[str, str]]) -> str:
    body = [f"| {_escape(key)} | {_escape(value)} |" for key, value in rows]
    return "\n".join(["| Field | Value |", "| --- | --- |", *body])


def _rows_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "None."
    output = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        output.append("| " + " | ".join(_escape(row.get(column, "")) for column in columns) + " |")
    return "\n".join(output)


def _bullet_list(rows: list[str]) -> str:
    return "\n".join(f"- {_escape(row)}" for row in rows) if rows else "- None."


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2 demo readiness countdown report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_phase2_demo_countdown_report(args.root, args.output_json)
    print(f"Phase 2 demo countdown: {output.status}")
    print(output.markdown_path)
    print(f"Pending gates: {output.pending_gate_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
