from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import is_four_year_report, load_variants
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"

SELECTED_MEMBERS = [
    "v6_freq_v4_rr0p7_max2",
    "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning",
    "freq_h1_h4_short_rr0p7_v1_core_1_5_15_19",
]


def summarize_subset(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize(name, trades)
    summary["avg_usd_per_trade"] = round(summary["net_usd"] / summary["trades"], 4) if summary["trades"] else 0.0
    return summary


def remove_top_winners(trades: list[dict[str, Any]], count: int) -> dict[str, Any]:
    profits = sorted((float(row["profit"]) for row in trades if float(row["profit"]) > 0), reverse=True)
    return {
        "remove_top_winners": count,
        "removed_profit": round(sum(profits[:count]), 2),
        "remaining_net_usd": round(sum(float(row["profit"]) for row in trades) - sum(profits[:count]), 2),
    }


def group_summary(trades: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        if field == "year":
            key = row["entry_date"][:4]
        elif field == "month":
            key = row["entry_date"][:7]
        elif field == "hour":
            key = f"{int(row['entry_hour']):02d}"
        else:
            key = str(row.get(field, ""))
        grouped[key].append(row)
    rows = []
    for key, values in sorted(grouped.items()):
        summary = summarize_subset(key, values)
        rows.append(
            {
                "bucket": key,
                "trades": summary["trades"],
                "win_rate_pct": summary["win_rate_pct"],
                "net_usd": summary["net_usd"],
                "profit_factor": summary["profit_factor"],
                "active_days": summary["active_days"],
                "trades_per_active_day": summary["trades_per_active_day"],
            }
        )
    return rows


def daily_extremes(trades: list[dict[str, Any]], count: int = 10) -> dict[str, Any]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in trades:
        grouped[row["entry_date"]].append(float(row["profit"]))
    days = [{"date": key, "net_usd": round(sum(values), 2), "trades": len(values)} for key, values in grouped.items()]
    return {
        "best_days": sorted(days, key=lambda row: row["net_usd"], reverse=True)[:count],
        "worst_days": sorted(days, key=lambda row: row["net_usd"])[:count],
    }


def member_contribution(trades: list[dict[str, Any]], members: list[str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        grouped[str(row.get("variant", ""))].append(row)
    rows = []
    for member in members:
        values = grouped.get(member, [])
        summary = summarize_subset(member, values)
        rows.append(
            {
                "member": member,
                "kept_trades": summary["trades"],
                "win_rate_pct": summary["win_rate_pct"],
                "net_usd": summary["net_usd"],
                "profit_factor": summary["profit_factor"],
                "active_days": summary["active_days"],
                "trades_per_active_day": summary["trades_per_active_day"],
            }
        )
    return rows


def without_member_summaries(
    raw_by_member: dict[str, list[dict[str, Any]]],
    priority: dict[str, int],
    members: list[str],
) -> list[dict[str, Any]]:
    rows = []
    for omitted in members:
        raw: list[dict[str, Any]] = []
        for member, trades in raw_by_member.items():
            if member != omitted:
                raw.extend(trades)
        deduped = dedupe_trades(raw, priority)
        summary = summarize_subset(f"without {omitted}", deduped)
        rows.append(
            {
                "omitted_member": omitted,
                "deduped_trades": summary["trades"],
                "win_rate_pct": summary["win_rate_pct"],
                "net_usd": summary["net_usd"],
                "profit_factor": summary["profit_factor"],
                "active_days": summary["active_days"],
                "trades_per_active_day": summary["trades_per_active_day"],
                "positive_months": summary["positive_months"],
                "negative_months": summary["negative_months"],
                "top25_removed_usd": summary["top25_removed_usd"],
                "max_closed_drawdown_usd": summary["max_closed_drawdown_usd"],
            }
        )
    return rows


def split_window(trades: list[dict[str, Any]], start: str, end: str) -> list[dict[str, Any]]:
    return [row for row in trades if start <= row["entry_date"] <= end]


def verdict(summary: dict[str, Any], top_removals: list[dict[str, Any]], by_year: list[dict[str, Any]]) -> str:
    if summary["win_rate_pct"] < 60:
        return "REVISE_WIN_RATE"
    if summary["profit_factor"] is None or summary["profit_factor"] < 1.25:
        return "REVISE_PF"
    if summary["trades_per_active_day"] < 3.0:
        return "REVISE_FREQUENCY"
    if any(item["remaining_net_usd"] <= 0 for item in top_removals if item["remove_top_winners"] <= 50):
        return "REVISE_TOP_WINNER_DEPENDENCE"
    if any(row["net_usd"] <= 0 for row in by_year):
        return "REVISE_YEAR_INSTABILITY"
    return "REVIEW_FOR_FORWARD_TEST"


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# A1 XAU M5 Momentum Deep Portfolio Stress Test",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV stress test only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Candidate",
        "",
        "```text",
        "\n+\n".join(payload["members"]),
        "```",
        "",
        "## Deduped Portfolio Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Deduped trades | {summary['trades']} |",
        f"| Win rate | {summary['win_rate_pct']}% |",
        f"| Net USD | {summary['net_usd']} |",
        f"| Profit factor | {summary['profit_factor']} |",
        f"| Active days | {summary['active_days']} |",
        f"| Trades / active day | {summary['trades_per_active_day']} |",
        f"| Positive / negative months | {summary['positive_months']} / {summary['negative_months']} |",
        f"| Worst month USD | {summary['worst_month_usd']} |",
        f"| Top25 removed USD | {summary['top25_removed_usd']} |",
        f"| Max closed DD USD | {summary['max_closed_drawdown_usd']} |",
        f"| Verdict | `{payload['verdict']}` |",
        "",
        "## Top-Winner Stress",
        "",
        "| Removed winners | Removed profit | Remaining net USD |",
        "|---:|---:|---:|",
    ]
    for item in payload["top_winner_stress"]:
        lines.append(
            f"| {item['remove_top_winners']} | {item['removed_profit']} | {item['remaining_net_usd']} |"
        )
    lines.extend(["", "## Member Contribution After Deduplication", "", "| Member | Trades | WR % | Net USD | PF | Active days | T/active |", "|---|---:|---:|---:|---:|---:|---:|"])
    for row in payload["member_contribution"]:
        lines.append(
            f"| `{row['member']}` | {row['kept_trades']} | {row['win_rate_pct']} | {row['net_usd']} | {row['profit_factor']} | {row['active_days']} | {row['trades_per_active_day']} |"
        )
    lines.extend(["", "## Portfolio Without Each Member", "", "| Omitted member | Trades | WR % | Net USD | PF | Active days | T/active | +M | -M | Top25 removed | DD |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for row in payload["without_member"]:
        lines.append(
            f"| `{row['omitted_member']}` | {row['deduped_trades']} | {row['win_rate_pct']} | {row['net_usd']} | {row['profit_factor']} | {row['active_days']} | {row['trades_per_active_day']} | {row['positive_months']} | {row['negative_months']} | {row['top25_removed_usd']} | {row['max_closed_drawdown_usd']} |"
        )
    for section, title in [
        ("year", "Year Split"),
        ("window", "Two-Year Window Split"),
        ("direction", "Direction Split"),
        ("session", "Session Split"),
        ("hour", "Hour Split"),
    ]:
        lines.extend(["", f"## {title}", "", "| Bucket | Trades | WR % | Net USD | PF | Active days | T/active |", "|---|---:|---:|---:|---:|---:|---:|"])
        for row in payload[f"by_{section}"]:
            lines.append(
                f"| `{row['bucket']}` | {row['trades']} | {row['win_rate_pct']} | {row['net_usd']} | {row['profit_factor']} | {row['active_days']} | {row['trades_per_active_day']} |"
            )
    lines.extend(["", "## Daily Extremes", "", "### Best Days", "", "| Date | Net USD | Trades |", "|---|---:|---:|"])
    for row in payload["daily_extremes"]["best_days"]:
        lines.append(f"| {row['date']} | {row['net_usd']} | {row['trades']} |")
    lines.extend(["", "### Worst Days", "", "| Date | Net USD | Trades |", "|---|---:|---:|"])
    for row in payload["daily_extremes"]["worst_days"]:
        lines.append(f"| {row['date']} | {row['net_usd']} | {row['trades']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This report is still diagnostic. It checks whether the portfolio deserves independent review and a frozen minimum-lot forward test. It does not approve runtime attachment by itself.",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="append", type=Path, default=[])
    parser.add_argument("--output-json", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_2026_07_02.json")
    parser.add_argument("--output-md", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_2026_07_02.md")
    parser.add_argument("--output-member-csv", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_STRESS_MEMBERS_2026_07_02.csv")
    parser.add_argument("--member", action="append", default=[])
    args = parser.parse_args()

    selected_members = args.member or SELECTED_MEMBERS
    reports = args.report or sorted(path for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*.json") if is_four_year_report(path))
    variants = load_variants(reports)
    missing = [name for name in selected_members if name not in variants]
    if missing:
        raise SystemExit(f"Missing selected variants: {', '.join(missing)}")
    raw_by_member = {name: variants[name]["trades"] for name in selected_members}
    priority = {name: index for index, name in enumerate(selected_members)}
    raw_trades = [row for name in selected_members for row in raw_by_member[name]]
    deduped = dedupe_trades(raw_trades, priority)
    summary = summarize_subset("deep_portfolio_selected", deduped)
    top_stress = [remove_top_winners(deduped, count) for count in [1, 3, 5, 10, 25, 50, 100]]
    by_year = group_summary(deduped, "year")
    payload = {
        "status": "DEEP_PORTFOLIO_STRESS_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "members": selected_members,
        "summary": summary,
        "top_winner_stress": top_stress,
        "member_contribution": member_contribution(deduped, selected_members),
        "without_member": without_member_summaries(raw_by_member, priority, selected_members),
        "by_year": by_year,
        "by_window": [
            {"bucket": "2022-07_to_2024-06", **summarize_subset("2022-07_to_2024-06", split_window(deduped, "2022-07-01", "2024-06-30"))},
            {"bucket": "2024-07_to_2026-06", **summarize_subset("2024-07_to_2026-06", split_window(deduped, "2024-07-01", "2026-06-30"))},
        ],
        "by_direction": group_summary(deduped, "direction"),
        "by_session": group_summary(deduped, "entry_session"),
        "by_hour": group_summary(deduped, "hour"),
        "daily_extremes": daily_extremes(deduped),
        "verdict": verdict(summary, top_stress, by_year),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    write_csv(args.output_member_csv, payload["member_contribution"])
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
