from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times, week_start
from analyze_a1_momentum_causal_robust_coverage_search import reconstruct
from analyze_a1_momentum_daily_state_guard_search import apply_state_guard
from analyze_a1_momentum_feature_band_reliability_residual_search import enrich_base_trades
from analyze_a1_momentum_feature_band_residual_package_optimizer import residual_raw_trades
from analyze_a1_momentum_market_day_coverage_search import (
    load_csv_variants,
    load_synthetic_business_packages,
)
from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    LAST12_START,
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    parse_dt,
    summary_metrics,
)
from run_a1_h4_d1_geometry_v2_weekly_shape import read_composition_csv, write_signal_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
OUTPUT_STEM = "A1_XAU_SMOOTH_SECOND_BOOK_WEEKLY_TARGET_DIAGNOSTIC_202207_202606"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
CAUSAL_SEARCH_JSON = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_CAUSAL_ROBUST_COVERAGE_SEARCH_2026_07_03.json"
START_DATE = date(2022, 7, 1)
END_DATE = date(2026, 6, 30)
TARGET_LOW = 70.0
TARGET_HIGH = 80.0
TARGET_ACTIVITY = 90.0
SECOND_BOOK_WEIGHT_SWEEP = [0.5, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def safe_key(value: str, max_len: int = 72) -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_").lower()
    return text[:max_len] or "unnamed"


def all_week_starts() -> list[date]:
    start = week_start(START_DATE)
    end = week_start(END_DATE)
    weeks: list[date] = []
    current = start
    while current <= end:
        weeks.append(current)
        current += timedelta(days=7)
    return weeks


ALL_WEEK_STARTS = all_week_starts()


def parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def maybe_parse_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return parse_dt(text)
    except Exception:
        return None


def ensure_exit_times(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ready: list[dict[str, Any]] = []
    needs_enrichment: list[dict[str, Any]] = []
    for row in rows:
        exit_time = maybe_parse_dt(row.get("exit_time"))
        if exit_time is None:
            needs_enrichment.append(row)
            continue
        item = dict(row)
        item["exit_time"] = exit_time
        item["exit_date"] = exit_time.date()
        item["exit_match_status"] = item.get("exit_match_status") or "prepopulated"
        ready.append(item)

    enriched: list[dict[str, Any]] = []
    stats: dict[str, Any] = {
        "prepopulated_exit_rows": len(ready),
        "enrichment_requested_rows": len(needs_enrichment),
    }
    if needs_enrichment:
        enriched, enrich_stats = enrich_exit_times(needs_enrichment)
        stats.update(enrich_stats)
    else:
        stats.update(
            {
                "source_csvs_indexed": 0,
                "missing_source_csvs": [],
                "match_failures": 0,
                "fallback_entry_time_rows": 0,
            }
        )
    return ready + enriched, stats


def normalize_baseline() -> list[dict[str, Any]]:
    rows = read_composition_csv(BASELINE_KEPT)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["entry_date"] = parse_date(item["entry_date"])
        item["pnl_usd"] = float(item.get("pnl_usd") or 0.0)
        item["tickets"] = int(item.get("tickets") or 1)
        item["source_priority"] = int(item.get("source_priority") or 0)
        item["source_row"] = int(item.get("source_row") or 0)
        normalized.append(item)
    return normalized


def normalize_momentum_trades(source_id: str, trades: list[dict[str, Any]], priority: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(trades, start=2):
        entry_time = maybe_parse_dt(row.get("entry_time"))
        if entry_time is None:
            continue
        entry_day = parse_date(row.get("entry_date") or entry_time.date().isoformat())
        if entry_day < START_DATE or entry_day > END_DATE:
            continue
        exit_time = maybe_parse_dt(row.get("exit_time")) or entry_time
        variant = str(row.get("variant") or source_id)
        rows.append(
            {
                "component": source_id,
                "source_id": source_id,
                "upstream_source_id": variant,
                "upstream_component": "smooth_second_book",
                "family_group": "smooth_second_book",
                "source_priority": priority,
                "cell_id": source_id,
                "component_priority": 0,
                "variant_name": variant,
                "entry_time": entry_time,
                "entry_date": entry_day,
                "exit_time": exit_time,
                "exit_date": exit_time.date(),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": float(row.get("profit") or 0.0),
                "tickets": 1,
                "lots": float(row.get("volume") or row.get("lots") or 0.0),
                "source_csv": str(row.get("source_csv") or ""),
                "source_row": ordinal,
            }
        )
    return rows


def weighted_rows(rows: list[dict[str, Any]], multiplier: float) -> list[dict[str, Any]]:
    suffix = str(multiplier).replace(".", "p")
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["source_id"] = f"{row['source_id']}_x{suffix}"
        item["component"] = f"{row.get('component', row['source_id'])}_x{suffix}"
        item["upstream_source_id"] = row.get("source_id", "")
        item["pnl_usd"] = round(float(row.get("pnl_usd") or 0.0) * multiplier, 6)
        item["lots"] = round(float(row.get("lots") or 0.0) * multiplier, 6)
        out.append(item)
    return out


def load_causal_search_top_candidates(limit: int = 25) -> list[dict[str, Any]]:
    if not CAUSAL_SEARCH_JSON.exists():
        return []
    payload = json.loads(CAUSAL_SEARCH_JSON.read_text(encoding="utf-8"))
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    out: list[dict[str, Any]] = []
    for row in payload.get("top_results", []):
        source_variants = tuple(row.get("source_variants", []))
        key = (str(row.get("portfolio_name", "")), str(row.get("guard_name", "")), source_variants)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
        if len(out) >= limit:
            break
    return out


def build_current_causal_residual_packages() -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    base = enrich_base_trades()
    residual_raw, blocked = residual_raw_trades(base)
    configs = [
        {
            "name": "residual_plus75_target75_cooldown10_causal",
            "profit_target_usd": 75.0,
            "max_trades_per_day": None,
        },
        {
            "name": "residual_plus50_max6_cooldown10_causal",
            "profit_target_usd": 50.0,
            "max_trades_per_day": 6,
        },
        {
            "name": "residual_plus50_max8_cooldown10_causal",
            "profit_target_usd": 50.0,
            "max_trades_per_day": 8,
        },
    ]
    packages: dict[str, list[dict[str, Any]]] = {}
    stats: dict[str, Any] = {
        "residual_raw_trades": len(residual_raw),
        "residual_blocked_trades": len(blocked),
        "packages": [],
    }
    for config in configs:
        selected, guard_stats = apply_state_guard(
            residual_raw,
            state_rule="none",
            profit_target_usd=config["profit_target_usd"],
            loss_stop_usd=None,
            max_trades_per_day=config["max_trades_per_day"],
            max_losses_per_day=None,
            cooldown_after_loss_minutes=10,
            early_trade_count=2,
            early_pnl_threshold=0.0,
        )
        packages[config["name"]] = selected
        stats["packages"].append(
            {
                "name": config["name"],
                "selected_trades": len(selected),
                "profit_target_usd": config["profit_target_usd"],
                "max_trades_per_day": config["max_trades_per_day"],
                "cooldown_after_loss_minutes": 10,
                "guard_stats": guard_stats,
            }
        )
    return packages, stats


def load_second_books() -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    csv_variants = load_csv_variants()
    synthetic_packages_for_reconstruction = load_synthetic_business_packages()
    variants = {**csv_variants, **synthetic_packages_for_reconstruction}
    books: dict[str, list[dict[str, Any]]] = {}
    current_residual_packages, residual_package_meta = build_current_causal_residual_packages()
    meta: dict[str, Any] = {
        "csv_variant_count": len(csv_variants),
        "synthetic_package_count_for_reconstruction": len(synthetic_packages_for_reconstruction),
        "current_causal_residual_package_meta": residual_package_meta,
        "candidate_source": rel(CAUSAL_SEARCH_JSON),
    }

    priority = 300
    for package_name, rows in current_residual_packages.items():
        books[package_name] = normalize_momentum_trades(package_name, rows, priority)
        priority += 1

    exact_variant_meta: list[dict[str, Any]] = []
    for variant_name, trades in sorted(csv_variants.items()):
        net = round(sum(float(row.get("profit") or 0.0) for row in trades), 2)
        if len(trades) < 100 or net <= 0.0:
            continue
        source_id = f"exact_{safe_key(variant_name)}"
        books[source_id] = normalize_momentum_trades(source_id, trades, priority)
        priority += 1
        exact_variant_meta.append(
            {
                "book": source_id,
                "variant_name": variant_name,
                "trades": len(trades),
                "net_usd": net,
            }
        )
    meta["exact_variant_books"] = exact_variant_meta

    top_candidates = load_causal_search_top_candidates()
    reconstructed_meta: list[dict[str, Any]] = []
    for index, candidate in enumerate(top_candidates, start=1):
        source_variants = list(candidate.get("source_variants", []))
        guard_name = str(candidate.get("guard_name", ""))
        selected, guard_stats, duplicate_drops, missing = reconstruct(variants, source_variants, guard_name)
        if not selected:
            continue
        safe_name = f"causal_top{index:02d}_{guard_name}"
        books[safe_name] = normalize_momentum_trades(safe_name, selected, priority)
        priority += 1
        reconstructed_meta.append(
            {
                "book": safe_name,
                "portfolio_name": candidate.get("portfolio_name", ""),
                "guard_name": guard_name,
                "source_variants": source_variants,
                "missing": missing,
                "duplicate_drops_before_guard": duplicate_drops,
                "guard_stats": guard_stats,
            }
        )
    meta["reconstructed_candidates"] = reconstructed_meta
    return books, meta


def weekly_shape(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_week: dict[date, float] = defaultdict(float)
    by_month: dict[str, float] = defaultdict(float)
    for row in rows:
        exit_day = parse_date(row.get("exit_date") or maybe_parse_dt(row.get("exit_time")).date())
        pnl = float(row.get("pnl_usd") or 0.0)
        by_week[week_start(exit_day)] += pnl
        by_month[exit_day.strftime("%Y-%m")] += pnl

    active_weeks = [week for week, value in by_week.items() if abs(value) > 0.0000001]
    positive_weeks_all = sum(1 for week in ALL_WEEK_STARTS if by_week.get(week, 0.0) > 0.0)
    positive_weeks_active = sum(1 for week in active_weeks if by_week.get(week, 0.0) > 0.0)
    rolling_positive = 0
    rolling_total = 0
    for index in range(0, len(ALL_WEEK_STARTS) - 3):
        rolling_total += 1
        total = sum(by_week.get(ALL_WEEK_STARTS[index + offset], 0.0) for offset in range(4))
        if total > 0:
            rolling_positive += 1

    months = sorted(by_month)
    return {
        "calendar_weeks": len(ALL_WEEK_STARTS),
        "active_weeks": len(active_weeks),
        "active_week_pct": round(100.0 * len(active_weeks) / len(ALL_WEEK_STARTS), 2) if ALL_WEEK_STARTS else 0.0,
        "positive_weeks": positive_weeks_all,
        "positive_week_pct": round(100.0 * positive_weeks_all / len(ALL_WEEK_STARTS), 2) if ALL_WEEK_STARTS else 0.0,
        "positive_active_week_pct": round(100.0 * positive_weeks_active / len(active_weeks), 2)
        if active_weeks
        else 0.0,
        "worst_week_usd": round(min((by_week.get(week, 0.0) for week in ALL_WEEK_STARTS), default=0.0), 2),
        "best_week_usd": round(max((by_week.get(week, 0.0) for week in ALL_WEEK_STARTS), default=0.0), 2),
        "rolling_4_week_positive_pct": round(100.0 * rolling_positive / rolling_total, 2) if rolling_total else 0.0,
        "months": len(months),
        "positive_months": sum(1 for month in months if by_month[month] > 0),
        "positive_month_pct": round(100.0 * sum(1 for month in months if by_month[month] > 0) / len(months), 2)
        if months
        else 0.0,
        "worst_month_usd": round(min(by_month.values(), default=0.0), 2),
        "best_month_usd": round(max(by_month.values(), default=0.0), 2),
        "june_2026_net_usd": round(by_month.get("2026-06", 0.0), 2),
    }


def remove_top_winners(rows: list[dict[str, Any]], count: int) -> float:
    profits = [float(row.get("pnl_usd") or 0.0) for row in rows]
    return round(sum(profits) - sum(sorted((value for value in profits if value > 0), reverse=True)[:count]), 2)


def decide(metrics: dict[str, Any], shape: dict[str, Any], stress_030: dict[str, Any]) -> str:
    wl = metrics.get("avg_win_loss") or 0.0
    stress_wl = stress_030.get("avg_win_loss") or 0.0
    if shape["positive_week_pct"] >= TARGET_HIGH and metrics["active_weekday_pct"] >= TARGET_ACTIVITY:
        return "HITS_80_WEEK_AND_90_ACTIVITY_DIAGNOSTIC"
    if shape["positive_week_pct"] >= TARGET_LOW and metrics["active_weekday_pct"] >= TARGET_ACTIVITY:
        return "HITS_70_WEEK_AND_90_ACTIVITY_DIAGNOSTIC"
    if shape["positive_week_pct"] >= TARGET_LOW:
        return "HITS_70_WEEK_ACTIVITY_GAP"
    if metrics["active_weekday_pct"] >= TARGET_ACTIVITY:
        return "ACTIVITY_HIT_WEEKLY_GAP"
    if wl < 2.0 or stress_wl < 2.0:
        return "WEEKLY_GAP_AND_WL_DILUTION"
    return "WEEKLY_GAP"


def evaluate_portfolio(name: str, rows: list[dict[str, Any]], dedupe: bool) -> dict[str, Any]:
    deduped_rows, dropped = dedupe_signals(rows) if dedupe else (list(rows), [])
    enriched_rows, exit_stats = ensure_exit_times(deduped_rows)
    metrics = summary_metrics(enriched_rows, market_days=MARKET_DAYS)
    last12 = summary_metrics(
        [row for row in enriched_rows if row["entry_date"] >= LAST12_START],
        market_days=LAST12_MARKET_DAYS,
    )
    stress_030 = summary_metrics(enriched_rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_shape(enriched_rows)
    row = {
        "name": name,
        "dedupe_applied": dedupe,
        "dropped_overlap_signals": len(dropped),
        "signals": metrics["signals"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "stress_030_wl": stress_030["avg_win_loss"],
        "active_weekday_pct": metrics["active_weekday_pct"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "dd": metrics["max_closed_drawdown_usd"],
        "positive_week_pct": shape["positive_week_pct"],
        "positive_active_week_pct": shape["positive_active_week_pct"],
        "active_week_pct": shape["active_week_pct"],
        "worst_week": shape["worst_week_usd"],
        "rolling4_positive_pct": shape["rolling_4_week_positive_pct"],
        "positive_month_pct": shape["positive_month_pct"],
        "worst_month": shape["worst_month_usd"],
        "june_2026": shape["june_2026_net_usd"],
        "last12_wr": last12["win_rate_pct"],
        "last12_wl": last12["avg_win_loss"],
        "last12_active_weekday_pct": last12["active_weekday_pct"],
        "top100_removed_net": remove_top_winners(enriched_rows, 100),
        "top200_removed_net": remove_top_winners(enriched_rows, 200),
        "decision": decide(metrics, shape, stress_030),
        "exit_stats": exit_stats,
        "kept_rows": enriched_rows,
        "dropped_rows": dropped,
    }
    return row


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Smooth Second-Book Weekly Target Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: offline recomposition of existing exact-MT5 ledgers and reconstructed residual package trades. No live/demo MT5 runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Target now tested: first reach 70-80% positive calendar weeks while keeping about 90% active weekdays. Rows marked diagnostic are not demo-ready until converted into a causal MT5 rule and re-run exactly.",
        "",
        "## Best Rows",
        "",
        "| Rank | Portfolio | Decision | Signals | WR% | W/L | Stress -0.30 W/L | Active weekdays% | Positive weeks% | Active weeks% | PF | Net | DD | Worst week | Rolling 4w+% | June 2026 | Top200 removed |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(payload["top_rows"][:20], start=1):
        lines.append(
            f"| {index} | `{row['name'][:90]}` | `{row['decision']}` | {row['signals']} | {row['wr']:.2f} | "
            f"{row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | {row['active_weekday_pct']:.2f} | "
            f"{row['positive_week_pct']:.2f} | {row['active_week_pct']:.2f} | {row['pf'] or 0.0:.4f} | "
            f"{row['net']:.2f} | {row['dd']:.2f} | {row['worst_week']:.2f} | {row['rolling4_positive_pct']:.2f} | "
            f"{row['june_2026']:.2f} | {row['top200_removed_net']:.2f} |"
        )
    best = payload["best_row"]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Best weekly/activity row: `{best['name']}`.",
            f"- It reaches `{best['positive_week_pct']:.2f}%` positive calendar weeks and `{best['active_weekday_pct']:.2f}%` active weekdays.",
            f"- Average W/L is `{best['wl'] or 0.0:.4f}` and stressed W/L at -0.30 per ticket is `{best['stress_030_wl'] or 0.0:.4f}`.",
            f"- Verdict: `{best['decision']}`.",
            "",
            "## Artifacts",
            "",
        ]
    )
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def csv_safe_row(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "name",
        "decision",
        "signals",
        "wr",
        "wl",
        "stress_030_wl",
        "active_weekday_pct",
        "positive_week_pct",
        "positive_active_week_pct",
        "active_week_pct",
        "pf",
        "net",
        "dd",
        "worst_week",
        "rolling4_positive_pct",
        "positive_month_pct",
        "worst_month",
        "june_2026",
        "top100_removed_net",
        "top200_removed_net",
        "last12_wr",
        "last12_wl",
        "last12_active_weekday_pct",
        "dropped_overlap_signals",
    ]
    return {field: row.get(field) for field in fields}


def write_results_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(csv_safe_row(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(csv_safe_row(row))


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"kept_rows", "dropped_rows"}}


def main() -> int:
    baseline, baseline_exit_stats = ensure_exit_times(normalize_baseline())
    second_books, source_meta = load_second_books()
    source_meta["baseline_exit_stats"] = baseline_exit_stats

    evaluations: list[dict[str, Any]] = []
    evaluations.append(evaluate_portfolio("baseline_f67_h16_no_f33", baseline, dedupe=False))

    for name, rows in second_books.items():
        evaluations.append(evaluate_portfolio(name, rows, dedupe=False))
        evaluations.append(evaluate_portfolio(f"baseline_plus_{name}", baseline + rows, dedupe=True))
        for multiplier in SECOND_BOOK_WEIGHT_SWEEP:
            scaled = weighted_rows(rows, multiplier)
            label = str(multiplier).replace(".", "p")
            evaluations.append(
                evaluate_portfolio(
                    f"baseline_plus_{name}_sized_x{label}",
                    baseline + scaled,
                    dedupe=True,
                )
            )

    rank_order = {
        "HITS_80_WEEK_AND_90_ACTIVITY_DIAGNOSTIC": 0,
        "HITS_70_WEEK_AND_90_ACTIVITY_DIAGNOSTIC": 1,
        "HITS_70_WEEK_ACTIVITY_GAP": 2,
        "ACTIVITY_HIT_WEEKLY_GAP": 3,
    }
    evaluations.sort(
        key=lambda row: (
            rank_order.get(row["decision"], 9),
            -row["positive_week_pct"],
            -row["active_weekday_pct"],
            -row["rolling4_positive_pct"],
            -row["net"],
        )
    )
    best = evaluations[0] if evaluations else {}

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    best_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv"
    best_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv"

    if best:
        write_signal_csv(best_kept_csv, best["kept_rows"])
        write_signal_csv(best_dropped_csv, best["dropped_rows"])

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "results_csv": rel(results_csv),
        "best_kept_csv": rel(best_kept_csv),
        "best_dropped_csv": rel(best_dropped_csv),
    }
    payload = {
        "status": "WEEKLY_TARGET_DIAGNOSTIC_COMPLETE" if evaluations else "NO_RESULTS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "boundary": "offline_existing_exact_mt5_ledgers_no_runtime_change",
        "targets": {
            "positive_week_pct_low": TARGET_LOW,
            "positive_week_pct_high": TARGET_HIGH,
            "active_weekday_pct": TARGET_ACTIVITY,
        },
        "baseline_csv": rel(BASELINE_KEPT),
        "source_meta": source_meta,
        "best_row": strip_heavy(best) if best else {},
        "top_rows": [strip_heavy(row) for row in evaluations[:50]],
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_results_csv(results_csv, evaluations)
    report_md.write_text(render(payload), encoding="utf-8")
    print(report_md)
    if best:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "best": best["name"],
                    "decision": best["decision"],
                    "positive_week_pct": best["positive_week_pct"],
                    "active_weekday_pct": best["active_weekday_pct"],
                    "wr": best["wr"],
                    "wl": best["wl"],
                    "stress_030_wl": best["stress_030_wl"],
                    "net": best["net"],
                    "june_2026": best["june_2026"],
                },
                indent=2,
            )
        )
    return 0 if evaluations else 1


if __name__ == "__main__":
    raise SystemExit(main())
