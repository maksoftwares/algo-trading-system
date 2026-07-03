from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_causal_robust_coverage_search import reconstruct
from analyze_a1_momentum_broad_portfolio_search import load_variants
from analyze_a1_momentum_distinct_family_companion_search import COMMON_END, COMMON_START, DISTINCT_REPORTS, restrict
from analyze_a1_momentum_market_day_coverage_search import (
    dedupe_portfolio,
    load_csv_variants,
    load_synthetic_business_packages,
)
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_POSITION_SIZING_DIAGNOSTIC_2026_07_03"

BASE_SOURCES = [
    "residual_plus75_high_net",
    "v6_freq_v4_rr0p7_max2",
    "freq_h1_h4_long_rr0p7_v4_combo_rank1",
]
DISTINCT_ADDON = "v9_sweep_h1_long_rr0p6"
RR_RE = re.compile(r"rr(\d+)p(\d+)", re.IGNORECASE)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def rr_from_row(row: dict[str, Any]) -> tuple[float, str]:
    source = str(row.get("portfolio_member") or row.get("variant") or "")
    match = RR_RE.search(source)
    if not match:
        return 0.70, "fallback_rr0p70"
    rr = float(f"{int(match.group(1))}.{match.group(2)}")
    return rr, source


def r_profit(row: dict[str, Any]) -> float:
    profit = float(row.get("profit", 0.0) or 0.0)
    if profit > 0:
        rr, _source = rr_from_row(row)
        return rr
    if profit < 0:
        return -1.0
    return 0.0


def pf(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


def top_removed(values: list[float], count: int) -> float:
    ordered = sorted(values, reverse=True)
    return round(sum(values) - sum(ordered[:count]), 2)


def row_group(row: dict[str, Any]) -> str:
    return str(row.get("portfolio_member") or row.get("variant") or "unknown")


def summarize_book(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    deduped, duplicate_drops = dedupe_portfolio(rows)
    usd_summary = summarize(name, deduped)
    r_values = [r_profit(row) for row in deduped]
    profits = [float(row.get("profit", 0.0) or 0.0) for row in deduped]
    wins = sum(1 for value in profits if value > 0)
    rr_sources: dict[str, int] = {}
    for row in deduped:
        _rr, source = rr_from_row(row)
        rr_sources[source] = rr_sources.get(source, 0) + 1
    usd_summary.update(
        {
            "duplicate_drops": duplicate_drops,
            "net_r_fixed_risk": round(sum(r_values), 2),
            "profit_factor_r_fixed_risk": pf(r_values),
            "win_rate_r_basis_pct": round(100.0 * wins / len(deduped), 2) if deduped else 0.0,
            "top100_removed_r": top_removed(r_values, 100),
            "top200_removed_r": top_removed(r_values, 200),
            "top300_removed_r": top_removed(r_values, 300),
            "top100_removed_usd": top_removed(profits, 100),
            "top200_removed_usd": top_removed(profits, 200),
            "top300_removed_usd": top_removed(profits, 300),
            "rr_source_counts": rr_sources,
        }
    )
    return usd_summary


def group_breakdown(rows: list[dict[str, Any]], group_field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if group_field == "source":
            key = row_group(row)
        else:
            key = str(row.get(group_field) or "")
        grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key, group_rows in sorted(grouped.items()):
        deduped, _drops = dedupe_portfolio(group_rows)
        profits = [float(row.get("profit", 0.0) or 0.0) for row in deduped]
        r_values = [r_profit(row) for row in deduped]
        wins = sum(1 for value in profits if value > 0)
        losses = sum(1 for value in profits if value < 0)
        output.append(
            {
                "group_field": group_field,
                "group": key,
                "trades": len(deduped),
                "wins": wins,
                "losses": losses,
                "win_rate_pct": round(100.0 * wins / len(deduped), 2) if deduped else 0.0,
                "net_usd": round(sum(profits), 2),
                "pf_usd": pf(profits),
                "net_r_fixed_risk": round(sum(r_values), 2),
                "pf_r_fixed_risk": pf(r_values),
                "top100_removed_usd": top_removed(profits, min(100, len(profits))),
                "top100_removed_r": top_removed(r_values, min(100, len(r_values))),
            }
        )
    output.sort(key=lambda item: (item["net_usd"], item["net_r_fixed_risk"]), reverse=True)
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "book",
        "group_field",
        "group",
        "trades",
        "wins",
        "losses",
        "win_rate_pct",
        "net_usd",
        "pf_usd",
        "net_r_fixed_risk",
        "pf_r_fixed_risk",
        "top100_removed_usd",
        "top100_removed_r",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    books = payload["books"]
    lines = [
        "# A1 XAU M5 Momentum Position-Sizing Diagnostic - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline analysis only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Purpose",
        "",
        "The causal coverage and distinct-family searches can reach the owner's trade-frequency and win-rate target, but they fail large-winner robustness. This diagnostic asks whether that failure is mostly fixed-lot sizing/high-volatility trade concentration or a weaker entry edge.",
        "",
        "The fixed-risk R view is approximate because the exported MT5 trade CSVs do not contain original SL distance. R is inferred from the variant name (`rr0p6`, `rr0p7`, etc.); losses are counted as `-1R`, wins as the declared target R.",
        "",
        "## Book Comparison",
        "",
        "| Book | Trades | WR | USD PF | USD Net | USD Top300 Removed | Fixed-R PF | Fixed-R Net | Fixed-R Top300 Removed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for book in books:
        lines.append(
            f"| `{book['name']}` | {book['trades']} | {book['win_rate_pct']}% | {book['profit_factor']} | {book['net_usd']} | {book['top300_removed_usd']} | {book['profit_factor_r_fixed_risk']} | {book['net_r_fixed_risk']} | {book['top300_removed_r']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Sizing diagnosis: `{payload['sizing_diagnosis']}`",
            f"- Next action: `{payload['next_action']}`",
            "",
            "If fixed-risk R is still weak after top-winner removal, position sizing alone will not solve the problem. If fixed-risk R survives while USD fails, the next repair should be fixed-risk sizing or volatility-scaled lots rather than another entry filter.",
            "",
            "## Top Group Breakdowns",
            "",
            "| Book | Group Field | Group | Trades | WR | USD PF | USD Net | Fixed-R PF | Fixed-R Net |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["breakdowns"][:30]:
        lines.append(
            f"| `{row['book']}` | `{row['group_field']}` | `{row['group']}` | {row['trades']} | {row['win_rate_pct']}% | {row['pf_usd']} | {row['net_usd']} | {row['pf_r_fixed_risk']} | {row['net_r_fixed_risk']} |"
        )
    lines.extend(
        [
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
    distinct_variants = load_variants(DISTINCT_REPORTS)
    addon_item = distinct_variants.get(DISTINCT_ADDON)
    addon = addon_item["trades"] if addon_item else []
    if not addon:
        raise RuntimeError(f"missing addon variant: {DISTINCT_ADDON}")
    books = [
        ("robust_base", restrict(base_rows)),
        ("robust_base_plus_sweep_reclaim", restrict(base_rows + addon)),
    ]
    summaries: list[dict[str, Any]] = []
    breakdowns: list[dict[str, Any]] = []
    for name, rows in books:
        summary = summarize_book(name, rows)
        summaries.append(summary)
        for field in ("source", "direction", "entry_session"):
            for row in group_breakdown(rows, field):
                row["book"] = name
                breakdowns.append(row)
    best = summaries[-1] if summaries else {}
    sizing_diagnosis = (
        "ENTRY_EDGE_STILL_WEAK_AFTER_R_NORMALIZATION"
        if best.get("top300_removed_r", 0.0) <= 0
        else "FIXED_LOT_VOLATILITY_CONCENTRATION_IS_PRIMARY"
    )
    next_action = (
        "design_new_entry_or_reduce_weak_groups"
        if sizing_diagnosis == "ENTRY_EDGE_STILL_WEAK_AFTER_R_NORMALIZATION"
        else "test_fixed_risk_or_volatility_scaled_lot_model"
    )
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "PASS_POSITION_SIZING_DIAGNOSTIC_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_analysis_only_no_runtime_change",
        "window": f"{COMMON_START.date()} -> {COMMON_END.date()}",
        "books": summaries,
        "breakdowns": sorted(
            breakdowns,
            key=lambda item: (item["book"], item["group_field"], item["net_usd"]),
            reverse=True,
        ),
        "sizing_diagnosis": sizing_diagnosis,
        "next_action": next_action,
        "json": rel(output_json),
        "csv": rel(output_csv),
        "report": rel(output_md),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(output_csv, payload["breakdowns"])
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "sizing_diagnosis": sizing_diagnosis,
                "next_action": next_action,
                "books": [
                    {
                        "name": row["name"],
                        "trades": row["trades"],
                        "win_rate_pct": row["win_rate_pct"],
                        "usd_pf": row["profit_factor"],
                        "usd_net": row["net_usd"],
                        "usd_top300": row["top300_removed_usd"],
                        "r_pf": row["profit_factor_r_fixed_risk"],
                        "r_net": row["net_r_fixed_risk"],
                        "r_top300": row["top300_removed_r"],
                    }
                    for row in summaries
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
