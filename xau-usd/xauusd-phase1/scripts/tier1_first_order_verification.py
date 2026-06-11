from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tier1_breakout_retest_common import (
    CANDIDATE,
    DEFAULT_LOCAL_PRESET,
    DEFAULT_PORTABLE_ROOT,
    DERIVED_MAGIC,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_PENDING_MANUAL,
    STATUS_PENDING_RUNTIME,
    TARGET_SYMBOL,
    boundary_lines,
    check,
    checks_table,
    mask_account,
    now_utc,
    overall_status,
    parse_set_file,
    read_csv,
    report_header,
    write_report_pair,
)


DEFAULT_ORDER_LOG = DEFAULT_PORTABLE_ROOT / "MQL5" / "Files" / "tier1_bestea_order_log_xauusd.csv"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "TIER1_FIRST_ORDER_VERIFICATION.json"


def generate_tier1_first_order_verification(
    root: Path,
    order_log: Path = DEFAULT_ORDER_LOG,
    local_preset: Path | None = None,
    output_json: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    local_preset = (local_preset or root / DEFAULT_LOCAL_PRESET).resolve()
    output_json = (output_json or root / DEFAULT_OUTPUT_JSON).resolve()
    preset = parse_set_file(local_preset)
    rows = [row for row in read_csv(order_log) if row.get("action") == "ORDER_SEND_OK"]
    first = rows[0] if rows else {}
    checks = [
        check("order_log_present", STATUS_PASS if order_log.exists() else STATUS_PENDING_RUNTIME, str(order_log)),
        check("first_order_present", STATUS_PASS if first else STATUS_PENDING_RUNTIME, "Waiting for first ORDER_SEND_OK row."),
    ]
    if first:
        checks.extend(_first_order_checks(first, preset))
    payload: dict[str, Any] = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Tier-1 first-order verification for the isolated breakout_retest demo lane.",
        "order_log": str(order_log),
        "local_preset": str(local_preset),
        "first_order": _masked_order(first),
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _first_order_checks(row: dict[str, str], preset: dict[str, str]) -> list[dict[str, str]]:
    account = row.get("account_login", "")
    expected_account = preset.get("InpAllowedAccountLoginsCsv", "")
    return [
        check("account_login_matches_allowlist", STATUS_PASS if account == expected_account else STATUS_FAIL, f"account={mask_account(account)}; allowlist={mask_account(expected_account)}"),
        check("symbol_xauusd", STATUS_PASS if row.get("symbol") == TARGET_SYMBOL else STATUS_FAIL, f"symbol={row.get('symbol', '')!r}"),
        check("candidate_breakout_retest", STATUS_PASS if row.get("candidate") == CANDIDATE else STATUS_FAIL, f"candidate={row.get('candidate', '')!r}"),
        check("magic_920101", STATUS_PASS if _to_int(row.get("magic")) == DERIVED_MAGIC else STATUS_FAIL, f"magic={row.get('magic', '')!r}"),
        check("broker_action_true", STATUS_PASS if row.get("broker_action_allowed") == "true" else STATUS_FAIL, f"broker_action_allowed={row.get('broker_action_allowed', '')!r}"),
        check("dry_run_false", STATUS_PASS if row.get("dry_run") == "false" else STATUS_FAIL, f"dry_run={row.get('dry_run', '')!r}"),
        check("lot_0_01", STATUS_PASS if _to_float(row.get("volume")) == 0.01 else STATUS_FAIL, f"volume={row.get('volume', '')!r}"),
        check("hard_sl_present", STATUS_PASS if (_to_float(row.get("sl")) or 0.0) > 0.0 else STATUS_FAIL, f"sl={row.get('sl', '')!r}"),
        check("hard_tp_present", STATUS_PASS if (_to_float(row.get("tp")) or 0.0) > 0.0 else STATUS_FAIL, f"tp={row.get('tp', '')!r}"),
        check("estimated_cost_r_lte_0_30", STATUS_PASS if (_to_float(row.get("estimated_cost_R")) or 999.0) <= 0.30 else STATUS_FAIL, f"estimated_cost_R={row.get('estimated_cost_R', '')!r}"),
        check("stop_distance_logged", STATUS_PASS if (_to_float(row.get("stop_distance_points")) or 0.0) > 0.0 else STATUS_FAIL, f"stop_distance_points={row.get('stop_distance_points', '')!r}"),
        check("comment_history_verification", STATUS_PENDING_MANUAL, "Order log does not include request.comment; verify MT5 history comment is P2DEMO_br_XAUUSD."),
    ]


def _masked_order(row: dict[str, str]) -> dict[str, str]:
    if not row:
        return {}
    masked = dict(row)
    if "account_login" in masked:
        masked["account_login"] = mask_account(masked["account_login"])
    return masked


def _to_int(value: object) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _to_float(value: object) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value))
    except ValueError:
        return None


def _render(payload: dict[str, Any]) -> str:
    lines = report_header("Tier-1 First Order Verification", payload)
    lines.extend(boundary_lines())
    lines.extend([
        f"- Order log: `{payload['order_log']}`",
        f"- Local preset: `{payload['local_preset']}`",
        f"- First order: `{payload['first_order']}`",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Tier-1 first-order verification report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--order-log", type=Path, default=DEFAULT_ORDER_LOG)
    parser.add_argument("--local-preset", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_tier1_first_order_verification(args.root, args.order_log, args.local_preset, args.output_json)
    print(f"Tier-1 first-order verification: {payload['status']}")
    return 0 if payload["status"] == STATUS_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
