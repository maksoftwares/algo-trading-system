from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_r3_compression_long_v1_exact as r3
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_PREREG_2026_07_09.md"
OUTPUT_STEM = "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709"
TAG = "OWNER_GOAL_R1_LONG_EXPANSION_R3_RECLASS_EXACT_202207_202606"
SOURCE_ID = "r1_long_expansion_r3_reclass_strict_r1"
RUN_ID = "BT_A1_XAU_R1_LONG_EXP_R3_RECLASS_STRICT_R1"
CURRENT_R1_R2 = (
    REPORTS_DIR
    / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"
)


NO_FILTER_INPUTS = {
    "InpBlockedEntryHoursCsv": "",
    "InpBlockedEntryDayHoursCsv": "",
    "InpBlockedLongEntryHoursCsv": "",
    "InpBlockedShortEntryHoursCsv": "",
    "InpUseDirectionalSessionFilter": "false",
}


EXPECTED_R3_VALUES = {
    "InpSignalMode": "7",
    "InpDirectionMode": "1",
    "InpRiskReward": "2.00",
    "InpMaxEstimatedCostR": "0.15",
    "InpStopCeilingPoints": "0",
    "InpMaxTradesPerDay": "6",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "false",
    "InpMaxOpenPositionsPerMagic": "16",
    "InpD1CompressionAtrPercentileMax": "60.00",
    "InpD1CompressionBoxDays": "3",
    "InpD1CompressionRangeMedianMax": "1.25",
    "InpD1CompressionH4MinBodyFraction": "0.35",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpH4D1SupportiveStateGuardEnabled": "false",
    "InpH4D1WeeklyLossGovernorEnabled": "false",
    "InpH4D1PrevMonthHealthGateEnabled": "false",
    "InpH4D1NegativeStackGuardEnabled": "false",
    "InpH4D1ThirdEntryQualityGateEnabled": "false",
    "InpProfitProtectionEnabled": "false",
    "InpPartialCloseEnabled": "false",
    "InpSplitEntryEnabled": "false",
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def tester_inputs() -> dict[str, str]:
    return {
        **ROUTER_INPUTS,
        **r3.R3_INPUTS,
        **NO_FILTER_INPUTS,
        "InpRegimeRouterMode": "1",
    }


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name=SOURCE_ID,
            label="Strict R1-routed reclass of frozen R3 D1-compression/H4-expansion long source",
            run_id=RUN_ID,
            tester_inputs=tester_inputs(),
        )
    ]


def mt5_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = r3.mt5_rows(result)
    for row in rows:
        row["component"] = SOURCE_ID
        row["source_id"] = SOURCE_ID
        row["upstream_source_id"] = SOURCE_ID
        row["upstream_component"] = result["name"]
        row["family_group"] = "xau_r1_long_expansion_r3_reclass"
        row["cell_id"] = "r1_long_expansion_r3_reclass"
        row["source_priority"] = 85
    return rows


def static_checks(variants: list[a1.Variant]) -> dict[str, bool]:
    inputs = variants[0].tester_inputs if variants else {}
    checks: dict[str, bool] = {
        "variant_count_eq_1": len(variants) == 1,
        "router_strict_r1": inputs.get("InpRegimeRouterMode") == "1",
        "r4_not_included": all("r4" not in variant.name.lower() for variant in variants),
        "no_session_or_hour_filter": all(
            inputs.get(key, "") in {"", "false"}
            for key in [
                "InpBlockedEntryHoursCsv",
                "InpBlockedEntryDayHoursCsv",
                "InpBlockedLongEntryHoursCsv",
                "InpBlockedShortEntryHoursCsv",
                "InpUseDirectionalSessionFilter",
            ]
        ),
        "no_management_layers": all(
            inputs.get(key) == "false"
            for key in [
                "InpProfitProtectionEnabled",
                "InpPartialCloseEnabled",
                "InpSplitEntryEnabled",
            ]
        ),
    }
    for key, expected in EXPECTED_R3_VALUES.items():
        checks[f"{key}_unchanged"] = inputs.get(key) == expected
    for key, expected in ROUTER_INPUTS.items():
        checks[f"{key}_router_v1_unchanged"] = inputs.get(key) == expected
    return checks


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    share = row["best_month_share_pct"]
    return {
        "trades_ge_100": row["signals"] >= 100,
        "wr_ge_55": row["wr"] >= 55.0,
        "wl_ge_2": (row["wl"] or 0.0) >= 2.0,
        "pf_ge_2p50": (row["pf"] or 0.0) >= 2.50,
        "stress_pf_ge_2p25": (row["stress_030_pf"] or 0.0) >= 2.25,
        "net_ge_5000": row["net"] >= 5000.0,
        "stress_net_ge_4500": row["stress_030_net"] >= 4500.0,
        "net_2023_2024_ge_0": row["net_2023_2024"] >= 0.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
        "max_closed_dd_lte_900": row["max_closed_dd"] <= 900.0,
        "best_month_share_lte_35pct": share is not None and share <= 35.0,
        "recent3_net_ge_minus_50": row["recent3_net"] >= -50.0,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    share = row["best_month_share_pct"]
    return {
        "net_ge_baseline_plus_2000": row["net"] >= baseline["net"] + 2000.0,
        "stress_net_ge_baseline_plus_2000": row["stress_030_net"] >= baseline["stress_030_net"] + 2000.0,
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_2": (row["wl"] or 0.0) >= 2.0,
        "pf_ge_2p50": (row["pf"] or 0.0) >= 2.50,
        "dd_lte_115pct_baseline": row["max_closed_dd"] <= baseline["max_closed_dd"] * 1.15,
        "recent3_net_ge_baseline_minus_50": row["recent3_net"] >= baseline["recent3_net"] - 50.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30pct": share is not None and share <= 30.0,
        "positive_months_gte_baseline": row["positive_months"] >= baseline["positive_months"],
    }


def strip_book(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in row.items()
        if key
        not in {
            "data",
            "dropped_data",
            "exit_stats",
            "year_rows",
            "top3_days",
            "source_contributions",
            "checks",
        }
    }


def decide(
    static: dict[str, bool],
    standalone: dict[str, Any],
    combined: dict[str, Any],
    baseline: dict[str, Any],
) -> tuple[str, str]:
    if not all(static.values()):
        return (
            "R1_LONG_EXPANSION_R3_RECLASS_INVALID_TEST",
            "The static preregistration guard failed. Treat this run as invalid evidence.",
        )
    standalone_pass = all(standalone["checks"].values())
    combined_pass = all(combined["checks"].values())
    if standalone_pass and combined_pass:
        return (
            "R1_LONG_EXPANSION_R3_RECLASS_REVIEW_CANDIDATE",
            "The strict R1-routed R3 reclassification passed standalone and current R1+R2 combined gates. Keep research-only and request reviewer approval before any baseline promotion.",
        )
    if standalone_pass or (
        combined["net"] > baseline["net"]
        and (
            not combined["checks"]["dd_lte_115pct_baseline"]
            or not combined["checks"]["recent3_net_ge_baseline_minus_50"]
        )
    ):
        return (
            "R1_LONG_EXPANSION_R3_RECLASS_SHADOW_ONLY",
            "The strict R1-routed R3 reclassification has usable evidence but did not clear every combined promotion gate. Keep as shadow-only.",
        )
    return (
        "R1_LONG_EXPANSION_R3_RECLASS_NO_SURVIVOR",
        "The strict R1-routed R3 reclassification failed the standalone quality gate. Freeze R3 for this label under the preregistered kill rules.",
    )


def render(payload: dict[str, Any]) -> str:
    baseline = payload["baseline"]
    standalone = payload["standalone"]
    combined = payload["combined"]
    lines = [
        "# A1 XAU R1 Long Expansion R3 Reclass Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 strict R1-router execution of the frozen R3 D1-compression/H4-expansion long source. Research-only.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Current R1+R2 baseline: `{payload['current_r1_r2_baseline']}`",
        f"Current R1+R2 baseline SHA256: `{payload['current_r1_r2_baseline_sha256']}`",
        "",
        "## Result Table",
        "",
        "| Book | Trades | WR% | W/L | PF | Net | Stress net | Stress PF | Recent3 trades | Recent3 net | Max DD | +Months | Best month share% | Top10 rem | Top3 days rem | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in [baseline, standalone, combined]:
        share = row["best_month_share_pct"] if row["best_month_share_pct"] is not None else 0.0
        checks = row.get("checks")
        pass_text = "n/a" if checks is None else str(all(checks.values()))
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_net']:.2f} | "
            f"{row['stress_030_pf'] or 0.0:.4f} | {row['recent3_signals']} | {row['recent3_net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {row['positive_months']} | {share:.2f} | "
            f"{row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | {pass_text} |"
        )

    lines.extend(
        [
            "",
            "## April-May-June 2026",
            "",
            "| Book | April trades/net | May trades/net | June trades/net |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in [standalone, combined]:
        april = row["month_2026_04"]
        may = row["month_2026_05"]
        june = row["month_2026_06"]
        lines.append(
            f"| `{row['name']}` | {april['signals']} / {april['net']:.2f} | "
            f"{may['signals']} / {may['net']:.2f} | {june['signals']} / {june['net']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Gate Thresholds From Baseline",
            "",
            f"- Combined net minimum: `{baseline['net'] + 2000.0:.2f}`",
            f"- Combined stress net minimum: `{baseline['stress_030_net'] + 2000.0:.2f}`",
            f"- Combined max DD cap: `{baseline['max_closed_dd'] * 1.15:.2f}`",
            f"- Combined recent3 minimum: `{baseline['recent3_net'] - 50.0:.2f}`",
            f"- Positive months minimum: `{baseline['positive_months']}`",
            "",
            "## Failed Checks",
            "",
        ]
    )
    static_failed = [key for key, value in payload["static_checks"].items() if not value]
    lines.append(f"- `static`: {', '.join(static_failed) if static_failed else 'none'}")
    for row in [standalone, combined]:
        failed = [key for key, value in row["checks"].items() if not value]
        lines.append(f"- `{row['name']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Router / Guard Notes", ""])
    guard_reasons = payload["guard_counts"]["guard_reasons"]
    router_blocks = {key: value for key, value in guard_reasons.items() if key.startswith("regime_router_block")}
    if router_blocks:
        for reason, count in sorted(router_blocks.items()):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- no router blocks logged")
    lines.append(f"- `ORDER_SEND_OK`: {payload['guard_counts']['actions'].get('ORDER_SEND_OK', 0)}")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R1-routed R3 long-expansion reclassification test.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(CURRENT_R1_R2)

    variants = build_variants()
    static = static_checks(variants)
    a1.VARIANTS = variants

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    standalone_csv = REPORTS_DIR / f"{OUTPUT_STEM}_STANDALONE.csv"
    combined_csv = REPORTS_DIR / f"{OUTPUT_STEM}_COMBINED.csv"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.json"

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
    candidate_rows = mt5_rows(result)
    baseline_rows = read_ledger(CURRENT_R1_R2)
    baseline = r3.enriched_book("current_r1_r2_baseline", baseline_rows)
    standalone = r3.enriched_book(result["name"], candidate_rows)
    combined = r3.enriched_book(f"current_r1_r2_plus_{result['name']}", baseline_rows + candidate_rows, dedupe=True)

    standalone["checks"] = standalone_checks(standalone)
    combined["checks"] = combined_checks(combined, baseline)
    status, interpretation = decide(static, standalone, combined, baseline)

    normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
    combined_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_KEPT.csv"
    combined_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_DROPPED.csv"
    write_signal_csv(normalized_csv, candidate_rows)
    write_signal_csv(combined_kept_csv, combined["data"])
    write_signal_csv(combined_dropped_csv, combined["dropped_data"])
    r1.write_csv(standalone_csv, [strip_book(standalone)])
    r1.write_csv(combined_csv, [strip_book(combined)])

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "standalone_csv": rel(standalone_csv),
        "combined_csv": rel(combined_csv),
        "normalized_trades_csv": rel(normalized_csv),
        "combined_kept_csv": rel(combined_kept_csv),
        "combined_dropped_csv": rel(combined_dropped_csv),
        "mt5_report_md": rel(mt5_report_md),
        "mt5_report_json": rel(mt5_report_json),
    }
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "current_r1_r2_baseline": rel(CURRENT_R1_R2),
        "current_r1_r2_baseline_sha256": sha256_file(CURRENT_R1_R2),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_result": result,
        "static_checks": static,
        "guard_counts": guard_counts(result),
        "baseline": strip_book(baseline),
        "standalone": strip_book(standalone) | {"checks": standalone["checks"]},
        "combined": strip_book(combined) | {"checks": combined["checks"]},
        "interpretation": interpretation,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "baseline": payload["baseline"],
                "standalone": payload["standalone"],
                "combined": payload["combined"],
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
