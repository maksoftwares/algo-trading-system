from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import (
    duplicate_like_stats,
    is_four_year_report,
    load_variants,
)
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"


def single_score(summary: dict[str, Any]) -> float:
    pf = float(summary.get("profit_factor") or 0.0)
    net = float(summary.get("net_usd") or 0.0)
    active = float(summary.get("active_days") or 0.0)
    tpa = float(summary.get("trades_per_active_day") or 0.0)
    dd = max(float(summary.get("max_closed_drawdown_usd") or 1.0), 1.0)
    neg_months = float(summary.get("negative_months") or 0.0)
    return (pf * 900.0) + (net / dd * 100.0) + active + (tpa * 80.0) - (neg_months * 18.0)


def portfolio_score(summary: dict[str, Any]) -> float:
    pf = float(summary.get("profit_factor") or 0.0)
    wr = float(summary.get("win_rate_pct") or 0.0)
    net = float(summary.get("net_usd") or 0.0)
    active = float(summary.get("active_days") or 0.0)
    tpa = float(summary.get("trades_per_active_day") or 0.0)
    dd = max(float(summary.get("max_closed_drawdown_usd") or 1.0), 1.0)
    neg_months = float(summary.get("negative_months") or 0.0)
    worst_month = min(float(summary.get("worst_month_usd") or 0.0), 0.0)
    top25 = float(summary.get("top25_removed_usd") or 0.0)
    return (
        pf * 1200.0
        + wr * 15.0
        + (net / dd * 140.0)
        + active
        + tpa * 120.0
        + min(top25, net) / 10.0
        - neg_months * 24.0
        + worst_month
    )


def dedupe_trades(trades: list[dict[str, Any]], priority: dict[str, int]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in trades:
        key = (row["entry_time"].strftime("%Y-%m-%d %H:%M"), row.get("direction", ""))
        grouped.setdefault(key, []).append(row)
    kept: list[dict[str, Any]] = []
    for rows in grouped.values():
        chosen = sorted(
            rows,
            key=lambda row: (
                priority.get(str(row.get("variant", "")), 9999),
                row["entry_time"],
                row["exit_time"],
            ),
        )[0]
        kept.append(chosen)
    return kept


def decision_for(summary: dict[str, Any], raw_duplicate_pct: float) -> str:
    if summary["trades"] < 1000:
        return "FAIL_SAMPLE"
    if summary["active_days"] < 500:
        return "FAIL_ACTIVE_DAY_COVERAGE"
    if summary["trades_per_active_day"] < 2.25:
        return "FAIL_INTRADAY_FREQUENCY"
    if summary["win_rate_pct"] < 58.0:
        return "FAIL_WIN_RATE"
    if summary["profit_factor"] is None or summary["profit_factor"] < 1.25:
        return "FAIL_PF"
    if summary["net_usd"] < 1000:
        return "FAIL_NET"
    if summary["top25_removed_usd"] <= 0:
        return "FAIL_TOP_WINNER_ROBUSTNESS"
    if summary["negative_months"] > 16:
        return "FAIL_MONTH_STABILITY"
    if summary["worst_month_usd"] < -90:
        return "FAIL_WORST_MONTH"
    if summary["max_closed_drawdown_usd"] > 180:
        return "FAIL_DRAWDOWN"
    if raw_duplicate_pct > 50.0:
        return "FAIL_STACKING_TOO_HIGH"
    return "REVIEW_CANDIDATE"


def compact(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": row["decision"],
        "score": row["score"],
        "name": row["name"],
        "members": row["members"],
        "raw_trades": row["raw_trades"],
        "deduped_trades": row["trades"],
        "win_rate_pct": row["win_rate_pct"],
        "net_usd": row["net_usd"],
        "profit_factor": row["profit_factor"],
        "active_days": row["active_days"],
        "trades_per_active_day": row["trades_per_active_day"],
        "multi_trade_days": row["multi_trade_days"],
        "positive_months": row["positive_months"],
        "negative_months": row["negative_months"],
        "worst_month_usd": row["worst_month_usd"],
        "top25_removed_usd": row["top25_removed_usd"],
        "max_closed_drawdown_usd": row["max_closed_drawdown_usd"],
        "raw_duplicate_like_trade_pct": row["raw_duplicate_like_trade_pct"],
        "dedupe_removed_trades": row["dedupe_removed_trades"],
    }


def build_pool(variants: dict[str, dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    pool: list[dict[str, Any]] = []
    for item in variants.values():
        summary = item["summary"]
        if summary["trades"] < 100:
            continue
        if summary["net_usd"] <= 0:
            continue
        if summary["profit_factor"] is None or summary["profit_factor"] < 1.08:
            continue
        if summary["win_rate_pct"] < 50:
            continue
        item = dict(item)
        item["single_score"] = single_score(summary)
        pool.append(item)
    return sorted(pool, key=lambda row: row["single_score"], reverse=True)[:limit]


def evaluate_combo(combo: tuple[dict[str, Any], ...], priority: dict[str, int]) -> dict[str, Any]:
    raw_trades: list[dict[str, Any]] = []
    for item in combo:
        raw_trades.extend(item["trades"])
    raw_dups = duplicate_like_stats(raw_trades)
    deduped = dedupe_trades(raw_trades, priority)
    name = " + ".join(str(item["name"]) for item in combo)
    summary = summarize(name, deduped)
    summary["members"] = [str(item["name"]) for item in combo]
    summary["raw_trades"] = len(raw_trades)
    summary["raw_duplicate_like_trade_pct"] = raw_dups["duplicate_like_trade_pct"]
    summary["dedupe_removed_trades"] = len(raw_trades) - len(deduped)
    summary["decision"] = decision_for(summary, raw_dups["duplicate_like_trade_pct"])
    summary["score"] = round(portfolio_score(summary), 2)
    return summary


def search(pool: list[dict[str, Any]], max_size: int) -> list[dict[str, Any]]:
    priority = {str(item["name"]): index for index, item in enumerate(pool)}
    rows: list[dict[str, Any]] = []
    for size in range(1, max_size + 1):
        for combo in itertools.combinations(pool, size):
            rows.append(evaluate_combo(combo, priority))
    rows.sort(key=lambda row: (row["decision"] != "REVIEW_CANDIDATE", -row["score"]))
    return rows


def render_markdown(rows: list[dict[str, Any]], reports: list[Path], output_json: Path) -> str:
    review = [row for row in rows if row["decision"] == "REVIEW_CANDIDATE"]
    top = review[:25] if review else rows[:25]
    lines = [
        "# A1 XAU M5 Momentum Deep Portfolio Search",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The owner rejected sparse strategies as primary lanes. This search looks for small portfolios that keep the original objective alive: frequent intraday activity, win rate above 50%, positive net, acceptable drawdown, and no fake boost from duplicate stacking.",
        "",
        "The score is computed after deterministic same-minute same-direction de-duplication. Raw duplicate-like overlap is still reported so we can see whether a portfolio is leaning on clone stacking.",
        "",
        "## Source reports",
        "",
    ]
    for report in reports:
        lines.append(f"- `{report}`")
    lines.extend(
        [
            "",
            "## Top Deduped Portfolio Candidates",
            "",
            "| Rank | Decision | Score | Members | Raw trades | Deduped trades | WR % | Net USD | PF | Active days | T/active | +M | -M | Worst M | Top25 removed | Max DD | Raw dup % | Removed |",
            "|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(top, 1):
        lines.append(
            "| {rank} | `{decision}` | {score:.2f} | {members} | {raw} | {dedup} | {wr:.2f} | {net:.2f} | {pf} | {active} | {tpa:.2f} | {pm} | {nm} | {worst:.2f} | {top25:.2f} | {dd:.2f} | {dup:.2f} | {removed} |".format(
                rank=index,
                decision=row["decision"],
                score=row["score"],
                members="<br>".join(row["members"]),
                raw=row["raw_trades"],
                dedup=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                pm=row["positive_months"],
                nm=row["negative_months"],
                worst=row["worst_month_usd"],
                top25=row["top25_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
                dup=row["raw_duplicate_like_trade_pct"],
                removed=row["dedupe_removed_trades"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a diagnostic search, not approval to attach anything. It is useful because it tests the actual desired shape after de-duplication: enough trades, enough active days, and still-good win rate/PF.",
            "",
            "Any review candidate should still be sent for independent review and then forward-tested at minimum lot with frozen inputs before runtime promotion.",
            "",
            f"Machine-readable output: `{output_json}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "decision",
        "score",
        "name",
        "members",
        "raw_trades",
        "deduped_trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "multi_trade_days",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "top25_removed_usd",
        "max_closed_drawdown_usd",
        "raw_duplicate_like_trade_pct",
        "dedupe_removed_trades",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            compacted = compact(row)
            compacted["deduped_trades"] = compacted.pop("deduped_trades")
            compacted["members"] = " + ".join(compacted["members"])
            writer.writerow(compacted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="append", type=Path, default=[])
    parser.add_argument("--pool-limit", type=int, default=28)
    parser.add_argument("--max-size", type=int, default=3)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.md",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.csv",
    )
    args = parser.parse_args()

    reports = args.report or sorted(path for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*.json") if is_four_year_report(path))
    variants = load_variants(reports)
    pool = build_pool(variants, args.pool_limit)
    rows = search(pool, args.max_size)
    payload = {
        "status": "DEEP_PORTFOLIO_SEARCH_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "pool_limit": args.pool_limit,
        "max_size": args.max_size,
        "variant_pool_count": len(pool),
        "candidate_count": len(rows),
        "source_reports": [str(path) for path in reports],
        "top_candidates": [compact(row) for row in rows[:100]],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    args.output_md.write_text(render_markdown(rows, reports, args.output_json), encoding="utf-8")
    write_csv(args.output_csv, rows)
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
