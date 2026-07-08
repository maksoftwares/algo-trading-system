from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, dedupe_signals, rel, summary_metrics
from analyze_a1_xau_source_monthly_firewall import max_closed_drawdown, month_shape, read_ledger, weekly_shape
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import period_stats, source_contributions


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708"

BASELINE_KEPT = (
    REPORTS_DIR
    / "A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_broad_quarantined_KEPT.csv"
)
SHORT_STEM = "A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708"
SHORT_VARIANTS = [
    "short_v4_impulse_retest_d1_nonup_h1h4",
    "short_v4_impulse_retest_d1_structural_h1h4",
    "short_v4_impulse_retest_d1_nonup_h1_only",
]
SHORT_V2_SOURCE = "short_hedge_v2_breakdown_retest"
Q2_START = date(2026, 4, 1)
Q2_END = date(2026, 6, 30)
RECENT3_START = date(2026, 4, 1)
RECENT3_END = date(2026, 6, 30)


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def short_csv(variant: str) -> Path:
    return REPORTS_DIR / f"{SHORT_STEM}_{variant}_NORMALIZED_TRADES.csv"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def without_short_v2(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("source_id") != SHORT_V2_SOURCE and row.get("upstream_source_id") != SHORT_V2_SOURCE]


def flat_shape(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    months = month_shape(rows)
    weeks = weekly_shape(rows)
    q2 = period_stats(rows, Q2_START, Q2_END)
    recent3 = period_stats(rows, RECENT3_START, RECENT3_END)
    return {
        "signals": metrics["signals"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_pf": stress["profit_factor"],
        "stress_030_net": stress["net_usd"],
        "active_weekday_pct": metrics["active_weekday_pct"],
        "max_closed_dd": max_closed_drawdown(rows),
        "positive_week_pct": weeks["positive_week_pct"],
        "worst_week": weeks["worst_week"],
        "q2_2026_net": q2["net_usd"],
        "recent3_net": recent3["net_usd"],
        **months,
    }


def pass_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "wr_ge_48": row["wr"] >= 48.0,
        "wl_ge_2": (row["wl"] or 0.0) >= 2.0,
        "stress_wl_ge_1p90": (row["stress_030_wl"] or 0.0) >= 1.90,
        "net_ge_19000": row["net"] >= 19000.0,
        "active_ge_84": row["active_weekday_pct"] >= 84.0,
        "dd_not_worse": row["max_closed_dd"] <= baseline["max_closed_dd"],
        "positive_months_not_worse": row["positive_months"] >= baseline["positive_months"],
        "negative_months_not_worse": row["negative_months"] <= baseline["negative_months"],
        "q2_improved": row["q2_2026_net"] > baseline["q2_2026_net"],
        "recent3_improved": row["recent3_net"] > baseline["recent3_net"],
    }


def evaluate(
    name: str,
    mode: str,
    variant: str,
    raw_rows: list[dict[str, Any]],
    baseline: dict[str, Any],
    baseline_row_count: int,
    short_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    kept, dropped = dedupe_signals(raw_rows)
    shape = flat_shape(kept)
    checks = pass_checks(shape, baseline)
    additions_kept = [row for row in kept if short_rows and row.get("source_id") == variant]
    v2_rows = [row for row in kept if row.get("source_id") == SHORT_V2_SOURCE]
    row = {
        "name": name,
        "mode": mode,
        "short_variant": variant,
        "baseline_rows": baseline_row_count,
        "kept_rows": len(kept),
        "dropped_rows": len(dropped),
        "short_rows_raw": len(short_rows or []),
        "short_rows_kept": len(additions_kept),
        "short_net_kept": round(sum(float(row["pnl_usd"]) for row in additions_kept), 2),
        "short_v2_rows_kept": len(v2_rows),
        "short_v2_net_kept": round(sum(float(row["pnl_usd"]) for row in v2_rows), 2),
        "kept_data": kept,
        "dropped_data": dropped,
        **shape,
        "q2_delta": round(shape["q2_2026_net"] - baseline["q2_2026_net"], 2),
        "recent3_delta": round(shape["recent3_net"] - baseline["recent3_net"], 2),
        "net_delta": round(shape["net"] - baseline["net"], 2),
        "dd_delta": round(shape["max_closed_dd"] - baseline["max_closed_dd"], 2),
        "positive_month_delta": shape["positive_months"] - baseline["positive_months"],
        "checks": checks,
        "decision": "CHART_CONTEXT_BLEND_REVIEW_CANDIDATE" if all(checks.values()) else "REJECT_BLEND_GATE",
    }
    return row


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"kept_data", "dropped_data", "checks"}}


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Chart-Context Long/Short Blend",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: recomposition of exact-MT5 ledgers only. The chart-context V4 downside-impulse short is tested as a hedge overlay inside the current H4 box2 health/broad-quarantine book. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Baseline",
        "",
        "| Row | Signals | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Q2-2026 | Recent3 | Pos weeks% | Worst week |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    base = payload["baseline"]
    lines.append(
        f"| `current_prevhealth_box2_broad_quarantined` | {base['signals']} | {base['wr']:.2f} | "
        f"{base['wl'] or 0.0:.4f} | {base['stress_030_wl'] or 0.0:.4f} | {base['active_weekday_pct']:.2f} | "
        f"{base['net']:.2f} | {base['max_closed_dd']:.2f} | {base['positive_months']} | {base['negative_months']} | "
        f"{base['q2_2026_net']:.2f} | {base['recent3_net']:.2f} | {base['positive_week_pct']:.2f} | {base['worst_week']:.2f} |"
    )

    lines.extend(
        [
            "",
            "## Blend Results",
            "",
            "| Row | Decision | Mode | Short kept | Short net | V2 kept | WR% | W/L | Stress W/L | Net | Net delta | Max DD | DD delta | +Months | Q2 delta | Recent3 delta | Pos weeks% | Worst week |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["results"]:
        lines.append(
            f"| `{row['name']}` | `{row['decision']}` | `{row['mode']}` | {row['short_rows_kept']} | "
            f"{row['short_net_kept']:.2f} | {row['short_v2_rows_kept']} | {row['wr']:.2f} | "
            f"{row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['net_delta']:.2f} | {row['max_closed_dd']:.2f} | {row['dd_delta']:.2f} | "
            f"{row['positive_months']} | {row['q2_delta']:.2f} | {row['recent3_delta']:.2f} | "
            f"{row['positive_week_pct']:.2f} | {row['worst_week']:.2f} |"
        )

    lines.extend(["", "## Gate Failures", ""])
    for row in payload["details"]:
        failed = [key for key, value in row["checks"].items() if not value]
        lines.append(f"- `{row['name']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Best Source Contributions", "", "| Source | Signals | Net USD |", "| --- | ---: | ---: |"])
    for source, contribution in payload["best_source_contributions"].items():
        lines.append(f"| `{source}` | {contribution['signals']} | {contribution['net_usd']:.2f} |")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    require_file(PREREG)
    require_file(BASELINE_KEPT)
    for variant in SHORT_VARIANTS:
        require_file(short_csv(variant))

    baseline_rows = read_ledger(BASELINE_KEPT)
    baseline_shape = flat_shape(baseline_rows)
    no_v2_rows = without_short_v2(baseline_rows)
    short_rows_by_variant = {variant: read_ledger(short_csv(variant)) for variant in SHORT_VARIANTS}

    rows: list[dict[str, Any]] = []
    rows.append(evaluate("long_book_without_short_v2", "diagnostic_remove_v2", "", no_v2_rows, baseline_shape, len(baseline_rows)))
    for variant, short_rows in short_rows_by_variant.items():
        rows.append(
            evaluate(
                f"add_{variant}",
                "add",
                variant,
                baseline_rows + short_rows,
                baseline_shape,
                len(baseline_rows),
                short_rows,
            )
        )
        rows.append(
            evaluate(
                f"replace_v2_with_{variant}",
                "replace_v2",
                variant,
                no_v2_rows + short_rows,
                baseline_shape,
                len(baseline_rows),
                short_rows,
            )
        )

    candidates = [row for row in rows if row["decision"] == "CHART_CONTEXT_BLEND_REVIEW_CANDIDATE"]
    if candidates:
        best = sorted(candidates, key=lambda row: (-row["recent3_delta"], row["max_closed_dd"], -row["net"]))[0]
        status = "CHART_CONTEXT_BLEND_REVIEW_CANDIDATE"
        interpretation = (
            f"`{best['name']}` passed the fixed combined-book gate. Keep research-only until reviewer sign-off."
        )
    else:
        best = sorted(
            rows,
            key=lambda row: (
                -(row["recent3_delta"] + row["q2_delta"]),
                row["max_closed_dd"],
                -row["net"],
            ),
        )[0]
        status = "CHART_CONTEXT_BLEND_NO_SURVIVOR"
        interpretation = (
            f"No chart-context blend passed all combined-book gates. Best diagnostic row was `{best['name']}` with "
            f"recent3 delta {best['recent3_delta']:.2f}, Q2 delta {best['q2_delta']:.2f}, net delta {best['net_delta']:.2f}, "
            f"and DD delta {best['dd_delta']:.2f}. Treat the V4 short as a hedge clue only unless a reviewer approves a new gate."
        )

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    best_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{best['name']}_KEPT.csv"
    best_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{best['name']}_DROPPED.csv"

    write_csv(results_csv, [strip_heavy(row) for row in rows])
    write_signal_csv(best_kept_csv, best["kept_data"])
    write_signal_csv(best_dropped_csv, best["dropped_data"])

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "inputs": {
            "baseline_kept": rel(BASELINE_KEPT),
            "baseline_sha256": sha256_file(BASELINE_KEPT),
            "short_csvs": {variant: rel(short_csv(variant)) for variant in SHORT_VARIANTS},
            "short_sha256": {variant: sha256_file(short_csv(variant)) for variant in SHORT_VARIANTS},
        },
        "baseline": baseline_shape,
        "results": [strip_heavy(row) for row in rows],
        "details": [{"name": row["name"], "checks": row["checks"]} for row in rows],
        "best": strip_heavy(best),
        "best_source_contributions": source_contributions(best["kept_data"]),
        "interpretation": interpretation,
        "outputs": {
            "report_md": rel(report_md),
            "report_json": rel(report_json),
            "results_csv": rel(results_csv),
            "best_kept_csv": rel(best_kept_csv),
            "best_dropped_csv": rel(best_dropped_csv),
        },
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "best": best["name"],
                "recent3_delta": best["recent3_delta"],
                "q2_delta": best["q2_delta"],
                "net_delta": best["net_delta"],
                "dd_delta": best["dd_delta"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
