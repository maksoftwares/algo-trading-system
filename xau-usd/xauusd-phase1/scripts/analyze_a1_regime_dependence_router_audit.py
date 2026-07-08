from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, rel, summary_metrics
from analyze_a1_xau_source_monthly_firewall import max_closed_drawdown, month_shape, read_ledger, weekly_shape
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import period_stats, source_contributions


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_REGIME_DEPENDENCE_ROUTER_AUDIT_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_REGIME_DEPENDENCE_ROUTER_AUDIT_20260708"
BASELINE_KEPT = (
    REPORTS_DIR
    / "A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708_replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4_KEPT.csv"
)

LONG_SOURCE = "h4_d1_long_best_box2_atr80"
FREQ_SOURCE = "freq_step3_frontier"
SHORT_SOURCE = "short_v4_impulse_retest_d1_structural_h1h4"

PERIODS = [
    ("full_202207_202606", date(2022, 7, 1), date(2026, 6, 30)),
    ("pre_2025_202207_202412", date(2022, 7, 1), date(2024, 12, 31)),
    ("bull_harvest_202501_202601", date(2025, 1, 1), date(2026, 1, 31)),
    ("q1_transition_202601_202603", date(2026, 1, 1), date(2026, 3, 31)),
    ("q2_recent_202604_202606", date(2026, 4, 1), date(2026, 6, 30)),
    ("last12_202507_202606", date(2025, 7, 1), date(2026, 6, 30)),
]

DIAGNOSTIC_PORTFOLIOS = {
    "current_blend": {LONG_SOURCE, FREQ_SOURCE, SHORT_SOURCE},
    "h4_long_only": {LONG_SOURCE},
    "freq_only": {FREQ_SOURCE},
    "short_v4_only": {SHORT_SOURCE},
    "freq_plus_short_no_h4": {FREQ_SOURCE, SHORT_SOURCE},
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def market_days_between(start: date, end: date) -> list[date]:
    return [day for day in MARKET_DAYS if start <= day <= end]


def rows_in_period(rows: list[dict[str, Any]], start: date, end: date) -> list[dict[str, Any]]:
    return [row for row in rows if start <= row["entry_date"] <= end]


def rows_for_sources(rows: list[dict[str, Any]], sources: set[str]) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("source_id", "")) in sources]


def flat_shape(rows: list[dict[str, Any]], market_days: list[date] | None = None) -> dict[str, Any]:
    metrics = summary_metrics(rows, market_days=market_days or MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=market_days or MARKET_DAYS)
    months = month_shape(rows)
    weeks = weekly_shape(rows)
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
        "active_weekdays": metrics["active_weekdays"],
        "max_closed_dd": max_closed_drawdown(rows),
        "positive_week_pct": weeks["positive_week_pct"],
        "worst_week": weeks["worst_week"],
        **months,
    }


def period_source_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    sources = ["ALL", LONG_SOURCE, FREQ_SOURCE, SHORT_SOURCE]
    for period_name, start, end in PERIODS:
        period_rows = rows_in_period(rows, start, end)
        days = market_days_between(start, end)
        for source in sources:
            selected = period_rows if source == "ALL" else rows_for_sources(period_rows, {source})
            shape = flat_shape(selected, days)
            output.append(
                {
                    "period": period_name,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "source_id": source,
                    **shape,
                }
            )
    return output


def monthly_source_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        month = row["exit_date"].strftime("%Y-%m")
        grouped[(month, str(row.get("source_id", "")))].append(row)
    output: list[dict[str, Any]] = []
    for (month, source), items in sorted(grouped.items()):
        shape = flat_shape(items)
        output.append(
            {
                "exit_month": month,
                "source_id": source,
                "signals": shape["signals"],
                "wins": shape["wins"],
                "losses": shape["losses"],
                "wr": shape["wr"],
                "wl": shape["wl"],
                "net": shape["net"],
            }
        )
    return output


def diagnostic_portfolio_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for name, sources in DIAGNOSTIC_PORTFOLIOS.items():
        selected = rows_for_sources(rows, sources)
        shape = flat_shape(selected)
        q2 = period_stats(selected, date(2026, 4, 1), date(2026, 6, 30))
        row = {
            "portfolio": name,
            "sources": ",".join(sorted(sources)),
            **shape,
            "q2_signals": q2["signals"],
            "q2_wr": q2["win_rate_pct"],
            "q2_wl": q2["avg_win_loss"],
            "q2_net": q2["net_usd"],
            "core_gate": (
                shape["wr"] >= 50.0
                and (shape["wl"] or 0.0) >= 2.0
                and shape["net"] >= 19000.0
                and shape["active_weekday_pct"] >= 84.0
            ),
        }
        output.append(row)
    return output


def top_months(rows: list[dict[str, Any]], source: str, limit: int = 8) -> list[dict[str, Any]]:
    grouped: dict[str, float] = defaultdict(float)
    for row in rows_for_sources(rows, {source}):
        grouped[row["exit_date"].strftime("%Y-%m")] += float(row["pnl_usd"])
    ranked = sorted(grouped.items(), key=lambda item: item[1], reverse=True)
    return [{"exit_month": month, "net": round(net, 2)} for month, net in ranked[:limit]]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pct(numerator: float, denominator: float) -> float:
    if abs(denominator) < 0.0000001:
        return 0.0
    return round(100.0 * numerator / denominator, 2)


def decision(payload: dict[str, Any]) -> tuple[str, str]:
    current = payload["diagnostic_portfolios_by_name"]["current_blend"]
    no_h4 = payload["diagnostic_portfolios_by_name"]["freq_plus_short_no_h4"]
    long_full = payload["full_source_contributions"].get(LONG_SOURCE, {"net_usd": 0.0, "signals": 0})
    all_full = payload["full_shape"]
    long_q2 = payload["q2_source_stats"].get(LONG_SOURCE, {"net_usd": 0.0, "signals": 0})
    q2_all = payload["q2_all"]

    current_core = (
        current["wr"] >= 50.0
        and (current["wl"] or 0.0) >= 2.0
        and (current["stress_030_wl"] or 0.0) >= 1.90
        and current["net"] >= 19000.0
    )
    long_net_pct = pct(float(long_full["net_usd"]), float(all_full["net"]))

    if (
        long_net_pct >= 60.0
        and float(long_q2["net_usd"]) <= 0.0
        and int(long_q2["signals"]) == 0
        and not bool(no_h4["core_gate"])
    ):
        return (
            "REGIME_DEPENDENCE_CONFIRMED_SHADOW_ONLY",
            "The user's concern is confirmed. The full-window book is mostly carried by the H4/D1 long source, but Q2-2026 survival came from frequency plus short rows while the H4/D1 long source had no Q2 trades. Removing the long source leaves no viable full-window book. Treat this as a regime-routed research candidate, not demo-ready.",
        )
    if current_core and float(q2_all["net_usd"]) > 0.0:
        return (
            "REGIME_ROUTER_REVIEW_CANDIDATE",
            "The current blend keeps core full-window shape and Q2 survival is positive, but the long edge must be described as conditional, not as current all-regime proof.",
        )
    return (
        "REGIME_ROUTER_NO_SURVIVOR",
        "The current blend does not preserve enough full-window or recent-regime evidence to promote.",
    )


def render(payload: dict[str, Any]) -> str:
    full = payload["full_shape"]
    q2 = payload["q2_all"]
    lines = [
        "# A1 XAU Regime-Dependence Router Audit",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: source/time attribution over the current exact-MT5 chart-context blend ledger. PnL and shape are manually recomputed from trade rows. No MT5 launch, live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Input SHA256: `{payload['input_sha256']}`",
        "",
        "## Current Blend",
        "",
        "| Period | Signals | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst week |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| Full | {full['signals']} | {full['wr']:.2f} | {full['wl'] or 0.0:.4f} | {full['stress_030_wl'] or 0.0:.4f} | {full['active_weekday_pct']:.2f} | {full['net']:.2f} | {full['max_closed_dd']:.2f} | {full['positive_months']} | {full['negative_months']} | {full['positive_week_pct']:.2f} | {full['worst_week']:.2f} |",
        f"| Q2-2026 | {q2['signals']} | {q2['win_rate_pct']:.2f} | {q2['avg_win_loss'] or 0.0:.4f} | n/a | n/a | {q2['net_usd']:.2f} | n/a | n/a | n/a | n/a | n/a |",
        "",
        "## Full-Window Source Concentration",
        "",
        "| Source | Signals | Net | Net share |",
        "| --- | ---: | ---: | ---: |",
    ]
    for source, item in payload["full_source_contributions"].items():
        lines.append(
            f"| `{source}` | {item['signals']} | {item['net_usd']:.2f} | {pct(float(item['net_usd']), full['net']):.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Q2-2026 Source Contribution",
            "",
            "| Source | Signals | Wins | Losses | WR% | W/L | Net |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for source, item in payload["q2_source_stats"].items():
        lines.append(
            f"| `{source}` | {item['signals']} | {item['wins']} | {item['losses']} | {item['win_rate_pct']:.2f} | {item['avg_win_loss'] or 0.0:.4f} | {item['net_usd']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Diagnostic Portfolios",
            "",
            "| Portfolio | Core gate | Signals | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | Q2 signals | Q2 WR% | Q2 W/L | Q2 net |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["diagnostic_portfolios"]:
        lines.append(
            f"| `{row['portfolio']}` | `{row['core_gate']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['active_weekday_pct']:.2f} | {row['net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['positive_months']} | {row['q2_signals']} | {row['q2_wr']:.2f} | {row['q2_wl'] or 0.0:.4f} | {row['q2_net']:.2f} |"
        )

    lines.extend(["", "## Top H4/D1 Long Months", "", "| Exit month | Net |", "| --- | ---: |"])
    for item in payload["top_long_months"]:
        lines.append(f"| `{item['exit_month']}` | {item['net']:.2f} |")

    lines.extend(["", "## Period/Source Snapshot", "", "| Period | Source | Signals | WR% | W/L | Net | Active% |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"])
    important_periods = {"pre_2025_202207_202412", "bull_harvest_202501_202601", "q2_recent_202604_202606", "last12_202507_202606"}
    for row in payload["period_source_rows"]:
        if row["period"] not in important_periods:
            continue
        if row["source_id"] not in {"ALL", LONG_SOURCE, FREQ_SOURCE, SHORT_SOURCE}:
            continue
        lines.append(
            f"| `{row['period']}` | `{row['source_id']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['net']:.2f} | {row['active_weekday_pct']:.2f} |"
        )

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    require_file(PREREG)
    require_file(BASELINE_KEPT)

    rows = read_ledger(BASELINE_KEPT)
    full_shape = flat_shape(rows)
    q2_rows = rows_in_period(rows, date(2026, 4, 1), date(2026, 6, 30))
    q2_all = period_stats(rows, date(2026, 4, 1), date(2026, 6, 30))
    q2_source_stats = {
        source: period_stats(rows_for_sources(rows, {source}), date(2026, 4, 1), date(2026, 6, 30))
        for source in (FREQ_SOURCE, SHORT_SOURCE, LONG_SOURCE)
    }
    full_source_contrib = source_contributions(rows)
    period_rows = period_source_rows(rows)
    monthly_rows = monthly_source_rows(rows)
    portfolio_rows = diagnostic_portfolio_rows(rows)
    portfolio_by_name = {row["portfolio"]: row for row in portfolio_rows}
    top_long = top_months(rows, LONG_SOURCE)

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    period_csv = REPORTS_DIR / f"{OUTPUT_STEM}_PERIOD_SOURCE.csv"
    monthly_csv = REPORTS_DIR / f"{OUTPUT_STEM}_MONTHLY_SOURCE.csv"
    portfolio_csv = REPORTS_DIR / f"{OUTPUT_STEM}_DIAGNOSTIC_PORTFOLIOS.csv"
    q2_csv = REPORTS_DIR / f"{OUTPUT_STEM}_Q2_ROWS.csv"

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "input": rel(BASELINE_KEPT),
        "input_sha256": sha256_file(BASELINE_KEPT),
        "full_shape": full_shape,
        "full_source_contributions": full_source_contrib,
        "q2_all": q2_all,
        "q2_source_stats": q2_source_stats,
        "q2_source_contributions": source_contributions(q2_rows),
        "period_source_rows": period_rows,
        "monthly_source_rows": monthly_rows,
        "diagnostic_portfolios": portfolio_rows,
        "diagnostic_portfolios_by_name": portfolio_by_name,
        "top_long_months": top_long,
        "outputs": {
            "report_md": rel(report_md),
            "report_json": rel(report_json),
            "period_source_csv": rel(period_csv),
            "monthly_source_csv": rel(monthly_csv),
            "diagnostic_portfolios_csv": rel(portfolio_csv),
            "q2_rows_csv": rel(q2_csv),
        },
    }
    status, interpretation = decision(payload)
    payload["status"] = status
    payload["interpretation"] = interpretation

    write_csv(period_csv, period_rows)
    write_csv(monthly_csv, monthly_rows)
    write_csv(portfolio_csv, portfolio_rows)
    write_signal_csv(q2_csv, q2_rows)
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "full_net": full_shape["net"],
                "long_full_net": full_source_contrib.get(LONG_SOURCE, {}).get("net_usd", 0.0),
                "q2_net": q2_all["net_usd"],
                "long_q2_signals": q2_source_stats[LONG_SOURCE]["signals"],
                "long_q2_net": q2_source_stats[LONG_SOURCE]["net_usd"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
