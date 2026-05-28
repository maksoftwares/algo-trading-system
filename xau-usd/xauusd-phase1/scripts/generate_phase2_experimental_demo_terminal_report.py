from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json"
DEFAULT_REPORT_MD = Path("outputs") / "reports" / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.md"
AUTHORITY_NOTE = (
    "This report verifies an owner-opened experimental demo terminal only. It does not authorize "
    "canonical Phase 2 readiness, live capital, or broker-side execution from the Phase 1 runtime."
)
KNOWN_PORTABLE_ROOTS = (
    Path("C:/MT5PortableGoldMission"),
    Path("C:/MT5PortableSpreadLogger"),
)
EXPECTED_EXPERIMENTAL_OBSERVER = "Phase2ExperimentalDemoObserver"

AUTH_RE = re.compile(
    r"(?P<time>\d{2}:\d{2}:\d{2}\.\d{3}).*?authorized on (?P<server>.+?) "
    r"through Access Point (?P<access_point>\d+) \(ping: (?P<ping>[\d.]+) ms",
    flags=re.IGNORECASE,
)
SYNC_RE = re.compile(
    r"(?P<time>\d{2}:\d{2}:\d{2}\.\d{3}).*?terminal synchronized.*?: "
    r"(?P<positions>\d+) positions, (?P<orders>\d+) orders",
    flags=re.IGNORECASE,
)
TRADING_ENABLED_RE = re.compile(r"(?P<time>\d{2}:\d{2}:\d{2}\.\d{3}).*?trading has been enabled", re.IGNORECASE)
EXPERT_EVENT_RE = re.compile(
    r"(?P<time>\d{2}:\d{2}:\d{2}\.\d{3}).*?Experts\s+expert "
    r"(?P<expert>.+?) \((?P<symbol>[^,]+),(?P<timeframe>[^)]+)\) "
    r"(?P<action>loaded successfully|removed)",
    flags=re.IGNORECASE,
)
TERMINAL_STARTED_RE = re.compile(
    r"(?P<time>\d{2}:\d{2}:\d{2}\.\d{3}).*?Terminal\s+MetaTrader 5 .* started",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class TerminalCheck:
    name: str
    status: str
    evidence: str


@dataclass(frozen=True)
class DemoTerminalOutput:
    status: str
    json_path: Path
    markdown_path: Path
    checks: tuple[TerminalCheck, ...]


def generate_phase2_experimental_demo_terminal_report(
    root: Path,
    terminal_data_dir: Path,
    terminal_exe: Path | None = None,
    output_json: Path | None = None,
) -> DemoTerminalOutput:
    root = root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    terminal_exe = terminal_exe.resolve() if terminal_exe else None
    output_json = (output_json or root / DEFAULT_REPORT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_REPORT_JSON.name else root / DEFAULT_REPORT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    parsed = _parse_latest_log(terminal_data_dir / "logs")
    session_start_index = _to_int(parsed.get("latest_session_start_line_index"))
    active_experts = _active_experts(parsed["expert_events"], session_start_index)
    latest_auth = _latest_mapping(parsed["authorizations"])
    latest_auth_index = _to_int(latest_auth.get("line_index"))
    sync_after_auth = _latest_after(parsed["syncs"], latest_auth_index)
    trading_after_auth = _latest_after(parsed["trading_enabled"], latest_auth_index)

    checks = [
        _terminal_exe_check(terminal_exe),
        _terminal_data_dir_check(terminal_data_dir),
        _latest_log_check(parsed["latest_log"]),
        _latest_authorization_check(latest_auth),
        _demo_server_check(latest_auth),
        _zero_positions_orders_check(sync_after_auth),
        _trading_enabled_check(trading_after_auth),
        _active_experts_check(active_experts),
        _runtime_isolation_check(terminal_exe, terminal_data_dir),
        TerminalCheck("authority_boundary", "PASS", "Report is evidence-only; it does not flip any broker-action authorization flag."),
    ]
    expected_observer_count = _expected_observer_count(active_experts)
    status = _overall_status(checks, expected_observer_count > 0)
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": AUTHORITY_NOTE,
        "clean_demo_setup_ready": status == "DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP",
        "can_start_experimental_demo_setup": status == "DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP",
        "experimental_observers_attached": expected_observer_count > 0,
        "experimental_observer_active_count": expected_observer_count,
        "can_start_demo_broker_rehearsal": False,
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "mt5_runtime_touched_by_script": False,
        "terminal": {
            "terminal_exe": str(terminal_exe) if terminal_exe else "not_provided",
            "terminal_data_dir": str(terminal_data_dir),
            "latest_log": str(parsed["latest_log"]) if parsed["latest_log"] else "missing",
            "latest_session_start": parsed.get("latest_session_start", "missing"),
            "latest_authorization_server": latest_auth.get("server", "missing"),
            "latest_authorization_time": latest_auth.get("timestamp", "missing"),
            "latest_access_point": latest_auth.get("access_point", "missing"),
            "latest_ping_ms": latest_auth.get("ping_ms", "missing"),
        },
        "checks": [check.__dict__ for check in checks],
        "active_experts": active_experts,
        "next_actions": _next_actions(status, active_experts),
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return DemoTerminalOutput(status, output_json, output_md, tuple(checks))


def _parse_latest_log(logs_dir: Path) -> dict[str, Any]:
    if not logs_dir.exists():
        return {
            "latest_log": None,
            "latest_session_start": "missing",
            "latest_session_start_line_index": None,
            "authorizations": [],
            "syncs": [],
            "trading_enabled": [],
            "expert_events": [],
        }
    logs = sorted(logs_dir.glob("*.log"), key=lambda path: (path.stat().st_mtime, path.name))
    latest_log = logs[-1] if logs else None
    if latest_log is None:
        return {
            "latest_log": None,
            "latest_session_start": "missing",
            "latest_session_start_line_index": None,
            "authorizations": [],
            "syncs": [],
            "trading_enabled": [],
            "expert_events": [],
        }
    log_date = _date_from_log_name(latest_log)
    text = _read_log_text(latest_log)
    authorizations: list[dict[str, Any]] = []
    syncs: list[dict[str, Any]] = []
    trading_enabled: list[dict[str, Any]] = []
    expert_events: list[dict[str, Any]] = []
    session_starts: list[dict[str, Any]] = []
    for line_index, line in enumerate(text.splitlines()):
        started = TERMINAL_STARTED_RE.search(line)
        if started:
            session_starts.append(
                {
                    "line_index": line_index,
                    "timestamp": _timestamp(log_date, started.group("time")),
                }
            )
            continue
        auth = AUTH_RE.search(line)
        if auth:
            authorizations.append(
                {
                    "line_index": line_index,
                    "timestamp": _timestamp(log_date, auth.group("time")),
                    "server": auth.group("server").strip(),
                    "access_point": auth.group("access_point"),
                    "ping_ms": float(auth.group("ping")),
                    "source_file": str(latest_log),
                }
            )
            continue
        sync = SYNC_RE.search(line)
        if sync:
            syncs.append(
                {
                    "line_index": line_index,
                    "timestamp": _timestamp(log_date, sync.group("time")),
                    "positions": int(sync.group("positions")),
                    "orders": int(sync.group("orders")),
                }
            )
            continue
        trading = TRADING_ENABLED_RE.search(line)
        if trading:
            trading_enabled.append(
                {
                    "line_index": line_index,
                    "timestamp": _timestamp(log_date, trading.group("time")),
                }
            )
            continue
        expert = EXPERT_EVENT_RE.search(line)
        if expert:
            expert_events.append(
                {
                    "line_index": line_index,
                    "timestamp": _timestamp(log_date, expert.group("time")),
                    "expert": expert.group("expert").strip(),
                    "symbol": expert.group("symbol").strip(),
                    "timeframe": expert.group("timeframe").strip(),
                    "action": expert.group("action").lower(),
                }
            )
    return {
        "latest_log": latest_log,
        "latest_session_start": session_starts[-1]["timestamp"] if session_starts else "missing",
        "latest_session_start_line_index": session_starts[-1]["line_index"] if session_starts else None,
        "authorizations": authorizations,
        "syncs": syncs,
        "trading_enabled": trading_enabled,
        "expert_events": expert_events,
    }


def _terminal_exe_check(path: Path | None) -> TerminalCheck:
    if path is None:
        return TerminalCheck("terminal_exe", "PENDING", "Terminal executable path was not provided.")
    if path.exists():
        return TerminalCheck("terminal_exe", "PASS", f"`{path}` exists.")
    return TerminalCheck("terminal_exe", "FAIL", f"`{path}` does not exist.")


def _terminal_data_dir_check(path: Path) -> TerminalCheck:
    if (path / "logs").exists():
        return TerminalCheck("terminal_data_dir", "PASS", f"`{path}` contains an MT5 logs directory.")
    return TerminalCheck("terminal_data_dir", "FAIL", f"`{path}` does not contain a logs directory.")


def _latest_log_check(path: Path | None) -> TerminalCheck:
    if path is None:
        return TerminalCheck("latest_log", "FAIL", "No MT5 log file was found.")
    return TerminalCheck("latest_log", "PASS", f"Latest log inspected: `{path}`.")


def _latest_authorization_check(auth: dict[str, Any]) -> TerminalCheck:
    if not auth:
        return TerminalCheck("latest_authorization", "FAIL", "No authorization line was found in the latest MT5 log.")
    return TerminalCheck(
        "latest_authorization",
        "PASS",
        f"Latest authorization is on `{auth.get('server')}` at {auth.get('timestamp')}; account id and IP are intentionally omitted.",
    )


def _demo_server_check(auth: dict[str, Any]) -> TerminalCheck:
    server = str(auth.get("server", ""))
    if not server:
        return TerminalCheck("demo_server", "FAIL", "No server name was available from latest authorization.")
    if _has_live_marker(server):
        return TerminalCheck("demo_server", "FAIL", f"Latest authorization server `{server}` is live/real context.")
    if _has_demo_marker(server):
        return TerminalCheck("demo_server", "PASS", f"Latest authorization server `{server}` is demo/practice context.")
    return TerminalCheck("demo_server", "FAIL", f"Latest authorization server `{server}` is not explicitly demo/practice.")


def _zero_positions_orders_check(sync: dict[str, Any]) -> TerminalCheck:
    if not sync:
        return TerminalCheck("zero_positions_orders", "FAIL", "No post-authorization terminal synchronization line was found.")
    positions = _to_int(sync.get("positions"))
    orders = _to_int(sync.get("orders"))
    if positions == 0 and orders == 0:
        return TerminalCheck("zero_positions_orders", "PASS", "Latest post-authorization sync shows 0 positions and 0 orders.")
    return TerminalCheck(
        "zero_positions_orders",
        "FAIL",
        f"Latest post-authorization sync shows positions={positions}, orders={orders}; terminal is not clean.",
    )


def _trading_enabled_check(event: dict[str, Any]) -> TerminalCheck:
    if event:
        return TerminalCheck("trading_enabled", "PASS", f"Trading-enabled line was found after authorization at {event.get('timestamp')}.")
    return TerminalCheck("trading_enabled", "PENDING", "No trading-enabled line was found after latest authorization.")


def _active_experts_check(active_experts: list[dict[str, str]]) -> TerminalCheck:
    if not active_experts:
        return TerminalCheck("active_chart_experts", "PASS", "No active expert-loaded state was detected in the latest log.")
    if all(item.get("expert") == EXPECTED_EXPERIMENTAL_OBSERVER for item in active_experts):
        return TerminalCheck(
            "active_chart_experts",
            "PASS",
            f"Only expected telemetry observer attachments are active: {len(active_experts)} {EXPECTED_EXPERIMENTAL_OBSERVER} charts.",
        )
    names = ", ".join(f"{item['expert']}({item['symbol']},{item['timeframe']})" for item in active_experts)
    return TerminalCheck(
        "active_chart_experts",
        "WARN",
        f"Active expert-loaded state detected in latest log: {names}. Clean or quarantine the terminal before demo broker rehearsal.",
    )


def _runtime_isolation_check(terminal_exe: Path | None, terminal_data_dir: Path) -> TerminalCheck:
    candidates = [path for path in (terminal_exe, terminal_data_dir) if path is not None]
    for candidate in candidates:
        try:
            resolved_candidate = candidate.resolve()
        except OSError:
            resolved_candidate = candidate
        for root in KNOWN_PORTABLE_ROOTS:
            try:
                resolved_root = root.resolve()
            except OSError:
                resolved_root = root
            if _is_relative_to(resolved_candidate, resolved_root):
                return TerminalCheck(
                    "runtime_isolation",
                    "FAIL",
                    f"`{candidate}` is inside known protected runtime `{root}`.",
                )
    return TerminalCheck("runtime_isolation", "PASS", "Terminal path is distinct from known Phase 1 dry-run and spread-logger portable runtimes.")


def _overall_status(checks: list[TerminalCheck], expected_observers_attached: bool = False) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "WARN" for check in checks):
        return "DEMO_TERMINAL_VERIFIED_QUARANTINE_REQUIRED"
    if any(check.status == "PENDING" for check in checks):
        return "PENDING"
    if expected_observers_attached:
        return "DEMO_TERMINAL_VERIFIED_EXPERIMENTAL_OBSERVERS_ATTACHED"
    return "DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP"


def _next_actions(status: str, active_experts: list[dict[str, str]]) -> list[str]:
    if status == "DEMO_TERMINAL_VERIFIED_QUARANTINE_REQUIRED":
        return [
            "Detach or disable the active chart expert(s) shown in this report, or open a clean demo-only profile.",
            "Regenerate this report and require DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP before any demo broker rehearsal.",
            "Keep C:/MT5PortableGoldMission and C:/MT5PortableSpreadLogger untouched; they remain dry-run/passive collectors.",
        ]
    if status == "DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP":
        return [
            "Use this terminal only for an explicitly owner-approved experimental demo setup.",
            "Attach only the experimental demo component after canonical dry-run collectors are confirmed untouched.",
            "Record every demo event in a separate experimental ledger; do not mark canonical Phase 2 as passed from this report.",
        ]
    if status == "DEMO_TERMINAL_VERIFIED_EXPERIMENTAL_OBSERVERS_ATTACHED":
        return [
            "Keep the experimental observers isolated on the standard Capital.com demo terminal.",
            "Use PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.md as the source of truth for candidate-symbol coverage.",
            "Do not treat telemetry observers as broker-execution or canonical Phase 2 approval.",
        ]
    return [
        "Do not use this terminal for demo broker rehearsal until every failing or pending check is resolved.",
        "Regenerate this report after the terminal state changes.",
    ]


def _active_experts(events: list[dict[str, Any]], session_start_index: int | None) -> list[dict[str, str]]:
    latest_by_chart: dict[tuple[str, str, str], dict[str, Any]] = {}
    for event in events:
        event_index = _to_int(event.get("line_index"))
        if session_start_index is not None and event_index is not None and event_index < session_start_index:
            continue
        key = (str(event["expert"]), str(event["symbol"]), str(event["timeframe"]))
        latest_by_chart[key] = event
    active: list[dict[str, str]] = []
    for event in latest_by_chart.values():
        if event.get("action") == "loaded successfully":
            active.append(
                {
                    "expert": str(event["expert"]),
                    "symbol": str(event["symbol"]),
                    "timeframe": str(event["timeframe"]),
                    "last_seen": str(event["timestamp"]),
                }
            )
    return sorted(active, key=lambda item: (item["symbol"], item["timeframe"], item["expert"]))


def _expected_observer_count(active_experts: list[dict[str, str]]) -> int:
    return sum(1 for item in active_experts if item.get("expert") == EXPECTED_EXPERIMENTAL_OBSERVER)


def _latest_after(rows: list[dict[str, Any]], line_index: int | None) -> dict[str, Any]:
    if line_index is None:
        return {}
    matching = [row for row in rows if _to_int(row.get("line_index")) is not None and int(row["line_index"]) > line_index]
    return matching[-1] if matching else {}


def _latest_mapping(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[-1] if rows else {}


def _has_demo_marker(server: str) -> bool:
    normalized = server.lower()
    return "demo" in normalized or "practice" in normalized


def _has_live_marker(server: str) -> bool:
    normalized = server.lower()
    return "live" in normalized or "real" in normalized


def _read_log_text(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8", errors="replace")


def _date_from_log_name(path: Path) -> str:
    return path.stem if re.fullmatch(r"\d{8}", path.stem) else datetime.now(timezone.utc).strftime("%Y%m%d")


def _timestamp(log_date: str, time_text: str) -> str:
    try:
        parsed = datetime.strptime(f"{log_date} {time_text}", "%Y%m%d %H:%M:%S.%f")
        return parsed.isoformat(sep=" ")
    except ValueError:
        return f"{log_date} {time_text}"


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _render_markdown(payload: dict[str, Any]) -> str:
    terminal = payload.get("terminal", {})
    return "\n".join(
        [
            "# Phase 2 Experimental Demo Terminal Report",
            "",
            AUTHORITY_NOTE,
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Decision",
            "",
            _table(
                [
                    ("Clean demo setup ready", str(payload.get("clean_demo_setup_ready", False))),
                    ("Can start experimental demo setup", str(payload.get("can_start_experimental_demo_setup", False))),
                    ("Can start demo broker rehearsal", str(payload.get("can_start_demo_broker_rehearsal", False))),
                    ("Canonical Phase 2 authorized", str(payload.get("canonical_phase2_authorized", False))),
                    ("Live trading authorized", str(payload.get("live_trading_authorized", False))),
                    ("MT5 runtime touched by script", str(payload.get("mt5_runtime_touched_by_script", False))),
                ]
            ),
            "",
            "## Terminal",
            "",
            _table(
                [
                    ("Terminal exe", str(terminal.get("terminal_exe", "not_provided"))),
                    ("Terminal data dir", str(terminal.get("terminal_data_dir", "missing"))),
                    ("Latest log", str(terminal.get("latest_log", "missing"))),
                    ("Latest session start", str(terminal.get("latest_session_start", "missing"))),
                    ("Latest authorization server", str(terminal.get("latest_authorization_server", "missing"))),
                    ("Latest authorization time", str(terminal.get("latest_authorization_time", "missing"))),
                    ("Latest access point", str(terminal.get("latest_access_point", "missing"))),
                    ("Latest ping ms", str(terminal.get("latest_ping_ms", "missing"))),
                ]
            ),
            "",
            "## Checks",
            "",
            _dict_table(payload.get("checks", []), ["name", "status", "evidence"]),
            "",
            "## Active Experts",
            "",
            _dict_table(payload.get("active_experts", []), ["expert", "symbol", "timeframe", "last_seen"]),
            "",
            "## Next Actions",
            "",
            _bullet_list([str(item) for item in payload.get("next_actions", [])]),
            "",
        ]
    )


def _dict_table(rows: Any, columns: list[str]) -> str:
    if not isinstance(rows, list) or not rows:
        return "No rows."
    output = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        item = row if isinstance(row, dict) else {}
        output.append("| " + " | ".join(_escape(str(item.get(column, ""))) for column in columns) + " |")
    return "\n".join(output)


def _table(rows: list[tuple[str, str]]) -> str:
    return "\n".join(["| Field | Value |", "| --- | --- |", *[f"| {_escape(k)} | {_escape(v)} |" for k, v in rows]])


def _bullet_list(rows: list[str]) -> str:
    return "\n".join(f"- {row}" for row in rows) if rows else "- None."


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an evidence-only report for an owner-opened MT5 demo terminal.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal-data-dir", type=Path, required=True)
    parser.add_argument("--terminal-exe", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args(argv)

    output = generate_phase2_experimental_demo_terminal_report(
        root=args.root,
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        output_json=args.output_json,
    )
    print(f"Phase 2 experimental demo terminal: {output.status}")
    print(output.json_path)
    print(output.markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
