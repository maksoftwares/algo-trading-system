from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    MARKET_DAYS,
    PHASE1_ROOT,
    REPORTS_DIR,
    REPO_ROOT,
    build_source_specs,
    dedupe_signals,
    load_sources,
    rel,
    sha256_file,
    summary_metrics,
)


OUTPUT_STEM = "A1_XAU_HYBRID_COMPANION_ACTIVITY_SEARCH_2026_07_05"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
PREREG_PATH = (
    PHASE1_ROOT / "docs" / "A1_XAU_HYBRID_COMPANION_ACTIVITY_SEARCH_PREREG_2026_07_05.md"
)

SKIP_SOURCE_IDS = {
    # The current baseline already contains the exact F67-H16 frequency branch plus H4/D1 long rows.
    # Older step1 cells are same-family management alternatives and should not be used as fresh cadence proof.
    "step1_f33_r30_be_1r",
    "step1_f33_r30_be_never",
    "step1_f67_r20_be_tp1",
}


def parse_dt(value: Any) -> datetime:
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(text)


def read_signal_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for ordinal, row in enumerate(reader, start=2):
            entry_time = parse_dt(row["entry_time"])
            entry_date = entry_time.date()
            rows.append(
                {
                    "source_id": str(row.get("source_id") or row.get("component") or "baseline"),
                    "family_group": str(row.get("family_group") or "baseline"),
                    "source_priority": int(float(row.get("source_priority") or 10)),
                    "entry_time": entry_time,
                    "entry_date": entry_date,
                    "direction": str(row.get("direction") or "").upper(),
                    "pnl_usd": float(row.get("pnl_usd") or row.get("signal_pnl_usd") or 0.0),
                    "tickets": int(float(row.get("tickets") or 1)),
                    "lots": float(row.get("lots") or row.get("volume") or 0.0),
                    "component": str(row.get("component") or row.get("source_id") or "baseline"),
                    "source_csv": str(row.get("source_csv") or path),
                    "source_row": int(float(row.get("source_row") or ordinal)),
                }
            )
    return rows


def row_hour(row: dict[str, Any]) -> int:
    return int(row["entry_time"].hour)


def row_weekday(row: dict[str, Any]) -> int:
    return int(row["entry_time"].weekday())


def row_month(row: dict[str, Any]) -> int:
    return int(row["entry_time"].month)


def last12_subset(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    day_set = set(LAST12_MARKET_DAYS)
    return [row for row in rows if row["entry_date"] in day_set]


def decision(metrics: dict[str, Any]) -> str:
    wr = float(metrics.get("win_rate_pct") or 0.0)
    wl = float(metrics.get("avg_win_loss") or 0.0)
    active = float(metrics.get("active_weekday_pct") or 0.0)
    stress_wl = float(metrics.get("stress_030_avg_win_loss") or 0.0)
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0 and stress_wl >= 2.0:
        return "OWNER_SHAPE_AND_STRESS_HIT_DIAGNOSTIC"
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0:
        return "OWNER_SHAPE_ACTIVITY_HIT_STRESS_GAP_DIAGNOSTIC"
    if wr >= 50.0 and wl >= 2.0:
        return "CORE_SHAPE_ACTIVITY_GAP"
    if active >= 90.0 and wr >= 50.0:
        return "ACTIVITY_HIT_PAYOUT_GAP"
    if active >= 90.0 and wl >= 2.0:
        return "ACTIVITY_HIT_WR_GAP"
    return "NO_OWNER_SHAPE"


def score(row: dict[str, Any]) -> float:
    return round(
        min(float(row.get("active_weekday_pct") or 0.0) / 90.0, 1.15) * 375.0
        + min(float(row.get("win_rate_pct") or 0.0) / 50.0, 1.2) * 275.0
        + min(float(row.get("avg_win_loss") or 0.0) / 2.0, 1.25) * 275.0
        + min(float(row.get("new_active_weekdays") or 0.0) / 40.0, 1.5) * 75.0
        + min(float(row.get("net_usd") or 0.0) / 20000.0, 1.5) * 50.0,
        4,
    )


def candidate_filters(rows: list[dict[str, Any]]) -> list[tuple[str, Callable[[dict[str, Any]], bool]]]:
    filters: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [("all", lambda row: True)]
    directions = sorted({row["direction"] for row in rows if row.get("direction")})
    hours = sorted({row_hour(row) for row in rows})
    weekdays = sorted({row_weekday(row) for row in rows})
    months = sorted({row_month(row) for row in rows})

    for direction in directions:
        filters.append((f"direction={direction}", lambda row, direction=direction: row["direction"] == direction))
    for hour in hours:
        filters.append((f"hour={hour:02d}", lambda row, hour=hour: row_hour(row) == hour))
    for weekday in weekdays:
        filters.append((f"weekday={weekday}", lambda row, weekday=weekday: row_weekday(row) == weekday))
    for month in months:
        filters.append((f"month={month:02d}", lambda row, month=month: row_month(row) == month))
    for direction in directions:
        for hour in hours:
            filters.append(
                (
                    f"direction={direction};hour={hour:02d}",
                    lambda row, direction=direction, hour=hour: row["direction"] == direction
                    and row_hour(row) == hour,
                )
            )
    for direction in directions:
        for weekday in weekdays:
            filters.append(
                (
                    f"direction={direction};weekday={weekday}",
                    lambda row, direction=direction, weekday=weekday: row["direction"] == direction
                    and row_weekday(row) == weekday,
                )
            )
    return filters


def evaluate(
    baseline: list[dict[str, Any]],
    baseline_days: set[date],
    source_id: str,
    filter_id: str,
    candidate_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    raw = baseline + candidate_rows
    kept, dropped = dedupe_signals(raw)
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    stress_030 = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    last12 = summary_metrics(last12_subset(kept), market_days=LAST12_MARKET_DAYS)
    active_days = {row["entry_date"] for row in kept}
    selected_days = {row["entry_date"] for row in candidate_rows}
    metrics.update(
        {
            "source_id": source_id,
            "filter_id": filter_id,
            "candidate_rows": len(candidate_rows),
            "candidate_active_weekdays": len(selected_days.intersection(set(MARKET_DAYS))),
            "new_active_weekdays": len(active_days.difference(baseline_days).intersection(set(MARKET_DAYS))),
            "dropped_overlap_signals": len(dropped),
            "stress_030_net_usd": stress_030["net_usd"],
            "stress_030_avg_win_loss": stress_030["avg_win_loss"],
            "last12_signals": last12["signals"],
            "last12_win_rate_pct": last12["win_rate_pct"],
            "last12_avg_win_loss": last12["avg_win_loss"],
            "last12_active_weekday_pct": last12["active_weekday_pct"],
        }
    )
    metrics["decision"] = decision(metrics)
    metrics["score"] = score(metrics)
    return metrics, kept, dropped


def write_csv(path: Path, rows: list[dict[str, Any]], keys: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def signal_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "source_id",
        "family_group",
        "source_priority",
        "entry_time",
        "entry_date",
        "direction",
        "pnl_usd",
        "tickets",
        "lots",
        "component",
        "source_csv",
        "source_row",
        "drop_reason",
        "duplicate_of_source_id",
        "duplicate_of_entry_time",
    ]
    serializable: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["entry_time"] = item["entry_time"].isoformat(sep=" ")
        item["entry_date"] = item["entry_date"].isoformat()
        serializable.append(item)
    write_csv(path, serializable, keys)


def render_markdown(payload: dict[str, Any]) -> str:
    baseline = payload["baseline"]
    best = payload["best_row"]
    top_rows = payload["top_rows"][:20]
    lines = [
        "# A1 XAU Hybrid Companion Activity Search",
        "",
        f"Generated UTC: `{payload['generated_utc']}`",
        "",
        "Scope: exact-ledger diagnostic only. It reuses already-realized MT5 Strategy Tester trade/signal CSVs and applies simple component/direction/hour/weekday/month filters. No MT5 launch, live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Preregistration: `{rel(PREREG_PATH)}`",
        f"Baseline kept CSV: `{rel(BASELINE_KEPT)}`",
        "",
        "## Baseline",
        "",
        "| Signals | WR% | W/L | Active% | PF | Net USD | Stress -0.30 W/L |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        "| {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {profit_factor:.4f} | {net_usd:.2f} | {stress_030_avg_win_loss:.4f} |".format(
            **baseline
        ),
        "",
        "## Best Companion Diagnostic",
        "",
        "| Decision | Source | Filter | Signals | WR% | W/L | Active% | New Days | PF | Net USD | Stress -0.30 W/L | Last12 WR/WL/Active |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        "| `{decision}` | `{source_id}` | `{filter_id}` | {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {new_active_weekdays} | {profit_factor:.4f} | {net_usd:.2f} | {stress_030_avg_win_loss:.4f} | {last12_win_rate_pct:.2f}/{last12_avg_win_loss:.4f}/{last12_active_weekday_pct:.2f} |".format(
            **best
        ),
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Source | Filter | Candidate Rows | New Days | WR% | W/L | Active% | Net | Stress W/L |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(top_rows, start=1):
        lines.append(
            "| {index} | `{decision}` | `{source_id}` | `{filter_id}` | {candidate_rows} | {new_active_weekdays} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {net_usd:.2f} | {stress_030_avg_win_loss:.4f} |".format(
                index=index, **row
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "## Artifacts",
            "",
            f"- rows_csv: `{rel(REPORTS_DIR / (OUTPUT_STEM + '.csv'))}`",
            f"- best_kept_csv: `{rel(REPORTS_DIR / (OUTPUT_STEM + '_BEST_KEPT.csv'))}`",
            f"- best_dropped_csv: `{rel(REPORTS_DIR / (OUTPUT_STEM + '_BEST_DROPPED.csv'))}`",
            f"- json: `{rel(REPORTS_DIR / (OUTPUT_STEM + '.json'))}`",
            f"- md: `{rel(REPORTS_DIR / (OUTPUT_STEM + '.md'))}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    generated = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    baseline = read_signal_csv(BASELINE_KEPT)
    baseline_metrics = summary_metrics(baseline, market_days=MARKET_DAYS)
    baseline_stress = summary_metrics(baseline, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    baseline_metrics["stress_030_avg_win_loss"] = baseline_stress["avg_win_loss"]
    baseline_days = {row["entry_date"] for row in baseline}

    specs = [spec for spec in build_source_specs() if spec.source_id not in SKIP_SOURCE_IDS]
    sources, inventory = load_sources(specs)

    rows: list[dict[str, Any]] = []
    best_kept: list[dict[str, Any]] = []
    best_dropped: list[dict[str, Any]] = []
    for spec in specs:
        source_rows = sources.get(spec.source_id, [])
        if not source_rows:
            continue
        for filter_id, predicate in candidate_filters(source_rows):
            selected = [row for row in source_rows if predicate(row)]
            if len(selected) < 10:
                continue
            metrics, kept, dropped = evaluate(baseline, baseline_days, spec.source_id, filter_id, selected)
            if metrics["new_active_weekdays"] < 5:
                continue
            rows.append(metrics)
            if not best_kept or metrics["score"] > rows[-2]["score"] if len(rows) > 1 else True:
                best_kept = kept
                best_dropped = dropped

    rows.sort(
        key=lambda row: (
            row["decision"] in {"OWNER_SHAPE_AND_STRESS_HIT_DIAGNOSTIC", "OWNER_SHAPE_ACTIVITY_HIT_STRESS_GAP_DIAGNOSTIC"},
            float(row.get("avg_win_loss") or 0.0) >= 2.0,
            float(row.get("win_rate_pct") or 0.0) >= 50.0,
            float(row.get("active_weekday_pct") or 0.0),
            float(row.get("score") or 0.0),
        ),
        reverse=True,
    )
    best_row = rows[0] if rows else {}

    # Recompute the best kept/dropped after sorting; this keeps the exported ledger tied to the report winner.
    if best_row:
        best_source = next(spec for spec in specs if spec.source_id == best_row["source_id"])
        selected = [
            row
            for row in sources[best_source.source_id]
            if any(
                label == best_row["filter_id"] and predicate(row)
                for label, predicate in candidate_filters(sources[best_source.source_id])
            )
        ]
        _, best_kept, best_dropped = evaluate(
            baseline,
            baseline_days,
            best_source.source_id,
            str(best_row["filter_id"]),
            selected,
        )

    if best_row and best_row["decision"].startswith("OWNER_SHAPE"):
        interpretation = (
            "A diagnostic companion row reaches the owner WR/W-L/activity shape from already-realized exact MT5 ledgers. "
            "This is not demo-ready yet because the filter was searched post hoc; next step is a preregistered exact MT5 rerun with the filter implemented in tester inputs."
        )
    else:
        interpretation = (
            "No simple exact-ledger companion filter simultaneously solved the activity gap and preserved the owner WR/W-L shape. "
            "The search confirms the bottleneck: extra cadence is available, but it usually pulls W/L under 2.0 or WR under 50. Continue with a new source family or a preregistered anti-poison gate, not reviewer spend."
        )

    payload = {
        "generated_utc": generated,
        "baseline": baseline_metrics,
        "best_row": best_row,
        "top_rows": rows[:50],
        "row_count": len(rows),
        "source_inventory": inventory,
        "interpretation": interpretation,
        "baseline_csv": str(BASELINE_KEPT),
        "baseline_sha256": sha256_file(BASELINE_KEPT),
    }

    csv_keys = [
        "decision",
        "score",
        "source_id",
        "filter_id",
        "candidate_rows",
        "candidate_active_weekdays",
        "new_active_weekdays",
        "signals",
        "wins",
        "losses",
        "win_rate_pct",
        "avg_win_loss",
        "active_weekdays",
        "active_weekday_pct",
        "profit_factor",
        "net_usd",
        "max_closed_drawdown_usd",
        "top25_removed_net_usd",
        "top100_removed_net_usd",
        "stress_030_net_usd",
        "stress_030_avg_win_loss",
        "last12_signals",
        "last12_win_rate_pct",
        "last12_avg_win_loss",
        "last12_active_weekday_pct",
        "dropped_overlap_signals",
    ]
    write_csv(REPORTS_DIR / f"{OUTPUT_STEM}.csv", rows, csv_keys)
    if best_kept:
        signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv", best_kept)
    if best_dropped:
        signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv", best_dropped)
    (REPORTS_DIR / f"{OUTPUT_STEM}.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (REPORTS_DIR / f"{OUTPUT_STEM}.md").write_text(render_markdown(payload), encoding="utf-8")

    print(json.dumps({"output": str(REPORTS_DIR / f"{OUTPUT_STEM}.md"), "best": best_row}, indent=2, default=str))


if __name__ == "__main__":
    main()
