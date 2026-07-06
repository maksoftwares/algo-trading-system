from __future__ import annotations

import csv
import itertools
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_hybrid_companion_activity_search import (
    BASELINE_KEPT,
    OUTPUT_STEM as SINGLE_OUTPUT_STEM,
    SKIP_SOURCE_IDS,
    candidate_filters,
    read_signal_csv,
)
from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    MARKET_DAYS,
    PHASE1_ROOT,
    REPORTS_DIR,
    build_source_specs,
    dedupe_signals,
    load_sources,
    rel,
    summary_metrics,
)


OUTPUT_STEM = "A1_XAU_HYBRID_COMPANION_COMBO_SEARCH_2026_07_05"
PREREG_PATH = PHASE1_ROOT / "docs" / "A1_XAU_HYBRID_COMPANION_ACTIVITY_SEARCH_PREREG_2026_07_05.md"
MAX_POOL = 18
MAX_COMBO_SIZE = 3


def last12_subset(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    day_set = set(LAST12_MARKET_DAYS)
    return [row for row in rows if row["entry_date"] in day_set]


def decision(row: dict[str, Any]) -> str:
    wr = float(row.get("win_rate_pct") or 0.0)
    wl = float(row.get("avg_win_loss") or 0.0)
    active = float(row.get("active_weekday_pct") or 0.0)
    stress_wl = float(row.get("stress_030_avg_win_loss") or 0.0)
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0 and stress_wl >= 2.0:
        return "OWNER_SHAPE_AND_STRESS_HIT_DIAGNOSTIC"
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0:
        return "OWNER_SHAPE_ACTIVITY_HIT_STRESS_GAP_DIAGNOSTIC"
    if wr >= 50.0 and wl >= 2.0:
        return "CORE_SHAPE_ACTIVITY_GAP"
    if active >= 90.0 and wl >= 2.0:
        return "ACTIVITY_HIT_WR_GAP"
    if active >= 90.0 and wr >= 50.0:
        return "ACTIVITY_HIT_PAYOUT_GAP"
    return "NO_OWNER_SHAPE"


def score(row: dict[str, Any]) -> float:
    return round(
        min(float(row.get("active_weekday_pct") or 0.0) / 90.0, 1.15) * 390.0
        + min(float(row.get("win_rate_pct") or 0.0) / 50.0, 1.2) * 280.0
        + min(float(row.get("avg_win_loss") or 0.0) / 2.0, 1.25) * 280.0
        + min(float(row.get("new_active_weekdays") or 0.0) / 40.0, 1.5) * 80.0
        + min(float(row.get("net_usd") or 0.0) / 20000.0, 1.5) * 45.0,
        4,
    )


def filter_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["source_id"]), str(row["filter_id"])


def selected_identity(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["source_id"]), int(row.get("source_row") or 0)


def evaluate(
    baseline: list[dict[str, Any]],
    baseline_days: set,
    filter_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    unique: dict[tuple[str, int], dict[str, Any]] = {}
    for row in filter_rows:
        unique[selected_identity(row)] = row
    kept, dropped = dedupe_signals(baseline + list(unique.values()))
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    stress_030 = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    last12 = summary_metrics(last12_subset(kept), market_days=LAST12_MARKET_DAYS)
    active_days = {row["entry_date"] for row in kept}
    metrics.update(
        {
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
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["entry_time"] = item["entry_time"].isoformat(sep=" ")
        item["entry_date"] = item["entry_date"].isoformat()
        out.append(item)
    write_csv(path, out, keys)


def render(payload: dict[str, Any]) -> str:
    best = payload["best_row"]
    lines = [
        "# A1 XAU Hybrid Companion Combo Search",
        "",
        f"Generated UTC: `{payload['generated_utc']}`",
        "",
        "Scope: exact-ledger diagnostic only. It combines the best simple companion filters from existing MT5 Strategy Tester ledgers. No MT5 launch, runtime attach, chart, preset, order, position, or broker state was changed.",
        "",
        f"Shared preregistration: `{rel(PREREG_PATH)}`",
        f"Single-filter seed report: `{rel(REPORTS_DIR / (SINGLE_OUTPUT_STEM + '.md'))}`",
        "",
        "## Best Combo",
        "",
        "| Decision | Filters | Signals | WR% | W/L | Active% | New Days | PF | Net USD | Stress -0.30 W/L | Last12 WR/WL/Active |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        "| `{decision}` | `{combo_id}` | {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {new_active_weekdays} | {profit_factor:.4f} | {net_usd:.2f} | {stress_030_avg_win_loss:.4f} | {last12_win_rate_pct:.2f}/{last12_avg_win_loss:.4f}/{last12_active_weekday_pct:.2f} |".format(
            **best
        ),
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Filters | New Days | WR% | W/L | Active% | Net | Stress W/L |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(payload["top_rows"][:20], start=1):
        lines.append(
            "| {index} | `{decision}` | `{combo_id}` | {new_active_weekdays} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {net_usd:.2f} | {stress_030_avg_win_loss:.4f} |".format(
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
        ]
    )
    return "\n".join(lines)


def main() -> None:
    generated = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    baseline = read_signal_csv(BASELINE_KEPT)
    baseline_days = {row["entry_date"] for row in baseline}
    specs = [spec for spec in build_source_specs() if spec.source_id not in SKIP_SOURCE_IDS]
    sources, _ = load_sources(specs)

    pool: list[dict[str, Any]] = []
    selected_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for spec in specs:
        source_rows = sources.get(spec.source_id, [])
        for filter_id, predicate in candidate_filters(source_rows):
            selected = [row for row in source_rows if predicate(row)]
            if len(selected) < 10:
                continue
            metrics, _, _ = evaluate(baseline, baseline_days, selected)
            if metrics["new_active_weekdays"] < 3:
                continue
            if (
                metrics["active_weekday_pct"] >= 90.0
                or metrics["avg_win_loss"] >= 1.95
                or metrics["win_rate_pct"] >= 49.75
            ):
                item = {
                    "source_id": spec.source_id,
                    "filter_id": filter_id,
                    "seed_score": metrics["score"],
                    "seed_new_days": metrics["new_active_weekdays"],
                    "seed_wr": metrics["win_rate_pct"],
                    "seed_wl": metrics["avg_win_loss"],
                    "seed_active": metrics["active_weekday_pct"],
                }
                pool.append(item)
                selected_by_key[filter_key(item)] = selected

    pool.sort(
        key=lambda row: (
            row["seed_active"] >= 90.0,
            row["seed_wl"] >= 2.0,
            row["seed_wr"] >= 50.0,
            row["seed_new_days"],
            row["seed_score"],
        ),
        reverse=True,
    )
    pool = pool[:MAX_POOL]

    rows: list[dict[str, Any]] = []
    best_kept: list[dict[str, Any]] = []
    best_dropped: list[dict[str, Any]] = []
    for size in range(2, MAX_COMBO_SIZE + 1):
        for combo in itertools.combinations(pool, size):
            source_ids = [row["source_id"] for row in combo]
            if len(source_ids) != len(set(source_ids)):
                continue
            combo_rows: list[dict[str, Any]] = []
            for item in combo:
                combo_rows.extend(selected_by_key[filter_key(item)])
            metrics, kept, dropped = evaluate(baseline, baseline_days, combo_rows)
            metrics["combo_id"] = " + ".join(f"{item['source_id']}[{item['filter_id']}]" for item in combo)
            metrics["filter_count"] = size
            metrics["candidate_rows"] = len(combo_rows)
            rows.append(metrics)

    rows.sort(
        key=lambda row: (
            row["decision"] in {"OWNER_SHAPE_AND_STRESS_HIT_DIAGNOSTIC", "OWNER_SHAPE_ACTIVITY_HIT_STRESS_GAP_DIAGNOSTIC"},
            row["avg_win_loss"] >= 2.0,
            row["win_rate_pct"] >= 50.0,
            row["active_weekday_pct"],
            row["score"],
        ),
        reverse=True,
    )
    best = rows[0] if rows else {}
    if best:
        best_items = []
        for token in str(best["combo_id"]).split(" + "):
            source_id, rest = token.split("[", 1)
            filter_id = rest[:-1]
            best_items.append({"source_id": source_id, "filter_id": filter_id})
        best_rows: list[dict[str, Any]] = []
        for item in best_items:
            best_rows.extend(selected_by_key[(item["source_id"], item["filter_id"])])
        _, best_kept, best_dropped = evaluate(baseline, baseline_days, best_rows)

    if best and str(best.get("decision", "")).startswith("OWNER_SHAPE"):
        interpretation = "A searched combo reaches the owner shape on exact ledgers. It is a rerun candidate only, not a demo spec, because the filter combo was selected post hoc."
    else:
        interpretation = "No small combo of exact-ledger companion filters reaches WR >=50%, W/L >=2.0, and active weekdays >=90%. Frequency can be bought, but the available exact sources still buy it with win-rate damage."

    payload = {
        "generated_utc": generated,
        "best_row": best,
        "top_rows": rows[:50],
        "pool": pool,
        "row_count": len(rows),
        "interpretation": interpretation,
    }
    keys = [
        "decision",
        "score",
        "combo_id",
        "filter_count",
        "candidate_rows",
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
        "stress_030_avg_win_loss",
        "last12_win_rate_pct",
        "last12_avg_win_loss",
        "last12_active_weekday_pct",
    ]
    write_csv(REPORTS_DIR / f"{OUTPUT_STEM}.csv", rows, keys)
    if best_kept:
        signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv", best_kept)
    if best_dropped:
        signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv", best_dropped)
    (REPORTS_DIR / f"{OUTPUT_STEM}.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (REPORTS_DIR / f"{OUTPUT_STEM}.md").write_text(render(payload), encoding="utf-8")
    print(json.dumps({"output": str(REPORTS_DIR / f"{OUTPUT_STEM}.md"), "best": best}, indent=2, default=str))


if __name__ == "__main__":
    main()
