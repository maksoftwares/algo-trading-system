from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times, week_start
from analyze_a1_owner_goal_step3_portfolio_composition import (
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    parse_dt,
    rel,
    summary_metrics,
)
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
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_PREREG_2026_07_07.md"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv"
OUTPUT_STEM = "A1_XAU_NONUPTREND_RANGE_FADE_RED_WEEK_EXACT_202207_202606"
TAG = "OWNER_GOAL_NONUPTREND_RANGE_FADE_202207_202606"

NONUP_PRIORITY = 90
NONUP_FAMILY = "nonuptrend_range_fade_red_week"

COMMON_NONUP_INPUTS = {
    "InpDirectionMode": "0",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpD1SupportStateGateMode": "2",
    "InpD1SupportStateEmaPeriod": "20",
    "InpD1SupportStateSlopeLagBars": "5",
    "InpBlockedEntryDayHoursCsv": "5:20",
}

COMBOS = {
    "nonup_daily_extreme_rr2_only": ["nonup_daily_extreme_rr2"],
    "nonup_prior_day_reversal_rr2_only": ["nonup_prior_day_reversal_rr2"],
    "nonup_orrev_london_rr2_only": ["nonup_orrev_london_rr2"],
    "nonup_all_range_fade_rr2": [
        "nonup_daily_extreme_rr2",
        "nonup_prior_day_reversal_rr2",
        "nonup_orrev_london_rr2",
    ],
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def parse_money(value: Any) -> float:
    return float(str(value or "0").replace(" ", "").strip() or "0")


def parse_date(value: Any) -> date:
    return date.fromisoformat(str(value).strip())


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def guard_counts(result: dict[str, Any]) -> dict[str, Any]:
    rows = read_tsv(Path(result["order_csv"]))
    actions = Counter(row.get("action", "") for row in rows)
    reasons = Counter(row.get("reason", "") for row in rows if row.get("action") == "GUARD_BLOCK")
    return {
        "order_rows": len(rows),
        "actions": dict(actions),
        "guard_reasons": dict(reasons),
    }


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="nonup_daily_extreme_rr2",
            label="Non-uptrend daily-extreme reclaim, fixed 2R",
            run_id="BT_A1_XAU_NONUP_DAILY_EXTREME_RR2",
            tester_inputs={
                **COMMON_NONUP_INPUTS,
                "InpSignalMode": "11",
                "InpMaxEstimatedCostR": "0.15",
                "InpStopFloorPoints": "100",
                "InpStopCeilingPoints": "0",
                "InpMaxTradesPerDay": "24",
                "InpCooldownMinutes": "0",
                "InpOnePositionPerMagic": "false",
                "InpMaxOpenPositionsPerMagic": "16",
                "InpMinRangeAtr": "0.20",
                "InpLongCloseLocation": "0.58",
                "InpShortCloseLocation": "0.42",
                "InpDailyExtremeMinMoveAtr": "1.00",
                "InpDailyExtremeTouchAtr": "0.06",
                "InpDailyExtremeReclaimAtr": "0.10",
                "InpDailyExtremeStopBufferAtr": "0.10",
                "InpDailyExtremeMinBodyFraction": "0.25",
                "InpDailyExtremeMinBarsSinceOpen": "24",
                "InpDailyExtremeStartHour": "7",
                "InpDailyExtremeEndHour": "22",
            },
        ),
        a1.Variant(
            name="nonup_prior_day_reversal_rr2",
            label="Non-uptrend prior-day high/low reversal, fixed 2R",
            run_id="BT_A1_XAU_NONUP_PRIOR_DAY_REVERSAL_RR2",
            tester_inputs={
                **COMMON_NONUP_INPUTS,
                "InpSignalMode": "13",
                "InpPriorDayLevelMode": "1",
                "InpPriorDayLevelStartHour": "6",
                "InpPriorDayLevelEndHour": "22",
                "InpPriorDayLevelBreakAtr": "0.10",
                "InpPriorDayLevelTouchAtr": "0.05",
                "InpPriorDayLevelReclaimAtr": "0.10",
                "InpPriorDayLevelStopBufferAtr": "0.25",
                "InpPriorDayLevelMinBodyFraction": "0.35",
                "InpMaxEstimatedCostR": "0.10",
                "InpStopFloorPoints": "250",
                "InpStopCeilingPoints": "1400",
                "InpMaxTradesPerDay": "24",
                "InpCooldownMinutes": "0",
                "InpOnePositionPerMagic": "true",
            },
        ),
        a1.Variant(
            name="nonup_orrev_london_rr2",
            label="Non-uptrend London opening-range reversal, fixed 2R",
            run_id="BT_A1_XAU_NONUP_ORREV_LONDON_RR2",
            tester_inputs={
                **COMMON_NONUP_INPUTS,
                "InpSignalMode": "6",
                "InpOpeningRangeStartHour": "7",
                "InpOpeningRangeMinutes": "60",
                "InpOpeningTradeWindowHours": "5",
                "InpOpeningBreakAtrMultiple": "0.10",
                "InpReclaimAtrMultiple": "0.05",
                "InpMinRangeAtr": "0.40",
                "InpMinBodyFraction": "0.35",
                "InpLongCloseLocation": "0.60",
                "InpShortCloseLocation": "0.40",
                "InpStopAtrMultiple": "1.50",
                "InpStopFloorPoints": "250",
                "InpStopCeilingPoints": "1400",
                "InpMaxEstimatedCostR": "0.08",
                "InpMaxTradesPerDay": "24",
                "InpCooldownMinutes": "0",
                "InpOnePositionPerMagic": "true",
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
                "upstream_component": "exact_mt5_nonuptrend_range_fade",
                "family_group": NONUP_FAMILY,
                "source_priority": NONUP_PRIORITY,
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


def weekly_pnl(rows: list[dict[str, Any]]) -> dict[date, float]:
    enriched, _stats = enrich_exit_times(rows)
    by_week: dict[date, float] = defaultdict(float)
    for row in enriched:
        by_week[week_start(row["exit_date"])] += float(row["pnl_usd"])
    return {key: round(value, 2) for key, value in by_week.items()}


def source_rows(rows: list[dict[str, Any]], source_ids: set[str]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("source_id") in source_ids]


def red_week_score(
    baseline_weekly: dict[date, float],
    combined_weekly: dict[date, float],
    new_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    new_weekly = weekly_pnl(new_rows)
    red_weeks = {week for week, pnl in baseline_weekly.items() if pnl < 0.0}
    green_weeks = {week for week, pnl in baseline_weekly.items() if pnl > 0.0}
    touched_red = {week for week in red_weeks if abs(new_weekly.get(week, 0.0)) > 0.0}
    flipped = {week for week in red_weeks if baseline_weekly[week] < 0.0 and combined_weekly.get(week, 0.0) > 0.0}
    worsened = {week for week in red_weeks if combined_weekly.get(week, 0.0) < baseline_weekly[week]}
    return {
        "baseline_red_weeks": len(red_weeks),
        "baseline_green_weeks": len(green_weeks),
        "red_weeks_touched": len(touched_red),
        "red_weeks_flipped": len(flipped),
        "red_weeks_worsened": len(worsened),
        "new_net_in_red_weeks": round(sum(new_weekly.get(week, 0.0) for week in red_weeks), 2),
        "new_net_in_green_weeks": round(sum(new_weekly.get(week, 0.0) for week in green_weeks), 2),
        "new_net_in_nonbaseline_weeks": round(
            sum(value for week, value in new_weekly.items() if week not in red_weeks and week not in green_weeks), 2
        ),
        "flipped_weeks": [week.isoformat() for week in sorted(flipped)],
        "worsened_weeks": [week.isoformat() for week in sorted(worsened)],
    }


def pass_fail(
    metrics: dict[str, Any],
    stress_030: dict[str, Any],
    shape: dict[str, Any],
    baseline_shape: dict[str, Any],
    score: dict[str, Any],
) -> tuple[bool, dict[str, bool], str]:
    checks = {
        "wr_ge_50": metrics["win_rate_pct"] >= 50.0,
        "wl_ge_2": (metrics["avg_win_loss"] or 0.0) >= 2.0,
        "active_ge_85": metrics["active_weekday_pct"] >= 85.0,
        "stress_wl_ge_1p90": (stress_030["avg_win_loss"] or 0.0) >= 1.90,
        "positive_weeks_plus_3pp": shape["positive_week_pct"] - baseline_shape["positive_week_pct"] >= 3.0,
        "red_weeks_flipped_ge_8": score["red_weeks_flipped"] >= 8,
        "red_weeks_worsened_le_4": score["red_weeks_worsened"] <= 4,
        "new_red_week_net_ge_300": score["new_net_in_red_weeks"] >= 300.0,
        "worst_week_improved": shape["worst_week_usd"] > baseline_shape["worst_week_usd"],
    }
    if all(checks.values()):
        return True, checks, "PASS_REVIEW_REQUIRED"
    if not checks["wr_ge_50"] or not checks["wl_ge_2"]:
        return False, checks, "REJECT_BREAKS_CORE_SHAPE"
    if not checks["stress_wl_ge_1p90"]:
        return False, checks, "REJECT_FAILS_COST_STRESS"
    if not checks["positive_weeks_plus_3pp"]:
        return False, checks, "REJECT_WEEKLY_NOT_IMPROVED"
    if not checks["red_weeks_flipped_ge_8"]:
        return False, checks, "REJECT_INSUFFICIENT_RED_WEEK_REPAIR"
    if not checks["red_weeks_worsened_le_4"]:
        return False, checks, "REJECT_WORSENS_RED_WEEKS"
    if not checks["new_red_week_net_ge_300"]:
        return False, checks, "REJECT_RED_WEEK_NET_WEAK"
    if not checks["worst_week_improved"]:
        return False, checks, "REJECT_WORST_WEEK_NOT_IMPROVED"
    return False, checks, "REJECT_REPAIR_GATE"


def result_row(
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
        "new_net_in_green_weeks": score["new_net_in_green_weeks"],
        "decision": decision,
    }


def baseline_result_row(baseline: list[dict[str, Any]], baseline_shape: dict[str, Any]) -> dict[str, Any]:
    empty_score = {
        "new_trades_kept": 0,
        "new_net_kept": 0.0,
        "red_weeks_touched": 0,
        "red_weeks_flipped": 0,
        "red_weeks_worsened": 0,
        "new_net_in_red_weeks": 0.0,
        "new_net_in_green_weeks": 0.0,
    }
    return result_row("baseline_supportive_guard", baseline, baseline_shape, empty_score, "BASELINE")


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Non-Uptrend Range-Fade Red-Week Exact MT5 Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: three preregistered exact-MT5 non-uptrend range-fade variants, recomposed onto the corrected supportive-guard book. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Results",
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
    parser = argparse.ArgumentParser(description="Run exact-MT5 non-uptrend range-fade red-week probe.")
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
    result_by_name = {result["name"]: result for result in mt5_payload["variants"]}
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
        passed, checks, decision = pass_fail(metrics, stress, shape, baseline_shape, score)
        row = result_row(combo_name, kept, baseline_shape, score, decision)
        rows.append(row)

        enriched_kept, kept_exit_stats = enrich_exit_times(kept)
        kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combo_name}_KEPT.csv"
        dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combo_name}_DROPPED.csv"
        write_signal_csv(kept_csv, enriched_kept)
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
                "kept_exit_stats": kept_exit_stats,
                "kept_csv": str(kept_csv),
                "dropped_csv": str(dropped_csv),
            }
        )

    with Path(outputs["results_csv"]).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    passes = [detail for detail in details if detail["passed"]]
    if passes:
        status = "NONUPTREND_RANGE_FADE_REVIEW_CANDIDATE"
        best = max(
            passes,
            key=lambda item: (
                item["row"]["positive_week_delta_pp"],
                item["row"]["red_weeks_flipped"],
                item["row"]["new_net_in_red_weeks"],
            ),
        )
        interpretation = (
            f"`{best['combo']}` passed the preregistered red-week repair gates. Freeze the inputs and request review before any "
            "demo-spec discussion."
        )
    else:
        status = "NO_NONUPTREND_RANGE_FADE_RED_WEEK_SURVIVOR"
        best = max(
            details,
            key=lambda item: (
                item["row"]["positive_week_delta_pp"],
                item["row"]["red_weeks_flipped"],
                item["row"]["new_net_in_red_weeks"],
            ),
        )
        interpretation = (
            f"No non-uptrend range-fade combo passed. Best diagnostic by weekly repair was `{best['combo']}` with "
            f"{best['row']['positive_week_delta_pp']:.2f}pp positive-week delta, "
            f"{best['row']['red_weeks_flipped']} red weeks flipped, and "
            f"{best['row']['new_net_in_red_weeks']:.2f} USD new-source net in baseline red weeks. "
            "Per preregistration, do not tune hours or thresholds from this output; freeze or move to a different source class."
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
        "rows": rows,
        "details": details,
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "rows": rows, "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
