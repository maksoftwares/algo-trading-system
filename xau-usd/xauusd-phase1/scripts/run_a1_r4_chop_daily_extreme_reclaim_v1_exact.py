from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as v1
import run_a1_r4_chop_failed_break_v1_exact as r4
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_20260708"
TAG = "OWNER_GOAL_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_EXACT_202207_202606"
SOURCE_ID = "r4_chop_daily_extreme_reclaim_v1_liquid"


DER_INPUTS = {
    **r4.R4_INPUTS,
    "InpSignalMode": "11",
    "InpRiskReward": "2.00",
    "InpMaxTradesPerDay": "24",
    "InpMaxOpenPositionsPerMagic": "16",
    "InpMinRangeAtr": "0.20",
    "InpLongCloseLocation": "0.58",
    "InpShortCloseLocation": "0.42",
    "InpDailyExtremeMinMoveAtr": "1.00",
    "InpDailyExtremeTouchAtr": "0.06",
    "InpDailyExtremeReclaimAtr": "0.10",
    "InpDailyExtremeStopBufferAtr": "0.10",
    "InpDailyExtremeMinBodyFraction": "0.25",
    "InpDailyExtremeMinBarsSinceOpen": "24",
    "InpDailyExtremeStartHour": "7",
    "InpDailyExtremeEndHour": "22",
    "InpStopFloorPoints": "100",
    "InpStopCeilingPoints": "0",
}


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="r4_chop_daily_extreme_reclaim_v1_liquid",
            label="R4 chop-only daily extreme reclaim, liquid session, both directions, fixed 2R",
            run_id="BT_A1_XAU_R4_CHOP_DAILY_EXTREME_RECLAIM_V1_LIQUID",
            tester_inputs=DER_INPUTS,
        )
    ]


def mt5_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = v1.mt5_rows(result, source_priority=90)
    for row in rows:
        row["component"] = SOURCE_ID
        row["source_id"] = SOURCE_ID
        row["upstream_source_id"] = SOURCE_ID
        row["upstream_component"] = result["name"]
        row["family_group"] = "xau_r4_chop_daily_extreme_reclaim"
        row["cell_id"] = "r4_chop_daily_extreme_reclaim_v1"
    return rows


def decide(standalone: dict[str, Any], combined: dict[str, Any]) -> tuple[str, str]:
    if all(standalone["checks"].values()) and all(combined["checks"].values()):
        return (
            "R4_CHOP_DAILY_EXTREME_RECLAIM_V1_REVIEW_CANDIDATE",
            "The daily-extreme R4 specialist passed standalone and combined gates. Keep research-only and send for reviewer approval.",
        )
    if standalone["net"] > 0.0 or (combined["recent3_signals"] > 0 and combined["recent3_net"] >= 0.0 and combined["wr"] >= 50.0):
        return (
            "R4_CHOP_DAILY_EXTREME_RECLAIM_V1_SHADOW_ONLY",
            "The daily-extreme R4 test produced useful evidence but did not clear every promotion gate. Do not deploy without repair/review.",
        )
    return (
        "R4_CHOP_DAILY_EXTREME_RECLAIM_V1_NO_SURVIVOR",
        "The daily-extreme R4 test did not produce a positive standalone or useful combined recent-coverage result.",
    )


def render(payload: dict[str, Any]) -> str:
    standalone = payload["standalone"]
    combined = payload["combined"]
    baseline = payload["baseline"]
    lines = [
        "# A1 XAU R4 Chop Daily-Extreme Reclaim V1 Exact-MT5",
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
    parser = argparse.ArgumentParser(description="Run exact-MT5 R4 chop daily-extreme reclaim V1.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    r4.require_file(PREREG)
    r4.require_file(r4.CURRENT_R1_BOOK)

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
    candidate_rows = mt5_rows(result)
    r1_rows = read_ledger(r4.CURRENT_R1_BOOK)
    standalone = r4.enriched_book(result["name"], candidate_rows)
    baseline = r4.enriched_book("current_r1_box_plus_v2_pullback", r1_rows)
    combined = r4.enriched_book(f"current_r1_plus_{result['name']}", r1_rows + candidate_rows, dedupe=True)

    standalone["checks"] = r4.standalone_checks(standalone)
    combined["checks"] = r4.combined_checks(combined, baseline)
    status, interpretation = decide(standalone, combined)

    normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
    combined_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_KEPT.csv"
    combined_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_DROPPED.csv"
    write_signal_csv(normalized_csv, candidate_rows)
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
        "current_r1_book": rel(r4.CURRENT_R1_BOOK),
        "current_r1_book_sha256": sha256_file(r4.CURRENT_R1_BOOK),
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
