from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import load_variants
from analyze_a1_momentum_causal_robust_coverage_search import reconstruct
from analyze_a1_momentum_daily_state_guard_search import top_removed_usd
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
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_DISTINCT_FAMILY_COMPANION_SEARCH_2026_07_03"

COMMON_START = datetime(2024, 7, 1)
COMMON_END = datetime(2026, 6, 30, 23, 59, 59)
BASE_SOURCES = [
    "residual_plus75_high_net",
    "v6_freq_v4_rr0p7_max2",
    "freq_h1_h4_long_rr0p7_v4_combo_rank1",
]
BASE_GUARD = "no_daily_guard"
DISTINCT_REPORTS = [
    REPORTS_DIR / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V7_PULLBACK_TWO_YEAR_2024_07_2026_06.json",
    REPORTS_DIR / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V8_COMPRESSION_TWO_YEAR_2024_07_2026_06.json",
    REPORTS_DIR / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V9_SWEEP_RECLAIM_TWO_YEAR_2024_07_2026_06.json",
    REPORTS_DIR / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V10_OPENING_RANGE_TWO_YEAR_2024_07_2026_06.json",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def in_window(row: dict[str, Any]) -> bool:
    return COMMON_START <= row["entry_time"] <= COMMON_END


def restrict(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if in_window(row)]


def family(name: str) -> str:
    if name.startswith("v7_"):
        return "pullback"
    if name.startswith("v8_"):
        return "compression"
    if name.startswith("v9_"):
        return "sweep_reclaim"
    if name.startswith("v10_"):
        return "opening_range"
    return "control_or_other"


def quiet_day_addon(base: list[dict[str, Any]], addon: list[dict[str, Any]], max_base_count: int) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in base:
        day = str(row.get("entry_date", ""))
        counts[day] = counts.get(day, 0) + 1
    return [row for row in addon if counts.get(str(row.get("entry_date", "")), 0) < max_base_count]


def metrics(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    deduped, duplicate_drops = dedupe_portfolio(rows)
    if not deduped:
        return {}
    start, end, market_days = date_window(deduped)
    summary = summarize(name, deduped)
    summary.update(day_distribution(deduped, market_days))
    half = grouped_stats(deduped, "half_year")
    quarter = grouped_stats(deduped, "quarter")
    r250 = rolling_stats(deduped, 250)
    r500 = rolling_stats(deduped, 500)
    summary.update(
        {
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "duplicate_drops": duplicate_drops,
            "top100_removed_usd": top_removed_usd(deduped, 100),
            "top200_removed_usd": top_removed_usd(deduped, 200),
            "top300_removed_usd": top_removed_usd(deduped, 300),
            "negative_half_years": sum(1 for row in half if row["net_usd"] <= 0),
            "negative_quarters": sum(1 for row in quarter if row["net_usd"] <= 0),
            "rolling_250_negative": r250.get("negative_windows", 0),
            "rolling_250_pf_below_1": r250.get("pf_below_1_windows", 0),
            "rolling_500_negative": r500.get("negative_windows", 0),
            "rolling_500_pf_below_1": r500.get("pf_below_1_windows", 0),
        }
    )
    return summary


def decide(row: dict[str, Any]) -> str:
    if row["trades"] < 1000:
        return "FAIL_SAMPLE"
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_CADENCE"
    if row["win_rate_pct"] < 60.0 or (row["profit_factor"] or 0.0) < 1.25:
        return "FAIL_QUALITY"
    if row["top200_removed_usd"] <= 0:
        return "FAIL_TOP200"
    if row["negative_half_years"] > 0 or row["negative_quarters"] > 3:
        return "FAIL_STABILITY"
    if row["rolling_500_negative"] > 0:
        return "FAIL_500_ROLLING"
    if row["top300_removed_usd"] <= 0 or row["rolling_250_negative"] > 0:
        return "REVISE_ROBUSTNESS"
    return "REVIEW_DISTINCT_FAMILY_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    bonus = {
        "REVIEW_DISTINCT_FAMILY_CANDIDATE": 1500.0,
        "REVISE_ROBUSTNESS": 500.0,
    }.get(row.get("decision", ""), 0.0)
    return round(
        bonus
        + float(row.get("net_usd") or 0.0)
        + 100.0 * float(row.get("trades_per_market_day") or 0.0)
        + 12.0 * float(row.get("win_rate_pct") or 0.0)
        + 160.0 * ((float(row.get("profit_factor") or 0.0)) - 1.0)
        + 0.4 * float(row.get("top300_removed_usd") or 0.0)
        - 0.8 * float(row.get("rolling_250_negative") or 0.0),
        2,
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "addon_family",
        "addon_name",
        "mode",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net_usd",
        "trades_per_market_day",
        "three_plus_market_day_pct",
        "top100_removed_usd",
        "top200_removed_usd",
        "top300_removed_usd",
        "negative_half_years",
        "negative_quarters",
        "rolling_250_negative",
        "rolling_500_negative",
        "duplicate_drops",
        "score",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    base = payload.get("base", {})
    best = payload.get("best_result", {})
    lines = [
        "# A1 XAU M5 Momentum Distinct-Family Companion Search - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Purpose",
        "",
        "The momentum-family quiet-day repair still failed strong robustness. This search tests already MT5-tested distinct signal families as companions over their common two-year window: pullback, compression, sweep-reclaim, and opening-range.",
        "",
        "## Base Window",
        "",
        f"- Common window: `{payload['common_window']}`",
        f"- Base sources: `{', '.join(BASE_SOURCES)}`",
        f"- Base metrics: `{base.get('trades')} trades / WR {base.get('win_rate_pct')}% / PF {base.get('profit_factor')} / {base.get('trades_per_market_day')} trades per market day / top300 {base.get('top300_removed_usd')}`",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision', '')}` |",
        f"| Mode | `{best.get('mode', '')}` |",
        f"| Addon family | `{best.get('addon_family', '')}` |",
        f"| Addon | `{best.get('addon_name', '')}` |",
        f"| Trades | {best.get('trades', 'n/a')} |",
        f"| Win rate | {best.get('win_rate_pct', 'n/a')}% |",
        f"| PF | {best.get('profit_factor', 'n/a')} |",
        f"| Net | {best.get('net_usd', 'n/a')} USD |",
        f"| Trades / market day | {best.get('trades_per_market_day', 'n/a')} |",
        f"| Top300 removed | {best.get('top300_removed_usd', 'n/a')} USD |",
        f"| Negative 250 windows | {best.get('rolling_250_negative', 'n/a')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Mode | Family | Addon | Trades | WR | PF | Net | T/market day | Top300 | 250-neg |",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload.get("top_results", [])[:20], start=1):
        lines.append(
            f"| {index} | `{row.get('decision', '')}` | `{row.get('mode', '')}` | `{row.get('addon_family', '')}` | `{str(row.get('addon_name', ''))[:70]}` | {row.get('trades', '')} | {row.get('win_rate_pct', '')}% | {row.get('profit_factor', '')} | {row.get('net_usd', '')} | {row.get('trades_per_market_day', '')} | {row.get('top300_removed_usd', '')} | {row.get('rolling_250_negative', '')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a direct test of genuinely different mechanisms already implemented in the EA/backtester.",
            "- If the top rows still fail, the existing distinct families are not enough; the next new EA should be a new mechanism, not more portfolio mixing.",
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
    base_variants = {**load_csv_variants(), **load_synthetic_business_packages()}
    base_rows, _guard_stats, _dups, missing = reconstruct(base_variants, BASE_SOURCES, BASE_GUARD)
    if missing:
        raise RuntimeError(f"missing base variants: {missing}")
    base_rows = restrict(base_rows)
    base_summary = metrics("base", base_rows)

    distinct = load_variants(DISTINCT_REPORTS)
    rows: list[dict[str, Any]] = []
    for name, item in sorted(distinct.items()):
        if name.startswith("freq_h1_h4_long_rr0p7_v4"):
            continue
        addon_rows = restrict(item["trades"])
        if len(addon_rows) < 100:
            continue
        for mode, addon in {
            "all_addon": addon_rows,
            "quiet_day_addon": quiet_day_addon(base_rows, addon_rows, max_base_count=3),
        }.items():
            if len(addon) < 50:
                continue
            summary = metrics(f"base + {mode}_{name}", base_rows + addon)
            if not summary:
                continue
            summary.update({"addon_name": name, "addon_family": family(name), "mode": mode})
            summary["decision"] = decide(summary)
            summary["score"] = score(summary)
            rows.append(summary)

    rows.sort(
        key=lambda row: (
            0 if row["decision"] == "REVIEW_DISTINCT_FAMILY_CANDIDATE" else 1 if row["decision"] == "REVISE_ROBUSTNESS" else 2,
            -row["score"],
            -float(row.get("trades_per_market_day") or 0.0),
        )
    )
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "PASS_DISTINCT_FAMILY_COMPANION_SEARCH_READY" if rows else "FAIL_NO_RESULTS",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "common_window": f"{COMMON_START.date()} -> {COMMON_END.date()}",
        "source_reports": [str(path) for path in DISTINCT_REPORTS],
        "base": base_summary,
        "candidate_count": len(rows),
        "best_result": rows[0] if rows else {},
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
                "best_decision": payload["best_result"].get("decision"),
                "mode": payload["best_result"].get("mode"),
                "family": payload["best_result"].get("addon_family"),
                "addon": payload["best_result"].get("addon_name"),
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
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
