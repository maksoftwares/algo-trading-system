from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as v1
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708"
TAG = "OWNER_GOAL_R1_PULLBACK_LONG_V2_SESSION_EXACT_202207_202606"


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="r1_pullback_long_v2_m15_session_09_15",
            label="R1 H1 EMA20 pullback long, M15 confirmation, server hours 09-14, fixed 2R",
            run_id="BT_A1_XAU_R1_PULLBACK_LONG_V2_M15_SESSION_09_15",
            tester_inputs={
                **v1.PULLBACK_BASE_INPUTS,
                "InpR1PullbackConfirmTimeframe": "15",
                "InpUseDirectionalSessionFilter": "true",
                "InpLongSessionStartHour": "9",
                "InpLongSessionEndHour": "15",
            },
        )
    ]


def decide(standalone_rows: list[dict[str, Any]], combined_rows: list[dict[str, Any]]) -> tuple[str, str]:
    if any(all(row["checks"].values()) for row in standalone_rows) and any(all(row["checks"].values()) for row in combined_rows):
        return (
            "R1_PULLBACK_LONG_V2_SESSION_REVIEW_CANDIDATE",
            "The single preregistered session repair passed standalone and combined-with-box gates. Keep research-only and send for reviewer approval before any demo spec.",
        )
    if any(row["net"] > 0.0 for row in standalone_rows):
        return (
            "R1_PULLBACK_LONG_V2_SESSION_SHADOW_ONLY",
            "The session repair stayed positive but did not clear every promotion gate. Do not add it to the deployable R1 book without review.",
        )
    return (
        "R1_PULLBACK_LONG_V2_SESSION_NO_SURVIVOR",
        "The session repair did not preserve positive evidence. Retire this repair path.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R1 Pullback Long V2 Session Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 component rerun using the EA-side R1 router and one preregistered session repair. Research-only.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Standalone Result",
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

    baseline = payload["baseline_row"]
    lines.extend(
        [
            "",
            "## Baseline",
            "",
            f"Routed R1 box baseline: {baseline['signals']} trades, WR {baseline['wr']:.2f}%, "
            f"W/L {baseline['wl'] or 0.0:.4f}, PF {baseline['pf'] or 0.0:.4f}, net {baseline['net']:.2f}, "
            f"active {baseline['active_weekday_pct']:.2f}%, max DD {baseline['max_closed_dd']:.2f}.",
            "",
            "## Failed Checks",
            "",
        ]
    )
    for row in payload["standalone_rows"] + payload["combined_rows"]:
        failed = [key for key, value in row["checks"].items() if not value]
        lines.append(f"- `{row['name']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Router / Guard Notes", ""])
    for item in payload["mt5_component_details"]:
        lines.append(f"### `{item['variant']}`")
        guard_reasons = item["guard_counts"]["guard_reasons"]
        for reason, count in sorted(guard_reasons.items()):
            if reason.startswith("regime_router_block") or reason in {"directional_session_filter_block", "pass"}:
                lines.append(f"- `{reason}`: {count}")
        lines.append("")

    lines.extend(["## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R1 pullback long V2 session repair.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    if not PREREG.exists():
        raise FileNotFoundError(PREREG)
    if not v1.BOX_BASELINE_CSV.exists():
        raise FileNotFoundError(v1.BOX_BASELINE_CSV)

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

    box_rows = read_ledger(v1.BOX_BASELINE_CSV)
    baseline = v1.evaluate_book("router_v1_r1_long_box2_prevhealth", box_rows)
    standalone_rows: list[dict[str, Any]] = []
    combined_rows: list[dict[str, Any]] = []
    mt5_component_details: list[dict[str, Any]] = []

    for result in mt5_payload["variants"]:
        rows = v1.mt5_rows(result, source_priority=71)
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv", rows)

        standalone = v1.evaluate_book(result["name"], rows)
        standalone["checks"] = v1.standalone_checks(standalone)
        standalone_rows.append(standalone)

        combined = v1.evaluate_book(f"box_plus_{result['name']}", box_rows + rows, dedupe=True)
        combined["checks"] = v1.combined_checks(combined, baseline)
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

    v1.write_csv(standalone_csv, [v1.strip_heavy(row) for row in standalone_rows])
    v1.write_csv(combined_csv, [v1.strip_heavy(row) for row in combined_rows])

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
        "box_baseline_csv": rel(v1.BOX_BASELINE_CSV),
        "box_baseline_sha256": sha256_file(v1.BOX_BASELINE_CSV),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "baseline_row": v1.strip_heavy(baseline),
        "standalone_rows": [v1.strip_heavy(row) | {"checks": row["checks"]} for row in standalone_rows],
        "combined_rows": [v1.strip_heavy(row) | {"checks": row["checks"]} for row in combined_rows],
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
                "baseline": v1.strip_heavy(baseline),
                "standalone": [v1.strip_heavy(row) | {"checks": row["checks"]} for row in standalone_rows],
                "combined": [v1.strip_heavy(row) | {"checks": row["checks"]} for row in combined_rows],
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
