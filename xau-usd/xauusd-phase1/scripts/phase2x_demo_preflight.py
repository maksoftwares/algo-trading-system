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
    MAX_ACCOUNT_ORDERS_PER_DAY,
    MAX_ESTIMATED_COST_R,
    MAX_FAMILY_OPEN_POSITIONS,
    MAX_MEASURED_SPREAD_POINTS,
    MAX_ORDERS_PER_DAY,
    OLD_MAGIC,
    PHASE2X_STATUS_FAIL,
    PHASE2X_STATUS_PASS,
    PHASE2X_STATUS_PENDING_OWNER,
    PHASE2X_STATUS_PENDING_RUNTIME,
    TARGET_SYMBOL,
    boundary_lines,
    check,
    checks_table,
    now_utc,
    overall_status,
    parse_set_file,
    read_json,
    read_status_markdown,
    report_header,
    reports_dir,
    write_report_pair,
)


DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2X_DEMO_PREFLIGHT_REPORT.json"
DEFAULT_LOCAL_PRESET = Path("local") / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set"


def generate_phase2x_demo_preflight(root: Path, local_preset: Path | None = None, output_json: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    report_dir = reports_dir(root)
    output_json = (output_json or root / DEFAULT_JSON).resolve()
    local_preset = (local_preset or root / DEFAULT_LOCAL_PRESET).resolve()
    readiness = read_status_markdown(report_dir / "PHASE2_READINESS_REPORT.md")
    owner = read_json(report_dir / "PHASE2X_OWNER_AUTHORIZATION_STATUS.json")
    safe = read_json(report_dir / "PHASE2X_SAFE_DEFAULTS_REPORT.json")
    runtime_cleanup = read_json(report_dir / "PHASE2X_RUNTIME_CLEANUP_REPORT.json")
    kill_switch = read_json(report_dir / "PHASE2X_KILL_SWITCH_BLOCK_TEST_REPORT.json")
    audit = read_json(report_dir / "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT.json")
    preset = parse_set_file(local_preset)
    checks = [
        check("canonical_phase2_readiness_is_fail_or_blocked", PHASE2X_STATUS_PASS if readiness in {"FAIL", "BLOCKED", "NO-GO"} else PHASE2X_STATUS_FAIL, f"PHASE2_READINESS_REPORT.md status={readiness}"),
        _cost_suspended_lifecycle_check(read_status_markdown(report_dir / "COST_SUSPENDED_LIFECYCLE_REPORT.md")),
        _report_status_check("source_governance_parity", read_status_markdown(report_dir / "P2WEAKNESS_BR_V1_SOURCE_GOVERNANCE_PARITY.md")),
        _report_status_check("magic_collision_audit", read_status_markdown(report_dir / "P2WEAKNESS_BR_V1_MAGIC_COLLISION_AUDIT.md")),
        _report_status_check("clean_clone_reconciliation", read_status_markdown(report_dir / "P2WEAKNESS_BR_V1_CLEAN_CLONE_RECONCILIATION.md")),
        _json_status_check("safe_preset_non_executing", safe, "PASS"),
        _json_status_check("owner_authorization_status", owner, "PASS", pending=PHASE2X_STATUS_PENDING_OWNER),
        check("owner_authorization_local_file_present", PHASE2X_STATUS_PASS if local_preset.exists() else PHASE2X_STATUS_PENDING_OWNER, str(local_preset)),
        _preset_check(preset, "owner_local_preset_uses_931000", "InpMagicNumber", str(ACTIVE_MAGIC)),
        _preset_check(preset, "owner_local_preset_fixed_lot_lte_0_01", "InpFixedLot", max_float=FIXED_LOT),
        _preset_check(preset, "owner_local_preset_max_orders_per_day_lte_3", "InpMaxOrdersPerDay", max_int=MAX_ORDERS_PER_DAY),
        _preset_check(preset, "owner_local_preset_max_account_orders_per_day_lte_3", "InpMaxAccountOrdersPerDay", max_int=MAX_ACCOUNT_ORDERS_PER_DAY),
        _preset_check(preset, "owner_local_preset_max_family_open_positions_eq_1", "InpMaxFamilyOpenPositions", str(MAX_FAMILY_OPEN_POSITIONS)),
        _preset_check(preset, "owner_local_preset_cost_r_lte_0_15", "InpMaxEstimatedCostR", max_float=MAX_ESTIMATED_COST_R),
        _preset_check(preset, "owner_local_preset_spread_lte_75", "InpMaxMeasuredSpreadPoints", max_float=MAX_MEASURED_SPREAD_POINTS),
        _preset_check(preset, "target_symbol_xauusd", "InpTargetSymbol", TARGET_SYMBOL),
        check("owner_local_preset_not_committed", PHASE2X_STATUS_PASS if "local" in [part.lower() for part in local_preset.parts] else PHASE2X_STATUS_FAIL, str(local_preset)),
        check("old_magic_930101_not_allowed_for_new_deployment", PHASE2X_STATUS_PASS if preset.get("InpMagicNumber") != str(OLD_MAGIC) else PHASE2X_STATUS_FAIL, f"preset_magic={preset.get('InpMagicNumber', '')}"),
        _json_status_check("runtime_cleanup_report_pass", runtime_cleanup, "PASS", pending=PHASE2X_STATUS_PENDING_RUNTIME),
        _json_status_check("kill_switch_block_test_pass", kill_switch, "PASS", pending=PHASE2X_STATUS_PENDING_RUNTIME),
        check("demo_account_isolation_evidence", PHASE2X_STATUS_PASS if owner.get("status") == "PASS" and owner.get("masked_authorized_account_login") else PHASE2X_STATUS_PENDING_OWNER, "owner authorization masks account when available"),
        check("server_marker_demo", PHASE2X_STATUS_PASS if _demo_marker(preset.get("InpExpectedServerMarker", "")) else (PHASE2X_STATUS_PENDING_OWNER if not preset else PHASE2X_STATUS_FAIL), f"server_marker={preset.get('InpExpectedServerMarker', '')!r}"),
        check("no_live_server_marker_in_authorized_runtime", PHASE2X_STATUS_PASS if "live" not in str(preset.get("InpExpectedServerMarker", "")).lower() and "real" not in str(preset.get("InpExpectedServerMarker", "")).lower() else PHASE2X_STATUS_FAIL, f"server_marker={preset.get('InpExpectedServerMarker', '')!r}"),
        check("no_canonical_promotion", PHASE2X_STATUS_PASS, "Phase 2X does not change PHASE2_READINESS_REPORT.md or cost-suspension reports."),
        check("runtime_attachment_audit_available", PHASE2X_STATUS_PASS if audit else PHASE2X_STATUS_PENDING_RUNTIME, "P2WEAKNESS runtime attachment audit is used as evidence."),
    ]
    payload = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Phase 2X demo preflight. Can approve only quarantined experimental demo execution; cannot approve canonical Phase 2, live trading, or real capital.",
        "phase2x_demo_execution_authorized": False,
        "canonical_phase2_authorized": False,
        "live_trading_authorized": False,
        "real_capital_authorized": False,
        "local_preset": str(local_preset),
        "checks": checks,
    }
    payload["phase2x_demo_execution_authorized"] = payload["status"] == "PASS"
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _report_status_check(name: str, status: str) -> dict[str, str]:
    return check(name, PHASE2X_STATUS_PASS if status == "PASS" else PHASE2X_STATUS_FAIL, f"status={status}")


def _cost_suspended_lifecycle_check(status: str) -> dict[str, str]:
    return check(
        "cost_suspended_lifecycle_acknowledged",
        PHASE2X_STATUS_PASS if status == "COST_SUSPENDED_CANONICAL" else PHASE2X_STATUS_FAIL,
        f"status={status}; expected=COST_SUSPENDED_CANONICAL",
    )


def _json_status_check(name: str, payload: dict[str, Any], expected: str, pending: str = PHASE2X_STATUS_PENDING_RUNTIME) -> dict[str, str]:
    if not payload:
        return check(name, pending, "report missing")
    status = payload.get("status", "")
    return check(name, PHASE2X_STATUS_PASS if status == expected else (pending if str(status).startswith("PENDING") else PHASE2X_STATUS_FAIL), f"status={status}; expected={expected}")


def _preset_check(values: dict[str, str], name: str, key: str, expected: str | None = None, max_int: int | None = None, max_float: float | None = None) -> dict[str, str]:
    if not values:
        return check(name, PHASE2X_STATUS_PENDING_OWNER, "local owner-authorized preset missing")
    raw = values.get(key, "")
    ok = raw == expected if expected is not None else True
    if max_int is not None:
        try:
            ok = int(float(raw)) <= max_int
        except ValueError:
            ok = False
    if max_float is not None:
        try:
            ok = float(raw) <= max_float
        except ValueError:
            ok = False
    return check(name, PHASE2X_STATUS_PASS if ok else PHASE2X_STATUS_FAIL, f"{key}={raw!r}")


def _demo_marker(value: str) -> bool:
    text = value.lower()
    return "demo" in text or "practice" in text


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Phase 2X Demo Preflight Report", payload)
    lines.extend(boundary_lines())
    lines.extend([
        f"- Phase 2X demo execution authorized: `{payload['phase2x_demo_execution_authorized']}`",
        f"- Local preset: `{payload['local_preset']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2X demo preflight report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--local-preset", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_phase2x_demo_preflight(args.root, args.local_preset, args.output_json)
    print(f"Phase 2X demo preflight: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
