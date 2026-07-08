from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, parse_dt, rel, summary_metrics
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, weekly_exit_shape, write_signal_csv
from run_a1_h4_d1_review_repair_exact import RECENT3_END, RECENT3_START, period_stats
from run_a1_short_v2_robustness_probe import BLOCK_PERIODS, YEAR_PERIODS, bool_text, concentration_stats, guard_counts, period_metric_row
from run_a1_v9_v10_rr2_stretch_probe import read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_20260708"
TAG = "OWNER_GOAL_NONUP_HTF_RESISTANCE_SWEEP_SHORT_202207_202606"


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="nonup_htf_resistance_sweep_short_v1",
            label="Non-up D1 HTF resistance sweep/reclaim short, fixed 2R",
            run_id="BT_A1_XAU_NONUP_HTF_RESISTANCE_SWEEP_SHORT_V1",
            tester_inputs={
                "InpDirectionMode": "2",
                "InpSignalMode": "18",
                "InpRiskReward": "2.00",
                "InpMaxSpreadPoints": "75",
                "InpMaxEstimatedCostR": "0.05",
                "InpMaxTradesPerDay": "24",
                "InpCooldownMinutes": "0",
                "InpBlockedEntryHoursCsv": "",
                "InpBlockedEntryDayHoursCsv": "",
                "InpBlockedLongEntryHoursCsv": "",
                "InpBlockedShortEntryHoursCsv": "",
                "InpD1SupportStateGateMode": "4",
                "InpD1SupportStateEmaPeriod": "20",
                "InpD1SupportStateSlopeLagBars": "5",
                "InpD1StructuralDownGateEnabled": "false",
                "InpUseH1TrendFilter": "false",
                "InpUseH4TrendFilter": "false",
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


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def parse_money(value: Any) -> float:
    return float(str(value or "0").replace(" ", "").strip() or "0")


def variant_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    trade_csv = Path(result["trade_csv"])
    for ordinal, row in enumerate(read_trade_csv(trade_csv), start=2):
        entry_time = parse_dt(row["entry_time"])
        exit_text = str(row.get("exit_time") or "").strip()
        exit_time = parse_dt(exit_text) if exit_text else entry_time
        rows.append(
            {
                "component": result["name"],
                "source_id": result["name"],
                "upstream_source_id": result["name"],
                "upstream_component": "exact_mt5_nonup_htf_resistance_sweep_short",
                "family_group": "xau_nonup_htf_resistance_sweep_short",
                "source_priority": 88,
                "cell_id": result["name"],
                "component_priority": 0,
                "variant_name": result["name"],
                "entry_time": entry_time,
                "entry_date": date.fromisoformat(str(row.get("entry_date") or entry_time.date().isoformat())),
                "exit_time": exit_time,
                "exit_date": exit_time.date(),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": parse_money(row.get("profit_float") or row.get("profit_aed")),
                "tickets": 1,
                "lots": parse_money(row.get("volume")),
                "source_csv": str(trade_csv),
                "source_row": ordinal,
            }
        )
    return rows


def checks_for(metrics: dict[str, Any], stress: dict[str, Any], year_rows: list[dict[str, Any]], concentration: dict[str, Any]) -> dict[str, bool]:
    net_2023_2024 = sum(float(row["net"]) for row in year_rows if row["period"] in {"2023", "2024"})
    positive_years = sum(1 for row in year_rows if float(row["net"]) > 0.0)
    return {
        "trades_ge_100": metrics["signals"] >= 100,
        "wr_ge_45": metrics["win_rate_pct"] >= 45.0,
        "wl_ge_1p90": (metrics["avg_win_loss"] or 0.0) >= 1.90,
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
    recent3 = period_stats(rows, RECENT3_START, RECENT3_END)
    concentration = concentration_stats(rows, metrics["net_usd"])
    year_rows = [period_metric_row(result["name"], label, rows, start, end) for label, start, end in YEAR_PERIODS]
    block_rows = [period_metric_row(result["name"], label, rows, start, end) for label, start, end in BLOCK_PERIODS]
    checks = checks_for(metrics, stress, year_rows, concentration)
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
        "recent3_net": recent3["net_usd"],
        "net_2023_2024": round(sum(float(row["net"]) for row in year_rows if row["period"] in {"2023", "2024"}), 2),
        "positive_year_buckets": sum(1 for row in year_rows if float(row["net"]) > 0.0),
        "top10_removed_net": concentration["top10_removed_net"],
        "top3_days_removed_net": concentration["top3_days_removed_net"],
        "best_day_share_pct": concentration["best_day_share_pct"],
        "checks": checks,
        "watchlist_pass": all(checks.values()),
        "strict_pass": all(checks.values()) and metrics["win_rate_pct"] >= 50.0,
        "year_rows": year_rows,
        "block_rows": block_rows,
        "rows": rows,
    }


def strip_heavy(summary: dict[str, Any]) -> dict[str, Any]:
    out = {key: value for key, value in summary.items() if key not in {"checks", "year_rows", "block_rows", "rows"}}
    out.update({f"check_{key}": value for key, value in summary["checks"].items()})
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render(payload: dict[str, Any]) -> str:
    row = payload["summary"]
    lines = [
        "# A1 XAU Non-Up HTF Resistance Sweep Short",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: one fixed exact-MT5 short specialist test: D1 non-up, HTF resistance sweep/reclaim, fixed 2R. No hour/session/day/month masks.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Result",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | Recent3 | 2023+2024 | Year+ | Top10-removed | Top3-days-removed | Pos weeks% | Watchlist | Strict |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        f"| `{row['variant']}` | {row['trades']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
        f"{row['stress_030_pf'] or 0.0:.4f} | {row['stress_030_net']:.2f} | {row['recent3_net']:.2f} | {row['net_2023_2024']:.2f} | "
        f"{row['positive_year_buckets']} | {row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | {row['positive_week_pct']:.2f} | "
        f"{bool_text(row['watchlist_pass'])} | {bool_text(row['strict_pass'])} |",
        "",
        "## Gate Checks",
        "",
    ]
    for key, value in row["checks"].items():
        lines.append(f"- `{key}`: `{bool_text(value)}`")

    lines.extend(["", "## By Year", "", "| Year | Trades | WR% | W/L | PF | Net |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for year_row in row["year_rows"]:
        lines.append(
            f"| {year_row['period']} | {year_row['trades']} | {year_row['wr']:.2f} | {year_row['wl'] or 0.0:.4f} | "
            f"{year_row['pf'] or 0.0:.4f} | {year_row['net']:.2f} |"
        )

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 non-up HTF resistance sweep short probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    summary_csv = REPORTS_DIR / f"{OUTPUT_STEM}_SUMMARY.csv"
    year_csv = REPORTS_DIR / f"{OUTPUT_STEM}_YEAR.csv"
    block_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BLOCK.csv"
    trades_csv = REPORTS_DIR / f"{OUTPUT_STEM}_NORMALIZED_TRADES.csv"
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

    summary = summarize(mt5_payload["variants"][0])
    write_csv(summary_csv, [strip_heavy(summary)])
    write_csv(year_csv, summary["year_rows"])
    write_csv(block_csv, summary["block_rows"])
    write_signal_csv(trades_csv, summary["rows"])

    if summary["strict_pass"]:
        status = "NONUP_HTF_RESISTANCE_SWEEP_STRICT_PASS_REVIEW_REQUIRED"
        interpretation = "The fixed HTF resistance sweep short passed the strict WR50 durability gate. Keep research-only and request review."
    elif summary["watchlist_pass"]:
        status = "NONUP_HTF_RESISTANCE_SWEEP_WATCHLIST"
        interpretation = "The fixed HTF resistance sweep short passed the watchlist gate but not WR50. Treat as possible hedge/specialist input, not standalone demo-ready."
    else:
        status = "NONUP_HTF_RESISTANCE_SWEEP_NO_SURVIVOR"
        interpretation = "The fixed HTF resistance sweep short failed the preregistered watchlist gate. Do not tune this path without review."

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_component_details": [
            {
                "variant": mt5_payload["variants"][0]["name"],
                "trade_rows": len(summary["rows"]),
                "mt5_result": mt5_payload["variants"][0],
                "guard_counts": guard_counts(mt5_payload["variants"][0]),
            }
        ],
        "summary": summary,
        "interpretation": interpretation,
        "outputs": {
            "report_md": rel(report_md),
            "report_json": rel(report_json),
            "summary_csv": rel(summary_csv),
            "year_csv": rel(year_csv),
            "block_csv": rel(block_csv),
            "normalized_trades_csv": rel(trades_csv),
            "mt5_components_md": rel(mt5_report_md),
            "mt5_components_json": rel(mt5_report_json),
        },
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "summary": strip_heavy(summary), "report": str(report_md)}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
