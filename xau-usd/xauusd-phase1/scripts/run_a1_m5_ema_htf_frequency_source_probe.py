from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from run_a1_v9_v10_rr2_stretch_probe import last12_metrics, owner_metrics, read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_M5_EMA_HTF_FREQUENCY_SOURCE_PREREG_2026_07_05.md"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "OWNER_GOAL_M5_EMA_HTF_FREQUENCY_SOURCE_202207_202606"


BASE_INPUTS = {
    "InpSignalMode": "5",
    "InpDirectionMode": "1",
    "InpRiskReward": "2.00",
    "InpMaxEstimatedCostR": "0.15",
    "InpStopCeilingPoints": "0",
    "InpMaxTradesPerDay": "24",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "false",
    "InpMaxOpenPositionsPerMagic": "16",
}


VARIANTS = [
    a1.Variant(
        name="m5ema_long_h4_rr2p0",
        label="M5 EMA trend continuation, long-only, H4 trend gate, 2.0R",
        run_id="BT_A1_XAU_M5_EMA_LONG_H4_RR2P0_OWNER_GOAL",
        tester_inputs={
            **BASE_INPUTS,
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "true",
            "InpH4TrendMinSlopePoints": "0",
        },
    ),
    a1.Variant(
        name="m5ema_long_h1h4_rr2p0",
        label="M5 EMA trend continuation, long-only, H1+H4 trend gate, 2.0R",
        run_id="BT_A1_XAU_M5_EMA_LONG_H1H4_RR2P0_OWNER_GOAL",
        tester_inputs={
            **BASE_INPUTS,
            "InpUseH1TrendFilter": "true",
            "InpH1TrendMinSlopePoints": "0",
            "InpUseH4TrendFilter": "true",
            "InpH4TrendMinSlopePoints": "0",
        },
    ),
    a1.Variant(
        name="m5ema_long_h4_quality_rr2p0",
        label="M5 EMA trend continuation, long-only, H4 trend gate, stricter M5 quality, 2.0R",
        run_id="BT_A1_XAU_M5_EMA_LONG_H4_QUALITY_RR2P0_OWNER_GOAL",
        tester_inputs={
            **BASE_INPUTS,
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "true",
            "InpH4TrendMinSlopePoints": "0",
            "InpMinRangeAtr": "0.80",
            "InpMinBodyFraction": "0.55",
            "InpLongCloseLocation": "0.78",
            "InpMinThreeBarMoveAtr": "0.90",
        },
    ),
]


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
        "signals_rows": len(signals),
        "signal_stage_counts": dict(Counter(row.get("stage", "") for row in signals)),
        "signal_direction_counts": dict(
            Counter(row.get("direction", "") for row in signals if row.get("stage") != "NO_SIGNAL")
        ),
    }


def row_decision(metrics: dict[str, Any]) -> str:
    wr = float(metrics.get("win_rate_pct") or 0.0)
    wl = float(metrics.get("avg_win_loss_ratio") or 0.0)
    active = float(metrics.get("active_day_pct") or 0.0)
    pf = float(metrics.get("profit_factor") or 0.0)
    pnl = float(metrics.get("manual_pnl") or 0.0)
    if pnl <= 0:
        return "FAIL_NET"
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0:
        return "OWNER_GOAL_HIT"
    if wr >= 50.0 and wl >= 2.0:
        return "CORE_SHAPE_FREQUENCY_GAP"
    if wr >= 48.0 and wl >= 1.8 and active >= 70.0 and pf >= 1.30:
        return "NEAR_OWNER_FRONTIER"
    if wr >= 50.0:
        return "FAIL_WIN_LOSS"
    if wl >= 2.0:
        return "FAIL_WIN_RATE"
    return "FAIL_OWNER_SHAPE"


def choose_winner(results: list[dict[str, Any]]) -> dict[str, str]:
    ranked = sorted(
        results,
        key=lambda result: (
            {
                "OWNER_GOAL_HIT": 5,
                "CORE_SHAPE_FREQUENCY_GAP": 4,
                "NEAR_OWNER_FRONTIER": 3,
                "FAIL_WIN_LOSS": 2,
                "FAIL_WIN_RATE": 1,
                "FAIL_OWNER_SHAPE": 0,
                "FAIL_NET": -1,
            }.get(result["decision"], -2),
            result["owner_goal_metrics"].get("active_day_pct") or 0.0,
            result["owner_goal_metrics"].get("profit_factor") or 0.0,
            result["owner_goal_metrics"].get("manual_pnl") or 0.0,
        ),
        reverse=True,
    )
    best = ranked[0] if ranked else None
    if not best:
        return {"status": "REJECT_NO_ROWS", "best_variant": ""}
    if best["decision"] == "OWNER_GOAL_HIT":
        return {"status": "M5_EMA_HTF_OWNER_GOAL_HIT_REVIEW_REQUIRED", "best_variant": best["name"]}
    if best["decision"] == "CORE_SHAPE_FREQUENCY_GAP":
        return {"status": "M5_EMA_HTF_CORE_SHAPE_FREQUENCY_GAP", "best_variant": best["name"]}
    if best["decision"] == "NEAR_OWNER_FRONTIER":
        return {"status": "M5_EMA_HTF_NEAR_OWNER_FRONTIER", "best_variant": best["name"]}
    return {"status": "REJECT_M5_EMA_HTF_NO_OWNER_SHAPE", "best_variant": best["name"]}


def enrich_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for result in payload["variants"]:
        rows = read_trade_csv(Path(result["trade_csv"]))
        result["owner_goal_metrics"] = owner_metrics(rows, FROM_DATE, TO_DATE)
        result["last12_owner_goal_metrics"] = last12_metrics(rows, TO_DATE)
        result["ledger_counts"] = ledger_counts(result)
        result["decision"] = row_decision(result["owner_goal_metrics"])
    payload["winner"] = choose_winner(payload["variants"])
    payload["status"] = payload["winner"]["status"]
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload["scope"]["family"] = "A1 M5 EMA HTF frequency source"
    payload["scope"]["period"] = f"{FROM_DATE} -> {TO_DATE}"
    payload["scope"]["preregistration"] = str(PREREG)
    payload["scope"]["anti_overfit_boundary"] = "Three fixed variants only; no optimizer and no post-result threshold selection."
    return payload


def metric_row(name: str, metrics: dict[str, Any], last12: dict[str, Any], decision: str) -> str:
    return (
        f"| `{name}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
        f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
        f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} | "
        f"{metrics['max_closed_dd']:.2f} | {last12['win_rate_pct']:.2f}/{last12['avg_win_loss_ratio'] or 0.0:.2f} | "
        f"`{decision}` |"
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 EMA HTF Frequency Source Exact Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester probe in isolated root. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['scope']['preregistration']}`",
        "",
        "## Owner Frontier",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L USD | Max DD USD | Last12 WR/WL | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for result in payload["variants"]:
        lines.append(
            metric_row(
                result["name"],
                result["owner_goal_metrics"],
                result["last12_owner_goal_metrics"],
                result["decision"],
            )
        )

    lines.extend(["", "## Ledger Counts", ""])
    for result in payload["variants"]:
        counts = result["ledger_counts"]
        lines.extend(
            [
                f"### `{result['name']}`",
                "",
                f"- Order actions: `{json.dumps(counts['order_action_counts'], sort_keys=True)}`",
                f"- Order reasons: `{json.dumps(counts['order_reason_counts'], sort_keys=True)}`",
                f"- Signal stages: `{json.dumps(counts['signal_stage_counts'], sort_keys=True)}`",
                f"- Signal directions: `{json.dumps(counts['signal_direction_counts'], sort_keys=True)}`",
                "",
            ]
        )

    lines.extend(["## Artifacts", ""])
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

    lines.extend(["## Verdict", ""])
    if payload["status"] == "M5_EMA_HTF_OWNER_GOAL_HIT_REVIEW_REQUIRED":
        lines.append("Exact MT5 reached all owner metrics. Freeze and review before any spec work.")
    elif payload["status"] == "M5_EMA_HTF_CORE_SHAPE_FREQUENCY_GAP":
        lines.append("Exact MT5 reached WR/W-L core shape but still missed activity. Treat as a component clue only.")
    elif payload["status"] == "M5_EMA_HTF_NEAR_OWNER_FRONTIER":
        lines.append("Exact MT5 reached a near-owner frontier. Review is optional only if the owner wants to relax one metric.")
    else:
        lines.append("The M5 EMA HTF source did not bridge the owner WR/W-L/activity tradeoff. Do not spend reviewer.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact MT5 M5 EMA HTF frequency-source probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    if not PREREG.exists():
        raise FileNotFoundError(PREREG)
    a1.VARIANTS = VARIANTS
    report_md = REPORTS / "A1_XAU_M5_EMA_HTF_FREQUENCY_SOURCE_202207_202606.md"
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
