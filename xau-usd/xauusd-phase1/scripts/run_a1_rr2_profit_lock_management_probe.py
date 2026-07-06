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
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_M5_RR2_PROFIT_LOCK_MANAGEMENT_PROBE_PREREG_2026_07_05.md"
DESIGN_FROM = "2016.01.01"
DESIGN_TO = "2021.12.31"
EXAM_FROM = "2022.07.01"
EXAM_TO = "2026.06.30"


BASE_INPUTS = {
    "InpDirectionMode": "1",
    "InpUseH1TrendFilter": "true",
    "InpH1TrendMinSlopePoints": "0",
    "InpUseH4TrendFilter": "true",
    "InpH4TrendMinSlopePoints": "0",
    "InpMinAtrAbsoluteForEntry": "1.5",
    "InpBlockedEntryHoursCsv": "9,10",
    "InpRiskReward": "2.00",
    "InpProfitProtectionEnabled": "false",
    "InpProfitProtectionShadowOnly": "true",
}


def make_variant(name: str, label: str, trigger: str | None, lock: str | None) -> a1.Variant:
    inputs = dict(BASE_INPUTS)
    if trigger is not None and lock is not None:
        inputs.update(
            {
                "InpProfitProtectionEnabled": "true",
                "InpProfitProtectionShadowOnly": "false",
                "InpProfitProtectionTriggerR": trigger,
                "InpProfitProtectionLockR": lock,
            }
        )
    return a1.Variant(
        name=name,
        label=label,
        run_id=f"BT_A1_XAU_M5_RR2_PROFIT_LOCK_{name.upper()}",
        tester_inputs=inputs,
    )


def build_variants() -> list[a1.Variant]:
    return [
        make_variant("rr2_baseline_no_lock", "RR2 long-only baseline, no profit lock", None, None),
        make_variant("rr2_lock080_010", "RR2 profit lock: trigger +0.80R, lock +0.10R", "0.80", "0.10"),
        make_variant("rr2_lock080_020", "RR2 profit lock: trigger +0.80R, lock +0.20R", "0.80", "0.20"),
        make_variant("rr2_lock100_010", "RR2 profit lock: trigger +1.00R, lock +0.10R", "1.00", "0.10"),
        make_variant("rr2_lock100_020", "RR2 profit lock: trigger +1.00R, lock +0.20R", "1.00", "0.20"),
        make_variant("rr2_lock125_025", "RR2 profit lock: trigger +1.25R, lock +0.25R", "1.25", "0.25"),
    ]


def enrich(payload: dict[str, Any], from_date: str, to_date: str, stage: str) -> dict[str, Any]:
    for result in payload["variants"]:
        rows = read_trade_csv(Path(result["trade_csv"]))
        result["owner_goal_metrics"] = owner_metrics(rows, from_date, to_date)
        result["last12_owner_goal_metrics"] = last12_metrics(rows, to_date)
        result["ranking_tuple"] = list(ranking_tuple(result))
    payload["scope"]["family"] = "A1 RR2 profit-lock management probe"
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
    return (core, near, min(wr, 60.0), min(wl, 3.0) * 10.0, min(active, 100.0), pf, pnl)


def choose_names(design_payload: dict[str, Any], limit: int = 3) -> list[str]:
    traded = [item for item in design_payload["variants"] if item["owner_goal_metrics"]["trades"] > 0]
    return [item["name"] for item in sorted(traded, key=ranking_tuple, reverse=True)[:limit]]


def choose_status(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {"status": "NO_RESULTS", "best_variant": ""}
    full = [item for item in results if item["owner_goal_metrics"]["owner_core_shape_pass"] and item["owner_goal_metrics"]["owner_daily_frequency_pass"]]
    if full:
        best = max(full, key=ranking_tuple)
        return {"status": "OWNER_GOAL_HIT_REVIEW_REQUIRED", "best_variant": best["name"]}
    core = [item for item in results if item["owner_goal_metrics"]["owner_core_shape_pass"]]
    if core:
        best = max(core, key=ranking_tuple)
        return {"status": "CORE_SHAPE_HIT_FREQUENCY_GAP_PACKAGE_FOR_REVIEW", "best_variant": best["name"]}
    near = [item for item in results if item["owner_goal_metrics"]["win_rate_pct"] >= 48.0 and (item["owner_goal_metrics"]["avg_win_loss_ratio"] or 0.0) >= 1.9]
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
    stem: str,
    stage: str,
    timeout: int,
    deposit: str,
    currency: str,
) -> dict[str, Any]:
    report_md = REPORTS / f"{stem}.md"
    report_json = report_md.with_suffix(".json")
    a1.VARIANTS = variants
    payload = a1.run_variants(
        from_date=from_date,
        to_date=to_date,
        tag=a1.safe_name(tag),
        report_md=report_md,
        report_json=report_json,
        variant_timeout_seconds=timeout,
        deposit=deposit,
        currency=currency,
    )
    payload = enrich(payload, from_date, to_date, stage)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_stage(payload), encoding="utf-8")
    return payload


def render_stage(payload: dict[str, Any]) -> str:
    lines = [
        f"# A1 XAU M5 RR2 Profit-Lock Management Probe - {payload['scope']['stage'].title()}",
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
    lines.append("")
    return "\n".join(lines)


def render_combined(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 RR2 Profit-Lock Management Probe Combined Verdict",
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
        "## Exam Frontier",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L | Last12 WR/WL |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    exam = payload.get("exam")
    if exam:
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
    parser = argparse.ArgumentParser(description="Run A1 RR2 profit-lock management design/exam probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    parser.add_argument("--deposit", default="1000")
    parser.add_argument("--currency", default="USD")
    args = parser.parse_args()

    variants = build_variants()
    design = run_stage(
        variants,
        DESIGN_FROM,
        DESIGN_TO,
        "OWNER_GOAL_RR2_PROFIT_LOCK_DESIGN_201601_202112",
        "A1_XAU_M5_RR2_PROFIT_LOCK_MANAGEMENT_PROBE_DESIGN_201601_202112",
        "design",
        args.variant_timeout_seconds,
        args.deposit,
        args.currency,
    )
    selected_names = choose_names(design)
    selected = [variant for variant in variants if variant.name in set(selected_names)]
    exam: dict[str, Any] | None = None
    status = "DESIGN_NO_TRADES_NO_EXAM"
    if selected:
        exam = run_stage(
            selected,
            EXAM_FROM,
            EXAM_TO,
            "OWNER_GOAL_RR2_PROFIT_LOCK_EXAM_202207_202606",
            "A1_XAU_M5_RR2_PROFIT_LOCK_MANAGEMENT_PROBE_EXAM_202207_202606",
            "exam",
            args.variant_timeout_seconds,
            args.deposit,
            args.currency,
        )
        status = exam["winner"]["status"]

    combined_md = REPORTS / "A1_XAU_M5_RR2_PROFIT_LOCK_MANAGEMENT_PROBE_COMBINED_VERDICT_2026_07_05.md"
    combined_json = combined_md.with_suffix(".json")
    combined = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "preregistration": str(PREREG),
        "design_report": str(REPORTS / "A1_XAU_M5_RR2_PROFIT_LOCK_MANAGEMENT_PROBE_DESIGN_201601_202112.md"),
        "exam_report": str(REPORTS / "A1_XAU_M5_RR2_PROFIT_LOCK_MANAGEMENT_PROBE_EXAM_202207_202606.md") if exam else None,
        "selected_for_exam": selected_names,
        "reviewer_spend": "NO_REVIEWER_UNLESS_EXAM_CORE_SHAPE_HIT",
        "design": design,
        "exam": exam,
    }
    combined_json.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    combined_md.write_text(render_combined(combined), encoding="utf-8")
    print(json.dumps({"status": status, "selected_for_exam": selected_names, "report": str(combined_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
