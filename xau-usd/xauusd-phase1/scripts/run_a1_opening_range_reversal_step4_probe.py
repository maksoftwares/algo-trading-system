from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from run_a1_v9_v10_rr2_stretch_probe import last12_metrics, owner_metrics, read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_M5_OPENING_RANGE_REVERSAL_STEP4_PREREG_2026_07_05.md"
DESIGN_FROM = "2016.01.01"
DESIGN_TO = "2021.12.31"
EXAM_FROM = "2022.07.01"
EXAM_TO = "2026.06.30"
DEFAULT_TAG = "OWNER_GOAL_ORREV_STEP4"


def variant_name(session: str, strictness: str, stop_label: str) -> str:
    return f"orrev_{session}_{strictness}_{stop_label}"


def make_variant(
    session: str,
    session_label: str,
    start_hour: int,
    range_minutes: int,
    trade_window_hours: int,
    strictness: str,
    stop_atr: str,
) -> a1.Variant:
    if strictness == "loose":
        trigger = {
            "InpOpeningBreakAtrMultiple": "0.05",
            "InpReclaimAtrMultiple": "0.00",
            "InpMinRangeAtr": "0.30",
            "InpMinBodyFraction": "0.25",
            "InpLongCloseLocation": "0.55",
            "InpShortCloseLocation": "0.45",
        }
    elif strictness == "firm":
        trigger = {
            "InpOpeningBreakAtrMultiple": "0.10",
            "InpReclaimAtrMultiple": "0.05",
            "InpMinRangeAtr": "0.40",
            "InpMinBodyFraction": "0.35",
            "InpLongCloseLocation": "0.60",
            "InpShortCloseLocation": "0.40",
        }
    else:
        raise ValueError(f"Unknown strictness: {strictness}")

    stop_label = "stop10" if stop_atr == "1.00" else "stop15"
    name = variant_name(session, strictness, stop_label)
    return a1.Variant(
        name=name,
        label=(
            f"Opening-range reversal, {session_label}, {range_minutes}m range, "
            f"{trade_window_hours}h window, {strictness}, {stop_atr} ATR stop"
        ),
        run_id=f"BT_A1_XAU_M5_ORREV_{name.upper()}",
        tester_inputs={
            "InpSignalMode": "6",
            "InpDirectionMode": "0",
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "false",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.08",
            "InpMaxSpreadPoints": "75",
            "InpOpeningRangeStartHour": str(start_hour),
            "InpOpeningRangeMinutes": str(range_minutes),
            "InpOpeningTradeWindowHours": str(trade_window_hours),
            "InpStopAtrMultiple": stop_atr,
            "InpStopFloorPoints": "250",
            "InpStopCeilingPoints": "1400",
            "InpMaxTradesPerDay": "24",
            "InpCooldownMinutes": "0",
            "InpOnePositionPerMagic": "true",
            **trigger,
        },
    )


def build_design_variants() -> list[a1.Variant]:
    sessions = [
        ("asia", "Asia server-hour 2", 2, 120, 6),
        ("london", "London server-hour 7", 7, 60, 5),
        ("ny", "NY server-hour 13", 13, 60, 5),
    ]
    variants: list[a1.Variant] = []
    for session, label, start_hour, range_minutes, window_hours in sessions:
        for strictness in ("loose", "firm"):
            for stop_atr in ("1.00", "1.50"):
                variants.append(make_variant(session, label, start_hour, range_minutes, window_hours, strictness, stop_atr))
    return variants


def enrich_payload(payload: dict[str, Any], from_date: str, to_date: str, stage: str) -> dict[str, Any]:
    for result in payload["variants"]:
        rows = read_trade_csv(Path(result["trade_csv"]))
        result["owner_goal_metrics"] = owner_metrics(rows, from_date, to_date)
        result["last12_owner_goal_metrics"] = last12_metrics(rows, to_date)
        result["ranking_tuple"] = ranking_tuple(result)
    payload["scope"]["family"] = "A1 opening-range reversal Step 4"
    payload["scope"]["stage"] = stage
    payload["scope"]["preregistration"] = str(PREREG)
    payload["scope"]["review_spend_rule"] = "Do not spend reviewer unless an exam row reaches WR >= 50% and realized W/L >= 2.0."
    payload["winner"] = choose_status(payload["variants"])
    return payload


def ranking_tuple(result: dict[str, Any]) -> tuple[float, ...]:
    metrics = result["owner_goal_metrics"]
    wr = float(metrics["win_rate_pct"])
    wl = float(metrics["avg_win_loss_ratio"] or 0.0)
    active = float(metrics["active_day_pct"])
    pf = float(metrics["profit_factor"] or 0.0)
    pnl = float(metrics["manual_pnl"])
    core = 1.0 if wr >= 50.0 and wl >= 2.0 else 0.0
    near = 1.0 if wr >= 48.0 and wl >= 1.9 else 0.0
    return (
        core,
        near,
        min(wr, 60.0),
        min(wl, 3.0) * 10.0,
        min(active, 100.0),
        pf,
        pnl,
    )


def choose_exam_variants(design_payload: dict[str, Any], limit: int = 3) -> list[str]:
    traded = [item for item in design_payload["variants"] if item["owner_goal_metrics"]["trades"] > 0]
    ranked = sorted(traded, key=ranking_tuple, reverse=True)
    return [item["name"] for item in ranked[:limit]]


def choose_status(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {"status": "NO_RESULTS", "best_variant": ""}
    full_hits = [
        item
        for item in results
        if item["owner_goal_metrics"]["owner_core_shape_pass"]
        and item["owner_goal_metrics"]["owner_daily_frequency_pass"]
    ]
    if full_hits:
        best = max(full_hits, key=ranking_tuple)
        return {"status": "OWNER_GOAL_HIT_REVIEW_REQUIRED", "best_variant": best["name"]}
    core_hits = [item for item in results if item["owner_goal_metrics"]["owner_core_shape_pass"]]
    if core_hits:
        best = max(core_hits, key=ranking_tuple)
        return {"status": "CORE_SHAPE_HIT_FREQUENCY_GAP_PACKAGE_FOR_REVIEW", "best_variant": best["name"]}
    near = [
        item
        for item in results
        if item["owner_goal_metrics"]["win_rate_pct"] >= 48.0
        and (item["owner_goal_metrics"]["avg_win_loss_ratio"] or 0.0) >= 1.9
    ]
    if near:
        best = max(near, key=ranking_tuple)
        return {"status": "NEAR_MISS_NO_REVIEW_YET", "best_variant": best["name"]}
    best = max(results, key=ranking_tuple)
    return {"status": "REJECT_NO_OWNER_GOAL_HIT", "best_variant": best["name"]}


def run_stage(
    variants: list[a1.Variant],
    from_date: str,
    to_date: str,
    tag: str,
    report_stem: str,
    stage: str,
    variant_timeout_seconds: int,
    deposit: str,
    currency: str,
) -> dict[str, Any]:
    report_md = REPORTS / f"{report_stem}.md"
    report_json = report_md.with_suffix(".json")
    a1.VARIANTS = variants
    payload = a1.run_variants(
        from_date=from_date,
        to_date=to_date,
        tag=tag,
        report_md=report_md,
        report_json=report_json,
        variant_timeout_seconds=variant_timeout_seconds,
        deposit=deposit,
        currency=currency,
    )
    payload = enrich_payload(payload, from_date, to_date, stage)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_stage_markdown(payload), encoding="utf-8")
    return payload


def render_stage_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# A1 XAU M5 Opening-Range Reversal Step 4 - {payload['scope']['stage'].title()}",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester in isolated root. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['winner']['status']}`",
        "",
        f"- Period: `{payload['scope']['period']}`",
        f"- Variant count: `{payload['scope']['variant_count']}`",
        f"- Preregistration: `{payload['scope']['preregistration']}`",
        "",
        "## Owner Frontier",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L | Max DD | Last12 WR/WL | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for result in sorted(payload["variants"], key=ranking_tuple, reverse=True):
        metrics = result["owner_goal_metrics"]
        last12 = result["last12_owner_goal_metrics"]
        decision = "OWNER_GOAL" if metrics["owner_core_shape_pass"] and metrics["owner_daily_frequency_pass"] else "CORE_SHAPE" if metrics["owner_core_shape_pass"] else "NEAR" if metrics["win_rate_pct"] >= 48.0 and (metrics["avg_win_loss_ratio"] or 0.0) >= 1.9 else "FAIL_SHAPE"
        lines.append(
            f"| `{result['name']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
            f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
            f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} | "
            f"{metrics['max_closed_dd']:.2f} | {last12['win_rate_pct']:.2f}/{last12['avg_win_loss_ratio'] or 0.0:.2f} | "
            f"`{decision}` |"
        )
    lines.extend(["", "## Artifacts", ""])
    for result in payload["variants"]:
        lines.extend(
            [
                f"### `{result['name']}`",
                "",
                f"- Label: {result['label']}",
                f"- Config: `{result['tester_config']}`",
                f"- MT5 report: `{result['html_report']}`",
                f"- Trade CSV: `{result['trade_csv']}`",
                f"- Order CSV: `{result['order_csv']}`",
                f"- Signal CSV: `{result['signal_csv']}`",
                f"- Summary JSON: `{result['summary_json']}`",
                "",
            ]
        )
    return "\n".join(lines)


def render_combined_markdown(payload: dict[str, Any]) -> str:
    design = payload["design"]
    exam = payload.get("exam")
    lines = [
        "# A1 XAU M5 Opening-Range Reversal Step 4 Combined Verdict",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester only in isolated root `C:\\MT5A1M5MomentumBacktest`. No live/demo runtime state was touched.",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Preregistration: `{payload['preregistration']}`",
        f"- Design report: `{payload['design_report']}`",
        f"- Exam report: `{payload.get('exam_report', 'n/a')}`",
        f"- Selected for exam: `{', '.join(payload.get('selected_for_exam', [])) or 'none'}`",
        "",
        "## Design Frontier",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in sorted(design["variants"], key=ranking_tuple, reverse=True)[:12]:
        metrics = result["owner_goal_metrics"]
        lines.append(
            f"| `{result['name']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
            f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
            f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} |"
        )
    if exam:
        lines.extend(["", "## Exam Frontier", "", "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L | Last12 WR/WL |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"])
        for result in sorted(exam["variants"], key=ranking_tuple, reverse=True):
            metrics = result["owner_goal_metrics"]
            last12 = result["last12_owner_goal_metrics"]
            lines.append(
                f"| `{result['name']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
                f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
                f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} | "
                f"{last12['win_rate_pct']:.2f}/{last12['avg_win_loss_ratio'] or 0.0:.2f} |"
            )
    lines.extend(["", "## Reviewer Decision", ""])
    if payload["status"] in {"OWNER_GOAL_HIT_REVIEW_REQUIRED", "CORE_SHAPE_HIT_FREQUENCY_GAP_PACKAGE_FOR_REVIEW"}:
        lines.append("Core owner shape reached on exam. Prepare full robustness packet before spending the daily reviewer token.")
    else:
        lines.append("No exam row reached the owner core shape. Do not spend the reviewer token on this branch.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run A1 opening-range reversal Step 4 design/exam probe.")
    parser.add_argument("--design-from", default=DESIGN_FROM)
    parser.add_argument("--design-to", default=DESIGN_TO)
    parser.add_argument("--exam-from", default=EXAM_FROM)
    parser.add_argument("--exam-to", default=EXAM_TO)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    parser.add_argument("--deposit", default="1000")
    parser.add_argument("--currency", default="USD")
    args = parser.parse_args()

    safe_base = a1.safe_name(args.tag)
    design_tag = f"{safe_base}_DESIGN_201601_202112"
    exam_tag = f"{safe_base}_EXAM_202207_202606"
    design_stem = "A1_XAU_M5_OPENING_RANGE_REVERSAL_STEP4_DESIGN_201601_202112"
    exam_stem = "A1_XAU_M5_OPENING_RANGE_REVERSAL_STEP4_EXAM_202207_202606"
    combined_md = REPORTS / "A1_XAU_M5_OPENING_RANGE_REVERSAL_STEP4_COMBINED_VERDICT_2026_07_05.md"
    combined_json = combined_md.with_suffix(".json")

    design_variants = build_design_variants()
    design_payload = run_stage(
        design_variants,
        args.design_from,
        args.design_to,
        design_tag,
        design_stem,
        "design",
        args.variant_timeout_seconds,
        args.deposit,
        args.currency,
    )
    selected_names = choose_exam_variants(design_payload)
    selected_variants = [variant for variant in design_variants if variant.name in set(selected_names)]

    exam_payload: dict[str, Any] | None = None
    status = "DESIGN_NO_TRADES_NO_EXAM"
    if selected_variants:
        exam_payload = run_stage(
            selected_variants,
            args.exam_from,
            args.exam_to,
            exam_tag,
            exam_stem,
            "exam",
            args.variant_timeout_seconds,
            args.deposit,
            args.currency,
        )
        status = exam_payload["winner"]["status"]

    combined_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "preregistration": str(PREREG),
        "design_report": str(REPORTS / f"{design_stem}.md"),
        "exam_report": str(REPORTS / f"{exam_stem}.md") if exam_payload else None,
        "selected_for_exam": selected_names,
        "reviewer_spend": "NO_REVIEWER_UNLESS_EXAM_CORE_SHAPE_HIT",
        "design": design_payload,
        "exam": exam_payload,
    }
    combined_json.write_text(json.dumps(combined_payload, indent=2), encoding="utf-8")
    combined_md.write_text(render_combined_markdown(combined_payload), encoding="utf-8")
    print(json.dumps({"status": status, "selected_for_exam": selected_names, "report": str(combined_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
