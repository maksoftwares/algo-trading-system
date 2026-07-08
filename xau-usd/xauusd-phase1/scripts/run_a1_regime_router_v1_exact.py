from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, dedupe_signals, parse_dt, rel, summary_metrics
from analyze_a1_xau_source_monthly_firewall import max_closed_drawdown, month_shape, read_ledger, weekly_shape
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import BASE_H4_INPUTS, COMPONENTS, guard_counts, period_stats, replacement_rows, source_contributions
from run_a1_v9_v10_rr2_stretch_probe import read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_REGIME_ROUTER_V1_EXACT_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_REGIME_ROUTER_V1_EXACT_20260708"
TAG = "OWNER_GOAL_REGIME_ROUTER_V1_EXACT_202207_202606"

CURRENT_BLEND = (
    REPORTS_DIR
    / "A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708_replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4_KEPT.csv"
)
FREQ_SOURCE = "freq_step3_frontier"
LONG_SOURCE = "h4_d1_long_best_box2_atr80"
SHORT_SOURCE = "short_v4_impulse_retest_d1_structural_h1h4"
Q2_START = date(2026, 4, 1)
Q2_END = date(2026, 6, 30)
CURRENT_BLEND_MAX_DD = 958.86

ROUTER_INPUTS = {
    "InpRegimeFastEmaPeriod": "20",
    "InpRegimeSlowEmaPeriod": "50",
    "InpRegimeSlopeLagBars": "5",
    "InpRegimePersistenceD1Bars": "2",
    "InpRegimeRequireH4Confirm": "true",
    "InpRegimeShockH1RangeAtrMultiple": "3.00",
    "InpRegimeShockD1AtrPercentileMin": "95.00",
    "InpRegimeShockD1AtrLookback": "60",
    "InpRegimeCompressionD1AtrPercentileMax": "30.00",
    "InpRegimeCompressionBoxDays": "5",
    "InpRegimeCompressionRangeMedianMax": "1.00",
}

SHORT_V4_INPUTS = {
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
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def build_variants() -> tuple[list[a1.Variant], dict[str, dict[str, Any]]]:
    box2 = COMPONENTS["box2"]
    long_inputs = {
        **BASE_H4_INPUTS,
        **box2["inputs"],
        **ROUTER_INPUTS,
        "InpH4D1SupportiveStateGuardEnabled": "true",
        "InpH4D1SupportiveEmaPeriod": "20",
        "InpH4D1SupportiveSlopeLagBars": "5",
        "InpH4D1PrevMonthHealthGateEnabled": "true",
        "InpH4D1PrevMonthNetMinUsd": "-50.00",
        "InpRegimeRouterMode": "1",
    }
    short_inputs = {
        **SHORT_V4_INPUTS,
        **ROUTER_INPUTS,
        "InpRegimeRouterMode": "2",
    }
    variants = [
        a1.Variant(
            name="router_v1_r1_long_box2_prevhealth",
            label="Router V1: H4/D1 box2 previous-month-health long armed only in R1 uptrend",
            run_id="BT_A1_XAU_ROUTER_V1_R1_LONG_BOX2_PREVHEALTH",
            tester_inputs=long_inputs,
        ),
        a1.Variant(
            name="router_v1_r2_short_v4_structural",
            label="Router V1: V4 downside impulse/retest short armed only in R2 downtrend",
            run_id="BT_A1_XAU_ROUTER_V1_R2_SHORT_V4_STRUCTURAL",
            tester_inputs=short_inputs,
        ),
    ]
    metadata = {
        "router_v1_r1_long_box2_prevhealth": {
            "probe": "router_v1_r1",
            "component_key": "box2",
            "source_id": LONG_SOURCE,
            "source_priority": box2["source_priority"],
            "family_group": "h4_d1_core_shape",
            "label": "router_v1_r1_long_box2_prevhealth",
        },
        "router_v1_r2_short_v4_structural": {
            "probe": "router_v1_r2",
            "component_key": "short_v4",
            "source_id": SHORT_SOURCE,
            "source_priority": 88,
            "family_group": "xau_short_v4_regime_router",
            "label": "router_v1_r2_short_v4_structural",
        },
    }
    return variants, metadata


def parse_money(value: Any) -> float:
    return float(str(value or "0").replace(" ", "").strip() or "0")


def short_replacement_rows(result: dict[str, Any], meta: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    trade_csv = Path(result["trade_csv"])
    for ordinal, row in enumerate(read_trade_csv(trade_csv), start=2):
        entry_time = parse_dt(row["entry_time"])
        exit_text = str(row.get("exit_time") or "").strip()
        exit_time = parse_dt(exit_text) if exit_text else entry_time
        rows.append(
            {
                "component": meta["source_id"],
                "source_id": meta["source_id"],
                "upstream_source_id": meta["source_id"],
                "upstream_component": meta["label"],
                "family_group": meta["family_group"],
                "source_priority": meta["source_priority"],
                "cell_id": meta["probe"],
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


def normalize_rows(result: dict[str, Any], meta: dict[str, Any]) -> list[dict[str, Any]]:
    if meta["source_id"] == LONG_SOURCE:
        rows = replacement_rows(result, meta)
        for row in rows:
            row["exit_date"] = row["exit_time"].date() if isinstance(row.get("exit_time"), datetime) else row["entry_date"]
        return rows
    return short_replacement_rows(result, meta)


def freq_rows() -> list[dict[str, Any]]:
    return [row for row in read_ledger(CURRENT_BLEND) if row.get("source_id") == FREQ_SOURCE]


def flat_shape(rows: list[dict[str, Any]]) -> dict[str, Any]:
    enriched, exit_stats = enrich_exit_times(rows)
    metrics = summary_metrics(enriched, market_days=MARKET_DAYS)
    stress = summary_metrics(enriched, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    months = month_shape(enriched)
    weeks = weekly_shape(enriched)
    q2 = period_stats(enriched, Q2_START, Q2_END)
    return {
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
        "q2_wr": q2["win_rate_pct"],
        "q2_wl": q2["avg_win_loss"],
        "q2_net": q2["net_usd"],
        "exit_stats": exit_stats,
        **months,
    }


def evaluate_portfolio(name: str, raw_rows: list[dict[str, Any]]) -> dict[str, Any]:
    kept, dropped = dedupe_signals(raw_rows)
    shape = flat_shape(kept)
    return {
        "name": name,
        "kept_data": kept,
        "dropped_data": dropped,
        "dropped_signals": len(dropped),
        **shape,
        "source_contributions": source_contributions(kept),
    }


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"kept_data", "dropped_data", "source_contributions", "exit_stats"}}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def router_block_counts(result: dict[str, Any]) -> dict[str, int]:
    counts = guard_counts(result)["guard_reasons"]
    return {reason: count for reason, count in sorted(counts.items()) if reason.startswith("regime_router_block")}


def decide(component_rows: dict[str, list[dict[str, Any]]], portfolios: list[dict[str, Any]]) -> tuple[str, str]:
    long_shape = flat_shape(component_rows["router_v1_r1_long_box2_prevhealth"])
    short_shape = flat_shape(component_rows["router_v1_r2_short_v4_structural"])
    no_freq = next(row for row in portfolios if row["name"] == "router_long_short_no_freq")
    with_freq = next(row for row in portfolios if row["name"] == "router_long_short_with_freq_observer")

    if (
        long_shape["net"] > 0.0
        and (short_shape["net"] > 0.0 or short_shape["q2_net"] > 0.0)
        and no_freq["net"] > 0.0
        and no_freq["q2_net"] >= 0.0
        and no_freq["max_closed_dd"] <= CURRENT_BLEND_MAX_DD
    ):
        return (
            "ROUTER_V1_ARCHITECTURE_REVIEW_CANDIDATE",
            "The routed long/short book is positive without the frequency layer and does not exceed the current blend drawdown. Keep research-only and request review before adding more specialists.",
        )

    if with_freq["net"] > 0.0 and with_freq["q2_net"] >= 0.0:
        return (
            "ROUTER_V1_SHADOW_ONLY",
            "Router V1 is useful as a shadow architecture, but the current result still relies on frequency or lacks enough routed standalone coverage. Do not promote; use this to guide the next specialist.",
        )

    return (
        "ROUTER_V1_NO_SURVIVOR",
        "Router V1 did not preserve positive routed portfolio evidence in this exact-MT5 pass. Do not promote the router without revising the preregistered regime map through review.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Regime Router V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 component rerun with the EA-side completed-bar regime router. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Component Results",
        "",
        "| Component | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Q2 trades | Q2 net | Router blocks |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["component_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['stress_030_pf'] or 0.0:.4f} | {row['q2_signals']} | {row['q2_net']:.2f} | {row['router_blocks']} |"
        )

    lines.extend(
        [
            "",
            "## Portfolio Diagnostics",
            "",
            "| Portfolio | Trades | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Q2 trades | Q2 net |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["portfolio_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['active_weekday_pct']:.2f} | {row['net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {row['positive_months']} | {row['negative_months']} | "
            f"{row['positive_week_pct']:.2f} | {row['q2_signals']} | {row['q2_net']:.2f} |"
        )

    lines.extend(["", "## Router Block Reasons", ""])
    for item in payload["mt5_component_details"]:
        lines.append(f"### `{item['variant']}`")
        if item["router_block_counts"]:
            for reason, count in item["router_block_counts"].items():
                lines.append(f"- `{reason}`: {count}")
        else:
            lines.append("- none")
        lines.append("")

    lines.extend(["## Source Contributions", ""])
    for row in payload["portfolio_rows_full"]:
        lines.extend([f"### `{row['name']}`", "", "| Source | Signals | Net USD |", "| --- | ---: | ---: |"])
        for source, contribution in row["source_contributions"].items():
            lines.append(f"| `{source}` | {contribution['signals']} | {contribution['net_usd']:.2f} |")
        lines.append("")

    lines.extend(["## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 XAU Regime Router V1 component pass.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(CURRENT_BLEND)

    variants, metadata = build_variants()
    a1.VARIANTS = variants
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    component_csv = REPORTS_DIR / f"{OUTPUT_STEM}_COMPONENTS.csv"
    portfolio_csv = REPORTS_DIR / f"{OUTPUT_STEM}_PORTFOLIOS.csv"
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

    component_data: dict[str, list[dict[str, Any]]] = {}
    component_rows: list[dict[str, Any]] = []
    mt5_component_details: list[dict[str, Any]] = []
    for result in mt5_payload["variants"]:
        meta = metadata[result["name"]]
        rows = normalize_rows(result, meta)
        component_data[result["name"]] = rows
        shape = flat_shape(rows)
        component_rows.append(
            {
                "name": result["name"],
                **shape,
                "router_blocks": sum(router_block_counts(result).values()),
            }
        )
        mt5_component_details.append(
            {
                "variant": result["name"],
                "replacement_rows": len(rows),
                "mt5_result": result,
                "guard_counts": guard_counts(result),
                "router_block_counts": router_block_counts(result),
            }
        )
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv", rows)

    routed_rows = component_data["router_v1_r1_long_box2_prevhealth"] + component_data["router_v1_r2_short_v4_structural"]
    portfolios = [
        evaluate_portfolio("router_long_short_no_freq", routed_rows),
        evaluate_portfolio("router_long_short_with_freq_observer", routed_rows + freq_rows()),
    ]

    status, interpretation = decide(component_data, portfolios)

    for portfolio in portfolios:
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{portfolio['name']}_KEPT.csv", portfolio["kept_data"])
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{portfolio['name']}_DROPPED.csv", portfolio["dropped_data"])

    write_csv(component_csv, [strip_heavy(row) for row in component_rows])
    write_csv(portfolio_csv, [strip_heavy(row) for row in portfolios])

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "current_blend": rel(CURRENT_BLEND),
        "current_blend_sha256": sha256_file(CURRENT_BLEND),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "component_rows": [strip_heavy(row) for row in component_rows],
        "portfolio_rows": [strip_heavy(row) for row in portfolios],
        "portfolio_rows_full": portfolios,
        "mt5_component_details": mt5_component_details,
        "interpretation": interpretation,
        "outputs": {
            "report_md": rel(report_md),
            "report_json": rel(report_json),
            "component_csv": rel(component_csv),
            "portfolio_csv": rel(portfolio_csv),
            "mt5_components_md": rel(mt5_report_md),
            "mt5_components_json": rel(mt5_report_json),
        },
    }
    for item in component_data:
        payload["outputs"][f"{item}_normalized_trades_csv"] = rel(REPORTS_DIR / f"{OUTPUT_STEM}_{item}_NORMALIZED_TRADES.csv")
    for portfolio in portfolios:
        payload["outputs"][f"{portfolio['name']}_kept_csv"] = rel(REPORTS_DIR / f"{OUTPUT_STEM}_{portfolio['name']}_KEPT.csv")
        payload["outputs"][f"{portfolio['name']}_dropped_csv"] = rel(REPORTS_DIR / f"{OUTPUT_STEM}_{portfolio['name']}_DROPPED.csv")

    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "components": [strip_heavy(row) for row in component_rows],
                "portfolios": [strip_heavy(row) for row in portfolios],
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
