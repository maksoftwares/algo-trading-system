from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r2_pullback_rejection_short_v1_exact as v1
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_PREREG_2026_07_09.md"
OUTPUT_STEM = "A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709"
TAG = "OWNER_GOAL_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_202207_202606"


def build_variants() -> list[a1.Variant]:
    base = {
        **v1.R2_BASE_INPUTS,
        "InpR2PullbackConfirmTimeframe": "60",
        "InpR2PullbackLookbackBars": "3",
        "InpR2PullbackM5ExecutionBodyFilterEnabled": "true",
        "InpR2PullbackM5MinBodyFraction": "0.58",
    }
    return [
        a1.Variant(
            name="r2_h1_m5_body58",
            label="Strict R2 H1 rejection short, M5 execution body >= 0.58, fixed 2R",
            run_id="BT_A1_XAU_R2_H1_M5_BODY58",
            tester_inputs=base,
        ),
        a1.Variant(
            name="r2_h1_m5_body58_hours05_18",
            label="Strict R2 H1 rejection short, M5 body >= 0.58, server hours 05-18, fixed 2R",
            run_id="BT_A1_XAU_R2_H1_M5_BODY58_HOURS05_18",
            tester_inputs={
                **base,
                "InpUseDirectionalSessionFilter": "true",
                "InpShortSessionStartHour": "5",
                "InpShortSessionEndHour": "19",
            },
        ),
    ]


def repair_checks(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "wr_ge_50": row["wr"] >= 50.0,
        "trades_ge_80_review_candidate": row["signals"] >= 80,
        "wl_ge_1p90": (row["wl"] or 0.0) >= 1.90,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.00,
        "net_gt_0": row["net"] > 0.0,
        "recent3_net_ge_0": row["recent3_net"] >= 0.0,
        "stress_pf_ge_1p15": (row["stress_030_pf"] or 0.0) >= 1.15,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_current_r1": row["net"] > baseline["net"],
        "wr_ge_50": row["wr"] >= 50.0,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.00,
        "recent3_trades_gt_0": row["recent3_signals"] > 0,
        "recent3_net_ge_0": row["recent3_net"] >= 0.0,
        "dd_not_worse_10pct": row["max_closed_dd"] <= baseline["max_closed_dd"] * 1.10,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def decide(standalone_rows: list[dict[str, Any]]) -> tuple[str, str]:
    for row in standalone_rows:
        checks = row["repair_checks"]
        if checks["wr_ge_50"] and checks["trades_ge_80_review_candidate"] and all(
            checks[key]
            for key in [
                "wl_ge_1p90",
                "pf_ge_2",
                "net_gt_0",
                "recent3_net_ge_0",
                "stress_pf_ge_1p15",
                "top10_removed_net_gt_0",
                "top3_days_removed_net_gt_0",
            ]
        ):
            return (
                "R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_REVIEW_CANDIDATE",
                "A V2 repair variant reached WR, payoff, PF, robustness, and sample gates. Keep research-only and send for review.",
            )
    for row in standalone_rows:
        checks = row["repair_checks"]
        if checks["wr_ge_50"] and checks["wl_ge_1p90"] and checks["pf_ge_2"] and checks["net_gt_0"] and checks["recent3_net_ge_0"]:
            return (
                "R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_SHADOW_LOW_SAMPLE",
                "A V2 repair variant repaired WR and payoff quality, but sample remains below the 80-trade review-candidate gate.",
            )
    return (
        "R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_NO_SURVIVOR",
        "The V2 repair did not produce a WR/payoff repair worth review.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R2 Pullback-Rejection Short V2 Repair Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 research-only repair of the strict R2 H1 short specialist. No demo/live runtime, chart, preset, order, position, account, or broker state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Current R1 book: `{payload['current_r1_book']}`",
        f"MT5 component evidence: `{payload['outputs']['mt5_components_md']}`",
        "",
        "## Standalone Full Window",
        "",
        "| Variant | Trades | Wins | Losses | WR% | W/L | PF | Net | Stress W/L | Stress PF | Max DD | Top10 rem | Top3 days rem | Best month% | Repair status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalone_rows"]:
        share = row["best_month_share_pct"] if row["best_month_share_pct"] is not None else 0.0
        repair_status = "PASS_SAMPLE" if all(row["repair_checks"].values()) else ("LOW_SAMPLE_WR_REPAIRED" if row["repair_checks"]["wr_ge_50"] else "FAIL_WR")
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wins']} | {row['losses']} | {row['wr']:.2f} | "
            f"{row['wl'] or 0.0:.4f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['stress_030_pf'] or 0.0:.4f} | "
            f"{row['max_closed_dd']:.2f} | {row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | "
            f"{share:.2f} | `{repair_status}` |"
        )

    lines.extend(
        [
            "",
            "## Standalone Last Three Months",
            "",
            "| Variant | Recent3 trades | Recent3 WR% | Recent3 W/L | Recent3 PF | Recent3 net | June trades | June WR% | June PF | June net |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["standalone_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['recent3_signals']} | {row['recent3_wr']:.2f} | {row['recent3_wl'] or 0.0:.4f} | "
            f"{row['recent3_pf'] or 0.0:.4f} | {row['recent3_net']:.2f} | {row['june2026_signals']} | "
            f"{row['june2026_wr']:.2f} | {row['june2026_pf'] or 0.0:.4f} | {row['june2026_net']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Combined With Current R1 Book",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Recent3 trades | Recent3 net | Max DD | Combined pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["combined_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['recent3_signals']} | {row['recent3_net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {all(row['combined_checks'].values())} |"
        )

    lines.extend(["", "## Failed Checks", ""])
    for row in payload["standalone_rows"]:
        failed = [key for key, value in row["repair_checks"].items() if not value]
        lines.append(f"- `{row['name']}` standalone: {', '.join(failed) if failed else 'none'}")
    for row in payload["combined_rows"]:
        failed = [key for key, value in row["combined_checks"].items() if not value]
        lines.append(f"- `{row['name']}` combined: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Guard Summary", ""])
    for item in payload["mt5_component_details"]:
        lines.append(f"### `{item['variant']}`")
        for reason, count in sorted(item["guard_counts"]["guard_reasons"].items()):
            if reason.startswith("regime_router_block") or reason in {"directional_session_filter_block", "stop_ceiling_exceeded", "pass"}:
                lines.append(f"- `{reason}`: {count}")
        lines.append("")

    lines.extend(["## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R2 pullback-rejection short V2 repair.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    v1.require_file(PREREG)
    v1.require_file(v1.CURRENT_R1_BOOK)
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

    r1_rows = read_ledger(v1.CURRENT_R1_BOOK)
    baseline = v1.evaluate_book("current_r1_box_plus_pullback_v2_session", r1_rows)
    standalone_rows: list[dict[str, Any]] = []
    combined_rows: list[dict[str, Any]] = []
    mt5_component_details: list[dict[str, Any]] = []

    for index, result in enumerate(mt5_payload["variants"], start=1):
        rows = v1.r2_rows(result, source_priority=90 + index)
        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
        write_signal_csv(normalized_csv, rows)

        standalone = v1.evaluate_book(result["name"], rows)
        standalone["repair_checks"] = repair_checks(standalone)
        standalone_rows.append(standalone)

        combined = v1.evaluate_book(f"current_r1_plus_{result['name']}", r1_rows + rows, dedupe=True)
        combined["combined_checks"] = combined_checks(combined, baseline)
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

    status, interpretation = decide(standalone_rows)
    v1.v1.write_csv(standalone_csv, [v1.strip_heavy(row) for row in standalone_rows])
    v1.v1.write_csv(combined_csv, [v1.strip_heavy(row) for row in combined_rows])

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
        "current_r1_book": rel(v1.CURRENT_R1_BOOK),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "baseline_row": v1.strip_heavy(baseline),
        "standalone_rows": [v1.strip_heavy(row) | {"repair_checks": row["repair_checks"]} for row in standalone_rows],
        "combined_rows": [v1.strip_heavy(row) | {"combined_checks": row["combined_checks"]} for row in combined_rows],
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
                "standalone": [v1.strip_heavy(row) | {"repair_checks": row["repair_checks"]} for row in standalone_rows],
                "combined": [v1.strip_heavy(row) | {"combined_checks": row["combined_checks"]} for row in combined_rows],
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
