from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from run_a1_v9_v10_rr2_stretch_probe import owner_metrics, read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_M5_DAILY_EXTREME_RECLAIM_PREREG_2026_07_05.md"
DESIGN_FROM = "2016.01.01"
DESIGN_TO = "2021.12.31"
EXAM_FROM = "2022.01.01"
EXAM_TO = "2026.06.30"
TAG = "OWNER_GOAL_M5_DAILY_EXTREME_RECLAIM_PREREG_20260705"


def daily_extreme_variant(
    *,
    name: str,
    label: str,
    session_start: int,
    session_end: int,
    min_move: float,
    touch: float,
    reclaim: float,
    stop_buffer: float,
    min_range: float,
    min_body: float,
    long_close_location: float,
    short_close_location: float,
) -> a1.Variant:
    return a1.Variant(
        name=name,
        label=label,
        run_id=f"BT_A1_XAU_M5_DAILY_EXTREME_RECLAIM_{name.upper()}",
        tester_inputs={
            "InpSignalMode": "11",
            "InpDirectionMode": "0",
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "false",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.15",
            "InpStopFloorPoints": "100",
            "InpStopCeilingPoints": "0",
            "InpMaxTradesPerDay": "24",
            "InpCooldownMinutes": "0",
            "InpOnePositionPerMagic": "false",
            "InpMaxOpenPositionsPerMagic": "16",
            "InpMinRangeAtr": f"{min_range:.2f}",
            "InpLongCloseLocation": f"{long_close_location:.2f}",
            "InpShortCloseLocation": f"{short_close_location:.2f}",
            "InpDailyExtremeMinMoveAtr": f"{min_move:.2f}",
            "InpDailyExtremeTouchAtr": f"{touch:.2f}",
            "InpDailyExtremeReclaimAtr": f"{reclaim:.2f}",
            "InpDailyExtremeStopBufferAtr": f"{stop_buffer:.2f}",
            "InpDailyExtremeMinBodyFraction": f"{min_body:.2f}",
            "InpDailyExtremeMinBarsSinceOpen": "24",
            "InpDailyExtremeStartHour": str(session_start),
            "InpDailyExtremeEndHour": str(session_end),
        },
    )


DESIGN_VARIANTS = [
    daily_extreme_variant(
        name="der_broad_all_day_075",
        label="Daily extreme reclaim broad all-day 0.75D1ATR stretch",
        session_start=0,
        session_end=24,
        min_move=0.75,
        touch=0.08,
        reclaim=0.08,
        stop_buffer=0.08,
        min_range=0.15,
        min_body=0.20,
        long_close_location=0.55,
        short_close_location=0.45,
    ),
    daily_extreme_variant(
        name="der_broad_liquid_075",
        label="Daily extreme reclaim liquid-session 0.75D1ATR stretch",
        session_start=7,
        session_end=22,
        min_move=0.75,
        touch=0.08,
        reclaim=0.08,
        stop_buffer=0.08,
        min_range=0.15,
        min_body=0.20,
        long_close_location=0.55,
        short_close_location=0.45,
    ),
    daily_extreme_variant(
        name="der_standard_liquid_100",
        label="Daily extreme reclaim liquid-session 1.00D1ATR stretch",
        session_start=7,
        session_end=22,
        min_move=1.00,
        touch=0.06,
        reclaim=0.10,
        stop_buffer=0.10,
        min_range=0.20,
        min_body=0.25,
        long_close_location=0.58,
        short_close_location=0.42,
    ),
    daily_extreme_variant(
        name="der_us_100",
        label="Daily extreme reclaim US-session 1.00D1ATR stretch",
        session_start=12,
        session_end=23,
        min_move=1.00,
        touch=0.06,
        reclaim=0.10,
        stop_buffer=0.10,
        min_range=0.20,
        min_body=0.25,
        long_close_location=0.58,
        short_close_location=0.42,
    ),
    daily_extreme_variant(
        name="der_deep_reclaim_100",
        label="Daily extreme reclaim liquid-session deeper reclaim",
        session_start=7,
        session_end=22,
        min_move=1.00,
        touch=0.08,
        reclaim=0.15,
        stop_buffer=0.08,
        min_range=0.15,
        min_body=0.20,
        long_close_location=0.55,
        short_close_location=0.45,
    ),
    daily_extreme_variant(
        name="der_exhaustion_125",
        label="Daily extreme reclaim liquid-session 1.25D1ATR stretch",
        session_start=7,
        session_end=22,
        min_move=1.25,
        touch=0.06,
        reclaim=0.10,
        stop_buffer=0.10,
        min_range=0.20,
        min_body=0.25,
        long_close_location=0.58,
        short_close_location=0.42,
    ),
]


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def ledger_counts(result: dict[str, Any]) -> dict[str, Any]:
    orders = read_tsv(Path(result["order_csv"]))
    signals = read_tsv(Path(result["signal_csv"]))
    return {
        "orders_rows": len(orders),
        "order_action_counts": dict(Counter(row.get("action", "") for row in orders)),
        "order_reason_counts": dict(Counter(row.get("reason", "") for row in orders)),
        "signal_stage_counts": dict(Counter(row.get("stage", "") for row in signals)),
        "signal_direction_counts": dict(
            Counter(row.get("direction", "") for row in signals if row.get("stage") != "NO_SIGNAL")
        ),
    }


def stress_metrics(metrics: dict[str, Any]) -> dict[str, float]:
    trades = metrics["trades"]
    return {
        "minus_0p10_per_trade_usd": round(metrics["manual_pnl"] - 0.10 * trades, 2),
        "minus_0p30_per_trade_usd": round(metrics["manual_pnl"] - 0.30 * trades, 2),
    }


def core_pass(metrics: dict[str, Any]) -> bool:
    ratio = metrics["avg_win_loss_ratio"] or 0.0
    pf = metrics["profit_factor"] or 0.0
    return (
        metrics["trades"] >= 100
        and metrics["win_rate_pct"] >= 50.0
        and ratio >= 2.0
        and pf > 1.0
        and metrics["manual_pnl"] > 0.0
    )


def near_frontier(metrics: dict[str, Any]) -> bool:
    ratio = metrics["avg_win_loss_ratio"] or 0.0
    pf = metrics["profit_factor"] or 0.0
    return (
        metrics["trades"] >= 100
        and metrics["win_rate_pct"] >= 48.0
        and ratio >= 1.80
        and pf >= 1.20
        and metrics["manual_pnl"] > 0.0
    )


def enrich_results(results: list[dict[str, Any]], from_date: str, to_date: str) -> list[dict[str, Any]]:
    for result in results:
        rows = read_trade_csv(Path(result["trade_csv"]))
        metrics = owner_metrics(rows, from_date, to_date)
        result["owner_goal_metrics"] = metrics
        result["ledger_counts"] = ledger_counts(result)
        result["stress_metrics"] = stress_metrics(metrics)
        result["selection"] = {
            "core_pass": core_pass(metrics),
            "near_frontier": near_frontier(metrics),
        }
    return results


def select_exam_variants(design_results: list[dict[str, Any]]) -> list[a1.Variant]:
    qualifying = [
        result for result in design_results
        if result["selection"]["core_pass"] or result["selection"]["near_frontier"]
    ]
    qualifying.sort(
        key=lambda result: (
            result["selection"]["core_pass"],
            result["owner_goal_metrics"]["manual_pnl"],
            result["owner_goal_metrics"]["active_day_pct"],
            result["owner_goal_metrics"]["trades"],
        ),
        reverse=True,
    )
    selected_names = {result["name"] for result in qualifying[:3]}
    return [variant for variant in DESIGN_VARIANTS if variant.name in selected_names]


def result_status(design_results: list[dict[str, Any]], exam_results: list[dict[str, Any]]) -> str:
    if not any(result["selection"]["core_pass"] or result["selection"]["near_frontier"] for result in design_results):
        return "REJECT_DESIGN_NO_CORE_OR_NEAR_FRONTIER"
    if not exam_results:
        return "DESIGN_QUALIFIED_EXAM_NOT_RUN"
    if any(result["selection"]["core_pass"] for result in exam_results):
        return "EXAM_CORE_SHAPE_PASS_WATCHLIST_ONLY"
    return "REJECT_EXAM_CORE_SHAPE_FAIL"


def best_result(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not results:
        return None
    return sorted(
        results,
        key=lambda result: (
            result["selection"]["core_pass"],
            result["selection"]["near_frontier"],
            result["owner_goal_metrics"]["manual_pnl"],
            result["owner_goal_metrics"]["active_day_pct"],
            result["owner_goal_metrics"]["trades"],
        ),
        reverse=True,
    )[0]


def run_window(
    *,
    variants: list[a1.Variant],
    from_date: str,
    to_date: str,
    tag_suffix: str,
    report_md: Path,
    report_json: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    a1.VARIANTS = variants
    payload = a1.run_variants(
        from_date=from_date,
        to_date=to_date,
        tag=a1.safe_name(f"{TAG}_{tag_suffix}"),
        report_md=report_md,
        report_json=report_json,
        variant_timeout_seconds=timeout_seconds,
        deposit="1000",
        currency="USD",
    )
    payload["variants"] = enrich_results(payload["variants"], from_date, to_date)
    payload["scope"]["family"] = "A1 M5 daily extreme reclaim"
    payload["scope"]["preregistration"] = str(PREREG)
    payload["scope"]["period"] = f"{from_date} -> {to_date}"
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def metric_row(result: dict[str, Any]) -> str:
    metrics = result["owner_goal_metrics"]
    stress = result["stress_metrics"]
    ratio = metrics["avg_win_loss_ratio"] or 0.0
    pf = metrics["profit_factor"] or 0.0
    decision = "CORE" if result["selection"]["core_pass"] else ("NEAR" if result["selection"]["near_frontier"] else "FAIL")
    return (
        f"| `{result['name']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
        f"{ratio:.4f} | {metrics['active_day_pct']:.2f} | {pf:.4f} | "
        f"{metrics['manual_pnl']:.2f} | {stress['minus_0p10_per_trade_usd']:.2f} | "
        f"{stress['minus_0p30_per_trade_usd']:.2f} | {metrics['max_closed_dd']:.2f} | `{decision}` |"
    )


def render(payload: dict[str, Any]) -> str:
    design_results = payload["design"]["variants"]
    exam_results = payload["exam"]["variants"] if payload.get("exam") else []
    lines = [
        "# A1 XAU M5 Daily Extreme Reclaim Exact MT5 Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester in isolated root. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Preregistration: `{payload['preregistration']}`",
        f"- Design period: `{DESIGN_FROM} -> {DESIGN_TO}`",
        f"- Exam period: `{EXAM_FROM} -> {EXAM_TO}`",
        f"- Design variants: `{len(design_results)}`",
        f"- Frozen exam variants: `{len(exam_results)}`",
        "",
        "## Design Window",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L USD | -0.10/trade | -0.30/trade | Max DD USD | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    lines.extend(metric_row(result) for result in sorted(design_results, key=lambda item: item["owner_goal_metrics"]["manual_pnl"], reverse=True))

    selected = payload["selected_for_exam"]
    lines.extend(["", f"Selected for exam: `{', '.join(selected) if selected else 'NONE'}`", ""])

    if exam_results:
        lines.extend([
            "## Frozen Exam",
            "",
            "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L USD | -0.10/trade | -0.30/trade | Max DD USD | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ])
        lines.extend(metric_row(result) for result in sorted(exam_results, key=lambda item: item["owner_goal_metrics"]["manual_pnl"], reverse=True))
        lines.append("")

    lines.extend([
        "## Ledger Notes",
        "",
    ])
    best_design = best_result(design_results)
    if best_design:
        lines.append(f"- Best design ledger actions: `{json.dumps(best_design['ledger_counts']['order_action_counts'], sort_keys=True)}`")
        lines.append(f"- Best design signal directions: `{json.dumps(best_design['ledger_counts']['signal_direction_counts'], sort_keys=True)}`")
    best_exam = best_result(exam_results)
    if best_exam:
        lines.append(f"- Best exam ledger actions: `{json.dumps(best_exam['ledger_counts']['order_action_counts'], sort_keys=True)}`")
        lines.append(f"- Best exam signal directions: `{json.dumps(best_exam['ledger_counts']['signal_direction_counts'], sort_keys=True)}`")
    lines.extend(["", "## Verdict", ""])
    if payload["status"] == "REJECT_DESIGN_NO_CORE_OR_NEAR_FRONTIER":
        lines.append("The family failed the design-window core/near-frontier gate, so the 2022-2026 exam was not spent.")
    elif payload["status"] == "EXAM_CORE_SHAPE_PASS_WATCHLIST_ONLY":
        lines.append("At least one frozen exam row hit the owner core shape. This is watchlist-only and needs robustness before any demo discussion.")
    else:
        lines.append("The family earned an exam but failed the frozen 2022-2026 core-shape requirement. Reject for the current owner goal.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run preregistered exact-MT5 daily extreme reclaim probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)

    design_md = REPORTS / "A1_XAU_M5_DAILY_EXTREME_RECLAIM_DESIGN_201601_202112.md"
    design_json = design_md.with_suffix(".json")
    design_payload = run_window(
        variants=DESIGN_VARIANTS,
        from_date=DESIGN_FROM,
        to_date=DESIGN_TO,
        tag_suffix="DESIGN_201601_202112",
        report_md=design_md,
        report_json=design_json,
        timeout_seconds=args.variant_timeout_seconds,
    )
    selected = select_exam_variants(design_payload["variants"])

    exam_payload: dict[str, Any] | None = None
    if selected:
        exam_md = REPORTS / "A1_XAU_M5_DAILY_EXTREME_RECLAIM_EXAM_202201_202606.md"
        exam_json = exam_md.with_suffix(".json")
        exam_payload = run_window(
            variants=selected,
            from_date=EXAM_FROM,
            to_date=EXAM_TO,
            tag_suffix="EXAM_202201_202606",
            report_md=exam_md,
            report_json=exam_json,
            timeout_seconds=args.variant_timeout_seconds,
        )

    status = result_status(design_payload["variants"], exam_payload["variants"] if exam_payload else [])
    final_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": status,
        "preregistration": str(PREREG),
        "selected_for_exam": [variant.name for variant in selected],
        "design": design_payload,
        "exam": exam_payload,
    }
    final_md = REPORTS / "A1_XAU_M5_DAILY_EXTREME_RECLAIM_PREREG_EXACT_PROBE_2026_07_05.md"
    final_json = final_md.with_suffix(".json")
    final_json.write_text(json.dumps(final_payload, indent=2), encoding="utf-8")
    final_md.write_text(render(final_payload), encoding="utf-8")
    print(json.dumps({"status": status, "selected_for_exam": final_payload["selected_for_exam"], "report": str(final_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
