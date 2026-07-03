from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_causal_robust_coverage_search import evaluate_candidate, unique_candidates
from analyze_a1_momentum_market_day_coverage_search import (
    guard_by_name,
    load_csv_variants,
    search_portfolios,
    traced_guard_rows,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_PURE_CAUSAL_COVERAGE_SEARCH_2026_07_03"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def score(row: dict[str, Any]) -> float:
    decision_bonus = {
        "REVIEW_STRONG_CAUSAL_CANDIDATE": 1000.0,
        "REVISE_ROBUSTNESS": 450.0,
        "REVIEW_CANDIDATE_OWNER_CADENCE": 250.0,
    }.get(str(row.get("decision")), 0.0)
    return round(
        decision_bonus
        + float(row.get("net_usd") or 0.0)
        + 100.0 * float(row.get("trades_per_market_day") or 0.0)
        + 12.0 * float(row.get("win_rate_pct") or 0.0)
        + 160.0 * (float(row.get("profit_factor") or 0.0) - 1.0)
        + 0.2 * float(row.get("top200_removed_usd") or 0.0)
        + 0.1 * float(row.get("top300_removed_usd") or 0.0)
        - 0.4 * float(row.get("rolling_250_negative") or 0.0)
        - 80.0 * float(row.get("negative_half_years") or 0.0),
        2,
    )


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
        "three_plus_market_day_pct",
        "top100_removed_usd",
        "top200_removed_usd",
        "top300_removed_usd",
        "rolling_250_negative",
        "rolling_500_negative",
        "negative_quarters",
        "negative_half_years",
        "duplicate_drops",
        "source_variant_count",
        "score",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def write_kept_dropped(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render(payload: dict[str, Any]) -> str:
    best = payload["best_result"]
    lines = [
        "# A1 XAU M5 Momentum Pure Causal Coverage Search - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 terminal, chart, preset, order, or position was touched.",
        "",
        "## Why This Report Exists",
        "",
        "Claude's independent review rejected the earlier 3,900-trade headline because the old guard layer looked outcome-leaky. This report removes the synthetic residual packages and reruns the coverage search using only exact MT5 tester trade CSVs plus the event-time causal guard.",
        "",
        "The purpose is to find the cleanest frequent candidate that still matches the owner's goal: multiple intraday trades, win rate above 50%, positive PF/net, and no hidden duplicate stacking.",
        "",
        "## Verdict",
        "",
        f"- Best pure tester candidate: `{best.get('portfolio_name', '')}`.",
        f"- Guard: `{best.get('guard_name', '')}`.",
        f"- Result: {best.get('trades')} trades, {best.get('win_rate_pct')}% WR, PF {best.get('profit_factor')}, net {best.get('net_usd')} USD, {best.get('trades_per_market_day')} trades/market day.",
        f"- Robustness: top200-winners-removed = {best.get('top200_removed_usd')} USD, top300-winners-removed = {best.get('top300_removed_usd')} USD, negative 250-trade rolling windows = {best.get('rolling_250_negative')}.",
        "",
        "Decision: `REVISE_ROBUSTNESS_PURE_TESTER_CANDIDATE`. The candidate is cleaner and frequent enough to study, but it is not yet a final demo attach because deeper top-winner removal and 250-trade rolling windows are still weak.",
        "",
        "## Top Pure Tester Candidates",
        "",
        "| Rank | Decision | Portfolio | Guard | Trades | WR | PF | Net | Trades/day | Top200 | Top300 | 250-neg |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_results"][:20], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{portfolio}` | `{guard}` | {trades} | {wr}% | {pf} | {net} | {tpd} | {top200} | {top300} | {r250} |".format(
                rank=index,
                decision=row.get("decision", ""),
                portfolio=str(row.get("portfolio_name", ""))[:82],
                guard=row.get("guard_name", ""),
                trades=row.get("trades", ""),
                wr=row.get("win_rate_pct", ""),
                pf=row.get("profit_factor", ""),
                net=row.get("net_usd", ""),
                tpd=row.get("trades_per_market_day", ""),
                top200=row.get("top200_removed_usd", ""),
                top300=row.get("top300_removed_usd", ""),
                r250=row.get("rolling_250_negative", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Actionable Read",
            "",
            "1. Do not use the old leaked 66%/PF1.44 headline.",
            "2. Treat this pure candidate as the current best frequent XAU momentum base.",
            "3. The next repair should target the 122 negative rolling-250 windows and top300 fragility, not add another outcome-shaped daily guard.",
            "4. If a demo lane is considered, it should be explicitly labelled forward-test/provisional, with small lot, pinned start, no tuning, and reviewer signoff.",
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Best kept/dropped audit CSV: `{payload['best_kept_dropped_csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    variants = load_csv_variants()
    base_results = search_portfolios(variants)
    reviewable = [row for row in base_results if not str(row.get("decision", "")).startswith("FAIL")]
    candidates = unique_candidates(reviewable or base_results, 120)
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
            -float(row.get("score") or 0.0),
            -float(row.get("trades_per_market_day") or 0.0),
            -float(row.get("net_usd") or 0.0),
        )
    )
    best = stressed[0] if stressed else {}

    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_kept_dropped = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT_DROPPED.csv"
    kept_dropped_rows: list[dict[str, Any]] = []
    kept_dropped_stats: dict[str, Any] = {}
    if best:
        raw: list[dict[str, Any]] = []
        for name in best.get("source_variants", []):
            raw.extend(variants.get(name, []))
        kept_dropped_rows, kept_dropped_stats = traced_guard_rows(raw, guard_by_name(str(best["guard_name"])))
        write_kept_dropped(output_kept_dropped, kept_dropped_rows)

    payload = {
        "status": "REVISE_ROBUSTNESS_PURE_TESTER_CANDIDATE" if stressed else "FAIL_NO_PURE_RESULTS",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "guard_model": "event_time_causal_v2",
        "synthetic_packages_allowed": False,
        "loaded_csv_variant_count": len(variants),
        "base_result_count": len(base_results),
        "stressed_count": len(stressed),
        "best_result": best,
        "top_results": stressed[:50],
        "best_kept_dropped_stats": kept_dropped_stats,
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
        "best_kept_dropped_csv": rel(output_kept_dropped) if kept_dropped_rows else "",
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(output_csv, stressed)
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "best": best.get("portfolio_name"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor": best.get("profit_factor"),
                "net_usd": best.get("net_usd"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top300_removed_usd": best.get("top300_removed_usd"),
                "rolling_250_negative": best.get("rolling_250_negative"),
            },
            indent=2,
        )
    )
    return 0 if stressed else 1


if __name__ == "__main__":
    raise SystemExit(main())
