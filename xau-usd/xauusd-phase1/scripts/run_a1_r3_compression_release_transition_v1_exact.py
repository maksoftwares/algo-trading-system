from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as metrics
import run_a1_xau_m5_momentum_backtest_variants as mt5
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R3_COMPRESSION_RELEASE_TRANSITION_V1_EXACT_PREREG_2026_07_10.md"
OUTPUT_STEM = "A1_XAU_R3_COMPRESSION_RELEASE_TRANSITION_V1_EXACT_20260710"
TAG = "OWNER_GOAL_R3_COMPRESSION_RELEASE_TRANSITION_V1_EXACT_202207_202606"
SOURCE_ID = "r3_compression_release_transition_v1_strict_symmetric"

EXPECTED_SIGNAL_REASONS = {
    "D1_COMPRESSION_H4_EXPANSION_LONG",
    "D1_COMPRESSION_H4_EXPANSION_SHORT",
}

R3_INPUTS = {
    "InpSignalMode": "7",
    "InpDirectionMode": "0",
    "InpRegimeRouterMode": "5",
    "InpD1CompressionAtrPercentileMax": "30.00",
    "InpD1CompressionBoxDays": "5",
    "InpD1CompressionRangeMedianMax": "1.00",
    "InpD1CompressionH4MinBodyFraction": "0.50",
    "InpRegimeShockH1RangeAtrMultiple": "3.00",
    "InpRegimeShockD1AtrPercentileMin": "95.00",
    "InpRegimeShockD1AtrLookback": "60",
    "InpRiskReward": "2.00",
    "InpStopCeilingPoints": "0",
    "InpStopCapPoints": "0",
    "InpMaxEstimatedCostR": "0.15",
    "InpUseRiskNormalizedLots": "true",
    "InpRiskAmountUsd": "100.00",
    "InpMaxRiskLots": "0.05",
    "InpRejectRiskOvershootEnabled": "true",
    "InpMaxRiskOvershootPct": "0.00",
    "InpOnePositionPerMagic": "true",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpMaxTradesPerDay": "6",
    "InpCooldownMinutes": "0",
    "InpBlockedEntryHoursCsv": "",
    "InpBlockedEntryDayHoursCsv": "",
    "InpBlockedLongEntryHoursCsv": "",
    "InpBlockedShortEntryHoursCsv": "",
    "InpUseDirectionalSessionFilter": "false",
    "InpMinAtrAbsoluteForEntry": "0.00",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpH4D1SupportiveStateGuardEnabled": "false",
    "InpD1SupportStateGateMode": "0",
    "InpD1StructuralDownGateEnabled": "false",
    "InpPortfolioDailyGuardEnabled": "false",
    "InpH4D1WeeklyLossGovernorEnabled": "false",
    "InpH4D1PrevMonthHealthGateEnabled": "false",
    "InpH4D1NegativeStackGuardEnabled": "false",
    "InpH4D1ThirdEntryQualityGateEnabled": "false",
    "InpProfitProtectionEnabled": "false",
    "InpPartialCloseEnabled": "false",
    "InpSplitEntryEnabled": "false",
    "InpEarlyAdverseExitEnabled": "false",
}


def require_ready() -> None:
    for path in (EA_SOURCE, PREREG):
        if not path.exists():
            raise FileNotFoundError(path)
    source = EA_SOURCE.read_text(encoding="utf-8")
    required_tokens = (
        "REGIME_ROUTER_R3_COMPRESSION_RELEASE_SHOCK_BLOCK = 5",
        "InpRejectRiskOvershootEnabled",
        "RiskOvershootAllowed",
        'return "r3_compression_release_shock_block"',
    )
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            "R3 exact infrastructure is not ready; missing EA tokens: " + ", ".join(missing)
        )


def build_variants() -> list[mt5.Variant]:
    return [
        mt5.Variant(
            name=SOURCE_ID,
            label=(
                "R3 strict D1 compression setup / symmetric H4 release, "
                "shock-blocked, one position, fixed $100 stop risk and 2R"
            ),
            run_id="BT_A1_XAU_R3_COMPRESSION_RELEASE_TRANSITION_V1",
            tester_inputs=R3_INPUTS,
        )
    ]


def normalized_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = metrics.mt5_rows(result, source_priority=90)
    for row in rows:
        row.update(
            {
                "component": SOURCE_ID,
                "source_id": SOURCE_ID,
                "upstream_source_id": SOURCE_ID,
                "upstream_component": result["name"],
                "family_group": "xau_r3_compression_release_transition",
                "cell_id": "r3_compression_release_transition_v1",
            }
        )
    return rows


def parse_money_percent(value: object) -> tuple[float | None, float | None]:
    text = str(value or "").strip()
    match = re.search(r"([-+]?\d[\d\s,]*\.?\d*)\s*\(([-+]?\d+(?:\.\d+)?)%\)", text)
    if not match:
        return None, None
    money = float(match.group(1).replace(" ", "").replace(",", ""))
    return money, float(match.group(2))


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def signal_audit(result: dict[str, Any]) -> dict[str, Any]:
    rows = read_tsv(Path(result["signal_csv"]))
    reasons = Counter(
        row.get("reason", "")
        for row in rows
        if row.get("stage", "") == "WOULD_SIGNAL"
    )
    unexpected = sorted(reason for reason in reasons if reason not in EXPECTED_SIGNAL_REASONS)
    return {
        "would_signal_rows": sum(reasons.values()),
        "reason_counts": dict(sorted(reasons.items())),
        "unexpected_reasons": unexpected,
    }


def direction_shape(rows: list[dict[str, Any]], direction: str) -> dict[str, Any]:
    selected = [row for row in rows if str(row.get("direction", "")).upper() == direction]
    return metrics.strip_heavy(metrics.flat_shape(f"{SOURCE_ID}_{direction.lower()}", selected))


def standalone_checks(
    book: dict[str, Any],
    long_shape: dict[str, Any],
    short_shape: dict[str, Any],
    equity_dd_pct: float | None,
    orders: dict[str, Any],
    signals: dict[str, Any],
) -> dict[str, bool]:
    actions = orders["actions"]
    reasons = orders["guard_reasons"]
    forbidden_calendar_blocks = sum(
        reasons.get(reason, 0)
        for reason in (
            "blocked_entry_hour",
            "blocked_entry_day_hour",
            "direction_blocked_entry_hour",
            "directional_session_filter_block",
            "h4_d1_previous_month_health_gate",
            "h4_d1_weekly_loss_governor",
        )
    )
    incompatible_router_blocks = reasons.get(
        "regime_router_block_r3_compression_release_shock_block_incompatible_signal_mode", 0
    )
    return {
        "trades_ge_100": book["signals"] >= 100,
        "wr_ge_50": book["wr"] >= 50.0,
        "wl_ge_2": (book["wl"] or 0.0) >= 2.0,
        "pf_ge_2": (book["pf"] or 0.0) >= 2.0,
        "stress_pf_ge_1p75": (book["stress_030_pf"] or 0.0) >= 1.75,
        "stress_net_gt_0": book["stress_030_net"] > 0.0,
        "positive_year_buckets_ge_3": book["positive_year_buckets"] >= 3,
        "long_trades_ge_20": long_shape["signals"] >= 20,
        "long_stress_net_gt_0": long_shape["stress_030_net"] > 0.0,
        "short_trades_ge_20": short_shape["signals"] >= 20,
        "short_stress_net_gt_0": short_shape["stress_030_net"] > 0.0,
        "top10_removed_net_gt_0": book["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": book["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30pct": (
            book["best_month_share_pct"] is not None
            and book["best_month_share_pct"] <= 30.0
        ),
        "max_equity_dd_lte_10pct": equity_dd_pct is not None and equity_dd_pct <= 10.0,
        "order_send_failures_zero": actions.get("ORDER_SEND_FAIL", 0) == 0,
        "calendar_performance_mask_blocks_zero": forbidden_calendar_blocks == 0,
        "incompatible_router_blocks_zero": incompatible_router_blocks == 0,
        "signal_reasons_exact": not signals["unexpected_reasons"],
    }


def render(payload: dict[str, Any]) -> str:
    book = payload["standalone"]
    long_shape = payload["direction"]["LONG"]
    short_shape = payload["direction"]["SHORT"]
    failed = [name for name, passed in payload["checks"].items() if not passed]
    lines = [
        "# A1 XAU R3 Compression-Release Transition V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "One preregistered symmetric compression-setup/H4-release candidate. Research-only.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Standalone Result",
        "",
        "| Trades | WR% | W/L | PF | Stress PF | Net | Stress net | Best month% | Closed DD | Equity DD |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {book['signals']} | {book['wr']:.2f} | {book['wl'] or 0.0:.4f} | "
            f"{book['pf'] or 0.0:.4f} | {book['stress_030_pf'] or 0.0:.4f} | "
            f"{book['net']:.2f} | {book['stress_030_net']:.2f} | "
            f"{book['best_month_share_pct'] or 0.0:.2f} | {book['max_closed_dd']:.2f} | "
            f"{payload['equity_dd']['usd'] or 0.0:.2f} ({payload['equity_dd']['pct'] or 0.0:.2f}%) |"
        ),
        "",
        "## Direction Proof",
        "",
        "| Direction | Trades | WR% | W/L | PF | Stress PF | Net | Stress net |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for direction, shape in (("LONG", long_shape), ("SHORT", short_shape)):
        lines.append(
            f"| {direction} | {shape['signals']} | {shape['wr']:.2f} | {shape['wl'] or 0.0:.4f} | "
            f"{shape['pf'] or 0.0:.4f} | {shape['stress_030_pf'] or 0.0:.4f} | "
            f"{shape['net']:.2f} | {shape['stress_030_net']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Gate Result",
            "",
            f"Failed checks: `{', '.join(failed) if failed else 'none'}`",
            "",
            "## Signal and Guard Reconciliation",
            "",
            f"- Exact signal reasons: `{json.dumps(payload['signal_audit']['reason_counts'], sort_keys=True)}`",
            f"- Order actions: `{json.dumps(payload['orders']['actions'], sort_keys=True)}`",
            f"- Guard reasons: `{json.dumps(payload['orders']['guard_reasons'], sort_keys=True)}`",
            "",
            "## Artifacts",
            "",
        ]
    )
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the preregistered R3 compression-release transition V1 exact test."
    )
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_ready()
    variants = build_variants()
    mt5.VARIANTS = variants

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{SOURCE_ID}_NORMALIZED_TRADES.csv"
    long_csv = REPORTS_DIR / f"{OUTPUT_STEM}_LONG.csv"
    short_csv = REPORTS_DIR / f"{OUTPUT_STEM}_SHORT.csv"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.json"

    mt5_payload = mt5.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=mt5.safe_name(TAG),
        report_md=mt5_report_md,
        report_json=mt5_report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="10000",
        currency="USD",
    )
    result = mt5_payload["variants"][0]
    rows = normalized_rows(result)
    book = metrics.evaluate_book(SOURCE_ID, rows)
    long_shape = direction_shape(book["data"], "LONG")
    short_shape = direction_shape(book["data"], "SHORT")
    orders = guard_counts(result)
    signals = signal_audit(result)
    equity_dd_usd, equity_dd_pct = parse_money_percent(
        result.get("mt5_report_metrics", {}).get("Equity Drawdown Maximal")
    )
    checks = standalone_checks(
        book,
        long_shape,
        short_shape,
        equity_dd_pct,
        orders,
        signals,
    )
    status = (
        "R3_COMPRESSION_RELEASE_TRANSITION_V1_STANDALONE_SHADOW"
        if all(checks.values())
        else "R3_COMPRESSION_RELEASE_TRANSITION_V1_NO_SURVIVOR"
    )

    write_signal_csv(normalized_csv, book["data"])
    write_signal_csv(long_csv, [row for row in book["data"] if row["direction"] == "LONG"])
    write_signal_csv(short_csv, [row for row in book["data"] if row["direction"] == "SHORT"])

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "normalized_trades_csv": rel(normalized_csv),
        "long_csv": rel(long_csv),
        "short_csv": rel(short_csv),
        "mt5_report_md": rel(mt5_report_md),
        "mt5_report_json": rel(mt5_report_json),
    }
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "source_id": SOURCE_ID,
        "frozen_inputs": R3_INPUTS,
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "standalone": metrics.strip_heavy(book),
        "direction": {"LONG": long_shape, "SHORT": short_shape},
        "equity_dd": {"raw": result.get("mt5_report_metrics", {}).get("Equity Drawdown Maximal"), "usd": equity_dd_usd, "pct": equity_dd_pct},
        "orders": orders,
        "signal_audit": signals,
        "checks": checks,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "checks": checks, "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
