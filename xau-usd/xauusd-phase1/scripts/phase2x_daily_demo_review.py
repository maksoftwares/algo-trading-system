from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from phase2x_common import ACTIVE_MAGIC, DEFAULT_OWNER_JSON, FIXED_LOT, MAX_ESTIMATED_COST_R, MAX_FAMILY_OPEN_POSITIONS, MAX_ORDERS_PER_DAY, TARGET_SYMBOL, boundary_lines, checks_table, now_utc, read_csv, read_json, report_header, summarize_order_rows, write_report_pair


DEFAULT_ORDER_LOG = Path("C:/MT5PortableP2WeaknessDemo/MQL5/Files/p2weakness_br_v1_order_log_xauusd.csv")


def generate_phase2x_daily_demo_review(
    root: Path,
    review_date: str | None = None,
    order_log: Path = DEFAULT_ORDER_LOG,
    output_json: Path | None = None,
    owner_json: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    review_date = review_date or datetime.now(timezone.utc).strftime("%Y_%m_%d")
    output_json = (output_json or root / "outputs" / "reports" / f"PHASE2X_DAILY_DEMO_REVIEW_{review_date}.json").resolve()
    owner_json = (owner_json or root / DEFAULT_OWNER_JSON).resolve()
    rows_for_date = _filter_date(read_csv(order_log), review_date)
    rows, legacy_rows, authorization_cutoff = _split_legacy_rows(rows_for_date, owner_json)
    summary = summarize_order_rows(rows)
    checks = _daily_checks(rows, order_log, legacy_rows, authorization_cutoff)
    status = "FAIL" if any(c["status"] == "FAIL" for c in checks) else ("PENDING" if not rows else "PASS")
    decision = "NO" if status == "FAIL" else ("OWNER REVIEW REQUIRED" if status == "PENDING" else "YES")
    payload = {
        "status": status,
        "created_at_utc": now_utc(),
        "authority": "Phase 2X daily demo review. Experimental demo evidence only; no canonical Phase 2, live trading, or real capital authorization.",
        "date": review_date,
        "order_log": str(order_log),
        "owner_authorization_file": str(owner_json),
        "owner_authorization_cutoff_utc": authorization_cutoff.isoformat().replace("+00:00", "Z") if authorization_cutoff else "",
        "legacy_pre_authorization_rows": len(legacy_rows),
        "legacy_pre_authorization_summary": summarize_order_rows(legacy_rows),
        "order_summary": summary,
        "continue_tomorrow": decision,
        "continue_reason": "Hard-stop checks passed." if decision == "YES" else "Owner/runtime evidence incomplete or hard-stop condition found.",
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _filter_date(rows: list[dict[str, str]], review_date: str) -> list[dict[str, str]]:
    prefix = review_date.replace("_", ".")
    return [row for row in rows if str(row.get("timestamp_broker", "")).startswith(prefix) or str(row.get("timestamp_utc", "")).startswith(prefix)]


def _split_legacy_rows(rows: list[dict[str, str]], owner_json: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], datetime | None]:
    cutoff = _authorization_cutoff(owner_json)
    if cutoff is None:
        return rows, [], None
    active_rows: list[dict[str, str]] = []
    legacy_rows: list[dict[str, str]] = []
    for row in rows:
        row_time = _row_utc_time(row)
        if row_time is not None and row_time < cutoff:
            legacy_rows.append(row)
        else:
            active_rows.append(row)
    return active_rows, legacy_rows, cutoff


def _authorization_cutoff(owner_json: Path) -> datetime | None:
    value = read_json(owner_json).get("approved_at_utc")
    if not value:
        return None
    return _parse_datetime(value)


def _row_utc_time(row: dict[str, str]) -> datetime | None:
    for key in ("timestamp_utc", "timestamp_broker"):
        parsed = _parse_datetime(row.get(key, ""))
        if parsed is not None:
            return parsed
    return None


def _parse_datetime(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _daily_checks(rows: list[dict[str, str]], order_log: Path, legacy_rows: list[dict[str, str]], authorization_cutoff: datetime | None) -> list[dict[str, str]]:
    checks = [{"name": "order_log_present", "status": "PASS" if order_log.exists() else "PENDING_RUNTIME_EVIDENCE", "evidence": str(order_log)}]
    if legacy_rows:
        cutoff_text = authorization_cutoff.isoformat().replace("+00:00", "Z") if authorization_cutoff else "none"
        checks.append({"name": "legacy_pre_owner_authorization_rows_excluded", "status": "PASS", "evidence": f"legacy_rows={len(legacy_rows)}; cutoff_utc={cutoff_text}"})
    if not rows:
        checks.append({"name": "daily_rows_present", "status": "PENDING_RUNTIME_EVIDENCE", "evidence": "No rows for review date."})
        return checks
    sent = [row for row in rows if row.get("action") == "ORDER_SEND_OK"]
    checks.extend([
        _all_check("magic_931000", rows, lambda row: str(row.get("magic", "")) == str(ACTIVE_MAGIC), "All rows must use magic 931000."),
        _all_check("symbol_xauusd", rows, lambda row: row.get("symbol") == TARGET_SYMBOL, "All rows must be XAUUSD."),
        _all_check("fixed_lot_lte_0_01", sent, lambda row: _float(row.get("lot")) <= FIXED_LOT, "Sent lots must be <=0.01."),
        {"name": "orders_per_day_lte_3", "status": "PASS" if len(sent) <= MAX_ORDERS_PER_DAY else "FAIL", "evidence": f"sent_orders={len(sent)}"},
        _all_check("family_open_positions_lte_1", rows, lambda row: _int(row.get("family_open_exposure")) <= MAX_FAMILY_OPEN_POSITIONS, "Family exposure must be <=1."),
        _all_check("estimated_cost_r_lte_0_15", rows, lambda row: _float(row.get("estimated_cost_R")) <= MAX_ESTIMATED_COST_R, "Cost R must be <=0.15."),
        _all_check("no_live_or_real_marker", rows, lambda row: "live" not in str(row.get("account_server", "")).lower() and "real" not in str(row.get("account_server", "")).lower(), "Server marker must not be live/real."),
    ])
    return checks


def _all_check(name: str, rows: list[dict[str, str]], predicate, evidence: str) -> dict[str, str]:
    if not rows:
        return {"name": name, "status": "PASS", "evidence": "No applicable rows."}
    failures = sum(1 for row in rows if not predicate(row))
    return {"name": name, "status": "PASS" if failures == 0 else "FAIL", "evidence": f"{evidence} failures={failures}; rows={len(rows)}"}


def _float(value: object) -> float:
    try:
        return float(str(value))
    except ValueError:
        return 0.0


def _int(value: object) -> int:
    try:
        return int(float(str(value)))
    except ValueError:
        return 0


def _render(payload: dict[str, Any]) -> str:
    lines = report_header(f"Phase 2X Daily Demo Review {payload['date']}", payload)
    lines.extend(boundary_lines())
    lines.extend([
        f"- Owner authorization cutoff UTC: `{payload['owner_authorization_cutoff_utc'] or 'none'}`",
        f"- Legacy pre-authorization rows excluded: `{payload['legacy_pre_authorization_rows']}`",
        f"- Legacy pre-authorization summary: `{payload['legacy_pre_authorization_summary']}`",
        f"- Order summary: `{payload['order_summary']}`",
        f"- Continue tomorrow: `{payload['continue_tomorrow']}`",
        f"- Reason: {payload['continue_reason']}",
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2X daily demo review.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--date", default=None)
    parser.add_argument("--order-log", type=Path, default=DEFAULT_ORDER_LOG)
    parser.add_argument("--owner-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_phase2x_daily_demo_review(args.root, args.date, args.order_log, args.output_json, args.owner_json)
    print(f"Phase 2X daily review: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
