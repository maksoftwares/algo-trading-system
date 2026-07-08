from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, rel, summary_metrics
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, weekly_exit_shape, write_signal_csv
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
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_SHORT_LOWER_HIGH_WR50_RR2_20260708"
TAG = "OWNER_GOAL_SHORT_LOWER_HIGH_WR50_RR2_202207_202606"

COMMON_INPUTS = {
    "InpDirectionMode": "2",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.05",
    "InpMaxTradesPerDay": "24",
    "InpCooldownMinutes": "0",
    "InpBlockedEntryHoursCsv": "",
    "InpBlockedEntryDayHoursCsv": "",
    "InpBlockedLongEntryHoursCsv": "",
    "InpBlockedShortEntryHoursCsv": "",
    "InpSignalMode": "17",
    "InpD1SupportStateGateMode": "0",
    "InpD1StructuralDownGateEnabled": "true",
    "InpD1StructuralDownEmaPeriod": "50",
    "InpD1StructuralDownSlopeLagBars": "5",
    "InpUseH1TrendFilter": "true",
    "InpUseH4TrendFilter": "true",
    "InpH1TrendApplyToShort": "true",
    "InpH4TrendApplyToShort": "true",
    "InpH1TrendMinSlopePoints": "0",
    "InpH4TrendMinSlopePoints": "0",
    "InpStopFloorPoints": "350",
    "InpStopCeilingPoints": "2200",
}


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="lower_high_lh1_base",
            label="Lower-high failed-rally base, RR2",
            run_id="BT_A1_XAU_SHORT_LOWER_HIGH_LH1_BASE",
            tester_inputs={
                **COMMON_INPUTS,
                "InpPullbackEmaPeriod": "20",
                "InpShortCloseLocation": "0.25",
                "InpBearLowerHighLookbackBars": "48",
                "InpBearLowerHighRecentBars": "12",
                "InpBearLowerHighMinGapAtr": "0.25",
                "InpBearLowerHighMinDropAtr": "0.80",
                "InpBearLowerHighEmaTouchAtr": "0.20",
                "InpBearLowerHighReclaimAtr": "0.05",
                "InpBearLowerHighStopBufferAtr": "0.25",
                "InpBearLowerHighMinBodyFraction": "0.45",
            },
        ),
        a1.Variant(
            name="lower_high_lh2_deeper_drop",
            label="Lower-high failed-rally deeper prior drop, RR2",
            run_id="BT_A1_XAU_SHORT_LOWER_HIGH_LH2_DEEPER_DROP",
            tester_inputs={
                **COMMON_INPUTS,
                "InpPullbackEmaPeriod": "20",
                "InpShortCloseLocation": "0.25",
                "InpBearLowerHighLookbackBars": "72",
                "InpBearLowerHighRecentBars": "14",
                "InpBearLowerHighMinGapAtr": "0.35",
                "InpBearLowerHighMinDropAtr": "1.20",
                "InpBearLowerHighEmaTouchAtr": "0.25",
                "InpBearLowerHighReclaimAtr": "0.05",
                "InpBearLowerHighStopBufferAtr": "0.25",
                "InpBearLowerHighMinBodyFraction": "0.45",
            },
        ),
        a1.Variant(
            name="lower_high_lh3_tighter_reject",
            label="Lower-high failed-rally tighter rejection, RR2",
            run_id="BT_A1_XAU_SHORT_LOWER_HIGH_LH3_TIGHTER_REJECT",
            tester_inputs={
                **COMMON_INPUTS,
                "InpPullbackEmaPeriod": "20",
                "InpShortCloseLocation": "0.20",
                "InpBearLowerHighLookbackBars": "48",
                "InpBearLowerHighRecentBars": "10",
                "InpBearLowerHighMinGapAtr": "0.30",
                "InpBearLowerHighMinDropAtr": "1.00",
                "InpBearLowerHighEmaTouchAtr": "0.15",
                "InpBearLowerHighReclaimAtr": "0.10",
                "InpBearLowerHighStopBufferAtr": "0.25",
                "InpBearLowerHighMinBodyFraction": "0.55",
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


def pass_checks(metrics: dict[str, Any], stress: dict[str, Any], year_rows: list[dict[str, Any]], concentration: dict[str, Any]) -> dict[str, bool]:
    net_2023_2024 = sum(float(row["net"]) for row in year_rows if row["period"] in {"2023", "2024"})
    return {
        "wr_ge_50": metrics["win_rate_pct"] >= 50.0,
        "wl_ge_1p90": (metrics["avg_win_loss"] or 0.0) >= 1.90,
        "trades_ge_100": metrics["signals"] >= 100,
        "net_gt_0": metrics["net_usd"] > 0.0,
        "stress_net_gt_0": stress["net_usd"] > 0.0,
        "stress_pf_ge_1p15": (stress["profit_factor"] or 0.0) >= 1.15,
        "y2023_2024_net_ge_0": net_2023_2024 >= 0.0,
        "top10_removed_net_gt_0": concentration["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": concentration["top3_days_removed_net"] > 0.0,
    }


def summarize_variant(result: dict[str, Any]) -> dict[str, Any]:
    rows = variant_rows(result)
    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_exit_shape(rows)
    concentration = concentration_stats(rows, metrics["net_usd"])
    year_rows = [period_metric_row(result["name"], label, rows, start, end) for label, start, end in YEAR_PERIODS]
    block_rows = [period_metric_row(result["name"], label, rows, start, end) for label, start, end in BLOCK_PERIODS]
    checks = pass_checks(metrics, stress, year_rows, concentration)
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
        "net_2023_2024": round(sum(float(row["net"]) for row in year_rows if row["period"] in {"2023", "2024"}), 2),
        "top10_removed_net": concentration["top10_removed_net"],
        "top3_days_removed_net": concentration["top3_days_removed_net"],
        "best_day_share_pct": concentration["best_day_share_pct"],
        "checks": checks,
        "pass": all(checks.values()),
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
        "# A1 XAU Lower-High Short WR50 RR2 Exact MT5 Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: purpose-built lower-high failed-rally short signal, fixed RR2, exact MT5. No hour/session/day/month masks.",
        "",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Results",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | 2023+2024 | Top10-removed | Top3-days-removed | Pos weeks% | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["summary_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {(row['wl'] or 0.0):.4f} | "
            f"{(row['pf'] or 0.0):.4f} | {row['net']:.2f} | {(row['stress_030_pf'] or 0.0):.4f} | "
            f"{row['stress_030_net']:.2f} | {row['net_2023_2024']:.2f} | {row['top10_removed_net']:.2f} | "
            f"{row['top3_days_removed_net']:.2f} | {row['positive_week_pct']:.2f} | {bool_text(row['pass'])} |"
        )

    lines.extend(["", "## Gate Failures", ""])
    for row in payload["summary_rows"]:
        failed = [key for key, value in row["checks"].items() if not value]
        lines.append(f"- `{row['variant']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Decision", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 lower-high short WR50/RR2 probe.")
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

    summaries = [summarize_variant(result) for result in mt5_payload["variants"]]
    flat_rows = [flat_row(summary) for summary in summaries]
    year_rows = [row for summary in summaries for row in summary["year_rows"]]
    block_rows = [row for summary in summaries for row in summary["block_rows"]]

    write_csv(summary_csv, flat_rows)
    write_csv(year_csv, year_rows)
    write_csv(block_csv, block_rows)
    for summary in summaries:
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{summary['variant']}_NORMALIZED_TRADES.csv", summary["rows"])

    passers = [summary for summary in summaries if summary["pass"]]
    if passers:
        status = "LOWER_HIGH_SHORT_WR50_RR2_REVIEW_CANDIDATE"
        best = sorted(passers, key=lambda row: (-row["wr"], -row["net"]))[0]
        interpretation = f"`{best['variant']}` passed the lower-high WR50/RR2 gate. Research-only until reviewer sign-off."
    else:
        status = "NO_LOWER_HIGH_SHORT_WR50_RR2_SURVIVOR"
        best_wr = max(summaries, key=lambda row: row["wr"]) if summaries else None
        best_net = max(summaries, key=lambda row: row["net"]) if summaries else None
        interpretation = (
            f"No lower-high variant reached the hard WR50/RR2 gate. Best WR was `{best_wr['variant']}` at "
            f"{best_wr['wr']:.2f}% with {best_wr['trades']} trades. Best net was `{best_net['variant']}` at "
            f"{best_net['net']:.2f} USD. The hard target remains unsolved."
        )

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
        outputs[f"{summary['variant']}_normalized_trades_csv"] = str(REPORTS_DIR / f"{OUTPUT_STEM}_{summary['variant']}_NORMALIZED_TRADES.csv")

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
                "trade_rows": len(next(summary for summary in summaries if summary["variant"] == result["name"])["rows"]),
                "mt5_result": result,
                "guard_counts": guard_counts(result),
            }
            for result in mt5_payload["variants"]
        ],
        "summary_rows": summaries,
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "summary": flat_rows, "report": str(report_md)}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
