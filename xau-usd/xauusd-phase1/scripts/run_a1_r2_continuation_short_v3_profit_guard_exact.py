from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_r2_continuation_short_v1_exact as v1
import run_a1_r2_pullback_rejection_short_v1_exact as r2v1
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_PREREG_2026_07_09.md"
OUTPUT_STEM = "A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709"
TAG = "OWNER_GOAL_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_202207_202606"

V1_COMBINED_REFERENCE = {
    "name": "current_r1_best_r2_pullback_plus_r2_impulse_retest_body45",
    "signals": 1060,
    "wr": 44.72,
    "pf": 2.4634,
    "net": 9750.48,
    "recent3_signals": 88,
    "recent3_wr": 55.68,
    "recent3_net": 818.35,
    "max_closed_dd": 889.69,
}


def build_variants() -> list[a1.Variant]:
    base = {
        **v1.COMMON_CONT_INPUTS,
        "InpSignalMode": "19",
        "InpPortfolioDailyGuardEnabled": "true",
    }
    return [
        a1.Variant(
            name="r2_impulse_body45_daily_loss7",
            label="Strict R2 impulse/retest body45 with portfolio daily loss stop -$7",
            run_id="BT_A1_XAU_R2_IMPULSE_BODY45_DAILY_LOSS7",
            tester_inputs={
                **base,
                "InpPortfolioDailyLossStopUsd": "7.00",
            },
        ),
        a1.Variant(
            name="r2_impulse_body45_daily_loss10",
            label="Strict R2 impulse/retest body45 with portfolio daily loss stop -$10",
            run_id="BT_A1_XAU_R2_IMPULSE_BODY45_DAILY_LOSS10",
            tester_inputs={
                **base,
                "InpPortfolioDailyLossStopUsd": "10.00",
            },
        ),
        a1.Variant(
            name="r2_impulse_body45_loss_cooldown240",
            label="Strict R2 impulse/retest body45 with 240 minute cooldown after closed loss",
            run_id="BT_A1_XAU_R2_IMPULSE_BODY45_LOSS_COOLDOWN240",
            tester_inputs={
                **base,
                "InpPortfolioCooldownAfterLossMinutes": "240",
            },
        ),
    ]


def static_checks(variants: list[a1.Variant]) -> dict[str, bool]:
    return {
        "variant_count_eq_3": len(variants) == 3,
        "all_strict_r2_router": all(variant.tester_inputs.get("InpRegimeRouterMode") == "2" for variant in variants),
        "all_short_only": all(variant.tester_inputs.get("InpDirectionMode") == "2" for variant in variants),
        "all_signal_19": all(variant.tester_inputs.get("InpSignalMode") == "19" for variant in variants),
        "all_rr_2": all(variant.tester_inputs.get("InpRiskReward") == "2.00" for variant in variants),
        "all_portfolio_guard_enabled": all(variant.tester_inputs.get("InpPortfolioDailyGuardEnabled") == "true" for variant in variants),
        "no_session_filter": all(variant.tester_inputs.get("InpUseDirectionalSessionFilter") == "false" for variant in variants),
        "no_breakeven_partial_trailing": all(
            variant.tester_inputs.get("InpProfitProtectionEnabled") == "false"
            and variant.tester_inputs.get("InpPartialCloseEnabled") == "false"
            and variant.tester_inputs.get("InpSplitEntryEnabled") == "false"
            for variant in variants
        ),
    }


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_0": row["net"] > 0.0,
        "stress_net_gt_0": row["stress_030_net"] > 0.0,
        "recent3_net_ge_500": row["recent3_net"] >= 500.0,
        "recent3_trades_ge_50": row["recent3_signals"] >= 50,
        "pf_ge_1p25": (row["pf"] or 0.0) >= 1.25,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_baseline_r1_pullback": row["net"] > baseline["net"],
        "recent3_net_ge_700": row["recent3_net"] >= 700.0,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.0,
        "stress_net_gt_0": row["stress_030_net"] > 0.0,
        "dd_not_worse": row["max_closed_dd"] <= baseline["max_closed_dd"],
    }


def decide(combined_rows: list[dict[str, Any]]) -> tuple[str, str]:
    best = max(combined_rows, key=lambda row: (row["recent3_net"], row["net"]))
    if best["recent3_net"] >= V1_COMBINED_REFERENCE["recent3_net"] and best["net"] >= V1_COMBINED_REFERENCE["net"]:
        return (
            "R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_IMPROVES_V1",
            f"`{best['name']}` improved both full-window net and last-3-month net versus V1.",
        )
    if best["recent3_net"] >= 700.0 and best["net"] > 9050.59:
        return (
            "R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_USEFUL_BUT_BELOW_V1",
            f"`{best['name']}` preserved useful recent profit but did not beat the ungated V1 continuation reference.",
        )
    return (
        "R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_NO_IMPROVEMENT",
        "The exact-MT5 profit guards did not preserve enough of the V1 recent profit.",
    )


def strip(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in v1.strip_heavy(row).items()
        if key not in {"yearly_rows", "monthly_rows"}
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R2 Continuation Short V3 Profit Guard Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 research-only profit-guard pass over the strict-R2 V1 continuation short. No demo/live runtime, chart, preset, order, position, account, or broker state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"MT5 component evidence: `{payload['outputs']['mt5_components_md']}`",
        "",
        "## Reference",
        "",
        "| Book | Trades | WR% | PF | Net | Recent3 trades | Recent3 WR% | Recent3 net | Max DD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| `{V1_COMBINED_REFERENCE['name']}` | {V1_COMBINED_REFERENCE['signals']} | {V1_COMBINED_REFERENCE['wr']:.2f} | {V1_COMBINED_REFERENCE['pf']:.4f} | {V1_COMBINED_REFERENCE['net']:.2f} | {V1_COMBINED_REFERENCE['recent3_signals']} | {V1_COMBINED_REFERENCE['recent3_wr']:.2f} | {V1_COMBINED_REFERENCE['recent3_net']:.2f} | {V1_COMBINED_REFERENCE['max_closed_dd']:.2f} |",
        "",
        "## Standalone Full Window",
        "",
        "| Variant | Trades | Wins | Losses | WR% | W/L | PF | Net | Stress net | Recent3 trades | Recent3 WR% | Recent3 net | June net | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalone_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wins']} | {row['losses']} | {row['wr']:.2f} | "
            f"{row['wl'] or 0.0:.4f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_net']:.2f} | "
            f"{row['recent3_signals']} | {row['recent3_wr']:.2f} | {row['recent3_net']:.2f} | {row['june2026_net']:.2f} | {all(row['standalone_checks'].values())} |"
        )

    lines.extend(
        [
            "",
            "## Combined With Current R1 Plus Best R2 Pullback",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Stress net | Recent3 trades | Recent3 WR% | Recent3 net | June net | Max DD | Dropped | Pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["combined_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_net']:.2f} | {row['recent3_signals']} | "
            f"{row['recent3_wr']:.2f} | {row['recent3_net']:.2f} | {row['june2026_net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['dropped_signals']} | {all(row['combined_checks'].values())} |"
        )

    lines.extend(["", "## Guard Summary", ""])
    for item in payload["mt5_component_details"]:
        lines.append(f"### `{item['variant']}`")
        for reason, count in sorted(item["guard_counts"]["guard_reasons"].items()):
            if reason in {
                "pass",
                "portfolio_daily_loss_stop_reached",
                "portfolio_cooldown_after_loss_active",
                "portfolio_daily_trade_cap_reached",
                "max_open_positions_reached",
                "daily_trade_cap_reached",
            } or reason.startswith("regime_router_block"):
                lines.append(f"- `{reason}`: {count}")
        lines.append("")

    lines.extend(["## Failed Checks", ""])
    for row in payload["standalone_rows"]:
        failed = [key for key, value in row["standalone_checks"].items() if not value]
        lines.append(f"- `{row['name']}` standalone: {', '.join(failed) if failed else 'none'}")
    for row in payload["combined_rows"]:
        failed = [key for key, value in row["combined_checks"].items() if not value]
        lines.append(f"- `{row['name']}` combined: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R2 continuation short V3 profit guard.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    r2v1.require_file(PREREG)
    r2v1.require_file(r2v1.CURRENT_R1_BOOK)
    r2v1.require_file(v1.BEST_R2_PULLBACK_BOOK)

    variants = build_variants()
    checks = static_checks(variants)
    if not all(checks.values()):
        raise RuntimeError(f"Invalid static runner configuration: {checks}")

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

    r1_rows = read_ledger(r2v1.CURRENT_R1_BOOK)
    pullback_rows = read_ledger(v1.BEST_R2_PULLBACK_BOOK)
    baseline_rows = r1_rows + pullback_rows
    baseline = r2v1.evaluate_book("current_r1_plus_best_r2_pullback", baseline_rows, dedupe=True)

    standalone_rows: list[dict[str, Any]] = []
    combined_rows: list[dict[str, Any]] = []
    mt5_component_details: list[dict[str, Any]] = []

    for index, result in enumerate(mt5_payload["variants"], start=1):
        rows = v1.continuation_rows(result, source_priority=110 + index)
        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
        write_signal_csv(normalized_csv, rows)

        standalone = r2v1.evaluate_book(result["name"], rows)
        standalone["standalone_checks"] = standalone_checks(standalone)
        standalone_rows.append(standalone)

        combined = r2v1.evaluate_book(f"current_r1_best_r2_pullback_plus_{result['name']}", baseline_rows + rows, dedupe=True)
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
                "tester_input_sha256": r2v1.stable_hash(variants[index - 1].tester_inputs),
            }
        )

    status, interpretation = decide(combined_rows)
    r1.write_csv(standalone_csv, [strip(row) for row in standalone_rows])
    r1.write_csv(combined_csv, [strip(row) for row in combined_rows])

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
        "current_r1_book": rel(r2v1.CURRENT_R1_BOOK),
        "best_r2_pullback_book": rel(v1.BEST_R2_PULLBACK_BOOK),
        "baseline_row": strip(baseline),
        "standalone_rows": [strip(row) | {"standalone_checks": row["standalone_checks"]} for row in standalone_rows],
        "combined_rows": [strip(row) | {"combined_checks": row["combined_checks"]} for row in combined_rows],
        "mt5_component_details": mt5_component_details,
        "static_checks": checks,
        "interpretation": interpretation,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "combined": payload["combined_rows"], "report": str(report_md)}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
