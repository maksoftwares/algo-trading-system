from __future__ import annotations

import argparse
import json
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
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708"
TAG = "OWNER_GOAL_R4_CHOP_FAILED_BREAK_V1_EXACT_202207_202606"

CURRENT_R1_BOOK = (
    REPORTS_DIR
    / "A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_box_plus_r1_pullback_long_v2_m15_session_09_15_KEPT.csv"
)
R4_SOURCE = "r4_chop_failed_break_v1_sweep_reclaim"
RECENT3_START = date(2026, 4, 1)
RECENT3_END = date(2026, 6, 30)


R4_INPUTS = {
    **ROUTER_INPUTS,
    "InpRegimeRouterMode": "4",
    "InpSignalMode": "3",
    "InpDirectionMode": "0",
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
    "InpSweepLookbackBars": "12",
    "InpSweepAtrMultiple": "0.10",
    "InpReclaimAtrMultiple": "0.05",
    "InpMinRangeAtr": "0.60",
    "InpMinBodyFraction": "0.45",
    "InpLongCloseLocation": "0.72",
    "InpShortCloseLocation": "0.28",
    "InpStopFloorPoints": "350",
    "InpStopCeilingPoints": "2200",
    "InpStopCapPoints": "0",
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="r4_chop_failed_break_v1_sweep_reclaim",
            label="R4 chop-only M5 sweep-reclaim failed-break, both directions, fixed 2R",
            run_id="BT_A1_XAU_R4_CHOP_FAILED_BREAK_V1_SWEEP_RECLAIM",
            tester_inputs=R4_INPUTS,
        )
    ]


def mt5_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = v1.mt5_rows(result, source_priority=90)
    for row in rows:
        row["component"] = R4_SOURCE
        row["source_id"] = R4_SOURCE
        row["upstream_source_id"] = R4_SOURCE
        row["upstream_component"] = result["name"]
        row["family_group"] = "xau_r4_chop_failed_break"
        row["cell_id"] = "r4_chop_failed_break_v1"
    return rows


def period_net(rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
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


def enriched_book(name: str, rows: list[dict[str, Any]], *, dedupe: bool = False) -> dict[str, Any]:
    book = v1.evaluate_book(name, rows, dedupe=dedupe)
    recent3 = period_net(book["data"], RECENT3_START, RECENT3_END)
    y2023_2024 = period_net(book["data"], date(2023, 1, 1), date(2024, 12, 31))
    return {
        **book,
        "recent3_signals": recent3["signals"],
        "recent3_wr": recent3["wr"],
        "recent3_wl": recent3["wl"],
        "recent3_pf": recent3["pf"],
        "recent3_net": recent3["net"],
        "net_2023_2024": y2023_2024["net"],
    }


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "trades_ge_150": row["signals"] >= 150,
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_1p80": (row["wl"] or 0.0) >= 1.80,
        "pf_ge_1p50": (row["pf"] or 0.0) >= 1.50,
        "stress_pf_ge_1p30": (row["stress_030_pf"] or 0.0) >= 1.30,
        "stress_wl_ge_1p65": (row["stress_030_wl"] or 0.0) >= 1.65,
        "net_gt_0": row["net"] > 0.0,
        "recent3_trades_ge_30": row["recent3_signals"] >= 30,
        "recent3_net_gt_0": row["recent3_net"] > 0.0,
        "net_2023_2024_ge_0": row["net_2023_2024"] >= 0.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_current_r1": row["net"] > baseline["net"],
        "recent3_trades_gt_0": row["recent3_signals"] > 0,
        "recent3_net_ge_0": row["recent3_net"] >= 0.0,
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_or_stress_wl_ok": (row["wl"] or 0.0) >= 2.00 or (row["stress_030_wl"] or 0.0) >= 1.90,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.00,
        "dd_not_worse_15pct": row["max_closed_dd"] <= baseline["max_closed_dd"] * 1.15,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def decide(standalone: dict[str, Any], combined: dict[str, Any]) -> tuple[str, str]:
    if all(standalone["checks"].values()) and all(combined["checks"].values()):
        return (
            "R4_CHOP_FAILED_BREAK_V1_REVIEW_CANDIDATE",
            "The chop failed-break specialist passed standalone and combined gates. Keep research-only and send for reviewer approval.",
        )
    if standalone["net"] > 0.0 or (combined["recent3_signals"] > 0 and combined["recent3_net"] >= 0.0 and combined["wr"] >= 50.0):
        return (
            "R4_CHOP_FAILED_BREAK_V1_SHADOW_ONLY",
            "The chop failed-break test produced useful evidence but did not clear every promotion gate. Do not deploy without repair/review.",
        )
    return (
        "R4_CHOP_FAILED_BREAK_V1_NO_SURVIVOR",
        "The chop failed-break test did not produce a positive standalone or useful combined recent-coverage result.",
    )


def render(payload: dict[str, Any]) -> str:
    standalone = payload["standalone"]
    combined = payload["combined"]
    baseline = payload["baseline"]
    lines = [
        "# A1 XAU R4 Chop Failed-Break V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 run using the EA-side R4 chop-only router. Research-only.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Results",
        "",
        "| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in [standalone, combined]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['stress_030_pf'] or 0.0:.4f} | {row['recent3_signals']} | {row['recent3_net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | {all(row['checks'].values())} |"
        )

    lines.extend(
        [
            "",
            "## Current R1 Baseline",
            "",
            f"Current R1 book: {baseline['signals']} trades, WR {baseline['wr']:.2f}%, W/L {baseline['wl'] or 0.0:.4f}, "
            f"PF {baseline['pf'] or 0.0:.4f}, net {baseline['net']:.2f}, recent3 trades {baseline['recent3_signals']}, "
            f"recent3 net {baseline['recent3_net']:.2f}, max DD {baseline['max_closed_dd']:.2f}.",
            "",
            "## Failed Checks",
            "",
        ]
    )
    for row in [standalone, combined]:
        failed = [key for key, value in row["checks"].items() if not value]
        lines.append(f"- `{row['name']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Router / Guard Notes", ""])
    guard_reasons = payload["guard_counts"]["guard_reasons"]
    for reason, count in sorted(guard_reasons.items()):
        if reason.startswith("regime_router_block") or reason in {"pass", "stop_ceiling_exceeded", "spread_too_high", "estimated_cost_r_too_high"}:
            lines.append(f"- `{reason}`: {count}")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R4 chop failed-break V1.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(CURRENT_R1_BOOK)

    variants = build_variants()
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
    r4_rows = mt5_rows(result)
    r1_rows = read_ledger(CURRENT_R1_BOOK)
    standalone = enriched_book(result["name"], r4_rows)
    baseline = enriched_book("current_r1_box_plus_v2_pullback", r1_rows)
    combined = enriched_book(f"current_r1_plus_{result['name']}", r1_rows + r4_rows, dedupe=True)

    standalone["checks"] = standalone_checks(standalone)
    combined["checks"] = combined_checks(combined, baseline)
    status, interpretation = decide(standalone, combined)

    normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
    combined_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_KEPT.csv"
    combined_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_DROPPED.csv"
    write_signal_csv(normalized_csv, r4_rows)
    write_signal_csv(combined_kept_csv, combined["data"])
    write_signal_csv(combined_dropped_csv, combined["dropped_data"])
    v1.write_csv(standalone_csv, [v1.strip_heavy(standalone)])
    v1.write_csv(combined_csv, [v1.strip_heavy(combined)])

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
        "current_r1_book": rel(CURRENT_R1_BOOK),
        "current_r1_book_sha256": sha256_file(CURRENT_R1_BOOK),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_result": result,
        "guard_counts": guard_counts(result),
        "baseline": v1.strip_heavy(baseline),
        "standalone": v1.strip_heavy(standalone) | {"checks": standalone["checks"]},
        "combined": v1.strip_heavy(combined) | {"checks": combined["checks"]},
        "interpretation": interpretation,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "standalone": v1.strip_heavy(standalone) | {"checks": standalone["checks"]},
                "combined": v1.strip_heavy(combined) | {"checks": combined["checks"]},
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
