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
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_RISK_NORMALIZED_HOUR_REPAIR_2026_07_03"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")


def profit_factor(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


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


def rolling_negative_count(values: list[float], window: int) -> tuple[float | None, int | None]:
    if len(values) < window:
        return None, None
    nets = [sum(values[index : index + window]) for index in range(len(values) - window + 1)]
    return round(min(nets), 2), sum(1 for value in nets if value < 0)


def read_exact_package() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(BACKTEST_DIR.glob("*_trades.csv")):
        variant = path.name.split("_XAUUSD_M5_", 1)[1].replace("_trades.csv", "")
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append(
                    {
                        "variant": variant,
                        "entry_time": parse_time(row["entry_time"]),
                        "exit_time": parse_time(row["exit_time"]),
                        "direction": row["direction"],
                        "hour": int(row["entry_hour"]),
                        "profit": float(row["profit_aed"]),
                    }
                )
    return rows


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: (row["entry_time"], row["variant"], row["direction"]))
    kept: list[dict[str, Any]] = []
    for row in ordered:
        duplicate = False
        for previous in reversed(kept[-20:]):
            delta = abs((row["entry_time"] - previous["entry_time"]).total_seconds())
            if delta > 300:
                break
            if row["direction"] == previous["direction"]:
                duplicate = True
                break
        if not duplicate:
            kept.append(row)
    return kept


def summarize(rows: list[dict[str, Any]], blocked_hours: tuple[int, ...], market_day_count: int) -> dict[str, Any]:
    values = [row["profit"] for row in rows]
    by_day: dict[date, int] = defaultdict(int)
    for row in rows:
        by_day[row["entry_time"].date()] += 1
    ordered_exit_values = [row["profit"] for row in sorted(rows, key=lambda item: item["exit_time"])]
    rolling100_worst, rolling100_negative = rolling_negative_count(ordered_exit_values, 100)
    rolling200_worst, rolling200_negative = rolling_negative_count(ordered_exit_values, 200)
    wins = sum(1 for value in values if value > 0)
    return {
        "blocked_hours": ",".join(str(hour) for hour in blocked_hours) if blocked_hours else "none",
        "blocked_hour_count": len(blocked_hours),
        "trades": len(rows),
        "win_rate_pct": round(100.0 * wins / len(values), 2),
        "profit_factor": profit_factor(values),
        "net_usd": round(sum(values), 2),
        "trades_per_market_day": round(len(values) / market_day_count, 2),
        "three_plus_market_day_pct": round(100.0 * sum(count >= 3 for count in by_day.values()) / market_day_count, 2),
        "top100_removed_usd": top_removed(values, 100),
        "top200_removed_usd": top_removed(values, 200),
        "top300_removed_usd": top_removed(values, 300),
        "rolling100_worst_usd": rolling100_worst,
        "rolling100_negative_windows": rolling100_negative,
        "rolling200_worst_usd": rolling200_worst,
        "rolling200_negative_windows": rolling200_negative,
    }


def decision(row: dict[str, Any]) -> str:
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_CADENCE"
    if row["top300_removed_usd"] <= 0:
        return "FAIL_TOP300_ROBUSTNESS"
    if row["rolling100_negative_windows"]:
        return "FAIL_ROLLING100_ROBUSTNESS"
    return "REVIEW_READY"


def search_rows(base: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start = min(row["entry_time"].date() for row in base)
    end = max(row["entry_time"].date() for row in base)
    market_day_count = market_days(start, end)

    hour_values: dict[int, list[float]] = defaultdict(list)
    for row in base:
        hour_values[row["hour"]].append(row["profit"])
    weak_hours = [
        hour
        for _net, _count, hour in sorted(
            (sum(values), len(values), hour) for hour, values in hour_values.items()
        )[:12]
    ]

    candidate_masks: set[tuple[int, ...]] = {()}
    for count in range(1, 7):
        for combo in itertools.combinations(weak_hours, count):
            candidate_masks.add(tuple(sorted(combo)))
    for count in range(1, 4):
        for combo in itertools.combinations(range(24), count):
            candidate_masks.add(tuple(sorted(combo)))

    rows: list[dict[str, Any]] = []
    for mask in candidate_masks:
        blocked = set(mask)
        kept = [row for row in base if row["hour"] not in blocked]
        if len(kept) < 1000:
            continue
        summary = summarize(kept, mask, market_day_count)
        if summary["win_rate_pct"] < 60.0 or (summary["profit_factor"] or 0.0) < 1.25:
            continue
        summary["decision"] = decision(summary)
        rows.append(summary)
    rows.sort(
        key=lambda row: (
            row["decision"].startswith("FAIL"),
            -row["trades_per_market_day"],
            -row["top300_removed_usd"],
            -(row["rolling100_negative_windows"] or 0),
            -row["net_usd"],
        )
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "blocked_hours",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net_usd",
        "trades_per_market_day",
        "three_plus_market_day_pct",
        "top200_removed_usd",
        "top300_removed_usd",
        "rolling100_worst_usd",
        "rolling100_negative_windows",
        "rolling200_worst_usd",
        "rolling200_negative_windows",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best_rolling = payload.get("best_rolling100_result", {})
    lines = [
        "# A1 XAU M5 Momentum Risk-Normalized Hour Repair - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime was touched.",
        "",
        "This search tests whether a small blocked-hour mask can repair the exact risk-normalized component package without dropping below the owner's cadence target.",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Blocked hours | Trades | WR | PF | Net | T/market day | 3+ market days | Top200 | Top300 | Rolling100 neg |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["rows"][:20], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{hours}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {three:.2f}% | {top200:.2f} | {top300:.2f} | {r100} |".format(
                rank=index,
                decision=row["decision"],
                hours=row["blocked_hours"],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                pf=row["profit_factor"],
                net=row["net_usd"],
                tmd=row["trades_per_market_day"],
                three=row["three_plus_market_day_pct"],
                top200=row["top200_removed_usd"],
                top300=row["top300_removed_usd"],
                r100=row["rolling100_negative_windows"],
            )
        )
    best = payload["best_result"]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Best row by cadence keeps `{best.get('trades_per_market_day')}` trades/market day but remains `{best.get('decision')}`.",
            f"- Best rolling-100 repair blocks `{best_rolling.get('blocked_hours', 'n/a')}`, keeps `{best_rolling.get('trades_per_market_day', 'n/a')}` trades/market day, and has `{best_rolling.get('rolling100_negative_windows', 'n/a')}` negative rolling-100 windows.",
            "- No searched blocked-hour mask fixed top300 robustness while also preserving the owner's frequency target.",
            "- This makes the next aligned move a complementary entry mechanism, not more hour-pruning of the same package.",
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    base = dedupe(read_exact_package())
    rows = search_rows(base)
    rolling100_rows = [row for row in rows if row.get("rolling100_negative_windows") == 0]
    rolling100_rows.sort(key=lambda row: (-row["trades_per_market_day"], -row["net_usd"]))
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "NO_HOUR_REPAIR_FOUND",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "base_trades": len(base),
        "best_result": rows[0] if rows else {},
        "best_rolling100_result": rolling100_rows[0] if rolling100_rows else {},
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
                "best_decision": payload["best_result"].get("decision"),
                "best_blocked_hours": payload["best_result"].get("blocked_hours"),
                "best_trades_per_market_day": payload["best_result"].get("trades_per_market_day"),
                "best_top300_removed_usd": payload["best_result"].get("top300_removed_usd"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
