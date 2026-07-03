from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_state_guard_search import apply_state_guard


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
PACKAGES = {
    "rr0p7": {
        "title": "A1 XAU M5 Momentum Risk-Balanced Exact MT5 Package - 2026-07-03",
        "backtest_dir": REPORTS_DIR
        / "mt5_backtests"
        / "a1_momentum_variants_risk_balanced_exact_2024_07_2026_06_20260701",
        "output_stem": "A1_XAU_M5_MOMENTUM_RISK_BALANCED_EXACT_MT5_PACKAGE_2026_07_03",
        "components": [
            "risk_norm_rb_freq_weak_hours_all8",
            "risk_norm_rb_v4_combo_all8",
            "risk_norm_rb_v6_max2_all8",
            "risk_norm_rb_v13_rr0p7_all8_22",
            "risk_norm_rb_v13_rr0p6_nomorning_all8_22",
        ],
    },
    "rr1p0": {
        "title": "A1 XAU M5 Momentum Risk-Balanced RR1 Exact MT5 Package - 2026-07-03",
        "backtest_dir": REPORTS_DIR
        / "mt5_backtests"
        / "a1_momentum_variants_risk_balanced_rr1_exact_2024_07_2026_06_20260701",
        "output_stem": "A1_XAU_M5_MOMENTUM_RISK_BALANCED_RR1_EXACT_MT5_PACKAGE_2026_07_03",
        "components": [
            "risk_norm_rb_rr1_freq_weak_hours_all8",
            "risk_norm_rb_rr1_v4_combo_all8",
            "risk_norm_rb_rr1_v6_max2_all8",
            "risk_norm_rb_rr1_v13_all8_22",
            "risk_norm_rb_rr1_v13_nomorning_all8_22",
        ],
    },
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def parse_time(value: str) -> datetime:
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"unsupported timestamp: {value}")


def market_days(start: date, end: date) -> int:
    current = start
    total = 0
    while current <= end:
        if current.weekday() < 5:
            total += 1
        current += timedelta(days=1)
    return total


def profit_factor(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return round(drawdown, 2)


def top_removed(values: list[float], count: int) -> float:
    wins = sorted((value for value in values if value > 0), reverse=True)
    return round(sum(values) - sum(wins[:count]), 2)


def rolling(values: list[float], window: int) -> dict[str, Any]:
    if len(values) < window:
        return {"window": window, "available": False, "negative": None, "worst": None}
    nets = [sum(values[index : index + window]) for index in range(len(values) - window + 1)]
    return {
        "window": window,
        "available": True,
        "negative": sum(value < 0 for value in nets),
        "worst": round(min(nets), 2),
    }


def read_trade_csv(path: Path, component: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            entry_time = parse_time(row["entry_time"])
            exit_time = parse_time(row["exit_time"])
            rows.append(
                {
                    "variant": component,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "entry_date": entry_time.date().isoformat(),
                    "exit_date": exit_time.date().isoformat(),
                    "entry_hour": int(row.get("entry_hour") or entry_time.hour),
                    "direction": row["direction"],
                    "profit": float(row["profit_aed"]),
                    "volume": float(row["volume"]),
                    "exit_comment": row.get("exit_comment", ""),
                }
            )
    return rows


def load_components(backtest_dir: Path, components: list[str]) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    loaded: dict[str, list[dict[str, Any]]] = {}
    missing: list[str] = []
    for component in components:
        matches = sorted(backtest_dir.glob(f"*_XAUUSD_M5_{component}_trades.csv"))
        if not matches:
            missing.append(component)
            continue
        loaded[component] = read_trade_csv(matches[0], component)
    return loaded, missing


def dedupe(rows: list[dict[str, Any]], window_minutes: int) -> tuple[list[dict[str, Any]], int]:
    ordered = sorted(rows, key=lambda row: (row["entry_time"], row["variant"], row["direction"]))
    kept: list[dict[str, Any]] = []
    dropped = 0
    window_seconds = window_minutes * 60
    for row in ordered:
        duplicate = False
        for previous in reversed(kept[-30:]):
            delta = abs((row["entry_time"] - previous["entry_time"]).total_seconds())
            if delta > window_seconds:
                break
            if row["direction"] == previous["direction"]:
                duplicate = True
                break
        if duplicate:
            dropped += 1
            continue
        kept.append(row)
    return kept, dropped


def summarize(label: str, rows: list[dict[str, Any]], duplicate_drops: int, guard_stats: dict[str, Any]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row["exit_time"], row["entry_time"], row["variant"]))
    values = [row["profit"] for row in ordered]
    start = min(row["entry_time"].date() for row in ordered)
    end = max(row["entry_time"].date() for row in ordered)
    market_day_count = market_days(start, end)
    by_day: dict[date, list[float]] = defaultdict(list)
    by_month: dict[str, list[float]] = defaultdict(list)
    by_quarter: dict[str, list[float]] = defaultdict(list)
    by_component: dict[str, list[float]] = defaultdict(list)
    by_direction: dict[str, list[float]] = defaultdict(list)
    for row in ordered:
        day = row["entry_time"].date()
        by_day[day].append(row["profit"])
        by_month[row["entry_time"].strftime("%Y-%m")].append(row["profit"])
        quarter = (row["entry_time"].month - 1) // 3 + 1
        by_quarter[f"{row['entry_time'].year}-Q{quarter}"].append(row["profit"])
        by_component[row["variant"]].append(row["profit"])
        by_direction[row["direction"]].append(row["profit"])
    wins = sum(value > 0 for value in values)
    lots = sorted(row["volume"] for row in ordered)
    result = {
        "label": label,
        "trades": len(ordered),
        "wins": wins,
        "losses": len(ordered) - wins,
        "win_rate_pct": round(100.0 * wins / len(ordered), 2),
        "profit_factor": profit_factor(values),
        "net_usd": round(sum(values), 2),
        "avg_usd": round(sum(values) / len(ordered), 2),
        "max_closed_drawdown_usd": max_drawdown(values),
        "date_start": start.isoformat(),
        "date_end": end.isoformat(),
        "market_days": market_day_count,
        "active_days": len(by_day),
        "trades_per_market_day": round(len(ordered) / market_day_count, 2),
        "three_plus_market_day_pct": round(100.0 * sum(len(day_rows) >= 3 for day_rows in by_day.values()) / market_day_count, 2),
        "positive_active_day_pct": round(100.0 * sum(sum(day_rows) > 0 for day_rows in by_day.values()) / len(by_day), 2),
        "positive_months": sum(sum(values_for_period) > 0 for values_for_period in by_month.values()),
        "negative_months": sum(sum(values_for_period) <= 0 for values_for_period in by_month.values()),
        "negative_quarters": sum(sum(values_for_period) <= 0 for values_for_period in by_quarter.values()),
        "top50_removed_usd": top_removed(values, 50),
        "top100_removed_usd": top_removed(values, 100),
        "top200_removed_usd": top_removed(values, 200),
        "top300_removed_usd": top_removed(values, 300),
        "rolling100": rolling(values, 100),
        "rolling250": rolling(values, 250),
        "rolling500": rolling(values, 500),
        "duplicate_drops": duplicate_drops,
        "guard_stats": guard_stats,
        "lot_min": min(lots),
        "lot_median": lots[len(lots) // 2],
        "lot_max": max(lots),
        "lot_values": sorted({round(lot, 2) for lot in lots}),
        "component_contributions": {
            key: {"trades": len(component_values), "net_usd": round(sum(component_values), 2), "profit_factor": profit_factor(component_values)}
            for key, component_values in sorted(by_component.items())
        },
        "direction": {
            key: {"trades": len(direction_values), "net_usd": round(sum(direction_values), 2), "profit_factor": profit_factor(direction_values)}
            for key, direction_values in sorted(by_direction.items())
        },
    }
    result["decision"] = decision(result)
    return result


def decision(row: dict[str, Any]) -> str:
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_CADENCE"
    if row["win_rate_pct"] < 60.0:
        return "FAIL_WIN_RATE"
    if (row["profit_factor"] or 0.0) < 1.30:
        return "FAIL_PROFIT_FACTOR"
    if row["top200_removed_usd"] <= 0:
        return "FAIL_TOP200_ROBUSTNESS"
    if row["top300_removed_usd"] <= 0:
        return "REVISE_TOP300_ROBUSTNESS"
    if row["rolling250"].get("negative", 0) not in (0, None):
        return "REVISE_ROLLING250_ROBUSTNESS"
    return "REVIEW_READY_FOR_FORWARD_SPEC"


def write_trades(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "variant",
        "entry_time",
        "exit_time",
        "entry_date",
        "entry_hour",
        "direction",
        "profit",
        "volume",
        "exit_comment",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["entry_time"] = row["entry_time"].strftime("%Y.%m.%d %H:%M:%S")
            out["exit_time"] = row["exit_time"].strftime("%Y.%m.%d %H:%M:%S")
            writer.writerow({field: out.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload["best_result"]
    lines = [
        f"# {payload['title']}",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No demo/live MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Purpose",
        "",
        "This verifies the latest risk-balanced repair using exact MT5 Strategy Tester outputs for the five matching risk-normalized components. The component hour blocks are baked into tester inputs; the package then applies 4-minute same-direction de-duplication and the event-time-causal `target75_cooldown10` guard.",
        "",
        "## Package Result",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Decision | `{best['decision']}` |",
        f"| Trades | {best['trades']} |",
        f"| Win rate | {best['win_rate_pct']}% |",
        f"| PF | {best['profit_factor']} |",
        f"| Net | {best['net_usd']} USD |",
        f"| Trades / market day | {best['trades_per_market_day']} |",
        f"| 3+ trade market days | {best['three_plus_market_day_pct']}% |",
        f"| Positive active days | {best['positive_active_day_pct']}% |",
        f"| Positive / negative months | {best['positive_months']} / {best['negative_months']} |",
        f"| Negative quarters | {best['negative_quarters']} |",
        f"| Top100 removed | {best['top100_removed_usd']} USD |",
        f"| Top200 removed | {best['top200_removed_usd']} USD |",
        f"| Top300 removed | {best['top300_removed_usd']} USD |",
        f"| Rolling250 negative windows | {best['rolling250']['negative']} |",
        f"| Max closed DD | {best['max_closed_drawdown_usd']} USD |",
        f"| Lots used | `{', '.join(str(value) for value in best['lot_values'])}` |",
        "",
        "## Component Contributions",
        "",
        "| Component | Trades | Net | PF |",
        "|---|---:|---:|---:|",
    ]
    for component, row in best["component_contributions"].items():
        lines.append(f"| `{component}` | {row['trades']} | {row['net_usd']} | {row['profit_factor']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    if best["decision"] == "REVIEW_READY_FOR_FORWARD_SPEC":
        lines.append("The exact risk-normalized MT5 package clears the current frequency, win-rate, PF, top-winner, and rolling-window checks. Next step is reviewer review and a frozen forward-test spec, not immediate live/canonical approval.")
    elif best["decision"].startswith("REVISE"):
        lines.append("The exact MT5 package improves the risk-balanced thesis but still needs revision before demo attachment. Keep searching or refine the package without using leaked outcome guards.")
    else:
        lines.append("The exact MT5 package does not clear the required bar. Treat the prior risk-balanced spreadsheet-level signal as insufficient.")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- Kept trades CSV: `{payload['trades_csv']}`",
            f"- Source backtest dir: `{payload['backtest_dir']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stress an exact MT5 risk-balanced momentum package.")
    parser.add_argument("--package", choices=sorted(PACKAGES), default="rr0p7")
    args = parser.parse_args()
    package = PACKAGES[args.package]
    backtest_dir = Path(package["backtest_dir"])
    component_names = list(package["components"])
    components, missing = load_components(backtest_dir, component_names)
    if missing:
        raise FileNotFoundError(f"Missing exact MT5 component trade CSVs: {', '.join(missing)} in {backtest_dir}")
    raw: list[dict[str, Any]] = []
    for name in component_names:
        raw.extend(components[name])
    deduped, duplicate_drops = dedupe(raw, 4)
    selected, guard_stats = apply_state_guard(
        deduped,
        state_rule="none",
        profit_target_usd=75.0,
        loss_stop_usd=None,
        max_trades_per_day=None,
        max_losses_per_day=None,
        cooldown_after_loss_minutes=10,
        early_trade_count=0,
        early_pnl_threshold=0.0,
    )
    selected = sorted(selected, key=lambda row: (row["exit_time"], row["entry_time"], row["variant"]))
    summary = summarize("risk_balanced_exact_mt5_package", selected, duplicate_drops, guard_stats)

    output_stem = str(package["output_stem"])
    output_md = REPORTS_DIR / f"{output_stem}.md"
    output_json = REPORTS_DIR / f"{output_stem}.json"
    output_trades = REPORTS_DIR / f"{output_stem}_TRADES.csv"
    payload = {
        "status": summary["decision"],
        "package": args.package,
        "title": package["title"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_strategy_tester_only_no_runtime_change",
        "backtest_dir": rel(backtest_dir),
        "components": component_names,
        "missing_components": missing,
        "best_result": summary,
        "report": rel(output_md),
        "json": rel(output_json),
        "trades_csv": rel(output_trades),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_trades(output_trades, selected)
    output_md.write_text(render(payload), encoding="utf-8")
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "trades": summary["trades"],
                "win_rate_pct": summary["win_rate_pct"],
                "profit_factor": summary["profit_factor"],
                "net_usd": summary["net_usd"],
                "trades_per_market_day": summary["trades_per_market_day"],
                "top300_removed_usd": summary["top300_removed_usd"],
                "rolling250_negative": summary["rolling250"]["negative"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
