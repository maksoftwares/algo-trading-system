from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_causal_robust_coverage_search import evaluate_candidate, reconstruct
from analyze_a1_momentum_daily_state_guard_search import top_removed_usd
from analyze_a1_momentum_market_day_coverage_search import (
    day_distribution,
    date_window,
    dedupe_portfolio,
    load_csv_variants,
    load_synthetic_business_packages,
)
from analyze_a1_momentum_market_day_coverage_stress import grouped_stats, rolling_stats
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
ROBUST_SEARCH_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_CAUSAL_ROBUST_COVERAGE_SEARCH_2026_07_03.json"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_QUIET_DAY_COMPANION_SEARCH_2026_07_03"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def load_robust_base() -> dict[str, Any]:
    payload = json.loads(ROBUST_SEARCH_JSON.read_text(encoding="utf-8"))
    for row in payload.get("top_results", []):
        if (
            row.get("decision") == "FAIL_OWNER_CADENCE"
            and row.get("rolling_250_negative", 999) == 0
            and (row.get("profit_factor") or 0.0) >= 1.35
            and row.get("trades_per_market_day", 0.0) >= 2.4
        ):
            return row
    raise RuntimeError("no robust low-cadence base found")


def market_day_counts(trades: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in trades:
        counts[str(row.get("entry_date", ""))] += 1
    return counts


def quiet_day_addon(base: list[dict[str, Any]], addon: list[dict[str, Any]], max_base_count: int) -> list[dict[str, Any]]:
    counts = market_day_counts(base)
    return [row for row in addon if counts.get(str(row.get("entry_date", "")), 0) < max_base_count]


def evaluate_trades(name: str, trades: list[dict[str, Any]], *, addon_name: str, base_name: str) -> dict[str, Any]:
    deduped, duplicate_drops = dedupe_portfolio(trades)
    if not deduped:
        return {}
    start, end, market_days = date_window(deduped)
    summary = summarize(name, deduped)
    summary.update(day_distribution(deduped, market_days))
    half_year = grouped_stats(deduped, "half_year")
    quarter = grouped_stats(deduped, "quarter")
    rolling_250 = rolling_stats(deduped, 250)
    rolling_500 = rolling_stats(deduped, 500)
    summary.update(
        {
            "addon_name": addon_name,
            "base_name": base_name,
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "duplicate_drops": duplicate_drops,
            "negative_half_years": sum(1 for row in half_year if row["net_usd"] <= 0),
            "negative_quarters": sum(1 for row in quarter if row["net_usd"] <= 0),
            "rolling_250_negative": rolling_250.get("negative_windows", 0),
            "rolling_250_pf_below_1": rolling_250.get("pf_below_1_windows", 0),
            "rolling_500_negative": rolling_500.get("negative_windows", 0),
            "rolling_500_pf_below_1": rolling_500.get("pf_below_1_windows", 0),
            "top100_removed_usd": top_removed_usd(deduped, 100),
            "top200_removed_usd": top_removed_usd(deduped, 200),
            "top300_removed_usd": top_removed_usd(deduped, 300),
        }
    )
    summary["decision"] = decide(summary)
    summary["score"] = score(summary)
    return summary


def decide(row: dict[str, Any]) -> str:
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_CADENCE_STILL_LOW"
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
    return "REVIEW_STRONG_QUIET_DAY_COMPANION"


def score(row: dict[str, Any]) -> float:
    bonus = {
        "REVIEW_STRONG_QUIET_DAY_COMPANION": 1200.0,
        "REVISE_ROBUSTNESS": 500.0,
    }.get(str(row.get("decision")), 0.0)
    return round(
        bonus
        + float(row.get("net_usd") or 0.0)
        + 100.0 * float(row.get("trades_per_market_day") or 0.0)
        + 12.0 * float(row.get("win_rate_pct") or 0.0)
        + 150.0 * ((float(row.get("profit_factor") or 0.0)) - 1.0)
        + 0.3 * float(row.get("top300_removed_usd") or 0.0)
        - 0.7 * float(row.get("rolling_250_negative") or 0.0)
        - 20.0 * float(row.get("negative_quarters") or 0.0),
        2,
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "base_name",
        "addon_name",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net_usd",
        "trades_per_market_day",
        "three_plus_market_day_pct",
        "positive_active_day_pct",
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
    best = payload.get("best_result", {})
    lines = [
        "# A1 XAU M5 Momentum Quiet-Day Companion Search - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Purpose",
        "",
        "The robust causal search found a stronger low-cadence base with no negative 250-trade rolling windows, but it failed the owner's cadence target. This search adds one companion only on days where the base has fewer than three trades, then retests quality and robustness.",
        "",
        "## Base",
        "",
        f"- Base candidate: `{payload.get('base_name', '')}`",
        f"- Base guard: `{payload.get('base_guard', '')}`",
        f"- Base metrics: `{payload.get('base_metrics', '')}`",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision', '')}` |",
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
        "| Rank | Decision | Addon | Trades | WR | PF | Net | T/market day | Top300 | 250-neg |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload.get("top_results", [])[:20], start=1):
        lines.append(
            f"| {index} | `{row.get('decision', '')}` | `{str(row.get('addon_name', ''))[:80]}` | {row.get('trades', '')} | {row.get('win_rate_pct', '')}% | {row.get('profit_factor', '')} | {row.get('net_usd', '')} | {row.get('trades_per_market_day', '')} | {row.get('top300_removed_usd', '')} | {row.get('rolling_250_negative', '')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This search tests the most natural repair: keep the robust base and fill quiet days only.",
            "- If no strong row appears, the current momentum-family combinations are probably near their limit and a genuinely different entry family is needed.",
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
    base_row = load_robust_base()
    base_selected, _stats, _dups, missing = reconstruct(
        variants,
        list(base_row.get("source_variants", [])),
        str(base_row.get("guard_name", "")),
    )
    if missing:
        raise RuntimeError(f"missing base sources: {missing}")
    base_source_set = set(base_row.get("source_variants", []))
    base_name = str(base_row.get("portfolio_name", ""))
    rows: list[dict[str, Any]] = []
    for addon_name, addon_rows in sorted(variants.items()):
        if addon_name in base_source_set:
            continue
        addon = quiet_day_addon(base_selected, addon_rows, max_base_count=3)
        if len(addon) < 100:
            continue
        result = evaluate_trades(
            f"{base_name} + quiet_day_{addon_name}",
            base_selected + addon,
            addon_name=addon_name,
            base_name=base_name,
        )
        if result:
            rows.append(result)
    rows.sort(
        key=lambda row: (
            0 if row["decision"] == "REVIEW_STRONG_QUIET_DAY_COMPANION" else 1 if row["decision"] == "REVISE_ROBUSTNESS" else 2,
            -row["score"],
            -float(row.get("trades_per_market_day") or 0.0),
        )
    )

    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "PASS_QUIET_DAY_COMPANION_SEARCH_READY" if rows else "FAIL_NO_RESULTS",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "base_name": base_name,
        "base_guard": base_row.get("guard_name", ""),
        "base_metrics": (
            f"{base_row.get('trades')} trades / WR {base_row.get('win_rate_pct')}% / "
            f"PF {base_row.get('profit_factor')} / {base_row.get('trades_per_market_day')} trades per market day"
        ),
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
