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
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_M5_COMPRESSION_H1H4_RR2_EXAM_PREREG_2026_07_05.md"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "OWNER_GOAL_M5_COMPRESSION_H1H4_RR2_EXAM_202207_202606"


VARIANTS = [
    a1.Variant(
        name="compression_long_h1h4_rr2p0",
        label="M5 compression expansion, long-only, H1+H4 trend gate, 2.0R",
        run_id="BT_A1_XAU_M5_COMPRESSION_LONG_H1H4_RR2P0_EXAM",
        tester_inputs={
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.15",
            "InpStopCeilingPoints": "0",
            "InpMaxTradesPerDay": "24",
            "InpCooldownMinutes": "0",
            "InpOnePositionPerMagic": "false",
            "InpMaxOpenPositionsPerMagic": "16",
            "InpSignalMode": "2",
            "InpDirectionMode": "1",
            "InpUseH1TrendFilter": "true",
            "InpUseH4TrendFilter": "true",
            "InpCompressionLookbackBars": "8",
            "InpCompressionMaxRangeAtr": "1.20",
            "InpCompressionBreakAtrMultiple": "0.10",
        },
    )
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
        return "EXAM_OWNER_HIT_REVIEW_REQUIRED"
    if wr >= 50.0 and wl >= 2.0:
        return "EXAM_CORE_SHAPE_SPARSE_CLUE"
    if wr >= 48.0 and wl >= 1.8 and active >= 30.0 and pf >= 1.30:
        return "EXAM_NEAR_FRONTIER_CLUE"
    if wr >= 50.0:
        return "FAIL_WIN_LOSS"
    if wl >= 2.0:
        return "FAIL_WIN_RATE"
    return "FAIL_OWNER_SHAPE"


def choose_status(result: dict[str, Any]) -> str:
    decision = result["decision"]
    if decision in {
        "EXAM_OWNER_HIT_REVIEW_REQUIRED",
        "EXAM_CORE_SHAPE_SPARSE_CLUE",
        "EXAM_NEAR_FRONTIER_CLUE",
    }:
        return decision
    return "REJECT_COMPRESSION_H1H4_RR2_EXAM_FAILED"


def enrich_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for result in payload["variants"]:
        rows = read_trade_csv(Path(result["trade_csv"]))
        result["owner_goal_metrics"] = owner_metrics(rows, FROM_DATE, TO_DATE)
        result["last12_owner_goal_metrics"] = last12_metrics(rows, TO_DATE)
        result["ledger_counts"] = ledger_counts(result)
        result["decision"] = row_decision(result["owner_goal_metrics"])
    payload["status"] = choose_status(payload["variants"][0])
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload["scope"]["family"] = "A1 M5 compression H1+H4 2R exam"
    payload["scope"]["period"] = f"{FROM_DATE} -> {TO_DATE}"
    payload["scope"]["preregistration"] = str(PREREG)
    payload["scope"]["anti_overfit_boundary"] = "Single frozen design candidate; no optimizer and no post-result threshold selection."
    return payload


def render(payload: dict[str, Any]) -> str:
    result = payload["variants"][0]
    metrics = result["owner_goal_metrics"]
    last12 = result["last12_owner_goal_metrics"]
    counts = result["ledger_counts"]
    lines = [
        "# A1 XAU M5 Compression H1+H4 2R Exact Exam",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester exam in isolated root. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['scope']['preregistration']}`",
        "",
        "## Exam Row",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L USD | Max DD USD | Last12 WR/WL | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        (
            f"| `{result['name']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
            f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
            f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} | "
            f"{metrics['max_closed_dd']:.2f} | {last12['win_rate_pct']:.2f}/{last12['avg_win_loss_ratio'] or 0.0:.2f} | "
            f"`{result['decision']}` |"
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
    if payload["status"] == "EXAM_OWNER_HIT_REVIEW_REQUIRED":
        lines.append("The frozen candidate passed the full owner gate on the recent exact-MT5 exam. Send for review before any demo/runtime work.")
    elif payload["status"] == "EXAM_CORE_SHAPE_SPARSE_CLUE":
        lines.append("The frozen candidate retained the 50%/2R core shape but is too sparse for the owner daily-frequency goal. Treat as a clue for hybrid/frequency work, not a demo candidate.")
    elif payload["status"] == "EXAM_NEAR_FRONTIER_CLUE":
        lines.append("The frozen candidate is a recent-window near-frontier clue, not a demo candidate.")
    else:
        lines.append("The frozen candidate failed the recent exact-MT5 exam. Do not spend the reviewer token on this branch.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact MT5 exam for frozen M5 compression H1+H4 2R candidate.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    if not PREREG.exists():
        raise FileNotFoundError(PREREG)

    a1.VARIANTS = VARIANTS
    report_md = REPORTS / "A1_XAU_M5_COMPRESSION_H1H4_RR2_EXAM_202207_202606.md"
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
    print(json.dumps({"status": payload["status"], "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
