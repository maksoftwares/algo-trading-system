from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as v1
import run_a1_r4_chop_failed_break_v1_exact as r4
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts, period_stats


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_PREREG_2026_07_09.md"
OUTPUT_STEM = "A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709"
TAG = "OWNER_GOAL_R3_COMPRESSION_LONG_V1_EXACT_202207_202606"
SOURCE_ID = "r3_compression_long_v1_broad_box3_atr60_range125_body035"
RECENT3_START = date(2026, 4, 1)
RECENT3_END = date(2026, 6, 30)


R3_INPUTS = {
    "InpSignalMode": "7",
    "InpDirectionMode": "1",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
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


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name=SOURCE_ID,
            label="R3 D1-compression/H4-expansion long-only, broad box3 atr60 range125 body035, fixed 2R",
            run_id="BT_A1_XAU_R3_COMPRESSION_LONG_V1_BROAD",
            tester_inputs=R3_INPUTS,
        )
    ]


def mt5_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = v1.mt5_rows(result, source_priority=80)
    for row in rows:
        row["component"] = SOURCE_ID
        row["source_id"] = SOURCE_ID
        row["upstream_source_id"] = SOURCE_ID
        row["upstream_component"] = result["name"]
        row["family_group"] = "xau_r3_compression_long"
        row["cell_id"] = "r3_compression_long_v1"
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


def month_stats(rows: list[dict[str, Any]], year: int, month: int) -> dict[str, Any]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, month + 1, 1)
        end = date.fromordinal(end.toordinal() - 1)
    return period_net(rows, start, end)


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
        "month_2026_04": month_stats(book["data"], 2026, 4),
        "month_2026_05": month_stats(book["data"], 2026, 5),
        "month_2026_06": month_stats(book["data"], 2026, 6),
    }


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "trades_ge_150": row["signals"] >= 150,
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_2": (row["wl"] or 0.0) >= 2.0,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.0,
        "stress_pf_ge_1p50": (row["stress_030_pf"] or 0.0) >= 1.50,
        "stress_wl_ge_1p90": (row["stress_030_wl"] or 0.0) >= 1.90,
        "net_gt_0": row["net"] > 0.0,
        "net_2023_2024_ge_0": row["net_2023_2024"] >= 0.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_current_r1": row["net"] > baseline["net"],
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_or_stress_wl_ok": (row["wl"] or 0.0) >= 2.00 or (row["stress_030_wl"] or 0.0) >= 1.90,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.00,
        "dd_not_worse_25pct": row["max_closed_dd"] <= baseline["max_closed_dd"] * 1.25,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def decide(standalone: dict[str, Any], combined: dict[str, Any]) -> tuple[str, str]:
    if all(standalone["checks"].values()) and all(combined["checks"].values()):
        return (
            "R3_COMPRESSION_LONG_V1_REVIEW_CANDIDATE",
            "The R3 compression long specialist passed standalone and combined gates. It is still research-only and needs reviewer approval.",
        )
    if all(standalone["checks"].values()):
        return (
            "R3_COMPRESSION_LONG_V1_STANDALONE_SHADOW",
            "The R3 compression long specialist passed standalone gates but did not clear combined promotion gates.",
        )
    return (
        "R3_COMPRESSION_LONG_V1_NO_SURVIVOR",
        "The R3 compression long specialist did not pass the standalone quality gate.",
    )


def render(payload: dict[str, Any]) -> str:
    standalone = payload["standalone"]
    combined = payload["combined"]
    baseline = payload["baseline"]
    lines = [
        "# A1 XAU R3 Compression Long V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 run using the existing D1-compression/H4-expansion signal. Research-only.",
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

    lines.extend(["", "## Guard Notes", ""])
    for reason, count in sorted(payload["guard_counts"]["guard_reasons"].items()):
        if reason in {"direction_mode_block", "max_open_positions_reached", "estimated_cost_r_too_high", "stop_ceiling_exceeded", "pass"}:
            lines.append(f"- `{reason}`: {count}")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R3 compression long V1.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
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
    standalone = enriched_book(result["name"], candidate_rows)
    baseline = enriched_book("current_r1_box_plus_v2_pullback", r1_rows)
    combined = enriched_book(f"current_r1_plus_{result['name']}", r1_rows + candidate_rows, dedupe=True)

    standalone["checks"] = standalone_checks(standalone)
    combined["checks"] = combined_checks(combined, baseline)
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
