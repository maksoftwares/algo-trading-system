from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase2x_common import (
    ACTIVE_MAGIC,
    FIXED_LOT,
    MAX_ESTIMATED_COST_R,
    MAX_FAMILY_OPEN_POSITIONS,
    RUN_ID,
    TARGET_SYMBOL,
    boundary_lines,
    check,
    checks_table,
    mask_account,
    now_utc,
    overall_status,
    read_csv,
    report_header,
    summarize_order_rows,
    write_report_pair,
)


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2X_OWNER_EXECUTION_STATUS_REPORT.json"
DEFAULT_OWNER_EXEC_ROOT = Path("C:/MT5PortableP2WeaknessOwnerExec")


def generate_phase2x_owner_execution_status_report(
    root: Path,
    owner_exec_root: Path = DEFAULT_OWNER_EXEC_ROOT,
    output_json: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    owner_exec_root = owner_exec_root.resolve()
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    startup_log = owner_exec_root / "MQL5" / "Files" / "p2weakness_br_v1_startup_xauusd.csv"
    signal_log = owner_exec_root / "MQL5" / "Files" / "p2weakness_br_v1_signal_log_xauusd.csv"
    order_log = owner_exec_root / "MQL5" / "Files" / "p2weakness_br_v1_order_log_xauusd.csv"
    startup_rows = read_csv(startup_log)
    signal_rows = read_csv(signal_log)
    order_rows = read_csv(order_log)
    latest_startup = startup_rows[-1] if startup_rows else {}
    latest_signal = signal_rows[-1] if signal_rows else {}
    sent_orders = [row for row in order_rows if row.get("action") == "ORDER_SEND_OK"]
    checks = [
        check("owner_exec_terminal_root_present", "PASS" if owner_exec_root.exists() else "FAIL", str(owner_exec_root)),
        check("startup_log_present", "PASS" if startup_rows else "PENDING_RUNTIME_EVIDENCE", str(startup_log)),
        check("attached_owner_authorized", "PASS" if latest_startup.get("startup_status") == "ATTACHED_OWNER_AUTHORIZED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED" else "PENDING_RUNTIME_EVIDENCE", f"startup_status={latest_startup.get('startup_status', '')!r}"),
        check("broker_action_enabled_for_demo", "PASS" if latest_startup.get("broker_action_allowed") == "true" and latest_startup.get("dry_run") == "false" else "FAIL", f"dry_run={latest_startup.get('dry_run', '')!r}; broker_action_allowed={latest_startup.get('broker_action_allowed', '')!r}"),
        check("demo_server_only", _demo_server_status(latest_startup), f"account_server={latest_startup.get('account_server', '')!r}"),
        check("account_login_present_masked", "PASS" if latest_startup.get("account_login") else "PENDING_RUNTIME_EVIDENCE", mask_account(latest_startup.get("account_login", ""))),
        check("magic_931000", "PASS" if str(latest_startup.get("magic", "")) == str(ACTIVE_MAGIC) else "FAIL", f"magic={latest_startup.get('magic', '')!r}"),
        check("symbol_xauusd", "PASS" if latest_startup.get("symbol") == TARGET_SYMBOL else "FAIL", f"symbol={latest_startup.get('symbol', '')!r}"),
        check("fixed_lot_guard", "PASS" if _float_lte(latest_startup.get("max_estimated_cost_R"), MAX_ESTIMATED_COST_R) else "FAIL", f"max_estimated_cost_R={latest_startup.get('max_estimated_cost_R', '')!r}"),
        check("family_exposure_guard", "PASS" if str(latest_startup.get("max_family_open_positions", "")) == str(MAX_FAMILY_OPEN_POSITIONS) else "FAIL", f"max_family_open_positions={latest_startup.get('max_family_open_positions', '')!r}"),
        check("signal_log_active", "PASS" if signal_rows else "PENDING_RUNTIME_EVIDENCE", f"signal_rows={len(signal_rows)}"),
        check("all_order_rows_magic_931000", _all_order_rows(order_rows, lambda row: str(row.get("magic", "")) == str(ACTIVE_MAGIC)), f"order_rows={len(order_rows)}"),
        check("all_order_rows_symbol_xauusd", _all_order_rows(order_rows, lambda row: row.get("symbol") == TARGET_SYMBOL), f"order_rows={len(order_rows)}"),
        check("sent_lots_lte_0_01", _all_order_rows(sent_orders, lambda row: _float(row.get("volume")) <= FIXED_LOT), f"sent_orders={len(sent_orders)}"),
        check("sent_cost_r_lte_0_15", _all_order_rows(sent_orders, lambda row: _float(row.get("estimated_cost_R")) <= MAX_ESTIMATED_COST_R), f"sent_orders={len(sent_orders)}"),
    ]
    payload = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Phase 2X owner-execution status. Experimental demo only; no canonical Phase 2, no live trading, and no real capital authorization.",
        "run_id": RUN_ID,
        "owner_exec_root": str(owner_exec_root),
        "startup_log": str(startup_log),
        "signal_log": str(signal_log),
        "order_log": str(order_log),
        "latest_startup": _masked_row(latest_startup),
        "latest_signal": _masked_row(latest_signal),
        "order_summary": summarize_order_rows(order_rows),
        "sent_orders": len(sent_orders),
        "phase2x_demo_execution_attached": latest_startup.get("startup_status") == "ATTACHED_OWNER_AUTHORIZED_WEAKNESS_REVIEW_DEMO_EXECUTOR_ENABLED",
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _demo_server_status(row: dict[str, str]) -> str:
    server = str(row.get("account_server", "")).lower()
    if not server:
        return "PENDING_RUNTIME_EVIDENCE"
    return "PASS" if ("demo" in server or "practice" in server) and "live" not in server and "real" not in server else "FAIL"


def _all_order_rows(rows: list[dict[str, str]], predicate) -> str:
    if not rows:
        return "PASS"
    return "PASS" if all(predicate(row) for row in rows) else "FAIL"


def _float(value: object) -> float:
    try:
        return float(str(value))
    except ValueError:
        return 0.0


def _float_lte(value: object, limit: float) -> bool:
    try:
        return float(str(value)) <= limit
    except ValueError:
        return False


def _masked_row(row: dict[str, str]) -> dict[str, str]:
    masked = dict(row)
    for key in ("account_login", "account", "login", "allowed_account_logins"):
        if key in masked:
            masked[key] = mask_account(masked[key])
    return masked


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Phase 2X Owner Execution Status Report", payload)
    lines.extend(boundary_lines())
    lines.extend([
        f"- Phase 2X demo execution attached: `{payload['phase2x_demo_execution_attached']}`",
        f"- Owner exec root: `{payload['owner_exec_root']}`",
        f"- Sent orders observed: `{payload['sent_orders']}`",
        f"- Order summary: `{payload['order_summary']}`",
        "",
        "## Logs",
        "",
        f"- Startup log: `{payload['startup_log']}`",
        f"- Signal log: `{payload['signal_log']}`",
        f"- Order log: `{payload['order_log']}`",
        "",
        "## Latest Startup",
        "",
        f"- `{payload['latest_startup']}`",
        "",
        "## Latest Signal",
        "",
        f"- `{payload['latest_signal']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2X owner-execution status report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--owner-exec-root", type=Path, default=DEFAULT_OWNER_EXEC_ROOT)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_phase2x_owner_execution_status_report(args.root, args.owner_exec_root, args.output_json)
    print(f"Phase 2X owner execution status: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
