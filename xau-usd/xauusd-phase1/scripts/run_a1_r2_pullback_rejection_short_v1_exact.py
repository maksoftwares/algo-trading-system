from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as v1
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts, period_stats
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708"
TAG = "OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_202207_202606"

CURRENT_R1_BOOK = (
    REPORTS_DIR
    / "A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_box_plus_r1_pullback_long_v2_m15_session_09_15_KEPT.csv"
)

R2_SOURCE = "r2_pullback_rejection_short_v1"
RECENT3_START = date(2026, 4, 1)
RECENT3_END = date(2026, 6, 30)
JUNE_START = date(2026, 6, 1)
JUNE_END = date(2026, 6, 30)
Y2023_2024_START = date(2023, 1, 1)
Y2023_2024_END = date(2024, 12, 31)
R1_BEST_MONTH_SHARE_REFERENCE = 30.92

YEAR_PERIODS = [
    ("2022", date(2022, 7, 1), date(2022, 12, 31)),
    ("2023", date(2023, 1, 1), date(2023, 12, 31)),
    ("2024", date(2024, 1, 1), date(2024, 12, 31)),
    ("2025", date(2025, 1, 1), date(2025, 12, 31)),
    ("2026", date(2026, 1, 1), date(2026, 6, 30)),
]


R2_BASE_INPUTS = {
    **ROUTER_INPUTS,
    "InpRegimeRouterMode": "2",
    "InpDirectionMode": "2",
    "InpSignalMode": "21",
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
    "InpR2PullbackH1FastEmaPeriod": "20",
    "InpR2PullbackH1SlowEmaPeriod": "50",
    "InpR2PullbackTouchAtr": "0.25",
    "InpR2PullbackStopBufferAtr": "0.25",
    "InpR2PullbackMinBodyFraction": "0.35",
    "InpR2PullbackCloseLocation": "0.35",
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def stable_hash(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def git_value(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="r2_pullback_short_m15_confirm",
            label="Strict R2 failed-rally short, M15 rejection confirmation, fixed 2R",
            run_id="BT_A1_XAU_R2_PULLBACK_SHORT_M15_CONFIRM",
            tester_inputs={
                **R2_BASE_INPUTS,
                "InpR2PullbackConfirmTimeframe": "15",
                "InpR2PullbackLookbackBars": "6",
            },
        ),
        a1.Variant(
            name="r2_pullback_short_h1_confirm",
            label="Strict R2 failed-rally short, H1 rejection confirmation, fixed 2R",
            run_id="BT_A1_XAU_R2_PULLBACK_SHORT_H1_CONFIRM",
            tester_inputs={
                **R2_BASE_INPUTS,
                "InpR2PullbackConfirmTimeframe": "60",
                "InpR2PullbackLookbackBars": "3",
            },
        ),
    ]


def r2_rows(result: dict[str, Any], source_priority: int) -> list[dict[str, Any]]:
    rows = v1.mt5_rows(result, source_priority=source_priority)
    for row in rows:
        row["component"] = R2_SOURCE
        row["source_id"] = R2_SOURCE
        row["upstream_source_id"] = R2_SOURCE
        row["upstream_component"] = result["name"]
        row["family_group"] = "xau_r2_pullback_rejection_short"
        row["cell_id"] = "r2_pullback_rejection_short_v1"
    return rows


def period_row(rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    stats = period_stats(rows, start, end)
    return {
        "signals": stats["signals"],
        "wins": stats["wins"],
        "losses": stats["losses"],
        "wr": stats["win_rate_pct"],
        "wl": stats["avg_win_loss"],
        "pf": stats["profit_factor"],
        "net": stats["net_usd"],
    }


def yearly_rows(name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"name": name, "period": label, **period_row(rows, start, end)}
        for label, start, end in YEAR_PERIODS
    ]


def monthly_rows(name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for year in range(2022, 2027):
        for month in range(1, 13):
            start = date(year, month, 1)
            if start < date(2022, 7, 1) or start > date(2026, 6, 30):
                continue
            end_month = month + 1
            end_year = year
            if end_month == 13:
                end_month = 1
                end_year += 1
            end = date(end_year, end_month, 1)
            end = date.fromordinal(end.toordinal() - 1)
            stats = period_row(rows, start, end)
            if stats["signals"] > 0:
                output.append({"name": name, "period": f"{year:04d}-{month:02d}", **stats})
    return output


def add_periods(book: dict[str, Any]) -> dict[str, Any]:
    rows = book["data"]
    recent3 = period_row(rows, RECENT3_START, RECENT3_END)
    june = period_row(rows, JUNE_START, JUNE_END)
    y2023_2024 = period_row(rows, Y2023_2024_START, Y2023_2024_END)
    return {
        **book,
        "recent3_signals": recent3["signals"],
        "recent3_wr": recent3["wr"],
        "recent3_wl": recent3["wl"],
        "recent3_pf": recent3["pf"],
        "recent3_net": recent3["net"],
        "june2026_signals": june["signals"],
        "june2026_wr": june["wr"],
        "june2026_wl": june["wl"],
        "june2026_pf": june["pf"],
        "june2026_net": june["net"],
        "y2023_2024_signals": y2023_2024["signals"],
        "y2023_2024_wr": y2023_2024["wr"],
        "y2023_2024_wl": y2023_2024["wl"],
        "y2023_2024_pf": y2023_2024["pf"],
        "y2023_2024_net": y2023_2024["net"],
        "yearly_rows": yearly_rows(book["name"], rows),
        "monthly_rows": monthly_rows(book["name"], rows),
    }


def evaluate_book(name: str, rows: list[dict[str, Any]], *, dedupe: bool = False) -> dict[str, Any]:
    return add_periods(v1.evaluate_book(name, rows, dedupe=dedupe))


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    best_month_share = row["best_month_share_pct"]
    return {
        "trades_ge_80": row["signals"] >= 80,
        "wr_ge_45_watchlist": row["wr"] >= 45.0,
        "wr_ge_50_true_pass": row["wr"] >= 50.0,
        "wl_ge_1p90": (row["wl"] or 0.0) >= 1.90,
        "pf_ge_1p25": (row["pf"] or 0.0) >= 1.25,
        "stress_pf_ge_1p15": (row["stress_030_pf"] or 0.0) >= 1.15,
        "stress_net_gt_0": row["stress_030_net"] > 0.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_35pct": best_month_share is not None and best_month_share <= 35.0,
        "june_nonnegative_if_exposed": row["june2026_signals"] == 0 or row["june2026_net"] >= 0.0,
        "recent3_nonnegative_if_exposed": row["recent3_signals"] == 0 or row["recent3_net"] >= 0.0,
        "y2023_2024_nonnegative_if_exposed": row["y2023_2024_signals"] == 0 or row["y2023_2024_net"] >= 0.0,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    best_month_limit = baseline["best_month_share_pct"] if baseline["best_month_share_pct"] is not None else R1_BEST_MONTH_SHARE_REFERENCE
    return {
        "net_gt_current_r1": row["net"] > baseline["net"],
        "recent3_trades_gt_0": row["recent3_signals"] > 0,
        "recent3_net_ge_0": row["recent3_net"] >= 0.0,
        "wr_ge_49": row["wr"] >= 49.0,
        "wl_or_stress_wl_ok": (row["wl"] or 0.0) >= 2.00 or (row["stress_030_wl"] or 0.0) >= 1.90,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.00,
        "dd_not_worse_10pct": row["max_closed_dd"] <= baseline["max_closed_dd"] * 1.10,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_current_r1": row["best_month_share_pct"] is not None and row["best_month_share_pct"] <= best_month_limit,
    }


def stop_path_checks(row: dict[str, Any], combined: dict[str, Any]) -> dict[str, bool]:
    return {
        "wr_lt_40": row["wr"] < 40.0,
        "pf_lt_1p10": (row["pf"] or 0.0) < 1.10,
        "stress_net_lte_0": row["stress_030_net"] <= 0.0,
        "top10_removed_net_lte_0": row["top10_removed_net"] <= 0.0,
        "top3_days_removed_net_lte_0": row["top3_days_removed_net"] <= 0.0,
        "combined_wl_lt_1p90": (combined["wl"] or 0.0) < 1.90,
        "combined_pf_lt_1p80": (combined["pf"] or 0.0) < 1.80,
    }


def decide(standalone_rows: list[dict[str, Any]], combined_rows: list[dict[str, Any]]) -> tuple[str, str]:
    for standalone, combined in zip(standalone_rows, combined_rows):
        if all(standalone["checks"].values()) and all(combined["checks"].values()):
            return (
                "R2_PULLBACK_REJECTION_SHORT_V1_REVIEW_CANDIDATE",
                "At least one strict R2 pullback-rejection short variant passed standalone and combined gates. Keep research-only and send for reviewer approval before any demo or forward spec.",
            )
    if any(row["net"] > 0.0 for row in standalone_rows):
        return (
            "R2_PULLBACK_REJECTION_SHORT_V1_SHADOW_ONLY",
            "At least one strict R2 variant was positive, but no variant cleared the full standalone-plus-combined gate set. Keep as research-only shadow evidence.",
        )
    return (
        "R2_PULLBACK_REJECTION_SHORT_V1_NO_SURVIVOR",
        "Both strict R2 pullback-rejection variants failed to produce a positive standalone specialist. Do not relax R2 or tune thresholds without reviewer approval.",
    )


def check_runner_static(variants: list[a1.Variant]) -> dict[str, bool]:
    forbidden_filter_fields = {
        "InpBlockedEntryHoursCsv",
        "InpBlockedEntryDayHoursCsv",
        "InpBlockedLongEntryHoursCsv",
        "InpBlockedShortEntryHoursCsv",
    }
    return {
        "variant_count_eq_2": len(variants) == 2,
        "all_strict_r2_router": all(variant.tester_inputs.get("InpRegimeRouterMode") == "2" for variant in variants),
        "all_short_only": all(variant.tester_inputs.get("InpDirectionMode") == "2" for variant in variants),
        "all_signal_21": all(variant.tester_inputs.get("InpSignalMode") == "21" for variant in variants),
        "all_rr_2": all(variant.tester_inputs.get("InpRiskReward") == "2.00" for variant in variants),
        "no_session_filter": all(variant.tester_inputs.get("InpUseDirectionalSessionFilter") == "false" for variant in variants),
        "no_hour_day_filters": all(all(variant.tester_inputs.get(field, "") == "" for field in forbidden_filter_fields) for variant in variants),
        "no_breakeven_partial_trailing": all(
            variant.tester_inputs.get("InpProfitProtectionEnabled") == "false"
            and variant.tester_inputs.get("InpPartialCloseEnabled") == "false"
            and variant.tester_inputs.get("InpSplitEntryEnabled") == "false"
            for variant in variants
        ),
    }


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in v1.strip_heavy(row).items()
        if key not in {"yearly_rows", "monthly_rows"}
    }


def table_period_lines(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["| Book | Period | Trades | WR% | W/L | PF | Net |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(
            f"| `{row['name']}` | `{row['period']}` | {row['signals']} | {row['wr']:.2f} | "
            f"{row['wl'] or 0.0:.4f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} |"
        )
    return lines


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R2 Pullback-Rejection Short V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Scope and Runtime Boundary",
        "",
        "Exact-MT5 research-only run for a strict Router V1 R2 short specialist. No demo/live runtime, chart, preset, profile, order, position, account, or broker state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"EA source commit hash: `{payload['ea_source_commit_hash']}`",
        f"Repo HEAD during run: `{payload['repo_head']}`",
        f"Tester input set SHA256: `{payload['tester_input_set_sha256']}`",
        f"MT5 raw component evidence: `{payload['outputs']['mt5_components_md']}`",
        f"Compile log: `{payload['compile_log']}`",
        "",
        "## Standalone Results",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Stress net | Recent3 trades | Recent3 net | June trades | June net | 2023+2024 net | Max DD | Best month% | Top10 rem | Top3 days rem | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalone_rows"]:
        share = row["best_month_share_pct"] if row["best_month_share_pct"] is not None else 0.0
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['stress_030_pf'] or 0.0:.4f} | {row['stress_030_net']:.2f} | "
            f"{row['recent3_signals']} | {row['recent3_net']:.2f} | {row['june2026_signals']} | "
            f"{row['june2026_net']:.2f} | {row['y2023_2024_net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{share:.2f} | {row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | {all(row['checks'].values())} |"
        )

    lines.extend(
        [
            "",
            "## Combined With Current R1 Book",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Best month% | Dropped | Top10 rem | Top3 days rem | Pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["combined_rows"]:
        share = row["best_month_share_pct"] if row["best_month_share_pct"] is not None else 0.0
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['stress_030_pf'] or 0.0:.4f} | {row['recent3_signals']} | {row['recent3_net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {share:.2f} | {row['dropped_signals']} | "
            f"{row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | {all(row['checks'].values())} |"
        )

    baseline = payload["baseline_row"]
    lines.extend(
        [
            "",
            "## Current R1 Reference",
            "",
            f"Current R1 book: {baseline['signals']} trades, WR {baseline['wr']:.2f}%, W/L {baseline['wl'] or 0.0:.4f}, "
            f"PF {baseline['pf'] or 0.0:.4f}, net {baseline['net']:.2f}, recent3 trades {baseline['recent3_signals']}, "
            f"recent3 net {baseline['recent3_net']:.2f}, max DD {baseline['max_closed_dd']:.2f}, "
            f"best-month share {baseline['best_month_share_pct'] or 0.0:.2f}%.",
            "",
            "## Router Block Summary",
            "",
        ]
    )
    for item in payload["mt5_component_details"]:
        lines.append(f"### `{item['variant']}`")
        guard_reasons = item["guard_counts"]["guard_reasons"]
        shown = False
        for reason, count in sorted(guard_reasons.items()):
            if reason.startswith("regime_router_block") or reason in {"pass", "stop_ceiling_exceeded", "spread_too_high", "estimated_cost_r_too_high", "observer_mode"}:
                lines.append(f"- `{reason}`: {count}")
                shown = True
        if not shown:
            lines.append("- no selected guard reasons logged")
        lines.append("")

    lines.extend(["## Yearly Table", ""])
    yearly: list[dict[str, Any]] = []
    for row in payload["standalone_rows"] + payload["combined_rows"]:
        yearly.extend(row["yearly_rows"])
    lines.extend(table_period_lines(yearly))

    lines.extend(["", "## Monthly Table", ""])
    monthly: list[dict[str, Any]] = []
    for row in payload["standalone_rows"] + payload["combined_rows"]:
        monthly.extend(row["monthly_rows"])
    lines.extend(table_period_lines(monthly))

    lines.extend(["", "## Failed Checks", ""])
    for row in payload["standalone_rows"] + payload["combined_rows"]:
        failed = [key for key, value in row["checks"].items() if not value]
        lines.append(f"- `{row['name']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Stop Path Checks", ""])
    for item in payload["stop_path_checks"]:
        triggered = [key for key, value in item["checks"].items() if value]
        lines.append(f"- `{item['variant']}`: {', '.join(triggered) if triggered else 'none'}")

    lines.extend(["", "## Static Validation", ""])
    for key, value in payload["static_checks"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R2 pullback-rejection short V1.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(CURRENT_R1_BOOK)

    variants = build_variants()
    static_checks = check_runner_static(variants)
    if not all(static_checks.values()):
        raise RuntimeError(f"Invalid static runner configuration: {static_checks}")

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

    r1_rows = read_ledger(CURRENT_R1_BOOK)
    baseline = evaluate_book("current_r1_box_plus_pullback_v2_session", r1_rows)
    standalone_rows: list[dict[str, Any]] = []
    combined_rows: list[dict[str, Any]] = []
    mt5_component_details: list[dict[str, Any]] = []
    stop_checks: list[dict[str, Any]] = []

    for index, result in enumerate(mt5_payload["variants"], start=1):
        variant = variants[index - 1]
        rows = r2_rows(result, source_priority=82 + index)
        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
        write_signal_csv(normalized_csv, rows)

        standalone = evaluate_book(result["name"], rows)
        standalone["checks"] = standalone_checks(standalone)
        standalone_rows.append(standalone)

        combined = evaluate_book(f"current_r1_plus_{result['name']}", r1_rows + rows, dedupe=True)
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
                "tester_input_sha256": stable_hash(variant.tester_inputs),
            }
        )
        stop_checks.append({"variant": result["name"], "checks": stop_path_checks(standalone, combined)})

    status, interpretation = decide(standalone_rows, combined_rows)
    v1.write_csv(standalone_csv, [strip_heavy(row) for row in standalone_rows])
    v1.write_csv(combined_csv, [strip_heavy(row) for row in combined_rows])

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
        "current_r1_book": rel(CURRENT_R1_BOOK),
        "current_r1_book_sha256": sha256_file(CURRENT_R1_BOOK),
        "repo_head": git_value(["rev-parse", "HEAD"]),
        "ea_source_commit_hash": git_value(["log", "-1", "--format=%H", "--", a1.EA_SOURCE.relative_to(REPO_ROOT).as_posix()]),
        "tester_input_set_sha256": stable_hash([variant.tester_inputs for variant in variants]),
        "variant_inputs": [{"name": variant.name, "tester_inputs": variant.tester_inputs, "sha256": stable_hash(variant.tester_inputs)} for variant in variants],
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "baseline_row": strip_heavy(baseline),
        "standalone_rows": [strip_heavy(row) | {"checks": row["checks"], "yearly_rows": row["yearly_rows"], "monthly_rows": row["monthly_rows"]} for row in standalone_rows],
        "combined_rows": [strip_heavy(row) | {"checks": row["checks"], "yearly_rows": row["yearly_rows"], "monthly_rows": row["monthly_rows"]} for row in combined_rows],
        "mt5_component_details": mt5_component_details,
        "stop_path_checks": stop_checks,
        "static_checks": static_checks,
        "interpretation": interpretation,
        "outputs": outputs,
    }

    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
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
