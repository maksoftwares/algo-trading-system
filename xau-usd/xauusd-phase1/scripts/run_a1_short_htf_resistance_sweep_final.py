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
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_FINAL_20260708"
TAG = "OWNER_GOAL_SHORT_HTF_RESISTANCE_SWEEP_FINAL_202207_202606"


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="short_htf_resistance_sweep_reclaim_rr2",
            label="Final WR50/RR2 falsification: M15 reclaim of HTF resistance sweep",
            run_id="BT_A1_XAU_SHORT_HTF_RESISTANCE_SWEEP_RECLAIM_RR2",
            tester_inputs={
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
                "InpSignalMode": "18",
                "InpD1SupportStateGateMode": "4",
                "InpD1SupportStateEmaPeriod": "20",
                "InpD1SupportStateSlopeLagBars": "5",
                "InpD1StructuralDownGateEnabled": "false",
                "InpBearHtfResistanceH4LookbackBars": "30",
                "InpBearHtfResistanceReclaimBars": "6",
                "InpBearHtfResistanceH4AtrPeriod": "14",
                "InpBearHtfResistanceSweepH4Atr": "0.10",
                "InpBearHtfResistanceStopH4Atr": "0.10",
                "InpBearHtfResistanceMinBodyFraction": "0.35",
                "InpBearHtfResistanceCloseLocation": "0.35",
                "InpStopFloorPoints": "350",
                "InpStopCeilingPoints": "2200",
            },
        )
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


def checks_for(metrics: dict[str, Any], stress: dict[str, Any], year_rows: list[dict[str, Any]], concentration: dict[str, Any]) -> dict[str, bool]:
    net_2023_2024 = sum(float(row["net"]) for row in year_rows if row["period"] in {"2023", "2024"})
    positive_years = sum(1 for row in year_rows if float(row["net"]) > 0.0)
    return {
        "wr_ge_50": metrics["win_rate_pct"] >= 50.0,
        "wr_ge_45_watchlist": metrics["win_rate_pct"] >= 45.0,
        "wl_ge_1p90": (metrics["avg_win_loss"] or 0.0) >= 1.90,
        "trades_ge_100": metrics["signals"] >= 100,
        "pf_ge_1p20": (metrics["profit_factor"] or 0.0) >= 1.20,
        "stress_pf_ge_1p15": (stress["profit_factor"] or 0.0) >= 1.15,
        "stress_net_gt_0": stress["net_usd"] > 0.0,
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
    concentration = concentration_stats(rows, metrics["net_usd"])
    year_rows = [period_metric_row(result["name"], label, rows, start, end) for label, start, end in YEAR_PERIODS]
    block_rows = [period_metric_row(result["name"], label, rows, start, end) for label, start, end in BLOCK_PERIODS]
    checks = checks_for(metrics, stress, year_rows, concentration)
    non_wr_checks = {key: value for key, value in checks.items() if key not in {"wr_ge_50", "wr_ge_45_watchlist"}}
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
        "positive_year_buckets": sum(1 for row in year_rows if float(row["net"]) > 0.0),
        "top10_removed_net": concentration["top10_removed_net"],
        "top3_days_removed_net": concentration["top3_days_removed_net"],
        "best_day_share_pct": concentration["best_day_share_pct"],
        "checks": checks,
        "true_pass": checks["wr_ge_50"] and all(non_wr_checks.values()),
        "watchlist_pass": checks["wr_ge_45_watchlist"] and all(non_wr_checks.values()),
        "year_rows": year_rows,
        "block_rows": block_rows,
        "rows": rows,
    }


def flat_row(summary: dict[str, Any]) -> dict[str, Any]:
    out = {key: value for key, value in summary.items() if key not in {"checks", "year_rows", "block_rows", "rows"}}
    out.update({f"check_{key}": value for key, value in summary["checks"].items()})
    return out


def render(payload: dict[str, Any]) -> str:
    row = payload["summary"]
    lines = [
        "# A1 XAU Short HTF Resistance Sweep/Reclaim Final Test",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: one fixed exact-MT5 final falsification test for standalone XAU short WR50/RR2. Signal is evaluated once per completed M15 bar. No hour/session/day/month masks, no RR reduction.",
        "",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Result",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | 2023+2024 | Year buckets+ | Top10-removed | Top3-days-removed | Pos weeks% | True pass | Watchlist |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {(row['wl'] or 0.0):.4f} | "
        f"{(row['pf'] or 0.0):.4f} | {row['net']:.2f} | {(row['stress_030_pf'] or 0.0):.4f} | "
        f"{row['stress_030_net']:.2f} | {row['net_2023_2024']:.2f} | {row['positive_year_buckets']} | "
        f"{row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | {row['positive_week_pct']:.2f} | "
        f"{bool_text(row['true_pass'])} | {bool_text(row['watchlist_pass'])} |",
        "",
        "## Gate Checks",
        "",
    ]
    for key, value in row["checks"].items():
        lines.append(f"- `{key}`: `{bool_text(value)}`")

    lines.extend(["", "## By Year", "", "| Year | Trades | WR% | W/L | PF | Net |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for year_row in row["year_rows"]:
        lines.append(
            f"| {year_row['period']} | {year_row['trades']} | {year_row['wr']:.2f} | {(year_row['wl'] or 0.0):.4f} | "
            f"{(year_row['pf'] or 0.0):.4f} | {year_row['net']:.2f} |"
        )

    lines.extend(["", "## Decision", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run final exact-MT5 HTF resistance sweep short test.")
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

    result = mt5_payload["variants"][0]
    summary = summarize(result)
    write_csv(summary_csv, [flat_row(summary)])
    write_csv(year_csv, summary["year_rows"])
    write_csv(block_csv, summary["block_rows"])
    normalized_trades = REPORTS_DIR / f"{OUTPUT_STEM}_{summary['variant']}_NORMALIZED_TRADES.csv"
    write_signal_csv(normalized_trades, summary["rows"])

    if summary["true_pass"]:
        status = "HTF_RESISTANCE_SWEEP_WR50_RR2_PASS_REVIEW_REQUIRED"
        interpretation = (
            "The final HTF resistance sweep test passed the true WR50/RR2 gate. Keep research-only until reviewer sign-off."
        )
    elif summary["watchlist_pass"]:
        status = "HTF_RESISTANCE_SWEEP_WR45_WATCHLIST_REVIEW_REQUIRED"
        interpretation = (
            "The final HTF resistance sweep test did not reach WR50 but reached the reviewer watchlist threshold with all non-WR gates. "
            "Do not promote without reviewer sign-off."
        )
    elif summary["wr"] < 45.0:
        status = "WR50_FINAL_FALSIFIED_CLOSE_STANDALONE_SHORT_SEARCH"
        interpretation = (
            "The final HTF resistance sweep test landed below the 45% WR falsification threshold. Per both reviews, close the standalone "
            "XAU short WR50/RR2 search. Treat shorts as hedge-only unless a new reviewer-signed objective is created."
        )
    else:
        status = "HTF_RESISTANCE_SWEEP_WR_IMPROVED_BUT_GATES_FAILED"
        interpretation = (
            "The final HTF resistance sweep test improved WR above 45% but failed one or more non-WR gates. Per review, do not continue "
            "standalone short iteration without a new signed work order."
        )

    outputs = {
        "md": str(report_md),
        "json": str(report_json),
        "summary_csv": str(summary_csv),
        "year_csv": str(year_csv),
        "block_csv": str(block_csv),
        "normalized_trades_csv": str(normalized_trades),
        "mt5_components_md": str(mt5_report_md),
        "mt5_components_json": str(mt5_report_json),
    }
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
                "mt5_result": result,
                "guard_counts": guard_counts(result),
            }
        ],
        "summary": summary,
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "summary": flat_row(summary), "report": str(report_md)}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
