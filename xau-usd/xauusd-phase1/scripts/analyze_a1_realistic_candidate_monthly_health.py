from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, rel, summary_metrics
from analyze_a1_xau_source_monthly_firewall import max_closed_drawdown, month_shape, read_ledger, weekly_shape
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import period_stats, source_contributions


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_REALISTIC_CANDIDATE_MONTHLY_HEALTH_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_REALISTIC_CANDIDATE_MONTHLY_HEALTH_20260708"
BASELINE_KEPT = (
    REPORTS_DIR
    / "A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708_replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4_KEPT.csv"
)

FREQ_SOURCE = "freq_step3_frontier"
SHORT_SOURCE = "short_v4_impulse_retest_d1_structural_h1h4"
LONG_SOURCE = "h4_d1_long_best_box2_atr80"
Q2_START = date(2026, 4, 1)
Q2_END = date(2026, 6, 30)
RECENT3_START = date(2026, 4, 1)
RECENT3_END = date(2026, 6, 30)

VARIANTS = {
    "freq_only_prev_month_health": {FREQ_SOURCE},
    "short_only_prev_month_health": {SHORT_SOURCE},
    "freq_and_short_prev_month_health": {FREQ_SOURCE, SHORT_SOURCE},
    "all_sources_prev_month_health": {FREQ_SOURCE, SHORT_SOURCE, LONG_SOURCE},
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def month_key(day: date) -> str:
    return day.strftime("%Y-%m")


def previous_month(key: str) -> str:
    year, month = [int(part) for part in key.split("-")]
    if month == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month - 1:02d}"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def apply_prev_month_health(rows: list[dict[str, Any]], gated_sources: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_entry_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_entry_month[month_key(row["entry_date"])].append(row)

    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    source_exit_month_pnl: dict[tuple[str, str], float] = defaultdict(float)

    for current_month in sorted(by_entry_month):
        prior = previous_month(current_month)
        blocked_sources = {
            source
            for source in gated_sources
            if source_exit_month_pnl.get((source, prior), 0.0) < 0.0
        }
        for row in sorted(by_entry_month[current_month], key=lambda item: (item["entry_time"], item["source_priority"], item["source_id"])):
            source = row.get("source_id", "")
            if source in blocked_sources:
                blocked = dict(row)
                blocked["drop_reason"] = f"prev_month_source_health_{prior}_negative"
                dropped.append(blocked)
                continue
            kept.append(row)
            source_exit_month_pnl[(source, month_key(row["exit_date"]))] += float(row["pnl_usd"])

    return kept, dropped


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
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_2": (row["wl"] or 0.0) >= 2.0,
        "stress_wl_ge_1p90": (row["stress_030_wl"] or 0.0) >= 1.90,
        "net_ge_19000": row["net"] >= 19000.0,
        "active_ge_84": row["active_weekday_pct"] >= 84.0,
        "dd_not_worse": row["max_closed_dd"] <= baseline["max_closed_dd"],
        "positive_months_ge_32": row["positive_months"] >= 32,
        "negative_months_le_16": row["negative_months"] <= 16,
        "q2_net_gt_0": row["q2_2026_net"] > 0.0,
        "recent3_net_gt_0": row["recent3_net"] > 0.0,
        "positive_weeks_not_worse": row["positive_week_pct"] >= baseline["positive_week_pct"],
    }


def evaluate(name: str, rows: list[dict[str, Any]], baseline: dict[str, Any]) -> dict[str, Any]:
    kept, dropped = apply_prev_month_health(rows, VARIANTS[name])
    shape = flat_shape(kept)
    checks = pass_checks(shape, baseline)
    by_drop_reason: dict[str, int] = defaultdict(int)
    by_drop_source: dict[str, int] = defaultdict(int)
    for row in dropped:
        by_drop_reason[str(row.get("drop_reason", ""))] += 1
        by_drop_source[str(row.get("source_id", ""))] += 1
    return {
        "name": name,
        "gated_sources": ",".join(sorted(VARIANTS[name])),
        "kept_data": kept,
        "dropped_data": dropped,
        "dropped_signals": len(dropped),
        "dropped_net": round(sum(float(row["pnl_usd"]) for row in dropped), 2),
        "drop_reasons": dict(sorted(by_drop_reason.items())),
        "drop_sources": dict(sorted(by_drop_source.items())),
        **shape,
        "net_delta": round(shape["net"] - baseline["net"], 2),
        "dd_delta": round(shape["max_closed_dd"] - baseline["max_closed_dd"], 2),
        "positive_month_delta": shape["positive_months"] - baseline["positive_months"],
        "negative_month_delta": shape["negative_months"] - baseline["negative_months"],
        "positive_week_delta": round(shape["positive_week_pct"] - baseline["positive_week_pct"], 2),
        "checks": checks,
        "decision": "REALISTIC_CANDIDATE_REVIEW_READY" if all(checks.values()) else "REJECT_REALISTIC_GATE",
    }


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"kept_data", "dropped_data", "checks", "drop_reasons", "drop_sources"}}


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Realistic Candidate Monthly Health",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: causal previous-month source-health gate on the current chart-context long/short blend. No MT5 launch, live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Baseline",
        "",
        "| Signals | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Q2 | Recent3 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    b = payload["baseline"]
    lines.append(
        f"| {b['signals']} | {b['wr']:.2f} | {b['wl'] or 0.0:.4f} | {b['stress_030_wl'] or 0.0:.4f} | "
        f"{b['active_weekday_pct']:.2f} | {b['net']:.2f} | {b['max_closed_dd']:.2f} | "
        f"{b['positive_months']} | {b['negative_months']} | {b['positive_week_pct']:.2f} | "
        f"{b['q2_2026_net']:.2f} | {b['recent3_net']:.2f} |"
    )

    lines.extend(
        [
            "",
            "## Results",
            "",
            "| Variant | Decision | Dropped | Dropped net | WR% | W/L | Stress W/L | Net | Net delta | Max DD | DD delta | +Months | -Months | Pos weeks% | Week delta | Q2 | Recent3 |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["results"]:
        lines.append(
            f"| `{row['name']}` | `{row['decision']}` | {row['dropped_signals']} | {row['dropped_net']:.2f} | "
            f"{row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['net']:.2f} | {row['net_delta']:.2f} | {row['max_closed_dd']:.2f} | {row['dd_delta']:.2f} | "
            f"{row['positive_months']} | {row['negative_months']} | {row['positive_week_pct']:.2f} | "
            f"{row['positive_week_delta']:.2f} | {row['q2_2026_net']:.2f} | {row['recent3_net']:.2f} |"
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

    baseline_rows = read_ledger(BASELINE_KEPT)
    baseline = flat_shape(baseline_rows)
    rows = [evaluate(name, baseline_rows, baseline) for name in VARIANTS]
    candidates = [row for row in rows if row["decision"] == "REALISTIC_CANDIDATE_REVIEW_READY"]
    if candidates:
        best = sorted(candidates, key=lambda row: (-row["positive_months"], row["max_closed_dd"], -row["net"]))[0]
        status = "REALISTIC_CANDIDATE_REVIEW_READY"
        interpretation = (
            f"`{best['name']}` passed the realistic gate with {best['positive_months']} positive months, "
            f"{best['wr']:.2f}% WR, W/L {best['wl'] or 0.0:.4f}, net {best['net']:.2f}, and max DD {best['max_closed_dd']:.2f}. "
            "Keep research-only and send to review before any demo-forward plan."
        )
    else:
        best = sorted(rows, key=lambda row: (-row["positive_months"], row["max_closed_dd"], -row["net"]))[0]
        status = "REALISTIC_MONTHLY_HEALTH_NO_SURVIVOR"
        interpretation = (
            f"No previous-month source-health row passed all realistic gates. Best diagnostic was `{best['name']}` "
            f"with {best['positive_months']} positive months, WR {best['wr']:.2f}%, net {best['net']:.2f}, "
            f"and DD delta {best['dd_delta']:.2f}. The current chart-context blend remains the best review candidate."
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
        },
        "baseline": baseline,
        "results": [strip_heavy(row) for row in rows],
        "details": [
            {
                "name": row["name"],
                "checks": row["checks"],
                "drop_sources": row["drop_sources"],
                "drop_reasons": row["drop_reasons"],
            }
            for row in rows
        ],
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
    print(json.dumps({"status": status, "best": best["name"], "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
