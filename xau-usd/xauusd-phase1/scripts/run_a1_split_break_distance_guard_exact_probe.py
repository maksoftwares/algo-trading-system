from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PHASE1_ROOT / "outputs" / "reports"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_M5_SPLIT_BREAK_DISTANCE_GUARD_EXACT_PROBE_PREREG_2026_07_05.md"
FROM_DATE = "2022.07.01"
TO_DATE = "2026.06.30"
TAG = "OWNER_GOAL_SPLIT_F33_R30_BE1R_MINBD08994_202207_202606"
THRESHOLD = "0.8994"

COMPONENTS = [
    ("v6", "goal_split_f33_r30_be_1r_v6", 1),
    ("weak", "goal_split_f33_r30_be_1r_weak", 2),
    ("v13", "goal_split_f33_r30_be_1r_v13", 3),
]


@dataclass
class Signal:
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


def load_component_signals(component: str, priority: int, path: Path) -> list[Signal]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[(row["entry_time"], row["direction"])].append(row)

    signals: list[Signal] = []
    for (entry_time, direction), rows in grouped.items():
        dt = datetime.strptime(entry_time, "%Y.%m.%d %H:%M:%S")
        signals.append(
            Signal(
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
    return {
        "signals": len(signals),
        "tickets": sum(signal.tickets for signal in signals),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round((len(wins) / len(signals) * 100.0) if signals else 0.0, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "win_loss_ratio": round(wl_ratio, 4) if wl_ratio is not None else None,
        "net": round(sum(pnl), 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "active_days": len(active_dates),
        "market_weekdays": weekdays,
        "active_day_pct": round(active_pct, 2),
        "max_closed_dd": round(max_closed_drawdown(pnl), 2),
        "top10_removed": round(sum(sorted_pnl[10:]) if len(sorted_pnl) > 10 else sum(sorted_pnl), 2),
        "top25_removed": round(sum(sorted_pnl[25:]) if len(sorted_pnl) > 25 else sum(sorted_pnl), 2),
        "owner_core_shape_pass": bool(signals and len(wins) / len(signals) * 100.0 >= 50.0 and wl_ratio is not None and wl_ratio >= 2.0),
        "owner_daily_frequency_pass": active_pct >= 90.0,
    }


def last12_metrics(signals: list[Signal], to_date: str) -> dict[str, Any]:
    end = mt5_date(to_date)
    start = date(end.year - 1, end.month, end.day)
    subset = [signal for signal in signals if signal.entry_date >= start]
    return metrics(subset, start.strftime("%Y.%m.%d"), to_date)


def signal_row(signal: Signal) -> dict[str, Any]:
    return {
        "entry_time": signal.entry_time.isoformat(sep=" "),
        "entry_date": signal.entry_date.isoformat(),
        "direction": signal.direction,
        "component": signal.component,
        "priority": signal.priority,
        "signal_pnl": round(signal.pnl, 2),
        "tickets": signal.tickets,
        "lots": signal.lots,
        "source_csv": signal.source_csv,
    }


def guarded_variants() -> list[a1.Variant]:
    base_by_name = {variant.name: variant for variant in a1.VARIANTS}
    variants: list[a1.Variant] = []
    for component, base_name, _priority in COMPONENTS:
        base = base_by_name[base_name]
        variants.append(
            a1.Variant(
                name=f"split_f33_r30_be1r_minbd08994_{component}",
                label=f"{base.label}; exact guard MinBreakDistanceAtr={THRESHOLD}",
                run_id=f"BT_A1_XAU_M5_SPLIT_F33_R30_BE1R_MINBD08994_{component.upper()}",
                tester_inputs={
                    **base.tester_inputs,
                    "InpMinBreakDistanceAtr": THRESHOLD,
                    "InpMaxBreakDistanceAtr": "0.0",
                },
            )
        )
    return variants


def render(payload: dict[str, Any]) -> str:
    m = payload["metrics"]
    last12 = payload["last12_metrics"]
    lines = [
        "# A1 XAU M5 Split Break-Distance Guard Exact Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact MT5 Strategy Tester in isolated root, followed by deterministic component dedupe. No live/demo runtime state was touched.",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- Preregistration: `{payload['preregistration']}`",
        f"- Period: `{FROM_DATE}` to `{TO_DATE}`",
        f"- Guard: `InpMinBreakDistanceAtr={THRESHOLD}`",
        f"- Signals: `{m['signals']}`",
        f"- Tickets: `{m['tickets']}`",
        "",
        "## Owner Metrics",
        "",
        "| Signals | WR% | W/L | Active% | PF | Manual P&L | Max DD | Last12 WR/WL | Decision |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        (
            f"| {m['signals']} | {m['win_rate_pct']:.2f} | {m['win_loss_ratio'] or 0.0:.4f} | "
            f"{m['active_day_pct']:.2f} | {m['profit_factor'] or 0.0:.4f} | {m['net']:.2f} | "
            f"{m['max_closed_dd']:.2f} | {last12['win_rate_pct']:.2f}/{last12['win_loss_ratio'] or 0.0:.2f} | "
            f"`{payload['decision']}` |"
        ),
        "",
        "## Component Inputs",
        "",
        "| Component | Priority | Trades CSV |",
        "| --- | ---: | --- |",
    ]
    for component in payload["components"]:
        lines.append(f"| `{component['component']}` | {component['priority']} | `{component['trade_csv']}` |")
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
    parser = argparse.ArgumentParser(description="Run exact MT5 split break-distance guard probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    require_file(PREREG)
    variants = guarded_variants()
    a1.VARIANTS = variants
    report_md = REPORTS / "A1_XAU_M5_SPLIT_BREAK_DISTANCE_GUARD_EXACT_PROBE_202207_202606.md"
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

    component_results: list[dict[str, Any]] = []
    all_signals: list[Signal] = []
    result_by_suffix = {result["name"].rsplit("_", 1)[-1]: result for result in mt5_payload["variants"]}
    for component, _base_name, priority in COMPONENTS:
        result = result_by_suffix[component]
        trade_csv = Path(result["trade_csv"])
        component_signals = load_component_signals(component, priority, trade_csv)
        all_signals.extend(component_signals)
        component_results.append(
            {
                "component": component,
                "priority": priority,
                "trade_csv": str(trade_csv),
                "raw_signals": len(component_signals),
                "raw_tickets": sum(signal.tickets for signal in component_signals),
                "mt5_result": result,
            }
        )

    kept, dropped = dedupe(all_signals)
    m = metrics(kept, FROM_DATE, TO_DATE)
    last12 = last12_metrics(kept, TO_DATE)
    if m["owner_core_shape_pass"] and m["owner_daily_frequency_pass"]:
        status = "OWNER_GOAL_HIT_REVIEW_REQUIRED"
        decision = "OWNER_GOAL"
        verdict = "Exact MT5 run reached owner core shape and daily frequency. Package full robustness before spending the reviewer token."
    elif m["owner_core_shape_pass"]:
        status = "CORE_SHAPE_HIT_FREQUENCY_GAP_PACKAGE_BEFORE_REVIEW"
        decision = "CORE_SHAPE_FREQ_GAP"
        verdict = "Exact MT5 run reached WR >= 50% and W/L >= 2.0, but active-day frequency failed. This is a clue, not demo-ready."
    else:
        status = "REJECT_NO_OWNER_CORE_SHAPE"
        decision = "FAIL_SHAPE"
        verdict = "Exact MT5 run did not reach the owner core shape. Do not spend the reviewer token on this probe."

    kept_csv = REPORTS / "A1_XAU_M5_SPLIT_BREAK_DISTANCE_GUARD_EXACT_PROBE_KEPT_SIGNALS_202207_202606.csv"
    dropped_csv = REPORTS / "A1_XAU_M5_SPLIT_BREAK_DISTANCE_GUARD_EXACT_PROBE_DROPPED_SIGNALS_202207_202606.csv"
    with kept_csv.open("w", encoding="utf-8", newline="") as handle:
        fields = list(signal_row(kept[0]).keys()) if kept else ["entry_time"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(signal_row(signal) for signal in kept)
    with dropped_csv.open("w", encoding="utf-8", newline="") as handle:
        fields = list(dropped[0].keys()) if dropped else ["entry_time"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dropped)

    payload = {
        **mt5_payload,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": status,
        "decision": decision,
        "verdict": verdict,
        "preregistration": str(PREREG),
        "guard": {"InpMinBreakDistanceAtr": THRESHOLD, "InpMaxBreakDistanceAtr": "0.0"},
        "components": component_results,
        "metrics": m,
        "last12_metrics": last12,
        "dedupe": {"kept_signals": len(kept), "dropped_signals": len(dropped), "window_minutes": 4},
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
    print(json.dumps({"status": status, "metrics": m, "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
