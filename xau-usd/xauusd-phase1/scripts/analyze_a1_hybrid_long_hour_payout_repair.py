from __future__ import annotations

import csv
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analyze_a1_best_of_each_hybrid_frontier import build_components
from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    LAST12_START,
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    summary_metrics,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_HYBRID_LONG_HOUR_PAYOUT_REPAIR_PREREG_2026_07_05.md"
OUTPUT_STEM = "A1_XAU_HYBRID_LONG_HOUR_PAYOUT_REPAIR_2026_07_05"
MIN_SIGNALS = 3500
SEEDS = (frozenset({3, 13}), frozenset({3, 14}))
MAX_EXTRA_HOURS = 2
ALL_HOURS = tuple(range(24))
COMBO = (
    "freq_step3_frontier",
    "split_high_payout_f33_r30_be_never",
    "h4_d1_long_best_box2_atr80",
    "h4_d1_long_broad_box3_atr60",
)


def hour(row: dict[str, Any]) -> int:
    return int(row["entry_time"].hour)


def raw_rows(components: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for component in COMBO:
        rows.extend(components[component])
    return rows


def block_sets() -> list[tuple[int, ...]]:
    sets: set[tuple[int, ...]] = set()
    for seed in SEEDS:
        remaining = [value for value in ALL_HOURS if value not in seed]
        for extra_count in range(MAX_EXTRA_HOURS + 1):
            for extra in itertools.combinations(remaining, extra_count):
                sets.add(tuple(sorted(seed.union(extra))))
    return sorted(sets, key=lambda item: (len(item), item))


def evaluate(rows: list[dict[str, Any]], blocked_long_hours: tuple[int, ...]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blocked_set = set(blocked_long_hours)
    kept_raw: list[dict[str, Any]] = []
    blocked_raw = 0
    for row in rows:
        if row.get("direction") == "LONG" and hour(row) in blocked_set:
            blocked_raw += 1
            continue
        kept_raw.append(row)
    kept, dropped = dedupe_signals(kept_raw)
    metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    last12 = summary_metrics(
        [row for row in kept if row["entry_date"] >= LAST12_START],
        market_days=LAST12_MARKET_DAYS,
    )
    stress_010 = summary_metrics(kept, cost_per_ticket=0.10, market_days=MARKET_DAYS)
    stress_030 = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    metrics.update(
        {
            "blocked_long_hours": ",".join(str(value) for value in blocked_long_hours),
            "blocked_hour_count": len(blocked_long_hours),
            "raw_rows": len(rows),
            "blocked_raw_rows": blocked_raw,
            "dedupe_dropped_rows": len(dropped),
            "last12_signals": last12["signals"],
            "last12_win_rate_pct": last12["win_rate_pct"],
            "last12_avg_win_loss": last12["avg_win_loss"],
            "last12_active_weekday_pct": last12["active_weekday_pct"],
            "last12_net_usd": last12["net_usd"],
            "stress_010_net_usd": stress_010["net_usd"],
            "stress_010_avg_win_loss": stress_010["avg_win_loss"],
            "stress_030_net_usd": stress_030["net_usd"],
            "stress_030_avg_win_loss": stress_030["avg_win_loss"],
        }
    )
    metrics["decision"] = decision(metrics)
    metrics["score"] = score(metrics)
    return metrics, kept


def decision(metrics: dict[str, Any]) -> str:
    wr = float(metrics.get("win_rate_pct") or 0.0)
    wl = float(metrics.get("avg_win_loss") or 0.0)
    active = float(metrics.get("active_weekday_pct") or 0.0)
    pf = float(metrics.get("profit_factor") or 0.0)
    net = float(metrics.get("net_usd") or 0.0)
    signals = int(metrics.get("signals") or 0)
    if signals < MIN_SIGNALS or net <= 0:
        return "FAIL_FLOOR"
    if wr >= 50.0 and wl >= 2.0 and active >= 90.0 and pf >= 1.30:
        return "DIAGNOSTIC_OWNER_HIT_EXACT_REPLAY_REQUIRED"
    if wr >= 50.0 and wl >= 2.0 and active >= 85.0 and pf >= 1.30:
        return "DIAGNOSTIC_CORE_NEAR_ACTIVITY_EXACT_REPLAY_REQUIRED"
    if wr >= 50.0 and wl >= 1.95 and active >= 85.0 and pf >= 1.30:
        return "DIAGNOSTIC_NEAR_PAYOUT_NO_REVIEW"
    if wr >= 50.0 and wl < 2.0:
        return "FAIL_WIN_LOSS"
    if wr < 50.0 and wl >= 2.0:
        return "FAIL_WIN_RATE"
    return "FAIL_OWNER_SHAPE"


def score(metrics: dict[str, Any]) -> float:
    return round(
        min(float(metrics.get("win_rate_pct") or 0.0) / 50.0, 1.2) * 350
        + min(float(metrics.get("avg_win_loss") or 0.0) / 2.0, 1.35) * 350
        + min(float(metrics.get("active_weekday_pct") or 0.0) / 90.0, 1.1) * 250
        + min(float(metrics.get("profit_factor") or 0.0) / 1.4, 1.4) * 100,
        4,
    )


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "decision",
        "score",
        "blocked_long_hours",
        "blocked_hour_count",
        "signals",
        "win_rate_pct",
        "avg_win_loss",
        "active_weekday_pct",
        "profit_factor",
        "net_usd",
        "max_closed_drawdown_usd",
        "top25_removed_net_usd",
        "top100_removed_net_usd",
        "last12_signals",
        "last12_win_rate_pct",
        "last12_avg_win_loss",
        "last12_active_weekday_pct",
        "last12_net_usd",
        "stress_010_net_usd",
        "stress_010_avg_win_loss",
        "stress_030_net_usd",
        "stress_030_avg_win_loss",
        "raw_rows",
        "blocked_raw_rows",
        "dedupe_dropped_rows",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU Hybrid Long-Hour Payout Repair Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: diagnostic-only composition of existing exact MT5 ledgers. No MT5 launch, runtime attach, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        f"Searched block sets: `{payload['searched_block_sets']}`",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Blocked LONG Hours | Signals | WR% | W/L | Active% | PF | Net | Last12 WR/WL | Stress -0.30 W/L |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for index, row in enumerate(payload["top_rows"], start=1):
        lines.append(
            f"| {index} | `{row['decision']}` | `{row['blocked_long_hours']}` | "
            f"{row['signals']} | {row['win_rate_pct']} | {row['avg_win_loss']} | "
            f"{row['active_weekday_pct']} | {row['profit_factor']} | {row['net_usd']} | "
            f"{row['last12_win_rate_pct']}/{row['last12_avg_win_loss']} | {row['stress_030_avg_win_loss']} |"
        )
    lines.extend(["", "## Verdict", "", payload["interpretation"], ""])
    lines.append(f"CSV: `{payload['outputs']['csv']}`")
    lines.append(f"JSON: `{payload['outputs']['json']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not PREREG.exists():
        raise FileNotFoundError(PREREG)

    components, _inventory = build_components()
    rows = raw_rows(components)
    results: list[dict[str, Any]] = []
    for blocked in block_sets():
        result, _kept = evaluate(rows, blocked)
        results.append(result)

    decision_rank = {
        "DIAGNOSTIC_OWNER_HIT_EXACT_REPLAY_REQUIRED": 5,
        "DIAGNOSTIC_CORE_NEAR_ACTIVITY_EXACT_REPLAY_REQUIRED": 4,
        "DIAGNOSTIC_NEAR_PAYOUT_NO_REVIEW": 3,
        "FAIL_WIN_LOSS": 2,
        "FAIL_WIN_RATE": 1,
        "FAIL_OWNER_SHAPE": 0,
        "FAIL_FLOOR": -1,
    }
    results.sort(
        key=lambda row: (
            decision_rank.get(str(row.get("decision")), -2),
            row.get("score") or 0.0,
            row.get("active_weekday_pct") or 0.0,
            row.get("avg_win_loss") or 0.0,
        ),
        reverse=True,
    )
    best = results[0]
    status = "REJECT_LONG_HOUR_PAYOUT_REPAIR"
    interpretation = "No seeded long-hour block repair reached W/L 2.0 with enough cadence. Do not spend reviewer or exact MT5 replay time on this branch."
    if best["decision"] == "DIAGNOSTIC_OWNER_HIT_EXACT_REPLAY_REQUIRED":
        status = "DIAGNOSTIC_OWNER_HIT_EXACT_REPLAY_REQUIRED"
        interpretation = "The diagnostic crossed all owner metrics. Rerun the affected exact MT5 components with the same blocked-long-hour list before reviewer spend."
    elif best["decision"] == "DIAGNOSTIC_CORE_NEAR_ACTIVITY_EXACT_REPLAY_REQUIRED":
        status = "DIAGNOSTIC_CORE_NEAR_ACTIVITY_EXACT_REPLAY_REQUIRED"
        interpretation = "The diagnostic crossed WR and W/L with near-owner activity. Rerun the affected exact MT5 components before reviewer spend."
    elif best["decision"] == "DIAGNOSTIC_NEAR_PAYOUT_NO_REVIEW":
        status = "DIAGNOSTIC_NEAR_PAYOUT_NO_REVIEW"
        interpretation = "The diagnostic stayed near the payout target but did not cross W/L 2.0. Keep it as frontier context only."

    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    write_rows(output_csv, results)
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "portfolio": list(COMBO),
        "seed_sets": [sorted(seed) for seed in SEEDS],
        "searched_block_sets": len(results),
        "min_signals": MIN_SIGNALS,
        "best_row": best,
        "top_rows": results[:30],
        "interpretation": interpretation,
        "outputs": {
            "csv": str(output_csv),
            "json": str(output_json),
            "markdown": str(output_md),
        },
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "best_decision": best["decision"], "report": str(output_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
