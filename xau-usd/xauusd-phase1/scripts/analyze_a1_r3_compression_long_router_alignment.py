from __future__ import annotations

import argparse
import bisect
import csv
import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_r3_compression_long_v1_exact as r3
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, parse_dt, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_PREREG_2026_07_09.md"
OUTPUT_STEM = "A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709"
TAG = "OWNER_GOAL_R3_ROUTER_ALIGNMENT_AUDIT_202207_202606"

R3_TRADES = REPORTS_DIR / "A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_r3_compression_long_v1_broad_box3_atr60_range125_body035_NORMALIZED_TRADES.csv"
CURRENT_R1_R2 = REPORTS_DIR / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"

RECENT3_START = date(2026, 4, 1)
RECENT3_END = date(2026, 6, 30)
REGIME_ORDER = ["shock", "uptrend", "downtrend", "compression", "chop", "unknown", "no_snapshot"]


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def build_snapshot_variant() -> a1.Variant:
    return a1.Variant(
        name="r3_alignment_full_window_regime_snapshot_m5",
        label="Full-window EA-router regime snapshot for R3 trade attribution",
        run_id="BT_A1_XAU_R3_ALIGNMENT_REGIME_SNAPSHOT_M5",
        tester_inputs={
            **ROUTER_INPUTS,
            "InpSignalMode": "0",
            "InpRegimeRouterMode": "0",
            "InpRegimeSnapshotLogEnabled": "true",
            "InpAllowDemoTrading": "false",
            "InpMinAtrAbsoluteForEntry": "0.00",
        },
    )


def run_snapshot(timeout_seconds: int) -> dict[str, Any]:
    a1.VARIANTS = [build_snapshot_variant()]
    return a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=REPORTS_DIR / f"{OUTPUT_STEM}_MT5.md",
        report_json=REPORTS_DIR / f"{OUTPUT_STEM}_MT5.json",
        variant_timeout_seconds=timeout_seconds,
        deposit="1000",
        currency="USD",
    )


def read_snapshots(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for ordinal, row in enumerate(csv.DictReader(handle, delimiter="\t"), start=2):
            if row.get("stage") != "REGIME_SNAPSHOT":
                continue
            timestamp = parse_dt(row["timestamp_broker"])
            rows.append(
                {
                    "timestamp_broker": timestamp,
                    "date": timestamp.date(),
                    "regime": str(row.get("reason") or "unknown").strip().lower(),
                    "spread_points": int(float(row.get("spread_points") or 0.0)),
                    "atr": float(row.get("atr") or 0.0),
                    "body_fraction": float(row.get("body_fraction") or 0.0),
                    "close_location": float(row.get("close_location") or 0.0),
                    "source_row": ordinal,
                }
            )
    return rows


def tag_rows_with_router_state(rows: list[dict[str, Any]], snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(snapshots, key=lambda item: item["timestamp_broker"])
    times = [item["timestamp_broker"] for item in ordered]
    tagged: list[dict[str, Any]] = []
    max_lag = timedelta(minutes=10)
    for row in rows:
        entry_time = row["entry_time"]
        index = bisect.bisect_right(times, entry_time) - 1
        if index < 0:
            regime = "no_snapshot"
            snapshot_time = ""
            lag_seconds = None
        else:
            snapshot = ordered[index]
            lag = entry_time - snapshot["timestamp_broker"]
            if lag < timedelta(0) or lag > max_lag:
                regime = "no_snapshot"
                snapshot_time = snapshot["timestamp_broker"]
                lag_seconds = lag.total_seconds()
            else:
                regime = snapshot["regime"]
                snapshot_time = snapshot["timestamp_broker"]
                lag_seconds = lag.total_seconds()
        tagged.append(
            {
                **row,
                "ea_router_regime": regime,
                "router_snapshot_time": snapshot_time,
                "router_snapshot_lag_seconds": lag_seconds,
            }
        )
    return tagged


def period_stats(rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    selected = [row for row in rows if start <= row["exit_date"] <= end]
    return r3.period_net(selected, start, end)


def add_audit_fields(book: dict[str, Any]) -> dict[str, Any]:
    y2023_2024 = r3.period_net(book["data"], date(2023, 1, 1), date(2024, 12, 31))
    recent3 = r3.period_net(book["data"], RECENT3_START, RECENT3_END)
    return {
        **book,
        "recent3_signals": recent3["signals"],
        "recent3_net": recent3["net"],
        "net_2023_2024": y2023_2024["net"],
    }


def evaluate(name: str, rows: list[dict[str, Any]], *, dedupe: bool = False) -> dict[str, Any]:
    return add_audit_fields(r1.evaluate_book(name, rows, dedupe=dedupe))


def empty_metric(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "signals": 0,
        "wins": 0,
        "losses": 0,
        "wr": 0.0,
        "wl": 0.0,
        "pf": 0.0,
        "net": 0.0,
        "stress_030_wl": 0.0,
        "stress_030_pf": 0.0,
        "stress_030_net": 0.0,
        "active_weekday_pct": 0.0,
        "max_closed_dd": 0.0,
        "positive_week_pct": 0.0,
        "worst_week": 0.0,
        "q2_signals": 0,
        "q2_net": 0.0,
        "top10_removed_net": 0.0,
        "top3_days_removed_net": 0.0,
        "best_month_share_pct": 0.0,
        "positive_year_buckets": 0,
        "closing_months": 0,
        "positive_months": 0,
        "negative_months": 0,
        "flat_months": 0,
        "positive_month_pct": 0.0,
        "worst_month": "",
        "worst_month_net": 0.0,
        "best_month": "",
        "best_month_net": 0.0,
        "dropped_signals": 0,
        "recent3_signals": 0,
        "recent3_net": 0.0,
        "net_2023_2024": 0.0,
    }


def strip_book(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in r1.strip_heavy(row).items()
        if key not in {"yearly_rows", "monthly_rows"}
    }


def regime_rows(tagged: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for regime in REGIME_ORDER:
        rows = [row for row in tagged if row.get("ea_router_regime") == regime]
        book = evaluate(f"r3_router_{regime}", rows) if rows else empty_metric(f"r3_router_{regime}")
        output.append({"ea_router_regime": regime, **strip_book(book)})
    return output


def monthly_rows(name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_month: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        month = f"{row['exit_date'].year:04d}-{row['exit_date'].month:02d}"
        by_month.setdefault(month, []).append(row)
    output: list[dict[str, Any]] = []
    for month, month_rows_ in sorted(by_month.items()):
        book = evaluate(f"{name}_{month}", month_rows_)
        output.append({"book": name, "month": month, **strip_book(book)})
    return output


def yearly_rows(name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_year: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_year.setdefault(row["exit_date"].year, []).append(row)
    output: list[dict[str, Any]] = []
    for year, year_rows_ in sorted(by_year.items()):
        book = evaluate(f"{name}_{year}", year_rows_)
        output.append({"book": name, "year": year, **strip_book(book)})
    return output


def full_r3_strong(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "trades_ge_150": row["signals"] >= 150,
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_2": (row["wl"] or 0.0) >= 2.0,
        "pf_ge_2p50": (row["pf"] or 0.0) >= 2.50,
        "stress_pf_ge_2": (row["stress_030_pf"] or 0.0) >= 2.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def true_compression_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "compression_trades_ge_100": row["signals"] >= 100,
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_2": (row["wl"] or 0.0) >= 2.0,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.0,
        "stress_pf_ge_1p50": (row["stress_030_pf"] or 0.0) >= 1.50,
        "net_gt_0": row["net"] > 0.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
        "net_2023_2024_ge_0": row["net_2023_2024"] >= 0.0,
        "max_dd_lte_baseline": row["max_closed_dd"] <= baseline["max_closed_dd"],
    }


def freeze_checks(full_r3: dict[str, Any], combined_all: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "r3_top10_removed_net_lte_0": full_r3["top10_removed_net"] <= 0.0,
        "r3_top3_days_removed_net_lte_0": full_r3["top3_days_removed_net"] <= 0.0,
        "r3_2023_2024_net_lt_0": full_r3["net_2023_2024"] < 0.0,
        "combined_dd_gt_125pct_baseline": combined_all["max_closed_dd"] > baseline["max_closed_dd"] * 1.25,
        "combined_wr_lt_50": combined_all["wr"] < 50.0,
        "combined_pf_lt_2": (combined_all["pf"] or 0.0) < 2.0,
    }


def portfolio_checks(combined_all: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_baseline": combined_all["net"] > baseline["net"],
        "stress_net_gt_baseline": combined_all["stress_030_net"] > baseline["stress_030_net"],
        "wr_ge_50": combined_all["wr"] >= 50.0,
        "wl_ge_2": (combined_all["wl"] or 0.0) >= 2.0,
        "pf_ge_2": (combined_all["pf"] or 0.0) >= 2.0,
        "max_dd_lte_115pct_baseline": combined_all["max_closed_dd"] <= baseline["max_closed_dd"] * 1.15,
        "recent3_net_ge_baseline_minus_100": combined_all["recent3_net"] >= baseline["recent3_net"] - 100.0,
        "top10_removed_net_gt_0": combined_all["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": combined_all["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_35": combined_all["best_month_share_pct"] is not None and combined_all["best_month_share_pct"] <= 35.0,
    }


def decide(payload: dict[str, Any]) -> tuple[str, str]:
    if any(payload["freeze_checks"].values()):
        return (
            "R3_COMPRESSION_LONG_V1_FREEZE",
            "R3 failed at least one reviewer-defined freeze rule. Do not carry it forward without reviewer approval.",
        )
    if all(payload["true_compression_checks"].values()) and all(payload["portfolio_checks"].values()):
        return (
            "R3_PORTFOLIO_REVIEW_CANDIDATE",
            "R3 is router-compression aligned and the combined R1+R2+R3 book passes the portfolio carry-forward gate.",
        )
    full_strong = all(payload["full_r3_strong_checks"].values())
    compression = payload["books"]["r3_compression_only"]
    noncompression = payload["books"]["r3_noncompression_only"]
    if full_strong and (compression["signals"] < 100 or noncompression["net"] > compression["net"]):
        return (
            "R3_MIXED_REGIME_LONG_EXPANSION_SHADOW",
            "R3 remains strong as a full source, but the EA-router attribution does not prove it is a clean compression specialist.",
        )
    if all(payload["true_compression_checks"].values()):
        return (
            "R3_TRUE_COMPRESSION_SPECIALIST_SHADOW",
            "R3 passes compression-specialist diagnostics but does not yet pass the combined portfolio carry-forward gate.",
        )
    return (
        "R3_ROUTER_ALIGNMENT_AUDIT_NO_PROMOTION",
        "R3 did not satisfy the true-compression, portfolio, or mixed-regime carry-forward definitions.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R3 Compression Long V1 Router-Alignment Audit",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 EA-router snapshot attribution plus recomposition of existing exact-MT5 R3 and current R1+R2 ledgers. Research-only.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Snapshot signal CSV SHA256: `{payload['snapshot_signal_sha256']}`",
        "",
        "## Router Attribution",
        "",
        "| EA router regime | Trades | WR% | W/L | PF | Net | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | 2023-2024 net |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["regime_rows"]:
        if row["signals"] == 0:
            continue
        lines.append(
            f"| `{row['ea_router_regime']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_pf'] or 0.0:.4f} | "
            f"{row['recent3_signals']} | {row['recent3_net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | {row['net_2023_2024']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Portfolio Books",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Stress net | Recent3 trades | Recent3 net | Max DD | Best month share% | Top10 rem | Top3 days rem |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for key in ("current_r1_r2_baseline", "r3_all", "r3_compression_only", "r3_noncompression_only", "current_r1_r2_plus_r3_all", "current_r1_r2_plus_r3_compression_only", "current_r1_r2_plus_r3_noncompression_only"):
        row = payload["books"][key]
        lines.append(
            f"| `{key}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_net']:.2f} | "
            f"{row['recent3_signals']} | {row['recent3_net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['best_month_share_pct'] or 0.0:.2f} | {row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} |"
        )

    lines.extend(["", "## Checks", ""])
    for label in ("full_r3_strong_checks", "true_compression_checks", "portfolio_checks", "freeze_checks"):
        lines.append(f"### `{label}`")
        for key, value in payload[label].items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")

    lines.extend(
        [
            "## Snapshot Coverage",
            "",
            f"- Snapshot rows: `{payload['snapshot_summary']['snapshot_rows']}`",
            f"- Tagged R3 rows: `{payload['snapshot_summary']['tagged_r3_rows']}`",
            f"- Missing/no-snapshot R3 rows: `{payload['snapshot_summary']['no_snapshot_r3_rows']}`",
            f"- Max snapshot lag seconds: `{payload['snapshot_summary']['max_snapshot_lag_seconds']}`",
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "## Artifacts",
            "",
        ]
    )
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit R3 compression long router alignment.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    require_file(R3_TRADES)
    require_file(CURRENT_R1_R2)

    mt5_payload = run_snapshot(args.variant_timeout_seconds)
    snapshot_result = mt5_payload["variants"][0]
    snapshots = read_snapshots(Path(snapshot_result["signal_csv"]))
    r3_rows = read_ledger(R3_TRADES)
    tagged_r3 = tag_rows_with_router_state(r3_rows, snapshots)

    compression_r3 = [row for row in tagged_r3 if row["ea_router_regime"] == "compression"]
    noncompression_r3 = [row for row in tagged_r3 if row["ea_router_regime"] != "compression"]
    baseline_rows = read_ledger(CURRENT_R1_R2)

    books = {
        "current_r1_r2_baseline": evaluate("current_r1_r2_baseline", baseline_rows),
        "r3_all": evaluate("r3_all", tagged_r3),
        "r3_compression_only": evaluate("r3_compression_only", compression_r3) if compression_r3 else empty_metric("r3_compression_only"),
        "r3_noncompression_only": evaluate("r3_noncompression_only", noncompression_r3) if noncompression_r3 else empty_metric("r3_noncompression_only"),
    }
    books["current_r1_r2_plus_r3_all"] = evaluate("current_r1_r2_plus_r3_all", baseline_rows + tagged_r3, dedupe=True)
    books["current_r1_r2_plus_r3_compression_only"] = evaluate(
        "current_r1_r2_plus_r3_compression_only",
        baseline_rows + compression_r3,
        dedupe=True,
    )
    books["current_r1_r2_plus_r3_noncompression_only"] = evaluate(
        "current_r1_r2_plus_r3_noncompression_only",
        baseline_rows + noncompression_r3,
        dedupe=True,
    )

    stripped_books = {key: strip_book(value) for key, value in books.items()}
    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "r3_trades": rel(R3_TRADES),
        "r3_trades_sha256": sha256_file(R3_TRADES),
        "current_r1_r2": rel(CURRENT_R1_R2),
        "current_r1_r2_sha256": sha256_file(CURRENT_R1_R2),
        "mt5_scope": mt5_payload["scope"],
        "mt5_result": snapshot_result,
        "snapshot_signal_sha256": sha256_file(Path(snapshot_result["signal_csv"])),
        "snapshot_summary": {
            "snapshot_rows": len(snapshots),
            "tagged_r3_rows": len(tagged_r3),
            "no_snapshot_r3_rows": sum(1 for row in tagged_r3 if row["ea_router_regime"] == "no_snapshot"),
            "max_snapshot_lag_seconds": max(
                [float(row["router_snapshot_lag_seconds"] or 0.0) for row in tagged_r3],
                default=0.0,
            ),
            "regime_counts": dict(Counter(row["ea_router_regime"] for row in tagged_r3)),
        },
        "books": stripped_books,
        "regime_rows": regime_rows(tagged_r3),
    }
    payload["full_r3_strong_checks"] = full_r3_strong(books["r3_all"])
    payload["true_compression_checks"] = true_compression_checks(books["r3_compression_only"], books["current_r1_r2_baseline"])
    payload["portfolio_checks"] = portfolio_checks(books["current_r1_r2_plus_r3_all"], books["current_r1_r2_baseline"])
    payload["freeze_checks"] = freeze_checks(books["r3_all"], books["current_r1_r2_plus_r3_all"], books["current_r1_r2_baseline"])
    status, interpretation = decide(payload)
    payload["status"] = status
    payload["interpretation"] = interpretation

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    tagged_csv = REPORTS_DIR / f"{OUTPUT_STEM}_ROUTER_TAGGED_TRADES.csv"
    regime_csv = REPORTS_DIR / f"{OUTPUT_STEM}_REGIME_ROWS.csv"
    portfolios_csv = REPORTS_DIR / f"{OUTPUT_STEM}_COMBINED_PORTFOLIOS.csv"
    monthly_csv = REPORTS_DIR / f"{OUTPUT_STEM}_MONTHLY.csv"
    yearly_csv = REPORTS_DIR / f"{OUTPUT_STEM}_YEARLY.csv"

    write_signal_csv(tagged_csv, tagged_r3)
    r1.write_csv(regime_csv, payload["regime_rows"])
    r1.write_csv(portfolios_csv, [{"book": key, **value} for key, value in stripped_books.items()])
    r1.write_csv(monthly_csv, monthly_rows("r3_all", tagged_r3) + monthly_rows("current_r1_r2_plus_r3_all", books["current_r1_r2_plus_r3_all"]["data"]))
    r1.write_csv(yearly_csv, yearly_rows("r3_all", tagged_r3) + yearly_rows("current_r1_r2_plus_r3_all", books["current_r1_r2_plus_r3_all"]["data"]))

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "router_tagged_trades_csv": rel(tagged_csv),
        "regime_rows_csv": rel(regime_csv),
        "combined_portfolios_csv": rel(portfolios_csv),
        "monthly_csv": rel(monthly_csv),
        "yearly_csv": rel(yearly_csv),
        "mt5_report_md": rel(REPORTS_DIR / f"{OUTPUT_STEM}_MT5.md"),
        "mt5_report_json": rel(REPORTS_DIR / f"{OUTPUT_STEM}_MT5.json"),
        "mt5_signal_csv": snapshot_result["signal_csv"],
    }
    payload["outputs"] = outputs

    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "snapshot_summary": payload["snapshot_summary"],
                "books": {
                    key: {
                        "signals": value["signals"],
                        "wr": value["wr"],
                        "pf": value["pf"],
                        "net": value["net"],
                        "recent3_net": value["recent3_net"],
                        "max_closed_dd": value["max_closed_dd"],
                    }
                    for key, value in stripped_books.items()
                },
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

