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
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_PREREG_2026_07_09.md"
OUTPUT_STEM = "A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709"
TAG = "OWNER_GOAL_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_202207_202606"
FAMILY_GROUP = "xau_r4_chop_prior_day_reclaim"


BASE_INPUTS = {
    **r4.R4_INPUTS,
    "InpSignalMode": "13",
    "InpRiskReward": "2.00",
    "InpMaxEstimatedCostR": "0.10",
    "InpMaxTradesPerDay": "12",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "true",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpPriorDayLevelMode": "1",
    "InpPriorDayLevelStartHour": "6",
    "InpPriorDayLevelEndHour": "22",
    "InpPriorDayLevelBreakAtr": "0.10",
    "InpPriorDayLevelTouchAtr": "0.05",
    "InpPriorDayLevelReclaimAtr": "0.10",
    "InpPriorDayLevelStopBufferAtr": "0.25",
    "InpPriorDayLevelMinBodyFraction": "0.35",
    "InpLongCloseLocation": "0.60",
    "InpShortCloseLocation": "0.40",
    "InpStopFloorPoints": "250",
    "InpStopCeilingPoints": "1400",
    "InpStopCapPoints": "0",
}


def build_variants() -> list[a1.Variant]:
    variants: list[tuple[str, str, str, str]] = [
        (
            "r4_chop_prior_day_reclaim_v1_both",
            "R4 chop-only prior-day high/low reclaim reversal, both directions, fixed 2R",
            "BT_A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_BOTH",
            "0",
        ),
        (
            "r4_chop_prior_day_reclaim_v1_long",
            "R4 chop-only prior-day-low reclaim reversal, long-only, fixed 2R",
            "BT_A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_LONG",
            "1",
        ),
        (
            "r4_chop_prior_day_reclaim_v1_short",
            "R4 chop-only prior-day-high reclaim reversal, short-only, fixed 2R",
            "BT_A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_SHORT",
            "2",
        ),
    ]
    return [
        a1.Variant(
            name=name,
            label=label,
            run_id=run_id,
            tester_inputs={**BASE_INPUTS, "InpDirectionMode": direction_mode},
        )
        for name, label, run_id, direction_mode in variants
    ]


def mt5_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = v1.mt5_rows(result, source_priority=90)
    for row in rows:
        row["component"] = result["name"]
        row["source_id"] = result["name"]
        row["upstream_source_id"] = result["name"]
        row["upstream_component"] = result["name"]
        row["family_group"] = FAMILY_GROUP
        row["cell_id"] = result["name"]
    return rows


def decide(standalones: list[dict[str, Any]], combineds: list[dict[str, Any]]) -> tuple[str, str]:
    paired = list(zip(standalones, combineds, strict=True))
    if any(all(standalone["checks"].values()) and all(combined["checks"].values()) for standalone, combined in paired):
        return (
            "R4_CHOP_PRIOR_DAY_RECLAIM_V1_REVIEW_CANDIDATE",
            "At least one R4 prior-day reclaim variant passed standalone and combined gates. Keep research-only and send for reviewer approval.",
        )
    if any(
        standalone["net"] > 0.0 or (combined["recent3_signals"] > 0 and combined["recent3_net"] >= 0.0 and combined["wr"] >= 50.0)
        for standalone, combined in paired
    ):
        return (
            "R4_CHOP_PRIOR_DAY_RECLAIM_V1_SHADOW_ONLY",
            "The R4 prior-day reclaim pass produced useful evidence but did not clear every promotion gate. Do not deploy without repair/review.",
        )
    return (
        "R4_CHOP_PRIOR_DAY_RECLAIM_V1_NO_SURVIVOR",
        "The R4 prior-day reclaim pass did not produce a positive standalone or useful combined recent-coverage result.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R4 Chop Prior-Day Reclaim V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 run using the EA-side R4 chop-only router and prior-day level reversal signal. Research-only.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Standalone Results",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalones"]:
        lines.append(_result_row(row))

    lines.extend(
        [
            "",
            "## Combined With Current R1",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["combineds"]:
        lines.append(_result_row(row))

    baseline = payload["baseline"]
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
    for section in ("standalones", "combineds"):
        for row in payload[section]:
            failed = [key for key, value in row["checks"].items() if not value]
            lines.append(f"- `{row['name']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Router / Guard Notes", ""])
    for name, counts in payload["guard_counts"].items():
        lines.append(f"### `{name}`")
        for reason, count in sorted(counts["guard_reasons"].items()):
            if reason.startswith("regime_router_block") or reason in {"pass", "stop_ceiling_exceeded", "spread_too_high", "estimated_cost_r_too_high"}:
                lines.append(f"- `{reason}`: {count}")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def _result_row(row: dict[str, Any]) -> str:
    return (
        f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
        f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_wl'] or 0.0:.4f} | "
        f"{row['stress_030_pf'] or 0.0:.4f} | {row['recent3_signals']} | {row['recent3_net']:.2f} | "
        f"{row['max_closed_dd']:.2f} | {row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | "
        f"{all(row['checks'].values())} |"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R4 chop prior-day reclaim V1.")
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

    r1_rows = read_ledger(r4.CURRENT_R1_BOOK)
    baseline = r4.enriched_book("current_r1_box_plus_v2_pullback", r1_rows)
    standalones: list[dict[str, Any]] = []
    combineds: list[dict[str, Any]] = []
    guards: dict[str, Any] = {}
    outputs: dict[str, str] = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "standalone_csv": rel(standalone_csv),
        "combined_csv": rel(combined_csv),
        "mt5_report_md": rel(mt5_report_md),
        "mt5_report_json": rel(mt5_report_json),
    }

    for result in mt5_payload["variants"]:
        rows = mt5_rows(result)
        standalone = r4.enriched_book(result["name"], rows)
        combined = r4.enriched_book(f"current_r1_plus_{result['name']}", r1_rows + rows, dedupe=True)
        standalone["checks"] = r4.standalone_checks(standalone)
        combined["checks"] = r4.combined_checks(combined, baseline)
        standalones.append(standalone)
        combineds.append(combined)
        guards[result["name"]] = guard_counts(result)

        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
        combined_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_KEPT.csv"
        combined_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_DROPPED.csv"
        write_signal_csv(normalized_csv, rows)
        write_signal_csv(combined_kept_csv, combined["data"])
        write_signal_csv(combined_dropped_csv, combined["dropped_data"])
        outputs[f"{result['name']}_normalized_trades_csv"] = rel(normalized_csv)
        outputs[f"{result['name']}_combined_kept_csv"] = rel(combined_kept_csv)
        outputs[f"{result['name']}_combined_dropped_csv"] = rel(combined_dropped_csv)

    status, interpretation = decide(standalones, combineds)
    v1.write_csv(standalone_csv, [v1.strip_heavy(row) for row in standalones])
    v1.write_csv(combined_csv, [v1.strip_heavy(row) for row in combineds])

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "current_r1_book": rel(r4.CURRENT_R1_BOOK),
        "current_r1_book_sha256": sha256_file(r4.CURRENT_R1_BOOK),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_results": mt5_payload["variants"],
        "guard_counts": guards,
        "baseline": v1.strip_heavy(baseline),
        "standalones": [v1.strip_heavy(row) | {"checks": row["checks"]} for row in standalones],
        "combineds": [v1.strip_heavy(row) | {"checks": row["checks"]} for row in combineds],
        "interpretation": interpretation,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "standalones": payload["standalones"],
                "combineds": payload["combineds"],
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
