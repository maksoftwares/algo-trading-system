from __future__ import annotations

import csv
import itertools
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from analyze_a1_momentum_position_sizing_diagnostic import (
    BASE_SOURCES,
    DISTINCT_ADDON,
    rel,
    r_profit,
    top_removed,
)
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


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_GROUP_PRUNE_SEARCH_2026_07_03"


def source(row: dict[str, Any]) -> str:
    return str(row.get("portfolio_member") or row.get("variant") or "")


def prune_rules() -> dict[str, Callable[[dict[str, Any]], bool]]:
    return {
        "drop_weak_cost005_source": lambda row: source(row)
        == "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1",
        "drop_sweep_reclaim_addon": lambda row: source(row) == DISTINCT_ADDON,
        "drop_evening": lambda row: str(row.get("entry_session") or "") == "evening",
        "drop_morning": lambda row: str(row.get("entry_session") or "") == "morning",
        "drop_low_r_sources": lambda row: source(row)
        in {
            "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1",
            DISTINCT_ADDON,
        },
    }


def metric_row(name: str, rows: list[dict[str, Any]], applied_rules: list[str]) -> dict[str, Any]:
    deduped, duplicate_drops = dedupe_portfolio(rows)
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
            "applied_rules": applied_rules,
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "duplicate_drops": duplicate_drops,
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
    return "REVIEW_PRUNED_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    bonus = {
        "REVIEW_PRUNED_CANDIDATE": 2000.0,
        "REVISE_250_ROLLING": 750.0,
        "REVISE_R_TOP300": 300.0,
    }.get(row.get("decision", ""), 0.0)
    return round(
        bonus
        + float(row.get("net_usd") or 0.0)
        + 100.0 * float(row.get("trades_per_market_day") or 0.0)
        + 12.0 * float(row.get("win_rate_pct") or 0.0)
        + 200.0 * ((float(row.get("profit_factor") or 0.0)) - 1.0)
        + 1.0 * float(row.get("top200_removed_usd") or 0.0)
        + 8.0 * float(row.get("top300_removed_r") or 0.0)
        - 1.2 * float(row.get("rolling_250_negative") or 0.0),
        2,
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "name",
        "applied_rules",
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
            out = dict(row)
            out["applied_rules"] = ",".join(row.get("applied_rules", []))
            writer.writerow({field: out.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload.get("best_result", {})
    lines = [
        "# A1 XAU M5 Momentum Group-Prune Search - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline analysis only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Purpose",
        "",
        "The position-sizing diagnostic showed that fixed-risk sizing helps but does not fully solve large-winner dependence. This search removes only weak groups identified by source/session diagnostics to see whether the existing candidate can meet cadence and robustness together.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision', '')}` |",
        f"| Rules | `{', '.join(best.get('applied_rules', []))}` |",
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
        "| Rank | Decision | Rules | Trades | WR | PF | Net | T/market day | USD top200 | R top300 | 250-neg |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload.get("top_results", [])[:20], start=1):
        lines.append(
            f"| {index} | `{row.get('decision', '')}` | `{', '.join(row.get('applied_rules', [])) or 'none'}` | {row.get('trades', '')} | {row.get('win_rate_pct', '')}% | {row.get('profit_factor', '')} | {row.get('net_usd', '')} | {row.get('trades_per_market_day', '')} | {row.get('top200_removed_usd', '')} | {row.get('top300_removed_r', '')} | {row.get('rolling_250_negative', '')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Search verdict: `{payload['verdict']}`",
            f"- Next action: `{payload['next_action']}`",
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
    rules = prune_rules()
    rows: list[dict[str, Any]] = []
    rule_names = list(rules)
    for size in range(0, 4):
        for selected in itertools.combinations(rule_names, size):
            if "drop_low_r_sources" in selected and (
                "drop_weak_cost005_source" in selected or "drop_sweep_reclaim_addon" in selected
            ):
                continue
            kept = [
                row
                for row in seed_rows
                if not any(rules[name](row) for name in selected)
            ]
            metric = metric_row("base_plus_sweep_pruned", kept, list(selected))
            if metric:
                rows.append(metric)
    rows.sort(
        key=lambda row: (
            0 if row["decision"] == "REVIEW_PRUNED_CANDIDATE" else 1 if row["decision"].startswith("REVISE") else 2,
            -row["score"],
            -float(row.get("trades_per_market_day") or 0.0),
        )
    )
    best = rows[0] if rows else {}
    verdict = (
        "FOUND_REVIEW_CANDIDATE"
        if best.get("decision") == "REVIEW_PRUNED_CANDIDATE"
        else "NO_PRUNED_CANDIDATE_YET"
    )
    next_action = (
        "prepare_review_prompt_and_exact_mt5_rerun"
        if verdict == "FOUND_REVIEW_CANDIDATE"
        else "new_entry_mechanism_required"
    )
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "PASS_GROUP_PRUNE_SEARCH_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_analysis_only_no_runtime_change",
        "window": f"{COMMON_START.date()} -> {COMMON_END.date()}",
        "verdict": verdict,
        "next_action": next_action,
        "candidate_count": len(rows),
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
                "best_decision": best.get("decision"),
                "rules": best.get("applied_rules"),
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
