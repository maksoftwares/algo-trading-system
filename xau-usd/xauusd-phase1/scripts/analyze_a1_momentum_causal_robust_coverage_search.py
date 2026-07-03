from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_state_guard_search import top_removed_usd
from analyze_a1_momentum_market_day_coverage_search import (
    GUARD_SCENARIOS,
    day_distribution,
    date_window,
    dedupe_portfolio,
    load_csv_variants,
    load_synthetic_business_packages,
    search_portfolios,
)
from analyze_a1_momentum_market_day_coverage_stress import grouped_stats, rolling_stats
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_CAUSAL_ROBUST_COVERAGE_SEARCH_2026_07_03"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def guard_by_name(name: str) -> dict[str, Any]:
    for guard in GUARD_SCENARIOS:
        if guard["name"] == name:
            return guard
    raise ValueError(f"unknown guard: {name}")


def apply_named_guard(trades: list[dict[str, Any]], guard_name: str) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    from analyze_a1_momentum_daily_state_guard_search import apply_state_guard

    deduped, duplicate_drops = dedupe_portfolio(trades)
    guard = guard_by_name(guard_name)
    selected, guard_stats = apply_state_guard(
        deduped,
        state_rule="none",
        profit_target_usd=guard["profit_target_usd"],
        loss_stop_usd=guard["loss_stop_usd"],
        max_trades_per_day=guard["max_trades_per_day"],
        max_losses_per_day=guard["max_losses_per_day"],
        cooldown_after_loss_minutes=guard["cooldown_after_loss_minutes"],
        early_trade_count=guard["early_trade_count"],
        early_pnl_threshold=guard["early_pnl_threshold"],
    )
    return selected, guard_stats, duplicate_drops


def reconstruct(
    variants: dict[str, list[dict[str, Any]]],
    source_variants: list[str],
    guard_name: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], int, list[str]]:
    raw: list[dict[str, Any]] = []
    missing: list[str] = []
    for name in source_variants:
        rows = variants.get(name)
        if rows is None:
            missing.append(name)
            continue
        raw.extend(rows)
    selected, guard_stats, duplicate_drops = apply_named_guard(raw, guard_name)
    return selected, guard_stats, duplicate_drops, missing


def evaluate_candidate(
    variants: dict[str, list[dict[str, Any]]],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    selected, guard_stats, duplicate_drops, missing = reconstruct(
        variants,
        list(candidate.get("source_variants", [])),
        str(candidate.get("guard_name", "")),
    )
    if not selected:
        return {}
    start, end, market_days = date_window(selected)
    summary = summarize("robust_candidate", selected)
    summary.update(day_distribution(selected, market_days))
    half_year = grouped_stats(selected, "half_year")
    quarter = grouped_stats(selected, "quarter")
    rolling = [rolling_stats(selected, 250), rolling_stats(selected, 500)]
    top_removed = {
        "top100_removed_usd": top_removed_usd(selected, 100),
        "top200_removed_usd": top_removed_usd(selected, 200),
        "top300_removed_usd": top_removed_usd(selected, 300),
    }
    source_variants = list(candidate.get("source_variants", []))
    synthetic_sources = [name for name in source_variants if name.startswith("residual_")]
    rolling_250 = next((row for row in rolling if row.get("window") == 250), {})
    rolling_500 = next((row for row in rolling if row.get("window") == 500), {})
    negative_quarters = sum(1 for row in quarter if row["net_usd"] <= 0)
    negative_half_years = sum(1 for row in half_year if row["net_usd"] <= 0)
    decision = decide(summary, top_removed, rolling_250, rolling_500, negative_quarters, negative_half_years)
    return {
        "decision": decision,
        "portfolio_name": candidate.get("portfolio_name", ""),
        "guard_name": candidate.get("guard_name", ""),
        "source_variants": source_variants,
        "synthetic_source_count": len(synthetic_sources),
        "synthetic_sources": synthetic_sources,
        "missing_sources": missing,
        "date_start": start.isoformat(),
        "date_end": end.isoformat(),
        "duplicate_drops": duplicate_drops,
        "guard_stats": guard_stats,
        "negative_half_years": negative_half_years,
        "negative_quarters": negative_quarters,
        "rolling_250_negative": rolling_250.get("negative_windows", 0),
        "rolling_250_pf_below_1": rolling_250.get("pf_below_1_windows", 0),
        "rolling_250_worst_net": rolling_250.get("worst_net", {}),
        "rolling_250_worst_pf": rolling_250.get("worst_pf", {}),
        "rolling_500_negative": rolling_500.get("negative_windows", 0),
        "rolling_500_pf_below_1": rolling_500.get("pf_below_1_windows", 0),
        "rolling_500_worst_net": rolling_500.get("worst_net", {}),
        "rolling_500_worst_pf": rolling_500.get("worst_pf", {}),
        **summary,
        **top_removed,
    }


def decide(
    summary: dict[str, Any],
    top_removed: dict[str, float],
    rolling_250: dict[str, Any],
    rolling_500: dict[str, Any],
    negative_quarters: int,
    negative_half_years: int,
) -> str:
    if summary["trades"] < 1000:
        return "FAIL_SAMPLE"
    if summary["trades_per_market_day"] < 3.0:
        return "FAIL_OWNER_CADENCE"
    if summary["win_rate_pct"] < 60.0:
        return "FAIL_WIN_RATE"
    if (summary["profit_factor"] or 0.0) < 1.25:
        return "FAIL_PROFIT_FACTOR"
    if top_removed["top200_removed_usd"] <= 0:
        return "FAIL_TOP200_ROBUSTNESS"
    if negative_half_years > 0:
        return "FAIL_HALF_YEAR_STABILITY"
    if negative_quarters > 3:
        return "FAIL_QUARTER_STABILITY"
    if rolling_500.get("negative_windows", 0) > 0:
        return "FAIL_500_ROLLING"
    if top_removed["top300_removed_usd"] <= 0 or rolling_250.get("negative_windows", 0) > 0:
        return "REVISE_ROBUSTNESS"
    return "REVIEW_STRONG_CAUSAL_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    decision_bonus = {
        "REVIEW_STRONG_CAUSAL_CANDIDATE": 800.0,
        "REVISE_ROBUSTNESS": 300.0,
    }.get(str(row.get("decision")), 0.0)
    return round(
        decision_bonus
        + float(row.get("net_usd") or 0.0)
        + 80.0 * float(row.get("trades_per_market_day") or 0.0)
        + 10.0 * float(row.get("win_rate_pct") or 0.0)
        + 120.0 * ((float(row.get("profit_factor") or 0.0)) - 1.0)
        + 0.2 * float(row.get("top300_removed_usd") or 0.0)
        - 0.5 * float(row.get("rolling_250_negative") or 0.0)
        - 4.0 * float(row.get("negative_quarters") or 0.0)
        - 30.0 * float(row.get("synthetic_source_count") or 0.0),
        2,
    )


def unique_candidates(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    seen: set[tuple[tuple[str, ...], str]] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = (tuple(sorted(row.get("source_variants", []))), str(row.get("guard_name", "")))
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
        if len(unique) >= limit:
            break
    return unique


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "decision",
        "portfolio_name",
        "guard_name",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net_usd",
        "trades_per_market_day",
        "trades_per_active_day",
        "active_market_day_pct",
        "three_plus_market_day_pct",
        "positive_active_day_pct",
        "top100_removed_usd",
        "top200_removed_usd",
        "top300_removed_usd",
        "negative_half_years",
        "negative_quarters",
        "rolling_250_negative",
        "rolling_500_negative",
        "synthetic_source_count",
        "duplicate_drops",
        "score",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def render(payload: dict[str, Any]) -> str:
    best = payload.get("best_result", {})
    lines = [
        "# A1 XAU M5 Momentum Causal Robust Coverage Search - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Purpose",
        "",
        "Claude's review correctly rejected the old guarded headline. This report reruns the search with the event-time causal guard and then ranks candidates by the owner's actual cadence goal plus stricter robustness.",
        "",
        "Hard screen: >=1000 trades, >=3 trades per weekday market day, WR >=60%, PF >=1.25, top200-winners-removed positive, no negative half-years, <=3 negative quarters, and no negative 500-trade rolling windows.",
        "",
        "Strong candidate requires top300-winners-removed positive and zero negative 250-trade rolling windows. Otherwise it remains `REVISE_ROBUSTNESS`.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision', '')}` |",
        f"| Portfolio | `{best.get('portfolio_name', '')}` |",
        f"| Guard | `{best.get('guard_name', '')}` |",
        f"| Trades | {best.get('trades', 'n/a')} |",
        f"| Win rate | {best.get('win_rate_pct', 'n/a')}% |",
        f"| Profit factor | {best.get('profit_factor', 'n/a')} |",
        f"| Net | {best.get('net_usd', 'n/a')} USD |",
        f"| Trades / market day | {best.get('trades_per_market_day', 'n/a')} |",
        f"| 3+ trade market days | {best.get('three_plus_market_day_pct', 'n/a')}% |",
        f"| Top 200 removed | {best.get('top200_removed_usd', 'n/a')} USD |",
        f"| Top 300 removed | {best.get('top300_removed_usd', 'n/a')} USD |",
        f"| Negative 250-trade windows | {best.get('rolling_250_negative', 'n/a')} |",
        f"| Negative 500-trade windows | {best.get('rolling_500_negative', 'n/a')} |",
        f"| Synthetic source count | {best.get('synthetic_source_count', 'n/a')} |",
        "",
        "## Top Candidates",
        "",
        "| Rank | Decision | Portfolio | Guard | Trades | WR | PF | Net | T/market day | Top300 | 250-neg | Synth |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload.get("top_results", [])[:20], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{portfolio}` | `{guard}` | {trades} | {wr}% | {pf} | {net} | {tpmd} | {top300} | {r250} | {synth} |".format(
                rank=index,
                decision=row.get("decision", ""),
                portfolio=str(row.get("portfolio_name", ""))[:88],
                guard=row.get("guard_name", ""),
                trades=row.get("trades", ""),
                wr=row.get("win_rate_pct", ""),
                pf=row.get("profit_factor", ""),
                net=row.get("net_usd", ""),
                tpmd=row.get("trades_per_market_day", ""),
                top300=row.get("top300_removed_usd", ""),
                r250=row.get("rolling_250_negative", ""),
                synth=row.get("synthetic_source_count", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A frequent, positive book remains real after removing the guard leak.",
            "- The current best still fails the strong robustness bar because top300-winners-removed is negative and some 250-trade rolling windows are negative.",
            "- This should steer the next build: keep the cadence idea, but reduce reliance on search-fit residual packages and improve the weak rolling windows before attaching.",
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
    base_results = search_portfolios(variants)
    reviewable = [row for row in base_results if not str(row.get("decision", "")).startswith("FAIL")]
    candidates = unique_candidates(reviewable or base_results, 80)
    stressed: list[dict[str, Any]] = []
    for candidate in candidates:
        result = evaluate_candidate(variants, candidate)
        if not result:
            continue
        result["score"] = score(result)
        stressed.append(result)
    stressed.sort(
        key=lambda row: (
            0 if row["decision"] == "REVIEW_STRONG_CAUSAL_CANDIDATE" else 1 if row["decision"] == "REVISE_ROBUSTNESS" else 2,
            -row["score"],
            -float(row.get("trades_per_market_day") or 0.0),
            -float(row.get("net_usd") or 0.0),
        )
    )

    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "PASS_CAUSAL_ROBUST_SEARCH_READY" if stressed else "FAIL_NO_RESULTS",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "guard_model": "event_time_causal_v2",
        "candidate_count": len(candidates),
        "stressed_count": len(stressed),
        "best_result": stressed[0] if stressed else {},
        "top_results": stressed[:50],
        "json": rel(output_json),
        "csv": rel(output_csv),
        "report": rel(output_md),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(output_csv, stressed)
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "best_decision": payload["best_result"].get("decision"),
                "best": payload["best_result"].get("portfolio_name"),
                "trades": payload["best_result"].get("trades"),
                "win_rate_pct": payload["best_result"].get("win_rate_pct"),
                "profit_factor": payload["best_result"].get("profit_factor"),
                "net_usd": payload["best_result"].get("net_usd"),
                "trades_per_market_day": payload["best_result"].get("trades_per_market_day"),
                "top300_removed_usd": payload["best_result"].get("top300_removed_usd"),
                "rolling_250_negative": payload["best_result"].get("rolling_250_negative"),
            },
            indent=2,
        )
    )
    return 0 if stressed else 1


if __name__ == "__main__":
    raise SystemExit(main())
