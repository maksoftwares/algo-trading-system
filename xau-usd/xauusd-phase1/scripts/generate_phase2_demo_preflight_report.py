from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_phase1_safety import audit_phase1_tree


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_PREFLIGHT.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_DEMO_PREFLIGHT_REPORT.md"


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    status: str
    evidence: str


@dataclass(frozen=True)
class PreflightOutput:
    status: str
    json_path: Path
    markdown_path: Path
    checks: tuple[PreflightCheck, ...]


def generate_phase2_demo_preflight_report(root: Path, output_json: Path | None = None) -> PreflightOutput:
    root = root.resolve()
    output_json = (output_json or root / DEFAULT_REPORT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_REPORT_JSON.name else root / DEFAULT_REPORT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    report_dir = root / "outputs" / "reports"
    readiness_path = report_dir / "PHASE2_READINESS_REPORT.md"
    countdown_path = report_dir / "PHASE2_DEMO_COUNTDOWN.json"
    summary_path = report_dir / "PHASE1_STATUS_SUMMARY.json"
    phase3_status_path = root.parent / "xauusd-phase3-experimental" / "outputs" / "reports" / "PHASE3_EXPERIMENTAL_STATUS.json"
    local_mt5_network_baseline_path = report_dir / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md"

    readiness_status = _read_markdown_status(readiness_path)
    readiness_gates = _read_gate_table(readiness_path)
    countdown = _read_json(countdown_path)
    summary = _read_json(summary_path)
    phase3_status = _read_json(phase3_status_path)
    latest = _mapping(_mapping(summary.get("runtime")).get("latest_row"))

    checks = [
        _status_check("phase2_readiness", readiness_status, "PASS", readiness_path),
        _gate_check(readiness_gates, "Project owner approval"),
        _gate_check(readiness_gates, "VPS selection"),
        _gate_check(readiness_gates, "VPS latency evidence"),
        _gate_check(readiness_gates, "VPS first-day verification"),
        _countdown_check(countdown, countdown_path),
        _latest_boundary_check(latest, summary_path),
        _countdown_authority_boundary_check(countdown, countdown_path),
        _demo_account_isolation_check(local_mt5_network_baseline_path),
        _phase3_separation_check(phase3_status, phase3_status_path),
        _safety_check(root),
    ]
    status = _overall_status(checks)
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "paper_mode_implementation_authorized": status == "PASS",
        "demo_trading_authorized": False,
        "live_trading_authorized": False,
        "boundary": "preflight_allows_phase2_paper_mode_implementation_only_when_pass",
        "checks": [check.__dict__ for check in checks],
        "source_reports": {
            "phase2_readiness": str(readiness_path),
            "phase2_demo_countdown": str(countdown_path),
            "phase1_status_summary": str(summary_path),
            "phase3_experimental_status": str(phase3_status_path),
            "local_mt5_network_baseline": str(local_mt5_network_baseline_path),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return PreflightOutput(status, output_json, output_md, tuple(checks))


def _status_check(name: str, observed: str, required: str, path: Path) -> PreflightCheck:
    if observed == required:
        return PreflightCheck(name, "PASS", f"`{path}` status is {observed}.")
    if observed in {"PENDING", "WARN", "REVIEW", ""}:
        return PreflightCheck(name, "PENDING", f"`{path}` status is {observed or 'missing'}; required {required}.")
    return PreflightCheck(name, "FAIL", f"`{path}` status is {observed}; required {required}.")


def _gate_check(gates: list[dict[str, str]], gate: str) -> PreflightCheck:
    row = next((item for item in gates if item.get("Gate") == gate), None)
    if row is None:
        return PreflightCheck(gate, "PENDING", f"Gate `{gate}` is missing from PHASE2_READINESS_REPORT.md.")
    status = row.get("Status", "")
    if status == "PASS":
        return PreflightCheck(gate, "PASS", row.get("Evidence", "Gate passed."))
    if status in {"PENDING", "WARN", "REVIEW", ""}:
        return PreflightCheck(gate, "PENDING", row.get("Evidence", f"Gate status is {status or 'missing'}."))
    return PreflightCheck(gate, "FAIL", row.get("Evidence", f"Gate status is {status}."))


def _countdown_check(countdown: dict[str, Any], path: Path) -> PreflightCheck:
    pending_count = _to_int(countdown.get("pending_gate_count"))
    status = str(countdown.get("status", ""))
    if pending_count == 0 and status == "DEMO_READY_TO_REQUEST_OWNER_APPROVAL":
        return PreflightCheck("demo_countdown", "PASS", f"`{path}` has zero pending gates and status {status}.")
    if pending_count is None:
        return PreflightCheck("demo_countdown", "PENDING", f"`{path}` is missing pending_gate_count.")
    if pending_count == 0:
        return PreflightCheck(
            "demo_countdown",
            "FAIL",
            f"`{path}` has zero pending gates but unexpected status {status or 'missing'}; required DEMO_READY_TO_REQUEST_OWNER_APPROVAL.",
        )
    return PreflightCheck(
        "demo_countdown",
        "PENDING",
        f"`{path}` status is {status or 'missing'} with {pending_count} pending gate(s).",
    )


def _latest_boundary_check(latest: dict[str, Any], path: Path) -> PreflightCheck:
    dry_run = str(latest.get("dry_run", "")).lower()
    permission = str(latest.get("trade_permission", "")).lower()
    server_time = str(latest.get("server_time_status", ""))
    if dry_run == "true" and permission == "false" and server_time == "CLOCK_OK":
        return PreflightCheck(
            "latest_runtime_boundary",
            "PASS",
            f"`{path}` latest bar {latest.get('bar_time', 'n/a')} is dry_run=true, trade_permission=false, server_time=CLOCK_OK.",
        )
    return PreflightCheck(
        "latest_runtime_boundary",
        "FAIL",
        f"`{path}` latest boundary is unsafe or unclear: dry_run={dry_run}, trade_permission={permission}, server_time={server_time}.",
    )


def _countdown_authority_boundary_check(countdown: dict[str, Any], path: Path) -> PreflightCheck:
    unsafe = [
        key
        for key in ("paper_mode_authorized", "broker_execution_authorized", "live_trading_authorized")
        if countdown.get(key) is not False
    ]
    if unsafe:
        return PreflightCheck("authority_boundary", "FAIL", f"`{path}` has unsafe authorization flag(s): {', '.join(unsafe)}.")
    return PreflightCheck("authority_boundary", "PASS", f"`{path}` keeps paper/broker/live authorization false.")


def _demo_account_isolation_check(path: Path) -> PreflightCheck:
    if not path.exists():
        return PreflightCheck(
            "demo_account_isolation",
            "PENDING",
            f"`{path}` is missing; cannot prove the MT5 account/server context is demo-only.",
        )
    text = path.read_text(encoding="utf-8", errors="replace")
    live_markers = sorted(_server_markers(text, ("Live", "Real")))
    demo_markers = sorted(_server_markers(text, ("Demo", "Practice")))
    if live_markers:
        return PreflightCheck(
            "demo_account_isolation",
            "FAIL",
            (
                f"`{path}` contains live/real server marker(s): {', '.join(live_markers)}. "
                "Do not start experimental demo trading from this runtime."
            ),
        )
    if demo_markers:
        return PreflightCheck(
            "demo_account_isolation",
            "PASS",
            f"`{path}` contains demo/practice server marker(s) and no live/real server markers: {', '.join(demo_markers)}.",
        )
    return PreflightCheck(
        "demo_account_isolation",
        "PENDING",
        f"`{path}` exists but does not contain an explicit demo/practice server marker.",
    )


def _server_markers(text: str, suffixes: tuple[str, ...]) -> set[str]:
    markers: set[str] = set()
    separators = " \t\r\n|`,;:()[]{}<>\"'"
    for raw in text.replace("\\", " ").replace("/", " ").split():
        token = raw.strip(separators)
        if not token:
            continue
        normalized = token.rstrip(".,;:")
        for suffix in suffixes:
            if normalized.endswith(f"-{suffix}"):
                markers.add(normalized)
    return markers


def _phase3_separation_check(phase3_status: dict[str, Any], path: Path) -> PreflightCheck:
    rehearsal = _mapping(phase3_status.get("demo_rehearsal"))
    completion = _mapping(phase3_status.get("completion_audit"))
    can_start = rehearsal.get("can_start_real_demo")
    demo_authorized = completion.get("demo_authorized")
    real_phase2 = phase3_status.get("real_phase2_readiness")
    unsafe_flags = {
        "authorized_for_deployment": phase3_status.get("authorized_for_deployment"),
        "broker_action_code_allowed": phase3_status.get("broker_action_code_allowed"),
        "mt5_runtime_touched": phase3_status.get("mt5_runtime_touched"),
    }
    owner_flow = phase3_status.get("owner_approval_flow")
    if (
        can_start is False
        and demo_authorized is False
        and real_phase2 != "PASS"
        and all(value is False for value in unsafe_flags.values())
        and owner_flow == "excluded_from_real_phase2_phase3_approval_flow"
    ):
        return PreflightCheck("phase3_separation", "PASS", f"`{path}` does not promote the side experiment into real demo.")
    return PreflightCheck(
        "phase3_separation",
        "FAIL",
        (
            f"`{path}` contains an unsafe Phase 3 promotion signal: "
            f"can_start_real_demo={can_start}, demo_authorized={demo_authorized}, "
            f"real_phase2_readiness={real_phase2}, "
            f"authorized_for_deployment={unsafe_flags['authorized_for_deployment']}, "
            f"broker_action_code_allowed={unsafe_flags['broker_action_code_allowed']}, "
            f"mt5_runtime_touched={unsafe_flags['mt5_runtime_touched']}, "
            f"owner_approval_flow={owner_flow}."
        ),
    )


def _safety_check(root: Path) -> PreflightCheck:
    findings = audit_phase1_tree(root)
    if findings:
        return PreflightCheck("phase1_safety_audit", "FAIL", f"Found {len(findings)} forbidden broker-action finding(s).")
    return PreflightCheck("phase1_safety_audit", "PASS", "Phase 1 safety audit found 0 forbidden broker-action findings.")


def _overall_status(checks: list[PreflightCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "PENDING" for check in checks):
        return "PENDING"
    return "PASS"


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 Demo Preflight Report",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authority",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Paper-mode implementation authorized | {str(payload['paper_mode_implementation_authorized']).lower()} |",
            f"| Demo trading authorized | {str(payload['demo_trading_authorized']).lower()} |",
            f"| Live trading authorized | {str(payload['live_trading_authorized']).lower()} |",
            f"| Boundary | {payload['boundary']} |",
            "",
            "## Checks",
            "",
            _markdown_table(payload["checks"], ["name", "status", "evidence"]),
            "",
            "## Source Reports",
            "",
            _markdown_table(
                [{"report": key, "path": value} for key, value in payload["source_reports"].items()],
                ["report", "path"],
            ),
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
        if len(parts) >= 3:
            rows.append({"Gate": parts[0], "Status": parts[1], "Evidence": parts[2]})
    return rows


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


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
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
    parser = argparse.ArgumentParser(description="Generate Phase 2 demo transition preflight report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_phase2_demo_preflight_report(args.root, args.output_json)
    print(f"Phase 2 demo preflight: {output.status}")
    print(output.markdown_path)
    return 0 if output.status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
