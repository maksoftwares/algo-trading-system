from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_OWNER_GOAL_STEP3_PORTFOLIO_COMPOSITION_2026_07_05"
PREREG_PATH = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_M5_OWNER_GOAL_STEP3_PORTFOLIO_COMPOSITION_PREREG_2026_07_05.md"
)

START_DATE = date(2022, 7, 1)
END_DATE = date(2026, 6, 30)
LAST12_START = date(2025, 7, 1)
DEDUPE_WINDOW_MINUTES = 5
MAX_COMBO_SIZE = 5

STEP1_LEDGER = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_KEPT_SIGNALS_2026_07_05.csv"
EARLY_ADVERSE_LEDGER = (
    REPORTS_DIR / "A1_XAU_M5_EARLY_ADVERSE_EXIT_EXACT_PROBE_KEPT_SIGNALS_202207_202606.csv"
)
BREAK_DISTANCE_LEDGER = (
    REPORTS_DIR / "A1_XAU_M5_SPLIT_BREAK_DISTANCE_GUARD_EXACT_PROBE_KEPT_SIGNALS_202207_202606.csv"
)

V7_V8_V11_V13_REPORT = (
    REPORTS_DIR / "A1_XAU_M5_V7_V8_V11_V13_RR2_STRETCH_PROBE_OWNER_GOAL_202207_202606.json"
)
V9_V10_REPORT = (
    REPORTS_DIR / "A1_XAU_M5_V9_V10_RR2_STRETCH_PROBE_OWNER_GOAL_V9V10_RR2_202207_202606.json"
)
MACRO_REPORT = REPORTS_DIR / "A1_XAU_M5_EXTERNAL_MACRO_TRAFFIC_LIGHT_GATE_DIAGNOSTIC_2026_07_05.json"

STEP1_CELL_IDS = {"f33_r30_be_1r", "f33_r30_be_never", "f67_r20_be_tp1"}


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    family_group: str
    priority: int
    kind: str
    path: Path
    cell_id: str | None = None
    label: str = ""


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def parse_dt(value: str) -> datetime:
    text = str(value).strip()
    if not text:
        raise ValueError("empty datetime")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(text)


def parse_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip().replace(" ", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def parse_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def weekday_market_days(start: date = START_DATE, end: date = END_DATE) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


MARKET_DAYS = weekday_market_days()
MARKET_DAY_SET = set(MARKET_DAYS)
LAST12_MARKET_DAYS = weekday_market_days(LAST12_START, END_DATE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def signal_from_row(row: dict[str, str], spec: SourceSpec, ordinal: int) -> dict[str, Any] | None:
    if spec.cell_id:
        row_cell = str(row.get("cell_id", "")).strip()
        if row_cell != spec.cell_id:
            return None

    entry_time = parse_dt(str(row["entry_time"]))
    entry_date = date.fromisoformat(str(row.get("entry_date") or entry_time.date().isoformat()))
    if entry_date < START_DATE or entry_date > END_DATE:
        return None

    pnl = parse_float(row.get("signal_pnl_usd", row.get("signal_pnl", row.get("profit_aed", "0"))))
    tickets = parse_int(row.get("tickets"), 1)
    if tickets <= 0:
        tickets = 1
    lots = parse_float(row.get("lots", row.get("volume", "0")), 0.0)
    if lots <= 0 and row.get("volume"):
        lots = parse_float(row.get("volume"), 0.0)

    return {
        "source_id": spec.source_id,
        "family_group": spec.family_group,
        "source_priority": spec.priority,
        "source_label": spec.label or spec.source_id,
        "entry_time": entry_time,
        "entry_date": entry_date,
        "direction": str(row.get("direction", "")).strip().upper(),
        "pnl_usd": pnl,
        "tickets": tickets,
        "lots": lots,
        "component": str(row.get("component", "")).strip(),
        "source_csv": str(row.get("source_csv") or spec.path),
        "source_row": ordinal,
    }


def load_signal_ledger(spec: SourceSpec) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(read_csv(spec.path), start=2):
        normalized = signal_from_row(row, spec, ordinal)
        if normalized is not None:
            rows.append(normalized)
    return rows


def load_trade_csv(spec: SourceSpec) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(read_csv(spec.path), start=2):
        normalized = signal_from_row(row, spec, ordinal)
        if normalized is not None:
            normalized["tickets"] = 1
            normalized["lots"] = parse_float(row.get("volume"), normalized["lots"])
            normalized["source_csv"] = str(spec.path)
            rows.append(normalized)
    return rows


def report_variants(report_path: Path) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    return json.loads(report_path.read_text(encoding="utf-8")).get("variants", [])


def macro_exam_families(report_path: Path) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    return json.loads(report_path.read_text(encoding="utf-8")).get("families", [])


def build_source_specs() -> list[SourceSpec]:
    specs: list[SourceSpec] = []

    step1_priority = {
        "f33_r30_be_1r": 10,
        "f33_r30_be_never": 11,
        "f67_r20_be_tp1": 12,
    }
    for cell_id in sorted(STEP1_CELL_IDS, key=lambda item: step1_priority[item]):
        specs.append(
            SourceSpec(
                source_id=f"step1_{cell_id}",
                family_group="a1_core_management",
                priority=step1_priority[cell_id],
                kind="signal_ledger",
                path=STEP1_LEDGER,
                cell_id=cell_id,
                label=f"Step1 split-grid {cell_id}",
            )
        )

    early_priority = {
        "eae60_r050": 20,
        "eae60_r035": 21,
        "eae30_r050": 22,
        "eae30_r035": 23,
    }
    for cell_id in sorted(early_priority, key=lambda item: early_priority[item]):
        specs.append(
            SourceSpec(
                source_id=f"early_{cell_id}",
                family_group="a1_core_management",
                priority=early_priority[cell_id],
                kind="signal_ledger",
                path=EARLY_ADVERSE_LEDGER,
                cell_id=cell_id,
                label=f"Early-adverse exact {cell_id}",
            )
        )

    specs.append(
        SourceSpec(
            source_id="break_distance_minbd08994",
            family_group="a1_core_management",
            priority=30,
            kind="signal_ledger",
            path=BREAK_DISTANCE_LEDGER,
            label="Break-distance exact MinBreakDistanceAtr 0.8994",
        )
    )

    for offset, item in enumerate(report_variants(V7_V8_V11_V13_REPORT), start=0):
        name = str(item.get("name", ""))
        trade_csv = item.get("trade_csv")
        if name and trade_csv:
            specs.append(
                SourceSpec(
                    source_id=name,
                    family_group="rr2_trend_stretch",
                    priority=100 + offset,
                    kind="trade_csv",
                    path=Path(trade_csv),
                    label=str(item.get("label") or name),
                )
            )

    for offset, item in enumerate(report_variants(V9_V10_REPORT), start=0):
        name = str(item.get("name", ""))
        trade_csv = item.get("trade_csv")
        if name and trade_csv:
            specs.append(
                SourceSpec(
                    source_id=name,
                    family_group="rr2_sweep_or_stretch",
                    priority=150 + offset,
                    kind="trade_csv",
                    path=Path(trade_csv),
                    label=str(item.get("label") or name),
                )
            )

    macro_priority = {
        "rr2_baseline_no_lock": 200,
        "rr2_lock100_010": 201,
        "rr2_lock080_010": 202,
        "orrev_london_firm_stop15": 250,
        "orrev_london_firm_stop10": 251,
        "orrev_london_loose_stop15": 252,
    }
    for item in macro_exam_families(MACRO_REPORT):
        family_id = str(item.get("family_id", ""))
        trade_csv = item.get("exam_trade_csv")
        if family_id not in macro_priority or not trade_csv:
            continue
        group = "rr2_profit_lock_exam" if family_id.startswith("rr2_") else "opening_range_reversal_exam"
        specs.append(
            SourceSpec(
                source_id=family_id,
                family_group=group,
                priority=macro_priority[family_id],
                kind="trade_csv",
                path=Path(trade_csv),
                label=str(item.get("label") or family_id),
            )
        )

    return specs


def load_sources(specs: list[SourceSpec]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    sources: dict[str, list[dict[str, Any]]] = {}
    inventory: list[dict[str, Any]] = []
    for spec in specs:
        exists = spec.path.exists()
        source_sha = sha256_file(spec.path) if exists else ""
        rows = load_signal_ledger(spec) if exists and spec.kind == "signal_ledger" else []
        if exists and spec.kind == "trade_csv":
            rows = load_trade_csv(spec)
        sources[spec.source_id] = rows
        inventory.append(
            {
                "source_id": spec.source_id,
                "family_group": spec.family_group,
                "priority": spec.priority,
                "kind": spec.kind,
                "cell_id": spec.cell_id,
                "rows": len(rows),
                "path": str(spec.path),
                "path_rel": rel(spec.path),
                "sha256": source_sha,
                "exists": exists,
            }
        )
    return sources, inventory


def max_closed_drawdown(profits: list[float], starting_balance: float = 1000.0) -> float:
    equity = starting_balance
    peak = starting_balance
    max_dd = 0.0
    for value in profits:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return round(max_dd, 2)


def summary_metrics(
    trades: list[dict[str, Any]],
    cost_per_ticket: float = 0.0,
    market_days: list[date] | None = None,
) -> dict[str, Any]:
    denominator_days = market_days or MARKET_DAYS
    denominator_day_set = set(denominator_days)
    ordered = sorted(trades, key=lambda row: (row["entry_time"], row["source_priority"], row["source_id"]))
    profits = [float(row["pnl_usd"]) - cost_per_ticket * int(row.get("tickets", 1)) for row in ordered]
    wins = [value for value in profits if value > 0]
    losses = [value for value in profits if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    win_loss = avg_win / avg_loss if avg_loss else None
    by_day: dict[date, list[float]] = defaultdict(list)
    by_month: dict[str, list[float]] = defaultdict(list)
    by_source: dict[str, list[float]] = defaultdict(list)
    for row, profit in zip(ordered, profits):
        entry_day = row["entry_date"]
        by_day[entry_day].append(profit)
        by_month[entry_day.strftime("%Y-%m")].append(profit)
        by_source[row["source_id"]].append(profit)

    active_days = len(set(by_day).intersection(denominator_day_set))
    positive_days = sum(1 for values in by_day.values() if sum(values) > 0)
    negative_days = sum(1 for values in by_day.values() if sum(values) < 0)
    monthly = {month: sum(values) for month, values in by_month.items()}
    top_wins = sorted(wins, reverse=True)
    net = sum(profits)

    return {
        "signals": len(ordered),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / len(ordered), 2) if ordered else 0.0,
        "avg_win_usd": round(avg_win, 4),
        "avg_loss_usd": round(avg_loss, 4),
        "avg_win_loss": round(win_loss, 4) if win_loss is not None else None,
        "gross_profit_usd": round(gross_profit, 2),
        "gross_loss_usd": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "net_usd": round(net, 2),
        "active_weekdays": active_days,
        "market_weekdays": len(denominator_days),
        "active_weekday_pct": round(100.0 * active_days / len(denominator_days), 2)
        if denominator_days
        else 0.0,
        "signals_per_active_day": round(len(ordered) / active_days, 2) if active_days else 0.0,
        "positive_active_days": positive_days,
        "negative_active_days": negative_days,
        "positive_months": sum(1 for value in monthly.values() if value > 0),
        "negative_months": sum(1 for value in monthly.values() if value < 0),
        "worst_day_usd": round(min((sum(values) for values in by_day.values()), default=0.0), 2),
        "best_day_usd": round(max((sum(values) for values in by_day.values()), default=0.0), 2),
        "worst_month_usd": round(min(monthly.values(), default=0.0), 2),
        "best_month_usd": round(max(monthly.values(), default=0.0), 2),
        "max_closed_drawdown_usd": max_closed_drawdown(profits),
        "top10_removed_net_usd": round(net - sum(top_wins[:10]), 2),
        "top25_removed_net_usd": round(net - sum(top_wins[:25]), 2),
        "top50_removed_net_usd": round(net - sum(top_wins[:50]), 2),
        "top100_removed_net_usd": round(net - sum(top_wins[:100]), 2),
        "source_contributions": {
            source_id: {
                "signals": len(values),
                "net_usd": round(sum(values), 2),
            }
            for source_id, values in sorted(by_source.items())
        },
    }


def decision_for(metrics: dict[str, Any]) -> str:
    win_loss = metrics.get("avg_win_loss") or 0.0
    wr = metrics["win_rate_pct"]
    active = metrics["active_weekday_pct"]
    net = metrics["net_usd"]
    if wr >= 50.0 and win_loss >= 2.0 and active >= 90.0:
        return "OWNER_GOAL_HIT"
    if wr >= 50.0 and win_loss >= 2.0:
        return "CORE_SHAPE_FREQUENCY_GAP"
    if wr >= 48.0 and win_loss >= 1.9 and active >= 50.0 and net > 0:
        return "NEAR_OWNER_SHAPE"
    if wr < 50.0 and win_loss >= 2.0:
        return "FAIL_WIN_RATE"
    if wr >= 50.0 and win_loss < 2.0:
        return "FAIL_WIN_LOSS"
    return "FAIL_OWNER_SHAPE"


def fitness(metrics: dict[str, Any]) -> float:
    win_loss = metrics.get("avg_win_loss") or 0.0
    net = metrics["net_usd"]
    robust = metrics["top25_removed_net_usd"]
    robust_bonus = min(max(robust, -5000.0), 5000.0) / 5000.0
    return round(
        3.0 * min(metrics["win_rate_pct"] / 50.0, 1.4)
        + 3.0 * min(win_loss / 2.0, 1.5)
        + 2.0 * min(metrics["active_weekday_pct"] / 90.0, 1.2)
        + 0.7 * math.tanh(net / 5000.0)
        + 0.3 * robust_bonus,
        6,
    )


def dedupe_signals(trades: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted(
        trades,
        key=lambda row: (
            row["entry_time"],
            row["source_priority"],
            row["source_id"],
            row["direction"],
            row["source_row"],
        ),
    )
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    max_seconds = DEDUPE_WINDOW_MINUTES * 60
    for row in ordered:
        duplicate_of: dict[str, Any] | None = None
        for previous in reversed(kept[-50:]):
            delta = (row["entry_time"] - previous["entry_time"]).total_seconds()
            if delta > max_seconds:
                break
            if (
                abs(delta) <= max_seconds
                and row["direction"] == previous["direction"]
                and row["source_id"] != previous["source_id"]
            ):
                duplicate_of = previous
                break
        if duplicate_of is None:
            kept.append(row)
        else:
            blocked = dict(row)
            blocked["drop_reason"] = "same_direction_overlap_5m"
            blocked["duplicate_of_source_id"] = duplicate_of["source_id"]
            blocked["duplicate_of_entry_time"] = duplicate_of["entry_time"].isoformat(sep=" ")
            dropped.append(blocked)
    return kept, dropped


def family_groups_ok(source_ids: tuple[str, ...], specs_by_id: dict[str, SourceSpec]) -> bool:
    groups = [specs_by_id[source_id].family_group for source_id in source_ids]
    return len(groups) == len(set(groups))


def all_combinations(source_ids: list[str], specs_by_id: dict[str, SourceSpec]) -> list[tuple[str, ...]]:
    combos: list[tuple[str, ...]] = []
    for size in range(1, min(MAX_COMBO_SIZE, len(source_ids)) + 1):
        for combo in itertools.combinations(source_ids, size):
            if family_groups_ok(combo, specs_by_id):
                combos.append(combo)
    return combos


def combo_row(
    combo: tuple[str, ...],
    kept: list[dict[str, Any]],
    dropped: list[dict[str, Any]],
    specs_by_id: dict[str, SourceSpec],
) -> dict[str, Any]:
    metrics = summary_metrics(kept)
    decision = decision_for(metrics)
    return {
        "portfolio_id": "__plus__".join(combo),
        "source_ids": list(combo),
        "family_groups": [specs_by_id[source_id].family_group for source_id in combo],
        "component_count": len(combo),
        "dropped_overlap_signals": len(dropped),
        "decision": decision,
        "fitness": fitness(metrics),
        **metrics,
    }


def add_frontier_diagnostics(row: dict[str, Any], kept: list[dict[str, Any]]) -> None:
    last12 = summary_metrics(
        [signal for signal in kept if signal["entry_date"] >= LAST12_START],
        market_days=LAST12_MARKET_DAYS,
    )
    stress_010 = summary_metrics(kept, cost_per_ticket=0.10)
    stress_030 = summary_metrics(kept, cost_per_ticket=0.30)
    row.update(
        {
            "last12_signals": last12["signals"],
            "last12_win_rate_pct": last12["win_rate_pct"],
            "last12_avg_win_loss": last12["avg_win_loss"],
            "last12_net_usd": last12["net_usd"],
            "last12_active_weekday_pct": last12["active_weekday_pct"],
            "stress_010_net_usd": stress_010["net_usd"],
            "stress_010_win_rate_pct": stress_010["win_rate_pct"],
            "stress_010_avg_win_loss": stress_010["avg_win_loss"],
            "stress_030_net_usd": stress_030["net_usd"],
            "stress_030_win_rate_pct": stress_030["win_rate_pct"],
            "stress_030_avg_win_loss": stress_030["avg_win_loss"],
        }
    )


def row_for_csv(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    for key in ("source_contributions", "source_ids", "family_groups"):
        if key in output:
            output[key] = json.dumps(output[key], sort_keys=True)
    return output


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if not fieldnames and rows:
        fieldnames = list(rows[0].keys())
    if not fieldnames:
        fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def signal_csv_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": row["source_id"],
        "family_group": row["family_group"],
        "source_priority": row["source_priority"],
        "entry_time": row["entry_time"].isoformat(sep=" "),
        "entry_date": row["entry_date"].isoformat(),
        "direction": row["direction"],
        "pnl_usd": row["pnl_usd"],
        "tickets": row["tickets"],
        "lots": row["lots"],
        "component": row.get("component", ""),
        "source_row": row["source_row"],
        "source_csv": row["source_csv"],
        "drop_reason": row.get("drop_reason", ""),
        "duplicate_of_source_id": row.get("duplicate_of_source_id", ""),
        "duplicate_of_entry_time": row.get("duplicate_of_entry_time", ""),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    best = payload["best_portfolio"]
    top_rows = payload["top_rows"][:20]
    inventory = payload["inventory"]
    lines = [
        "# A1 XAU M5 Owner Goal Step 3 Portfolio Composition Diagnostic",
        "",
        "Generated: 2026-07-05",
        "",
        "Scope: exact MT5 Strategy Tester outputs only. This script did not launch MT5, attach to runtime, infer exits, or create trades. It normalized already-realized MT5 rows and recalculated signal-level metrics.",
        "",
        f"Decision: **{payload['status']}**",
        "",
        "Reviewer spend rule: preserve the one daily reviewer pass unless this diagnostic reaches owner goal, core shape with frequency gap, or a non-trivial near-owner shape.",
        "",
        "## Best Frontier Portfolio",
        "",
        f"- Portfolio: `{best['portfolio_id']}`",
        f"- Decision: `{best['decision']}`",
        f"- Signals: {best['signals']}",
        f"- WR: {best['win_rate_pct']:.2f}%",
        f"- Avg win / avg loss: {best['avg_win_loss']}",
        f"- Active weekdays: {best['active_weekdays']} / {best['market_weekdays']} ({best['active_weekday_pct']:.2f}%)",
        f"- Net: {best['net_usd']:.2f}",
        f"- PF: {best['profit_factor']}",
        f"- Max closed DD: {best['max_closed_drawdown_usd']:.2f}",
        f"- Top25 removed net: {best['top25_removed_net_usd']:.2f}",
        f"- Last 12 months: {best['last12_signals']} signals, WR {best['last12_win_rate_pct']:.2f}%, W/L {best['last12_avg_win_loss']}, net {best['last12_net_usd']:.2f}, active weekdays {best['last12_active_weekday_pct']:.2f}%",
        f"- Stress -0.10/ticket: net {best['stress_010_net_usd']:.2f}, WR {best['stress_010_win_rate_pct']:.2f}%, W/L {best['stress_010_avg_win_loss']}",
        f"- Stress -0.30/ticket: net {best['stress_030_net_usd']:.2f}, WR {best['stress_030_win_rate_pct']:.2f}%, W/L {best['stress_030_avg_win_loss']}",
        "",
        "## Top Portfolio Rows",
        "",
        "| Rank | Decision | Components | Signals | WR % | W/L | Active % | Net | PF | Top25 Removed | Last12 WR | Last12 W/L |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_rows, start=1):
        lines.append(
            "| "
            f"{rank} | {row['decision']} | `{row['portfolio_id']}` | {row['signals']} | "
            f"{row['win_rate_pct']:.2f} | {row['avg_win_loss']} | {row['active_weekday_pct']:.2f} | "
            f"{row['net_usd']:.2f} | {row['profit_factor']} | {row['top25_removed_net_usd']:.2f} | "
            f"{row['last12_win_rate_pct']:.2f} | {row['last12_avg_win_loss']} |"
        )

    lines.extend(
        [
            "",
            "## Source Inventory",
            "",
            "| Source | Group | Rows | SHA256 | Path |",
            "|---|---|---:|---|---|",
        ]
    )
    for item in inventory:
        lines.append(
            f"| `{item['source_id']}` | `{item['family_group']}` | {item['rows']} | "
            f"`{item['sha256'][:12]}` | `{item['path_rel']}` |"
        )

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- Results CSV: `{rel(payload['outputs']['results_csv'])}`",
            f"- Best kept signals CSV: `{rel(payload['outputs']['best_kept_csv'])}`",
            f"- Best dropped signals CSV: `{rel(payload['outputs']['best_dropped_csv'])}`",
            f"- JSON: `{rel(payload['outputs']['json'])}`",
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    specs = build_source_specs()
    specs_by_id = {spec.source_id: spec for spec in specs}
    sources, inventory = load_sources(specs)
    non_empty_ids = [spec.source_id for spec in sorted(specs, key=lambda item: item.priority) if sources[spec.source_id]]
    combos = all_combinations(non_empty_ids, specs_by_id)

    rows: list[dict[str, Any]] = []
    combo_details: dict[str, tuple[list[dict[str, Any]], list[dict[str, Any]]]] = {}
    for combo in combos:
        raw: list[dict[str, Any]] = []
        for source_id in combo:
            raw.extend(sources[source_id])
        kept, dropped = dedupe_signals(raw)
        row = combo_row(combo, kept, dropped, specs_by_id)
        rows.append(row)
        combo_details[row["portfolio_id"]] = (kept, dropped)

    decision_rank = {
        "OWNER_GOAL_HIT": 5,
        "CORE_SHAPE_FREQUENCY_GAP": 4,
        "NEAR_OWNER_SHAPE": 3,
        "FAIL_WIN_LOSS": 2,
        "FAIL_WIN_RATE": 1,
        "FAIL_OWNER_SHAPE": 0,
    }
    rows.sort(
        key=lambda row: (
            decision_rank.get(row["decision"], -1),
            row["fitness"],
            row["active_weekday_pct"],
            row["win_rate_pct"],
            row.get("avg_win_loss") or 0.0,
            row["net_usd"],
        ),
        reverse=True,
    )

    for row in rows[:100]:
        kept, _dropped = combo_details.get(row["portfolio_id"], ([], []))
        add_frontier_diagnostics(row, kept)

    best = rows[0] if rows else {}
    best_kept, best_dropped = combo_details.get(best.get("portfolio_id", ""), ([], []))

    status = "REJECT_NO_STEP3_OWNER_PORTFOLIO"
    if best.get("decision") == "OWNER_GOAL_HIT":
        status = "OWNER_GOAL_HIT_REVIEW_REQUIRED"
    elif best.get("decision") == "CORE_SHAPE_FREQUENCY_GAP":
        status = "CORE_SHAPE_FREQUENCY_GAP_REVIEW_WORTHY"
    elif best.get("decision") == "NEAR_OWNER_SHAPE":
        status = "NEAR_OWNER_SHAPE_REVIEW_OPTIONAL"

    if status == "REJECT_NO_STEP3_OWNER_PORTFOLIO":
        interpretation = (
            "No exact-MT5 portfolio composition reached the owner shape. The best frontier still fails at least one "
            "of WR >= 50%, realized W/L >= 2.0, or 90% active weekday coverage, so the reviewer token is preserved."
        )
    else:
        interpretation = (
            "The best frontier is strong enough to package for reviewer scrutiny before any claim is promoted. "
            "It remains a diagnostic portfolio until reviewed."
        )

    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    best_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_KEPT_SIGNALS.csv"
    best_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_DROPPED_SIGNALS.csv"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"

    csv_rows = [row_for_csv(row) for row in rows]
    write_csv(results_csv, csv_rows)
    signal_fields = list(signal_csv_row(best_kept[0]).keys()) if best_kept else list(signal_csv_row({
        "source_id": "",
        "family_group": "",
        "source_priority": 0,
        "entry_time": datetime(1970, 1, 1),
        "entry_date": date(1970, 1, 1),
        "direction": "",
        "pnl_usd": 0.0,
        "tickets": 0,
        "lots": 0.0,
        "source_row": 0,
        "source_csv": "",
    }).keys())
    write_csv(best_kept_csv, [signal_csv_row(row) for row in best_kept], signal_fields)
    write_csv(best_dropped_csv, [signal_csv_row(row) for row in best_dropped], signal_fields)

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": status,
        "scope": {
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "period": f"{START_DATE.isoformat()} -> {END_DATE.isoformat()}",
            "method": "offline composition of exact MT5 Strategy Tester output rows",
            "no_mt5_launch": True,
            "no_runtime_attach": True,
            "dedupe_window_minutes": DEDUPE_WINDOW_MINUTES,
            "max_combo_size": MAX_COMBO_SIZE,
            "family_group_cap": "at most one stream per broad family_group",
            "preregistration": str(PREREG_PATH),
            "preregistration_sha256": sha256_file(PREREG_PATH) if PREREG_PATH.exists() else "",
        },
        "inventory": inventory,
        "combination_count": len(rows),
        "best_portfolio": best,
        "top_rows": rows[:50],
        "interpretation": interpretation,
        "outputs": {
            "markdown": output_md,
            "json": output_json,
            "results_csv": results_csv,
            "best_kept_csv": best_kept_csv,
            "best_dropped_csv": best_dropped_csv,
        },
    }

    json_ready = json.loads(
        json.dumps(
            payload,
            default=lambda value: str(value) if isinstance(value, Path) else value,
            sort_keys=True,
        )
    )
    output_json.write_text(json.dumps(json_ready, indent=2, sort_keys=True), encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"Wrote {output_md}")
    print(f"Status: {status}")
    print(
        "Best: "
        f"{best.get('portfolio_id')} | {best.get('decision')} | WR {best.get('win_rate_pct')} | "
        f"W/L {best.get('avg_win_loss')} | active {best.get('active_weekday_pct')} | "
        f"net {best.get('net_usd')}"
    )


if __name__ == "__main__":
    main()
