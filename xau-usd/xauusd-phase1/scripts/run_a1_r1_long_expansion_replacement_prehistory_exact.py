from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_box_clean_requalification_exact as clean
import run_a1_r1_long_expansion_r3_reclass_exact as source
import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file, write_signal_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R1_LONG_EXPANSION_REPLACEMENT_PREHISTORY_EXACT_PREREG_2026_07_10.md"
ORIGINAL_PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_PREREG_2026_07_09.md"
PRIMARY_REPORT_JSON = REPORTS_DIR / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709.json"
PRIMARY_NORMALIZED = (
    REPORTS_DIR
    / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_r1_long_expansion_r3_reclass_strict_r1_NORMALIZED_TRADES.csv"
)
OUTPUT_STEM = "A1_XAU_R1_LONG_EXPANSION_REPLACEMENT_PREHISTORY_EXACT_20260710"
TAG = "OWNER_GOAL_R1_LONG_EXPANSION_REPLACEMENT_PREHISTORY_201601_202112"


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def evaluate_evidence(name: str, result: dict[str, Any], rows: list[dict[str, Any]], *, primary: bool) -> dict[str, Any]:
    shape = r1.flat_shape(name, rows)
    years = clean.year_rows(rows)
    episodes = clean.episode_rows(rows)
    drawdown = clean.mt5_drawdown(result["mt5_report_metrics"])
    execution = clean.execution_reconciliation(result, rows)
    forbidden = clean.forbidden_guard_counts(result)
    equity_dd = drawdown["equity_dd_maximal_usd"] or 0.0
    compact = r1.strip_heavy(shape)
    compact.update(
        {
            "window": name,
            "year_rows": years,
            "episodes": episodes,
            "pre_2026_net": round(
                sum(float(row["pnl_usd"]) for row in rows if row["entry_date"] < date(2026, 1, 1)), 2
            ),
            "mt5_drawdown": drawdown,
            "net_to_equity_dd": round(shape["net"] / equity_dd, 4) if equity_dd > 0.0 else None,
            "equity_to_closed_dd": (
                round(equity_dd / shape["max_closed_dd"], 4) if shape["max_closed_dd"] > 0.0 else None
            ),
            "execution_reconciliation": execution,
            "forbidden_guard_counts": forbidden,
        }
    )
    compact["alpha_checks"] = clean.alpha_checks(compact, primary=primary)
    compact["robustness_checks"] = {
        "top10_removed_net_gt_0": compact["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": compact["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30": compact["best_month_share_pct"] is not None
        and compact["best_month_share_pct"] <= 30.0,
    }
    compact["regime_integrity_checks"] = {
        "strict_r1_static_configuration": all(source.static_checks(source.build_variants()).values()),
        "zero_forbidden_guard_blocks": sum(forbidden.values()) == 0,
    }
    compact["execution_checks"] = {
        "successful_sends_match_mt5": execution["successful_sends_match_mt5"],
        "mt5_matches_normalized": execution["mt5_matches_normalized"],
        "all_failures_described": execution["all_failures_described"],
        "zero_order_send_failures": execution["order_send_fail_count"] == 0,
    }
    compact["drawdown_checks"] = {
        "balance_dd_relative_lte_20": drawdown["balance_dd_relative_pct"] is not None
        and drawdown["balance_dd_relative_pct"] <= 20.0,
        "equity_dd_relative_lte_20": drawdown["equity_dd_relative_pct"] is not None
        and drawdown["equity_dd_relative_pct"] <= 20.0,
        "net_to_equity_dd_ge_2": compact["net_to_equity_dd"] is not None
        and compact["net_to_equity_dd"] >= 2.0,
        "equity_to_closed_dd_lte_2": compact["equity_to_closed_dd"] is not None
        and compact["equity_to_closed_dd"] <= 2.0,
    }
    return compact


def decide(windows: list[dict[str, Any]]) -> tuple[str, str]:
    if not all(all(row["alpha_checks"].values()) and all(row["regime_integrity_checks"].values()) for row in windows):
        return (
            "R1_LONG_EXPANSION_REPLACEMENT_REJECT",
            "The frozen long-expansion replacement failed alpha or regime integrity in at least one exact window. It cannot become the R1 owner.",
        )
    full = all(
        all(row["robustness_checks"].values())
        and all(row["execution_checks"].values())
        and all(row["drawdown_checks"].values())
        for row in windows
    )
    if full:
        return (
            "R1_LONG_EXPANSION_REPLACEMENT_QUALIFIED",
            "The existing long-expansion source passed both exact alpha windows and every capital gate as the sole R1 owner.",
        )
    return (
        "R1_LONG_EXPANSION_REPLACEMENT_ALPHA_ONLY_RISK_REPAIR_REQUIRED",
        "The existing long-expansion source passed both alpha windows but failed concentration, execution, or MT5 equity-risk gates. Only a separately preregistered capital layer may proceed.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R1 Long-Expansion Replacement Prehistory Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        payload["interpretation"],
        "",
        "This source competes with the rejected box for R1 ownership; the two are not combined.",
        "",
        "| Window | Trades | WR% | W/L | PF | Stress PF | Net | Closed DD | Equity DD% | Equity DD USD | Net/equity DD | Best month% | Top10 rem | Top3 days rem |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["windows"]:
        dd = row["mt5_drawdown"]
        lines.append(
            f"| `{row['window']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['stress_030_pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {dd['equity_dd_relative_pct'] or 0.0:.2f} | "
            f"{dd['equity_dd_maximal_usd'] or 0.0:.2f} | {row['net_to_equity_dd'] or 0.0:.2f} | "
            f"{row['best_month_share_pct'] or 0.0:.2f} | {row['top10_removed_net']:.2f} | "
            f"{row['top3_days_removed_net']:.2f} |"
        )
    lines.extend(["", "## Failed Gates", ""])
    for row in payload["windows"]:
        lines.append(f"### `{row['window']}`")
        for key in ("alpha_checks", "robustness_checks", "regime_integrity_checks", "execution_checks", "drawdown_checks"):
            failed = clean.failed_checks(row[key])
            lines.append(f"- `{key}`: {', '.join(failed) if failed else 'none'}")
        lines.append("")
    lines.extend(["## Yearly Evidence", ""])
    for row in payload["windows"]:
        lines.extend([f"### `{row['window']}`", "", "| Year | Trades | WR% | W/L | PF | Net |", "| ---: | ---: | ---: | ---: | ---: | ---: |"])
        for year in row["year_rows"]:
            lines.append(
                f"| {year['year']} | {year['trades']} | {year['wr']:.2f} | {year['wl'] or 0.0:.4f} | "
                f"{year['pf'] or 0.0:.4f} | {year['net']:.2f} |"
            )
        lines.append("")
    lines.extend(["## Artifacts", ""])
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen prehistory exam for the existing strict-R1 long-expansion source.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=1800)
    args = parser.parse_args()

    for path in (PREREG, ORIGINAL_PREREG, PRIMARY_REPORT_JSON, PRIMARY_NORMALIZED):
        require_file(path)
    variants = source.build_variants()
    static = source.static_checks(variants)
    if not all(static.values()):
        raise RuntimeError(f"Frozen source static checks failed: {clean.failed_checks(static)}")

    primary_payload = json.loads(PRIMARY_REPORT_JSON.read_text(encoding="utf-8"))
    primary_rows = read_ledger(PRIMARY_NORMALIZED)
    primary = evaluate_evidence("primary_202207_202606", primary_payload["mt5_result"], primary_rows, primary=True)

    a1.VARIANTS = variants
    mt5_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.md"
    mt5_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.json"
    mt5_payload = a1.run_variants(
        from_date="2016.01.01",
        to_date="2021.12.31",
        tag=a1.safe_name(TAG),
        report_md=mt5_md,
        report_json=mt5_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )
    result = mt5_payload["variants"][0]
    prehistory_rows = source.mt5_rows(result)
    normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_NORMALIZED_TRADES.csv"
    write_signal_csv(normalized_csv, prehistory_rows)
    prehistory = evaluate_evidence("prehistory_201601_202112", result, prehistory_rows, primary=False)

    windows = [primary, prehistory]
    status, interpretation = decide(windows)
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "prehistory_mt5_md": rel(mt5_md),
        "prehistory_mt5_json": rel(mt5_json),
        "prehistory_normalized_trades_csv": rel(normalized_csv),
        "existing_primary_report_json": rel(PRIMARY_REPORT_JSON),
        "existing_primary_normalized_trades_csv": rel(PRIMARY_NORMALIZED),
    }
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "original_preregistration_sha256": sha256_file(ORIGINAL_PREREG),
        "static_checks": static,
        "windows": windows,
        "interpretation": interpretation,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "windows": [
                    {
                        "window": row["window"],
                        "trades": row["signals"],
                        "wr": row["wr"],
                        "pf": row["pf"],
                        "net": row["net"],
                        "equity_dd_relative_pct": row["mt5_drawdown"]["equity_dd_relative_pct"],
                        "failed_alpha": clean.failed_checks(row["alpha_checks"]),
                    }
                    for row in windows
                ],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
