from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_r2_continuation_short_v1_exact as v1
import run_a1_r2_pullback_rejection_short_v1_exact as r2v1
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts, period_stats


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_PREREG_2026_07_09.md"
OUTPUT_STEM = "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709"
TAG = "OWNER_GOAL_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_202207_202606"

APRIL_START = date(2026, 4, 1)
APRIL_END = date(2026, 4, 30)
MAY_START = date(2026, 5, 1)
MAY_END = date(2026, 5, 31)
JUNE_START = date(2026, 6, 1)
JUNE_END = date(2026, 6, 30)

V1_REFERENCE = {
    "combined_name": "current_r1_best_r2_pullback_plus_r2_impulse_retest_body45",
    "combined_net": 9750.48,
    "combined_recent3_net": 818.35,
}


def build_variants() -> list[a1.Variant]:
    base = {
        **v1.COMMON_CONT_INPUTS,
        "InpSignalMode": "19",
    }
    return [
        a1.Variant(
            name="r2_impulse_body45_atr45",
            label="Strict R2 impulse/retest body45 with M5 ATR floor 4.50, fixed 2R",
            run_id="BT_A1_XAU_R2_IMPULSE_BODY45_ATR45",
            tester_inputs={
                **base,
                "InpMinAtrAbsoluteForEntry": "4.50",
            },
        ),
        a1.Variant(
            name="r2_impulse_body45_atr50",
            label="Strict R2 impulse/retest body45 with M5 ATR floor 5.00, fixed 2R",
            run_id="BT_A1_XAU_R2_IMPULSE_BODY45_ATR50",
            tester_inputs={
                **base,
                "InpMinAtrAbsoluteForEntry": "5.00",
            },
        ),
        a1.Variant(
            name="r2_impulse_body45_atr45_daily_loss10",
            label="Strict R2 impulse/retest body45 with M5 ATR floor 4.50 and daily loss stop -$10",
            run_id="BT_A1_XAU_R2_IMPULSE_BODY45_ATR45_DAILY_LOSS10",
            tester_inputs={
                **base,
                "InpMinAtrAbsoluteForEntry": "4.50",
                "InpPortfolioDailyGuardEnabled": "true",
                "InpPortfolioDailyLossStopUsd": "10.00",
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
        "all_have_atr_floor": all(float(variant.tester_inputs.get("InpMinAtrAbsoluteForEntry", "0")) > 0.0 for variant in variants),
        "no_session_filter": all(variant.tester_inputs.get("InpUseDirectionalSessionFilter") == "false" for variant in variants),
        "no_breakeven_partial_trailing": all(
            variant.tester_inputs.get("InpProfitProtectionEnabled") == "false"
            and variant.tester_inputs.get("InpPartialCloseEnabled") == "false"
            and variant.tester_inputs.get("InpSplitEntryEnabled") == "false"
            for variant in variants
        ),
    }


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


def add_month_breakout(row: dict[str, Any]) -> dict[str, Any]:
    data = row["data"]
    for label, start, end in (
        ("april2026", APRIL_START, APRIL_END),
        ("may2026", MAY_START, MAY_END),
        ("june2026", JUNE_START, JUNE_END),
    ):
        stats = period_row(data, start, end)
        row[f"{label}_signals"] = stats["signals"]
        row[f"{label}_wr"] = stats["wr"]
        row[f"{label}_pf"] = stats["pf"]
        row[f"{label}_net"] = stats["net"]
    return row


def signal_reason_counts(result: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    signal_csv = Path(result["signal_csv"])
    if not signal_csv.exists():
        return counts
    with signal_csv.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            key = f"{row.get('stage', '')}:{row.get('reason', '')}"
            counts[key] = counts.get(key, 0) + 1
    return counts


def evaluate(name: str, rows: list[dict[str, Any]], *, dedupe: bool = False) -> dict[str, Any]:
    return add_month_breakout(r2v1.evaluate_book(name, rows, dedupe=dedupe))


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "trades_ge_40": row["signals"] >= 40,
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_2": (row["wl"] or 0.0) >= 2.0,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.0,
        "net_gt_0": row["net"] > 0.0,
        "stress_net_gt_0": row["stress_030_net"] > 0.0,
        "may_nonnegative_if_exposed": row["may2026_signals"] == 0 or row["may2026_net"] >= 0.0,
        "june_net_ge_400_if_exposed": row["june2026_signals"] == 0 or row["june2026_net"] >= 400.0,
        "recent3_net_ge_500": row["recent3_net"] >= 500.0,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_baseline_r1_pullback": row["net"] > baseline["net"],
        "wr_ge_48": row["wr"] >= 48.0,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.0,
        "stress_net_gt_0": row["stress_030_net"] > 0.0,
        "may_nonnegative": row["may2026_net"] >= 0.0,
        "recent3_net_ge_650": row["recent3_net"] >= 650.0,
        "dd_not_worse": row["max_closed_dd"] <= baseline["max_closed_dd"],
    }


def decide(standalone_rows: list[dict[str, Any]], combined_rows: list[dict[str, Any]]) -> tuple[str, str]:
    passing = [
        combined
        for standalone, combined in zip(standalone_rows, combined_rows, strict=True)
        if all(standalone["standalone_checks"].values()) and all(combined["combined_checks"].values())
    ]
    if passing:
        best = max(passing, key=lambda row: (row["recent3_net"], row["net"]))
        if best["net"] >= V1_REFERENCE["combined_net"] and best["recent3_net"] >= V1_REFERENCE["combined_recent3_net"]:
            return (
                "R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_IMPROVES_V1",
                f"`{best['name']}` passed the volatility-gate checks and improved V1 full-window plus recent-three-month net.",
            )
        return (
            "R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_QUALITY_REPAIR_BELOW_V1_NET",
            f"`{best['name']}` improved R2 quality and neutralized May-style damage, but it did not beat V1 full-window profit.",
        )
    if any(row["net"] > 0.0 and row["recent3_net"] >= 500.0 for row in standalone_rows):
        return (
            "R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_SHADOW_ONLY",
            "The volatility gate found useful quality-filtered R2 trades, but no variant cleared the combined quality/profit checks.",
        )
    return (
        "R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_NO_SURVIVOR",
        "The volatility gate did not preserve enough R2 profit to justify carrying it forward.",
    )


def strip(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in v1.strip_heavy(row).items()
        if key not in {"yearly_rows", "monthly_rows"}
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R2 Continuation Short V4 Volatility Gate Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 research-only volatility participation layer over the strict-R2 V1 continuation short. No demo/live runtime, chart, preset, order, position, account, or broker state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"MT5 component evidence: `{payload['outputs']['mt5_components_md']}`",
        "",
        "## Reference",
        "",
        "| Book | Full net | Recent3 net | Note |",
        "| --- | ---: | ---: | --- |",
        f"| `{V1_REFERENCE['combined_name']}` | {V1_REFERENCE['combined_net']:.2f} | {V1_REFERENCE['combined_recent3_net']:.2f} | V1 profit leader |",
        "",
        "## Standalone V4",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress net | Apr net | May net | Jun trades | Jun WR% | Jun net | Recent3 net | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalone_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_net']:.2f} | "
            f"{row['april2026_net']:.2f} | {row['may2026_net']:.2f} | {row['june2026_signals']} | "
            f"{row['june2026_wr']:.2f} | {row['june2026_net']:.2f} | {row['recent3_net']:.2f} | "
            f"{all(row['standalone_checks'].values())} |"
        )

    lines.extend(
        [
            "",
            "## Combined With Current R1 Plus Best R2 Pullback",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Stress net | Apr net | May net | Jun trades | Jun WR% | Jun net | Recent3 net | Max DD | Dropped | Pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["combined_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_net']:.2f} | "
            f"{row['april2026_net']:.2f} | {row['may2026_net']:.2f} | {row['june2026_signals']} | "
            f"{row['june2026_wr']:.2f} | {row['june2026_net']:.2f} | {row['recent3_net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {row['dropped_signals']} | {all(row['combined_checks'].values())} |"
        )

    lines.extend(["", "## Guard Summary", ""])
    for item in payload["mt5_component_details"]:
        lines.append(f"### `{item['variant']}`")
        atr_blocks = item["signal_reason_counts"].get("NO_SIGNAL:atr_below_entry_floor", 0)
        if atr_blocks:
            lines.append(f"- `NO_SIGNAL:atr_below_entry_floor`: {atr_blocks}")
        for reason, count in sorted(item["guard_counts"]["guard_reasons"].items()):
            if reason in {
                "pass",
                "atr_below_entry_floor",
                "portfolio_daily_loss_stop_reached",
                "max_open_positions_reached",
                "daily_trade_cap_reached",
                "stop_ceiling_exceeded",
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
    parser = argparse.ArgumentParser(description="Run exact-MT5 R2 continuation short V4 volatility gate.")
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
        rows = v1.continuation_rows(result, source_priority=120 + index)
        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
        write_signal_csv(normalized_csv, rows)

        standalone = evaluate(result["name"], rows)
        standalone["standalone_checks"] = standalone_checks(standalone)
        standalone_rows.append(standalone)

        combined = evaluate(f"current_r1_best_r2_pullback_plus_{result['name']}", baseline_rows + rows, dedupe=True)
        combined["combined_checks"] = combined_checks(combined, baseline)
        combined_rows.append(combined)
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_KEPT.csv", combined["data"])
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_DROPPED.csv", combined["dropped_data"])

        mt5_component_details.append(
            {
                "variant": result["name"],
                "mt5_result": result,
                "guard_counts": guard_counts(result),
                "signal_reason_counts": signal_reason_counts(result),
                "normalized_trades": len(rows),
                "tester_input_sha256": r2v1.stable_hash(variants[index - 1].tester_inputs),
            }
        )

    status, interpretation = decide(standalone_rows, combined_rows)
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
