from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from run_a1_v9_v10_rr2_stretch_probe import owner_metrics, read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_D1_LONG_ONLY_PRE2022_ROBUSTNESS_PREREG_2026_07_05.md"
FROM_DATE = "2016.01.01"
TO_DATE = "2021.12.31"
TAG = "OWNER_GOAL_H4_D1_LONG_ONLY_PRE2022_ROBUSTNESS_201601_202112"


VARIANTS = [
    a1.Variant(
        name="long_box2_atr80_range150_body035_pre2022",
        label="Frozen H4 D1 long-only breakout clue, pre-2022 robustness extension",
        run_id="BT_A1_XAU_H4_D1_LONG_BOX2_ATR80_RANGE150_BODY035_PRE2022",
        tester_inputs={
            "InpSignalMode": "7",
            "InpDirectionMode": "1",
            "InpUseH1TrendFilter": "false",
            "InpUseH4TrendFilter": "false",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.15",
            "InpStopCeilingPoints": "0",
            "InpMaxTradesPerDay": "6",
            "InpCooldownMinutes": "0",
            "InpOnePositionPerMagic": "false",
            "InpMaxOpenPositionsPerMagic": "32",
            "InpD1CompressionAtrPercentileMax": "80.00",
            "InpD1CompressionBoxDays": "2",
            "InpD1CompressionRangeMedianMax": "1.50",
            "InpD1CompressionH4MinBodyFraction": "0.35",
        },
    )
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


def stress_metrics(metrics: dict[str, Any], trades: int) -> dict[str, float]:
    return {
        "minus_0p10_per_trade_usd": round(metrics["manual_pnl"] - 0.10 * trades, 2),
        "minus_0p30_per_trade_usd": round(metrics["manual_pnl"] - 0.30 * trades, 2),
    }


def enrich_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for result in payload["variants"]:
        rows = read_trade_csv(Path(result["trade_csv"]))
        metrics = owner_metrics(rows, FROM_DATE, TO_DATE)
        result["owner_goal_metrics"] = metrics
        result["ledger_counts"] = ledger_counts(result)
        result["stress_metrics"] = stress_metrics(metrics, metrics["trades"])
    payload["winner"] = choose_winner(payload["variants"])
    payload["status"] = payload["winner"]["status"]
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload["scope"]["family"] = "A1 H4 D1 long-only pre-2022 robustness extension"
    payload["scope"]["period"] = f"{FROM_DATE} -> {TO_DATE}"
    payload["scope"]["anti_overfit_boundary"] = "One frozen row only; no input changes from the current H4 long-only best clue."
    payload["scope"]["review_spend_rule"] = "Do not spend reviewer on this extension alone."
    payload["scope"]["preregistration"] = str(PREREG)
    return payload


def choose_winner(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {"status": "NO_RESULTS", "best_variant": ""}
    result = results[0]
    metrics = result["owner_goal_metrics"]
    if metrics["owner_core_shape_pass"]:
        return {"status": "PRE2022_CORE_SHAPE_PASS_FREQUENCY_GAP", "best_variant": result["name"]}
    return {"status": "REJECT_PRE2022_CORE_SHAPE_FAIL", "best_variant": result["name"]}


def render(payload: dict[str, Any]) -> str:
    result = payload["variants"][0]
    metrics = result["owner_goal_metrics"]
    counts = result["ledger_counts"]
    stress = result["stress_metrics"]
    decision = "CORE_SHAPE" if metrics["owner_core_shape_pass"] else "FAIL_CORE_SHAPE"
    lines = [
        "# A1 XAU H4 D1 Long-Only Pre-2022 Robustness Exact Probe",
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
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L USD | -0.10/trade | -0.30/trade | Max DD USD | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        (
            f"| `{result['name']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
            f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
            f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} | "
            f"{stress['minus_0p10_per_trade_usd']:.2f} | {stress['minus_0p30_per_trade_usd']:.2f} | "
            f"{metrics['max_closed_dd']:.2f} | `{decision}` |"
        ),
        "",
        "## Ledger Counts",
        "",
        f"- Order actions: `{json.dumps(counts['order_action_counts'], sort_keys=True)}`",
        f"- Order reasons: `{json.dumps(counts['order_reason_counts'], sort_keys=True)}`",
        f"- Signal stages: `{json.dumps(counts['signal_stage_counts'], sort_keys=True)}`",
        f"- Signal directions: `{json.dumps(counts['signal_direction_counts'], sort_keys=True)}`",
        "",
        "## Artifacts",
        "",
        f"- Config: `{result['tester_config']}`",
        f"- MT5 report: `{result['html_report']}`",
        f"- Trade CSV: `{result['trade_csv']}`",
        f"- Order CSV: `{result['order_csv']}`",
        f"- Signal CSV: `{result['signal_csv']}`",
        f"- Summary JSON: `{result['summary_json']}`",
        "",
        "## Verdict",
        "",
    ]
    if payload["status"] == "PRE2022_CORE_SHAPE_PASS_FREQUENCY_GAP":
        lines.append("The frozen H4 long-only clue survives the older window on WR/W-L core shape, but remains low-frequency. Keep it as a component clue only.")
    else:
        lines.append("The frozen H4 long-only clue fails the older-window core shape. Stop treating it as robust enough for portfolio promotion.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact MT5 pre-2022 robustness extension for H4 D1 long-only clue.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    a1.VARIANTS = VARIANTS
    report_md = REPORTS / "A1_XAU_H4_D1_LONG_ONLY_PRE2022_ROBUSTNESS_201601_202112.md"
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
