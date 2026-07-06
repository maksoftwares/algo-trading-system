from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from run_a1_v9_v10_rr2_stretch_probe import (
    last12_metrics,
    owner_metrics,
    read_trade_csv,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_D1_COMPRESSION_FREQUENCY_MECHANICS_PREREG_2026_07_05.md"
BASELINE_JSON = REPORTS / "A1_XAU_H4_INDEPENDENT_OBSERVER_FAMILIES_EXACT_PROBE_202207_202606.json"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "OWNER_GOAL_H4_D1_COMPRESSION_FREQUENCY_MECHANICS_202207_202606"


def variant(max_open: int) -> a1.Variant:
    name = f"d1_compression_h4_expansion_rr2p0_max{max_open}"
    return a1.Variant(
        name=name,
        label=f"D1 compression/H4 expansion, fixed 2.0R, max {max_open} open positions",
        run_id=f"BT_A1_XAU_H4_D1_COMP_FREQ_MAX{max_open}_RR2P0_OWNER_GOAL",
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
            "InpOnePositionPerMagic": "false",
            "InpMaxOpenPositionsPerMagic": str(max_open),
        },
    )


VARIANTS = [variant(2), variant(4), variant(8), variant(16)]


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
        "order_direction_counts": dict(Counter(row.get("direction", "") for row in orders)),
        "signals_rows": len(signals),
        "signal_stage_counts": dict(Counter(row.get("stage", "") for row in signals)),
        "signal_direction_counts": dict(
            Counter(row.get("direction", "") for row in signals if row.get("stage") != "NO_SIGNAL")
        ),
    }


def load_baseline_context() -> dict[str, Any]:
    payload = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    baseline = next(
        item for item in payload["variants"] if item["name"] == "d1_compression_h4_expansion_rr2p0"
    )
    baseline["ledger_counts"] = ledger_counts(baseline)
    return baseline


def enrich_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for result in payload["variants"]:
        rows = read_trade_csv(Path(result["trade_csv"]))
        result["owner_goal_metrics"] = owner_metrics(rows, FROM_DATE, TO_DATE)
        result["last12_owner_goal_metrics"] = last12_metrics(rows, TO_DATE)
        result["ledger_counts"] = ledger_counts(result)
    payload["baseline_context"] = load_baseline_context()
    payload["winner"] = choose_winner(payload["variants"])
    payload["status"] = payload["winner"]["status"]
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload["scope"]["family"] = "A1 H4 D1 compression frequency mechanics probe"
    payload["scope"]["period"] = f"{FROM_DATE} -> {TO_DATE}"
    payload["scope"]["anti_overfit_boundary"] = (
        "Only the max-open-position cap changes from the exact MT5 core-shape baseline; "
        "signal premise and 2.0R execution stay frozen."
    )
    payload["scope"]["review_spend_rule"] = (
        "Do not spend reviewer unless frequency materially improves while WR >= 50% and realized W/L >= 2.0 survive."
    )
    payload["scope"]["preregistration"] = str(PREREG)
    payload["scope"]["baseline_probe"] = str(BASELINE_JSON)
    return payload


def choose_winner(results: list[dict[str, Any]]) -> dict[str, Any]:
    core_hits = [result for result in results if result["owner_goal_metrics"]["owner_core_shape_pass"]]
    if core_hits:
        best = max(core_hits, key=lambda item: (item["owner_goal_metrics"]["active_day_pct"], item["owner_goal_metrics"]["manual_pnl"]))
        if best["owner_goal_metrics"]["owner_daily_frequency_pass"]:
            return {"status": "OWNER_GOAL_HIT_REVIEW_REQUIRED", "best_variant": best["name"]}
        return {"status": "CORE_SHAPE_SURVIVES_FREQUENCY_GAP", "best_variant": best["name"]}
    near = [
        result
        for result in results
        if result["owner_goal_metrics"]["win_rate_pct"] >= 48.0
        and (result["owner_goal_metrics"]["avg_win_loss_ratio"] or 0.0) >= 1.9
    ]
    if near:
        best = max(near, key=lambda item: (item["owner_goal_metrics"]["win_rate_pct"], item["owner_goal_metrics"]["manual_pnl"]))
        return {"status": "NEAR_MISS_FREQUENCY_MECHANICS", "best_variant": best["name"]}
    best = max(results, key=lambda item: item["owner_goal_metrics"]["manual_pnl"]) if results else None
    return {
        "status": "REJECT_FREQUENCY_UNCAP_BREAKS_CORE_SHAPE",
        "best_variant": best["name"] if best else "",
    }


def row_decision(metrics: dict[str, Any]) -> str:
    if metrics["owner_core_shape_pass"] and metrics["owner_daily_frequency_pass"]:
        return "OWNER_GOAL"
    if metrics["owner_core_shape_pass"]:
        return "CORE_SHAPE"
    if metrics["win_rate_pct"] >= 48.0 and (metrics["avg_win_loss_ratio"] or 0.0) >= 1.9:
        return "NEAR"
    return "FAIL_SHAPE"


def render_metric_row(name: str, metrics: dict[str, Any], last12: dict[str, Any] | None, decision: str) -> str:
    last12_cell = "n/a"
    if last12 is not None:
        last12_cell = f"{last12['win_rate_pct']:.2f}/{last12['avg_win_loss_ratio'] or 0.0:.2f}"
    return (
        f"| `{name}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
        f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
        f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} | "
        f"{metrics['max_closed_dd']:.2f} | {last12_cell} | `{decision}` |"
    )


def render_counts(result: dict[str, Any]) -> list[str]:
    counts = result["ledger_counts"]
    return [
        f"- Order actions: `{json.dumps(counts['order_action_counts'], sort_keys=True)}`",
        f"- Order reasons: `{json.dumps(counts['order_reason_counts'], sort_keys=True)}`",
        f"- Signal stages: `{json.dumps(counts['signal_stage_counts'], sort_keys=True)}`",
        f"- Signal directions: `{json.dumps(counts['signal_direction_counts'], sort_keys=True)}`",
    ]


def render(payload: dict[str, Any]) -> str:
    baseline = payload["baseline_context"]
    baseline_metrics = baseline["owner_goal_metrics"]
    baseline_last12 = baseline["last12_owner_goal_metrics"]
    lines = [
        "# A1 XAU H4 D1 Compression Frequency Mechanics Exact Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester probe in isolated root. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Preregistration: `{payload['scope']['preregistration']}`",
        f"- Baseline probe JSON: `{payload['scope']['baseline_probe']}`",
        f"- Period: `{payload['scope']['period']}`",
        f"- Tester currency: `{payload['scope'].get('tester_currency', 'USD')}`",
        f"- Variant count: `{payload['scope']['variant_count']}`",
        "",
        "## Owner Frontier",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L USD | Max DD USD | Last12 WR/WL | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        render_metric_row(
            "baseline_one_position_prior_exact",
            baseline_metrics,
            baseline_last12,
            row_decision(baseline_metrics),
        ),
    ]
    for result in payload["variants"]:
        metrics = result["owner_goal_metrics"]
        last12 = result["last12_owner_goal_metrics"]
        lines.append(render_metric_row(result["name"], metrics, last12, row_decision(metrics)))

    lines.extend(
        [
            "",
            "## Ledger Counts",
            "",
            "### `baseline_one_position_prior_exact`",
            "",
        ]
    )
    lines.extend(render_counts(baseline))
    for result in payload["variants"]:
        lines.extend(["", f"### `{result['name']}`", ""])
        lines.extend(render_counts(result))

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

    lines.extend(["## Verdict", ""])
    if payload["status"] == "CORE_SHAPE_SURVIVES_FREQUENCY_GAP":
        lines.append(
            "The core WR/W-L shape survived at a higher max-open cap, but active-day frequency is still below the owner goal. Treat this as a component clue, not a demo candidate."
        )
    elif payload["status"] == "OWNER_GOAL_HIT_REVIEW_REQUIRED":
        lines.append(
            "An expanded exact MT5 row reached the owner goal. Freeze artifacts and prepare a reviewer package before any demo specification."
        )
    elif payload["status"] == "NEAR_MISS_FREQUENCY_MECHANICS":
        lines.append(
            "The frequency-mechanics expansion produced only a near miss. Do not spend the reviewer token on this result."
        )
    else:
        lines.append(
            "Relaxing the one-position bottleneck did not preserve the hard WR >= 50% and W/L >= 2.0 core shape. Reject this branch for owner-goal use."
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact MT5 D1 compression/H4 expansion frequency-mechanics probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(BASELINE_JSON)
    a1.VARIANTS = VARIANTS
    report_md = REPORTS / "A1_XAU_H4_D1_COMPRESSION_FREQUENCY_MECHANICS_202207_202606.md"
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
