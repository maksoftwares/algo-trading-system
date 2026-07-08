from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, rel, summary_metrics
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, weekly_exit_shape, write_signal_csv
from run_a1_h4_d1_review_repair_exact import RECENT3_END, RECENT3_START, period_stats
from run_a1_short_v2_robustness_probe import (
    BLOCK_PERIODS,
    YEAR_PERIODS,
    bool_text,
    concentration_stats,
    guard_counts,
    period_metric_row,
    variant_rows,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708"
TAG = "OWNER_GOAL_SHORT_DOWNSIDE_IMPULSE_RETEST_202207_202606"
Q2_START = date(2026, 4, 1)
Q2_END = date(2026, 6, 30)

COMMON_INPUTS = {
    "InpDirectionMode": "2",
    "InpSignalMode": "19",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.05",
    "InpMaxTradesPerDay": "24",
    "InpCooldownMinutes": "0",
    "InpBlockedEntryHoursCsv": "",
    "InpBlockedEntryDayHoursCsv": "",
    "InpBlockedLongEntryHoursCsv": "",
    "InpBlockedShortEntryHoursCsv": "",
    "InpBearRetestLookbackBars": "10",
    "InpBearRetestSupportLookbackBars": "12",
    "InpBearRetestBreakAtr": "0.10",
    "InpBearRetestTouchAtr": "0.05",
    "InpBearRetestReclaimAtr": "0.05",
    "InpBearRetestStopBufferAtr": "0.25",
    "InpBearRetestMinBodyFraction": "0.35",
    "InpShortCloseLocation": "0.35",
    "InpBearImpulseRetestImpulseBars": "3",
    "InpBearImpulseRetestMinImpulseAtr": "1.20",
    "InpBearImpulseRetestBreakMinBodyFraction": "0.45",
    "InpStopFloorPoints": "350",
    "InpStopCeilingPoints": "2200",
}


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="short_v4_impulse_retest_d1_nonup_h1h4",
            label="V4 downside impulse retest: D1 non-up plus H1/H4 downtrend",
            run_id="BT_A1_XAU_SHORT_V4_IMPULSE_RETEST_D1_NONUP_H1H4",
            tester_inputs={
                **COMMON_INPUTS,
                "InpD1SupportStateGateMode": "4",
                "InpD1SupportStateEmaPeriod": "20",
                "InpD1SupportStateSlopeLagBars": "5",
                "InpD1StructuralDownGateEnabled": "false",
                "InpUseH1TrendFilter": "true",
                "InpH1TrendApplyToShort": "true",
                "InpH1TrendMinSlopePoints": "0",
                "InpUseH4TrendFilter": "true",
                "InpH4TrendApplyToShort": "true",
                "InpH4TrendMinSlopePoints": "0",
            },
        ),
        a1.Variant(
            name="short_v4_impulse_retest_d1_structural_h1h4",
            label="V4 downside impulse retest: D1 EMA50 structural down plus H1/H4 downtrend",
            run_id="BT_A1_XAU_SHORT_V4_IMPULSE_RETEST_D1_STRUCTURAL_H1H4",
            tester_inputs={
                **COMMON_INPUTS,
                "InpD1SupportStateGateMode": "0",
                "InpD1StructuralDownGateEnabled": "true",
                "InpD1StructuralDownEmaPeriod": "50",
                "InpD1StructuralDownSlopeLagBars": "5",
                "InpUseH1TrendFilter": "true",
                "InpH1TrendApplyToShort": "true",
                "InpH1TrendMinSlopePoints": "0",
                "InpUseH4TrendFilter": "true",
                "InpH4TrendApplyToShort": "true",
                "InpH4TrendMinSlopePoints": "0",
            },
        ),
        a1.Variant(
            name="short_v4_impulse_retest_d1_nonup_h1_only",
            label="V4 downside impulse retest: D1 non-up plus H1 downtrend only",
            run_id="BT_A1_XAU_SHORT_V4_IMPULSE_RETEST_D1_NONUP_H1_ONLY",
            tester_inputs={
                **COMMON_INPUTS,
                "InpD1SupportStateGateMode": "4",
                "InpD1SupportStateEmaPeriod": "20",
                "InpD1SupportStateSlopeLagBars": "5",
                "InpD1StructuralDownGateEnabled": "false",
                "InpUseH1TrendFilter": "true",
                "InpH1TrendApplyToShort": "true",
                "InpH1TrendMinSlopePoints": "0",
                "InpUseH4TrendFilter": "false",
            },
        ),
    ]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def checks_for(
    metrics: dict[str, Any],
    stress: dict[str, Any],
    q2: dict[str, Any],
    recent3: dict[str, Any],
    year_rows: list[dict[str, Any]],
    concentration: dict[str, Any],
) -> dict[str, bool]:
    net_2023_2024 = sum(float(row["net"]) for row in year_rows if row["period"] in {"2023", "2024"})
    positive_years = sum(1 for row in year_rows if float(row["net"]) > 0.0)
    return {
        "wr_ge_50": metrics["win_rate_pct"] >= 50.0,
        "wl_ge_1p90": (metrics["avg_win_loss"] or 0.0) >= 1.90,
        "trades_ge_75": metrics["signals"] >= 75,
        "net_gt_0": metrics["net_usd"] > 0.0,
        "stress_net_gt_0": stress["net_usd"] > 0.0,
        "stress_pf_ge_1p15": (stress["profit_factor"] or 0.0) >= 1.15,
        "q2_2026_net_gt_0": q2["net_usd"] > 0.0,
        "recent3_net_gt_0": recent3["net_usd"] > 0.0,
        "y2023_2024_net_ge_0": net_2023_2024 >= 0.0,
        "positive_year_buckets_ge_3": positive_years >= 3,
        "top10_removed_net_gt_0": concentration["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": concentration["top3_days_removed_net"] > 0.0,
    }


def summarize(result: dict[str, Any]) -> dict[str, Any]:
    rows = variant_rows(result)
    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_exit_shape(rows)
    q2 = period_stats(rows, Q2_START, Q2_END)
    recent3 = period_stats(rows, RECENT3_START, RECENT3_END)
    concentration = concentration_stats(rows, metrics["net_usd"])
    year_rows = [period_metric_row(result["name"], label, rows, start, end) for label, start, end in YEAR_PERIODS]
    block_rows = [period_metric_row(result["name"], label, rows, start, end) for label, start, end in BLOCK_PERIODS]
    checks = checks_for(metrics, stress, q2, recent3, year_rows, concentration)
    return {
        "variant": result["name"],
        "trades": metrics["signals"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_pf": stress["profit_factor"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_net": stress["net_usd"],
        "positive_week_pct": shape["positive_week_pct"],
        "worst_week": shape["worst_week_usd"],
        "q2_2026_net": q2["net_usd"],
        "recent3_net": recent3["net_usd"],
        "net_2023_2024": round(sum(float(row["net"]) for row in year_rows if row["period"] in {"2023", "2024"}), 2),
        "positive_year_buckets": sum(1 for row in year_rows if float(row["net"]) > 0.0),
        "top10_removed_net": concentration["top10_removed_net"],
        "top3_days_removed_net": concentration["top3_days_removed_net"],
        "best_day_share_pct": concentration["best_day_share_pct"],
        "checks": checks,
        "pass": all(checks.values()),
        "near_wr_watchlist": metrics["win_rate_pct"] >= 45.0 and (metrics["avg_win_loss"] or 0.0) >= 1.90,
        "year_rows": year_rows,
        "block_rows": block_rows,
        "rows": rows,
    }


def flat_row(summary: dict[str, Any]) -> dict[str, Any]:
    out = {key: value for key, value in summary.items() if key not in {"checks", "year_rows", "block_rows", "rows"}}
    out.update({f"check_{key}": value for key, value in summary["checks"].items()})
    return out


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Short Downside Impulse Retest Exact MT5 Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: standalone short-specialist test from the TradingView chart idea: downside impulse, failed retest, short-only, fixed 2R. No hour/session/day/month masks were used.",
        "",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Result",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | Q2-2026 | Recent3 | 2023+2024 | Year+ | Top10-removed | Top3-days-removed | Pos weeks% | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["summary_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {(row['wl'] or 0.0):.4f} | "
            f"{(row['pf'] or 0.0):.4f} | {row['net']:.2f} | {(row['stress_030_pf'] or 0.0):.4f} | "
            f"{row['stress_030_net']:.2f} | {row['q2_2026_net']:.2f} | {row['recent3_net']:.2f} | "
            f"{row['net_2023_2024']:.2f} | {row['positive_year_buckets']} | {row['top10_removed_net']:.2f} | "
            f"{row['top3_days_removed_net']:.2f} | {row['positive_week_pct']:.2f} | {bool_text(row['pass'])} |"
        )

    lines.extend(["", "## Gate Failures", ""])
    for row in payload["summary_rows"]:
        failed = [key for key, value in row["checks"].items() if not value]
        lines.append(f"- `{row['variant']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## By Year", "", "| Variant | Year | Trades | WR% | W/L | PF | Net |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"])
    for row in payload["summary_rows"]:
        for year_row in row["year_rows"]:
            lines.append(
                f"| `{row['variant']}` | {year_row['period']} | {year_row['trades']} | {year_row['wr']:.2f} | "
                f"{(year_row['wl'] or 0.0):.4f} | {(year_row['pf'] or 0.0):.4f} | {year_row['net']:.2f} |"
            )

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 XAU downside impulse retest short probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    if not PREREG.exists():
        raise FileNotFoundError(PREREG)

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    summary_csv = REPORTS_DIR / f"{OUTPUT_STEM}_SUMMARY.csv"
    year_csv = REPORTS_DIR / f"{OUTPUT_STEM}_YEAR.csv"
    block_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BLOCK.csv"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.json"

    a1.VARIANTS = build_variants()
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

    summaries = [summarize(result) for result in mt5_payload["variants"]]
    write_csv(summary_csv, [flat_row(summary) for summary in summaries])
    write_csv(year_csv, [row for summary in summaries for row in summary["year_rows"]])
    write_csv(block_csv, [row for summary in summaries for row in summary["block_rows"]])

    outputs = {
        "md": str(report_md),
        "json": str(report_json),
        "summary_csv": str(summary_csv),
        "year_csv": str(year_csv),
        "block_csv": str(block_csv),
        "mt5_components_md": str(mt5_report_md),
        "mt5_components_json": str(mt5_report_json),
    }
    for summary in summaries:
        normalized_trades = REPORTS_DIR / f"{OUTPUT_STEM}_{summary['variant']}_NORMALIZED_TRADES.csv"
        write_signal_csv(normalized_trades, summary["rows"])
        outputs[f"{summary['variant']}_normalized_trades_csv"] = str(normalized_trades)

    passers = [row for row in summaries if row["pass"]]
    if passers:
        best = max(passers, key=lambda row: (row["wr"], row["net"]))
        status = "SHORT_IMPULSE_RETEST_WR50_RR2_REVIEW_CANDIDATE"
        interpretation = (
            f"`{best['variant']}` passed the standalone WR50/RR2 gate. Keep research-only and request reviewer sign-off "
            "before any combined-book or demo-spec discussion."
        )
    else:
        near = [row for row in summaries if row["near_wr_watchlist"]]
        if near:
            best = max(near, key=lambda row: (row["wr"], row["net"]))
            status = "SHORT_IMPULSE_RETEST_NEAR_WR_WATCHLIST_ONLY"
            interpretation = (
                f"No variant passed all standalone gates. `{best['variant']}` reached the near-WR watchlist band "
                f"with WR {best['wr']:.2f}% and W/L {(best['wl'] or 0.0):.4f}, but failed one or more durability gates. "
                "Do not tune hours/months from this ledger."
            )
        else:
            best = max(summaries, key=lambda row: (row["wr"], row["net"]))
            status = "SHORT_IMPULSE_RETEST_NO_STANDALONE_SURVIVOR"
            interpretation = (
                f"No downside-impulse retest variant reached the standalone short objective. Best WR was "
                f"`{best['variant']}` at {best['wr']:.2f}% with W/L {(best['wl'] or 0.0):.4f}. "
                "The TradingView idea is useful as a visual hypothesis, but this exact-MT5 pass did not prove it as a standalone short expert."
            )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_component_details": [
            {
                "variant": result["name"],
                "trade_rows": len(summary["rows"]),
                "guard_counts": guard_counts(result),
                "mt5_result": result,
            }
            for result, summary in zip(mt5_payload["variants"], summaries, strict=True)
        ],
        "summary_rows": summaries,
        "interpretation": interpretation,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
