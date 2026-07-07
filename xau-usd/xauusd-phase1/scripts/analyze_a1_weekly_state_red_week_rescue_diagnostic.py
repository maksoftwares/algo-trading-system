from __future__ import annotations

import csv
import heapq
import json
from bisect import bisect_right
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from analyze_a1_hybrid_weekly_exit_anatomy import week_start
from analyze_a1_smooth_second_book_weekly_target_diagnostic import (
    BASELINE_KEPT,
    REPORTS_DIR,
    TARGET_ACTIVITY,
    TARGET_HIGH,
    TARGET_LOW,
    ensure_exit_times,
    evaluate_portfolio,
    load_second_books,
    normalize_baseline,
    rel,
    strip_heavy,
    weighted_rows,
    write_results_csv,
)
from run_a1_h4_d1_geometry_v2_weekly_shape import write_signal_csv


OUTPUT_STEM = "A1_XAU_WEEKLY_STATE_RED_WEEK_RESCUE_DIAGNOSTIC_202207_202606"
START_DATE = date(2022, 7, 1)
END_DATE = date(2026, 6, 30)
THRESHOLDS = [-25.0, -50.0, -75.0, -100.0, -150.0, -200.0, -300.0]
WEIGHTS = [0.5, 1.0, 2.0, 3.0, 5.0]
MAX_BOOKS = 40


def all_week_starts() -> list[date]:
    start = week_start(START_DATE)
    end = week_start(END_DATE)
    weeks: list[date] = []
    current = start
    while current <= end:
        weeks.append(current)
        current += timedelta(days=7)
    return weeks


ALL_WEEK_STARTS = all_week_starts()


def week_nets(rows: list[dict[str, Any]]) -> dict[date, float]:
    out: dict[date, float] = defaultdict(float)
    for row in rows:
        exit_day = row["exit_date"]
        out[week_start(exit_day)] += float(row.get("pnl_usd") or 0.0)
    return out


def build_week_state_index(rows: list[dict[str, Any]]) -> dict[date, dict[str, list[Any]]]:
    by_week: dict[date, list[tuple[datetime, float]]] = defaultdict(list)
    for row in rows:
        exit_time = row.get("exit_time")
        if not isinstance(exit_time, datetime):
            continue
        by_week[week_start(exit_time.date())].append((exit_time, float(row.get("pnl_usd") or 0.0)))

    index: dict[date, dict[str, list[Any]]] = {}
    for week, events in by_week.items():
        events.sort(key=lambda item: item[0])
        times: list[datetime] = []
        prefix: list[float] = [0.0]
        running = 0.0
        for event_time, pnl in events:
            times.append(event_time)
            running += pnl
            prefix.append(running)
        index[week] = {"times": times, "prefix": prefix}
    return index


def current_week_closed_pnl_before(state_index: dict[date, dict[str, list[Any]]], entry_time: datetime) -> float:
    bucket = state_index.get(week_start(entry_time.date()))
    if not bucket:
        return 0.0
    idx = bisect_right(bucket["times"], entry_time)
    return float(bucket["prefix"][idx])


def previous_week_net(week_net: dict[date, float], entry_time: datetime, lookback: int = 1) -> float:
    current_week = week_start(entry_time.date())
    return sum(week_net.get(current_week - timedelta(days=7 * offset), 0.0) for offset in range(1, lookback + 1))


def is_h4_d1(row: dict[str, Any]) -> bool:
    text = " ".join(
        str(row.get(key, ""))
        for key in ("component", "source_id", "upstream_source_id", "upstream_component", "family_group", "variant_name")
    ).lower()
    return "h4_d1" in text or "d1/h4" in text


def filter_baseline_riskoff(
    rows: list[dict[str, Any]],
    threshold: float,
    *,
    h4_only: bool,
) -> tuple[list[dict[str, Any]], int]:
    kept: list[dict[str, Any]] = []
    blocked = 0
    realized_by_week: dict[date, float] = defaultdict(float)
    pending_exits: list[tuple[datetime, date, float]] = []

    for row in sorted(rows, key=lambda item: item["entry_time"]):
        entry_time = row["entry_time"]
        while pending_exits and pending_exits[0][0] <= entry_time:
            _, exit_week, pnl = heapq.heappop(pending_exits)
            realized_by_week[exit_week] += pnl

        applies = (not h4_only) or is_h4_d1(row)
        if applies and realized_by_week.get(week_start(entry_time.date()), 0.0) <= threshold:
            blocked += 1
            continue

        kept.append(row)
        exit_time = row.get("exit_time")
        if isinstance(exit_time, datetime):
            heapq.heappush(
                pending_exits,
                (exit_time, week_start(exit_time.date()), float(row.get("pnl_usd") or 0.0)),
            )
    return kept, blocked


def select_current_week_drawdown_addon(
    rows: list[dict[str, Any]],
    state_index: dict[date, dict[str, list[Any]]],
    threshold: float,
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if current_week_closed_pnl_before(state_index, row["entry_time"]) <= threshold
    ]


def select_previous_week_red_addon(
    rows: list[dict[str, Any]],
    baseline_week_net: dict[date, float],
    lookback: int,
) -> list[dict[str, Any]]:
    return [row for row in rows if previous_week_net(baseline_week_net, row["entry_time"], lookback=lookback) < 0.0]


def select_candidate_books(second_books: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    scored: list[dict[str, Any]] = []
    for name, rows in second_books.items():
        if len(rows) < 150:
            continue
        result = evaluate_portfolio(name, rows, dedupe=False)
        if result["net"] <= 0:
            continue
        if result["positive_week_pct"] < 50.0 and result["active_weekday_pct"] < 40.0:
            continue
        scored.append(result)

    scored.sort(
        key=lambda row: (
            -row["positive_week_pct"],
            -row["active_weekday_pct"],
            -(row["pf"] or 0.0),
            -row["net"],
        )
    )
    selected_names = [row["name"] for row in scored[:MAX_BOOKS]]
    return {name: second_books[name] for name in selected_names}, scored


def decision_note(row: dict[str, Any]) -> str:
    if row["positive_week_pct"] >= TARGET_HIGH and row["active_weekday_pct"] >= TARGET_ACTIVITY:
        return "HITS_80_WEEK_AND_90_ACTIVITY_DIAGNOSTIC"
    if row["positive_week_pct"] >= TARGET_LOW and row["active_weekday_pct"] >= TARGET_ACTIVITY:
        return "HITS_70_WEEK_AND_90_ACTIVITY_DIAGNOSTIC"
    if row["positive_week_pct"] >= TARGET_LOW:
        return "HITS_70_WEEK_ACTIVITY_GAP"
    if row["active_weekday_pct"] >= TARGET_ACTIVITY:
        return "ACTIVITY_HIT_WEEKLY_GAP"
    return "NO_WEEKLY_ACTIVITY_HIT"


def rank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rank_order = {
        "HITS_80_WEEK_AND_90_ACTIVITY_DIAGNOSTIC": 0,
        "HITS_70_WEEK_AND_90_ACTIVITY_DIAGNOSTIC": 1,
        "HITS_70_WEEK_ACTIVITY_GAP": 2,
        "ACTIVITY_HIT_WEEKLY_GAP": 3,
    }
    for row in rows:
        row["state_decision"] = decision_note(row)
    rows.sort(
        key=lambda row: (
            rank_order.get(row["state_decision"], 9),
            -row["positive_week_pct"],
            -row["active_weekday_pct"],
            -row["rolling4_positive_pct"],
            -row["net"],
        )
    )
    return rows


def csv_safe(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "name",
        "state_rule",
        "state_decision",
        "signals",
        "wr",
        "wl",
        "stress_030_wl",
        "active_weekday_pct",
        "positive_week_pct",
        "positive_active_week_pct",
        "active_week_pct",
        "pf",
        "net",
        "dd",
        "worst_week",
        "rolling4_positive_pct",
        "positive_month_pct",
        "worst_month",
        "june_2026",
        "top100_removed_net",
        "top200_removed_net",
        "last12_wr",
        "last12_wl",
        "last12_active_weekday_pct",
        "selected_addon_signals",
        "blocked_baseline_signals",
    ]
    return {field: row.get(field) for field in fields}


def write_compact_results(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_safe(rows[0]).keys()) if rows else [])
        writer.writeheader()
        for row in rows:
            writer.writerow(csv_safe(row))


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Weekly-State Red-Week Rescue Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: offline diagnostic over existing exact-MT5 ledgers only. No live/demo MT5 runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Question: can a causal weekly state rule move the book toward `70-80%` positive calendar weeks while keeping about `90%` active weekdays?",
        "",
        "State rules tested:",
        "",
        "- current-week closed baseline P&L drawdown gates for adding a smoother second book;",
        "- previous-week red gates for adding a smoother second book;",
        "- current-week closed-P&L risk-off gates for all baseline trades and H4/D1-only baseline trades;",
        "- fixed add-on weights `0.5x`, `1x`, `2x`, `3x`, `5x`.",
        "",
        "## Best Rows",
        "",
        "| Rank | Portfolio | State rule | Decision | Signals | WR% | W/L | Stress W/L | Active% | Positive weeks% | PF | Net | Worst week | Rolling 4w+% | June 2026 |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in enumerate(payload["top_rows"][:20], start=1):
        lines.append(
            f"| {idx} | `{row['name']}` | `{row.get('state_rule', '')}` | `{row.get('state_decision', '')}` | "
            f"{row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['active_weekday_pct']:.2f} | {row['positive_week_pct']:.2f} | {row['pf'] or 0.0:.4f} | "
            f"{row['net']:.2f} | {row['worst_week']:.2f} | {row['rolling4_positive_pct']:.2f} | {row['june_2026']:.2f} |"
        )

    best = payload.get("best_row", {})
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Best row: `{best.get('name', '')}`.",
            f"- Positive calendar weeks: `{best.get('positive_week_pct', 0.0):.2f}%`.",
            f"- Active weekdays: `{best.get('active_weekday_pct', 0.0):.2f}%`.",
            f"- W/L: `{(best.get('wl') or 0.0):.4f}`; stressed W/L: `{(best.get('stress_030_wl') or 0.0):.4f}`.",
            f"- Decision: `{best.get('state_decision', '')}`.",
            "",
            "Rows remain diagnostic only. Any promising rule would still need conversion to exact MT5 and a frozen rerun before review.",
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
    baseline, baseline_exit_stats = ensure_exit_times(normalize_baseline())
    baseline_state = build_week_state_index(baseline)
    baseline_week_net = week_nets(baseline)
    second_books, source_meta = load_second_books()
    selected_books, standalone_scores = select_candidate_books(second_books)

    evaluations: list[dict[str, Any]] = []
    base = evaluate_portfolio("baseline_f67_h16_no_f33", baseline, dedupe=False)
    base["state_rule"] = "baseline"
    base["selected_addon_signals"] = 0
    base["blocked_baseline_signals"] = 0
    evaluations.append(base)

    for threshold in THRESHOLDS:
        for h4_only in (False, True):
            kept, blocked = filter_baseline_riskoff(baseline, threshold, h4_only=h4_only)
            label = "h4_only" if h4_only else "all"
            result = evaluate_portfolio(f"baseline_riskoff_{label}_t{abs(int(threshold))}", kept, dedupe=False)
            result["state_rule"] = f"riskoff_{label}_current_week_pnl_le_{threshold}"
            result["selected_addon_signals"] = 0
            result["blocked_baseline_signals"] = blocked
            evaluations.append(result)

    for name, rows in selected_books.items():
        current_week_selected: dict[float, list[dict[str, Any]]] = {}
        for threshold in THRESHOLDS:
            selected = select_current_week_drawdown_addon(rows, baseline_state, threshold)
            if len(selected) >= 100:
                current_week_selected[threshold] = selected

        previous_week_selected = {
            1: select_previous_week_red_addon(rows, baseline_week_net, 1),
            2: select_previous_week_red_addon(rows, baseline_week_net, 2),
        }

        for threshold, selected in current_week_selected.items():
            for weight in WEIGHTS:
                scaled = weighted_rows(selected, weight)
                suffix = str(weight).replace(".", "p")
                result = evaluate_portfolio(
                    f"baseline_plus_{name}_cwdn{abs(int(threshold))}_x{suffix}",
                    baseline + scaled,
                    dedupe=True,
                )
                result["state_rule"] = f"addon_when_current_week_baseline_closed_pnl_le_{threshold}"
                result["selected_addon_signals"] = len(selected)
                result["blocked_baseline_signals"] = 0
                evaluations.append(result)

        for lookback, selected in previous_week_selected.items():
            if len(selected) < 100:
                continue
            for weight in WEIGHTS:
                scaled = weighted_rows(selected, weight)
                suffix = str(weight).replace(".", "p")
                result = evaluate_portfolio(
                    f"baseline_plus_{name}_prev{lookback}wred_x{suffix}",
                    baseline + scaled,
                    dedupe=True,
                )
                result["state_rule"] = f"addon_when_previous_{lookback}_week_net_red"
                result["selected_addon_signals"] = len(selected)
                result["blocked_baseline_signals"] = 0
                evaluations.append(result)

    ranked = rank_rows(evaluations)
    best = ranked[0] if ranked else {}

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    best_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv"
    best_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv"

    if best:
        write_signal_csv(best_kept_csv, best["kept_rows"])
        write_signal_csv(best_dropped_csv, best["dropped_rows"])

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "results_csv": rel(results_csv),
        "best_kept_csv": rel(best_kept_csv),
        "best_dropped_csv": rel(best_dropped_csv),
    }
    payload = {
        "status": "WEEKLY_STATE_RESCUE_DIAGNOSTIC_COMPLETE" if ranked else "NO_RESULTS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "boundary": "offline_existing_exact_mt5_ledgers_no_runtime_change",
        "targets": {
            "positive_week_pct_low": TARGET_LOW,
            "positive_week_pct_high": TARGET_HIGH,
            "active_weekday_pct": TARGET_ACTIVITY,
        },
        "baseline_csv": rel(BASELINE_KEPT),
        "source_meta": {
            **source_meta,
            "baseline_exit_stats": baseline_exit_stats,
            "candidate_books_tested": len(selected_books),
            "standalone_book_scores": [strip_heavy(row) for row in standalone_scores[:MAX_BOOKS]],
            "thresholds": THRESHOLDS,
            "weights": WEIGHTS,
        },
        "best_row": strip_heavy(best) if best else {},
        "top_rows": [strip_heavy(row) for row in ranked[:50]],
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_compact_results(results_csv, ranked)
    report_md.write_text(render(payload), encoding="utf-8")

    print(report_md)
    if best:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "best": best["name"],
                    "state_rule": best["state_rule"],
                    "decision": best["state_decision"],
                    "positive_week_pct": best["positive_week_pct"],
                    "active_weekday_pct": best["active_weekday_pct"],
                    "wr": best["wr"],
                    "wl": best["wl"],
                    "stress_030_wl": best["stress_030_wl"],
                    "net": best["net"],
                    "june_2026": best["june_2026"],
                },
                indent=2,
            )
        )
    return 0 if ranked else 1


if __name__ == "__main__":
    raise SystemExit(main())
