from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase2x_common import (
    PHASE2X_STATUS_FAIL,
    PHASE2X_STATUS_PASS,
    boundary_lines,
    checks_table,
    now_utc,
    overall_status,
    read_csv,
    report_header,
    write_report_pair,
)


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2X_KILL_SWITCH_BLOCK_TEST_REPORT.json"
DEFAULT_ORDER_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_order_log_xauusd.csv")
DEFAULT_STARTUP_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_startup_xauusd.csv")
DEFAULT_KILL_SWITCH = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_kill_switch.txt")


def generate_phase2x_kill_switch_block_test_report(
    root: Path,
    order_log: Path = DEFAULT_ORDER_LOG,
    startup_log: Path = DEFAULT_STARTUP_LOG,
    kill_switch_file: Path = DEFAULT_KILL_SWITCH,
    output_json: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    rows = read_csv(order_log)
    startup_rows = read_csv(startup_log)
    kill_rows = [row for row in rows if "kill" in str(row.get("guard_reason", "")).lower()]
    startup_kill_rows = [row for row in startup_rows if "REFUSED_KILL_SWITCH_ACTIVE" in str(row.get("startup_status", ""))]
    sent_during_kill = [row for row in kill_rows if row.get("action") == "ORDER_SEND_OK"]
    proof_rows = len(kill_rows) + len(startup_kill_rows)
    checks = [
        {"name": "order_log_present", "status": PHASE2X_STATUS_PASS if order_log.exists() else "PENDING_RUNTIME_EVIDENCE", "evidence": str(order_log)},
        {"name": "startup_log_present", "status": PHASE2X_STATUS_PASS if startup_log.exists() else "PENDING_RUNTIME_EVIDENCE", "evidence": str(startup_log)},
        {
            "name": "kill_switch_block_observed",
            "status": PHASE2X_STATUS_PASS if proof_rows else "PENDING_RUNTIME_EVIDENCE",
            "evidence": f"order_kill_block_rows={len(kill_rows)}; startup_refusal_rows={len(startup_kill_rows)}",
        },
        {"name": "no_broker_action_during_block", "status": PHASE2X_STATUS_PASS if proof_rows and not sent_during_kill else (PHASE2X_STATUS_FAIL if sent_during_kill else "PENDING_RUNTIME_EVIDENCE"), "evidence": f"sent_during_kill={len(sent_during_kill)}"},
    ]
    payload = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Phase 2X kill-switch block-test report. Report-only; it does not create files, send orders, or modify MT5 state.",
        "kill_switch_file": str(kill_switch_file),
        "kill_switch_file_currently_exists": kill_switch_file.exists(),
        "order_log": str(order_log),
        "startup_log": str(startup_log),
        "order_kill_block_rows": len(kill_rows),
        "startup_refusal_rows": len(startup_kill_rows),
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Phase 2X Kill-Switch Block Test Report", payload)
    lines.extend(boundary_lines())
    lines.extend([
        "## Evidence",
        "",
        f"- Kill switch file: `{payload['kill_switch_file']}`",
        f"- Kill switch currently exists: `{payload['kill_switch_file_currently_exists']}`",
        f"- Order log: `{payload['order_log']}`",
        f"- Startup log: `{payload['startup_log']}`",
        f"- Order kill-block rows: `{payload['order_kill_block_rows']}`",
        f"- Startup refusal rows: `{payload['startup_refusal_rows']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2X kill-switch block-test report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--order-log", type=Path, default=DEFAULT_ORDER_LOG)
    parser.add_argument("--startup-log", type=Path, default=DEFAULT_STARTUP_LOG)
    parser.add_argument("--kill-switch-file", type=Path, default=DEFAULT_KILL_SWITCH)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_phase2x_kill_switch_block_test_report(args.root, args.order_log, args.startup_log, args.kill_switch_file, args.output_json)
    print(f"Phase 2X kill-switch block test: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
