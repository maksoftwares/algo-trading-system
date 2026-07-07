from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_f67_h16_no_f33_composition import read_raw_rows
from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times, week_start
from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    LAST12_START,
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    parse_dt,
    summary_metrics,
)
from run_a1_v9_v10_rr2_stretch_probe import last12_metrics, owner_metrics, read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_D1_GEOMETRY_V2_WEEKLY_SHAPE_PREREG_2026_07_06.md"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
BASELINE_RAW = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_202207_202606_HYBRID_RAW.csv"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "OWNER_GOAL_H4_D1_GEOMETRY_V2_WEEKLY_SHAPE_202207_202606"
OUTPUT_STEM = "A1_XAU_H4_D1_GEOMETRY_V2_WEEKLY_SHAPE_202207_202606"
REMOVED_SOURCE = "step1_f33_r30_be_never"
REPLACED_SOURCE = "h4_d1_long_best_box2_atr80"


BASE_H4_INPUTS = {
    "InpSignalMode": "7",
    "InpDirectionMode": "1",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpRiskReward": "2.00",
    "InpMaxEstimatedCostR": "0.15",
    "InpStopCeilingPoints": "0",
    "InpMaxTradesPerDay": "6",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "false",
    "InpMaxOpenPositionsPerMagic": "32",
    "InpD1CompressionAtrPercentileMax": "80.00",
    "InpD1CompressionBoxDays": "2",
    "InpD1CompressionRangeMedianMax": "1.50",
    "InpD1CompressionH4MinBodyFraction": "0.35",
}


def geometry_variant(name: str, cap_points: int, early_adverse: bool = False) -> a1.Variant:
    inputs = {
        **BASE_H4_INPUTS,
        "InpStopCapPoints": str(cap_points),
    }
    label = f"D1/H4 long-only best box2 ATR80, true stop cap {cap_points} points"
    if early_adverse:
        inputs.update(
            {
                "InpEarlyAdverseExitEnabled": "true",
                "InpEarlyAdverseExitShadowOnly": "false",
                "InpEarlyAdverseExitAfterMinutes": "240",
                "InpEarlyAdverseExitR": "0.60",
            }
        )
        label += ", early adverse close -0.60R after 240m"
    return a1.Variant(
        name=name,
        label=label,
        run_id=f"BT_A1_XAU_H4_D1_GEOM_V2_{name.upper()}",
        tester_inputs=inputs,
    )


VARIANTS = [
    geometry_variant("cap6000", 6000),
    geometry_variant("cap7500", 7500),
    geometry_variant("cap9000", 9000),
    geometry_variant("cap6000_eae240_r060", 6000, early_adverse=True),
    geometry_variant("cap7500_eae240_r060", 7500, early_adverse=True),
    geometry_variant("cap9000_eae240_r060", 9000, early_adverse=True),
]


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_date(value: str) -> date:
    return date.fromisoformat(str(value).strip())


def read_composition_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for ordinal, row in enumerate(csv.DictReader(handle), start=2):
            entry_time = parse_dt(str(row["entry_time"]))
            rows.append(
                {
                    "component": row.get("component", ""),
                    "source_id": row.get("source_id", ""),
                    "upstream_source_id": row.get("upstream_source_id", ""),
                    "upstream_component": row.get("upstream_component", ""),
                    "family_group": row.get("family_group", ""),
                    "source_priority": int(row.get("source_priority") or 0),
                    "cell_id": row.get("cell_id", ""),
                    "component_priority": int(row.get("component_priority") or 0),
                    "variant_name": row.get("variant_name", ""),
                    "entry_time": entry_time,
                    "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                    "exit_time": row.get("exit_time", ""),
                    "direction": row.get("direction", ""),
                    "pnl_usd": float(row.get("pnl_usd") or 0.0),
                    "tickets": int(row.get("tickets") or 1),
                    "lots": float(row.get("lots") or 0.0),
                    "source_csv": row.get("source_csv", str(path)),
                    "source_row": int(row.get("source_row") or ordinal),
                }
            )
    return rows


def replacement_rows(trade_csv: Path, variant_name: str) -> list[dict[str, Any]]:
    source_id = f"h4_d1_geom_v2_{variant_name}"
    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(read_trade_csv(trade_csv), start=2):
        entry_time = parse_dt(row["entry_time"])
        rows.append(
            {
                "component": source_id,
                "source_id": source_id,
                "upstream_source_id": source_id,
                "upstream_component": "h4_d1_geometry_v2_weekly_shape",
                "family_group": "h4_d1_core_shape",
                "source_priority": 80,
                "cell_id": variant_name,
                "component_priority": 0,
                "variant_name": variant_name,
                "entry_time": entry_time,
                "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                "exit_time": row.get("exit_time", ""),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": float(row.get("profit_float") or 0.0),
                "tickets": 1,
                "lots": float(row.get("volume") or 0.0),
                "source_csv": str(trade_csv),
                "source_row": ordinal,
            }
        )
    return rows


def remove_sources(raw: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    kept: list[dict[str, Any]] = []
    counts = {"removed_f33": 0, "removed_replaced_h4": 0}
    for row in raw:
        source = row.get("source_id", "")
        upstream = row.get("upstream_source_id", "")
        if source == REMOVED_SOURCE or upstream == REMOVED_SOURCE:
            counts["removed_f33"] += 1
            continue
        if source == REPLACED_SOURCE or upstream == REPLACED_SOURCE:
            counts["removed_replaced_h4"] += 1
            continue
        kept.append(row)
    return kept, counts


def rolling_positive_pct(weeks: list[date], by_week: dict[date, float], size: int = 4) -> float:
    if len(weeks) < size:
        return 0.0
    positives = 0
    total = 0
    for idx in range(len(weeks) - size + 1):
        total += 1
        value = sum(by_week[weeks[j]] for j in range(idx, idx + size))
        if value > 0:
            positives += 1
    return round(100.0 * positives / total, 2) if total else 0.0


def weekly_exit_shape(rows: list[dict[str, Any]]) -> dict[str, Any]:
    enriched, exit_stats = enrich_exit_times(rows)
    by_week: dict[date, float] = defaultdict(float)
    by_month: dict[str, float] = defaultdict(float)
    for row in enriched:
        pnl = float(row["pnl_usd"])
        exit_day = row["exit_date"]
        by_week[week_start(exit_day)] += pnl
        by_month[exit_day.strftime("%Y-%m")] += pnl

    weeks = sorted(by_week)
    months = sorted(by_month)
    positive_weeks = sum(1 for key in weeks if by_week[key] > 0)
    positive_months = sum(1 for key in months if by_month[key] > 0)
    return {
        "trade_weeks": len(weeks),
        "positive_weeks": positive_weeks,
        "positive_week_pct": round(100.0 * positive_weeks / len(weeks), 2) if weeks else 0.0,
        "worst_week_usd": round(min(by_week.values(), default=0.0), 2),
        "best_week_usd": round(max(by_week.values(), default=0.0), 2),
        "rolling_4_week_positive_pct": rolling_positive_pct(weeks, by_week),
        "months": len(months),
        "positive_months": positive_months,
        "positive_month_pct": round(100.0 * positive_months / len(months), 2) if months else 0.0,
        "worst_month_usd": round(min(by_month.values(), default=0.0), 2),
        "best_month_usd": round(max(by_month.values(), default=0.0), 2),
        "june_2026_net_usd": round(by_month.get("2026-06", 0.0), 2),
        "exit_match_stats": exit_stats,
    }


def remove_top_winners(rows: list[dict[str, Any]], pct: float) -> dict[str, Any]:
    wins = sorted((row for row in rows if float(row["pnl_usd"]) > 0), key=lambda row: float(row["pnl_usd"]), reverse=True)
    remove_count = math.ceil(len(wins) * pct)
    remove_ids = {id(row) for row in wins[:remove_count]}
    kept = [row for row in rows if id(row) not in remove_ids]
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    return {
        "removed_winners": remove_count,
        "signals": metrics["signals"],
        "win_rate_pct": metrics["win_rate_pct"],
        "avg_win_loss": metrics["avg_win_loss"],
        "profit_factor": metrics["profit_factor"],
        "net_usd": metrics["net_usd"],
    }


def decision_for(metrics: dict[str, Any], stress_030: dict[str, Any], shape: dict[str, Any], baseline_shape: dict[str, Any]) -> str:
    wl = metrics.get("avg_win_loss") or 0.0
    stress_wl = stress_030.get("avg_win_loss") or 0.0
    if metrics["win_rate_pct"] < 50.0 or wl < 2.0:
        return "REJECT_BREAKS_CORE_WR_WL"
    if stress_wl < 2.0:
        return "RESEARCH_ONLY_FAILS_030_TICKET_STRESS"
    if shape["positive_week_pct"] <= baseline_shape["positive_week_pct"]:
        return "RESEARCH_ONLY_WEEKLY_NOT_IMPROVED"
    if shape["worst_week_usd"] <= baseline_shape["worst_week_usd"]:
        return "RESEARCH_ONLY_WORST_WEEK_NOT_IMPROVED"
    if shape["rolling_4_week_positive_pct"] <= baseline_shape["rolling_4_week_positive_pct"]:
        return "RESEARCH_ONLY_ROLLING4_NOT_IMPROVED"
    if shape["positive_week_pct"] >= 90.0:
        return "OWNER_WEEKLY90_HIT_REVIEW_REQUIRED"
    return "WEEKLY_SHAPE_CLUE_NOT_DEMO_READY"


def write_signal_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "component",
        "source_id",
        "upstream_source_id",
        "upstream_component",
        "family_group",
        "source_priority",
        "cell_id",
        "component_priority",
        "variant_name",
        "entry_time",
        "entry_date",
        "exit_time",
        "exit_date",
        "direction",
        "pnl_usd",
        "tickets",
        "lots",
        "source_csv",
        "source_row",
        "drop_reason",
        "duplicate_of_source_id",
        "duplicate_of_entry_time",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            if isinstance(out.get("entry_time"), datetime):
                out["entry_time"] = out["entry_time"].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(out.get("exit_time"), datetime):
                out["exit_time"] = out["exit_time"].strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(out.get("entry_date"), "isoformat"):
                out["entry_date"] = out["entry_date"].isoformat()
            if hasattr(out.get("exit_date"), "isoformat"):
                out["exit_date"] = out["exit_date"].isoformat()
            writer.writerow(out)


def result_row(
    variant: str,
    metrics: dict[str, Any],
    stress_030: dict[str, Any],
    shape: dict[str, Any],
    decision: str,
) -> dict[str, Any]:
    return {
        "variant": variant,
        "signals": metrics["signals"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "active": metrics["active_weekday_pct"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "dd": metrics["max_closed_drawdown_usd"],
        "stress_030_wl": stress_030["avg_win_loss"],
        "positive_week_pct": shape["positive_week_pct"],
        "worst_week": shape["worst_week_usd"],
        "rolling4_positive_pct": shape["rolling_4_week_positive_pct"],
        "positive_month_pct": shape["positive_month_pct"],
        "worst_month": shape["worst_month_usd"],
        "june_2026": shape["june_2026_net_usd"],
        "decision": decision,
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU H4/D1 Geometry V2 Weekly-Shape Exact MT5 Pass",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: six preregistered exact-MT5 H4/D1 geometry cells in the isolated Strategy Tester root, recomposed into the current best hybrid. Weekly P&L is grouped by reconstructed final signal `exit_time`. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Baseline",
        "",
        "| Signals | WR% | W/L | Active% | PF | Net | DD | Stress -0.30 W/L | Positive weeks% | Worst week | Rolling 4w+% | Positive months% | Worst month | June 2026 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    base = payload["baseline_row"]
    lines.append(
        f"| {base['signals']} | {base['wr']:.2f} | {base['wl'] or 0.0:.4f} | {base['active']:.2f} | "
        f"{base['pf'] or 0.0:.4f} | {base['net']:.2f} | {base['dd']:.2f} | {base['stress_030_wl'] or 0.0:.4f} | "
        f"{base['positive_week_pct']:.2f} | {base['worst_week']:.2f} | {base['rolling4_positive_pct']:.2f} | "
        f"{base['positive_month_pct']:.2f} | {base['worst_month']:.2f} | {base['june_2026']:.2f} |"
    )
    lines.extend(
        [
            "",
            "## Recomposed Cells",
            "",
            "| Variant | Signals | WR% | W/L | Active% | PF | Net | DD | Stress -0.30 W/L | Positive weeks% | Worst week | Rolling 4w+% | Positive months% | Worst month | June 2026 | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["result_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['dd']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | {row['worst_week']:.2f} | "
            f"{row['rolling4_positive_pct']:.2f} | {row['positive_month_pct']:.2f} | {row['worst_month']:.2f} | "
            f"{row['june_2026']:.2f} | `{row['decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Tail Reliance",
            "",
            "| Variant | Ex-top-1 removed | Ex-top-1 W/L | Ex-top-1 PF | Ex-top-1 net | Ex-top-2 removed | Ex-top-2 W/L | Ex-top-2 PF | Ex-top-2 net |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["tail_rows"]:
        one = item["ex_top_1pct"]
        two = item["ex_top_2pct"]
        lines.append(
            f"| `{item['variant']}` | {one['removed_winners']} | {one['avg_win_loss'] or 0.0:.4f} | "
            f"{one['profit_factor'] or 0.0:.4f} | {one['net_usd']:.2f} | {two['removed_winners']} | "
            f"{two['avg_win_loss'] or 0.0:.4f} | {two['profit_factor'] or 0.0:.4f} | {two['net_usd']:.2f} |"
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 H4/D1 geometry v2 weekly-shape pass.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(BASELINE_KEPT)
    require_file(BASELINE_RAW)

    a1.VARIANTS = VARIANTS
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_VARIANTS.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_VARIANTS.json"
    mt5_payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=mt5_report_md,
        report_json=mt5_report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )

    baseline_rows = read_composition_csv(BASELINE_KEPT)
    baseline_metrics = summary_metrics(baseline_rows, market_days=MARKET_DAYS)
    baseline_stress_030 = summary_metrics(baseline_rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    baseline_shape = weekly_exit_shape(baseline_rows)
    baseline_row = result_row("baseline_f67_h16_no_f33", baseline_metrics, baseline_stress_030, baseline_shape, "BASELINE")

    raw = read_raw_rows(BASELINE_RAW)
    filtered_raw, removal_counts = remove_sources(raw)
    result_rows: list[dict[str, Any]] = []
    tail_rows: list[dict[str, Any]] = []
    variant_details: list[dict[str, Any]] = []
    outputs = {
        "md": str(report_md),
        "json": str(report_json),
        "results_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"),
        "mt5_variants_md": str(mt5_report_md),
        "mt5_variants_json": str(mt5_report_json),
    }

    for result in mt5_payload["variants"]:
        variant_name = result["name"]
        trade_csv = Path(result["trade_csv"])
        mt5_rows = read_trade_csv(trade_csv)
        standalone_metrics = owner_metrics(mt5_rows, FROM_DATE, TO_DATE)
        standalone_last12 = last12_metrics(mt5_rows, TO_DATE)

        replacement_raw = filtered_raw + replacement_rows(trade_csv, variant_name)
        replacement_kept, replacement_dropped = dedupe_signals(replacement_raw)
        replacement_metrics = summary_metrics(replacement_kept, market_days=MARKET_DAYS)
        replacement_last12 = summary_metrics(
            [row for row in replacement_kept if row["entry_date"] >= LAST12_START],
            market_days=LAST12_MARKET_DAYS,
        )
        replacement_metrics.update(
            {
                "last12_win_rate_pct": replacement_last12["win_rate_pct"],
                "last12_avg_win_loss": replacement_last12["avg_win_loss"],
                "last12_active_weekday_pct": replacement_last12["active_weekday_pct"],
            }
        )
        stress_030 = summary_metrics(replacement_kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
        replacement_shape = weekly_exit_shape(replacement_kept)
        decision = decision_for(replacement_metrics, stress_030, replacement_shape, baseline_shape)
        result_rows.append(result_row(variant_name, replacement_metrics, stress_030, replacement_shape, decision))
        tail_rows.append(
            {
                "variant": variant_name,
                "ex_top_1pct": remove_top_winners(replacement_kept, 0.01),
                "ex_top_2pct": remove_top_winners(replacement_kept, 0.02),
            }
        )

        enriched_kept, kept_exit_stats = enrich_exit_times(replacement_kept)
        kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{variant_name}_KEPT.csv"
        dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{variant_name}_DROPPED.csv"
        write_signal_csv(kept_csv, enriched_kept)
        write_signal_csv(dropped_csv, replacement_dropped)
        outputs[f"{variant_name}_kept_csv"] = str(kept_csv)
        outputs[f"{variant_name}_dropped_csv"] = str(dropped_csv)

        variant_details.append(
            {
                "variant": variant_name,
                "mt5_result": result,
                "standalone_metrics": standalone_metrics,
                "standalone_last12": standalone_last12,
                "replacement_metrics": replacement_metrics,
                "replacement_stress_030": stress_030,
                "replacement_shape": replacement_shape,
                "replacement_decision": decision,
                "replacement_raw_rows": len(replacement_raw),
                "replacement_kept_rows": len(replacement_kept),
                "replacement_dropped_rows": len(replacement_dropped),
                "kept_exit_match_stats": kept_exit_stats,
                "kept_csv": str(kept_csv),
                "dropped_csv": str(dropped_csv),
            }
        )

    with Path(outputs["results_csv"]).open("w", newline="", encoding="utf-8") as handle:
        keys = list(result_rows[0].keys()) if result_rows else []
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(result_rows)

    useful = [row for row in result_rows if row["decision"] in {"WEEKLY_SHAPE_CLUE_NOT_DEMO_READY", "OWNER_WEEKLY90_HIT_REVIEW_REQUIRED"}]
    owner_hits = [row for row in result_rows if row["decision"] == "OWNER_WEEKLY90_HIT_REVIEW_REQUIRED"]
    if owner_hits:
        status = "OWNER_WEEKLY90_HIT_REVIEW_REQUIRED"
        interpretation = (
            "At least one preregistered exact-MT5 geometry cell reached the owner weekly target. This is not auto-demo-ready; it needs external review and source-level audit before any demo spec."
        )
    elif useful:
        status = "USEFUL_WEEKLY_SHAPE_CLUE_NOT_DEMO_READY"
        best = max(useful, key=lambda row: (row["positive_week_pct"], row["worst_week"], row["net"]))
        interpretation = (
            f"The best useful cell is `{best['variant']}`. It improved closed-week shape while preserving the core gates, "
            "but it did not reach the owner 90% positive-week target, so it remains research-only."
        )
    else:
        status = "NO_GEOMETRY_V2_SURVIVOR"
        best = max(result_rows, key=lambda row: (row["positive_week_pct"], row["worst_week"], row["wl"] or 0.0)) if result_rows else None
        interpretation = (
            "No preregistered geometry-v2 cell met the core and weekly-shape gates. This freezes the current H4/D1 stop-cap/early-adverse path unless an external review proposes a materially new idea."
        )
        if best:
            interpretation += (
                f" Best raw weekly-shape row was `{best['variant']}` with {best['positive_week_pct']}% positive weeks, "
                f"worst week ${best['worst_week']}, WR {best['wr']}%, W/L {best['wl']}."
            )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "removal_counts": removal_counts,
        "baseline_metrics": baseline_metrics,
        "baseline_stress_030": baseline_stress_030,
        "baseline_shape": baseline_shape,
        "baseline_row": baseline_row,
        "baseline_ex_top_1pct": remove_top_winners(baseline_rows, 0.01),
        "baseline_ex_top_2pct": remove_top_winners(baseline_rows, 0.02),
        "result_rows": result_rows,
        "tail_rows": tail_rows,
        "variant_details": variant_details,
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "baseline": baseline_row,
                "best_by_weekly": max(result_rows, key=lambda row: (row["positive_week_pct"], row["worst_week"], row["wl"] or 0.0))
                if result_rows
                else None,
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
