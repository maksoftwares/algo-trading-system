from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
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
from run_a1_h4_d1_geometry_v2_weekly_shape import (
    FROM_DATE,
    TO_DATE,
    read_composition_csv,
    sha256_file,
    weekly_exit_shape,
    write_signal_csv,
)
from run_a1_h4_d1_review_repair_exact import RECENT3_END, RECENT3_START, period_stats
from run_a1_nonuptrend_range_fade_red_week_probe import red_week_score, weekly_pnl
from run_a1_v9_v10_rr2_stretch_probe import read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_SHORT_HEDGE_PREREG_2026_07_08.md"
FREEZE = PHASE1_ROOT / "docs" / "A1_XAU_BEAR_CONTINUATION_FAMILY_FREEZE_2026_07_08.md"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv"
OUTPUT_STEM = "A1_XAU_SHORT_HEDGE_EXACT_202207_202606"
TAG = "OWNER_GOAL_SHORT_HEDGE_202207_202606"
SHORT_PRIORITY = 88
SHORT_FAMILY = "xau_short_hedge"
LONG_BOX_SOURCE = "h4_d1_long_best_box2_atr80"
Q2_START = date(2026, 4, 1)
Q2_END = date(2026, 6, 30)


COMMON_SHORT_INPUTS = {
    "InpDirectionMode": "2",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.05",
    "InpMaxTradesPerDay": "24",
    "InpCooldownMinutes": "0",
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def parse_money(value: Any) -> float:
    return float(str(value or "0").replace(" ", "").strip() or "0")


def parse_date(value: Any) -> date:
    return date.fromisoformat(str(value).strip())


def ge(value: float | None, threshold: float) -> bool:
    return (value or 0.0) >= threshold


def gt(value: float | None, threshold: float) -> bool:
    return (value or 0.0) > threshold


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="short_hedge_v1_break_run_control",
            label="Short hedge V1 control: D1 bearish + H1/H4 break-and-run short, fixed 2R",
            run_id="BT_A1_XAU_SHORT_HEDGE_V1_BREAK_RUN_CONTROL",
            tester_inputs={
                **COMMON_SHORT_INPUTS,
                "InpSignalMode": "0",
                "InpD1SupportStateGateMode": "3",
                "InpD1SupportStateEmaPeriod": "20",
                "InpD1SupportStateSlopeLagBars": "5",
                "InpUseH1TrendFilter": "true",
                "InpUseH4TrendFilter": "true",
                "InpH1TrendMinSlopePoints": "0",
                "InpH4TrendMinSlopePoints": "0",
                "InpBreakLookbackBars": "12",
                "InpBreakAtrMultiple": "0.20",
                "InpMinRangeAtr": "0.35",
                "InpMinBodyFraction": "0.30",
                "InpShortCloseLocation": "0.42",
                "InpMinThreeBarMoveAtr": "0.10",
            },
        ),
        a1.Variant(
            name="short_hedge_v2_breakdown_retest",
            label="Short hedge V2: D1 bearish + H1/H4 breakdown-retest short, fixed 2R",
            run_id="BT_A1_XAU_SHORT_HEDGE_V2_BREAKDOWN_RETEST",
            tester_inputs={
                **COMMON_SHORT_INPUTS,
                "InpSignalMode": "15",
                "InpD1SupportStateGateMode": "3",
                "InpD1SupportStateEmaPeriod": "20",
                "InpD1SupportStateSlopeLagBars": "5",
                "InpUseH1TrendFilter": "true",
                "InpUseH4TrendFilter": "true",
                "InpH1TrendMinSlopePoints": "0",
                "InpH4TrendMinSlopePoints": "0",
                "InpShortCloseLocation": "0.42",
                "InpBearRetestLookbackBars": "10",
                "InpBearRetestSupportLookbackBars": "12",
                "InpBearRetestBreakAtr": "0.10",
                "InpBearRetestTouchAtr": "0.05",
                "InpBearRetestReclaimAtr": "0.05",
                "InpBearRetestStopBufferAtr": "0.25",
                "InpBearRetestMinBodyFraction": "0.30",
            },
        ),
        a1.Variant(
            name="short_hedge_v3_prior_high_sweep_reclaim",
            label="Short hedge V3: D1 non-up prior-day-high sweep/reclaim short, fixed 2R",
            run_id="BT_A1_XAU_SHORT_HEDGE_V3_PRIOR_HIGH_SWEEP_RECLAIM",
            tester_inputs={
                **COMMON_SHORT_INPUTS,
                "InpSignalMode": "16",
                "InpD1SupportStateGateMode": "4",
                "InpD1SupportStateEmaPeriod": "20",
                "InpD1SupportStateSlopeLagBars": "5",
                "InpUseH1TrendFilter": "false",
                "InpUseH4TrendFilter": "false",
                "InpBearSweepReclaimBars": "2",
                "InpBearSweepTouchAtr": "0.05",
                "InpBearSweepReclaimAtr": "0.05",
                "InpBearSweepStopBufferAtr": "0.25",
                "InpBearSweepMinBodyFraction": "0.20",
            },
        ),
    ]


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def guard_counts(result: dict[str, Any]) -> dict[str, Any]:
    rows = read_tsv(Path(result["order_csv"]))
    reasons = Counter(row.get("reason", "") for row in rows if row.get("action") == "GUARD_BLOCK")
    actions = Counter(row.get("action", "") for row in rows)
    return {
        "order_rows": len(rows),
        "actions": dict(actions),
        "guard_reasons": dict(reasons),
    }


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
                "upstream_component": "exact_mt5_short_hedge",
                "family_group": SHORT_FAMILY,
                "source_priority": SHORT_PRIORITY,
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


def contribution_stats(rows: list[dict[str, Any]], net: float) -> dict[str, Any]:
    if net <= 0.0:
        return {"top1_share_pct": None, "top5_share_pct": None, "top_day_share_pct": None, "top_day_net": 0.0}
    wins = sorted((float(row["pnl_usd"]) for row in rows if float(row["pnl_usd"]) > 0.0), reverse=True)
    by_day: dict[date, float] = defaultdict(float)
    for row in rows:
        by_day[row["entry_date"]] += float(row["pnl_usd"])
    top_day_net = max(by_day.values(), default=0.0)
    return {
        "top1_share_pct": round(100.0 * (wins[0] if wins else 0.0) / net, 2),
        "top5_share_pct": round(100.0 * sum(wins[:5]) / net, 2),
        "top_day_share_pct": round(100.0 * max(top_day_net, 0.0) / net, 2),
        "top_day_net": round(top_day_net, 2),
    }


def loss_reduction_pct(old_net: float, new_net: float) -> float | None:
    if old_net >= 0.0:
        return None
    return round(100.0 * (new_net - old_net) / abs(old_net), 2)


def standalone_decision(
    metrics: dict[str, Any],
    stress: dict[str, Any],
    q2: dict[str, Any],
    concentration: dict[str, Any],
) -> tuple[dict[str, bool], str]:
    checks = {
        "stress_pf_ge_1p15": ge(stress["profit_factor"], 1.15),
        "raw_wl_ge_2": ge(metrics["avg_win_loss"], 2.0),
        "stress_wl_ge_1p90": ge(stress["avg_win_loss"], 1.90),
        "stress_net_gt_0": stress["net_usd"] > 0.0,
        "q2_net_gt_0": q2["net_usd"] > 0.0,
        "trades_ge_200": metrics["signals"] >= 200,
        "top1_share_le_25": concentration["top1_share_pct"] is not None and concentration["top1_share_pct"] <= 25.0,
        "top_day_share_le_30": concentration["top_day_share_pct"] is not None and concentration["top_day_share_pct"] <= 30.0,
    }
    if all(checks.values()):
        return checks, "SHORT_HEDGE_STANDALONE_REVIEW_CANDIDATE"
    if not checks["q2_net_gt_0"]:
        return checks, "REJECT_NO_Q2_HEDGE"
    if not checks["stress_pf_ge_1p15"] or not checks["stress_net_gt_0"]:
        return checks, "REJECT_COST_STRESS"
    if not checks["raw_wl_ge_2"] or not checks["stress_wl_ge_1p90"]:
        return checks, "REJECT_PAYOFF_SHAPE"
    if not checks["trades_ge_200"]:
        return checks, "REJECT_TOO_SPARSE"
    if not checks["top1_share_le_25"] or not checks["top_day_share_le_30"]:
        return checks, "REJECT_CONCENTRATION"
    return checks, "REJECT_STANDALONE_HEDGE_GATE"


def standalone_row(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_exit_shape(rows)
    q2 = period_stats(rows, Q2_START, Q2_END)
    recent3 = period_stats(rows, RECENT3_START, RECENT3_END)
    concentration = contribution_stats(rows, metrics["net_usd"])
    checks, decision = standalone_decision(metrics, stress, q2, concentration)
    return {
        "variant": name,
        "trades": metrics["signals"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "active": metrics["active_weekday_pct"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_pf": stress["profit_factor"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_net": stress["net_usd"],
        "positive_week_pct": shape["positive_week_pct"],
        "worst_week": shape["worst_week_usd"],
        "q2_net": q2["net_usd"],
        "recent3_net": recent3["net_usd"],
        "top1_share_pct": concentration["top1_share_pct"],
        "top_day_share_pct": concentration["top_day_share_pct"],
        "decision": decision,
        "checks": checks,
    }


def combined_decision(
    metrics: dict[str, Any],
    stress: dict[str, Any],
    shape: dict[str, Any],
    baseline_shape: dict[str, Any],
    long_box_q2_reduction: float | None,
    long_box_q2_base_net: float,
    long_box_q2_with_short_net: float,
    baseline_recent3_net: float,
    combined_recent3_net: float,
) -> tuple[dict[str, bool], str]:
    if long_box_q2_base_net < 0.0:
        q2_defense_pass = long_box_q2_reduction is not None and long_box_q2_reduction >= 30.0
        recent3_defense_pass = True
    else:
        q2_defense_pass = long_box_q2_with_short_net > long_box_q2_base_net
        recent3_defense_pass = combined_recent3_net > baseline_recent3_net
    checks = {
        "wr_ge_48": metrics["win_rate_pct"] >= 48.0,
        "raw_wl_ge_2": ge(metrics["avg_win_loss"], 2.0),
        "stress_wl_ge_1p90": ge(stress["avg_win_loss"], 1.90),
        "pf_gt_1p50": gt(metrics["profit_factor"], 1.50),
        "positive_weeks_not_worse": shape["positive_week_pct"] >= baseline_shape["positive_week_pct"],
        "q2_defense_pass": q2_defense_pass,
        "recent3_defense_pass_when_q2_repair_na": recent3_defense_pass,
    }
    if all(checks.values()):
        return checks, "SHORT_HEDGE_COMBINED_REVIEW_CANDIDATE"
    if not checks["q2_defense_pass"]:
        return checks, "REJECT_NO_Q2_DEFENSE"
    if not checks["recent3_defense_pass_when_q2_repair_na"]:
        return checks, "REJECT_NO_RECENT3_DEFENSE"
    if not checks["wr_ge_48"] or not checks["raw_wl_ge_2"]:
        return checks, "REJECT_COMBINED_CORE_SHAPE"
    if not checks["stress_wl_ge_1p90"]:
        return checks, "REJECT_COMBINED_COST_STRESS"
    if not checks["positive_weeks_not_worse"]:
        return checks, "REJECT_COMBINED_WEEKLY_SHAPE"
    return checks, "REJECT_COMBINED_GATE"


def result_row(
    name: str,
    kept: list[dict[str, Any]],
    baseline_shape: dict[str, Any],
    score: dict[str, Any],
    long_box_q2_base: dict[str, Any],
    long_box_q2_with_short: dict[str, Any],
    decision: str,
) -> dict[str, Any]:
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    stress = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_exit_shape(kept)
    recent3 = period_stats(kept, RECENT3_START, RECENT3_END)
    reduction = loss_reduction_pct(long_box_q2_base["net_usd"], long_box_q2_with_short["net_usd"])
    q2_basis = "loss_reduction" if long_box_q2_base["net_usd"] < 0.0 else "positive_q2_addition_guarded_baseline_has_no_q2_long_box_loss"
    return {
        "combo": name,
        "signals": metrics["signals"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "active": metrics["active_weekday_pct"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_net": stress["net_usd"],
        "positive_week_pct": shape["positive_week_pct"],
        "positive_week_delta_pp": round(shape["positive_week_pct"] - baseline_shape["positive_week_pct"], 2),
        "worst_week": shape["worst_week_usd"],
        "recent3_net": recent3["net_usd"],
        "new_trades_kept": score["new_trades_kept"],
        "new_net_kept": score["new_net_kept"],
        "red_weeks_flipped": score["red_weeks_flipped"],
        "red_weeks_worsened": score["red_weeks_worsened"],
        "new_net_in_red_weeks": score["new_net_in_red_weeks"],
        "long_box_q2_base_net": long_box_q2_base["net_usd"],
        "long_box_q2_with_short_net": long_box_q2_with_short["net_usd"],
        "long_box_q2_loss_reduction_pct": reduction,
        "q2_defense_basis": q2_basis,
        "decision": decision,
    }


def baseline_row(baseline: list[dict[str, Any]], baseline_shape: dict[str, Any], long_box_q2: dict[str, Any]) -> dict[str, Any]:
    empty_score = {
        "new_trades_kept": 0,
        "new_net_kept": 0.0,
        "red_weeks_flipped": 0,
        "red_weeks_worsened": 0,
        "new_net_in_red_weeks": 0.0,
    }
    return result_row("baseline_supportive_guard", baseline, baseline_shape, empty_score, long_box_q2, long_box_q2, "BASELINE")


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Short Hedge Exact MT5 Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 short hedge work order. The prior bear-continuation family is frozen as a control; V2 and V3 are structural hedge tests. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Freeze note: `{rel(Path(payload['freeze_note']))}`",
        f"Freeze note SHA256: `{payload['freeze_note_sha256']}`",
        "",
        "## Standalone Short Hedge",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Net | Stress PF | Stress W/L | Stress net | Pos weeks% | Q2 net | Top1% | Top day% | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalone_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_pf'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['stress_030_net']:.2f} | {row['positive_week_pct']:.2f} | {row['q2_net']:.2f} | "
            f"{row['top1_share_pct'] or 0.0:.2f} | {row['top_day_share_pct'] or 0.0:.2f} | `{row['decision']}` |"
        )

    lines.extend(
        [
            "",
            "## Combined With Supportive-Guard Book",
            "",
        ]
    )
    if payload["long_box_q2"]["net_usd"] >= 0.0:
        lines.extend(
            [
                "Q2 repair note: the current guarded long-box baseline has no Q2-2026 long-box loss, so the original loss-reduction test is not applicable. The substitute defense check requires positive short Q2 addition and improved combined recent-three-month net.",
                "",
            ]
        )
    lines.extend(
        [
            "| Combo | Signals | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Delta pp | Recent3 | New kept | New net | Red flipped | Red worsened | Long-box Q2 base | Long-box Q2 with short | Q2 repair% | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in [payload["baseline_row"], *payload["rows"]]:
        repair = row["long_box_q2_loss_reduction_pct"]
        lines.append(
            f"| `{row['combo']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | "
            f"{row['positive_week_delta_pp']:.2f} | {row['recent3_net']:.2f} | "
            f"{row['new_trades_kept']} | {row['new_net_kept']:.2f} | {row['red_weeks_flipped']} | "
            f"{row['red_weeks_worsened']} | {row['long_box_q2_base_net']:.2f} | "
            f"{row['long_box_q2_with_short_net']:.2f} | {repair if repair is not None else 0.0:.2f} | `{row['decision']}` |"
        )
    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 XAU short hedge probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(FREEZE)
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
    baseline_recent3 = period_stats(baseline, RECENT3_START, RECENT3_END)
    long_box_rows = [row for row in baseline if row.get("source_id") == LONG_BOX_SOURCE]
    long_box_q2 = period_stats(long_box_rows, Q2_START, Q2_END)

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
    for variant_name, additions in rows_by_name.items():
        kept, dropped = dedupe_signals(baseline + additions)
        kept_new = [row for row in kept if row.get("source_id") == variant_name]
        combined_weekly = weekly_pnl(kept)
        score = red_week_score(baseline_weekly, combined_weekly, kept_new)
        score.update(
            {
                "new_trades_raw": len(additions),
                "new_trades_kept": len(kept_new),
                "new_trades_dropped": len([row for row in dropped if row.get("source_id") == variant_name]),
                "new_net_kept": round(sum(float(row["pnl_usd"]) for row in kept_new), 2),
            }
        )

        long_box_with_short, _long_dropped = dedupe_signals(long_box_rows + additions)
        long_box_q2_with_short = period_stats(long_box_with_short, Q2_START, Q2_END)
        metrics = summary_metrics(kept, market_days=MARKET_DAYS)
        stress = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
        shape = weekly_exit_shape(kept)
        recent3 = period_stats(kept, RECENT3_START, RECENT3_END)
        reduction = loss_reduction_pct(long_box_q2["net_usd"], long_box_q2_with_short["net_usd"])
        checks, decision = combined_decision(
            metrics,
            stress,
            shape,
            baseline_shape,
            reduction,
            long_box_q2["net_usd"],
            long_box_q2_with_short["net_usd"],
            baseline_recent3["net_usd"],
            recent3["net_usd"],
        )
        row = result_row(variant_name, kept, baseline_shape, score, long_box_q2, long_box_q2_with_short, decision)
        rows.append(row)

        kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{variant_name}_KEPT.csv"
        dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{variant_name}_DROPPED.csv"
        long_box_combo_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{variant_name}_LONG_BOX_PLUS_SHORT.csv"
        write_signal_csv(kept_csv, kept)
        write_signal_csv(dropped_csv, dropped)
        write_signal_csv(long_box_combo_csv, long_box_with_short)
        outputs[f"{variant_name}_kept_csv"] = str(kept_csv)
        outputs[f"{variant_name}_dropped_csv"] = str(dropped_csv)
        outputs[f"{variant_name}_long_box_plus_short_csv"] = str(long_box_combo_csv)
        details.append(
            {
                "variant": variant_name,
                "checks": checks,
                "score": score,
                "long_box_q2_with_short": long_box_q2_with_short,
                "row": row,
            }
        )

    base_row = baseline_row(baseline, baseline_shape, long_box_q2)
    with Path(outputs["results_csv"]).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with Path(outputs["standalone_csv"]).open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [key for key in standalone_rows[0].keys() if key != "checks"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in standalone_rows:
            writer.writerow({key: value for key, value in row.items() if key != "checks"})

    standalone_hits = [row for row in standalone_rows if row["decision"] == "SHORT_HEDGE_STANDALONE_REVIEW_CANDIDATE"]
    standalone_hit_names = {row["variant"] for row in standalone_hits}
    combined_hits = [row for row in rows if row["decision"] == "SHORT_HEDGE_COMBINED_REVIEW_CANDIDATE"]
    full_hits = [row for row in combined_hits if row["combo"] in standalone_hit_names]
    q2_repairs = [
        row
        for row in rows
        if row["decision"] == "SHORT_HEDGE_COMBINED_REVIEW_CANDIDATE" or (
            row["long_box_q2_loss_reduction_pct"] is not None and row["long_box_q2_loss_reduction_pct"] >= 30.0
        )
    ]
    if full_hits:
        status = "SHORT_HEDGE_COMBINED_REVIEW_CANDIDATE"
        best = max(full_hits, key=lambda row: (row["long_box_q2_loss_reduction_pct"] or 0.0, row["new_net_kept"]))
        interpretation = (
            f"`{best['combo']}` passed both the standalone hedge gate and the combined book gate. "
            "Keep it research-only until reviewer approval; do not draft a demo spec from this single pass."
        )
    elif combined_hits:
        status = "COMBINED_BOOK_CLUE_STANDALONE_HEDGE_NOT_CLEAN"
        best = max(combined_hits, key=lambda row: row["new_net_kept"])
        interpretation = (
            f"`{best['combo']}` passed the combined book shape gate, but no matching standalone hedge row passed. "
            "Treat it as a book-level clue only."
        )
    elif standalone_hits:
        status = "SHORT_HEDGE_STANDALONE_ONLY_NO_COMBINED_SURVIVOR"
        best = max(standalone_hits, key=lambda row: (row["q2_net"], row["stress_030_net"]))
        interpretation = (
            f"`{best['variant']}` passed standalone hedge checks but did not pass the combined book gate. "
            "It is a research clue, not a demo candidate."
        )
    elif q2_repairs:
        status = "Q2_REPAIR_CLUE_NO_FULL_SURVIVOR"
        best = max(q2_repairs, key=lambda row: row["long_box_q2_loss_reduction_pct"] or 0.0)
        interpretation = (
            f"`{best['combo']}` reduced the long-box Q2 hole by "
            f"{best['long_box_q2_loss_reduction_pct']:.2f}% but failed one or more hedge gates. "
            "Do not tune hours from this; either request review or move to the failed-rally/lower-high work order."
        )
    else:
        status = "SECOND_WORK_ORDER_NO_SURVIVOR"
        best = max(rows, key=lambda row: (row["long_box_q2_loss_reduction_pct"] or -999.0, row["new_net_kept"]))
        interpretation = (
            f"No second-work-order variant produced a defensible short hedge. Best combined diagnostic was "
            f"`{best['combo']}` with long-box Q2 repair {best['long_box_q2_loss_reduction_pct'] or 0.0:.2f}% "
            f"and new kept net {best['new_net_kept']:.2f} USD. Next step is the first work order."
        )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "freeze_note": str(FREEZE),
        "freeze_note_sha256": sha256_file(FREEZE),
        "baseline_row": base_row,
        "long_box_q2": long_box_q2,
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
