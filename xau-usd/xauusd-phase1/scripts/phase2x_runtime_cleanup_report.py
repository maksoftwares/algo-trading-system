from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase2x_common import (
    ACTIVE_MAGIC,
    OLD_MAGIC,
    PHASE2X_STATUS_FAIL,
    PHASE2X_STATUS_PASS,
    PHASE2X_STATUS_PENDING_MANUAL,
    boundary_lines,
    check,
    checks_table,
    now_utc,
    overall_status,
    read_json,
    report_header,
    reports_dir,
    write_report_pair,
)


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2X_RUNTIME_CLEANUP_REPORT.json"


def generate_phase2x_runtime_cleanup_report(root: Path, output_json: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    audit = read_json(reports_dir(root) / "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.json")
    old = audit.get("old_magic_930101", {})
    hardened = audit.get("hardened_magic_931000", {})
    reviewer = audit.get("reviewer_questions", {})
    checks = [
        check("old_magic_930101_positions_closed_or_absent", PHASE2X_STATUS_PASS if old.get("open_positions") == 0 else PHASE2X_STATUS_FAIL, f"open_positions={old.get('open_positions')}"),
        check("old_magic_930101_orders_closed_or_absent", PHASE2X_STATUS_PASS if old.get("open_orders") == 0 else PHASE2X_STATUS_FAIL, f"open_orders={old.get('open_orders')}"),
        check("old_magic_930101_charts_detached_or_absent", _profile_status(reviewer.get("is_any_old_930101_ea_still_attached")), f"answer={reviewer.get('is_any_old_930101_ea_still_attached')}"),
        check("current_magic_931000_ready", PHASE2X_STATUS_PASS if hardened.get("deployed_source_hardened") is True else PHASE2X_STATUS_PENDING_MANUAL, f"hardened_deployed={hardened.get('deployed_source_hardened')}"),
        check("no_open_family_exposure", PHASE2X_STATUS_PASS if audit.get("open_exposure_audit", {}).get("orders") == [] and audit.get("open_exposure_audit", {}).get("positions") == [] else PHASE2X_STATUS_FAIL, "P2WEAKNESS relevant exposure from MT5 bridge"),
        check("no_existing_p2weakness_orders_today", PHASE2X_STATUS_PENDING_MANUAL, "Requires owner/reviewer confirmation from broker history before attach."),
        check("kill_switch_file_tested", PHASE2X_STATUS_PENDING_MANUAL, "Requires PHASE2X_KILL_SWITCH_BLOCK_TEST_REPORT.md PASS."),
        check("demo_account_confirmed", PHASE2X_STATUS_PENDING_MANUAL, "Requires fresh startup/runtime evidence after attach."),
        check("owner_authorization_valid", PHASE2X_STATUS_PENDING_MANUAL, "Requires local owner authorization status PASS."),
    ]
    payload = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Phase 2X runtime cleanup report. Report-only; no MT5 runtime is modified.",
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "source_runtime_attachment_audit": str(reports_dir(root) / "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.json"),
        "old_magic": OLD_MAGIC,
        "active_magic": ACTIVE_MAGIC,
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _profile_status(answer: object) -> str:
    if answer in {"NO", "NO_PROFILE_EVIDENCE"}:
        return PHASE2X_STATUS_PASS
    if answer == "YES":
        return PHASE2X_STATUS_FAIL
    return PHASE2X_STATUS_PENDING_MANUAL


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Phase 2X Runtime Cleanup Report", payload)
    lines.extend(boundary_lines())
    lines.extend(["## Checks", "", *checks_table(payload["checks"]), ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2X runtime cleanup report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_phase2x_runtime_cleanup_report(args.root, args.output_json)
    print(f"Phase 2X runtime cleanup: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
