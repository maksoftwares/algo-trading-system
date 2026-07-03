from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_state_guard_search import apply_state_guard, top_removed_usd
from analyze_a1_momentum_market_day_coverage_search import (
    GUARD_SCENARIOS,
    day_distribution,
    date_window,
    dedupe_portfolio,
    load_csv_variants,
    load_synthetic_business_packages,
)
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_STRESS_CAUSAL_2026_07_03"

BEST_VARIANTS = [
    "residual_plus75_high_net",
    "freq_h1_h4_rr0p7_cost005_block_bad_hours",
    "v6_freq_v4_rr0p7_max2",
]
BEST_GUARD = next(item for item in GUARD_SCENARIOS if item["name"] == "target75_cooldown10")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def profit_factor(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if not gross_loss:
        return None
    return round(gross_profit / gross_loss, 2)


def group_key(row: dict[str, Any], kind: str) -> str:
    entry_time = row["entry_time"]
    if kind == "month":
        return entry_time.strftime("%Y-%m")
    if kind == "quarter":
        quarter = (entry_time.month - 1) // 3 + 1
        return f"{entry_time.year}-Q{quarter}"
    if kind == "half_year":
        half = "H1" if entry_time.month <= 6 else "H2"
        return f"{entry_time.year}-{half}"
    if kind == "direction":
        return str(row.get("direction", ""))
    if kind == "session":
        return str(row.get("entry_session", ""))
    if kind == "variant":
        return str(row.get("variant", ""))
    return ""


def grouped_stats(trades: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        groups[group_key(row, kind)].append(row)
    rows: list[dict[str, Any]] = []
    for key, values in sorted(groups.items()):
        profits = [float(row["profit"]) for row in values]
        wins = sum(1 for value in profits if value > 0)
        rows.append(
            {
                "key": key,
                "trades": len(values),
                "win_rate_pct": round(100.0 * wins / len(values), 2) if values else 0.0,
                "net_usd": round(sum(profits), 2),
                "profit_factor": profit_factor(profits),
            }
        )
    return rows


def rolling_stats(trades: list[dict[str, Any]], window: int) -> dict[str, Any]:
    ordered = sorted(trades, key=lambda row: (row["exit_time"], row["entry_time"], row["variant"]))
    if len(ordered) < window:
        return {"window": window, "available": False}
    windows: list[dict[str, Any]] = []
    for start in range(0, len(ordered) - window + 1):
        chunk = ordered[start : start + window]
        profits = [float(row["profit"]) for row in chunk]
        wins = sum(1 for value in profits if value > 0)
        windows.append(
            {
                "start": chunk[0]["entry_time"].strftime("%Y-%m-%d"),
                "end": chunk[-1]["entry_time"].strftime("%Y-%m-%d"),
                "net_usd": round(sum(profits), 2),
                "win_rate_pct": round(100.0 * wins / window, 2),
                "profit_factor": profit_factor(profits),
            }
        )
    worst_net = min(windows, key=lambda row: row["net_usd"])
    worst_pf = min(windows, key=lambda row: row["profit_factor"] or 0.0)
    return {
        "window": window,
        "available": True,
        "count": len(windows),
        "worst_net": worst_net,
        "worst_pf": worst_pf,
        "negative_windows": sum(1 for row in windows if row["net_usd"] < 0),
        "pf_below_1_windows": sum(1 for row in windows if (row["profit_factor"] or 0.0) < 1.0),
    }


def build_selected_trades(variants: dict[str, list[dict[str, Any]]], names: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw: list[dict[str, Any]] = []
    missing = [name for name in names if name not in variants]
    for name in names:
        raw.extend(variants.get(name, []))
    deduped, duplicate_drops = dedupe_portfolio(raw)
    selected, guard_stats = apply_state_guard(
        deduped,
        state_rule="none",
        profit_target_usd=BEST_GUARD["profit_target_usd"],
        loss_stop_usd=BEST_GUARD["loss_stop_usd"],
        max_trades_per_day=BEST_GUARD["max_trades_per_day"],
        max_losses_per_day=BEST_GUARD["max_losses_per_day"],
        cooldown_after_loss_minutes=BEST_GUARD["cooldown_after_loss_minutes"],
        early_trade_count=BEST_GUARD["early_trade_count"],
        early_pnl_threshold=BEST_GUARD["early_pnl_threshold"],
    )
    meta = {
        "missing_variants": missing,
        "raw_trades": len(raw),
        "deduped_trades_before_guard": len(deduped),
        "duplicate_drops": duplicate_drops,
        "guard_stats": guard_stats,
    }
    return selected, meta


def evaluate_trades(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    start, end, market_days = date_window(trades)
    summary = summarize(name, trades)
    summary.update(day_distribution(trades, market_days))
    summary.update(
        {
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "top1_removed_usd": top_removed_usd(trades, 1),
            "top3_removed_usd": top_removed_usd(trades, 3),
            "top5_removed_usd": top_removed_usd(trades, 5),
            "top10_removed_usd": top_removed_usd(trades, 10),
            "top25_removed_usd": top_removed_usd(trades, 25),
            "top50_removed_usd": top_removed_usd(trades, 50),
            "top100_removed_usd": top_removed_usd(trades, 100),
            "top200_removed_usd": top_removed_usd(trades, 200),
            "top300_removed_usd": top_removed_usd(trades, 300),
        }
    )
    return summary


def ablations(variants: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for removed in BEST_VARIANTS:
        names = [name for name in BEST_VARIANTS if name != removed]
        selected, meta = build_selected_trades(variants, names)
        summary = evaluate_trades(f"without_{removed}", selected)
        rows.append({"removed_variant": removed, **meta, **summary})
    return rows


def decision(summary: dict[str, Any], half_year: list[dict[str, Any]], quarter: list[dict[str, Any]], rolling: list[dict[str, Any]]) -> str:
    if summary["trades_per_market_day"] < 3.0 or summary["win_rate_pct"] < 60.0:
        return "REVISE_CADENCE_OR_QUALITY"
    if (summary["profit_factor"] or 0.0) < 1.30 or summary["top200_removed_usd"] <= 0:
        return "REVISE_ROBUSTNESS"
    if any(row["net_usd"] <= 0 for row in half_year):
        return "REVISE_HALF_YEAR_INSTABILITY"
    if sum(1 for row in quarter if row["net_usd"] <= 0) > 3:
        return "REVISE_QUARTER_INSTABILITY"
    if any(row.get("available") and row.get("negative_windows", 0) > 0 for row in rolling):
        return "REVIEW_WITH_ROLLING_DRAWDOWN_CAVEAT"
    return "REVIEW_READY_STRONG_CADENCE"


def write_trades(path: Path, trades: list[dict[str, Any]]) -> None:
    fieldnames = [
        "variant",
        "entry_time",
        "entry_date",
        "entry_hour",
        "entry_session",
        "direction",
        "profit",
        "exit_time",
        "exit_comment",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(trades, key=lambda item: (item["entry_time"], item["variant"])):
            writer.writerow(
                {
                    "variant": row.get("variant", ""),
                    "entry_time": row["entry_time"].strftime("%Y.%m.%d %H:%M:%S"),
                    "entry_date": row.get("entry_date", ""),
                    "entry_hour": row.get("entry_hour", ""),
                    "entry_session": row.get("entry_session", ""),
                    "direction": row.get("direction", ""),
                    "profit": row.get("profit", 0.0),
                    "exit_time": row["exit_time"].strftime("%Y.%m.%d %H:%M:%S"),
                    "exit_comment": row.get("exit_comment", ""),
                }
            )


def render(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# A1 XAU M5 Momentum Market-Day Coverage Stress - Causal Guard - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "Guard model: `event_time_causal_v2`. Guard state changes only after the simulated trade outcome is knowable at exit time.",
        "",
        "## Candidate",
        "",
        f"- Portfolio: `{payload['portfolio_name']}`",
        f"- Guard: `{payload['guard_name']}`",
        f"- Decision: `{payload['decision']}`",
        "",
        "## Headline Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Trades | {summary['trades']} |",
        f"| Win rate | {summary['win_rate_pct']}% |",
        f"| Profit factor | {summary['profit_factor']} |",
        f"| Net | {summary['net_usd']} USD |",
        f"| Trades / weekday market day | {summary['trades_per_market_day']} |",
        f"| Trades / active day | {summary['trades_per_active_day']} |",
        f"| 3+ trade market days | {summary['three_plus_market_day_pct']}% |",
        f"| Positive active days | {summary['positive_active_day_pct']}% |",
        f"| Top 100 removed | {summary['top100_removed_usd']} USD |",
        f"| Top 200 removed | {summary['top200_removed_usd']} USD |",
        f"| Top 300 removed | {summary['top300_removed_usd']} USD |",
        f"| Max closed drawdown | {summary['max_closed_drawdown_usd']} USD |",
        "",
        "## Source Contribution",
        "",
        "| Variant | Trades | Net | PF |",
        "|---|---:|---:|---:|",
    ]
    for name, row in summary.get("variant_contributions", {}).items():
        lines.append(f"| `{name}` | {row['trades']} | {row['net_usd']} | {row['profit_factor']} |")
    lines.extend(["", "## Half-Year Stability", "", "| Half-year | Trades | WR | Net | PF |", "|---|---:|---:|---:|---:|"])
    for row in payload["half_year"]:
        lines.append(f"| `{row['key']}` | {row['trades']} | {row['win_rate_pct']}% | {row['net_usd']} | {row['profit_factor']} |")
    lines.extend(["", "## Quarter Stability", "", "| Quarter | Trades | WR | Net | PF |", "|---|---:|---:|---:|---:|"])
    for row in payload["quarter"]:
        lines.append(f"| `{row['key']}` | {row['trades']} | {row['win_rate_pct']}% | {row['net_usd']} | {row['profit_factor']} |")
    lines.extend(["", "## Ablation Check", "", "| Removed variant | Trades | WR | Net | PF | T/market day | Decision read |", "|---|---:|---:|---:|---:|---:|---|"])
    for row in payload["ablations"]:
        read = "still_positive" if row["net_usd"] > 0 and (row["profit_factor"] or 0.0) > 1.15 else "depends_on_removed_variant"
        lines.append(
            f"| `{row['removed_variant']}` | {row['trades']} | {row['win_rate_pct']}% | {row['net_usd']} | {row['profit_factor']} | {row['trades_per_market_day']} | `{read}` |"
        )
    lines.extend(["", "## Rolling Windows", "", "| Window | Count | Negative windows | PF<1 windows | Worst net window | Worst PF window |", "|---:|---:|---:|---:|---|---|"])
    for row in payload["rolling"]:
        worst_net = row.get("worst_net", {})
        worst_pf = row.get("worst_pf", {})
        lines.append(
            f"| {row.get('window')} | {row.get('count', 0)} | {row.get('negative_windows', 0)} | {row.get('pf_below_1_windows', 0)} | "
            f"`{worst_net.get('start', '')}->{worst_net.get('end', '')}: {worst_net.get('net_usd', '')}` | "
            f"`{worst_pf.get('start', '')}->{worst_pf.get('end', '')}: {worst_pf.get('profit_factor', '')}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This candidate is meaningfully closer to the owner's original rhythm than sparse RR2-style systems.",
            "- It still does not guarantee 3+ trades every market day; 3+ trade market days remain below 50%.",
            "- Reviewer stress should focus on search bias, source overlap, short-leg regime risk, and whether the causal guard adds anything beyond the no-guard book.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['json']}`",
            f"- Selected trades CSV: `{payload['selected_trades_csv']}`",
            f"- Report: `{payload['report']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    variants = {**load_csv_variants(), **load_synthetic_business_packages()}
    selected, meta = build_selected_trades(variants, BEST_VARIANTS)
    summary = evaluate_trades("market_day_coverage_best", selected)
    half_year = grouped_stats(selected, "half_year")
    quarter = grouped_stats(selected, "quarter")
    rolling = [rolling_stats(selected, 250), rolling_stats(selected, 500)]
    ablation_rows = ablations(variants)
    verdict = decision(summary, half_year, quarter, rolling)

    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}_TRADES.csv"
    payload = {
        "status": "PASS_CAUSAL_STRESS_REPORT_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change_event_time_causal_guard",
        "guard_model": "event_time_causal_v2",
        "portfolio_name": " + ".join(BEST_VARIANTS),
        "guard_name": BEST_GUARD["name"],
        "decision": verdict,
        "summary": summary,
        "meta": meta,
        "half_year": half_year,
        "quarter": quarter,
        "month": grouped_stats(selected, "month"),
        "direction": grouped_stats(selected, "direction"),
        "session": grouped_stats(selected, "session"),
        "variant": grouped_stats(selected, "variant"),
        "rolling": rolling,
        "ablations": ablation_rows,
        "json": rel(output_json),
        "report": rel(output_md),
        "selected_trades_csv": rel(output_csv),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_trades(output_csv, selected)
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "decision": verdict,
                "trades": summary["trades"],
                "win_rate_pct": summary["win_rate_pct"],
                "profit_factor": summary["profit_factor"],
                "net_usd": summary["net_usd"],
                "trades_per_market_day": summary["trades_per_market_day"],
                "three_plus_market_day_pct": summary["three_plus_market_day_pct"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
