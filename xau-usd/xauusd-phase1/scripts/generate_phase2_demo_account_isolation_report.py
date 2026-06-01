from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_ACCOUNT_ISOLATION.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_DEMO_ACCOUNT_ISOLATION_REPORT.md"
AUTHORITY_NOTE = (
    "This report verifies demo-account isolation evidence only. "
    "It does not authorize Phase 2 readiness, paper-mode implementation, live capital, or broker-side execution."
)


@dataclass(frozen=True)
class IsolationCheck:
    name: str
    status: str
    evidence: str


@dataclass(frozen=True)
class DemoAccountIsolationOutput:
    status: str
    json_path: Path
    markdown_path: Path
    checks: tuple[IsolationCheck, ...]


def generate_phase2_demo_account_isolation_report(
    root: Path,
    output_json: Path | None = None,
) -> DemoAccountIsolationOutput:
    root = root.resolve()
    report_dir = root / "outputs" / "reports"
    output_json = (output_json or root / DEFAULT_REPORT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_REPORT_JSON.name else root / DEFAULT_REPORT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    terminal_report_path = report_dir / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json"
    attachments_report_path = report_dir / "PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json"
    latest_signal_path = _latest_path(report_dir.glob("DEMO_OBSERVER_WOULD_SIGNALS_*.csv"))
    terminal_report = _read_json(terminal_report_path)
    attachments = _read_json(attachments_report_path)
    terminal = _mapping(terminal_report.get("terminal"))
    account_server = str(terminal.get("latest_authorization_server", "UNKNOWN"))
    positions, orders = _positions_orders_from_checks(_mapping_rows(terminal_report.get("checks")))
    live_server_marker_present = _has_live_marker(account_server)
    account_type = _account_type(account_server)

    checks = [
        _source_report_check(terminal_report_path, terminal_report),
        _demo_server_check(account_server),
        _zero_positions_orders_check(positions, orders, terminal_report_path),
        _authority_boundary_check(terminal_report, terminal_report_path),
        _runtime_isolation_check(terminal_report, terminal_report_path),
        _attachments_boundary_check(attachments, attachments_report_path),
    ]
    status = _overall_status(checks)
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": AUTHORITY_NOTE,
        "paper_mode_authorized": False,
        "demo_trading_authorized": False,
        "live_trading_authorized": False,
        "broker_execution_authorized": False,
        "canonical_phase2_authorized": False,
        "account": {
            "account_server": account_server,
            "account_type_or_label": account_type,
            "evidence_source": str(terminal_report_path),
            "positions_count": positions if positions is not None else "UNKNOWN",
            "orders_count": orders if orders is not None else "UNKNOWN",
            "terminal_path": str(terminal.get("terminal_exe", "UNKNOWN")),
            "data_path": str(terminal.get("terminal_data_dir", "UNKNOWN")),
            "latest_decision_row_path": str(latest_signal_path) if latest_signal_path else "UNKNOWN",
            "live_server_marker_present": live_server_marker_present,
        },
        "experimental_observers": {
            "attached": terminal_report.get("experimental_observers_attached") is True,
            "active_count": terminal_report.get("experimental_observer_active_count", 0),
            "attachment_report": str(attachments_report_path),
        },
        "checks": [check.__dict__ for check in checks],
        "source_reports": {
            "experimental_demo_terminal": str(terminal_report_path),
            "experimental_demo_attachments": str(attachments_report_path),
            "latest_demo_observer_signal_csv": str(latest_signal_path) if latest_signal_path else "UNKNOWN",
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return DemoAccountIsolationOutput(status, output_json, output_md, tuple(checks))


def _source_report_check(path: Path, report: dict[str, Any]) -> IsolationCheck:
    if not path.exists():
        return IsolationCheck("experimental_demo_terminal_report", "PENDING", f"`{path}` is missing.")
    status = str(report.get("status", "UNKNOWN"))
    if status in {
        "DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP",
        "DEMO_TERMINAL_VERIFIED_EXPERIMENTAL_OBSERVERS_ATTACHED",
    }:
        return IsolationCheck("experimental_demo_terminal_report", "PASS", f"`{path}` status is {status}.")
    if status in {"PENDING", "UNKNOWN", ""}:
        return IsolationCheck("experimental_demo_terminal_report", "PENDING", f"`{path}` status is {status or 'missing'}.")
    return IsolationCheck("experimental_demo_terminal_report", "FAIL", f"`{path}` status is {status}.")


def _demo_server_check(server: str) -> IsolationCheck:
    if not server or server == "UNKNOWN":
        return IsolationCheck("demo_server", "PENDING", "No account server is available.")
    if _has_live_marker(server):
        return IsolationCheck("demo_server", "FAIL", f"Account server `{server}` is live/real context.")
    if _has_demo_marker(server):
        return IsolationCheck("demo_server", "PASS", f"Account server `{server}` is demo/practice context.")
    return IsolationCheck("demo_server", "PENDING", f"Account server `{server}` is not explicitly demo/practice.")


def _zero_positions_orders_check(positions: int | None, orders: int | None, path: Path) -> IsolationCheck:
    if positions == 0 and orders == 0:
        return IsolationCheck("zero_positions_orders", "PASS", f"`{path}` proves 0 positions and 0 orders.")
    if positions is None or orders is None:
        return IsolationCheck("zero_positions_orders", "PENDING", f"`{path}` does not expose position/order counts.")
    return IsolationCheck("zero_positions_orders", "FAIL", f"positions={positions}, orders={orders}; terminal is not clean.")


def _authority_boundary_check(report: dict[str, Any], path: Path) -> IsolationCheck:
    if not report:
        return IsolationCheck("authority_boundary", "PENDING", f"`{path}` is missing.")
    unsafe = [
        key
        for key in ("canonical_phase2_authorized", "live_trading_authorized", "can_start_demo_broker_rehearsal")
        if report.get(key) is not False
    ]
    if unsafe:
        return IsolationCheck("authority_boundary", "FAIL", f"`{path}` has unsafe true flag(s): {', '.join(unsafe)}.")
    return IsolationCheck("authority_boundary", "PASS", f"`{path}` keeps Phase 2/demo/live authorization false.")


def _runtime_isolation_check(report: dict[str, Any], path: Path) -> IsolationCheck:
    if not report:
        return IsolationCheck("runtime_isolation", "PENDING", f"`{path}` is missing.")
    for check in _mapping_rows(report.get("checks")):
        if check.get("name") == "runtime_isolation":
            status = str(check.get("status", "UNKNOWN"))
            if status == "PASS":
                return IsolationCheck("runtime_isolation", "PASS", str(check.get("evidence", "")))
            return IsolationCheck("runtime_isolation", status if status in {"FAIL", "PENDING"} else "FAIL", str(check.get("evidence", "")))
    return IsolationCheck("runtime_isolation", "PENDING", f"`{path}` does not include a runtime isolation check.")


def _attachments_boundary_check(report: dict[str, Any], path: Path) -> IsolationCheck:
    if not path.exists():
        return IsolationCheck("experimental_demo_attachments", "PENDING", f"`{path}` is missing.")
    unsafe = [
        key
        for key in ("canonical_phase2_authorized", "live_trading_authorized", "broker_execution_authorized")
        if key in report and report.get(key) is not False
    ]
    ea = _mapping(report.get("ea"))
    if ea and ea.get("broker_action_allowed") is not False:
        unsafe.append("ea.broker_action_allowed")
    if unsafe:
        return IsolationCheck("experimental_demo_attachments", "FAIL", f"`{path}` has unsafe true flag(s): {', '.join(unsafe)}.")
    return IsolationCheck("experimental_demo_attachments", "PASS", f"`{path}` keeps attachment evidence non-authorizing.")


def _overall_status(checks: list[IsolationCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "PENDING" for check in checks):
        return "PENDING"
    return "PASS"


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 Demo Account Isolation Report",
            "",
            AUTHORITY_NOTE,
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authority",
            "",
            _table(
                [
                    ("Paper mode authorized", str(payload.get("paper_mode_authorized", False)).lower()),
                    ("Demo trading authorized", str(payload.get("demo_trading_authorized", False)).lower()),
                    ("Live trading authorized", str(payload.get("live_trading_authorized", False)).lower()),
                    ("Broker execution authorized", str(payload.get("broker_execution_authorized", False)).lower()),
                    ("Canonical Phase 2 authorized", str(payload.get("canonical_phase2_authorized", False)).lower()),
                ]
            ),
            "",
            "## Account Evidence",
            "",
            _table([(key, str(value)) for key, value in _mapping(payload.get("account")).items()]),
            "",
            "## Checks",
            "",
            _rows_table(_mapping_rows(payload.get("checks")), ["name", "status", "evidence"]),
            "",
            "## Source Reports",
            "",
            _table([(key, str(value)) for key, value in _mapping(payload.get("source_reports")).items()]),
            "",
        ]
    )


def _positions_orders_from_checks(checks: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    for check in checks:
        if check.get("name") != "zero_positions_orders":
            continue
        evidence = str(check.get("evidence", "")).lower()
        if "0 positions" in evidence and "0 orders" in evidence:
            return 0, 0
    return None, None


def _account_type(server: str) -> str:
    if _has_live_marker(server):
        return "LIVE_OR_REAL"
    if _has_demo_marker(server):
        return "DEMO_OR_PRACTICE"
    return "UNKNOWN"


def _has_demo_marker(value: str) -> bool:
    lowered = value.lower()
    return "demo" in lowered or "practice" in lowered


def _has_live_marker(value: str) -> bool:
    lowered = value.lower()
    return "live" in lowered or "real" in lowered


def _latest_path(paths) -> Path | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    return max(existing, key=lambda path: (path.stat().st_mtime, path.name))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _mapping_rows(value: Any) -> list[dict[str, Any]]:
    return [item for item in value] if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def _table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return "No rows."
    body = ["| Field | Value |", "| --- | --- |"]
    body.extend(f"| {key} | {value} |" for key, value in rows)
    return "\n".join(body)


def _rows_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    body = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    body.extend("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |" for row in rows)
    return "\n".join(body)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2 demo account isolation evidence.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args(argv)

    output = generate_phase2_demo_account_isolation_report(args.root, args.output_json)
    print(f"Phase 2 demo account isolation: {output.markdown_path}")
    return 0 if output.status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
