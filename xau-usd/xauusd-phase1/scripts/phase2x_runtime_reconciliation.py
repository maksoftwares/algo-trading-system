from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase2x_common import ACTIVE_MAGIC, OLD_MAGIC, boundary_lines, checks_table, now_utc, read_csv, read_json, report_header, reports_dir, summarize_order_rows, write_report_pair


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2X_RUNTIME_RECONCILIATION.json"
DEFAULT_SIGNAL_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_signal_log_xauusd.csv")
DEFAULT_ORDER_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_order_log_xauusd.csv")
DEFAULT_STARTUP_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_startup_xauusd.csv")


def generate_phase2x_runtime_reconciliation(root: Path, signal_log: Path = DEFAULT_SIGNAL_LOG, order_log: Path = DEFAULT_ORDER_LOG, startup_log: Path = DEFAULT_STARTUP_LOG, output_json: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    signals = read_csv(signal_log)
    orders = read_csv(order_log)
    startups = read_csv(startup_log)
    audit = read_json(reports_dir(root) / "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.json")
    latest_order_magic = orders[-1].get("magic", "") if orders else ""
    latest_startup_magic = startups[-1].get("magic", "") if startups else ""
    checks = [
        {"name": "signal_log_present", "status": "PASS" if signal_log.exists() else "PENDING_RUNTIME_EVIDENCE", "evidence": str(signal_log)},
        {"name": "order_log_present", "status": "PASS" if order_log.exists() else "PENDING_RUNTIME_EVIDENCE", "evidence": str(order_log)},
        {"name": "startup_log_present", "status": "PASS" if startup_log.exists() else "PENDING_RUNTIME_EVIDENCE", "evidence": str(startup_log)},
        {"name": "new_runtime_magic_931000", "status": "PASS" if str(latest_order_magic or latest_startup_magic) == str(ACTIVE_MAGIC) else "PENDING_RUNTIME_EVIDENCE", "evidence": f"latest_order_magic={latest_order_magic}; latest_startup_magic={latest_startup_magic}; old {OLD_MAGIC} may be historical only"},
        {"name": "runtime_attachment_audit_present", "status": "PASS" if audit else "PENDING_RUNTIME_EVIDENCE", "evidence": "P2WEAKNESS runtime attachment audit"},
    ]
    payload = {
        "status": "FAIL" if any(c["status"] == "FAIL" for c in checks) else ("PENDING" if any(c["status"].startswith("PENDING") for c in checks) else "PASS"),
        "created_at_utc": now_utc(),
        "authority": "Phase 2X runtime reconciliation. Report-only; no MT5 runtime is modified.",
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "signal_rows": len(signals),
        "startup_rows": len(startups),
        "order_summary": summarize_order_rows(orders),
        "runtime_attachment_status": audit.get("status", "MISSING"),
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Phase 2X Runtime Reconciliation", payload)
    lines.extend(boundary_lines())
    lines.extend([
        f"- Signal rows: `{payload['signal_rows']}`",
        f"- Startup rows: `{payload['startup_rows']}`",
        f"- Order summary: `{payload['order_summary']}`",
        f"- Runtime attachment status: `{payload['runtime_attachment_status']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2X runtime reconciliation.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--signal-log", type=Path, default=DEFAULT_SIGNAL_LOG)
    parser.add_argument("--order-log", type=Path, default=DEFAULT_ORDER_LOG)
    parser.add_argument("--startup-log", type=Path, default=DEFAULT_STARTUP_LOG)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_phase2x_runtime_reconciliation(args.root, args.signal_log, args.order_log, args.startup_log, args.output_json)
    print(f"Phase 2X runtime reconciliation: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
