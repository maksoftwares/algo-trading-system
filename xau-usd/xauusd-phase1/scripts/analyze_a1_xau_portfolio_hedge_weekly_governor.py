from __future__ import annotations

import csv
import heapq
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from analyze_a1_hybrid_weekly_exit_anatomy import week_start
from analyze_a1_owner_goal_step3_portfolio_composition import (
    MARKET_DAYS,
    REPORTS_DIR,
    parse_dt,
    rel,
    summary_metrics,
)
from run_a1_h4_d1_geometry_v2_weekly_shape import write_signal_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_PORTFOLIO_HEDGE_WEEKLY_GOVERNOR_PREREG_2026_07_08.md"
SUPPORTIVE_LONG = REPORTS_DIR / "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606_supportive_guard_KEPT.csv"
LONG_PLUS_V2 = (
    REPORTS_DIR
    / "A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_KEPT.csv"
)
OUTPUT_STEM = "A1_XAU_PORTFOLIO_HEDGE_WEEKLY_GOVERNOR_202207_202606"

START_DATE = date(2022, 7, 1)
END_DATE = date(2026, 6, 30)
Q2_2026_START = date(2026, 4, 1)
Q2_2026_END = date(2026, 6, 30)

LOSS_STOPS = [25.0, 50.0, 75.0, 100.0, 150.0, 200.0]
PROFIT_LOCKS = [25.0, 50.0, 75.0, 100.0, 150.0, 200.0]
BRACKET_LOSSES = [50.0, 75.0, 100.0]
BRACKET_PROFITS = [50.0, 75.0, 100.0, 150.0]


def all_week_starts() -> list[date]:
    current = week_start(START_DATE)
    end = week_start(END_DATE)
    weeks: list[date] = []
    while current <= end:
        weeks.append(current)
        current += timedelta(days=7)
    return weeks


ALL_WEEK_STARTS = all_week_starts()


def parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())


def maybe_dt(value: Any, fallback: datetime) -> datetime:
    text = str(value or "").strip()
    if not text:
        return fallback
    return parse_dt(text)


def read_ledger(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for ordinal, row in enumerate(csv.DictReader(handle), start=2):
            entry_time = parse_dt(row["entry_time"])
            exit_time = maybe_dt(row.get("exit_time"), entry_time)
            rows.append(
                {
                    **row,
                    "component": row.get("component", ""),
                    "source_id": row.get("source_id", ""),
                    "upstream_source_id": row.get("upstream_source_id", ""),
                    "upstream_component": row.get("upstream_component", ""),
                    "family_group": row.get("family_group", ""),
                    "source_priority": int(row.get("source_priority") or 0),
                    "cell_id": row.get("cell_id", ""),
                    "component_priority": int(row.get("component_priority") or 0),
                    "variant_name": row.get("variant_name", ""),
                    "entry_time": entry_time,
                    "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                    "exit_time": exit_time,
                    "exit_date": exit_time.date(),
                    "direction": str(row.get("direction", "")).upper(),
                    "pnl_usd": float(row.get("pnl_usd") or 0.0),
                    "tickets": int(row.get("tickets") or 1),
                    "lots": float(row.get("lots") or 0.0),
                    "source_csv": row.get("source_csv", str(path)),
                    "source_row": int(row.get("source_row") or ordinal),
                }
            )
    return rows


def weekly_shape(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_week: dict[date, float] = defaultdict(float)
    by_month: dict[str, float] = defaultdict(float)
    for row in rows:
        exit_day = row["exit_date"]
        pnl = float(row["pnl_usd"])
        by_week[week_start(exit_day)] += pnl
        by_month[exit_day.strftime("%Y-%m")] += pnl

    active_weeks = [week for week, value in by_week.items() if abs(value) > 0.0000001]
    positive_all = sum(1 for week in ALL_WEEK_STARTS if by_week.get(week, 0.0) > 0.0)
    positive_active = sum(1 for week in active_weeks if by_week.get(week, 0.0) > 0.0)
    rolling_positive = 0
    rolling_total = 0
    for index in range(0, max(0, len(ALL_WEEK_STARTS) - 3)):
        rolling_total += 1
        total = sum(by_week.get(ALL_WEEK_STARTS[index + offset], 0.0) for offset in range(4))
        if total > 0.0:
            rolling_positive += 1

    return {
        "calendar_weeks": len(ALL_WEEK_STARTS),
        "active_weeks": len(active_weeks),
        "active_week_pct": round(100.0 * len(active_weeks) / len(ALL_WEEK_STARTS), 2),
        "positive_week_pct": round(100.0 * positive_all / len(ALL_WEEK_STARTS), 2),
        "positive_active_week_pct": round(100.0 * positive_active / len(active_weeks), 2)
        if active_weeks
        else 0.0,
        "worst_week": round(min((by_week.get(week, 0.0) for week in ALL_WEEK_STARTS), default=0.0), 2),
        "best_week": round(max((by_week.get(week, 0.0) for week in ALL_WEEK_STARTS), default=0.0), 2),
        "rolling4_positive_pct": round(100.0 * rolling_positive / rolling_total, 2) if rolling_total else 0.0,
        "june_2026": round(by_month.get("2026-06", 0.0), 2),
    }


def period_net(rows: list[dict[str, Any]], start: date, end: date) -> float:
    return round(sum(float(row["pnl_usd"]) for row in rows if start <= row["exit_date"] <= end), 2)


def apply_weekly_governor(
    rows: list[dict[str, Any]],
    *,
    loss_stop: float | None,
    profit_lock: float | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    closed_week_pnl: dict[date, float] = defaultdict(float)
    pending: list[tuple[datetime, int, date, float]] = []
    counter = 0

    for row in sorted(rows, key=lambda item: (item["entry_time"], item["source_priority"], item["source_id"])):
        entry_time = row["entry_time"]
        while pending and pending[0][0] <= entry_time:
            _exit_time, _counter, close_week, pnl = heapq.heappop(pending)
            closed_week_pnl[close_week] += pnl

        current_week = week_start(entry_time.date())
        closed_pnl = closed_week_pnl[current_week]
        reason = ""
        if loss_stop is not None and closed_pnl <= -loss_stop:
            reason = f"weekly_loss_stop_{loss_stop:g}"
        elif profit_lock is not None and closed_pnl >= profit_lock:
            reason = f"weekly_profit_lock_{profit_lock:g}"

        if reason:
            item = dict(row)
            item["drop_reason"] = reason
            item["closed_week_pnl_before_entry"] = round(closed_pnl, 2)
            dropped.append(item)
            continue

        kept.append(row)
        counter += 1
        heapq.heappush(
            pending,
            (row["exit_time"], counter, week_start(row["exit_date"]), float(row["pnl_usd"])),
        )

    return kept, dropped


def decision(row: dict[str, Any], combo_baseline: dict[str, Any]) -> str:
    wl = row.get("wl") or 0.0
    stress_wl = row.get("stress_030_wl") or 0.0
    core_ok = (
        row["wr"] >= 48.0
        and wl >= 2.0
        and stress_wl >= 1.90
        and row["net"] >= 17000.0
    )
    weekly_delta = row["positive_week_pct"] - combo_baseline["positive_week_pct"]
    june_improves = row["june_2026"] > combo_baseline["june_2026"]

    if (
        row["positive_week_pct"] >= 65.0
        and row["active_weekday_pct"] >= 85.0
        and core_ok
        and june_improves
    ):
        return "PORTFOLIO_GOVERNOR_REVIEW_CANDIDATE"
    if weekly_delta >= 3.0 and core_ok:
        return "SMOOTHING_WATCHLIST"
    if weekly_delta > 0.0 and not core_ok:
        return "WEEKLY_IMPROVES_CORE_BREAKS"
    return "REJECT_NO_WEEKLY_REPAIR"


def evaluate(
    name: str,
    rows: list[dict[str, Any]],
    dropped: list[dict[str, Any]],
    combo_baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metrics = summary_metrics(rows, market_days=MARKET_DAYS)
    stress = summary_metrics(rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    shape = weekly_shape(rows)
    row = {
        "name": name,
        "signals": metrics["signals"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "dd": metrics["max_closed_drawdown_usd"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_net": stress["net_usd"],
        "active_weekday_pct": metrics["active_weekday_pct"],
        "positive_week_pct": shape["positive_week_pct"],
        "positive_active_week_pct": shape["positive_active_week_pct"],
        "active_week_pct": shape["active_week_pct"],
        "worst_week": shape["worst_week"],
        "rolling4_positive_pct": shape["rolling4_positive_pct"],
        "june_2026": shape["june_2026"],
        "q2_2026_net": period_net(rows, Q2_2026_START, Q2_2026_END),
        "blocked_signals": len(dropped),
        "kept_rows": rows,
        "dropped_rows": dropped,
    }
    row["decision"] = "BASELINE" if combo_baseline is None else decision(row, combo_baseline)
    return row


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"kept_rows", "dropped_rows"}}


def csv_safe(row: dict[str, Any]) -> dict[str, Any]:
    return strip_heavy(row)


def write_results(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = list(csv_safe(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(csv_safe(row))


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Portfolio Hedge Weekly Governor Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: causal weekly governor diagnostic over existing exact-MT5 ledgers only. No MT5 launch, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        "",
        "## Best Rows",
        "",
        "| Rank | Rule | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Pos weeks% | Pos active weeks% | PF | Net | Worst week | Rolling 4w+% | June 2026 | Q2 2026 |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(payload["top_rows"], start=1):
        lines.append(
            f"| {index} | `{row['name']}` | `{row['decision']}` | {row['signals']} | {row['blocked_signals']} | "
            f"{row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['active_weekday_pct']:.2f} | {row['positive_week_pct']:.2f} | "
            f"{row['positive_active_week_pct']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['worst_week']:.2f} | {row['rolling4_positive_pct']:.2f} | {row['june_2026']:.2f} | "
            f"{row['q2_2026_net']:.2f} |"
        )

    best = payload["best_row"]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"Best row: `{best['name']}` with `{best['positive_week_pct']:.2f}%` positive calendar weeks, `{best['wr']:.2f}%` WR, `{best['wl'] or 0.0:.4f}` W/L, and `{best['net']:.2f}` net.",
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
    if not PREREG.exists():
        raise FileNotFoundError(PREREG)
    if not SUPPORTIVE_LONG.exists():
        raise FileNotFoundError(SUPPORTIVE_LONG)
    if not LONG_PLUS_V2.exists():
        raise FileNotFoundError(LONG_PLUS_V2)

    supportive = read_ledger(SUPPORTIVE_LONG)
    combo = read_ledger(LONG_PLUS_V2)

    baseline_supportive = evaluate("baseline_supportive_guard_no_hedge", supportive, [], None)
    combo_ungated = evaluate("long_plus_short_v2_no_weekly_gate", combo, [], None)

    rows: list[dict[str, Any]] = [baseline_supportive, combo_ungated]
    for stop in LOSS_STOPS:
        kept, dropped = apply_weekly_governor(combo, loss_stop=stop, profit_lock=None)
        rows.append(evaluate(f"long_plus_short_v2_loss_stop_{int(stop)}", kept, dropped, combo_ungated))
    for lock in PROFIT_LOCKS:
        kept, dropped = apply_weekly_governor(combo, loss_stop=None, profit_lock=lock)
        rows.append(evaluate(f"long_plus_short_v2_profit_lock_{int(lock)}", kept, dropped, combo_ungated))
    for stop in BRACKET_LOSSES:
        for lock in BRACKET_PROFITS:
            kept, dropped = apply_weekly_governor(combo, loss_stop=stop, profit_lock=lock)
            rows.append(
                evaluate(
                    f"long_plus_short_v2_bracket_loss{int(stop)}_profit{int(lock)}",
                    kept,
                    dropped,
                    combo_ungated,
                )
            )

    rank_order = {
        "PORTFOLIO_GOVERNOR_REVIEW_CANDIDATE": 0,
        "SMOOTHING_WATCHLIST": 1,
        "WEEKLY_IMPROVES_CORE_BREAKS": 2,
        "BASELINE": 3,
        "REJECT_NO_WEEKLY_REPAIR": 4,
    }
    ranked = sorted(
        rows,
        key=lambda row: (
            rank_order.get(row["decision"], 9),
            -row["positive_week_pct"],
            -row["positive_active_week_pct"],
            -row["active_weekday_pct"],
            -(row["stress_030_wl"] or 0.0),
            -row["net"],
        ),
    )
    best = ranked[0]
    outputs = {
        "report_md": rel(REPORTS_DIR / f"{OUTPUT_STEM}.md"),
        "report_json": rel(REPORTS_DIR / f"{OUTPUT_STEM}.json"),
        "results_csv": rel(REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"),
        "best_kept_csv": rel(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv"),
        "best_dropped_csv": rel(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv"),
    }
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    best_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv"
    best_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv"

    if best["decision"] == "PORTFOLIO_GOVERNOR_REVIEW_CANDIDATE":
        status = "PORTFOLIO_GOVERNOR_REVIEW_CANDIDATE"
        interpretation = "A bounded causal weekly governor reached the review-candidate gate. It still needs exact combined-EA implementation and reviewer approval before any demo discussion."
    elif best["decision"] == "SMOOTHING_WATCHLIST":
        status = "SMOOTHING_WATCHLIST"
        interpretation = "A bounded causal weekly governor improved weekly shape without breaking the core. Keep it as a watchlist implementation idea, not a demo candidate."
    else:
        status = "NO_PORTFOLIO_GOVERNOR_SURVIVOR"
        interpretation = "The weekly governor grid did not produce a useful repair. The blocker is not just week-level trade stopping; the portfolio still needs a genuinely smoother independent source or a relaxed weekly target."

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "boundary": "existing_exact_mt5_ledgers_only_no_runtime_change",
        "inputs": {
            "supportive_long": rel(SUPPORTIVE_LONG),
            "long_plus_v2": rel(LONG_PLUS_V2),
        },
        "baseline_supportive": strip_heavy(baseline_supportive),
        "combo_ungated": strip_heavy(combo_ungated),
        "best_row": strip_heavy(best),
        "top_rows": [strip_heavy(row) for row in ranked[:20]],
        "all_rows": [strip_heavy(row) for row in ranked],
        "interpretation": interpretation,
        "outputs": outputs,
    }

    write_results(results_csv, ranked)
    write_signal_csv(best_kept_csv, best["kept_rows"])
    write_signal_csv(best_dropped_csv, best["dropped_rows"])
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "best": best["name"],
                "decision": best["decision"],
                "signals": best["signals"],
                "blocked": best["blocked_signals"],
                "wr": best["wr"],
                "wl": best["wl"],
                "stress_030_wl": best["stress_030_wl"],
                "positive_week_pct": best["positive_week_pct"],
                "active_weekday_pct": best["active_weekday_pct"],
                "net": best["net"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
