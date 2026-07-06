from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_M5_EARLY_ADVERSE_EXIT_EXACT_PROBE_PREREG_2026_07_05.md"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "OWNER_GOAL_SPLIT_F33_R30_BE1R_EARLY_ADVERSE_202207_202606"

COMPONENTS = [
    ("v6", "goal_split_f33_r30_be_1r_v6", 1),
    ("weak", "goal_split_f33_r30_be_1r_weak", 2),
    ("v13", "goal_split_f33_r30_be_1r_v13", 3),
]

CELLS = [
    {"cell_id": "eae30_r035", "minutes": "30", "adverse_r": "0.35"},
    {"cell_id": "eae60_r035", "minutes": "60", "adverse_r": "0.35"},
    {"cell_id": "eae30_r050", "minutes": "30", "adverse_r": "0.50"},
    {"cell_id": "eae60_r050", "minutes": "60", "adverse_r": "0.50"},
]


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


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def parse_money(value: str) -> float:
    return float((value or "0").replace(" ", ""))


def mt5_date(value: str) -> date:
    return datetime.strptime(value, "%Y.%m.%d").date()


def trading_weekday_count(start: date, end: date) -> int:
    count = 0
    cursor = start
    while cursor <= end:
        if cursor.weekday() < 5:
            count += 1
        cursor += timedelta(days=1)
    return count


def max_closed_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def load_component_signals(cell_id: str, component: str, priority: int, path: Path) -> list[Signal]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[(row["entry_time"], row["direction"])].append(row)

    signals: list[Signal] = []
    for (entry_time, direction), rows in grouped.items():
        dt = datetime.strptime(entry_time, "%Y.%m.%d %H:%M:%S")
        signals.append(
            Signal(
                cell_id=cell_id,
                component=component,
                priority=priority,
                entry_time=dt,
                entry_date=dt.date(),
                direction=direction,
                pnl=sum(parse_money(row["profit_aed"]) for row in rows),
                tickets=len(rows),
                lots=sum(float(row.get("volume") or 0.0) for row in rows),
                source_csv=str(path),
            )
        )
    return signals


def dedupe(signals: list[Signal]) -> tuple[list[Signal], list[dict[str, Any]]]:
    kept: list[Signal] = []
    dropped: list[dict[str, Any]] = []
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
            kept.append(winner)
            for signal in cluster:
                if signal is winner:
                    continue
                dropped.append(
                    {
                        "cell_id": signal.cell_id,
                        "entry_time": signal.entry_time.isoformat(sep=" "),
                        "direction": signal.direction,
                        "component": signal.component,
                        "pnl": round(signal.pnl, 2),
                        "drop_reason": f"priority_dedupe_kept_{winner.component}",
                    }
                )
    return sorted(kept, key=lambda signal: signal.entry_time), dropped


def metrics(signals: list[Signal], from_date: str, to_date: str) -> dict[str, Any]:
    start = mt5_date(from_date)
    end = mt5_date(to_date)
    pnl = [signal.pnl for signal in signals]
    wins = [value for value in pnl if value > 0]
    losses = [-value for value in pnl if value < 0]
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    wl_ratio = avg_win / avg_loss if avg_loss else None
    active_dates = {signal.entry_date for signal in signals}
    weekdays = trading_weekday_count(start, end)
    active_pct = len(active_dates) / weekdays * 100.0 if weekdays else 0.0
    sorted_pnl = sorted(pnl, reverse=True)
    win_rate = len(wins) / len(signals) * 100.0 if signals else 0.0
    return {
        "signals": len(signals),
        "tickets": sum(signal.tickets for signal in signals),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(win_rate, 2),
        "avg_win_usd": round(avg_win, 2),
        "avg_loss_usd": round(avg_loss, 2),
        "win_loss_ratio": round(wl_ratio, 4) if wl_ratio is not None else None,
        "net_usd": round(sum(pnl), 2),
        "gross_profit_usd": round(gross_profit, 2),
        "gross_loss_usd": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "active_days": len(active_dates),
        "market_weekdays": weekdays,
        "active_day_pct": round(active_pct, 2),
        "max_closed_dd_usd": round(max_closed_drawdown(pnl), 2),
        "top10_removed_net_usd": round(sum(sorted_pnl[10:]) if len(sorted_pnl) > 10 else sum(sorted_pnl), 2),
        "top25_removed_net_usd": round(sum(sorted_pnl[25:]) if len(sorted_pnl) > 25 else sum(sorted_pnl), 2),
        "owner_core_shape_pass": bool(signals and win_rate >= 50.0 and wl_ratio is not None and wl_ratio >= 2.0),
        "owner_daily_frequency_pass": active_pct >= 90.0,
    }


def last12_metrics(signals: list[Signal], to_date: str) -> dict[str, Any]:
    end = mt5_date(to_date)
    start = date(end.year - 1, end.month, end.day)
    subset = [signal for signal in signals if signal.entry_date >= start]
    return metrics(subset, start.strftime("%Y.%m.%d"), to_date)


def signal_row(signal: Signal) -> dict[str, Any]:
    return {
        "cell_id": signal.cell_id,
        "entry_time": signal.entry_time.isoformat(sep=" "),
        "entry_date": signal.entry_date.isoformat(),
        "direction": signal.direction,
        "component": signal.component,
        "priority": signal.priority,
        "signal_pnl_usd": round(signal.pnl, 2),
        "tickets": signal.tickets,
        "lots": signal.lots,
        "source_csv": signal.source_csv,
    }


def build_variants() -> tuple[list[a1.Variant], dict[str, dict[str, Any]]]:
    base_by_name = {variant.name: variant for variant in a1.VARIANTS}
    variants: list[a1.Variant] = []
    index: dict[str, dict[str, Any]] = {}
    for cell in CELLS:
        for component, base_name, priority in COMPONENTS:
            base = base_by_name[base_name]
            name = f"split_f33_r30_be1r_{cell['cell_id']}_{component}"
            variants.append(
                a1.Variant(
                    name=name,
                    label=(
                        f"{base.label}; early adverse exit after {cell['minutes']}m "
                        f"at -{cell['adverse_r']}R"
                    ),
                    run_id=f"BT_A1_XAU_M5_SPLIT_F33_R30_BE1R_{cell['cell_id']}_{component}".upper(),
                    tester_inputs={
                        **base.tester_inputs,
                        "InpEarlyAdverseExitEnabled": "true",
                        "InpEarlyAdverseExitShadowOnly": "false",
                        "InpEarlyAdverseExitAfterMinutes": cell["minutes"],
                        "InpEarlyAdverseExitR": cell["adverse_r"],
                        "InpManagementLogMode": "1",
                    },
                )
            )
            index[name] = {
                "cell_id": cell["cell_id"],
                "component": component,
                "base_name": base_name,
                "priority": priority,
                "minutes": cell["minutes"],
                "adverse_r": cell["adverse_r"],
            }
    return variants, index


def cell_decision(m: dict[str, Any]) -> str:
    if m["owner_core_shape_pass"] and m["owner_daily_frequency_pass"]:
        return "OWNER_GOAL_HIT_REVIEW_REQUIRED"
    if m["owner_core_shape_pass"]:
        return "CORE_SHAPE_HIT_FREQUENCY_GAP"
    return "REJECT_NO_OWNER_CORE_SHAPE"


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 Early Adverse Exit Exact Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester in isolated root, followed by deterministic component dedupe and manual signal-level aggregation from exported trade CSVs.",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Preregistration: `{payload['preregistration']}`",
        f"- Period: `{FROM_DATE}` to `{TO_DATE}`",
        f"- Reviewer spend rule: `{payload['review_spend_rule']}`",
        "",
        "## Owner Metrics By Cell",
        "",
        "| Cell | Signals | WR% | W/L | Active% | PF | Manual P&L USD | Max DD USD | Last12 WR/WL | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for cell in payload["cells"]:
        m = cell["metrics"]
        last12 = cell["last12_metrics"]
        lines.append(
            f"| `{cell['cell_id']}` | {m['signals']} | {m['win_rate_pct']:.2f} | "
            f"{m['win_loss_ratio'] or 0.0:.4f} | {m['active_day_pct']:.2f} | "
            f"{m['profit_factor'] or 0.0:.4f} | {m['net_usd']:.2f} | "
            f"{m['max_closed_dd_usd']:.2f} | {last12['win_rate_pct']:.2f}/{last12['win_loss_ratio'] or 0.0:.2f} | "
            f"`{cell['decision']}` |"
        )

    lines.extend(
        [
            "",
            "## Component Contribution",
            "",
            "| Cell | Component | Priority | Raw signals | Kept signals | Manual P&L USD | Trade CSV |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for cell in payload["cells"]:
        for component in cell["components"]:
            lines.append(
                f"| `{cell['cell_id']}` | `{component['component']}` | {component['priority']} | "
                f"{component['raw_signals']} | {component['kept_signals']} | "
                f"{component['kept_net_usd']:.2f} | `{component['trade_csv']}` |"
            )

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            payload["verdict"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact MT5 early adverse exit probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    variants, variant_index = build_variants()
    a1.VARIANTS = variants
    report_md = REPORTS / "A1_XAU_M5_EARLY_ADVERSE_EXIT_EXACT_PROBE_202207_202606.md"
    report_json = report_md.with_suffix(".json")
    mt5_payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=report_md,
        report_json=report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )

    result_by_name = {result["name"]: result for result in mt5_payload["variants"]}
    cells: list[dict[str, Any]] = []
    all_kept: list[Signal] = []
    all_dropped: list[dict[str, Any]] = []

    for cell in CELLS:
        cell_id = cell["cell_id"]
        raw_signals: list[Signal] = []
        component_rows: list[dict[str, Any]] = []
        component_raw_by_name: dict[str, list[Signal]] = {}

        for component, _base_name, priority in COMPONENTS:
            variant_name = f"split_f33_r30_be1r_{cell_id}_{component}"
            result = result_by_name[variant_name]
            trade_csv = Path(result["trade_csv"])
            component_signals = load_component_signals(cell_id, component, priority, trade_csv)
            component_raw_by_name[component] = component_signals
            raw_signals.extend(component_signals)
            component_rows.append(
                {
                    "component": component,
                    "priority": priority,
                    "trade_csv": str(trade_csv),
                    "raw_signals": len(component_signals),
                    "raw_tickets": sum(signal.tickets for signal in component_signals),
                    "mt5_result": result,
                }
            )

        kept, dropped = dedupe(raw_signals)
        all_kept.extend(kept)
        all_dropped.extend(dropped)
        kept_by_component = Counter(signal.component for signal in kept)
        kept_net_by_component = defaultdict(float)
        for signal in kept:
            kept_net_by_component[signal.component] += signal.pnl

        for component in component_rows:
            name = component["component"]
            component["kept_signals"] = kept_by_component[name]
            component["kept_net_usd"] = round(kept_net_by_component[name], 2)

        m = metrics(kept, FROM_DATE, TO_DATE)
        last12 = last12_metrics(kept, TO_DATE)
        cells.append(
            {
                **cell,
                "metrics": m,
                "last12_metrics": last12,
                "decision": cell_decision(m),
                "components": component_rows,
                "dedupe": {
                    "kept_signals": len(kept),
                    "dropped_signals": len(dropped),
                    "window_minutes": 4,
                },
            }
        )

    any_owner = any(cell["decision"] == "OWNER_GOAL_HIT_REVIEW_REQUIRED" for cell in cells)
    any_core = any(cell["decision"] == "CORE_SHAPE_HIT_FREQUENCY_GAP" for cell in cells)
    if any_owner:
        status = "OWNER_GOAL_HIT_REVIEW_REQUIRED"
        verdict = "At least one exact MT5 cell reached the owner core shape and daily-frequency target. Freeze artifacts and prepare a full reviewer packet before any demo spec."
    elif any_core:
        status = "CORE_SHAPE_HIT_FREQUENCY_GAP_PACKAGE_BEFORE_REVIEW"
        verdict = "At least one exact MT5 cell reached WR >= 50% and W/L >= 2.0, but daily frequency did not reach the owner target. Treat as a serious clue, not demo-ready."
    else:
        status = "REJECT_NO_OWNER_CORE_SHAPE"
        verdict = "No exact MT5 early-adverse-exit cell reached both WR >= 50% and realized W/L >= 2.0. Do not spend the reviewer token on this branch."

    kept_csv = REPORTS / "A1_XAU_M5_EARLY_ADVERSE_EXIT_EXACT_PROBE_KEPT_SIGNALS_202207_202606.csv"
    dropped_csv = REPORTS / "A1_XAU_M5_EARLY_ADVERSE_EXIT_EXACT_PROBE_DROPPED_SIGNALS_202207_202606.csv"
    with kept_csv.open("w", encoding="utf-8", newline="") as handle:
        fields = list(signal_row(all_kept[0]).keys()) if all_kept else ["cell_id", "entry_time"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(signal_row(signal) for signal in all_kept)
    with dropped_csv.open("w", encoding="utf-8", newline="") as handle:
        fields = list(all_dropped[0].keys()) if all_dropped else ["cell_id", "entry_time"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_dropped)

    payload = {
        **mt5_payload,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": status,
        "verdict": verdict,
        "preregistration": str(PREREG),
        "cells": cells,
        "variant_index": variant_index,
        "artifacts": {
            "report_md": str(report_md),
            "report_json": str(report_json),
            "kept_signals_csv": str(kept_csv),
            "dropped_signals_csv": str(dropped_csv),
        },
        "review_spend_rule": "No reviewer unless exact MT5 reaches WR >= 50% and realized W/L >= 2.0.",
    }
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "cells": [{"cell_id": cell["cell_id"], "metrics": cell["metrics"], "decision": cell["decision"]} for cell in cells], "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
