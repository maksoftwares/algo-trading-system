from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"

DEFAULT_REPORTS = [
    REPORTS_DIR
    / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_DIRECTIONAL_MASK_FOUR_YEAR_2022_07_2026_06.json",
    REPORTS_DIR
    / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_ALT_FOUR_YEAR_2022_07_2026_06.json",
]


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")


def read_trades(path: Path, variant: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                profit = float(row.get("profit_aed", "0") or 0)
            except ValueError:
                profit = 0.0
            entry_time = parse_dt(row["entry_time"])
            exit_time = parse_dt(row["exit_time"]) if row.get("exit_time") else entry_time
            rows.append(
                {
                    "variant": variant,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "entry_date": row.get("entry_date") or entry_time.date().isoformat(),
                    "entry_hour": int(row.get("entry_hour") or entry_time.hour),
                    "entry_session": row.get("entry_session") or row.get("session") or "",
                    "direction": row.get("direction", ""),
                    "profit": profit,
                    "entry_price": row.get("entry_price", ""),
                    "exit_price": row.get("exit_price", ""),
                    "exit_comment": row.get("exit_comment", ""),
                }
            )
    return rows


def load_variant_trades(report_paths: list[Path]) -> dict[str, list[dict[str, Any]]]:
    variants: dict[str, list[dict[str, Any]]] = {}
    for report_path in report_paths:
        if not report_path.exists():
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for variant in report.get("variants", []):
            name = str(variant.get("name", ""))
            trade_csv = variant.get("trade_csv")
            if not name or not trade_csv:
                continue
            path = Path(trade_csv)
            if path.exists() and name not in variants:
                variants[name] = read_trades(path, name)
    return variants


def max_drawdown(profits: list[float], starting_balance: float = 1000.0) -> float:
    equity = starting_balance
    peak = starting_balance
    max_dd = 0.0
    for profit in profits:
        equity += profit
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return round(max_dd, 2)


def summarize(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(trades, key=lambda row: (row["exit_time"], row["entry_time"], row["variant"]))
    profits = [float(row["profit"]) for row in ordered]
    wins = sum(1 for value in profits if value > 0)
    losses = sum(1 for value in profits if value < 0)
    gross_profit = sum(value for value in profits if value > 0)
    gross_loss = -sum(value for value in profits if value < 0)
    by_day: dict[str, list[float]] = defaultdict(list)
    by_month: dict[str, list[float]] = defaultdict(list)
    by_variant: dict[str, list[float]] = defaultdict(list)
    for row in ordered:
        by_day[row["entry_date"]].append(float(row["profit"]))
        by_month[row["entry_date"][:7]].append(float(row["profit"]))
        by_variant[row["variant"]].append(float(row["profit"]))
    active_days = len(by_day)
    multi_trade_days = sum(1 for values in by_day.values() if len(values) >= 2)
    monthly = {month: round(sum(values), 2) for month, values in by_month.items()}
    daily = {day: round(sum(values), 2) for day, values in by_day.items()}
    top_sorted = sorted(profits, reverse=True)
    return {
        "name": name,
        "trades": len(ordered),
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(100.0 * wins / len(ordered), 2) if ordered else 0.0,
        "net_usd": round(sum(profits), 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else None,
        "active_days": active_days,
        "trades_per_active_day": round(len(ordered) / active_days, 2) if active_days else 0.0,
        "multi_trade_days": multi_trade_days,
        "multi_trade_day_pct": round(100.0 * multi_trade_days / active_days, 2) if active_days else 0.0,
        "positive_days": sum(1 for value in daily.values() if value > 0),
        "negative_days": sum(1 for value in daily.values() if value < 0),
        "positive_months": sum(1 for value in monthly.values() if value > 0),
        "negative_months": sum(1 for value in monthly.values() if value < 0),
        "worst_day_usd": round(min(daily.values()), 2) if daily else 0.0,
        "best_day_usd": round(max(daily.values()), 2) if daily else 0.0,
        "worst_month_usd": round(min(monthly.values()), 2) if monthly else 0.0,
        "best_month_usd": round(max(monthly.values()), 2) if monthly else 0.0,
        "top10_removed_usd": round(sum(profits) - sum(top_sorted[:10]), 2),
        "top25_removed_usd": round(sum(profits) - sum(top_sorted[:25]), 2),
        "max_closed_drawdown_usd": max_drawdown(profits),
        "variant_contributions": {
            variant: {
                "trades": len(values),
                "net_usd": round(sum(values), 2),
                "profit_factor": round(
                    sum(v for v in values if v > 0) / (-sum(v for v in values if v < 0)), 2
                )
                if any(v < 0 for v in values)
                else None,
            }
            for variant, values in sorted(by_variant.items())
        },
    }


def v13_only_on_v4_quiet_days(v4: list[dict[str, Any]], v13: list[dict[str, Any]]) -> list[dict[str, Any]]:
    v4_days = {row["entry_date"] for row in v4}
    return v4 + [row for row in v13 if row["entry_date"] not in v4_days]


def exclude_near_v4(
    v4: list[dict[str, Any]],
    companion: list[dict[str, Any]],
    minutes: int,
    same_direction_only: bool,
) -> list[dict[str, Any]]:
    v4_times = [(row["entry_time"], row["direction"]) for row in v4]
    kept = list(v4)
    max_seconds = minutes * 60
    for row in companion:
        near = False
        for base_time, base_direction in v4_times:
            if same_direction_only and row["direction"] != base_direction:
                continue
            if abs((row["entry_time"] - base_time).total_seconds()) <= max_seconds:
                near = True
                break
        if not near:
            kept.append(row)
    return kept


def build_portfolios(variants: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    v4 = variants.get("freq_h1_h4_long_rr0p7_v4_combo_rank1", [])
    v13 = variants.get("v13_ema_trend_h1h4_both_rr0p7_no_weak_short", [])
    v13_both_no_morning = variants.get("v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning", [])
    v13_short = variants.get("v13_ema_trend_h1h4_short_rr0p6_core", [])
    v13_long = variants.get("v13_ema_trend_h1h4_long_rr0p6_no_morning", [])
    portfolios = {
        "v4_only": v4,
        "v13_leading_only": v13,
        "v4_plus_v13_leading_raw": v4 + v13,
        "v4_plus_v13_leading_v13_only_on_v4_quiet_days": v13_only_on_v4_quiet_days(v4, v13),
        "v4_plus_v13_leading_exclude_30m_any_direction": exclude_near_v4(v4, v13, 30, False),
        "v4_plus_v13_leading_exclude_60m_same_direction": exclude_near_v4(v4, v13, 60, True),
        "v4_plus_v13_no_morning_raw": v4 + v13_both_no_morning,
        "v4_plus_v13_short_core_raw": v4 + v13_short,
        "v4_plus_v13_long_no_morning_raw": v4 + v13_long,
    }
    return {name: trades for name, trades in portfolios.items() if trades}


def decision_for(summary: dict[str, Any]) -> str:
    if summary["trades"] < 100:
        return "FAIL_SAMPLE"
    if summary["win_rate_pct"] < 50:
        return "FAIL_WIN_RATE"
    if summary["profit_factor"] is None or summary["profit_factor"] < 1.25:
        return "FAIL_PF"
    if summary["trades_per_active_day"] < 2:
        return "FAIL_ACTIVE_DAY_FREQUENCY"
    if summary["top25_removed_usd"] <= 0:
        return "FAIL_TOP_WINNER_ROBUSTNESS"
    if summary["negative_months"] > summary["positive_months"]:
        return "FAIL_MONTH_STABILITY"
    return "REVIEW_CANDIDATE"


def render_markdown(summaries: list[dict[str, Any]], output_json: Path) -> str:
    lines = [
        "# A1 XAU M5 Momentum Portfolio Combination Diagnostic",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline analysis of exact MT5 Strategy Tester trade CSVs only. No live/demo MT5 runtime, charts, presets, or orders were changed.",
        "",
        "## Why this exists",
        "",
        "The owner clarified that the strategy must create multiple intraday opportunities. This report checks whether V4 can be combined with V13 companion lanes to increase active-day coverage without destroying win rate, PF, or robustness.",
        "",
        "## Portfolio Results",
        "",
        "| Portfolio | Trades | WR % | Net USD | PF | Active days | T/active | Multi-trade days | +M | -M | Worst M | Top25 removed | Max DD | Decision |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in summaries:
        lines.append(
            "| {name} | {trades} | {win_rate_pct:.2f} | {net_usd:.2f} | {pf} | {active_days} | "
            "{trades_per_active_day:.2f} | {multi_trade_days} | {positive_months} | {negative_months} | "
            "{worst_month_usd:.2f} | {top25_removed_usd:.2f} | {max_closed_drawdown_usd:.2f} | `{decision}` |".format(
                name=item["name"],
                trades=item["trades"],
                win_rate_pct=item["win_rate_pct"],
                net_usd=item["net_usd"],
                pf=item["profit_factor"],
                active_days=item["active_days"],
                trades_per_active_day=item["trades_per_active_day"],
                multi_trade_days=item["multi_trade_days"],
                positive_months=item["positive_months"],
                negative_months=item["negative_months"],
                worst_month_usd=item["worst_month_usd"],
                top25_removed_usd=item["top25_removed_usd"],
                max_closed_drawdown_usd=item["max_closed_drawdown_usd"],
                decision=item["decision"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "V4 remains the cleanest single lane. Raw V4+V13 stacking gives the best activity profile and passes the broad frequency/quality screen, but it increases drawdown and month instability versus V4 alone. Quiet-day-only V13 adds coverage but contributes little net profit, so it is not enough by itself.",
            "",
            "The closest portfolio-shaped answer to the owner's frequency goal is:",
            "",
            "```text",
            "V4 primary + V13 leading companion, separate magic numbers, minimum lot, forward-tested as a portfolio experiment.",
            "```",
            "",
            "That is not a proof. It is a review candidate. It needs reviewer/owner approval and a frozen forward-test spec before any demo replacement or attachment.",
            "",
            f"Machine-readable output: `{output_json}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, summaries: list[dict[str, Any]]) -> None:
    fieldnames = [
        "name",
        "decision",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "multi_trade_days",
        "multi_trade_day_pct",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "best_month_usd",
        "top10_removed_usd",
        "top25_removed_usd",
        "max_closed_drawdown_usd",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in summaries:
            writer.writerow({field: item.get(field) for field in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="append", type=Path, default=[])
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.md",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.csv",
    )
    args = parser.parse_args()

    report_paths = args.report or DEFAULT_REPORTS
    variants = load_variant_trades(report_paths)
    portfolios = build_portfolios(variants)
    summaries = []
    for name, trades in portfolios.items():
        item = summarize(name, trades)
        item["decision"] = decision_for(item)
        summaries.append(item)
    summaries.sort(key=lambda row: (row["decision"] != "REVIEW_CANDIDATE", -row["net_usd"], -row["active_days"]))

    payload = {
        "status": "PORTFOLIO_DIAGNOSTIC_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "source_reports": [str(path) for path in report_paths],
        "summaries": summaries,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    args.output_md.write_text(render_markdown(summaries, args.output_json), encoding="utf-8")
    write_csv(args.output_csv, summaries)
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
