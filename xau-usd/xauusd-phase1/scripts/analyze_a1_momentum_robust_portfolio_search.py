from __future__ import annotations

import argparse
import csv
import itertools
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import (
    duplicate_like_stats,
    is_four_year_report,
    load_variants,
)
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
SPLIT_DATE = datetime(2024, 7, 1)


def window_summary(name: str, trades: list[dict[str, Any]], start: datetime | None, end: datetime | None) -> dict[str, Any]:
    selected = [
        row
        for row in trades
        if (start is None or row["entry_time"] >= start) and (end is None or row["entry_time"] < end)
    ]
    return summarize(name, selected) if selected else {
        "name": name,
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "win_rate_pct": 0.0,
        "net_usd": 0.0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "profit_factor": 0.0,
        "active_days": 0,
        "trades_per_active_day": 0.0,
        "positive_months": 0,
        "negative_months": 0,
        "worst_month_usd": 0.0,
        "top25_removed_usd": 0.0,
        "max_closed_drawdown_usd": 0.0,
    }


def min_window_pf(row: dict[str, Any]) -> float:
    values = [
        float(row.get("older_profit_factor") or 0.0),
        float(row.get("newer_profit_factor") or 0.0),
    ]
    return min(values)


def single_score(summary: dict[str, Any]) -> float:
    pf = float(summary.get("profit_factor") or 0.0)
    wr = float(summary.get("win_rate_pct") or 0.0)
    active = float(summary.get("active_days") or 0.0)
    net = float(summary.get("net_usd") or 0.0)
    dd = max(float(summary.get("max_closed_drawdown_usd") or 1.0), 1.0)
    return pf * 900.0 + wr * 10.0 + active + net / dd * 75.0


def portfolio_score(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    wr = float(row.get("win_rate_pct") or 0.0)
    net = float(row.get("net_usd") or 0.0)
    active = float(row.get("active_days") or 0.0)
    tpa = float(row.get("trades_per_active_day") or 0.0)
    dd = max(float(row.get("max_closed_drawdown_usd") or 1.0), 1.0)
    top25 = float(row.get("top25_removed_usd") or 0.0)
    worst_month = min(float(row.get("worst_month_usd") or 0.0), 0.0)
    older_pf = float(row.get("older_profit_factor") or 0.0)
    newer_pf = float(row.get("newer_profit_factor") or 0.0)
    older_net = float(row.get("older_net_usd") or 0.0)
    newer_net = float(row.get("newer_net_usd") or 0.0)
    neg_months = float(row.get("negative_months") or 0.0)
    duplicate_pct = float(row.get("raw_duplicate_like_trade_pct") or 0.0)
    balance_bonus = min(older_pf, newer_pf) * 900.0 + min(older_net, newer_net) / 2.0
    return (
        pf * 900.0
        + wr * 14.0
        + net / dd * 110.0
        + active
        + tpa * 100.0
        + top25 / 12.0
        + balance_bonus
        + worst_month
        - neg_months * 22.0
        - duplicate_pct * 18.0
    )


def decision_for(row: dict[str, Any]) -> str:
    if row["trades"] < 1500:
        return "FAIL_SAMPLE"
    if row["active_days"] < 500:
        return "FAIL_ACTIVE_DAY_COVERAGE"
    if row["trades_per_active_day"] < 2.5:
        return "FAIL_INTRADAY_FREQUENCY"
    if row["win_rate_pct"] < 58.0:
        return "FAIL_WIN_RATE"
    if row["profit_factor"] is None or row["profit_factor"] < 1.25:
        return "FAIL_PF"
    if row["net_usd"] < 1000:
        return "FAIL_NET"
    if row["top25_removed_usd"] <= 0:
        return "FAIL_TOP_WINNER_ROBUSTNESS"
    if row["negative_months"] > 16:
        return "FAIL_MONTH_STABILITY"
    if row["worst_month_usd"] < -90:
        return "FAIL_WORST_MONTH"
    if row["max_closed_drawdown_usd"] > 180:
        return "FAIL_DRAWDOWN"
    if row["raw_duplicate_like_trade_pct"] > 25.0:
        return "FAIL_STACKING_OVERLAP"
    if row["older_trades"] < 700 or row["newer_trades"] < 700:
        return "FAIL_SPLIT_SAMPLE"
    if row["older_net_usd"] <= 0 or row["newer_net_usd"] <= 0:
        return "FAIL_SPLIT_NET"
    if row["older_profit_factor"] < 1.20 or row["newer_profit_factor"] < 1.20:
        return "REVIEW_WITH_SPLIT_CAVEAT"
    return "ROBUST_REVIEW_CANDIDATE"


def build_pool(variants: dict[str, dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    pool: list[dict[str, Any]] = []
    for item in variants.values():
        summary = item["summary"]
        if summary["trades"] < 100:
            continue
        if summary["net_usd"] <= 0:
            continue
        if summary["profit_factor"] is None or summary["profit_factor"] < 1.06:
            continue
        if summary["win_rate_pct"] < 50.0:
            continue
        candidate = dict(item)
        candidate["single_score"] = single_score(summary)
        pool.append(candidate)
    return sorted(pool, key=lambda row: row["single_score"], reverse=True)[:limit]


def evaluate_combo(combo: tuple[dict[str, Any], ...], priority: dict[str, int]) -> dict[str, Any]:
    raw_trades: list[dict[str, Any]] = []
    for item in combo:
        raw_trades.extend(item["trades"])
    raw_dups = duplicate_like_stats(raw_trades)
    deduped = dedupe_trades(raw_trades, priority)
    name = " + ".join(str(item["name"]) for item in combo)
    summary = summarize(name, deduped)
    older = window_summary(name + "_older", deduped, None, SPLIT_DATE)
    newer = window_summary(name + "_newer", deduped, SPLIT_DATE, None)
    summary.update(
        {
            "members": [str(item["name"]) for item in combo],
            "raw_trades": len(raw_trades),
            "raw_duplicate_like_trade_pct": raw_dups["duplicate_like_trade_pct"],
            "dedupe_removed_trades": len(raw_trades) - len(deduped),
            "older_trades": older["trades"],
            "older_net_usd": older["net_usd"],
            "older_profit_factor": older["profit_factor"] or 0.0,
            "older_win_rate_pct": older["win_rate_pct"],
            "older_active_days": older["active_days"],
            "older_trades_per_active_day": older["trades_per_active_day"],
            "newer_trades": newer["trades"],
            "newer_net_usd": newer["net_usd"],
            "newer_profit_factor": newer["profit_factor"] or 0.0,
            "newer_win_rate_pct": newer["win_rate_pct"],
            "newer_active_days": newer["active_days"],
            "newer_trades_per_active_day": newer["trades_per_active_day"],
        }
    )
    summary["min_split_pf"] = round(min_window_pf(summary), 2)
    summary["decision"] = decision_for(summary)
    summary["score"] = round(portfolio_score(summary), 2)
    return summary


def search(pool: list[dict[str, Any]], max_size: int) -> list[dict[str, Any]]:
    priority = {str(item["name"]): index for index, item in enumerate(pool)}
    rows: list[dict[str, Any]] = []
    for size in range(1, max_size + 1):
        for combo in itertools.combinations(pool, size):
            rows.append(evaluate_combo(combo, priority))
    preferred = {"ROBUST_REVIEW_CANDIDATE": 0, "REVIEW_WITH_SPLIT_CAVEAT": 1}
    rows.sort(key=lambda row: (preferred.get(row["decision"], 9), -row["score"]))
    return rows


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "name",
        "members",
        "raw_trades",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "top25_removed_usd",
        "max_closed_drawdown_usd",
        "raw_duplicate_like_trade_pct",
        "dedupe_removed_trades",
        "older_trades",
        "older_net_usd",
        "older_profit_factor",
        "older_win_rate_pct",
        "older_trades_per_active_day",
        "newer_trades",
        "newer_net_usd",
        "newer_profit_factor",
        "newer_win_rate_pct",
        "newer_trades_per_active_day",
        "min_split_pf",
    ]
    return {key: row.get(key) for key in keys}


def render_markdown(rows: list[dict[str, Any]], reports: list[Path], output_json: Path) -> str:
    review = [
        row for row in rows if row["decision"] in {"ROBUST_REVIEW_CANDIDATE", "REVIEW_WITH_SPLIT_CAVEAT"}
    ]
    top = review[:30] if review else rows[:30]
    lines = [
        "# A1 XAU M5 Momentum Robust Portfolio Search",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The owner rejected sparse lanes and wants an active intraday system. The previous deep portfolio candidate fits frequency, but its older 2022-07 to 2024-06 split is weaker than its recent split. This search adds explicit split-period gates so we do not pick a portfolio that only works in the latest regime.",
        "",
        "Split rule: older window = entries before 2024-07-01; newer window = entries from 2024-07-01 onward.",
        "",
        "## Source reports",
        "",
    ]
    for report in reports:
        lines.append(f"- `{report}`")
    lines.extend(
        [
            "",
            "## Top Robust Candidates",
            "",
            "| Rank | Decision | Score | Members | Trades | WR % | Net | PF | Active | T/active | Older net/PF | Newer net/PF | Min split PF | +M/-M | Worst M | Top25 removed | DD | Dup % |",
            "|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(top, 1):
        lines.append(
            "| {rank} | `{decision}` | {score:.2f} | {members} | {trades} | {wr:.2f} | {net:.2f} | {pf} | {active} | {tpa:.2f} | {older_net:.2f} / {older_pf} | {newer_net:.2f} / {newer_pf} | {min_pf:.2f} | {pm}/{nm} | {worst:.2f} | {top25:.2f} | {dd:.2f} | {dup:.2f} |".format(
                rank=index,
                decision=row["decision"],
                score=row["score"],
                members="<br>".join(row["members"]),
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                older_net=row["older_net_usd"],
                older_pf=row["older_profit_factor"],
                newer_net=row["newer_net_usd"],
                newer_pf=row["newer_profit_factor"],
                min_pf=row["min_split_pf"],
                pm=row["positive_months"],
                nm=row["negative_months"],
                worst=row["worst_month_usd"],
                top25=row["top25_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
                dup=row["raw_duplicate_like_trade_pct"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "`ROBUST_REVIEW_CANDIDATE` means the candidate passes the frequency, WR, PF, duplicate, drawdown, top-winner, month-stability, and split-period checks. `REVIEW_WITH_SPLIT_CAVEAT` means the main metrics pass but one split has PF below 1.20; it may still be useful for forward testing but should not be treated as robust proof.",
            "",
            "No candidate here is authorization to attach. A forward demo still needs reviewer/owner approval and frozen inputs.",
            "",
            f"Machine-readable output: `{output_json}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(compact(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = compact(row)
            out["members"] = " | ".join(out["members"] or [])
            writer.writerow(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    parser.add_argument("--output-md", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SEARCH_2026_07_02.md")
    parser.add_argument("--output-json", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SEARCH_2026_07_02.json")
    parser.add_argument("--output-csv", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SEARCH_2026_07_02.csv")
    parser.add_argument("--pool-limit", type=int, default=34)
    parser.add_argument("--max-size", type=int, default=3)
    args = parser.parse_args()

    report_paths = sorted(path for path in args.reports_dir.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*.json") if is_four_year_report(path))
    variants = load_variants(report_paths)
    pool = build_pool(variants, args.pool_limit)
    rows = search(pool, args.max_size)
    compact_rows = [compact(row) for row in rows[:200]]

    payload = {
        "status": "ROBUST_PORTFOLIO_SEARCH_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "split_date": SPLIT_DATE.date().isoformat(),
        "pool_limit": args.pool_limit,
        "max_size": args.max_size,
        "variant_pool_count": len(pool),
        "candidate_count": len(rows),
        "source_reports": [str(path) for path in report_paths],
        "top_candidates": compact_rows[:25],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(rows, report_paths, args.output_json), encoding="utf-8")
    write_csv(args.output_csv, rows)
    print(args.output_md)
    print(args.output_json)
    print(args.output_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
