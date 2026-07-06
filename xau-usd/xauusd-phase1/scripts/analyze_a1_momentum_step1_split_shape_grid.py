from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
MT5_REPORTS = REPORTS / "mt5_backtests"
DEFAULT_TAG = "GOAL_SPLIT_GRID_202207_202606"
DEFAULT_VARIANT_DIR = MT5_REPORTS / "a1_momentum_variants_goal_split_grid_202207_202606_20260701"
OUT_MD = REPORTS / "A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_FRONTIER_2026_07_05.md"
OUT_JSON = OUT_MD.with_suffix(".json")
OUT_CSV = OUT_MD.with_suffix(".csv")
OUT_LEDGER_CSV = REPORTS / "A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_COMPONENT_LEDGER_2026_07_05.csv"
OUT_KEPT_CSV = REPORTS / "A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_KEPT_SIGNALS_2026_07_05.csv"
OUT_DROPPED_CSV = REPORTS / "A1_XAU_M5_MOMENTUM_STEP1_SPLIT_SHAPE_GRID_DROPPED_SIGNALS_2026_07_05.csv"

FROM_DATE = date(2022, 7, 1)
TO_DATE = date(2026, 6, 30)
LAST12_START = date(2025, 7, 1)

COMPONENTS = [
    ("v6", "risk_norm_split20_v6_max2_all8", 1),
    ("weak", "risk_norm_split20_freq_weak_hours_all8", 2),
    ("v13", "risk_norm_split20_v13_rr0p7_all8_22", 3),
]

TP1_FRACTIONS = [("f33", "1/3"), ("f50", "1/2"), ("f67", "2/3")]
RUNNER_TARGETS = [("r20", "2.0R"), ("r25", "2.5R"), ("r30", "3.0R")]
BE_MODES = [("be_tp1", "on TP1 fill"), ("be_1r", "at +1.0R"), ("be_never", "never")]


@dataclass
class Signal:
    cell_id: str
    component: str
    priority: int
    entry_time: datetime
    entry_date: date
    direction: str
    pnl: float
    tickets: int
    lots: float
    source_csv: str
    status: str = "candidate"
    drop_reason: str = ""


def expected_cells() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for fraction_code, fraction_label in TP1_FRACTIONS:
        for runner_code, runner_label in RUNNER_TARGETS:
            for be_code, be_label in BE_MODES:
                cell_id = f"{fraction_code}_{runner_code}_{be_code}"
                rows.append(
                    {
                        "cell_id": cell_id,
                        "tp1_fraction": fraction_label,
                        "runner_target": runner_label,
                        "be_timing": be_label,
                    }
                )
    return rows


def expected_variants() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell in expected_cells():
        for component, base_name, priority in COMPONENTS:
            variant = f"goal_split_{cell['cell_id']}_{component}"
            rows.append(
                {
                    **cell,
                    "component": component,
                    "base_component": base_name,
                    "priority": priority,
                    "variant": variant,
                }
            )
    return rows


def find_file(variant_dir: Path, variant: str, suffix: str) -> Path | None:
    matches = sorted(variant_dir.glob(f"*_{variant}{suffix}"))
    return matches[-1] if matches else None


def component_ledger(variant_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for expected in expected_variants():
        trade_csv = find_file(variant_dir, expected["variant"], "_trades.csv")
        summary_json = find_file(variant_dir, expected["variant"], "_summary.json")
        html_report = find_file(variant_dir, expected["variant"], ".htm")
        status = "COMPLETE" if trade_csv and summary_json and html_report else "MISSING"
        trades = ""
        elapsed_seconds = ""
        history_quality = ""
        profit_factor = ""
        net_profit = ""
        if summary_json and summary_json.exists():
            try:
                summary = json.loads(summary_json.read_text(encoding="utf-8"))
                trades = summary.get("summary", {}).get("overall", {}).get("trades", "")
                elapsed_seconds = summary.get("elapsed_seconds", "")
                metrics = summary.get("mt5_report_metrics", {})
                history_quality = metrics.get("History Quality", "")
                profit_factor = metrics.get("Profit Factor", "")
                net_profit = metrics.get("Total Net Profit", "")
            except json.JSONDecodeError:
                status = "BAD_SUMMARY_JSON"
        rows.append(
            {
                **expected,
                "status": status,
                "trades": trades,
                "elapsed_seconds": elapsed_seconds,
                "history_quality": history_quality,
                "profit_factor": profit_factor,
                "net_profit": net_profit,
                "trade_csv": str(trade_csv or ""),
                "summary_json": str(summary_json or ""),
                "html_report": str(html_report or ""),
            }
        )
    return rows


def parse_money(value: str) -> float:
    return float((value or "0").replace(" ", ""))


def load_component_signals(row: dict[str, Any]) -> list[Signal]:
    path = Path(row["trade_csv"])
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for trade in csv.DictReader(handle):
            grouped[(trade["entry_time"], trade["direction"])].append(trade)

    signals: list[Signal] = []
    for (entry_time, direction), trades in grouped.items():
        dt = datetime.strptime(entry_time, "%Y.%m.%d %H:%M:%S")
        pnl = sum(parse_money(trade["profit_aed"]) for trade in trades)
        lots = sum(float(trade.get("volume") or 0.0) for trade in trades)
        signals.append(
            Signal(
                cell_id=row["cell_id"],
                component=row["component"],
                priority=int(row["priority"]),
                entry_time=dt,
                entry_date=dt.date(),
                direction=direction,
                pnl=pnl,
                tickets=len(trades),
                lots=lots,
                source_csv=str(path),
            )
        )
    return signals


def dedupe_cell(signals: list[Signal]) -> tuple[list[Signal], list[Signal]]:
    kept: list[Signal] = []
    dropped: list[Signal] = []
    by_direction: dict[str, list[Signal]] = defaultdict(list)
    for signal in signals:
        by_direction[signal.direction].append(signal)

    for direction_signals in by_direction.values():
        ordered = sorted(direction_signals, key=lambda signal: signal.entry_time)
        index = 0
        while index < len(ordered):
            cluster = [ordered[index]]
            start = ordered[index].entry_time
            index += 1
            while index < len(ordered) and ordered[index].entry_time - start <= timedelta(minutes=4):
                cluster.append(ordered[index])
                index += 1
            winner = sorted(cluster, key=lambda signal: (signal.priority, signal.entry_time, signal.component))[0]
            winner.status = "kept"
            kept.append(winner)
            for signal in cluster:
                if signal is winner:
                    continue
                signal.status = "dropped"
                signal.drop_reason = f"priority_dedupe_kept_{winner.component}"
                dropped.append(signal)

    return sorted(kept, key=lambda signal: signal.entry_time), sorted(dropped, key=lambda signal: signal.entry_time)


def market_days(start: date = FROM_DATE, end: date = TO_DATE) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def max_closed_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        if equity > peak:
            peak = equity
        max_dd = max(max_dd, peak - equity)
    return max_dd


def metrics(
    signals: list[Signal],
    stress_per_ticket: float = 0.0,
    market_start: date = FROM_DATE,
    market_end: date = TO_DATE,
) -> dict[str, Any]:
    pnl = [signal.pnl - stress_per_ticket * signal.tickets for signal in signals]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    active_dates = {signal.entry_date for signal in signals}
    weekdays = market_days(market_start, market_end)
    sorted_pnl = sorted(pnl, reverse=True)
    return {
        "signals": len(signals),
        "tickets": sum(signal.tickets for signal in signals),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round((len(wins) / len(signals) * 100.0) if signals else 0.0, 2),
        "net": round(sum(pnl), 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round((gross_profit / gross_loss) if gross_loss else 0.0, 4),
        "avg_win": round((gross_profit / len(wins)) if wins else 0.0, 2),
        "avg_loss": round((gross_loss / len(losses)) if losses else 0.0, 2),
        "win_loss_ratio": round(((gross_profit / len(wins)) / (gross_loss / len(losses))) if wins and losses else 0.0, 4),
        "active_days": len(active_dates),
        "market_weekdays": len(weekdays),
        "active_day_pct": round((len(active_dates) / len(weekdays) * 100.0) if weekdays else 0.0, 2),
        "max_closed_dd": round(max_closed_drawdown(pnl), 2),
        "top10_removed": round(sum(sorted_pnl[10:]) if len(sorted_pnl) > 10 else sum(sorted_pnl), 2),
        "top25_removed": round(sum(sorted_pnl[25:]) if len(sorted_pnl) > 25 else sum(sorted_pnl), 2),
        "top100_removed": round(sum(sorted_pnl[100:]) if len(sorted_pnl) > 100 else sum(sorted_pnl), 2),
    }


def signal_to_row(signal: Signal) -> dict[str, Any]:
    return {
        "cell_id": signal.cell_id,
        "component": signal.component,
        "priority": signal.priority,
        "entry_time": signal.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
        "entry_date": signal.entry_date.isoformat(),
        "direction": signal.direction,
        "signal_pnl": round(signal.pnl, 2),
        "tickets": signal.tickets,
        "lots": round(signal.lots, 2),
        "status": signal.status,
        "drop_reason": signal.drop_reason,
        "source_csv": signal.source_csv,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def cell_score(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["goal_hit"],
        row["near_goal"],
        row["win_rate_pct"] >= 50.0,
        row["win_loss_ratio"] >= 2.0,
        row["active_day_pct"],
        row["win_loss_ratio"],
        row["win_rate_pct"],
        row["net"],
    )


def analyze(variant_dir: Path) -> dict[str, Any]:
    ledger = component_ledger(variant_dir)
    complete_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        if row["status"] == "COMPLETE":
            complete_by_cell[row["cell_id"]].append(row)

    cell_rows: list[dict[str, Any]] = []
    kept_rows: list[dict[str, Any]] = []
    dropped_rows: list[dict[str, Any]] = []
    for cell in expected_cells():
        cell_id = cell["cell_id"]
        components = complete_by_cell.get(cell_id, [])
        if len(components) != 3:
            cell_rows.append(
                {
                    **cell,
                    "status": "INCOMPLETE",
                    "completed_components": len(components),
                    "signals": 0,
                    "tickets": 0,
                    "win_rate_pct": 0.0,
                    "win_loss_ratio": 0.0,
                    "active_day_pct": 0.0,
                    "profit_factor": 0.0,
                    "net": 0.0,
                    "max_closed_dd": 0.0,
                    "last12_win_rate_pct": 0.0,
                    "last12_win_loss_ratio": 0.0,
                    "stress_010_net": 0.0,
                    "stress_030_net": 0.0,
                    "goal_hit": False,
                    "near_goal": False,
                }
            )
            continue

        candidates: list[Signal] = []
        for component in components:
            candidates.extend(load_component_signals(component))
        kept, dropped = dedupe_cell(candidates)
        kept_rows.extend(signal_to_row(signal) for signal in kept)
        dropped_rows.extend(signal_to_row(signal) for signal in dropped)

        base = metrics(kept)
        last12 = metrics([signal for signal in kept if signal.entry_date >= LAST12_START], market_start=LAST12_START, market_end=TO_DATE)
        stress_010 = metrics(kept, stress_per_ticket=0.10)
        stress_030 = metrics(kept, stress_per_ticket=0.30)
        goal_hit = base["win_rate_pct"] >= 50.0 and base["win_loss_ratio"] >= 2.0 and base["active_day_pct"] >= 90.0
        near_goal = base["win_rate_pct"] >= 48.0 and base["win_loss_ratio"] >= 1.8 and base["active_day_pct"] >= 80.0
        cell_rows.append(
            {
                **cell,
                "status": "COMPLETE",
                "completed_components": 3,
                **base,
                "last12_signals": last12["signals"],
                "last12_win_rate_pct": last12["win_rate_pct"],
                "last12_win_loss_ratio": last12["win_loss_ratio"],
                "last12_active_day_pct": last12["active_day_pct"],
                "last12_net": last12["net"],
                "stress_010_net": stress_010["net"],
                "stress_010_pf": stress_010["profit_factor"],
                "stress_030_net": stress_030["net"],
                "stress_030_pf": stress_030["profit_factor"],
                "goal_hit": goal_hit,
                "near_goal": near_goal,
            }
        )

    write_csv(OUT_LEDGER_CSV, ledger)
    write_csv(OUT_CSV, cell_rows)
    write_csv(OUT_KEPT_CSV, kept_rows)
    write_csv(OUT_DROPPED_CSV, dropped_rows)

    complete_cells = [row for row in cell_rows if row["status"] == "COMPLETE"]
    frontier = sorted(complete_cells, key=cell_score, reverse=True)[:5]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "variant_dir": str(variant_dir),
        "status": "COMPLETE" if len(complete_cells) == 27 else "INCOMPLETE",
        "complete_cells": len(complete_cells),
        "expected_cells": 27,
        "complete_components": sum(1 for row in ledger if row["status"] == "COMPLETE"),
        "expected_components": 81,
        "ledger_csv": str(OUT_LEDGER_CSV),
        "cell_csv": str(OUT_CSV),
        "kept_signals_csv": str(OUT_KEPT_CSV),
        "dropped_signals_csv": str(OUT_DROPPED_CSV),
        "frontier": frontier,
        "cells": cell_rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 Momentum Step 1 Split-Shape Grid Frontier",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester component reports composed into signal-level books. No live/demo runtime, chart, preset, order, or position was changed by this analyzer.",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Complete cells: `{payload['complete_cells']} / {payload['expected_cells']}`",
        f"- Complete MT5 components: `{payload['complete_components']} / {payload['expected_components']}`",
        f"- Source directory: `{payload['variant_dir']}`",
        f"- Component ledger: `{payload['ledger_csv']}`",
        f"- Kept signals: `{payload['kept_signals_csv']}`",
        f"- Dropped signals: `{payload['dropped_signals_csv']}`",
        "",
        "## Frontier",
        "",
        "| Cell | WR | W/L | Active days | PF | Net | DD | Last12 WR | Last12 W/L | +0.10 net | +0.30 net | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["frontier"]:
        lines.append(
            f"| `{row['cell_id']}` | {row['win_rate_pct']}% | {row['win_loss_ratio']} | "
            f"{row['active_day_pct']}% | {row['profit_factor']} | {row['net']} | {row['max_closed_dd']} | "
            f"{row['last12_win_rate_pct']}% | {row['last12_win_loss_ratio']} | "
            f"{row['stress_010_net']} | {row['stress_030_net']} | "
            f"{'GOAL_HIT' if row['goal_hit'] else ('NEAR_GOAL' if row['near_goal'] else 'FRONTIER')} |"
        )

    lines += [
        "",
        "## All Cells",
        "",
        "| Cell | Components | WR | W/L | Active days | PF | Net | DD | Goal hit | Near goal |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["cells"]:
        lines.append(
            f"| `{row['cell_id']}` | {row['completed_components']}/3 | {row['win_rate_pct']}% | "
            f"{row['win_loss_ratio']} | {row['active_day_pct']}% | {row['profit_factor']} | "
            f"{row['net']} | {row['max_closed_dd']} | {row['goal_hit']} | {row['near_goal']} |"
        )

    lines += [
        "",
        "## Interpretation Rules",
        "",
        "- Headline WR and W/L are signal-level only.",
        "- Daily activity denominator is weekdays in the exam window; this is conservative around holidays.",
        "- `GOAL_HIT` requires WR >= 50%, realized W/L >= 2.0, and active-day coverage >= 90%.",
        "- `NEAR_GOAL` is a visibility label only: WR >= 48%, W/L >= 1.8, and active-day coverage >= 80%.",
        "- No Step 1 conclusion is final until all 27 cells and 81 MT5 component runs are complete.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose the A1 Step 1 split-shape grid into signal-level metrics.")
    parser.add_argument("--variant-dir", type=Path, default=DEFAULT_VARIANT_DIR)
    args = parser.parse_args()
    payload = analyze(args.variant_dir)
    print(OUT_MD)
    print(f"{payload['status']}: {payload['complete_cells']}/{payload['expected_cells']} cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
