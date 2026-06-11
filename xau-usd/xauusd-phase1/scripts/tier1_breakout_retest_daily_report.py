from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tier1_breakout_retest_common import (
    DEFAULT_PORTABLE_ROOT,
    STATUS_PASS,
    STATUS_PENDING_RUNTIME,
    bucket_dubai_equivalent,
    boundary_lines,
    check,
    checks_table,
    filter_rows_for_date,
    now_utc,
    overall_status,
    parse_mt5_datetime,
    percentile,
    read_csv,
    report_header,
    reports_dir,
    session_bucket,
    summarize_order_rows,
    write_report_pair,
)


DEFAULT_ORDER_LOG = DEFAULT_PORTABLE_ROOT / "MQL5" / "Files" / "tier1_bestea_order_log_xauusd.csv"


def generate_tier1_daily_report(
    root: Path,
    review_date: str | None = None,
    order_log: Path = DEFAULT_ORDER_LOG,
    history_csv: Path | None = None,
    output_json: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    review_date = review_date or datetime.now(timezone.utc).strftime("%Y_%m_%d")
    output_json = (output_json or root / "outputs" / "reports" / f"TIER1_BREAKOUT_RETEST_DAILY_REPORT_{review_date}.json").resolve()
    rows = filter_rows_for_date(read_csv(order_log), review_date)
    history_rows = filter_rows_for_date(read_csv(history_csv), review_date) if history_csv else []
    value_date = _date_from_review_date(review_date)
    session_summary = _session_summary(rows, value_date)
    history_summary = _history_summary(history_rows)
    checks = [
        check("order_log_present", STATUS_PASS if order_log.exists() else STATUS_PENDING_RUNTIME, str(order_log)),
        check("order_rows_for_date_present", STATUS_PASS if rows else STATUS_PENDING_RUNTIME, f"rows={len(rows)}"),
        check("closed_trade_history_present", STATUS_PASS if history_rows else STATUS_PENDING_RUNTIME, str(history_csv or "not supplied")),
    ]
    payload: dict[str, Any] = {
        "status": overall_status(checks),
        "created_at_utc": now_utc(),
        "authority": "Tier-1 breakout_retest daily report. Experimental demo evidence only; net expectancy R after measured cost is the judgment metric.",
        "date": review_date,
        "order_log": str(order_log),
        "history_csv": str(history_csv or ""),
        "order_summary": summarize_order_rows(rows),
        "closed_trade_summary": history_summary,
        "session_buckets": session_summary,
        "standing_annotations": {
            "ny_morning_server_bucket": "12:00-15:59 server",
            "november_dst_prediction": "After US DST ends on Sunday 2026-11-01, the NY-morning money window should appear as 17:00-20:59 Dubai while remaining 12:00-15:59 server.",
            "us_holiday_note": "Flag US market holidays and early closes; a flat NY morning on those days confirms the NY-clock mechanism rather than edge decay.",
            "direction_split_required": "Track BUY vs SELL inside NY_MORNING; direction dominance is regime, not the session mechanism.",
            "sample_discipline": "Week 1 is a checkpoint; wait for at least 150 fresh closed trades before structural conclusions.",
        },
        "checks": checks,
    }
    write_report_pair(output_json, payload, _render(payload))
    return payload


def _date_from_review_date(value: str):
    normalized = value.replace("_", "-").replace(".", "-")
    return datetime.strptime(normalized, "%Y-%m-%d").date()


def _session_summary(rows: list[dict[str, str]], value_date) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        bucket = session_bucket(row.get("timestamp_broker", ""))
        buckets.setdefault(bucket, []).append(row)
    output: dict[str, Any] = {}
    for bucket in ("NY_MORNING", "NY_AFTERNOON", "ASIA", "LONDON_PRE", "HALT", "UNKNOWN"):
        bucket_rows = buckets.get(bucket, [])
        costs = [_float(row.get("estimated_cost_R")) for row in bucket_rows]
        costs = [value for value in costs if value is not None]
        sent = [row for row in bucket_rows if row.get("action") == "ORDER_SEND_OK"]
        buys = sum(1 for row in sent if row.get("direction") == "LONG")
        sells = sum(1 for row in sent if row.get("direction") == "SHORT")
        output[bucket] = {
            "server_bucket": _server_bucket_label(bucket),
            "dubai_equivalent": bucket_dubai_equivalent(bucket, value_date),
            "rows": len(bucket_rows),
            "orders_sent": len(sent),
            "guard_blocks": sum(1 for row in bucket_rows if row.get("action") == "GUARD_BLOCK"),
            "cost_r_mean": round(mean(costs), 6) if costs else None,
            "cost_r_p95": percentile(costs, 95) if costs else None,
            "buy_orders": buys,
            "sell_orders": sells,
            "wr": None,
            "net_r_after_measured_cost": None,
        }
    return output


def _history_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return {
            "closed_trades": 0,
            "wr": None,
            "net_aed": None,
            "net_r_after_measured_cost": None,
            "max_dd": None,
            "status": STATUS_PENDING_RUNTIME,
        }
    profits = [_float(row.get("profit") or row.get("net_aed") or row.get("pnl")) for row in rows]
    profits = [value for value in profits if value is not None]
    wins = [value for value in profits if value > 0]
    net_r_values = [_float(row.get("net_r_after_measured_cost") or row.get("net_R_after_measured_cost") or row.get("net_r")) for row in rows]
    net_r_values = [value for value in net_r_values if value is not None]
    return {
        "closed_trades": len(rows),
        "wr": round(len(wins) / len(profits), 4) if profits else None,
        "net_aed": round(sum(profits), 2) if profits else None,
        "net_r_after_measured_cost": round(sum(net_r_values), 4) if net_r_values else None,
        "max_dd": None,
        "status": STATUS_PASS,
    }


def _server_bucket_label(bucket: str) -> str:
    return {
        "NY_MORNING": "12:00-15:59 server",
        "NY_AFTERNOON": "16:00-20:59 server",
        "ASIA": "23:00-06:59 server",
        "LONDON_PRE": "07:00-11:59 server",
        "HALT": "21:00-22:59 server",
        "UNKNOWN": "unknown",
    }.get(bucket, "unknown")


def _float(value: object) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value))
    except ValueError:
        return None


def _render(payload: dict[str, Any]) -> str:
    lines = report_header(f"Tier-1 Breakout Retest Daily Report {payload['date']}", payload)
    lines.extend(boundary_lines())
    lines.extend([
        f"- Order summary: `{payload['order_summary']}`",
        f"- Closed trade summary: `{payload['closed_trade_summary']}`",
        "",
        "## Session Buckets",
        "",
        "| Bucket | Server | Dubai | Rows | Sent | Blocks | Cost R Mean | Cost R P95 | BUY | SELL | Net R |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for bucket, row in payload["session_buckets"].items():
        lines.append(
            f"| {bucket} | {row['server_bucket']} | {row['dubai_equivalent']} | {row['rows']} | {row['orders_sent']} | {row['guard_blocks']} | "
            f"{row['cost_r_mean']} | {row['cost_r_p95']} | {row['buy_orders']} | {row['sell_orders']} | {row['net_r_after_measured_cost']} |"
        )
    lines.extend([
        "",
        "## Standing Annotations",
        "",
    ])
    for key, value in payload["standing_annotations"].items():
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Checks",
        "",
        *checks_table(payload["checks"]),
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Tier-1 breakout_retest daily/session report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--date", default=None)
    parser.add_argument("--order-log", type=Path, default=DEFAULT_ORDER_LOG)
    parser.add_argument("--history-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = generate_tier1_daily_report(args.root, args.date, args.order_log, args.history_csv, args.output_json)
    print(f"Tier-1 daily report: {payload['status']}")
    return 0 if payload["status"] == STATUS_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
