from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import (
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    parse_dt,
    rel,
    summary_metrics,
)
from run_a1_downtrend_short_engine_probe import baseline_result_row, guard_counts, red_week_score, source_rows, weekly_pnl
from run_a1_h4_d1_geometry_v2_weekly_shape import (
    FROM_DATE,
    TO_DATE,
    read_composition_csv,
    sha256_file,
    weekly_exit_shape,
    write_signal_csv,
)
from run_a1_h4_d1_review_repair_exact import MAY_END, MAY_START, RECENT3_END, RECENT3_START, period_stats
from run_a1_v9_v10_rr2_stretch_probe import read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_BEAR_QUALITY_FIRST_PREREG_2026_07_07.md"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv"
OUTPUT_STEM = "A1_XAU_BEAR_QUALITY_FIRST_EXACT_202207_202606"
TAG = "OWNER_GOAL_BEAR_QUALITY_FIRST_202207_202606"

BEAR_PRIORITY = 90
BEAR_FAMILY = "bear_quality_first"

COMMON_BEAR_INPUTS = {
    "InpDirectionMode": "2",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpD1SupportStateGateMode": "3",
    "InpD1SupportStateEmaPeriod": "20",
    "InpD1SupportStateSlopeLagBars": "5",
    "InpBlockedEntryDayHoursCsv": "5:20",
    "InpMaxTradesPerDay": "6",
    "InpCooldownMinutes": "30",
    "InpOnePositionPerMagic": "true",
}

M5_QUALITY_BASE = {
    **COMMON_BEAR_INPUTS,
    "InpSignalMode": "5",
    "InpUseH1TrendFilter": "true",
    "InpUseH4TrendFilter": "true",
    "InpH1TrendMinSlopePoints": "50",
    "InpH4TrendMinSlopePoints": "50",
    "InpMaxEstimatedCostR": "0.04",
    "InpStopFloorPoints": "350",
    "InpStopCeilingPoints": "1000",
    "InpM5TrendEmaFastPeriod": "8",
    "InpM5TrendEmaSlowPeriod": "21",
    "InpM5TrendSlopeBars": "3",
    "InpM5TrendMinSlopeAtr": "0.08",
    "InpM5TrendMaxDistanceAtr": "0.80",
    "InpMinRangeAtr": "0.50",
    "InpMinBodyFraction": "0.45",
    "InpShortCloseLocation": "0.35",
    "InpMinThreeBarMoveAtr": "0.25",
    "InpMaxThreeBarMoveAtr": "2.50",
}

COMBOS = {
    "bear_quality_m5_ema_slope50_only": ["bear_quality_m5_ema_slope50"],
    "bear_quality_m5_ema_slope100_only": ["bear_quality_m5_ema_slope100"],
    "bear_quality_break_run_tight_only": ["bear_quality_break_run_tight"],
    "bear_quality_compression_break_only": ["bear_quality_compression_break"],
    "bear_quality_h4_pullback_d1bias_only": ["bear_quality_h4_pullback_d1bias"],
    "bear_quality_weekly_rejection_only": ["bear_quality_weekly_rejection"],
    "bear_quality_all_cells": [
        "bear_quality_m5_ema_slope50",
        "bear_quality_m5_ema_slope100",
        "bear_quality_break_run_tight",
        "bear_quality_compression_break",
        "bear_quality_h4_pullback_d1bias",
        "bear_quality_weekly_rejection",
    ],
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def parse_money(value: Any) -> float:
    return float(str(value or "0").replace(" ", "").strip() or "0")


def parse_date(value: Any) -> date:
    return date.fromisoformat(str(value).strip())


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="bear_quality_m5_ema_slope50",
            label="Bear quality: M5 EMA short, D1/H1/H4 down, stronger candle and cost filters, fixed 2R",
            run_id="BT_A1_XAU_BEAR_QUALITY_M5_EMA_SLOPE50_RR2",
            tester_inputs=M5_QUALITY_BASE,
        ),
        a1.Variant(
            name="bear_quality_m5_ema_slope100",
            label="Bear quality: M5 EMA short, stronger H1/H4 slope, fixed 2R",
            run_id="BT_A1_XAU_BEAR_QUALITY_M5_EMA_SLOPE100_RR2",
            tester_inputs={
                **M5_QUALITY_BASE,
                "InpH1TrendMinSlopePoints": "100",
                "InpH4TrendMinSlopePoints": "100",
                "InpM5TrendMinSlopeAtr": "0.10",
                "InpM5TrendMaxDistanceAtr": "0.75",
            },
        ),
        a1.Variant(
            name="bear_quality_break_run_tight",
            label="Bear quality: tight break-and-run short, D1/H1/H4 down, fixed 2R",
            run_id="BT_A1_XAU_BEAR_QUALITY_BREAK_RUN_TIGHT_RR2",
            tester_inputs={
                **COMMON_BEAR_INPUTS,
                "InpSignalMode": "0",
                "InpUseH1TrendFilter": "true",
                "InpUseH4TrendFilter": "true",
                "InpH1TrendMinSlopePoints": "50",
                "InpH4TrendMinSlopePoints": "50",
                "InpMaxEstimatedCostR": "0.04",
                "InpStopFloorPoints": "350",
                "InpStopCeilingPoints": "1000",
                "InpBreakLookbackBars": "12",
                "InpBreakAtrMultiple": "0.30",
                "InpMinBreakDistanceAtr": "0.10",
                "InpMaxBreakDistanceAtr": "0.80",
                "InpMinRangeAtr": "0.55",
                "InpMinBodyFraction": "0.50",
                "InpShortCloseLocation": "0.30",
                "InpMinThreeBarMoveAtr": "0.40",
                "InpMaxThreeBarMoveAtr": "2.20",
            },
        ),
        a1.Variant(
            name="bear_quality_compression_break",
            label="Bear quality: compression then downside expansion, D1/H1/H4 down, fixed 2R",
            run_id="BT_A1_XAU_BEAR_QUALITY_COMPRESSION_BREAK_RR2",
            tester_inputs={
                **COMMON_BEAR_INPUTS,
                "InpSignalMode": "2",
                "InpUseH1TrendFilter": "true",
                "InpUseH4TrendFilter": "true",
                "InpH1TrendMinSlopePoints": "50",
                "InpH4TrendMinSlopePoints": "50",
                "InpMaxEstimatedCostR": "0.04",
                "InpStopFloorPoints": "350",
                "InpStopCeilingPoints": "1000",
                "InpCompressionLookbackBars": "8",
                "InpCompressionMaxRangeAtr": "0.80",
                "InpCompressionBreakAtrMultiple": "0.15",
                "InpMinRangeAtr": "0.50",
                "InpMinBodyFraction": "0.45",
                "InpShortCloseLocation": "0.35",
                "InpMinThreeBarMoveAtr": "0.25",
                "InpMaxThreeBarMoveAtr": "2.50",
            },
        ),
        a1.Variant(
            name="bear_quality_h4_pullback_d1bias",
            label="Bear quality: H4 pullback continuation with D1 bearish bias, fixed 2R",
            run_id="BT_A1_XAU_BEAR_QUALITY_H4_PULLBACK_D1BIAS_RR2",
            tester_inputs={
                **COMMON_BEAR_INPUTS,
                "InpSignalMode": "8",
                "InpUseH1TrendFilter": "false",
                "InpUseH4TrendFilter": "false",
                "InpMaxEstimatedCostR": "0.08",
                "InpStopFloorPoints": "350",
                "InpStopCeilingPoints": "2500",
            },
        ),
        a1.Variant(
            name="bear_quality_weekly_rejection",
            label="Bear quality: weekly resistance rejection inside bearish D1 state, fixed 2R",
            run_id="BT_A1_XAU_BEAR_QUALITY_WEEKLY_REJECTION_RR2",
            tester_inputs={
                **COMMON_BEAR_INPUTS,
                "InpSignalMode": "9",
                "InpUseH1TrendFilter": "false",
                "InpUseH4TrendFilter": "false",
                "InpMaxEstimatedCostR": "0.10",
                "InpStopFloorPoints": "350",
                "InpStopCeilingPoints": "2500",
            },
        ),
    ]


def variant_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    name = result["name"]
    trade_csv = Path(result["trade_csv"])
    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(read_trade_csv(trade_csv), start=2):
        entry_time = parse_dt(row["entry_time"])
        exit_time = parse_dt(row["exit_time"]) if str(row.get("exit_time", "")).strip() else entry_time
        rows.append(
            {
                "component": name,
                "source_id": name,
                "upstream_source_id": name,
                "upstream_component": "exact_mt5_bear_quality_first",
                "family_group": BEAR_FAMILY,
                "source_priority": BEAR_PRIORITY,
                "cell_id": name,
                "component_priority": 0,
                "variant_name": name,
                "entry_time": entry_time,
                "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                "exit_time": exit_time,
                "exit_date": exit_time.date(),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": parse_money(row.get("profit_float") or row.get("profit_aed")),
                "tickets": 1,
                "lots": parse_money(row.get("volume")),
                "source_csv": str(trade_csv),
                "source_row": ordinal,
            }
        )
    return rows


def standalone_decision(metrics: dict[str, Any], stress: dict[str, Any]) -> tuple[dict[str, bool], str]:
    checks = {
        "trades_ge_60": metrics["signals"] >= 60,
        "wr_ge_50": metrics["win_rate_pct"] >= 50.0,
        "wr_ge_45": metrics["win_rate_pct"] >= 45.0,
        "wl_ge_2": (metrics["avg_win_loss"] or 0.0) >= 2.0,
        "pf_ge_1p20": (metrics["profit_factor"] or 0.0) >= 1.20,
        "pf_ge_1p10": (metrics["profit_factor"] or 0.0) >= 1.10,
        "net_gt_0": metrics["net_usd"] > 0.0,
        "stress_wl_ge_1p90": (stress["avg_win_loss"] or 0.0) >= 1.90,
    }
    review = all(
        checks[key]
        for key in ["trades_ge_60", "wr_ge_50", "wl_ge_2", "pf_ge_1p20", "net_gt_0", "stress_wl_ge_1p90"]
    )
    watchlist = all(
        checks[key]
        for key in ["trades_ge_60", "wr_ge_45", "wl_ge_2", "pf_ge_1p10", "net_gt_0", "stress_wl_ge_1p90"]
    )
    if review:
        return checks, "BEAR_QUALITY_REVIEW_CANDIDATE"
    if watchlist:
        return checks, "BEAR_QUALITY_WATCHLIST_CLUE"
    if checks["wr_ge_45"] and not checks["wl_ge_2"]:
        return checks, "WR_UP_PAYOFF_FAIL"
    if checks["wl_ge_2"] and not checks["wr_ge_45"]:
        return checks, "PAYOFF_OK_WR_FAIL"
    if not checks["trades_ge_60"]:
        return checks, "LOW_SAMPLE_REJECT"
    return checks, "QUALITY_REJECT"


def standalone_row(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_exit_shape(rows)
    recent3 = period_stats(rows, RECENT3_START, RECENT3_END)
    may = period_stats(rows, MAY_START, MAY_END)
    checks, decision = standalone_decision(metrics, stress)
    return {
        "variant": name,
        "trades": metrics["signals"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "active": metrics["active_weekday_pct"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_wl": stress["avg_win_loss"],
        "positive_week_pct": shape["positive_week_pct"],
        "worst_week": shape["worst_week_usd"],
        "recent3_net": recent3["net_usd"],
        "may_net": may["net_usd"],
        "checks": checks,
        "decision": decision,
    }


def combined_decision(metrics: dict[str, Any], stress: dict[str, Any], shape: dict[str, Any], baseline_shape: dict[str, Any]) -> tuple[dict[str, bool], str]:
    checks = {
        "wr_ge_50": metrics["win_rate_pct"] >= 50.0,
        "wl_ge_2": (metrics["avg_win_loss"] or 0.0) >= 2.0,
        "active_ge_85": metrics["active_weekday_pct"] >= 85.0,
        "stress_wl_ge_1p90": (stress["avg_win_loss"] or 0.0) >= 1.90,
        "positive_weeks_improved": shape["positive_week_pct"] > baseline_shape["positive_week_pct"],
    }
    if all(checks.values()):
        return checks, "COMBINED_BEAR_QUALITY_REVIEW_CANDIDATE"
    if not checks["wr_ge_50"]:
        return checks, "REJECT_COMBINED_WR"
    if not checks["wl_ge_2"]:
        return checks, "REJECT_COMBINED_WL"
    if not checks["positive_weeks_improved"]:
        return checks, "REJECT_COMBINED_WEEKLY_SHAPE"
    return checks, "REJECT_COMBINED_GATE"


def combined_row(
    name: str,
    kept: list[dict[str, Any]],
    baseline_shape: dict[str, Any],
    score: dict[str, Any],
    decision: str,
) -> dict[str, Any]:
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    stress = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_exit_shape(kept)
    recent3 = period_stats(kept, RECENT3_START, RECENT3_END)
    may = period_stats(kept, MAY_START, MAY_END)
    return {
        "combo": name,
        "signals": metrics["signals"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "active": metrics["active_weekday_pct"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_wl": stress["avg_win_loss"],
        "positive_week_pct": shape["positive_week_pct"],
        "positive_week_delta_pp": round(shape["positive_week_pct"] - baseline_shape["positive_week_pct"], 2),
        "worst_week": shape["worst_week_usd"],
        "recent3_net": recent3["net_usd"],
        "may_net": may["net_usd"],
        "new_trades_kept": score["new_trades_kept"],
        "new_net_kept": score["new_net_kept"],
        "red_weeks_touched": score["red_weeks_touched"],
        "red_weeks_flipped": score["red_weeks_flipped"],
        "red_weeks_worsened": score["red_weeks_worsened"],
        "new_net_in_red_weeks": score["new_net_in_red_weeks"],
        "decision": decision,
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Bear Quality-First Exact MT5 Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Standalone Bear Quality Rows",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Worst week | Recent3 | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalone_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | "
            f"{row['worst_week']:.2f} | {row['recent3_net']:.2f} | `{row['decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Combined With Uptrend Baseline",
            "",
            "| Combo | Signals | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Delta pp | Worst week | Recent3 | May | New kept | New net | Red touched | Red flipped | Red worsened | New red net | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in [payload["baseline_row"], *payload["rows"]]:
        lines.append(
            f"| `{row['combo']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | "
            f"{row['positive_week_delta_pp']:.2f} | {row['worst_week']:.2f} | {row['recent3_net']:.2f} | "
            f"{row['may_net']:.2f} | {row['new_trades_kept']} | {row['new_net_kept']:.2f} | "
            f"{row['red_weeks_touched']} | {row['red_weeks_flipped']} | {row['red_weeks_worsened']} | "
            f"{row['new_net_in_red_weeks']:.2f} | `{row['decision']}` |"
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 quality-first bear probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(BASELINE_KEPT)

    a1.VARIANTS = build_variants()
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.json"
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

    baseline = read_composition_csv(BASELINE_KEPT)
    baseline_shape = weekly_exit_shape(baseline)
    baseline_weekly = weekly_pnl(baseline)
    baseline_row = baseline_result_row(baseline, baseline_shape)
    rows_by_name = {result["name"]: variant_rows(result) for result in mt5_payload["variants"]}
    standalone_rows = [standalone_row(name, rows) for name, rows in rows_by_name.items()]

    outputs = {
        "md": str(report_md),
        "json": str(report_json),
        "results_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"),
        "standalone_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_STANDALONE.csv"),
        "mt5_components_md": str(mt5_report_md),
        "mt5_components_json": str(mt5_report_json),
    }

    rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for combo_name, names in COMBOS.items():
        additions = [row for name in names for row in rows_by_name[name]]
        kept, dropped = dedupe_signals(baseline + additions)
        kept_new = source_rows(kept, set(names))
        combined_weekly = weekly_pnl(kept)
        score = red_week_score(baseline_weekly, combined_weekly, kept_new)
        score.update(
            {
                "new_trades_raw": len(additions),
                "new_trades_kept": len(kept_new),
                "new_trades_dropped": len([row for row in dropped if row.get("source_id") in set(names)]),
                "new_net_kept": round(sum(float(row["pnl_usd"]) for row in kept_new), 2),
            }
        )
        metrics = summary_metrics(kept, market_days=MARKET_DAYS)
        stress = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
        shape = weekly_exit_shape(kept)
        checks, decision = combined_decision(metrics, stress, shape, baseline_shape)
        row = combined_row(combo_name, kept, baseline_shape, score, decision)
        rows.append(row)

        kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combo_name}_KEPT.csv"
        dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combo_name}_DROPPED.csv"
        write_signal_csv(kept_csv, kept)
        write_signal_csv(dropped_csv, dropped)
        outputs[f"{combo_name}_kept_csv"] = str(kept_csv)
        outputs[f"{combo_name}_dropped_csv"] = str(dropped_csv)
        details.append({"combo": combo_name, "variant_names": names, "checks": checks, "score": score, "row": row})

    with Path(outputs["results_csv"]).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with Path(outputs["standalone_csv"]).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[key for key in standalone_rows[0].keys() if key != "checks"])
        writer.writeheader()
        for row in standalone_rows:
            writer.writerow({key: value for key, value in row.items() if key != "checks"})

    combined_hits = [row for row in rows if row["decision"] == "COMBINED_BEAR_QUALITY_REVIEW_CANDIDATE"]
    review_hits = [row for row in standalone_rows if row["decision"] == "BEAR_QUALITY_REVIEW_CANDIDATE"]
    watchlist_hits = [row for row in standalone_rows if row["decision"] == "BEAR_QUALITY_WATCHLIST_CLUE"]
    if combined_hits:
        status = "BEAR_QUALITY_COMBINED_REVIEW_CANDIDATE"
        best = max(combined_hits, key=lambda row: (row["positive_week_delta_pp"], row["wr"], row["net"]))
        interpretation = f"`{best['combo']}` passed the combined quality gate. Freeze it and request review before any demo discussion."
    elif review_hits:
        status = "BEAR_QUALITY_STANDALONE_REVIEW_CANDIDATE"
        best = max(review_hits, key=lambda row: (row["wr"], row["wl"] or 0.0, row["net"]))
        interpretation = (
            f"`{best['variant']}` passed the standalone quality review gate: {best['trades']} trades, "
            f"WR {best['wr']:.2f}%, W/L {best['wl'] or 0.0:.4f}, PF {best['pf'] or 0.0:.4f}, "
            f"net {best['net']:.2f} USD. Combined gate still needs separate review."
        )
    elif watchlist_hits:
        status = "BEAR_QUALITY_WATCHLIST_CLUE_NO_COMBINED_SURVIVOR"
        best = max(watchlist_hits, key=lambda row: (row["wr"], row["wl"] or 0.0, row["net"]))
        interpretation = (
            f"`{best['variant']}` is a quality watchlist clue, not a review candidate: {best['trades']} trades, "
            f"WR {best['wr']:.2f}%, W/L {best['wl'] or 0.0:.4f}, PF {best['pf'] or 0.0:.4f}, "
            f"net {best['net']:.2f} USD. Do not tune hours from this output."
        )
    else:
        status = "NO_BEAR_QUALITY_FIRST_HIT"
        best = max(standalone_rows, key=lambda row: (row["wr"], row["wl"] or 0.0, row["net"]))
        interpretation = (
            f"No quality-first bear variant reached even the watchlist gate. Best WR row was `{best['variant']}`: "
            f"{best['trades']} trades, WR {best['wr']:.2f}%, W/L {best['wl'] or 0.0:.4f}, "
            f"PF {best['pf'] or 0.0:.4f}, net {best['net']:.2f} USD."
        )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "baseline_row": baseline_row,
        "standalone_rows": standalone_rows,
        "rows": rows,
        "details": details,
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_component_details": [
            {
                "variant": result["name"],
                "trade_rows": len(rows_by_name[result["name"]]),
                "mt5_result": result,
                "guard_counts": guard_counts(result),
            }
            for result in mt5_payload["variants"]
        ],
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "standalone": standalone_rows, "combined": rows, "report": str(report_md)}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
