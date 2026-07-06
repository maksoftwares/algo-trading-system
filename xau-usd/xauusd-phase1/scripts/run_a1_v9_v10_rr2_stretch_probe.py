from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
DEFAULT_FROM_DATE = "2022.07.01"
DEFAULT_TO_DATE = "2026.06.30"
DEFAULT_TAG = "OWNER_GOAL_V9V10_RR2_202207_202606"


VARIANTS = [
    a1.Variant(
        name="v9_sweep_h1_long_rr2p0",
        label="V9 sweep-reclaim, H1 trend, long-only, stretched to 2.0R",
        run_id="BT_A1_XAU_M5_MOM_V9_SWEEP_H1_LONG_RR2P0_OWNER_GOAL",
        tester_inputs={
            "InpSignalMode": "3",
            "InpDirectionMode": "1",
            "InpUseH1TrendFilter": "true",
            "InpH1TrendMinSlopePoints": "0",
            "InpUseH4TrendFilter": "false",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.05",
            "InpSweepLookbackBars": "12",
            "InpSweepAtrMultiple": "0.10",
            "InpReclaimAtrMultiple": "0.05",
            "InpMinRangeAtr": "0.40",
            "InpMinBodyFraction": "0.35",
            "InpLongCloseLocation": "0.58",
            "InpMaxTradesPerDay": "24",
            "InpCooldownMinutes": "0",
        },
    ),
    a1.Variant(
        name="v9_sweep_h1h4_long_rr2p0_v4mask",
        label="V9 sweep-reclaim, H1+H4 trend, long-only, V4 weak-hour mask, stretched to 2.0R",
        run_id="BT_A1_XAU_M5_MOM_V9_SWEEP_H1H4_LONG_RR2P0_V4MASK_OWNER_GOAL",
        tester_inputs={
            "InpSignalMode": "3",
            "InpDirectionMode": "1",
            "InpUseH1TrendFilter": "true",
            "InpH1TrendMinSlopePoints": "0",
            "InpUseH4TrendFilter": "true",
            "InpH4TrendMinSlopePoints": "0",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.05",
            "InpBlockedEntryHoursCsv": "2,9,10,11,12,13,17,19,21,23",
            "InpSweepLookbackBars": "12",
            "InpSweepAtrMultiple": "0.10",
            "InpReclaimAtrMultiple": "0.05",
            "InpMinRangeAtr": "0.40",
            "InpMinBodyFraction": "0.35",
            "InpLongCloseLocation": "0.58",
            "InpMaxTradesPerDay": "24",
            "InpCooldownMinutes": "0",
        },
    ),
    a1.Variant(
        name="v10_or_london_h1h4_both_rr2p0",
        label="V10 London opening-range continuation, H1+H4 trend, both directions, stretched to 2.0R",
        run_id="BT_A1_XAU_M5_MOM_V10_OR_LONDON_H1H4_BOTH_RR2P0_OWNER_GOAL",
        tester_inputs={
            "InpSignalMode": "4",
            "InpDirectionMode": "0",
            "InpUseH1TrendFilter": "true",
            "InpH1TrendMinSlopePoints": "0",
            "InpUseH4TrendFilter": "true",
            "InpH4TrendMinSlopePoints": "0",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.05",
            "InpOpeningRangeStartHour": "7",
            "InpOpeningRangeMinutes": "60",
            "InpOpeningTradeWindowHours": "5",
            "InpOpeningBreakAtrMultiple": "0.10",
            "InpMinRangeAtr": "0.40",
            "InpMinBodyFraction": "0.35",
            "InpLongCloseLocation": "0.60",
            "InpShortCloseLocation": "0.40",
            "InpMinThreeBarMoveAtr": "0.20",
            "InpMaxTradesPerDay": "24",
            "InpCooldownMinutes": "0",
        },
    ),
    a1.Variant(
        name="v10_or_asia_h1h4_long_rr2p0",
        label="V10 Asia opening-range continuation, H1+H4 trend, long-only, stretched to 2.0R",
        run_id="BT_A1_XAU_M5_MOM_V10_OR_ASIA_H1H4_LONG_RR2P0_OWNER_GOAL",
        tester_inputs={
            "InpSignalMode": "4",
            "InpDirectionMode": "1",
            "InpUseH1TrendFilter": "true",
            "InpH1TrendMinSlopePoints": "0",
            "InpUseH4TrendFilter": "true",
            "InpH4TrendMinSlopePoints": "0",
            "InpRiskReward": "2.00",
            "InpMaxEstimatedCostR": "0.05",
            "InpOpeningRangeStartHour": "2",
            "InpOpeningRangeMinutes": "60",
            "InpOpeningTradeWindowHours": "5",
            "InpOpeningBreakAtrMultiple": "0.10",
            "InpMinRangeAtr": "0.40",
            "InpMinBodyFraction": "0.35",
            "InpLongCloseLocation": "0.60",
            "InpMinThreeBarMoveAtr": "0.20",
            "InpMaxTradesPerDay": "24",
            "InpCooldownMinutes": "0",
        },
    ),
]


def parse_mt5_date(value: str) -> date:
    return datetime.strptime(value, "%Y.%m.%d").date()


def trading_weekday_count(start: date, end: date) -> int:
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current = date.fromordinal(current.toordinal() + 1)
    return days


def parse_money(value: str) -> float:
    return float((value or "0").replace(" ", ""))


def read_trade_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["profit_float"] = parse_money(row.get("profit_aed", "0"))
        row["entry_date_obj"] = datetime.strptime(row["entry_date"], "%Y-%m-%d").date()
    return rows


def max_closed_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def owner_metrics(rows: list[dict[str, Any]], from_date: str, to_date: str) -> dict[str, Any]:
    start = parse_mt5_date(from_date)
    end = parse_mt5_date(to_date)
    profits = [float(row["profit_float"]) for row in rows]
    wins = [value for value in profits if value > 0]
    losses = [-value for value in profits if value < 0]
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    active_dates = {row["entry_date_obj"] for row in rows}
    weekdays = trading_weekday_count(start, end)
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    wl_ratio = avg_win / avg_loss if avg_loss else None
    active_day_pct = len(active_dates) / weekdays * 100.0 if weekdays else 0.0
    sorted_pnl = sorted(profits, reverse=True)
    return {
        "trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(len(wins) / len(rows) * 100.0, 2) if rows else 0.0,
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "avg_win_loss_ratio": round(wl_ratio, 4) if wl_ratio is not None else None,
        "manual_pnl": round(sum(profits), 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "active_days": len(active_dates),
        "market_weekdays": weekdays,
        "active_day_pct": round(active_day_pct, 2),
        "max_closed_dd": round(max_closed_drawdown(profits), 2),
        "top10_removed": round(sum(sorted_pnl[10:]) if len(sorted_pnl) > 10 else sum(sorted_pnl), 2),
        "top25_removed": round(sum(sorted_pnl[25:]) if len(sorted_pnl) > 25 else sum(sorted_pnl), 2),
        "owner_core_shape_pass": bool(rows and len(wins) / len(rows) * 100.0 >= 50.0 and wl_ratio is not None and wl_ratio >= 2.0),
        "owner_daily_frequency_pass": active_day_pct >= 90.0,
    }


def last12_metrics(rows: list[dict[str, Any]], to_date: str) -> dict[str, Any]:
    end = parse_mt5_date(to_date)
    start = date(end.year - 1, end.month, end.day)
    subset = [row for row in rows if row["entry_date_obj"] >= start]
    return owner_metrics(subset, start.strftime("%Y.%m.%d"), to_date)


def enrich_payload(payload: dict[str, Any], from_date: str, to_date: str) -> dict[str, Any]:
    for result in payload["variants"]:
        rows = read_trade_csv(Path(result["trade_csv"]))
        result["owner_goal_metrics"] = owner_metrics(rows, from_date, to_date)
        result["last12_owner_goal_metrics"] = last12_metrics(rows, to_date)
    payload["winner"] = choose_owner_winner(payload["variants"])
    payload["scope"]["family"] = "A1 V9/V10 RR2 stretch probe"
    payload["scope"]["anti_overfit_boundary"] = "Four preregistered RR2 stretch variants only; no optimizer, no threshold sweep."
    payload["scope"]["review_spend_rule"] = "Do not spend reviewer unless a row reaches WR >= 50% and realized W/L >= 2.0."
    payload["scope"]["preregistration"] = str(
        PHASE1_ROOT / "docs" / "A1_XAU_M5_V9_V10_RR2_STRETCH_PROBE_PREREG_2026_07_05.md"
    )
    return payload


def choose_owner_winner(results: list[dict[str, Any]]) -> dict[str, Any]:
    full_hits = [
        result
        for result in results
        if result["owner_goal_metrics"]["owner_core_shape_pass"]
        and result["owner_goal_metrics"]["owner_daily_frequency_pass"]
    ]
    if full_hits:
        best = max(full_hits, key=lambda item: item["owner_goal_metrics"]["manual_pnl"])
        return {"status": "OWNER_GOAL_HIT_REVIEW_REQUIRED", "best_variant": best["name"]}
    core_hits = [result for result in results if result["owner_goal_metrics"]["owner_core_shape_pass"]]
    if core_hits:
        best = max(core_hits, key=lambda item: item["owner_goal_metrics"]["active_day_pct"])
        return {"status": "CORE_SHAPE_HIT_FREQUENCY_GAP", "best_variant": best["name"]}
    near = [
        result
        for result in results
        if result["owner_goal_metrics"]["win_rate_pct"] >= 48.0
        and (result["owner_goal_metrics"]["avg_win_loss_ratio"] or 0.0) >= 1.9
    ]
    if near:
        best = max(near, key=lambda item: (item["owner_goal_metrics"]["win_rate_pct"], item["owner_goal_metrics"]["manual_pnl"]))
        return {"status": "NEAR_MISS_NO_REVIEW_YET", "best_variant": best["name"]}
    best = max(results, key=lambda item: item["owner_goal_metrics"]["manual_pnl"]) if results else None
    return {
        "status": "REJECT_NO_OWNER_GOAL_HIT",
        "best_variant": best["name"] if best else "",
        "review_recommendation": "Do not spend reviewer; no row reaches core WR/W-L shape.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    currency = payload.get("scope", {}).get("tester_currency", "USD")
    lines = [
        "# A1 XAU M5 V9/V10 RR2 Stretch Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester probe in isolated root. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['winner']['status']}`",
        "",
        f"- Preregistration: `{payload['scope']['preregistration']}`",
        f"- Period: `{payload['scope']['period']}`",
        f"- Tester currency: `{currency}`",
        f"- Variant count: `{payload['scope']['variant_count']}`",
        "",
        "## Owner Frontier",
        "",
        "| Variant | Trades | WR% | W/L | Active% | PF | Manual P&L | Max DD | Last12 WR/WL | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for result in payload["variants"]:
        metrics = result["owner_goal_metrics"]
        last12 = result["last12_owner_goal_metrics"]
        decision = "CORE_SHAPE" if metrics["owner_core_shape_pass"] else "FAIL_SHAPE"
        if metrics["owner_core_shape_pass"] and metrics["owner_daily_frequency_pass"]:
            decision = "OWNER_GOAL"
        elif metrics["win_rate_pct"] >= 48.0 and (metrics["avg_win_loss_ratio"] or 0.0) >= 1.9:
            decision = "NEAR"
        lines.append(
            f"| `{result['name']}` | {metrics['trades']} | {metrics['win_rate_pct']:.2f} | "
            f"{metrics['avg_win_loss_ratio'] or 0.0:.4f} | {metrics['active_day_pct']:.2f} | "
            f"{metrics['profit_factor'] or 0.0:.4f} | {metrics['manual_pnl']:.2f} | "
            f"{metrics['max_closed_dd']:.2f} | {last12['win_rate_pct']:.2f}/{last12['avg_win_loss_ratio'] or 0.0:.2f} | "
            f"`{decision}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
        ]
    )
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
    lines.extend(
        [
            "## Verdict",
            "",
        ]
    )
    if payload["winner"]["status"] == "REJECT_NO_OWNER_GOAL_HIT":
        lines.append("No V9/V10 stretched row reaches the owner core shape. Do not spend reviewer tokens on this probe.")
    elif payload["winner"]["status"] == "NEAR_MISS_NO_REVIEW_YET":
        lines.append("A near miss exists, but it is not review-worthy unless a follow-up frozen test reaches core shape.")
    else:
        lines.append("Core owner shape was reached. Package source/configs/ledgers before spending the reviewer token.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run preregistered A1 V9/V10 RR2 owner-goal stretch probe.")
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE)
    parser.add_argument("--to-date", default=DEFAULT_TO_DATE)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    parser.add_argument("--deposit", default="1000")
    parser.add_argument("--currency", default="USD")
    args = parser.parse_args()

    safe_tag = a1.safe_name(args.tag)
    report_md = REPORTS / f"A1_XAU_M5_V9_V10_RR2_STRETCH_PROBE_{safe_tag}.md"
    report_json = report_md.with_suffix(".json")

    a1.VARIANTS = VARIANTS
    payload = a1.run_variants(
        from_date=args.from_date,
        to_date=args.to_date,
        tag=safe_tag,
        report_md=report_md,
        report_json=report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit=args.deposit,
        currency=args.currency,
    )
    payload = enrich_payload(payload, args.from_date, args.to_date)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"winner": payload["winner"], "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
