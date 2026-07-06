from __future__ import annotations

import csv
import itertools
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from analyze_a1_owner_goal_step3_portfolio_composition import (
    DEDUPE_WINDOW_MINUTES,
    LAST12_MARKET_DAYS,
    MARKET_DAYS,
    PHASE1_ROOT,
    REPORTS_DIR,
    dedupe_signals,
    rel,
    sha256_file,
    summary_metrics,
)


OUTPUT_STEM = "A1_XAU_HYBRID_V7_V11_ANTIPOISON_GATE_DIAGNOSTIC_2026_07_05"
PREREG_PATH = (
    PHASE1_ROOT / "docs" / "A1_XAU_HYBRID_V7_V11_ANTIPOISON_GATE_DIAGNOSTIC_PREREG_2026_07_05.md"
)
BASELINE_KEPT = REPORTS_DIR / "A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv"
SOURCE_DIR = (
    REPORTS_DIR
    / "mt5_backtests"
    / "a1_momentum_variants_owner_goal_v7_v8_v11_v13_rr2_202207_202606_20260701"
)

DESIGN_DAYS = [day for day in MARKET_DAYS if date(2022, 7, 1) <= day <= date(2024, 6, 30)]
VALIDATION_DAYS = [day for day in MARKET_DAYS if date(2024, 7, 1) <= day <= date(2026, 6, 30)]
MIN_FULL_SELECTED_ROWS = 20
MIN_DESIGN_SELECTED_ROWS = 8
TOP_SINGLE_FOR_COMBOS = 18
MAX_COMBO_SIZE = 3

FEATURES = [
    "spread_points",
    "atr",
    "body_fraction",
    "close_location",
    "three_bar_move_atr",
    "break_distance_atr",
    "estimated_cost_r",
]


@dataclass(frozen=True)
class SourceFile:
    source_id: str
    priority: int
    trades_csv: Path
    signals_csv: Path


SOURCES = [
    SourceFile(
        source_id="v7_pullback_h1_long_rr2p0",
        priority=101,
        trades_csv=SOURCE_DIR
        / "A1XauM5Momentum_OWNER_GOAL_V7_V8_V11_V13_RR2_202207_202606_XAUUSD_M5_v7_pullback_h1_long_rr2p0_trades.csv",
        signals_csv=SOURCE_DIR
        / "A1XauM5Momentum_OWNER_GOAL_V7_V8_V11_V13_RR2_202207_202606_XAUUSD_M5_v7_pullback_h1_long_rr2p0_signals.csv",
    ),
    SourceFile(
        source_id="v11_ema_trend_h1_long_rr2p0",
        priority=103,
        trades_csv=SOURCE_DIR
        / "A1XauM5Momentum_OWNER_GOAL_V7_V8_V11_V13_RR2_202207_202606_XAUUSD_M5_v11_ema_trend_h1_long_rr2p0_trades.csv",
        signals_csv=SOURCE_DIR
        / "A1XauM5Momentum_OWNER_GOAL_V7_V8_V11_V13_RR2_202207_202606_XAUUSD_M5_v11_ema_trend_h1_long_rr2p0_signals.csv",
    ),
]


def parse_dt(value: Any) -> datetime:
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(text)


def parse_day(value: Any) -> date:
    return parse_dt(value).date()


def read_baseline() -> list[dict[str, Any]]:
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
                }
            )
    return rows


def read_source(source: SourceFile) -> list[dict[str, Any]]:
    trades = pd.read_csv(source.trades_csv)
    signals = pd.read_csv(source.signals_csv, sep="\t")
    signals = signals[signals["stage"].astype(str).eq("WOULD_SIGNAL")].copy()
    signals["entry_key"] = pd.to_datetime(signals["timestamp_broker"], format="%Y.%m.%d %H:%M:%S")
    signals["direction_key"] = signals["direction"].astype(str).str.upper()
    signal_cols = ["entry_key", "direction_key", "reason", *FEATURES]
    signals = signals[signal_cols].drop_duplicates(["entry_key", "direction_key"], keep="first")

    trades["entry_key"] = pd.to_datetime(trades["entry_time"], format="%Y.%m.%d %H:%M:%S")
    trades["direction_key"] = trades["direction"].astype(str).str.upper()
    merged = trades.merge(signals, on=["entry_key", "direction_key"], how="left")

    rows: list[dict[str, Any]] = []
    for ordinal, row in merged.iterrows():
        entry_time = row["entry_key"].to_pydatetime()
        item: dict[str, Any] = {
            "source_id": source.source_id,
            "family_group": "rr2_trend_activity_antipoison_diagnostic",
            "source_priority": source.priority,
            "entry_time": entry_time,
            "entry_date": entry_time.date(),
            "direction": str(row["direction_key"]).upper(),
            "pnl_usd": float(row.get("profit_aed") or 0.0),
            "tickets": 1,
            "lots": float(row.get("volume") or 0.0),
            "component": source.source_id,
            "source_csv": str(source.trades_csv),
            "source_row": int(ordinal) + 2,
            "entry_hour": int(row.get("entry_hour") if pd.notna(row.get("entry_hour")) else entry_time.hour),
            "weekday": entry_time.weekday(),
            "month": entry_time.month,
            "reason": str(row.get("reason") or ""),
        }
        for feature in FEATURES:
            value = row.get(feature)
            item[feature] = float(value) if pd.notna(value) else None
        rows.append(item)
    return rows


def days_between(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def subset_rows(rows: list[dict[str, Any]], day_set: set[date]) -> list[dict[str, Any]]:
    return [row for row in rows if row["entry_date"] in day_set]


def metric_book(
    baseline: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    market_days: list[date],
) -> dict[str, Any]:
    day_set = set(market_days)
    kept, dropped = dedupe_signals(subset_rows(baseline, day_set) + subset_rows(selected, day_set))
    metrics = summary_metrics(kept, market_days=market_days)
    stress = summary_metrics(kept, cost_per_ticket=0.30, market_days=market_days)
    metrics["stress_030_avg_win_loss"] = stress["avg_win_loss"]
    metrics["stress_030_net_usd"] = stress["net_usd"]
    metrics["dropped_overlap_signals"] = len(dropped)
    return metrics


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
    if active >= 90.0 and wr >= 50.0:
        return "ACTIVITY_HIT_PAYOUT_GAP"
    return "NO_OWNER_SHAPE"


def score(row: dict[str, Any]) -> float:
    return round(
        min(float(row.get("win_rate_pct") or 0.0) / 50.0, 1.2) * 300
        + min(float(row.get("avg_win_loss") or 0.0) / 2.0, 1.25) * 300
        + min(float(row.get("active_weekday_pct") or 0.0) / 90.0, 1.15) * 300
        + min(float(row.get("new_active_weekdays") or 0.0) / 40.0, 1.5) * 80
        + min(float(row.get("validation_win_rate_pct") or 0.0) / 50.0, 1.2) * 60,
        4,
    )


def feature_values(rows: list[dict[str, Any]], feature: str) -> list[float]:
    values = [float(row[feature]) for row in rows if row.get(feature) is not None]
    return sorted(values)


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    index = round((len(values) - 1) * q)
    return float(values[index])


def gate_candidates(source_id: str, source_rows: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    design_set = set(DESIGN_DAYS)
    design_rows = [row for row in source_rows if row["entry_date"] in design_set]
    candidates: list[tuple[str, list[dict[str, Any]]]] = [(f"{source_id}[all]", source_rows)]

    for hour in sorted({int(row["entry_hour"]) for row in source_rows}):
        selected = [row for row in source_rows if int(row["entry_hour"]) == hour]
        candidates.append((f"{source_id}[hour={hour:02d}]", selected))
    for weekday in sorted({int(row["weekday"]) for row in source_rows}):
        selected = [row for row in source_rows if int(row["weekday"]) == weekday]
        candidates.append((f"{source_id}[weekday={weekday}]", selected))

    for feature in FEATURES:
        values = feature_values(design_rows, feature)
        if len(values) < MIN_DESIGN_SELECTED_ROWS:
            continue
        thresholds = sorted({round(quantile(values, q), 6) for q in (0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90)})
        for threshold in thresholds:
            candidates.append(
                (
                    f"{source_id}[{feature}<={threshold}]",
                    [row for row in source_rows if row.get(feature) is not None and float(row[feature]) <= threshold],
                )
            )
            candidates.append(
                (
                    f"{source_id}[{feature}>={threshold}]",
                    [row for row in source_rows if row.get(feature) is not None and float(row[feature]) >= threshold],
                )
            )
        for low, high in itertools.combinations(thresholds, 2):
            selected = [
                row
                for row in source_rows
                if row.get(feature) is not None and low <= float(row[feature]) <= high
            ]
            candidates.append((f"{source_id}[{low}<={feature}<={high}]", selected))

    deduped: dict[str, list[dict[str, Any]]] = {}
    for gate_id, selected in candidates:
        if len(selected) >= MIN_FULL_SELECTED_ROWS and len([row for row in selected if row["entry_date"] in design_set]) >= MIN_DESIGN_SELECTED_ROWS:
            deduped[gate_id] = selected
    return list(deduped.items())


def selected_identity(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["source_id"]), int(row.get("source_row") or 0)


def evaluate_gate(
    baseline: list[dict[str, Any]],
    baseline_days: set[date],
    gate_id: str,
    selected: list[dict[str, Any]],
) -> dict[str, Any]:
    unique = {selected_identity(row): row for row in selected}
    selected_rows = list(unique.values())
    full = metric_book(baseline, selected_rows, MARKET_DAYS)
    design = metric_book(baseline, selected_rows, DESIGN_DAYS)
    validation = metric_book(baseline, selected_rows, VALIDATION_DAYS)
    last12 = metric_book(baseline, selected_rows, LAST12_MARKET_DAYS)
    active_days = {row["entry_date"] for row in dedupe_signals(baseline + selected_rows)[0]}
    row: dict[str, Any] = {
        "gate_id": gate_id,
        "selected_rows": len(selected_rows),
        "new_active_weekdays": len(active_days.difference(baseline_days).intersection(set(MARKET_DAYS))),
        **full,
        "design_win_rate_pct": design["win_rate_pct"],
        "design_avg_win_loss": design["avg_win_loss"],
        "design_active_weekday_pct": design["active_weekday_pct"],
        "validation_win_rate_pct": validation["win_rate_pct"],
        "validation_avg_win_loss": validation["avg_win_loss"],
        "validation_active_weekday_pct": validation["active_weekday_pct"],
        "last12_win_rate_pct": last12["win_rate_pct"],
        "last12_avg_win_loss": last12["avg_win_loss"],
        "last12_active_weekday_pct": last12["active_weekday_pct"],
    }
    row["decision"] = decision(row)
    row["score"] = score(row)
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = [
        "decision",
        "score",
        "gate_id",
        "selected_rows",
        "new_active_weekdays",
        "signals",
        "win_rate_pct",
        "avg_win_loss",
        "active_weekday_pct",
        "profit_factor",
        "net_usd",
        "stress_030_avg_win_loss",
        "design_win_rate_pct",
        "design_avg_win_loss",
        "design_active_weekday_pct",
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
    baseline = payload["baseline"]
    lines = [
        "# A1 XAU Hybrid V7/V11 Antipoison Gate Diagnostic",
        "",
        f"Generated UTC: `{payload['generated_utc']}`",
        "",
        "Scope: diagnostic only. It joins causal MT5 signal features to already-realized exact MT5 v7/v11 trade ledgers, then recomposes with the current exact frontier. It does not prove an exact MT5 path because skipped trades can free later entries.",
        "",
        f"Preregistration: `{rel(PREREG_PATH)}`",
        "",
        "## Baseline",
        "",
        "| Signals | WR% | W/L | Active% | PF | Net USD | Stress -0.30 W/L |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        "| {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {profit_factor:.4f} | {net_usd:.2f} | {stress_030_avg_win_loss:.4f} |".format(
            **baseline
        ),
        "",
        "## Best Diagnostic Row",
        "",
        "| Decision | Gate | Selected | Signals | WR% | W/L | Active% | New Days | PF | Net | Validation WR/WL/Active | Last12 WR/WL/Active |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        "| `{decision}` | `{gate_id}` | {selected_rows} | {signals} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {new_active_weekdays} | {profit_factor:.4f} | {net_usd:.2f} | {validation_win_rate_pct:.2f}/{validation_avg_win_loss:.4f}/{validation_active_weekday_pct:.2f} | {last12_win_rate_pct:.2f}/{last12_avg_win_loss:.4f}/{last12_active_weekday_pct:.2f} |".format(
            **best
        ),
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Gate | Selected | New Days | WR% | W/L | Active% | Validation WR/WL | Last12 WR/WL |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for index, row in enumerate(payload["top_rows"][:25], start=1):
        lines.append(
            "| {index} | `{decision}` | `{gate_id}` | {selected_rows} | {new_active_weekdays} | {win_rate_pct:.2f} | {avg_win_loss:.4f} | {active_weekday_pct:.2f} | {validation_win_rate_pct:.2f}/{validation_avg_win_loss:.4f} | {last12_win_rate_pct:.2f}/{last12_avg_win_loss:.4f} |".format(
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
    baseline = read_baseline()
    baseline_days = {row["entry_date"] for row in baseline}
    baseline_metrics = summary_metrics(baseline, market_days=MARKET_DAYS)
    baseline_stress = summary_metrics(baseline, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    baseline_metrics["stress_030_avg_win_loss"] = baseline_stress["avg_win_loss"]

    source_rows_by_id = {source.source_id: read_source(source) for source in SOURCES}
    candidate_rows: list[dict[str, Any]] = []
    selected_by_gate: dict[str, list[dict[str, Any]]] = {}

    for source_id, rows in source_rows_by_id.items():
        for gate_id, selected in gate_candidates(source_id, rows):
            result = evaluate_gate(baseline, baseline_days, gate_id, selected)
            candidate_rows.append(result)
            selected_by_gate[gate_id] = selected

    # Combine the strongest single-source gates from distinct sources. This is still diagnostic.
    singles_for_combo = sorted(
        candidate_rows,
        key=lambda row: (
            row["active_weekday_pct"] >= 88.0,
            row["win_rate_pct"] >= 49.5,
            row["avg_win_loss"] >= 1.95,
            row["score"],
        ),
        reverse=True,
    )[:TOP_SINGLE_FOR_COMBOS]
    for size in range(2, min(MAX_COMBO_SIZE, len(singles_for_combo)) + 1):
        for combo in itertools.combinations(singles_for_combo, size):
            source_ids = [row["gate_id"].split("[", 1)[0] for row in combo]
            if len(source_ids) != len(set(source_ids)):
                continue
            selected: list[dict[str, Any]] = []
            combo_id = " + ".join(row["gate_id"] for row in combo)
            for row in combo:
                selected.extend(selected_by_gate[row["gate_id"]])
            result = evaluate_gate(baseline, baseline_days, combo_id, selected)
            result["selected_rows"] = len({selected_identity(row): row for row in selected})
            candidate_rows.append(result)
            selected_by_gate[combo_id] = selected

    candidate_rows.sort(
        key=lambda row: (
            row["decision"] == "DIAGNOSTIC_REPLAY_CANDIDATE",
            row["decision"] == "DIAGNOSTIC_FULL_HIT_VALIDATION_WEAK",
            row["win_rate_pct"] >= 50.0 and row["avg_win_loss"] >= 2.0,
            row["active_weekday_pct"],
            row["score"],
        ),
        reverse=True,
    )
    best = candidate_rows[0]
    best_selected = list({selected_identity(row): row for row in selected_by_gate[best["gate_id"]]}.values())
    best_kept, best_dropped = dedupe_signals(baseline + best_selected)

    if best["decision"] == "DIAGNOSTIC_REPLAY_CANDIDATE":
        interpretation = (
            "A diagnostic gate reaches the owner shape and has tolerable validation metrics. "
            "It is not evidence for demo; the next step is a preregistered exact MT5 rerun with the gate implemented, because ledger filtering cannot prove the one-position path."
        )
    elif best["decision"] == "DIAGNOSTIC_FULL_HIT_VALIDATION_WEAK":
        interpretation = (
            "A full-window diagnostic row reaches the owner shape, but validation is weak. "
            "Treat it as an overfit warning unless a stricter preregistered exact rerun is explicitly approved."
        )
    else:
        interpretation = (
            "No v7/v11 causal-feature gate bridges the current activity gap while preserving WR >=50%, W/L >=2.0, and active >=90%. "
            "The activity source still buys cadence with too much win-rate damage."
        )

    payload = {
        "generated_utc": generated,
        "baseline": baseline_metrics,
        "best_row": best,
        "top_rows": candidate_rows[:75],
        "row_count": len(candidate_rows),
        "interpretation": interpretation,
        "input_files": [
            {
                "source_id": source.source_id,
                "trades_csv": str(source.trades_csv),
                "signals_csv": str(source.signals_csv),
                "trades_sha256": sha256_file(source.trades_csv),
                "signals_sha256": sha256_file(source.signals_csv),
            }
            for source in SOURCES
        ],
        "baseline_csv": str(BASELINE_KEPT),
        "baseline_sha256": sha256_file(BASELINE_KEPT),
        "dedupe_window_minutes": DEDUPE_WINDOW_MINUTES,
    }

    write_csv(REPORTS_DIR / f"{OUTPUT_STEM}.csv", candidate_rows)
    signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT.csv", best_kept)
    signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED.csv", best_dropped)
    (REPORTS_DIR / f"{OUTPUT_STEM}.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (REPORTS_DIR / f"{OUTPUT_STEM}.md").write_text(render(payload), encoding="utf-8")
    print(json.dumps({"output": str(REPORTS_DIR / f"{OUTPUT_STEM}.md"), "best": best}, indent=2, default=str))


if __name__ == "__main__":
    main()
