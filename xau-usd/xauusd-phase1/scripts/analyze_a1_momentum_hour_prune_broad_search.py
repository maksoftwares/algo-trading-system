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
from analyze_a1_momentum_hour_prune_search import decide, score
from analyze_a1_momentum_market_day_coverage_search import (
    date_window,
    day_distribution,
    load_csv_variants,
    load_synthetic_business_packages,
)
from analyze_a1_momentum_market_day_coverage_stress import grouped_stats, rolling_stats
from analyze_a1_momentum_portfolio_combinations import summarize
from analyze_a1_momentum_position_sizing_diagnostic import BASE_SOURCES, DISTINCT_ADDON, r_profit, rel, top_removed


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_HOUR_PRUNE_BROAD_SEARCH_2026_07_03"
MAX_BLOCKED_HOURS = 4


def load_seed_rows() -> list[dict[str, Any]]:
    variants = {**load_csv_variants(), **load_synthetic_business_packages()}
    base_rows, _guard_stats, _dups, missing = reconstruct(variants, BASE_SOURCES, "no_daily_guard")
    if missing:
        raise RuntimeError(f"missing base variants: {missing}")
    addon_item = load_variants(DISTINCT_REPORTS).get(DISTINCT_ADDON)
    if not addon_item:
        raise RuntimeError(f"missing addon variant: {DISTINCT_ADDON}")
    return sorted(
        restrict(base_rows + addon_item["trades"]),
        key=lambda row: (row["entry_time"], row["variant"], row["direction"]),
    )


def dedupe_after_hour_block(
    sorted_rows: list[dict[str, Any]], blocked_hours: tuple[int, ...], window_minutes: int = 5
) -> tuple[list[dict[str, Any]], int]:
    blocked = set(blocked_hours)
    kept: list[dict[str, Any]] = []
    dropped = 0
    max_seconds = window_minutes * 60
    for row in sorted_rows:
        if int(row.get("entry_hour", -1)) in blocked:
            continue
        duplicate = False
        for previous in reversed(kept[-20:]):
            delta = abs((row["entry_time"] - previous["entry_time"]).total_seconds())
            if delta > max_seconds:
                break
            if row["direction"] == previous["direction"]:
                duplicate = True
                break
        if duplicate:
            dropped += 1
            continue
        kept.append(row)
    return kept, dropped


def evaluate(
    sorted_rows: list[dict[str, Any]], blocked_hours: tuple[int, ...], include_rolling: bool = False
) -> dict[str, Any]:
    deduped, duplicate_drops = dedupe_after_hour_block(sorted_rows, blocked_hours)
    if not deduped:
        return {}
    start, end, market_days = date_window(deduped)
    summary = summarize("base_plus_sweep_hour_pruned_broad", deduped)
    summary.update(day_distribution(deduped, market_days))
    profits = [float(row.get("profit", 0.0) or 0.0) for row in deduped]
    r_values = [r_profit(row) for row in deduped]
    summary.update(
        {
            "blocked_hours": blocked_hours,
            "blocked_hours_csv": ",".join(str(hour) for hour in blocked_hours),
            "blocked_hour_count": len(blocked_hours),
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
            "negative_half_years": None,
            "negative_quarters": None,
            "rolling_250_negative": None,
            "rolling_500_negative": None,
        }
    )
    if include_rolling:
        half = grouped_stats(deduped, "half_year")
        quarter = grouped_stats(deduped, "quarter")
        r250 = rolling_stats(deduped, 250)
        r500 = rolling_stats(deduped, 500)
        summary.update(
            {
                "negative_half_years": sum(1 for row in half if row["net_usd"] <= 0),
                "negative_quarters": sum(1 for row in quarter if row["net_usd"] <= 0),
                "rolling_250_negative": r250.get("negative_windows", 0),
                "rolling_500_negative": r500.get("negative_windows", 0),
            }
        )
    else:
        # Use neutral placeholders for preliminary ordering only. Final top rows are
        # re-evaluated with rolling/stability statistics before writing artifacts.
        summary.update(
            {
                "negative_half_years": 0,
                "negative_quarters": 0,
                "rolling_250_negative": 0,
                "rolling_500_negative": 0,
            }
        )
    summary["decision"] = decide(summary)
    summary["score"] = score(summary)
    return summary


def search(sorted_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    combos: list[tuple[int, ...]] = [()]
    hours = tuple(range(24))
    for size in range(1, MAX_BLOCKED_HOURS + 1):
        combos.extend(itertools.combinations(hours, size))

    preliminary: list[dict[str, Any]] = []
    for combo in combos:
        row = evaluate(sorted_rows, combo, include_rolling=False)
        if row:
            preliminary.append(row)

    preliminary.sort(
        key=lambda row: (
            0 if row["decision"] == "REVIEW_HOUR_PRUNED_CANDIDATE" else 1 if row["decision"].startswith("REVISE") else 2,
            -row["score"],
            -float(row.get("top200_removed_usd") or 0.0),
        )
    )
    # Recompute the most relevant rows with full rolling/stability stats. Include
    # all provisional pass/revise rows plus the top score rows so the report can
    # explain near misses honestly without spending rolling-window time on every mask.
    selected_combos: set[tuple[int, ...]] = {
        tuple(row["blocked_hours"])
        for row in preliminary
        if row["decision"] in {"REVIEW_HOUR_PRUNED_CANDIDATE", "REVISE_250_ROLLING", "REVISE_R_TOP300"}
        or float(row.get("top200_removed_usd") or 0.0) > -150.0
    }
    selected_combos.update(tuple(row["blocked_hours"]) for row in preliminary[:300])

    final_by_combo: dict[tuple[int, ...], dict[str, Any]] = {}
    for combo in selected_combos:
        final_by_combo[combo] = evaluate(sorted_rows, combo, include_rolling=True)

    final_rows = [final_by_combo.get(tuple(row["blocked_hours"]), row) for row in preliminary]
    final_rows.sort(
        key=lambda row: (
            0 if row["decision"] == "REVIEW_HOUR_PRUNED_CANDIDATE" else 1 if row["decision"].startswith("REVISE") else 2,
            -row["score"],
            -float(row.get("trades_per_market_day") or 0.0),
        )
    )
    return final_rows, len(combos)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "blocked_hours_csv",
        "blocked_hour_count",
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
        "# A1 XAU M5 Momentum Broad Hour-Prune Search - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline analysis only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Purpose",
        "",
        f"The previous hour-prune search checked only one- and two-hour masks. This expands the search to masks of up to `{MAX_BLOCKED_HOURS}` blocked server hours while keeping the owner's cadence target and the same top-winner robustness gates.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision', '')}` |",
        f"| Blocked hours | `{best.get('blocked_hours_csv', '')}` |",
        f"| Blocked hour count | {best.get('blocked_hour_count', 'n/a')} |",
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
            "If this report finds a candidate, it is still a review candidate only. Hour masks are especially easy to overfit; exact MT5 verification and reviewer approval remain required before any runtime change.",
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
    rows, combo_count = search(load_seed_rows())
    best = rows[0] if rows else {}
    verdict = (
        "FOUND_REVIEW_CANDIDATE"
        if best.get("decision") == "REVIEW_HOUR_PRUNED_CANDIDATE"
        else "NO_BROAD_HOUR_PRUNED_CANDIDATE_YET"
    )
    next_action = (
        "prepare_reviewer_packet_and_exact_mt5_rerun"
        if verdict == "FOUND_REVIEW_CANDIDATE"
        else "do_not_use_hour_mask_as_solution_without_new_edge"
    )
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "PASS_BROAD_HOUR_PRUNE_SEARCH_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_analysis_only_no_runtime_change",
        "window": f"{COMMON_START.date()} -> {COMMON_END.date()}",
        "max_blocked_hours": MAX_BLOCKED_HOURS,
        "combo_count": combo_count,
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
