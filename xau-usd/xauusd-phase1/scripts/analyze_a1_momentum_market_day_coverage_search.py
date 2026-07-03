from __future__ import annotations

import csv
import itertools
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_state_guard_search import apply_state_guard, top_removed_usd
from analyze_a1_momentum_feature_band_reliability_residual_search import enrich_base_trades
from analyze_a1_momentum_feature_band_residual_package_optimizer import residual_raw_trades
from analyze_a1_momentum_portfolio_combinations import read_trades, summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_MARKET_DAY_COVERAGE_SEARCH_CAUSAL_2026_07_03"

SOURCE_REPORTS = [
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FEATURE_PAIR_BAND_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_COMBO_BASE_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_DIRECTION_REPAIR_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_SHORT_V1_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_ALT_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_DIRECTIONAL_MASK_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V2_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V3_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V4_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V5_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V6_MAX2_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_WEAK_HOUR_V1_FOUR_YEAR_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V4_LOCK06_FOUR_YEAR_USD_2022_07_2026_06.json",
    "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V4_ROBUST_FOUR_YEAR_USD_2022_07_2026_06.json",
]

GUARD_SCENARIOS = [
    {
        "name": "no_daily_guard",
        "profit_target_usd": None,
        "loss_stop_usd": None,
        "max_trades_per_day": None,
        "max_losses_per_day": None,
        "cooldown_after_loss_minutes": 0,
        "early_trade_count": 2,
        "early_pnl_threshold": 0.0,
    },
    {
        "name": "target75_cooldown10",
        "profit_target_usd": 75.0,
        "loss_stop_usd": None,
        "max_trades_per_day": None,
        "max_losses_per_day": None,
        "cooldown_after_loss_minutes": 10,
        "early_trade_count": 2,
        "early_pnl_threshold": 0.0,
    },
    {
        "name": "target50_max8_cooldown10",
        "profit_target_usd": 50.0,
        "loss_stop_usd": None,
        "max_trades_per_day": 8,
        "max_losses_per_day": None,
        "cooldown_after_loss_minutes": 10,
        "early_trade_count": 2,
        "early_pnl_threshold": 0.0,
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def parse_entry_date(row: dict[str, Any]) -> date:
    value = row.get("entry_date")
    if value:
        return date.fromisoformat(str(value))
    entry_time = row.get("entry_time")
    if isinstance(entry_time, datetime):
        return entry_time.date()
    return datetime.strptime(str(entry_time), "%Y.%m.%d %H:%M:%S").date()


def market_days(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def day_distribution(trades: list[dict[str, Any]], all_market_days: list[date]) -> dict[str, Any]:
    by_day: dict[date, list[float]] = defaultdict(list)
    for row in trades:
        by_day[parse_entry_date(row)].append(float(row.get("profit", 0.0)))
    total_days = len(all_market_days)
    active_days = len(by_day)
    one_plus_days = active_days
    two_plus_days = sum(1 for values in by_day.values() if len(values) >= 2)
    three_plus_days = sum(1 for values in by_day.values() if len(values) >= 3)
    four_plus_days = sum(1 for values in by_day.values() if len(values) >= 4)
    positive_active_days = sum(1 for values in by_day.values() if sum(values) > 0)
    return {
        "market_days": total_days,
        "active_days": active_days,
        "trades_per_market_day": round(len(trades) / total_days, 2) if total_days else 0.0,
        "trades_per_active_day": round(len(trades) / active_days, 2) if active_days else 0.0,
        "active_market_day_pct": round(100.0 * one_plus_days / total_days, 2) if total_days else 0.0,
        "two_plus_market_day_pct": round(100.0 * two_plus_days / total_days, 2) if total_days else 0.0,
        "three_plus_market_day_pct": round(100.0 * three_plus_days / total_days, 2) if total_days else 0.0,
        "four_plus_market_day_pct": round(100.0 * four_plus_days / total_days, 2) if total_days else 0.0,
        "three_plus_active_day_pct": round(100.0 * three_plus_days / active_days, 2) if active_days else 0.0,
        "positive_active_day_pct": round(100.0 * positive_active_days / active_days, 2) if active_days else 0.0,
    }


def date_window(trades: list[dict[str, Any]]) -> tuple[date, date, list[date]]:
    dates = [parse_entry_date(row) for row in trades]
    start = min(dates)
    end = max(dates)
    return start, end, market_days(start, end)


def report_slug(path: Path) -> str:
    name = path.stem
    for token in (
        "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_",
        "_FOUR_YEAR_2022_07_2026_06",
        "_2022_07_2026_06",
    ):
        name = name.replace(token, "")
    return name.lower()


def load_csv_variants() -> dict[str, list[dict[str, Any]]]:
    variants: dict[str, list[dict[str, Any]]] = {}
    for filename in SOURCE_REPORTS:
        report_path = REPORTS_DIR / filename
        if not report_path.exists():
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        slug = report_slug(report_path)
        for item in report.get("variants", []):
            name = str(item.get("name", ""))
            trade_csv = item.get("trade_csv")
            if not name or not trade_csv:
                continue
            path = Path(trade_csv)
            if not path.exists():
                continue
            key = name
            if key in variants:
                key = f"{name}__{slug}"
            variants[key] = read_trades(path, key)
    return variants


def load_synthetic_business_packages() -> dict[str, list[dict[str, Any]]]:
    base = enrich_base_trades()
    residual_raw, _blocked = residual_raw_trades(base)
    packages: dict[str, list[dict[str, Any]]] = {}
    for scenario in GUARD_SCENARIOS[1:]:
        selected, _stats = apply_state_guard(
            residual_raw,
            state_rule="none",
            profit_target_usd=scenario["profit_target_usd"],
            loss_stop_usd=scenario["loss_stop_usd"],
            max_trades_per_day=scenario["max_trades_per_day"],
            max_losses_per_day=scenario["max_losses_per_day"],
            cooldown_after_loss_minutes=scenario["cooldown_after_loss_minutes"],
            early_trade_count=scenario["early_trade_count"],
            early_pnl_threshold=scenario["early_pnl_threshold"],
        )
        name = "residual_plus75_high_net" if scenario["name"] == "target75_cooldown10" else "residual_plus50_10m"
        packages[name] = [dict(row, variant=name) for row in selected]
    return packages


def dedupe_portfolio(trades: list[dict[str, Any]], window_minutes: int = 5) -> tuple[list[dict[str, Any]], int]:
    ordered = sorted(trades, key=lambda row: (row["entry_time"], row["variant"], row["direction"]))
    kept: list[dict[str, Any]] = []
    dropped = 0
    max_seconds = window_minutes * 60
    for row in ordered:
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


def individual_quality(summary: dict[str, Any]) -> bool:
    return (
        summary["trades"] >= 300
        and summary["net_usd"] > 0
        and summary["win_rate_pct"] >= 50.0
        and (summary["profit_factor"] or 0.0) >= 1.10
    )


def quality_score(summary: dict[str, Any]) -> float:
    return round(
        summary["net_usd"]
        + 140.0 * summary["trades_per_market_day"]
        + 12.0 * summary["win_rate_pct"]
        + 80.0 * ((summary["profit_factor"] or 0.0) - 1.0)
        + 6.0 * summary["three_plus_market_day_pct"]
        - 0.12 * summary["max_closed_drawdown_usd"],
        2,
    )


def decision(row: dict[str, Any]) -> str:
    if row["trades"] < 1000:
        return "FAIL_SAMPLE"
    if row["net_usd"] <= 0 or (row["profit_factor"] or 0.0) < 1.20:
        return "FAIL_QUALITY"
    if row["win_rate_pct"] < 50.0:
        return "FAIL_WIN_RATE"
    if row["top100_removed_usd"] <= 0:
        return "FAIL_TOP100_ROBUSTNESS"
    if row["top200_removed_usd"] <= 0:
        return "FAIL_TOP200_ROBUSTNESS"
    if row["trades_per_market_day"] < 2.0:
        return "FAIL_MARKET_DAY_CADENCE"
    if row["three_plus_market_day_pct"] < 35.0:
        return "REVIEW_CANDIDATE_WITH_3PLUS_CAVEAT"
    if row["trades_per_market_day"] < 3.0:
        return "REVIEW_CANDIDATE_WITH_MARKET_DAY_CAVEAT"
    return "REVIEW_CANDIDATE_OWNER_CADENCE"


def evaluate(name: str, raw_trades: list[dict[str, Any]], guard: dict[str, Any]) -> dict[str, Any]:
    deduped, duplicate_drops = dedupe_portfolio(raw_trades)
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
    if not selected:
        return {}
    start, end, all_market_days = date_window(selected)
    summary = summarize(f"{name}|{guard['name']}", selected)
    summary.update(day_distribution(selected, all_market_days))
    summary.update(
        {
            "portfolio_name": name,
            "guard_name": guard["name"],
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "source_variants": sorted({row["variant"] for row in raw_trades}),
            "source_variant_count": len({row["variant"] for row in raw_trades}),
            "raw_combined_trades": len(raw_trades),
            "deduped_trades_before_guard": len(deduped),
            "duplicate_drops": duplicate_drops,
            "duplicate_drop_pct": round(100.0 * duplicate_drops / len(raw_trades), 2) if raw_trades else 0.0,
            "top100_removed_usd": top_removed_usd(selected, 100),
            "top200_removed_usd": top_removed_usd(selected, 200),
        }
    )
    summary.update(guard_stats)
    summary["decision"] = decision(summary)
    summary["score"] = quality_score(summary)
    return summary


def guard_by_name(name: str) -> dict[str, Any]:
    for guard in GUARD_SCENARIOS:
        if guard["name"] == name:
            return guard
    raise ValueError(f"unknown guard: {name}")


def traced_guard_rows(raw_trades: list[dict[str, Any]], guard: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    deduped, _duplicate_drops = dedupe_portfolio(raw_trades)
    traced: list[dict[str, Any]] = []
    for index, row in enumerate(deduped, start=1):
        copied = dict(row)
        copied["coverage_trace_id"] = f"T{index:06d}"
        traced.append(copied)
    selected, guard_stats = apply_state_guard(
        traced,
        state_rule="none",
        profit_target_usd=guard["profit_target_usd"],
        loss_stop_usd=guard["loss_stop_usd"],
        max_trades_per_day=guard["max_trades_per_day"],
        max_losses_per_day=guard["max_losses_per_day"],
        cooldown_after_loss_minutes=guard["cooldown_after_loss_minutes"],
        early_trade_count=guard["early_trade_count"],
        early_pnl_threshold=guard["early_pnl_threshold"],
    )
    selected_ids = {row["coverage_trace_id"] for row in selected}
    rows: list[dict[str, Any]] = []
    for row in traced:
        decision_label = "kept" if row["coverage_trace_id"] in selected_ids else "dropped_by_guard"
        rows.append(
            {
                "coverage_trace_id": row["coverage_trace_id"],
                "guard_decision": decision_label,
                "variant": row.get("variant", ""),
                "entry_time": row["entry_time"].strftime("%Y.%m.%d %H:%M:%S"),
                "exit_time": row["exit_time"].strftime("%Y.%m.%d %H:%M:%S"),
                "entry_date": row.get("entry_date", ""),
                "entry_hour": row.get("entry_hour", ""),
                "entry_session": row.get("entry_session", ""),
                "direction": row.get("direction", ""),
                "profit": row.get("profit", 0.0),
                "entry_price": row.get("entry_price", ""),
                "exit_price": row.get("exit_price", ""),
                "exit_comment": row.get("exit_comment", ""),
            }
        )
    return rows, guard_stats


def write_kept_dropped_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "coverage_trace_id",
        "guard_decision",
        "variant",
        "entry_time",
        "exit_time",
        "entry_date",
        "entry_hour",
        "entry_session",
        "direction",
        "profit",
        "entry_price",
        "exit_price",
        "exit_comment",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_candidate_pool(variants: dict[str, list[dict[str, Any]]]) -> list[tuple[str, list[dict[str, Any]], dict[str, Any]]]:
    pool: list[tuple[str, list[dict[str, Any]], dict[str, Any]]] = []
    for name, trades in variants.items():
        summary = evaluate(name, trades, GUARD_SCENARIOS[0])
        if summary and individual_quality(summary):
            pool.append((name, trades, summary))
    pool.sort(key=lambda item: (-item[2]["score"], -item[2]["net_usd"], -item[2]["trades"]))
    return pool


def search_portfolios(variants: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    pool = build_candidate_pool(variants)
    selected_pool = pool[:14]
    results: list[dict[str, Any]] = []

    for name, trades, _summary in selected_pool:
        for guard in GUARD_SCENARIOS:
            results.append(evaluate(name, trades, guard))

    combo_pools = {
        2: selected_pool[:14],
        3: selected_pool[:14],
        4: selected_pool[:12],
    }
    for combo_size, combo_pool in combo_pools.items():
        for combo in itertools.combinations(combo_pool, combo_size):
            names = [item[0] for item in combo]
            raw_trades: list[dict[str, Any]] = []
            for _name, trades, _summary in combo:
                raw_trades.extend(trades)
            portfolio_name = " + ".join(names)
            for guard in GUARD_SCENARIOS:
                results.append(evaluate(portfolio_name, raw_trades, guard))

    filtered = [row for row in results if row]
    filtered.sort(
        key=lambda row: (
            row["decision"].startswith("FAIL"),
            -row["score"],
            -row["trades_per_market_day"],
            -row["net_usd"],
        )
    )
    return filtered


def render(payload: dict[str, Any]) -> str:
    top = payload["top_results"][:15]
    lines = [
        "# A1 XAU M5 Momentum Market-Day Coverage Search - 2026-07-02",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 terminal, chart, preset, order, or position was touched.",
        "",
        "Guard model: `event_time_causal_v2`. Daily PnL targets, cooldowns, loss counts, and state stops are updated only after a kept trade's exit time is reached. This replaces the rejected entry-ordered guard model that could react to outcomes before they were knowable.",
        "",
        "## Why This Exists",
        "",
        "The owner clarified that the target is not a low-frequency strategy with pretty statistics. The business requirement is multiple intraday trades, ideally every trading day, while keeping win rate above 50% and net/PF positive.",
        "",
        "This search tests whether existing momentum lanes can be combined as a deduped portfolio to improve market-day coverage without reintroducing duplicate stacking.",
        "",
        "## Search Rules",
        "",
        "- Inputs: exact MT5 Strategy Tester trade CSVs from existing four-year A1 XAU M5 momentum reports, plus the current residual +75/+50 business packages.",
        "- Duplicate control: one same-direction signal within a 5-minute window is kept; later same-direction duplicates are dropped.",
        "- Daily overlays tested: no guard, +75 target with 10m loss cooldown, +50 target with max eight trades/day and 10m loss cooldown.",
        "- Guard causality: guard state only changes on trade exits that have occurred before the next candidate entry.",
        "- Promotion-shaped gate: WR >= 50%, PF >= 1.20, top100/top200 removed remain positive, and at least 2 trades per weekday market day.",
        "",
        "## Best Results",
        "",
        "| Rank | Decision | Portfolio | Guard | Trades | WR | PF | Net | T/market day | T/active day | Active days | 3+ market days | Pos active days | Top100 removed | Top200 removed | Dup drops |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(top, start=1):
        lines.append(
            "| {rank} | `{decision}` | `{portfolio}` | `{guard}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tpmd:.2f} | {tpad:.2f} | {active:.2f}% | {three:.2f}% | {positive:.2f}% | {top100:.2f} | {top200:.2f} | {dups} |".format(
                rank=index,
                decision=row["decision"],
                portfolio=row["portfolio_name"][:90],
                guard=row["guard_name"],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                pf=row["profit_factor"],
                net=row["net_usd"],
                tpmd=row["trades_per_market_day"],
                tpad=row["trades_per_active_day"],
                active=row["active_market_day_pct"],
                three=row["three_plus_market_day_pct"],
                positive=row["positive_active_day_pct"],
                top100=row["top100_removed_usd"],
                top200=row["top200_removed_usd"],
                dups=row["duplicate_drops"],
            )
        )
    best = payload.get("best_result", {})
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Best current answer: `{best.get('portfolio_name', '')}` with guard `{best.get('guard_name', '')}`.",
            f"- It averages `{best.get('trades_per_market_day', 0.0)}` trades per weekday market day and `{best.get('trades_per_active_day', 0.0)}` trades per active day.",
            f"- It reaches 3+ trades on `{best.get('three_plus_market_day_pct', 0.0)}%` of weekday market days.",
            "- This is closer to the owner's multiple-trades/day vision than sparse RR2-style systems, but it still does not guarantee 3+ trades every market day.",
            "- If the owner wants truly every-day activity, the honest next step is not loosening this candidate blindly; it is either adding a genuinely complementary entry family or accepting lower quality.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Report: `{payload['report']}`",
            f"- Best kept/dropped audit CSV: `{payload.get('best_kept_dropped_csv', '')}`",
        ]
    )
    return "\n".join(lines) + "\n"


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
        "max_closed_drawdown_usd",
        "duplicate_drops",
        "duplicate_drop_pct",
        "source_variant_count",
        "score",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def main() -> int:
    csv_variants = load_csv_variants()
    synthetic_packages = load_synthetic_business_packages()
    variants = {**csv_variants, **synthetic_packages}
    results = search_portfolios(variants)
    reviewable = [row for row in results if not row["decision"].startswith("FAIL")]
    best = reviewable[0] if reviewable else (results[0] if results else {})

    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_kept_dropped = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT_DROPPED.csv"
    kept_dropped_rows: list[dict[str, Any]] = []
    kept_dropped_stats: dict[str, Any] = {}
    if best:
        best_raw_trades: list[dict[str, Any]] = []
        for variant_name in best.get("source_variants", []):
            best_raw_trades.extend(variants.get(variant_name, []))
        kept_dropped_rows, kept_dropped_stats = traced_guard_rows(best_raw_trades, guard_by_name(best["guard_name"]))
        write_kept_dropped_csv(output_kept_dropped, kept_dropped_rows)
    payload = {
        "status": "PASS_COVERAGE_SEARCH_READY" if results else "FAIL_NO_RESULTS",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change_event_time_causal_guard",
        "guard_model": "event_time_causal_v2",
        "source_reports": [rel(REPORTS_DIR / filename) for filename in SOURCE_REPORTS],
        "loaded_csv_variant_count": len(csv_variants),
        "loaded_synthetic_package_count": len(synthetic_packages),
        "searched_result_count": len(results),
        "reviewable_result_count": len(reviewable),
        "best_result": best,
        "top_results": results[:50],
        "best_kept_dropped_csv": rel(output_kept_dropped) if kept_dropped_rows else "",
        "best_kept_dropped_stats": kept_dropped_stats,
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(output_csv, results[:100])
    print(output_md)
    if best:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "best": best["portfolio_name"],
                    "decision": best["decision"],
                    "trades_per_market_day": best["trades_per_market_day"],
                    "three_plus_market_day_pct": best["three_plus_market_day_pct"],
                    "win_rate_pct": best["win_rate_pct"],
                    "profit_factor": best["profit_factor"],
                    "net_usd": best["net_usd"],
                },
                indent=2,
            )
        )
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
