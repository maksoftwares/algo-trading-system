from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, parse_dt, rel, summary_metrics
from run_a1_h4_d1_geometry_v2_weekly_shape import (
    FROM_DATE,
    TO_DATE,
    read_composition_csv,
    sha256_file,
    weekly_exit_shape,
    write_signal_csv,
)
from run_a1_h4_d1_review_repair_exact import MAY_END, MAY_START, RECENT3_END, RECENT3_START, period_stats
from run_a1_nonuptrend_range_fade_red_week_probe import (
    baseline_result_row,
    guard_counts,
    pass_fail,
    red_week_score,
    result_row,
    source_rows,
    weekly_pnl,
)
from run_a1_v9_v10_rr2_stretch_probe import read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_DOWNTREND_SHORT_ENGINE_PREREG_2026_07_07.md"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv"
OUTPUT_STEM = "A1_XAU_DOWNTREND_SHORT_ENGINE_EXACT_202207_202606"
TAG = "OWNER_GOAL_DOWNTREND_SHORT_ENGINE_202207_202606"

DOWN_PRIORITY = 90
DOWN_FAMILY = "downtrend_short_engine"

COMMON_DOWN_INPUTS = {
    "InpDirectionMode": "2",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpD1SupportStateGateMode": "3",
    "InpD1SupportStateEmaPeriod": "20",
    "InpD1SupportStateSlopeLagBars": "5",
    "InpBlockedEntryDayHoursCsv": "5:20",
}

COMBOS = {
    "down_h4_d1_short_box2_atr80_only": ["down_h4_d1_short_box2_atr80"],
    "down_h1_d1_short_box2_atr80_only": ["down_h1_d1_short_box2_atr80"],
    "down_m5_ema_h1h4_short_rr2_only": ["down_m5_ema_h1h4_short_rr2"],
    "down_prior_day_cont_short_rr2_only": ["down_prior_day_cont_short_rr2"],
    "down_all_short_engines": [
        "down_h4_d1_short_box2_atr80",
        "down_h1_d1_short_box2_atr80",
        "down_m5_ema_h1h4_short_rr2",
        "down_prior_day_cont_short_rr2",
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
    h4_box_inputs = {
        **COMMON_DOWN_INPUTS,
        "InpSignalMode": "7",
        "InpUseH1TrendFilter": "false",
        "InpUseH4TrendFilter": "false",
        "InpMaxEstimatedCostR": "0.15",
        "InpStopCeilingPoints": "0",
        "InpStopCapPoints": "0",
        "InpMaxTradesPerDay": "6",
        "InpCooldownMinutes": "0",
        "InpOnePositionPerMagic": "false",
        "InpMaxOpenPositionsPerMagic": "32",
        "InpD1CompressionAtrPercentileMax": "80.00",
        "InpD1CompressionBoxDays": "2",
        "InpD1CompressionRangeMedianMax": "1.50",
        "InpD1CompressionH4MinBodyFraction": "0.35",
    }
    h1_box_inputs = {
        **h4_box_inputs,
        "InpSignalMode": "10",
    }
    return [
        a1.Variant(
            name="down_h4_d1_short_box2_atr80",
            label="Bearish-D1 H4/D1 compression expansion, short-only, box2 ATR80, fixed 2R",
            run_id="BT_A1_XAU_DOWN_H4_D1_SHORT_BOX2_ATR80_RR2",
            tester_inputs=h4_box_inputs,
        ),
        a1.Variant(
            name="down_h1_d1_short_box2_atr80",
            label="Bearish-D1 H1/D1 compression expansion, short-only, box2 ATR80, fixed 2R",
            run_id="BT_A1_XAU_DOWN_H1_D1_SHORT_BOX2_ATR80_RR2",
            tester_inputs=h1_box_inputs,
        ),
        a1.Variant(
            name="down_m5_ema_h1h4_short_rr2",
            label="Bearish-D1 M5 EMA trend continuation, H1/H4 aligned, short-only, fixed 2R",
            run_id="BT_A1_XAU_DOWN_M5_EMA_H1H4_SHORT_RR2",
            tester_inputs={
                **COMMON_DOWN_INPUTS,
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
            },
        ),
        a1.Variant(
            name="down_prior_day_cont_short_rr2",
            label="Bearish-D1 prior-day level continuation, short-only, fixed 2R",
            run_id="BT_A1_XAU_DOWN_PRIOR_DAY_CONT_SHORT_RR2",
            tester_inputs={
                **COMMON_DOWN_INPUTS,
                "InpSignalMode": "13",
                "InpUseH1TrendFilter": "false",
                "InpUseH4TrendFilter": "false",
                "InpPriorDayLevelMode": "0",
                "InpPriorDayLevelStartHour": "6",
                "InpPriorDayLevelEndHour": "22",
                "InpPriorDayLevelBreakAtr": "0.05",
                "InpPriorDayLevelTouchAtr": "0.05",
                "InpPriorDayLevelReclaimAtr": "0.10",
                "InpPriorDayLevelStopBufferAtr": "0.25",
                "InpPriorDayLevelMinBodyFraction": "0.35",
                "InpMaxEstimatedCostR": "0.08",
                "InpStopFloorPoints": "250",
                "InpStopCeilingPoints": "1400",
                "InpMaxTradesPerDay": "8",
                "InpCooldownMinutes": "15",
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
                "upstream_component": "exact_mt5_downtrend_short_engine",
                "family_group": DOWN_FAMILY,
                "source_priority": DOWN_PRIORITY,
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
        "diagnostic": (
            "STANDALONE_SHORT_CLUE"
            if metrics["signals"] >= 80 and metrics["net_usd"] > 0.0 and (metrics["avg_win_loss"] or 0.0) >= 2.0
            else "STANDALONE_REJECT"
        ),
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Downtrend Short Engine Exact MT5 Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: four preregistered bearish-D1 short-engine variants, recomposed onto the corrected supportive-guard uptrend baseline. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Combined Results",
        "",
        "| Combo | Signals | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Delta pp | Worst week | Recent3 | May | New kept | New net | Red touched | Red flipped | Red worsened | New red net | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
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

    lines.extend(["", "## Standalone Downtrend Rows", ""])
    lines.extend(
        [
            "| Variant | Trades | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Worst week | Recent3 | Diagnostic |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["standalone_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | "
            f"{row['worst_week']:.2f} | {row['recent3_net']:.2f} | `{row['diagnostic']}` |"
        )

    lines.extend(["", "## Pass-Fail Checks", ""])
    for detail in payload["details"]:
        lines.extend(["", f"### `{detail['combo']}`", ""])
        for key, value in detail["checks"].items():
            lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## MT5 Guard Counts",
            "",
            "| Variant | Trades | Orders | d1_support_state_gate | Other guard blocks |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for detail in payload["mt5_component_details"]:
        reasons = detail["guard_counts"]["guard_reasons"]
        d1_gate = reasons.get("d1_support_state_gate", 0)
        other = sum(count for reason, count in reasons.items() if reason != "d1_support_state_gate")
        lines.append(
            f"| `{detail['variant']}` | {detail['trade_rows']} | {detail['guard_counts']['order_rows']} | {d1_gate} | {other} |"
        )

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 bearish-D1 downtrend short-engine probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(BASELINE_KEPT)

    variants = build_variants()
    a1.VARIANTS = variants

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
    mt5_component_details = [
        {
            "variant": result["name"],
            "trade_rows": len(rows_by_name[result["name"]]),
            "mt5_result": result,
            "guard_counts": guard_counts(result),
        }
        for result in mt5_payload["variants"]
    ]

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
        from analyze_a1_owner_goal_step3_portfolio_composition import dedupe_signals

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
        passed, checks, decision = pass_fail(metrics, stress, shape, baseline_shape, score)
        row = result_row(combo_name, kept, baseline_shape, score, decision)
        rows.append(row)

        kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combo_name}_KEPT.csv"
        dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combo_name}_DROPPED.csv"
        write_signal_csv(kept_csv, kept)
        write_signal_csv(dropped_csv, dropped)
        outputs[f"{combo_name}_kept_csv"] = str(kept_csv)
        outputs[f"{combo_name}_dropped_csv"] = str(dropped_csv)

        details.append(
            {
                "combo": combo_name,
                "variant_names": names,
                "passed": passed,
                "checks": checks,
                "score": score,
                "row": row,
                "kept_csv": str(kept_csv),
                "dropped_csv": str(dropped_csv),
            }
        )

    with Path(outputs["results_csv"]).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with Path(outputs["standalone_csv"]).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(standalone_rows[0].keys()))
        writer.writeheader()
        writer.writerows(standalone_rows)

    passes = [detail for detail in details if detail["passed"]]
    standalone_clues = [row for row in standalone_rows if row["diagnostic"] == "STANDALONE_SHORT_CLUE"]
    if passes:
        status = "DOWNTREND_SHORT_ENGINE_REVIEW_CANDIDATE"
        best = max(
            passes,
            key=lambda item: (
                item["row"]["positive_week_delta_pp"],
                item["row"]["red_weeks_flipped"],
                item["row"]["new_net_in_red_weeks"],
            ),
        )
        interpretation = (
            f"`{best['combo']}` passed the preregistered combined-regime gates. Freeze the inputs and request review before "
            "any demo-spec discussion."
        )
    elif standalone_clues:
        status = "DOWNTREND_SHORT_STANDALONE_CLUE_NO_COMBINED_SURVIVOR"
        best_standalone = max(standalone_clues, key=lambda row: (row["net"], row["trades"], row["wl"] or 0.0))
        best_combo = max(
            details,
            key=lambda item: (
                item["row"]["positive_week_delta_pp"],
                item["row"]["red_weeks_flipped"],
                item["row"]["new_net_in_red_weeks"],
            ),
        )
        interpretation = (
            f"No combined uptrend+downtrend row passed, but `{best_standalone['variant']}` is a standalone bearish clue "
            f"({best_standalone['trades']} trades, WR {best_standalone['wr']:.2f}%, W/L {best_standalone['wl'] or 0.0:.4f}, "
            f"net {best_standalone['net']:.2f} USD). Best combined diagnostic was `{best_combo['combo']}` with "
            f"{best_combo['row']['positive_week_delta_pp']:.2f}pp positive-week delta. Review only if the owner accepts a "
            "separate low-frequency downtrend branch; do not tune hours from this output."
        )
    else:
        status = "NO_DOWNTREND_SHORT_ENGINE_SURVIVOR"
        best = max(
            details,
            key=lambda item: (
                item["row"]["positive_week_delta_pp"],
                item["row"]["red_weeks_flipped"],
                item["row"]["new_net_in_red_weeks"],
            ),
        )
        interpretation = (
            f"No bearish-D1 short-engine combo passed. Best diagnostic was `{best['combo']}` with "
            f"{best['row']['positive_week_delta_pp']:.2f}pp positive-week delta, "
            f"{best['row']['red_weeks_flipped']} red weeks flipped, and "
            f"{best['row']['new_net_in_red_weeks']:.2f} USD downtrend-source net in baseline red weeks. "
            "Per preregistration, freeze this branch or move to a materially different short-engine design."
        )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "period": f"{FROM_DATE} -> {TO_DATE}",
        "baseline_name": "supportive_guard_session_parity",
        "baseline_csv": str(BASELINE_KEPT),
        "baseline_shape": baseline_shape,
        "baseline_row": baseline_row,
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_component_details": mt5_component_details,
        "standalone_rows": standalone_rows,
        "rows": rows,
        "details": details,
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "rows": rows, "standalone": standalone_rows, "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
