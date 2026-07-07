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
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_BEAR_ENGINE_IMPROVEMENT_PREREG_2026_07_07.md"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv"
OUTPUT_STEM = "A1_XAU_BEAR_ENGINE_IMPROVEMENT_EXACT_202207_202606"
TAG = "OWNER_GOAL_BEAR_ENGINE_IMPROVEMENT_202207_202606"

REFERENCE_TRADES = 438
REFERENCE_WR = 33.11
REFERENCE_NET = 137.34

BEAR_PRIORITY = 90
BEAR_FAMILY = "bear_engine_improvement"

COMMON_BEAR_INPUTS = {
    "InpDirectionMode": "2",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpD1SupportStateGateMode": "3",
    "InpD1SupportStateEmaPeriod": "20",
    "InpD1SupportStateSlopeLagBars": "5",
    "InpBlockedEntryDayHoursCsv": "5:20",
}

M5_EMA_BASE = {
    **COMMON_BEAR_INPUTS,
    "InpSignalMode": "5",
    "InpUseH1TrendFilter": "true",
    "InpUseH4TrendFilter": "true",
    "InpH1TrendMinSlopePoints": "0",
    "InpH4TrendMinSlopePoints": "0",
    "InpMaxEstimatedCostR": "0.05",
    "InpM5TrendEmaFastPeriod": "8",
    "InpM5TrendEmaSlowPeriod": "21",
    "InpM5TrendSlopeBars": "3",
    "InpM5TrendMinSlopeAtr": "0.03",
    "InpM5TrendMaxDistanceAtr": "1.20",
    "InpMinRangeAtr": "0.35",
    "InpMinBodyFraction": "0.30",
    "InpShortCloseLocation": "0.42",
    "InpMinThreeBarMoveAtr": "0.10",
    "InpMaxTradesPerDay": "24",
    "InpCooldownMinutes": "0",
}

COMBOS = {
    "bear_m5_ema_h1_only_rr2_morefreq_only": ["bear_m5_ema_h1_only_rr2_morefreq"],
    "bear_m5_ema_h1h4_rr2_strict_body_only": ["bear_m5_ema_h1h4_rr2_strict_body"],
    "bear_m5_ema_h1h4_rr2_fast_slope_only": ["bear_m5_ema_h1h4_rr2_fast_slope"],
    "bear_ema_pullback_h1h4_rr2_only": ["bear_ema_pullback_h1h4_rr2"],
    "bear_break_run_h1h4_rr2_only": ["bear_break_run_h1h4_rr2"],
    "bear_all_improvement_cells": [
        "bear_m5_ema_h1_only_rr2_morefreq",
        "bear_m5_ema_h1h4_rr2_strict_body",
        "bear_m5_ema_h1h4_rr2_fast_slope",
        "bear_ema_pullback_h1h4_rr2",
        "bear_break_run_h1h4_rr2",
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
            name="bear_m5_ema_h1_only_rr2_morefreq",
            label="Bear improvement: M5 EMA short, bearish D1 + H1 only, fixed 2R",
            run_id="BT_A1_XAU_BEAR_M5_EMA_H1_ONLY_RR2",
            tester_inputs={**M5_EMA_BASE, "InpUseH4TrendFilter": "false"},
        ),
        a1.Variant(
            name="bear_m5_ema_h1h4_rr2_strict_body",
            label="Bear improvement: M5 EMA short, strict candle quality, fixed 2R",
            run_id="BT_A1_XAU_BEAR_M5_EMA_H1H4_STRICT_BODY_RR2",
            tester_inputs={
                **M5_EMA_BASE,
                "InpMinRangeAtr": "0.50",
                "InpMinBodyFraction": "0.45",
                "InpShortCloseLocation": "0.35",
                "InpMinThreeBarMoveAtr": "0.25",
            },
        ),
        a1.Variant(
            name="bear_m5_ema_h1h4_rr2_fast_slope",
            label="Bear improvement: M5 EMA short, faster bearish slope, fixed 2R",
            run_id="BT_A1_XAU_BEAR_M5_EMA_H1H4_FAST_SLOPE_RR2",
            tester_inputs={
                **M5_EMA_BASE,
                "InpM5TrendMinSlopeAtr": "0.08",
                "InpM5TrendMaxDistanceAtr": "1.00",
            },
        ),
        a1.Variant(
            name="bear_ema_pullback_h1h4_rr2",
            label="Bear improvement: EMA pullback short, bearish D1 + H1/H4, fixed 2R",
            run_id="BT_A1_XAU_BEAR_EMA_PULLBACK_H1H4_RR2",
            tester_inputs={
                **COMMON_BEAR_INPUTS,
                "InpSignalMode": "1",
                "InpUseH1TrendFilter": "true",
                "InpUseH4TrendFilter": "true",
                "InpH1TrendMinSlopePoints": "0",
                "InpH4TrendMinSlopePoints": "0",
                "InpMaxEstimatedCostR": "0.05",
                "InpPullbackEmaPeriod": "20",
                "InpPullbackTouchAtr": "0.25",
                "InpMinRangeAtr": "0.35",
                "InpMinBodyFraction": "0.30",
                "InpShortCloseLocation": "0.42",
                "InpMinThreeBarMoveAtr": "0.10",
                "InpMaxTradesPerDay": "24",
                "InpCooldownMinutes": "0",
            },
        ),
        a1.Variant(
            name="bear_break_run_h1h4_rr2",
            label="Bear improvement: break-and-run short, bearish D1 + H1/H4, fixed 2R",
            run_id="BT_A1_XAU_BEAR_BREAK_RUN_H1H4_RR2",
            tester_inputs={
                **COMMON_BEAR_INPUTS,
                "InpSignalMode": "0",
                "InpUseH1TrendFilter": "true",
                "InpUseH4TrendFilter": "true",
                "InpH1TrendMinSlopePoints": "0",
                "InpH4TrendMinSlopePoints": "0",
                "InpMaxEstimatedCostR": "0.05",
                "InpBreakLookbackBars": "12",
                "InpBreakAtrMultiple": "0.20",
                "InpMinRangeAtr": "0.35",
                "InpMinBodyFraction": "0.30",
                "InpShortCloseLocation": "0.42",
                "InpMinThreeBarMoveAtr": "0.10",
                "InpMaxTradesPerDay": "24",
                "InpCooldownMinutes": "0",
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
                "upstream_component": "exact_mt5_bear_engine_improvement",
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


def standalone_row(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_exit_shape(rows)
    recent3 = period_stats(rows, RECENT3_START, RECENT3_END)
    may = period_stats(rows, MAY_START, MAY_END)
    checks = {
        "more_trades_than_reference": metrics["signals"] > REFERENCE_TRADES,
        "wr_gt_reference": metrics["win_rate_pct"] > REFERENCE_WR,
        "wl_ge_2": (metrics["avg_win_loss"] or 0.0) >= 2.0,
        "pf_gt_1p05": (metrics["profit_factor"] or 0.0) > 1.05,
        "net_gt_reference": metrics["net_usd"] > REFERENCE_NET,
        "stress_wl_ge_1p90": (stress["avg_win_loss"] or 0.0) >= 1.90,
    }
    if all(checks.values()):
        decision = "BEAR_IMPROVEMENT_CLUE"
    elif checks["more_trades_than_reference"] and checks["wr_gt_reference"]:
        decision = "MORE_TRADES_WR_UP_BUT_FAILS_PAYOFF_OR_NET"
    elif checks["wr_gt_reference"]:
        decision = "WR_UP_BUT_NOT_MORE_TRADES"
    elif checks["more_trades_than_reference"]:
        decision = "MORE_TRADES_BUT_WR_NOT_UP"
    else:
        decision = "NO_BEAR_IMPROVEMENT"
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
        return checks, "COMBINED_BEAR_REVIEW_CANDIDATE"
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
        "new_trades_kept": score["new_trades_kept"],
        "new_net_kept": score["new_net_kept"],
        "red_weeks_flipped": score["red_weeks_flipped"],
        "red_weeks_worsened": score["red_weeks_worsened"],
        "new_net_in_red_weeks": score["new_net_in_red_weeks"],
        "decision": decision,
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Bear Engine Improvement Exact MT5 Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Standalone Bear Rows",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Recent3 | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalone_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | "
            f"{row['recent3_net']:.2f} | `{row['decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Combined With Uptrend Baseline",
            "",
            "| Combo | Signals | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Delta pp | Recent3 | New kept | New net | Red flipped | Red worsened | New red net | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in [payload["baseline_row"], *payload["rows"]]:
        lines.append(
            f"| `{row['combo']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | "
            f"{row['positive_week_delta_pp']:.2f} | {row['recent3_net']:.2f} | "
            f"{row['new_trades_kept']} | {row['new_net_kept']:.2f} | {row['red_weeks_flipped']} | "
            f"{row['red_weeks_worsened']} | {row['new_net_in_red_weeks']:.2f} | `{row['decision']}` |"
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 bear-engine improvement probe.")
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

    standalone_hits = [row for row in standalone_rows if row["decision"] == "BEAR_IMPROVEMENT_CLUE"]
    combined_hits = [row for row in rows if row["decision"] == "COMBINED_BEAR_REVIEW_CANDIDATE"]
    if combined_hits:
        status = "BEAR_ENGINE_COMBINED_REVIEW_CANDIDATE"
        best = max(combined_hits, key=lambda row: (row["positive_week_delta_pp"], row["wr"], row["net"]))
        interpretation = f"`{best['combo']}` passed the combined gate. Freeze it and request review before demo discussion."
    elif standalone_hits:
        status = "BEAR_ENGINE_STANDALONE_IMPROVEMENT_NO_COMBINED_SURVIVOR"
        best = max(standalone_hits, key=lambda row: (row["trades"], row["wr"], row["net"]))
        interpretation = (
            f"`{best['variant']}` improved the standalone bear clue on trades and WR while preserving payoff. "
            "No combined row passed, so this remains research-only."
        )
    else:
        status = "NO_BEAR_ENGINE_IMPROVEMENT"
        best = max(standalone_rows, key=lambda row: (row["wr"] > REFERENCE_WR, row["trades"], row["net"]))
        interpretation = (
            f"No variant beat the reference on both more trades and better WR while preserving payoff. "
            f"Best diagnostic was `{best['variant']}`: {best['trades']} trades, WR {best['wr']:.2f}%, "
            f"W/L {best['wl'] or 0.0:.4f}, net {best['net']:.2f} USD. Do not tune hours from this output."
        )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "reference": {"variant": "down_m5_ema_h1h4_short_rr2", "trades": REFERENCE_TRADES, "wr": REFERENCE_WR, "net": REFERENCE_NET},
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
