from __future__ import annotations

import csv
import itertools
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
BACKTEST_DIR = (
    REPORTS_DIR
    / "mt5_backtests"
    / "a1_momentum_variants_risk_normalized_components_2024_07_2026_06_20260701"
)
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_RISK_NORMALIZED_COMPONENT_STRESS_2026_07_03"


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


def market_days(start: date, end: date) -> int:
    total = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            total += 1
        current += timedelta(days=1)
    return total


def top_removed(values: list[float], count: int) -> float:
    wins = sorted((value for value in values if value > 0), reverse=True)
    return round(sum(values) - sum(wins[:count]), 2)


def rolling_stats(rows: list[dict[str, Any]], window: int) -> dict[str, Any]:
    ordered = [row["profit"] for row in sorted(rows, key=lambda item: (item["exit_time"], item["entry_time"], item["variant"]))]
    if len(ordered) < window:
        return {"window": window, "available": False}
    nets = [sum(ordered[index : index + window]) for index in range(0, len(ordered) - window + 1)]
    return {
        "window": window,
        "available": True,
        "count": len(nets),
        "worst_net": round(min(nets), 2),
        "negative_windows": sum(1 for value in nets if value < 0),
    }


def read_trade_csv(path: Path, variant: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "variant": variant,
                    "entry_time": parse_time(row["entry_time"]),
                    "exit_time": parse_time(row["exit_time"]),
                    "direction": row["direction"],
                    "profit": float(row["profit_aed"]),
                    "volume": float(row["volume"]),
                    "entry_session": row.get("entry_session", ""),
                    "exit_comment": row.get("exit_comment", ""),
                }
            )
    return rows


def load_variants() -> dict[str, list[dict[str, Any]]]:
    variants: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(BACKTEST_DIR.glob("*_trades.csv")):
        variant = path.name.split("_XAUUSD_M5_", 1)[1].replace("_trades.csv", "")
        variants[variant] = read_trade_csv(path, variant)
    return variants


def dedupe(rows: list[dict[str, Any]], window_minutes: int = 5) -> tuple[list[dict[str, Any]], int]:
    ordered = sorted(rows, key=lambda row: (row["entry_time"], row["variant"], row["direction"]))
    kept: list[dict[str, Any]] = []
    dropped = 0
    window_seconds = window_minutes * 60
    for row in ordered:
        duplicate = False
        for previous in reversed(kept[-20:]):
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


def summarize(name: str, rows: list[dict[str, Any]], duplicate_drops: int = 0) -> dict[str, Any]:
    values = [row["profit"] for row in rows]
    start = min(row["entry_time"].date() for row in rows)
    end = max(row["entry_time"].date() for row in rows)
    market_day_count = market_days(start, end)
    by_day: dict[date, list[float]] = defaultdict(list)
    by_quarter: dict[str, list[float]] = defaultdict(list)
    by_half: dict[str, list[float]] = defaultdict(list)
    by_direction: dict[str, list[float]] = defaultdict(list)
    lots = [row["volume"] for row in rows]
    for row in rows:
        trade_day = row["entry_time"].date()
        by_day[trade_day].append(row["profit"])
        quarter = (row["entry_time"].month - 1) // 3 + 1
        by_quarter[f"{row['entry_time'].year}-Q{quarter}"].append(row["profit"])
        half = "H1" if row["entry_time"].month <= 6 else "H2"
        by_half[f"{row['entry_time'].year}-{half}"].append(row["profit"])
        by_direction[row["direction"]].append(row["profit"])
    wins = sum(1 for value in values if value > 0)
    active_days = len(by_day)
    return {
        "name": name,
        "trades": len(rows),
        "wins": wins,
        "losses": len(rows) - wins,
        "win_rate_pct": round(100.0 * wins / len(rows), 2),
        "profit_factor": profit_factor(values),
        "net_usd": round(sum(values), 2),
        "avg_usd": round(sum(values) / len(rows), 2),
        "max_closed_drawdown_usd": max_drawdown([row["profit"] for row in sorted(rows, key=lambda item: item["exit_time"])]),
        "duplicate_drops": duplicate_drops,
        "date_start": start.isoformat(),
        "date_end": end.isoformat(),
        "market_days": market_day_count,
        "active_days": active_days,
        "trades_per_market_day": round(len(rows) / market_day_count, 2),
        "active_market_day_pct": round(100.0 * active_days / market_day_count, 2),
        "three_plus_market_day_pct": round(100.0 * sum(1 for values_for_day in by_day.values() if len(values_for_day) >= 3) / market_day_count, 2),
        "positive_active_day_pct": round(100.0 * sum(1 for values_for_day in by_day.values() if sum(values_for_day) > 0) / active_days, 2),
        "top10_removed_usd": top_removed(values, 10),
        "top25_removed_usd": top_removed(values, 25),
        "top50_removed_usd": top_removed(values, 50),
        "top100_removed_usd": top_removed(values, 100),
        "top200_removed_usd": top_removed(values, 200),
        "top300_removed_usd": top_removed(values, 300),
        "rolling100": rolling_stats(rows, 100),
        "rolling200": rolling_stats(rows, 200),
        "rolling300": rolling_stats(rows, 300),
        "weak_quarters": [
            {"period": key, "trades": len(values_for_period), "net_usd": round(sum(values_for_period), 2), "profit_factor": profit_factor(values_for_period)}
            for key, values_for_period in sorted(by_quarter.items())
            if sum(values_for_period) <= 0 or (profit_factor(values_for_period) or 0.0) < 1.10
        ],
        "half_year": {
            key: {"trades": len(values_for_period), "net_usd": round(sum(values_for_period), 2), "profit_factor": profit_factor(values_for_period)}
            for key, values_for_period in sorted(by_half.items())
        },
        "direction": {
            key: {"trades": len(values_for_direction), "net_usd": round(sum(values_for_direction), 2), "profit_factor": profit_factor(values_for_direction)}
            for key, values_for_direction in sorted(by_direction.items())
        },
        "lot_min": min(lots),
        "lot_median": sorted(lots)[len(lots) // 2],
        "lot_max": max(lots),
        "lot_values": sorted({round(lot, 2) for lot in lots}),
    }


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
    if row["rolling100"].get("negative_windows", 0) > 0:
        return "REVISE_ROLLING100_ROBUSTNESS"
    if row["three_plus_market_day_pct"] < 50.0:
        return "REVIEW_CADENCE_COVERAGE"
    return "REVIEW_READY_FOR_OWNER_FORWARD_TEST"


def build_rows(variants: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    summaries: list[dict[str, Any]] = []
    portfolios: dict[str, list[dict[str, Any]]] = {}
    for name, rows in variants.items():
        summary = summarize(name, rows)
        summary["decision"] = decision(summary)
        summaries.append(summary)
        portfolios[name] = rows
    for size in range(2, len(variants) + 1):
        for combo in itertools.combinations(sorted(variants), size):
            raw: list[dict[str, Any]] = []
            for name in combo:
                raw.extend(variants[name])
            deduped, duplicate_drops = dedupe(raw)
            name = " + ".join(combo)
            summary = summarize(name, deduped, duplicate_drops=duplicate_drops)
            summary["decision"] = decision(summary)
            summaries.append(summary)
            portfolios[name] = deduped
    summaries.sort(
        key=lambda row: (
            row["decision"].startswith("FAIL"),
            row["decision"].startswith("REVISE"),
            -row["trades_per_market_day"],
            -row["net_usd"],
        )
    )
    return summaries, portfolios


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "name",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net_usd",
        "trades_per_market_day",
        "three_plus_market_day_pct",
        "top100_removed_usd",
        "top200_removed_usd",
        "top300_removed_usd",
        "max_closed_drawdown_usd",
        "duplicate_drops",
        "lot_min",
        "lot_median",
        "lot_max",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 Momentum Risk-Normalized Component Stress - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No demo/live MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## What Changed",
        "",
        "This report stress-tests the exact MT5 Strategy Tester outputs for the four risk-normalized momentum components over `2024-07-01 -> 2026-06-30`.",
        "",
        "Important caveat: exported lots are only `0.01` or `0.02`, so this is not a pure fixed-risk proof. It is best read as an exact MT5 test of the risk-normalized code path under broker min-lot constraints.",
        "",
        "## Ranked Results",
        "",
        "| Rank | Decision | Portfolio | Trades | WR | PF | Net | T/market day | 3+ market days | Top200 removed | Top300 removed | Rolling100 neg | Lots |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for index, row in enumerate(payload["rows"][:15], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{name}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {three:.2f}% | {top200:.2f} | {top300:.2f} | {r100} | `{lots}` |".format(
                rank=index,
                decision=row["decision"],
                name=row["name"][:110],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                pf=row["profit_factor"],
                net=row["net_usd"],
                tmd=row["trades_per_market_day"],
                three=row["three_plus_market_day_pct"],
                top200=row["top200_removed_usd"],
                top300=row["top300_removed_usd"],
                r100=row["rolling100"].get("negative_windows", 0),
                lots=",".join(str(value) for value in row["lot_values"]),
            )
        )
    best = payload["best_result"]
    lines.extend(
        [
            "",
            "## Current Read",
            "",
            f"- Best exact-MT5 shape: `{best['name']}`.",
            f"- It reaches `{best['trades_per_market_day']}` trades per market day, `{best['win_rate_pct']}%` WR, PF `{best['profit_factor']}`, and `{best['net_usd']}` tester USD.",
            f"- It passes top-200 removal (`{best['top200_removed_usd']}`) but fails top-300 removal (`{best['top300_removed_usd']}`).",
            f"- It still has `{best['rolling100'].get('negative_windows', 0)}` negative 100-trade rolling windows.",
            "- Therefore this is a serious lead, not a finished forward candidate.",
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            "- Source MT5 report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_RISK_NORMALIZED_COMPONENTS_2024_07_2026_06.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    variants = load_variants()
    rows, _portfolios = build_rows(variants)
    best = rows[0] if rows else {}
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "REVISE_ROBUSTNESS_EXACT_MT5_LEAD" if rows else "FAIL_NO_RISK_NORMALIZED_BACKTEST_ROWS",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_backtest_dir": rel(BACKTEST_DIR),
        "best_result": best,
        "rows": rows,
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
    }
    output_md.write_text(render(payload), encoding="utf-8")
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(output_csv, rows)
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "best": best.get("name"),
                "decision": best.get("decision"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor": best.get("profit_factor"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top300_removed_usd": best.get("top300_removed_usd"),
            },
            indent=2,
        )
    )
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
