from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_JSON = PHASE1_ROOT / "outputs" / "reports" / "XAU_920101_BREAKOUT_RETEST_VARIANT_BACKTEST_Q2_2026.json"
DEFAULT_REPORT_MD = PHASE1_ROOT / "outputs" / "reports" / "XAU_920101_BREAKOUT_RETEST_FAILURE_FORENSIC_2026_07_01.md"
DEFAULT_REPORT_JSON = PHASE1_ROOT / "outputs" / "reports" / "XAU_920101_BREAKOUT_RETEST_FAILURE_FORENSIC_2026_07_01.json"

DEFAULT_KEY_VARIANTS = [
    "baseline_24h_no_smart",
    "current_24h_h1_smart",
    "current_24h_h1_cost010",
    "server_16_19_h1_smart",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose why XAU 920101 breakout-retest backtests are failing.")
    parser.add_argument("--source-json", type=Path, default=DEFAULT_SOURCE_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    args = parser.parse_args()
    payload = build_payload(args.source_json)
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    args.report_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"Wrote {args.report_md}")
    print(f"Wrote {args.report_json}")


def build_payload(source_json: Path) -> dict[str, Any]:
    source = json.loads(source_json.read_text(encoding="utf-8"))
    variants = {variant["name"]: variant for variant in source["variants"]}
    display_variants = [
        name
        for name in DEFAULT_KEY_VARIANTS + [name for name in variants if name.startswith("repair_")]
        if name in variants
    ]
    analyzed: dict[str, Any] = {}
    for name in display_variants:
        variant = variants[name]
        trades = read_rows(Path(variant["trade_csv"]))
        orders = read_rows(Path(variant["order_csv"]))
        order_by_deal = {row.get("deal_ticket", ""): row for row in orders if row.get("action") == "ORDER_SEND_OK"}
        enriched = [enrich_trade(trade, order_by_deal.get(trade.get("entry_deal", ""), {})) for trade in trades]
        analyzed[name] = {
            "label": variant["label"],
            "note": variant["note"],
            "trade_csv": variant["trade_csv"],
            "order_csv": variant["order_csv"],
            "management_csv": variant.get("management_csv", ""),
            "overall": aggregate(enriched),
            "break_even_win_rate_pct": break_even_win_rate(enriched),
            "direction": grouped(enriched, "direction"),
            "session": grouped(enriched, "session"),
            "hour": grouped(enriched, "hour"),
            "month": grouped(enriched, "month"),
            "exit_type": grouped(enriched, "exit_type"),
            "cost_bucket": grouped(enriched, "cost_bucket"),
            "stop_bucket": grouped(enriched, "stop_bucket"),
            "hold_bucket": grouped(enriched, "hold_bucket"),
            "worst_days": worst_days(enriched, 8),
            "best_days": best_days(enriched, 5),
            "robustness": robustness(enriched),
            "order_activity": summarize_orders(orders),
            "management_activity": variant.get("management_activity", {}),
        }
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "OFFLINE_FORENSIC_NO_RUNTIME_CHANGE",
        "source_json": str(source_json),
        "period": source.get("scope", {}).get("period", "unknown"),
        "display_variants": display_variants,
        "variants": analyzed,
        "findings": derive_findings(analyzed),
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def enrich_trade(trade: dict[str, str], order: dict[str, str]) -> dict[str, Any]:
    enriched: dict[str, Any] = dict(trade)
    pnl = to_float(trade.get("profit_aed"))
    entry_time = parse_mt5_time(trade.get("entry_time", ""))
    exit_time = parse_mt5_time(trade.get("exit_time", ""))
    hold_minutes = None
    if entry_time and exit_time:
        hold_minutes = max(0.0, (exit_time - entry_time).total_seconds() / 60.0)
    exit_comment = (trade.get("exit_comment") or "").lower()
    enriched.update(
        {
            "profit_aed": pnl,
            "month": str(trade.get("entry_date", ""))[:7] or "unknown",
            "estimated_cost_R": to_float(order.get("estimated_cost_R"), None),
            "stop_distance_points": to_float(order.get("stop_distance_points"), None),
            "spread_at_order_points": to_float(order.get("spread_at_order_points"), None),
            "hold_minutes": hold_minutes,
            "exit_type": "tp" if "tp" in exit_comment else "sl" if "sl" in exit_comment else "other",
        }
    )
    enriched["cost_bucket"] = bucket_cost(enriched["estimated_cost_R"])
    enriched["stop_bucket"] = bucket_stop(enriched["stop_distance_points"])
    enriched["hold_bucket"] = bucket_hold(hold_minutes)
    return enriched


def parse_mt5_time(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def to_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def bucket_cost(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value <= 0.05:
        return "cost_R_<=0.05"
    if value <= 0.10:
        return "cost_R_0.05_0.10"
    if value <= 0.15:
        return "cost_R_0.10_0.15"
    return "cost_R_>0.15"


def bucket_stop(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value < 500:
        return "stop_<500pt"
    if value < 800:
        return "stop_500_800pt"
    if value < 1200:
        return "stop_800_1200pt"
    return "stop_>=1200pt"


def bucket_hold(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value <= 15:
        return "hold_<=15m"
    if value <= 60:
        return "hold_15_60m"
    if value <= 180:
        return "hold_1_3h"
    return "hold_>3h"


def aggregate(trades: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(trades)
    wins = [trade for trade in trades if float(trade["profit_aed"]) > 0]
    losses = [trade for trade in trades if float(trade["profit_aed"]) < 0]
    gross_profit = sum(float(trade["profit_aed"]) for trade in wins)
    gross_loss = -sum(float(trade["profit_aed"]) for trade in losses)
    pnl = gross_profit - gross_loss
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    return {
        "trades": count,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round((len(wins) / count) * 100, 2) if count else 0.0,
        "pnl_aed": round(pnl, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else None,
        "avg_pnl_aed": round(pnl / count, 2) if count else 0.0,
        "avg_win_aed": round(avg_win, 2),
        "avg_loss_aed": round(avg_loss, 2),
        "win_loss_ratio": round(avg_win / avg_loss, 2) if avg_loss else None,
    }


def break_even_win_rate(trades: list[dict[str, Any]]) -> float:
    agg = aggregate(trades)
    avg_win = agg["avg_win_aed"]
    avg_loss = agg["avg_loss_aed"]
    if avg_win <= 0 or avg_loss <= 0:
        return 0.0
    return round((avg_loss / (avg_win + avg_loss)) * 100, 2)


def grouped(trades: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        buckets[str(trade.get(key, "unknown"))].append(trade)
    return {name: aggregate(items) for name, items in sorted(buckets.items())}


def robustness(trades: list[dict[str, Any]]) -> dict[str, Any]:
    pnl = sum(float(trade["profit_aed"]) for trade in trades)
    winners = sorted((float(trade["profit_aed"]) for trade in trades if float(trade["profit_aed"]) > 0), reverse=True)
    top1 = sum(winners[:1])
    top3 = sum(winners[:3])
    top5 = sum(winners[:5])
    return {
        "pnl_aed": round(pnl, 2),
        "top1_removed_pnl_aed": round(pnl - top1, 2),
        "top3_removed_pnl_aed": round(pnl - top3, 2),
        "top5_removed_pnl_aed": round(pnl - top5, 2),
        "top3_winner_sum_aed": round(top3, 2),
        "top3_share_of_net_pct": round((top3 / pnl) * 100, 2) if pnl > 0 else None,
        "max_drawdown_aed": round(max_drawdown(trades), 2),
        "max_losing_streak": max_losing_streak(trades),
    }


def max_drawdown(trades: list[dict[str, Any]]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for trade in sorted(trades, key=lambda row: row.get("entry_time", "")):
        equity += float(trade["profit_aed"])
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
    return abs(max_dd)


def max_losing_streak(trades: list[dict[str, Any]]) -> int:
    current = 0
    worst = 0
    for trade in sorted(trades, key=lambda row: row.get("entry_time", "")):
        if float(trade["profit_aed"]) < 0:
            current += 1
            worst = max(worst, current)
        else:
            current = 0
    return worst


def worst_days(trades: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        by_day[str(trade.get("date", trade.get("entry_date", "unknown")))].append(trade)
    ranked = sorted(((day, aggregate(items)) for day, items in by_day.items()), key=lambda item: item[1]["pnl_aed"])
    return [{"date": day, **stats} for day, stats in ranked[:limit]]


def best_days(trades: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        by_day[str(trade.get("date", trade.get("entry_date", "unknown")))].append(trade)
    ranked = sorted(((day, aggregate(items)) for day, items in by_day.items()), key=lambda item: item[1]["pnl_aed"], reverse=True)
    return [{"date": day, **stats} for day, stats in ranked[:limit]]


def summarize_orders(rows: list[dict[str, str]]) -> dict[str, Any]:
    actions = Counter(row.get("action", "") for row in rows)
    guards = Counter(row.get("guard_reason", "") for row in rows if row.get("action") == "GUARD_BLOCK")
    order_ok = [row for row in rows if row.get("action") == "ORDER_SEND_OK"]
    cost_values = [to_float(row.get("estimated_cost_R"), None) for row in order_ok]
    stop_values = [to_float(row.get("stop_distance_points"), None) for row in order_ok]
    return {
        "rows": len(rows),
        "actions": dict(actions.most_common()),
        "top_guard_reasons": dict(guards.most_common(10)),
        "order_send_cost_r_median": round(median([v for v in cost_values if v is not None]), 4),
        "order_send_cost_r_p95": round(percentile([v for v in cost_values if v is not None], 95), 4),
        "order_send_stop_points_median": round(median([v for v in stop_values if v is not None]), 2),
    }


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round((pct / 100.0) * (len(ordered) - 1))))
    return ordered[idx]


def derive_findings(variants: dict[str, Any]) -> list[str]:
    current = variants["current_24h_h1_smart"]
    cost010 = variants["current_24h_h1_cost010"]
    evening = variants["server_16_19_h1_smart"]
    repair = variants.get("repair_24h_h1_faststop_min800")
    profit_repair = variants.get("repair_24h_h1_faststop_min800_lock100_050")
    findings = [
        "The base entry is weak: the current H1-guarded 24h variant has only "
        f"{current['overall']['win_rate_pct']}% WR and PF {current['overall']['profit_factor']}.",
        "The current variant is not robust: after removing the top 3 winners it becomes "
        f"{current['robustness']['top3_removed_pnl_aed']} AED.",
        "Cost discipline helps but does not solve the entry: cost_R<=0.10 improves net to "
        f"{cost010['overall']['pnl_aed']} AED, but top-3 removed is still "
        f"{cost010['robustness']['top3_removed_pnl_aed']} AED.",
        "The cleanest clue is the server 16->19 slice, but it has only "
        f"{evening['overall']['trades']} trades, so it is a forward-test hypothesis, not proof.",
    ]
    if repair:
        findings.append(
            "The fast-stopout repair improves the headline book to "
            f"{repair['overall']['pnl_aed']} AED, PF {repair['overall']['profit_factor']}, "
            f"and {repair['overall']['win_rate_pct']}% WR, but it remains outlier-sensitive with top-3 removed at "
            f"{repair['robustness']['top3_removed_pnl_aed']} AED."
        )
    if profit_repair:
        findings.append(
            "The fast-stopout plus profit-protection repair is the first 920101 breakout-retest tester slice to clear "
            f"the >50% win-rate demand: {profit_repair['overall']['trades']} trades, "
            f"{profit_repair['overall']['win_rate_pct']}% WR, {profit_repair['overall']['pnl_aed']} AED, "
            f"PF {profit_repair['overall']['profit_factor']}. It is still diagnostic-only because top-3 removed is only "
            f"{profit_repair['robustness']['top3_removed_pnl_aed']} AED and it has not passed fresh forward confirmation."
        )
    return findings


def render_markdown(payload: dict[str, Any]) -> str:
    variants = payload["variants"]
    lines = [
        "# XAU 920101 Breakout-Retest Failure Forensic",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        f"Source: `{payload['source_json']}`",
        f"Period: `{payload['period']}`",
        "",
        "## Boundary",
        "",
        "- Offline analysis only.",
        "- Reads the already-generated MT5 Strategy Tester trade/order CSVs.",
        "- No MT5 chart, preset, order, position, or runtime setting was changed.",
        "- This is a failure diagnosis, not an optimizer run.",
        "",
        "## Executive Diagnosis",
        "",
    ]
    for finding in payload["findings"]:
        lines.append(f"- {finding}")
    lines.extend(
        [
            "",
            "Plain English: breakout-retest has not improved because the problem is not just one bad setting. "
            "The entry is too low-quality across most of the day. H1 trend, cost caps, and session gates reduce damage, "
            "but they do not lift the full book into a stable high-win-rate edge.",
            "",
            "## Variant Anatomy",
            "",
            "| Variant | Trades | WR | BE WR | Net AED | PF | Avg Win | Avg Loss | Max DD AED | Losing Streak | Top 3 Removed | Verdict |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for name in payload["display_variants"]:
        data = variants[name]
        verdict = variant_verdict(name, data)
        overall = data["overall"]
        robust = data["robustness"]
        lines.append(
            f"| `{name}` | {overall['trades']} | {overall['win_rate_pct']}% | {data['break_even_win_rate_pct']}% | "
            f"{overall['pnl_aed']} | {overall['profit_factor']} | {overall['avg_win_aed']} | {overall['avg_loss_aed']} | "
            f"{robust['max_drawdown_aed']} | {robust['max_losing_streak']} | {robust['top3_removed_pnl_aed']} | {verdict} |"
        )
    lines.extend(["", "## Where The Current 24h H1 Variant Fails", ""])
    current = variants["current_24h_h1_smart"]
    append_group_table(lines, "By Direction", current["direction"])
    append_group_table(lines, "By Session", current["session"])
    append_group_table(lines, "By Cost Bucket", current["cost_bucket"])
    append_group_table(lines, "By Stop Distance", current["stop_bucket"])
    append_group_table(lines, "By Holding Time", current["hold_bucket"])
    append_group_table(lines, "By Exit Type", current["exit_type"])
    lines.extend(["", "## Current Variant Worst Days", ""])
    append_day_table(lines, current["worst_days"])
    lines.extend(["", "## Best Clue: Server 16->19 Slice", ""])
    evening = variants["server_16_19_h1_smart"]
    append_group_table(lines, "Server 16->19 By Direction", evening["direction"])
    append_group_table(lines, "Server 16->19 By Cost Bucket", evening["cost_bucket"])
    profit_repair = variants.get("repair_24h_h1_faststop_min800_lock100_050")
    if profit_repair:
        lines.extend(
            [
                "",
                "## Best Repair Candidate: Fast-Stopout + Profit Protection",
                "",
                "This is the first repaired `920101` breakout-retest slice that clears the diagnostic win-rate target. "
                "It is not promoted automatically; it needs a frozen forward test before touching demo runtime.",
                "",
            ]
        )
        append_group_table(lines, "Best Repair By Direction", profit_repair["direction"])
        append_group_table(lines, "Best Repair By Session", profit_repair["session"])
        actions = profit_repair.get("management_activity", {}).get("actions", {})
        lines.extend(
            [
                "### Profit-Protection Management",
                "",
                f"- Management CSV: `{profit_repair.get('management_csv', '')}`",
                f"- Management actions: `{json.dumps(actions, sort_keys=True)}`",
                "",
            ]
        )
    lines.extend(
        [
            "",
            "## Order Flow Read",
            "",
            "| Variant | Order Rows | ORDER_SEND_OK | GUARD_BLOCK | Median Cost R | P95 Cost R | Median Stop Points | Top Guard Reasons |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for name in payload["display_variants"]:
        activity = variants[name]["order_activity"]
        actions = activity["actions"]
        guards = ", ".join(f"{key}: {value}" for key, value in list(activity["top_guard_reasons"].items())[:3])
        lines.append(
            f"| `{name}` | {activity['rows']} | {actions.get('ORDER_SEND_OK', 0)} | {actions.get('GUARD_BLOCK', 0)} | "
            f"{activity['order_send_cost_r_median']} | {activity['order_send_cost_r_p95']} | "
            f"{activity['order_send_stop_points_median']} | {guards} |"
        )
    lines.extend(
        [
            "",
            "## Why It Has Not Improved",
            "",
            "1. The win rate sits around 35-39% for the main usable books. With the observed avg-win/avg-loss profile, "
            "that leaves the strategy near breakeven before stress and negative after top-winner removal.",
            "2. The H1 smart filter reduces trade count, but it does not lift the win rate enough. "
            "It selects slightly better trades, not a clean edge.",
            "3. Cost filtering removes the worst tight-stop/high-cost trades, but the remaining book is still "
            "dependent on a few winners.",
            "4. The old 12->15 lane is not supported by the Q2 MT5 tester. The better clue is 16->19, but the sample "
            "is too small to declare solved.",
            "5. D1 confirmation and stricter broad trend filters are too blunt. They remove trades but do not fix the "
            "entry-quality problem.",
            "",
            "## Actionable Repair Path",
            "",
            "Do not keep trying random breakout-retest parameter tweaks. The next work should be controlled and small:",
            "",
            "- Keep breakout-retest classified as an experiment, not the main profit engine.",
            "- Do not promote all-day 24h breakout-retest unless fresh broker evidence beats PF 1.25, positive top-2 removed, "
            "and drawdown stays controlled.",
            "- Build a shadow scoreboard for fixed slices only: current 24h H1, 16->19 H1, 16->19 H1 cost<=0.15, "
            "16->19 H1 cost<=0.10.",
            "- For a real repair, test a new entry-quality layer, not just a new session: continuation impulse quality, "
            "late-entry/exhaustion avoidance, and profit-protection exits.",
            "- Compare every repair against the new momentum lane. If momentum continues to outperform, breakout-retest "
            "should be demoted or paused rather than endlessly rescued.",
            "",
            "## Practical Decision",
            "",
            (
                "`breakout_retest` now has one actionable diagnostic repair: fast-stopout filtering plus a "
                "profit-protection stop move. This is a tester candidate, not a runtime promotion. Freeze the exact "
                "variant and confirm it forward before replacing any live/demo 920101 settings."
                if profit_repair
                else "`breakout_retest` is not fixed. The Q2 evidence says it is a weak, outlier-sensitive edge with one promising "
                "session pocket. The current best move is to let the new momentum lane forward-test while breakout-retest "
                "gets only shadow diagnostics and narrowly scoped repair tests."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def append_group_table(lines: list[str], title: str, groups: dict[str, dict[str, Any]]) -> None:
    lines.extend(
        [
            f"### {title}",
            "",
            "| Group | Trades | WR | Net AED | PF | Avg Win | Avg Loss |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, stats in groups.items():
        lines.append(
            f"| `{name}` | {stats['trades']} | {stats['win_rate_pct']}% | {stats['pnl_aed']} | "
            f"{stats['profit_factor']} | {stats['avg_win_aed']} | {stats['avg_loss_aed']} |"
        )
    lines.append("")


def append_day_table(lines: list[str], days: list[dict[str, Any]]) -> None:
    lines.extend(
        [
            "| Date | Trades | WR | Net AED | PF |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in days:
        lines.append(f"| `{row['date']}` | {row['trades']} | {row['win_rate_pct']}% | {row['pnl_aed']} | {row['profit_factor']} |")


def variant_verdict(name: str, data: dict[str, Any]) -> str:
    overall = data["overall"]
    robust = data["robustness"]
    if overall["pnl_aed"] <= 0:
        return "fail"
    if robust["top3_removed_pnl_aed"] <= 0:
        return "outlier-sensitive"
    if overall["trades"] < 40:
        return "promising but too few trades"
    if (overall["profit_factor"] or 0) < 1.25:
        return "not enough PF"
    return "diagnostic candidate"


if __name__ == "__main__":
    main()
