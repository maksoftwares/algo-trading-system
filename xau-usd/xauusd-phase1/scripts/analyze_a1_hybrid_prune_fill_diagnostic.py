from __future__ import annotations

import csv
import itertools
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from analyze_a1_hybrid_v7_v11_antipoison_gate_diagnostic import (
    LAST12_MARKET_DAYS,
    MARKET_DAYS,
    PHASE1_ROOT,
    REPORTS_DIR,
    SOURCES,
    VALIDATION_DAYS,
    gate_candidates,
    metric_book,
    read_source,
    rel,
    selected_identity,
)
from analyze_a1_owner_goal_step3_portfolio_composition import dedupe_signals, sha256_file, summary_metrics


OUTPUT_STEM = "A1_XAU_HYBRID_PRUNE_FILL_DIAGNOSTIC_2026_07_05"
PREREG_PATH = PHASE1_ROOT / "docs" / "A1_XAU_HYBRID_PRUNE_FILL_DIAGNOSTIC_PREREG_2026_07_05.md"
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
FILL_POOL_LIMIT = 8
PRUNE_COMBO_LIMIT = 0


def parse_dt(value: Any) -> datetime:
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(text)


def read_baseline_full() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with BASELINE_KEPT.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for ordinal, row in enumerate(reader, start=2):
            entry_time = parse_dt(row["entry_time"])
            rows.append(
                {
                    "source_id": row.get("source_id") or "baseline",
                    "family_group": row.get("family_group") or "baseline",
                    "source_priority": int(float(row.get("source_priority") or 10)),
                    "entry_time": entry_time,
                    "entry_date": entry_time.date(),
                    "direction": str(row.get("direction") or "").upper(),
                    "pnl_usd": float(row.get("pnl_usd") or 0.0),
                    "tickets": int(float(row.get("tickets") or 1)),
                    "lots": float(row.get("lots") or 0.0),
                    "component": row.get("component") or row.get("source_id") or "baseline",
                    "source_csv": row.get("source_csv") or str(BASELINE_KEPT),
                    "source_row": int(float(row.get("source_row") or ordinal)),
                    "variant_name": row.get("variant_name") or row.get("component") or "",
                    "entry_hour": entry_time.hour,
                    "weekday": entry_time.weekday(),
                    "month": entry_time.month,
                }
            )
    return rows


def subset_rows(rows: list[dict[str, Any]], day_set: set[date]) -> list[dict[str, Any]]:
    return [row for row in rows if row["entry_date"] in day_set]


def decision(row: dict[str, Any]) -> str:
    wr = float(row.get("win_rate_pct") or 0.0)
    wl = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    validation_wr = float(row.get("validation_win_rate_pct") or 0.0)
    validation_wl = float(row.get("validation_avg_win_loss") or 0.0)
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0 and validation_wr >= 48.0 and validation_wl >= 1.85:
        return "DIAGNOSTIC_REPLAY_CANDIDATE"
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0:
        return "DIAGNOSTIC_FULL_HIT_VALIDATION_WEAK"
    if wr >= 50.0 and wl >= 2.0:
        return "CORE_SHAPE_ACTIVITY_GAP"
    if active >= 90.0 and wl >= 2.0:
        return "ACTIVITY_HIT_WR_GAP"
    return "NO_OWNER_SHAPE"


def score(row: dict[str, Any]) -> float:
    return round(
        min(float(row.get("win_rate_pct") or 0.0) / 50.0, 1.2) * 310
        + min(float(row.get("avg_win_loss") or 0.0) / 2.0, 1.25) * 310
        + min(float(row.get("active_weekday_pct") or 0.0) / 90.0, 1.15) * 310
        + min(float(row.get("validation_win_rate_pct") or 0.0) / 50.0, 1.2) * 80,
        4,
    )


def prune_candidates(baseline: list[dict[str, Any]]) -> list[tuple[str, Callable[[dict[str, Any]], bool]]]:
    rows = [row for row in baseline if row["source_id"] == "freq_step3_frontier"]
    candidates: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [("no_prune", lambda row: False)]
    for variant in sorted({str(row["variant_name"]) for row in rows}):
        candidates.append((f"block_variant={variant}", lambda row, variant=variant: row["source_id"] == "freq_step3_frontier" and row["variant_name"] == variant))
    for hour in sorted({int(row["entry_hour"]) for row in rows}):
        candidates.append((f"block_hour={hour:02d}", lambda row, hour=hour: row["source_id"] == "freq_step3_frontier" and row["entry_hour"] == hour))
    for weekday in sorted({int(row["weekday"]) for row in rows}):
        candidates.append((f"block_weekday={weekday}", lambda row, weekday=weekday: row["source_id"] == "freq_step3_frontier" and row["weekday"] == weekday))
    for month in sorted({int(row["month"]) for row in rows}):
        candidates.append((f"block_month={month:02d}", lambda row, month=month: row["source_id"] == "freq_step3_frontier" and row["month"] == month))
    for direction in sorted({str(row["direction"]) for row in rows}):
        candidates.append((f"block_direction={direction}", lambda row, direction=direction: row["source_id"] == "freq_step3_frontier" and row["direction"] == direction))
    variant_hours = sorted({(str(row["variant_name"]), int(row["entry_hour"])) for row in rows})
    for variant, hour in variant_hours:
        candidates.append(
            (
                f"block_variant_hour={variant}|{hour:02d}",
                lambda row, variant=variant, hour=hour: row["source_id"] == "freq_step3_frontier"
                and row["variant_name"] == variant
                and row["entry_hour"] == hour,
            )
        )
    return candidates


def apply_prunes(
    baseline: list[dict[str, Any]],
    prunes: tuple[tuple[str, Callable[[dict[str, Any]], bool]], ...],
) -> list[dict[str, Any]]:
    return [row for row in baseline if not any(predicate(row) for _, predicate in prunes)]


def evaluate(
    baseline: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    baseline_days: set[date],
    prune_id: str,
    fill_id: str,
    removed_rows: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    kept, dropped = dedupe_signals(baseline + selected)
    full = summary_metrics(kept, market_days=MARKET_DAYS)
    stress = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    validation = metric_book(baseline, selected, VALIDATION_DAYS)
    last12 = metric_book(baseline, selected, LAST12_MARKET_DAYS)
    active_days = {row["entry_date"] for row in kept}
    row = {
        "prune_id": prune_id,
        "fill_id": fill_id,
        "removed_baseline_rows": removed_rows,
        "selected_fill_rows": len({selected_identity(row): row for row in selected}),
        "new_active_weekdays": len(active_days.difference(baseline_days).intersection(set(MARKET_DAYS))),
        **full,
        "stress_030_avg_win_loss": stress["avg_win_loss"],
        "stress_030_net_usd": stress["net_usd"],
        "validation_win_rate_pct": validation["win_rate_pct"],
        "validation_avg_win_loss": validation["avg_win_loss"],
        "validation_active_weekday_pct": validation["active_weekday_pct"],
        "last12_win_rate_pct": last12["win_rate_pct"],
        "last12_avg_win_loss": last12["avg_win_loss"],
        "last12_active_weekday_pct": last12["active_weekday_pct"],
        "dropped_overlap_signals": len(dropped),
    }
    row["decision"] = decision(row)
    row["score"] = score(row)
    return row, kept, dropped


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "decision",
        "score",
        "prune_id",
        "fill_id",
        "removed_baseline_rows",
        "selected_fill_rows",
        "new_active_weekdays",
        "signals",
        "win_rate_pct",
        "avg_win_loss",
        "active_weekday_pct",
        "profit_factor",
        "net_usd",
        "stress_030_avg_win_loss",
        "validation_win_rate_pct",
        "validation_avg_win_loss",
        "validation_active_weekday_pct",
        "last12_win_rate_pct",
        "last12_avg_win_loss",
        "last12_active_weekday_pct",
        "top25_removed_net_usd",
        "top100_removed_net_usd",
    ]
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
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["entry_time"] = item["entry_time"].isoformat(sep=" ")
        item["entry_date"] = item["entry_date"].isoformat()
        out.append(item)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out)


def render(payload: dict[str, Any]) -> str:
    best = payload["best_row"]
    lines = [
        "# A1 XAU Hybrid Prune-Fill Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_utc']}`",
        "",
        "Scope: diagnostic only. It applies categorical baseline prunes plus causal v7/v11 activity fills to exact ledgers. No MT5 launch, runtime attach, chart, preset, order, position, or broker state was changed.",
        "",
        f"Preregistration: `{rel(PREREG_PATH)}`",
        "",
        "## Best Row",
        "",
        "| Decision | Prune | Fill | Removed | Fill Rows | Signals | WR% | W/L | Active% | Validation WR/WL/Active | Last12 WR/WL/Active |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        "| `{decision}` | `{prune_id}` | `{fill_id}` | {removed_baseline_rows} | {selected_fill_rows} | {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {validation_win_rate_pct:.2f}/{validation_avg_win_loss:.4f}/{validation_active_weekday_pct:.2f} | {last12_win_rate_pct:.2f}/{last12_avg_win_loss:.4f}/{last12_active_weekday_pct:.2f} |".format(
            **best
        ),
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Prune | Fill | Removed | WR% | W/L | Active% | Validation WR/WL |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for index, row in enumerate(payload["top_rows"][:25], start=1):
        lines.append(
            "| {index} | `{decision}` | `{prune_id}` | `{fill_id}` | {removed_baseline_rows} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {validation_win_rate_pct:.2f}/{validation_avg_win_loss:.4f} |".format(
                index=index,
                **row,
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
        ]
    )
    return "\n".join(lines)


def main() -> None:
    generated = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    baseline = read_baseline_full()
    baseline_days = {row["entry_date"] for row in baseline}

    source_rows_by_id = {source.source_id: read_source(source) for source in SOURCES}
    fill_rows: list[dict[str, Any]] = []
    fill_selected: dict[str, list[dict[str, Any]]] = {}
    for source_id, source_rows in source_rows_by_id.items():
        for fill_id, selected in gate_candidates(source_id, source_rows):
            row, _, _ = evaluate(baseline, selected, baseline_days, "no_prune", fill_id, 0)
            if row["active_weekday_pct"] >= 89.5 or row["new_active_weekdays"] >= 35:
                fill_rows.append(row)
                fill_selected[fill_id] = selected
    fill_rows.sort(
        key=lambda row: (
            row["active_weekday_pct"],
            row["validation_win_rate_pct"],
            row["win_rate_pct"],
            row["avg_win_loss"],
        ),
        reverse=True,
    )
    fill_rows = fill_rows[:FILL_POOL_LIMIT]

    prune_pool = prune_candidates(baseline)
    rows: list[dict[str, Any]] = []
    best_kept: list[dict[str, Any]] = []
    best_dropped: list[dict[str, Any]] = []
    for fill in fill_rows:
        selected = fill_selected[fill["fill_id"]]
        for prune in prune_pool:
            pruned = apply_prunes(baseline, (prune,))
            row, kept, dropped = evaluate(pruned, selected, baseline_days, prune[0], fill["fill_id"], len(baseline) - len(pruned))
            rows.append(row)
    rows.sort(
        key=lambda row: (
            row["decision"] == "DIAGNOSTIC_REPLAY_CANDIDATE",
            row["decision"] == "DIAGNOSTIC_FULL_HIT_VALIDATION_WEAK",
            row["win_rate_pct"] >= 50.0 and row["avg_win_loss"] >= 2.0,
            row["active_weekday_pct"],
            row["score"],
        ),
        reverse=True,
    )

    # Pair-prune search is intentionally disabled in the quick pass. If a single prune cannot
    # move the frontier materially, a deeper exact rerun is not justified.
    if PRUNE_COMBO_LIMIT > 0:
        top_prunes = []
        for row in rows[:PRUNE_COMBO_LIMIT]:
            match = next((item for item in prune_pool if item[0] == row["prune_id"]), None)
            if match and match[0] != "no_prune" and match[0] not in {item[0] for item in top_prunes}:
                top_prunes.append(match)
        for fill in fill_rows[:10]:
            selected = fill_selected[fill["fill_id"]]
            for combo in itertools.combinations(top_prunes, 2):
                pruned = apply_prunes(baseline, combo)
                prune_id = " + ".join(item[0] for item in combo)
                row, kept, dropped = evaluate(pruned, selected, baseline_days, prune_id, fill["fill_id"], len(baseline) - len(pruned))
                rows.append(row)

    rows.sort(
        key=lambda row: (
            row["decision"] == "DIAGNOSTIC_REPLAY_CANDIDATE",
            row["decision"] == "DIAGNOSTIC_FULL_HIT_VALIDATION_WEAK",
            row["win_rate_pct"] >= 50.0 and row["avg_win_loss"] >= 2.0,
            row["active_weekday_pct"],
            row["score"],
        ),
        reverse=True,
    )
    best = rows[0]
    # Rebuild best ledger.
    best_prunes = []
    for token in best["prune_id"].split(" + "):
        match = next((item for item in prune_pool if item[0] == token), None)
        if match:
            best_prunes.append(match)
    best_baseline = apply_prunes(baseline, tuple(best_prunes))
    best_selected = fill_selected[best["fill_id"]]
    best_kept, best_dropped = dedupe_signals(best_baseline + best_selected)

    if best["decision"] == "DIAGNOSTIC_REPLAY_CANDIDATE":
        interpretation = "A prune-fill diagnostic reaches the owner shape and is worth considering for preregistered exact MT5 replay. It is not demo-ready evidence."
    else:
        interpretation = "No categorical prune-fill diagnostic reaches WR >=50%, W/L >=2.0, and active >=90%. Current baseline plus v7/v11 activity still cannot bridge the owner target."

    payload = {
        "generated_utc": generated,
        "best_row": best,
        "top_rows": rows[:75],
        "row_count": len(rows),
        "fill_pool": fill_rows,
        "interpretation": interpretation,
        "baseline_csv": str(BASELINE_KEPT),
        "baseline_sha256": sha256_file(BASELINE_KEPT),
    }
    write_csv(REPORTS_DIR / f"{OUTPUT_STEM}.csv", rows)
    signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv", best_kept)
    signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv", best_dropped)
    (REPORTS_DIR / f"{OUTPUT_STEM}.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (REPORTS_DIR / f"{OUTPUT_STEM}.md").write_text(render(payload), encoding="utf-8")
    print(json.dumps({"output": str(REPORTS_DIR / f"{OUTPUT_STEM}.md"), "best": best}, indent=2, default=str))


if __name__ == "__main__":
    main()
