from __future__ import annotations

import csv
import itertools
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import load_variants
from analyze_a1_momentum_causal_robust_coverage_search import reconstruct
from analyze_a1_momentum_distinct_family_companion_search import COMMON_END, COMMON_START, DISTINCT_REPORTS, restrict
from analyze_a1_momentum_market_day_coverage_search import (
    date_window,
    day_distribution,
    dedupe_portfolio,
    load_csv_variants,
    load_synthetic_business_packages,
)
from analyze_a1_momentum_market_day_coverage_stress import grouped_stats, rolling_stats
from analyze_a1_momentum_portfolio_combinations import summarize
from analyze_a1_momentum_position_sizing_diagnostic import BASE_SOURCES, DISTINCT_ADDON, r_profit, rel, top_removed


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_HOUR_PRUNE_SEARCH_2026_07_03"


def metric_row(name: str, rows: list[dict[str, Any]], blocked_hours: tuple[int, ...]) -> dict[str, Any]:
    kept = [row for row in rows if int(row.get("entry_hour", -1)) not in blocked_hours]
    deduped, duplicate_drops = dedupe_portfolio(kept)
    if not deduped:
        return {}
    start, end, market_days = date_window(deduped)
    summary = summarize(name, deduped)
    summary.update(day_distribution(deduped, market_days))
    profits = [float(row.get("profit", 0.0) or 0.0) for row in deduped]
    r_values = [r_profit(row) for row in deduped]
    half = grouped_stats(deduped, "half_year")
    quarter = grouped_stats(deduped, "quarter")
    r250 = rolling_stats(deduped, 250)
    r500 = rolling_stats(deduped, 500)
    summary.update(
        {
            "blocked_hours": blocked_hours,
            "blocked_hours_csv": ",".join(str(hour) for hour in blocked_hours),
            "duplicate_drops": duplicate_drops,
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "top100_removed_usd": top_removed(profits, 100),
            "top200_removed_usd": top_removed(profits, 200),
            "top300_removed_usd": top_removed(profits, 300),
            "net_r_fixed_risk": round(sum(r_values), 2),
            "top100_removed_r": top_removed(r_values, 100),
            "top200_removed_r": top_removed(r_values, 200),
            "top300_removed_r": top_removed(r_values, 300),
            "negative_half_years": sum(1 for row in half if row["net_usd"] <= 0),
            "negative_quarters": sum(1 for row in quarter if row["net_usd"] <= 0),
            "rolling_250_negative": r250.get("negative_windows", 0),
            "rolling_500_negative": r500.get("negative_windows", 0),
        }
    )
    summary["decision"] = decide(summary)
    summary["score"] = score(summary)
    return summary


def decide(row: dict[str, Any]) -> str:
    if row["trades"] < 1000:
        return "FAIL_SAMPLE"
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_CADENCE"
    if row["win_rate_pct"] < 60.0 or (row["profit_factor"] or 0.0) < 1.25:
        return "FAIL_QUALITY"
    if row["top200_removed_usd"] <= 0:
        return "FAIL_USD_TOP200"
    if row["top300_removed_r"] <= 0:
        return "REVISE_R_TOP300"
    if row["negative_half_years"] > 0 or row["negative_quarters"] > 3:
        return "FAIL_STABILITY"
    if row["rolling_500_negative"] > 0:
        return "FAIL_500_ROLLING"
    if row["rolling_250_negative"] > 0:
        return "REVISE_250_ROLLING"
    return "REVIEW_HOUR_PRUNED_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    bonus = {
        "REVIEW_HOUR_PRUNED_CANDIDATE": 2500.0,
        "REVISE_250_ROLLING": 900.0,
        "REVISE_R_TOP300": 400.0,
    }.get(row.get("decision", ""), 0.0)
    return round(
        bonus
        + float(row.get("net_usd") or 0.0)
        + 120.0 * float(row.get("trades_per_market_day") or 0.0)
        + 12.0 * float(row.get("win_rate_pct") or 0.0)
        + 250.0 * ((float(row.get("profit_factor") or 0.0)) - 1.0)
        + float(row.get("top200_removed_usd") or 0.0)
        + 12.0 * float(row.get("top300_removed_r") or 0.0)
        - 1.5 * float(row.get("rolling_250_negative") or 0.0)
        - 20.0 * len(row.get("blocked_hours", ())),
        2,
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "blocked_hours_csv",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net_usd",
        "trades_per_market_day",
        "three_plus_market_day_pct",
        "top100_removed_usd",
        "top200_removed_usd",
        "top300_removed_usd",
        "net_r_fixed_risk",
        "top100_removed_r",
        "top200_removed_r",
        "top300_removed_r",
        "negative_half_years",
        "negative_quarters",
        "rolling_250_negative",
        "rolling_500_negative",
        "score",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload.get("best_result", {})
    lines = [
        "# A1 XAU M5 Momentum Hour-Prune Search - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline analysis only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Purpose",
        "",
        "The base+distinct-family book is close in fixed-risk terms but still fails top-winner robustness. This search checks whether the weakness is concentrated in a small set of entry hours while preserving the owner's `>=3 trades/market day` goal.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision', '')}` |",
        f"| Blocked hours | `{best.get('blocked_hours_csv', '')}` |",
        f"| Trades | {best.get('trades', 'n/a')} |",
        f"| Win rate | {best.get('win_rate_pct', 'n/a')}% |",
        f"| PF | {best.get('profit_factor', 'n/a')} |",
        f"| Net | {best.get('net_usd', 'n/a')} USD |",
        f"| Trades / market day | {best.get('trades_per_market_day', 'n/a')} |",
        f"| USD top200 removed | {best.get('top200_removed_usd', 'n/a')} |",
        f"| Fixed-R top300 removed | {best.get('top300_removed_r', 'n/a')} |",
        f"| Rolling 250 negative | {best.get('rolling_250_negative', 'n/a')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Block Hours | Trades | WR | PF | Net | T/market day | USD top200 | R top300 | 250-neg |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload.get("top_results", [])[:25], start=1):
        lines.append(
            f"| {index} | `{row.get('decision', '')}` | `{row.get('blocked_hours_csv', '')}` | {row.get('trades', '')} | {row.get('win_rate_pct', '')}% | {row.get('profit_factor', '')} | {row.get('net_usd', '')} | {row.get('trades_per_market_day', '')} | {row.get('top200_removed_usd', '')} | {row.get('top300_removed_r', '')} | {row.get('rolling_250_negative', '')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Verdict: `{payload['verdict']}`",
            f"- Next action: `{payload['next_action']}`",
            "",
            "Hour masks are easy to overfit. Any candidate from this report must be independently reviewed and exact-tested before runtime use.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Report: `{payload['report']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    variants = {**load_csv_variants(), **load_synthetic_business_packages()}
    base_rows, _guard_stats, _dups, missing = reconstruct(variants, BASE_SOURCES, "no_daily_guard")
    if missing:
        raise RuntimeError(f"missing base variants: {missing}")
    addon_item = load_variants(DISTINCT_REPORTS).get(DISTINCT_ADDON)
    if not addon_item:
        raise RuntimeError(f"missing addon variant: {DISTINCT_ADDON}")
    seed_rows = restrict(base_rows + addon_item["trades"])
    combos: list[tuple[int, ...]] = [()]
    hours = tuple(range(24))
    for size in (1, 2):
        combos.extend(itertools.combinations(hours, size))
    rows: list[dict[str, Any]] = []
    for combo in combos:
        rows.append(metric_row("base_plus_sweep_hour_pruned", seed_rows, tuple(combo)))
    rows = [row for row in rows if row]
    rows.sort(
        key=lambda row: (
            0 if row["decision"] == "REVIEW_HOUR_PRUNED_CANDIDATE" else 1 if row["decision"].startswith("REVISE") else 2,
            -row["score"],
            -float(row.get("trades_per_market_day") or 0.0),
        )
    )
    best = rows[0] if rows else {}
    verdict = (
        "FOUND_REVIEW_CANDIDATE"
        if best.get("decision") == "REVIEW_HOUR_PRUNED_CANDIDATE"
        else "NO_HOUR_PRUNED_CANDIDATE_YET"
    )
    next_action = (
        "prepare_reviewer_packet_and_exact_mt5_rerun"
        if verdict == "FOUND_REVIEW_CANDIDATE"
        else "do_not_use_hour_mask_as_solution"
    )
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "PASS_HOUR_PRUNE_SEARCH_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_analysis_only_no_runtime_change",
        "window": f"{COMMON_START.date()} -> {COMMON_END.date()}",
        "combo_count": len(combos),
        "verdict": verdict,
        "next_action": next_action,
        "best_result": best,
        "top_results": rows[:50],
        "json": rel(output_json),
        "csv": rel(output_csv),
        "report": rel(output_md),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(output_csv, rows)
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "verdict": verdict,
                "decision": best.get("decision"),
                "blocked_hours": best.get("blocked_hours_csv"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor": best.get("profit_factor"),
                "net_usd": best.get("net_usd"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top200_removed_usd": best.get("top200_removed_usd"),
                "top300_removed_r": best.get("top300_removed_r"),
                "rolling_250_negative": best.get("rolling_250_negative"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
