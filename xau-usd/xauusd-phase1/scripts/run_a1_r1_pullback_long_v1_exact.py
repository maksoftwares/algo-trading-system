from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, dedupe_signals, parse_dt, rel, summary_metrics
from analyze_a1_xau_source_monthly_firewall import max_closed_drawdown, month_shape, read_ledger, weekly_shape
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts, period_stats, source_contributions
from run_a1_regime_router_v1_exact import ROUTER_INPUTS
from run_a1_v9_v10_rr2_stretch_probe import read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R1_PULLBACK_LONG_V1_EXACT_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708"
TAG = "OWNER_GOAL_R1_PULLBACK_LONG_V1_EXACT_202207_202606"

BOX_BASELINE_CSV = (
    REPORTS_DIR
    / "A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_router_v1_r1_long_box2_prevhealth_NORMALIZED_TRADES.csv"
)
BOX_SOURCE = "h4_d1_long_best_box2_atr80"
PULLBACK_SOURCE = "r1_h1_pullback_long_v1"
Q2_START = date(2026, 4, 1)
Q2_END = date(2026, 6, 30)
YEAR_PERIODS = [
    ("2022", date(2022, 7, 1), date(2022, 12, 31)),
    ("2023", date(2023, 1, 1), date(2023, 12, 31)),
    ("2024", date(2024, 1, 1), date(2024, 12, 31)),
    ("2025", date(2025, 1, 1), date(2025, 12, 31)),
    ("2026", date(2026, 1, 1), date(2026, 6, 30)),
]


PULLBACK_BASE_INPUTS = {
    **ROUTER_INPUTS,
    "InpRegimeRouterMode": "1",
    "InpDirectionMode": "1",
    "InpSignalMode": "20",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.15",
    "InpMaxTradesPerDay": "12",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "false",
    "InpMaxOpenPositionsPerMagic": "8",
    "InpBlockedEntryHoursCsv": "",
    "InpBlockedEntryDayHoursCsv": "",
    "InpBlockedLongEntryHoursCsv": "",
    "InpBlockedShortEntryHoursCsv": "",
    "InpUseDirectionalSessionFilter": "false",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpH4D1SupportiveStateGuardEnabled": "false",
    "InpH4D1WeeklyLossGovernorEnabled": "false",
    "InpH4D1PrevMonthHealthGateEnabled": "false",
    "InpH4D1NegativeStackGuardEnabled": "false",
    "InpH4D1ThirdEntryQualityGateEnabled": "false",
    "InpD1SupportStateGateMode": "0",
    "InpD1StructuralDownGateEnabled": "false",
    "InpProfitProtectionEnabled": "false",
    "InpPartialCloseEnabled": "false",
    "InpSplitEntryEnabled": "false",
    "InpStopFloorPoints": "350",
    "InpStopCeilingPoints": "2200",
    "InpStopCapPoints": "0",
    "InpR1PullbackLookbackBars": "6",
    "InpR1PullbackH1FastEmaPeriod": "20",
    "InpR1PullbackH1SlowEmaPeriod": "50",
    "InpR1PullbackTouchAtr": "0.25",
    "InpR1PullbackStopBufferAtr": "0.25",
    "InpR1PullbackMinBodyFraction": "0.35",
    "InpR1PullbackCloseLocation": "0.65",
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="r1_pullback_long_v1_m5_confirm",
            label="R1 H1 EMA20 pullback long, M5 bullish confirmation, fixed 2R",
            run_id="BT_A1_XAU_R1_PULLBACK_LONG_V1_M5_CONFIRM",
            tester_inputs={**PULLBACK_BASE_INPUTS, "InpR1PullbackConfirmTimeframe": "5"},
        ),
        a1.Variant(
            name="r1_pullback_long_v1_m15_confirm",
            label="R1 H1 EMA20 pullback long, M15 bullish confirmation, fixed 2R",
            run_id="BT_A1_XAU_R1_PULLBACK_LONG_V1_M15_CONFIRM",
            tester_inputs={**PULLBACK_BASE_INPUTS, "InpR1PullbackConfirmTimeframe": "15"},
        ),
    ]


def parse_money(value: Any) -> float:
    return float(str(value or "0").replace(" ", "").strip() or "0")


def mt5_rows(result: dict[str, Any], source_priority: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    trade_csv = Path(result["trade_csv"])
    for ordinal, row in enumerate(read_trade_csv(trade_csv), start=2):
        entry_time = parse_dt(row["entry_time"])
        exit_text = str(row.get("exit_time") or "").strip()
        exit_time = parse_dt(exit_text) if exit_text else entry_time
        rows.append(
            {
                "component": PULLBACK_SOURCE,
                "source_id": PULLBACK_SOURCE,
                "upstream_source_id": PULLBACK_SOURCE,
                "upstream_component": result["name"],
                "family_group": "xau_r1_pullback_long",
                "source_priority": source_priority,
                "cell_id": "r1_pullback_long_v1",
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


def concentration_stats(rows: list[dict[str, Any]], net: float) -> dict[str, Any]:
    wins = sorted((float(row["pnl_usd"]) for row in rows if float(row["pnl_usd"]) > 0.0), reverse=True)
    by_day: dict[date, float] = defaultdict(float)
    by_month: dict[str, float] = defaultdict(float)
    for row in rows:
        by_day[row["entry_date"]] += float(row["pnl_usd"])
        by_month[row["exit_date"].strftime("%Y-%m")] += float(row["pnl_usd"])

    top_days = sorted(by_day.items(), key=lambda item: item[1], reverse=True)
    top3_day_sum = sum(value for _day, value in top_days[:3])
    best_month = max(by_month.values(), default=0.0)
    return {
        "top10_removed_net": round(net - sum(wins[:10]), 2),
        "top3_days_removed_net": round(net - top3_day_sum, 2),
        "best_month_share_pct": round(100.0 * max(best_month, 0.0) / net, 2) if net > 0.0 else None,
        "top3_days": [{"date": day.isoformat(), "net": round(value, 2)} for day, value in top_days[:3]],
    }


def year_rows(name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for label, start, end in YEAR_PERIODS:
        stats = period_stats(rows, start, end)
        output.append(
            {
                "name": name,
                "period": label,
                "trades": stats["signals"],
                "wr": stats["win_rate_pct"],
                "wl": stats["avg_win_loss"],
                "pf": stats["profit_factor"],
                "net": stats["net_usd"],
            }
        )
    return output


def flat_shape(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    enriched, exit_stats = enrich_exit_times(rows)
    metrics = summary_metrics(enriched, market_days=MARKET_DAYS)
    stress = summary_metrics(enriched, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    months = month_shape(enriched)
    weeks = weekly_shape(enriched)
    q2 = period_stats(enriched, Q2_START, Q2_END)
    concentration = concentration_stats(enriched, metrics["net_usd"])
    years = year_rows(name, enriched)
    positive_years_with_exposure = sum(1 for row in years if row["trades"] > 0 and row["net"] > 0.0)
    return {
        "name": name,
        "signals": metrics["signals"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_pf": stress["profit_factor"],
        "stress_030_net": stress["net_usd"],
        "active_weekday_pct": metrics["active_weekday_pct"],
        "max_closed_dd": max_closed_drawdown(enriched),
        "positive_week_pct": weeks["positive_week_pct"],
        "worst_week": weeks["worst_week"],
        "q2_signals": q2["signals"],
        "q2_net": q2["net_usd"],
        "top10_removed_net": concentration["top10_removed_net"],
        "top3_days_removed_net": concentration["top3_days_removed_net"],
        "best_month_share_pct": concentration["best_month_share_pct"],
        "positive_year_buckets": positive_years_with_exposure,
        "exit_stats": exit_stats,
        "year_rows": years,
        "top3_days": concentration["top3_days"],
        **months,
    }


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "trades_ge_150": row["signals"] >= 150,
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_1p90": (row["wl"] or 0.0) >= 1.90,
        "pf_ge_1p50": (row["pf"] or 0.0) >= 1.50,
        "stress_pf_ge_1p30": (row["stress_030_pf"] or 0.0) >= 1.30,
        "stress_wl_ge_1p80": (row["stress_030_wl"] or 0.0) >= 1.80,
        "net_gt_0": row["net"] > 0.0,
        "q2_nonnegative_if_exposed": row["q2_signals"] == 0 or row["q2_net"] >= 0.0,
        "positive_year_buckets_ge_3": row["positive_year_buckets"] >= 3,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_box_baseline": row["net"] > baseline["net"],
        "active_plus_5pp": row["active_weekday_pct"] >= baseline["active_weekday_pct"] + 5.0,
        "wl_or_stress_wl_ok": (row["wl"] or 0.0) >= 2.00 or (row["stress_030_wl"] or 0.0) >= 1.90,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.00,
        "dd_not_worse_10pct": row["max_closed_dd"] <= baseline["max_closed_dd"] * 1.10,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30pct": row["best_month_share_pct"] is not None and row["best_month_share_pct"] <= 30.0,
    }


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"data", "exit_stats", "year_rows", "top3_days", "source_contributions", "checks"}}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def evaluate_book(name: str, rows: list[dict[str, Any]], *, dedupe: bool = False) -> dict[str, Any]:
    kept = rows
    dropped: list[dict[str, Any]] = []
    if dedupe:
        kept, dropped = dedupe_signals(rows)
    shape = flat_shape(name, kept)
    return {
        **shape,
        "data": kept,
        "dropped_data": dropped,
        "dropped_signals": len(dropped),
        "source_contributions": source_contributions(kept),
    }


def decide(standalone_rows: list[dict[str, Any]], combined_rows: list[dict[str, Any]]) -> tuple[str, str]:
    if any(all(row["checks"].values()) for row in combined_rows):
        return (
            "R1_PULLBACK_LONG_V1_REVIEW_CANDIDATE",
            "At least one pullback variant passed its standalone gate and improved the routed R1 box without breaking combined robustness. Keep research-only and send for review.",
        )
    if any(row["net"] > 0.0 for row in standalone_rows):
        return (
            "R1_PULLBACK_LONG_V1_SHADOW_ONLY",
            "A pullback variant was positive, but none passed the combined-with-box gate. Do not add it to the deployable R1 book without another preregistered repair.",
        )
    return (
        "R1_PULLBACK_LONG_V1_NO_SURVIVOR",
        "The preregistered R1 pullback test did not produce a positive specialist or a robust improvement over the routed R1 box.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R1 Pullback Long V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 component rerun using the EA-side R1 router. This remains research-only; no demo/live runtime state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Routed R1 box baseline: `{payload['box_baseline_csv']}`",
        f"Routed R1 box baseline SHA256: `{payload['box_baseline_sha256']}`",
        "",
        "## Standalone Pullback Results",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Active% | Max DD | +Years | Q2 trades | Q2 net | Top10 rem | Top3 days rem | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalone_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['stress_030_pf'] or 0.0:.4f} | {row['active_weekday_pct']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['positive_year_buckets']} | {row['q2_signals']} | {row['q2_net']:.2f} | "
            f"{row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | {all(row['checks'].values())} |"
        )

    lines.extend(
        [
            "",
            "## Combined With Routed R1 Box",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Active% | Max DD | +Months | -Months | Best month share% | Dropped | Pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["combined_rows"]:
        share = row["best_month_share_pct"] if row["best_month_share_pct"] is not None else 0.0
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['stress_030_pf'] or 0.0:.4f} | {row['active_weekday_pct']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['positive_months']} | {row['negative_months']} | {share:.2f} | {row['dropped_signals']} | {all(row['checks'].values())} |"
        )

    lines.extend(["", "## Baseline", ""])
    baseline = payload["baseline_row"]
    lines.append(
        f"Routed R1 box baseline: {baseline['signals']} trades, WR {baseline['wr']:.2f}%, "
        f"W/L {baseline['wl'] or 0.0:.4f}, PF {baseline['pf'] or 0.0:.4f}, net {baseline['net']:.2f}, "
        f"active {baseline['active_weekday_pct']:.2f}%, max DD {baseline['max_closed_dd']:.2f}."
    )

    lines.extend(["", "## Failed Checks", ""])
    for row in payload["standalone_rows"] + payload["combined_rows"]:
        failed = [key for key, value in row["checks"].items() if not value]
        lines.append(f"- `{row['name']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Router / Guard Notes", ""])
    for item in payload["mt5_component_details"]:
        lines.append(f"### `{item['variant']}`")
        guard_reasons = item["guard_counts"]["guard_reasons"]
        router_blocks = {reason: count for reason, count in guard_reasons.items() if reason.startswith("regime_router_block")}
        if router_blocks:
            for reason, count in sorted(router_blocks.items()):
                lines.append(f"- `{reason}`: {count}")
        else:
            lines.append("- no router blocks logged")
        lines.append("")

    lines.extend(["## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R1 pullback long specialist V1.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(BOX_BASELINE_CSV)

    variants = build_variants()
    a1.VARIANTS = variants

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    standalone_csv = REPORTS_DIR / f"{OUTPUT_STEM}_STANDALONE.csv"
    combined_csv = REPORTS_DIR / f"{OUTPUT_STEM}_COMBINED.csv"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.json"

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

    box_rows = read_ledger(BOX_BASELINE_CSV)
    baseline = evaluate_book("router_v1_r1_long_box2_prevhealth", box_rows)

    standalone_rows: list[dict[str, Any]] = []
    combined_rows: list[dict[str, Any]] = []
    mt5_component_details: list[dict[str, Any]] = []
    for index, result in enumerate(mt5_payload["variants"], start=1):
        rows = mt5_rows(result, source_priority=70 + index)
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv", rows)

        standalone = evaluate_book(result["name"], rows)
        standalone["checks"] = standalone_checks(standalone)
        standalone_rows.append(standalone)

        combined = evaluate_book(f"box_plus_{result['name']}", box_rows + rows, dedupe=True)
        combined["checks"] = combined_checks(combined, baseline)
        combined_rows.append(combined)

        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_KEPT.csv", combined["data"])
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_DROPPED.csv", combined["dropped_data"])

        mt5_component_details.append(
            {
                "variant": result["name"],
                "mt5_result": result,
                "guard_counts": guard_counts(result),
                "normalized_trades": len(rows),
            }
        )

    status, interpretation = decide(standalone_rows, combined_rows)

    write_csv(standalone_csv, [strip_heavy(row) for row in standalone_rows])
    write_csv(combined_csv, [strip_heavy(row) for row in combined_rows])

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "standalone_csv": rel(standalone_csv),
        "combined_csv": rel(combined_csv),
        "mt5_components_md": rel(mt5_report_md),
        "mt5_components_json": rel(mt5_report_json),
    }
    for row in standalone_rows:
        outputs[f"{row['name']}_normalized_trades_csv"] = rel(REPORTS_DIR / f"{OUTPUT_STEM}_{row['name']}_NORMALIZED_TRADES.csv")
    for row in combined_rows:
        outputs[f"{row['name']}_kept_csv"] = rel(REPORTS_DIR / f"{OUTPUT_STEM}_{row['name']}_KEPT.csv")
        outputs[f"{row['name']}_dropped_csv"] = rel(REPORTS_DIR / f"{OUTPUT_STEM}_{row['name']}_DROPPED.csv")

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "box_baseline_csv": rel(BOX_BASELINE_CSV),
        "box_baseline_sha256": sha256_file(BOX_BASELINE_CSV),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "baseline_row": strip_heavy(baseline),
        "standalone_rows": [strip_heavy(row) | {"checks": row["checks"]} for row in standalone_rows],
        "combined_rows": [strip_heavy(row) | {"checks": row["checks"]} for row in combined_rows],
        "mt5_component_details": mt5_component_details,
        "interpretation": interpretation,
        "outputs": outputs,
    }

    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "baseline": strip_heavy(baseline),
                "standalone": [strip_heavy(row) | {"checks": row["checks"]} for row in standalone_rows],
                "combined": [strip_heavy(row) | {"checks": row["checks"]} for row in combined_rows],
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
