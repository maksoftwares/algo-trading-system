from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from run_a1_v9_v10_rr2_stretch_probe import (
    choose_owner_winner,
    last12_metrics,
    owner_metrics,
    read_trade_csv,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_INDEPENDENT_OBSERVER_FAMILIES_EXACT_PROBE_PREREG_2026_07_05.md"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "OWNER_GOAL_H4_INDEPENDENT_OBSERVER_FAMILIES_202207_202606"


VARIANTS = [
    a1.Variant(
        name="d1_compression_h4_expansion_rr2p0",
        label="D1 compression box with H4 expansion close, fixed 2.0R",
        run_id="BT_A1_XAU_H4_D1_COMPRESSION_H4_EXPANSION_RR2P0_OWNER_GOAL",
        tester_inputs={
            "InpSignalMode": "7",
            "InpDirectionMode": "0",
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "false",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.15",
            "InpStopCeilingPoints": "0",
            "InpMaxTradesPerDay": "6",
            "InpCooldownMinutes": "0",
        },
    ),
    a1.Variant(
        name="h4_trend_pullback_d1_bias_rr2p0",
        label="H4 trend pullback/rejection in D1 EMA bias, fixed 2.0R",
        run_id="BT_A1_XAU_H4_TREND_PULLBACK_D1_BIAS_RR2P0_OWNER_GOAL",
        tester_inputs={
            "InpSignalMode": "8",
            "InpDirectionMode": "0",
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "false",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.15",
            "InpStopCeilingPoints": "0",
            "InpMaxTradesPerDay": "6",
            "InpCooldownMinutes": "0",
        },
    ),
    a1.Variant(
        name="weekly_level_h4_rejection_rr2p0",
        label="Previous/prior-four-week level H4 rejection, fixed 2.0R",
        run_id="BT_A1_XAU_H4_WEEKLY_LEVEL_REJECTION_RR2P0_OWNER_GOAL",
        tester_inputs={
            "InpSignalMode": "9",
            "InpDirectionMode": "0",
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "false",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.15",
            "InpStopCeilingPoints": "0",
            "InpMaxTradesPerDay": "6",
            "InpCooldownMinutes": "0",
        },
    ),
]


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def enrich_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for result in payload["variants"]:
        rows = read_trade_csv(Path(result["trade_csv"]))
        result["owner_goal_metrics"] = owner_metrics(rows, FROM_DATE, TO_DATE)
        result["last12_owner_goal_metrics"] = last12_metrics(rows, TO_DATE)
    payload["winner"] = choose_owner_winner(payload["variants"])
    payload["status"] = payload["winner"]["status"]
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload["scope"]["family"] = "A1 H4 independent observer family exact probe"
    payload["scope"]["period"] = f"{FROM_DATE} -> {TO_DATE}"
    payload["scope"]["anti_overfit_boundary"] = "Three preregistered Phase 2B observer premises only; one fixed 2.0R execution shape each; no tuning grid."
    payload["scope"]["review_spend_rule"] = "Do not spend reviewer unless a row reaches WR >= 50% and realized W/L >= 2.0."
    payload["scope"]["preregistration"] = str(PREREG)
    return payload


def row_decision(metrics: dict[str, Any]) -> str:
    if metrics["owner_core_shape_pass"] and metrics["owner_daily_frequency_pass"]:
        return "OWNER_GOAL"
    if metrics["owner_core_shape_pass"]:
        return "CORE_SHAPE"
    if metrics["win_rate_pct"] >= 48.0 and (metrics["avg_win_loss_ratio"] or 0.0) >= 1.9:
        return "NEAR"
    return "FAIL_SHAPE"


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU H4 Independent Observer Families Exact Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester probe in isolated root. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Preregistration: `{payload['scope']['preregistration']}`",
        f"- Period: `{payload['scope']['period']}`",
        f"- Tester currency: `{payload['scope'].get('tester_currency', 'USD')}`",
        f"- Variant count: `{payload['scope']['variant_count']}`",
        "",
        "## Owner Frontier",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L USD | Max DD USD | Last12 WR/WL | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for result in payload["variants"]:
        metrics = result["owner_goal_metrics"]
        last12 = result["last12_owner_goal_metrics"]
        lines.append(
            f"| `{result['name']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
            f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
            f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} | "
            f"{metrics['max_closed_dd']:.2f} | {last12['win_rate_pct']:.2f}/{last12['avg_win_loss_ratio'] or 0.0:.2f} | "
            f"`{row_decision(metrics)}` |"
        )

    lines.extend(["", "## Artifacts", ""])
    for result in payload["variants"]:
        lines.extend(
            [
                f"### `{result['name']}`",
                "",
                f"- Label: {result['label']}",
                f"- MT5 report: `{result['html_report']}`",
                f"- Trade CSV: `{result['trade_csv']}`",
                f"- Order CSV: `{result['order_csv']}`",
                f"- Signal CSV: `{result['signal_csv']}`",
                "",
            ]
        )

    if payload["status"] in {"OWNER_GOAL_HIT_REVIEW_REQUIRED", "CORE_SHAPE_HIT_FREQUENCY_GAP"}:
        verdict = "At least one exact MT5 row reached the hard WR/W-L core. Freeze artifacts before deciding whether to spend the reviewer token."
    else:
        verdict = "No exact MT5 row reached WR >= 50% and realized W/L >= 2.0. Do not spend the reviewer token on this branch."

    lines.extend(["## Verdict", "", verdict, ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact MT5 H4 independent observer family probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    a1.VARIANTS = VARIANTS
    report_md = REPORTS / "A1_XAU_H4_INDEPENDENT_OBSERVER_FAMILIES_EXACT_PROBE_202207_202606.md"
    report_json = report_md.with_suffix(".json")
    payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=report_md,
        report_json=report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )
    payload = enrich_payload(payload)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "winner": payload["winner"], "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
