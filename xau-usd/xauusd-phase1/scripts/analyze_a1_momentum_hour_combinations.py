"""Search frequency-first hour masks for the A1 XAU M5 momentum EA.

This is an offline ranking tool over broad MT5 Strategy Tester ledgers. It is
not a replacement for an exact MT5 rerun because blocking a trade can free a
later entry that did not appear in the all-hours ledger.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_ROOT = REPO_ROOT / "xau-usd" / "xauusd-phase1"
REPORT_DIR = PHASE1_ROOT / "outputs" / "reports"
DOC_DIR = PHASE1_ROOT / "docs"

WINDOWS = {
    "oos": REPORT_DIR / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_COMBO_BASE_OOS_2022_07_2024_06.json",
    "current": REPORT_DIR / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_COMBO_BASE_CURRENT_2024_07_2026_06.json",
    "four_year": REPORT_DIR / "A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_COMBO_BASE_FOUR_YEAR_2022_07_2026_06.json",
}

DIRECTIONS = {
    "LONG": "freq_h1_h4_long_rr0p7_cost005_all_hours",
    "SHORT": "freq_h1_h4_short_rr0p7_cost005_all_hours",
}


@dataclass(frozen=True)
class Trade:
    direction: str
    entry_time: str
    hour: int
    month: str
    day: str
    pnl: float
    win: bool


def main() -> int:
    ledgers = load_ledgers()
    direction_results = []
    top_masks: dict[str, list[dict[str, Any]]] = {}
    for direction in DIRECTIONS:
        results = search_direction(direction, ledgers[direction])
        top_masks[direction] = results[:60]
        direction_results.extend(results[:25])

    combined_results = search_combinations(top_masks, ledgers)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "ea": "A1XauM5MomentumContinuationExecutor",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "source": "offline filter over broad all-hours MT5 trade ledgers",
            "warning": "Ranking only; exact MT5 rerun required because blocked trades can change later scheduling.",
            "goal": "multiple trades per active day, win rate above 50%, positive expectancy, OOS/current stability",
        },
        "direction_top25": direction_results,
        "combined_top25": combined_results[:25],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    report_json = REPORT_DIR / "A1_XAU_M5_MOMENTUM_HOUR_COMBINATION_SEARCH_2026_07_02.json"
    report_md = REPORT_DIR / "A1_XAU_M5_MOMENTUM_HOUR_COMBINATION_SEARCH_2026_07_02.md"
    tracked_md = DOC_DIR / "A1_XAU_M5_MOMENTUM_HOUR_COMBINATION_SEARCH_2026_07_02.md"
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown = render_markdown(payload)
    report_md.write_text(markdown, encoding="utf-8")
    tracked_md.write_text(markdown, encoding="utf-8")
    print(json.dumps({"report": str(report_md), "tracked": str(tracked_md), "top_combined": combined_results[:3]}, indent=2))
    return 0


def load_ledgers() -> dict[str, dict[str, list[Trade]]]:
    ledgers: dict[str, dict[str, list[Trade]]] = {direction: {} for direction in DIRECTIONS}
    for window, report_path in WINDOWS.items():
        data = json.loads(report_path.read_text(encoding="utf-8"))
        for direction, variant_name in DIRECTIONS.items():
            variant = next(item for item in data["variants"] if item["name"] == variant_name)
            ledgers[direction][window] = read_trades(Path(variant["trade_csv"]), direction)
    return ledgers


def read_trades(path: Path, direction: str) -> list[Trade]:
    rows: list[Trade] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            entry_time = row.get("entry_time") or row.get("open_time") or ""
            hour = int(row.get("hour") or entry_time[11:13])
            pnl = float(row["profit_aed"])
            rows.append(
                Trade(
                    direction=direction,
                    entry_time=entry_time,
                    hour=hour,
                    month=entry_time[:7],
                    day=entry_time[:10],
                    pnl=pnl,
                    win=pnl > 0,
                )
            )
    return rows


def search_direction(direction: str, windows: dict[str, list[Trade]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    hourly = {window: hourly_stats(trades) for window, trades in windows.items()}
    eligible = eligible_hours(hourly)
    for mask in range(1, 1 << len(eligible)):
        hours = [hour for idx, hour in enumerate(eligible) if mask & (1 << idx)]
        if len(hours) < 4 or len(hours) > 18:
            continue
        basic_stats = {window: combine_hourly_stats(hourly[window], hours) for window in WINDOWS}
        if not passes_basic_direction_floor(basic_stats):
            continue
        stats = {window: aggregate(filter_hours(trades, hours)) for window, trades in windows.items()}
        if not passes_direction_floor(stats):
            continue
        score = score_stats(stats)
        results.append({"kind": direction, "hours": hours, "blocked_hours": blocked_hours(hours), "score": score, "stats": stats})
    results.sort(key=lambda item: item["score"], reverse=True)
    return results


def eligible_hours(hourly: dict[str, dict[int, dict[str, float]]]) -> list[int]:
    hours: list[int] = []
    for hour in range(24):
        oos = combine_hourly_stats(hourly["oos"], [hour])
        current = combine_hourly_stats(hourly["current"], [hour])
        four = combine_hourly_stats(hourly["four_year"], [hour])
        if four["trades"] < 15:
            continue
        split_positive = oos["pnl"] > 0 and current["pnl"] > 0
        four_quality = four["pnl"] > 0 and four["win_rate_pct"] >= 54.0 and (four["profit_factor"] or 0) >= 1.05
        one_split_strong = (
            (oos["pnl"] > 0 and (oos["profit_factor"] or 0) >= 1.15)
            or (current["pnl"] > 0 and (current["profit_factor"] or 0) >= 1.15)
        )
        if split_positive or (four_quality and one_split_strong):
            hours.append(hour)
    return hours


def hourly_stats(trades: list[Trade]) -> dict[int, dict[str, float]]:
    stats = {hour: {"trades": 0.0, "wins": 0.0, "gross_profit": 0.0, "gross_loss": 0.0} for hour in range(24)}
    for trade in trades:
        item = stats[trade.hour]
        item["trades"] += 1.0
        if trade.pnl > 0:
            item["wins"] += 1.0
            item["gross_profit"] += trade.pnl
        elif trade.pnl < 0:
            item["gross_loss"] += -trade.pnl
    return stats


def combine_hourly_stats(hourly: dict[int, dict[str, float]], hours: list[int]) -> dict[str, Any]:
    trades = sum(hourly[hour]["trades"] for hour in hours)
    wins = sum(hourly[hour]["wins"] for hour in hours)
    gross_profit = sum(hourly[hour]["gross_profit"] for hour in hours)
    gross_loss = sum(hourly[hour]["gross_loss"] for hour in hours)
    pnl = gross_profit - gross_loss
    return {
        "trades": int(trades),
        "wins": int(wins),
        "win_rate_pct": round((wins / trades) * 100, 2) if trades else 0.0,
        "pnl": round(pnl, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else None,
    }


def filter_hours(trades: list[Trade], hours: list[int]) -> list[Trade]:
    kept = set(hours)
    return [trade for trade in trades if trade.hour in kept]


def search_combinations(top_masks: dict[str, list[dict[str, Any]]], ledgers: dict[str, dict[str, list[Trade]]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    long_masks = top_masks["LONG"][:60]
    short_masks = top_masks["SHORT"][:60]
    for long_item in long_masks:
        for short_item in short_masks:
            stats: dict[str, dict[str, Any]] = {}
            for window in WINDOWS:
                long_rows = [trade for trade in ledgers["LONG"][window] if trade.hour in set(long_item["hours"])]
                short_rows = [trade for trade in ledgers["SHORT"][window] if trade.hour in set(short_item["hours"])]
                stats[window] = aggregate(long_rows + short_rows)
            if not passes_combined_floor(stats):
                continue
            results.append(
                {
                    "kind": "LONG_PLUS_SHORT",
                    "long_hours": long_item["hours"],
                    "short_hours": short_item["hours"],
                    "long_blocked_hours": blocked_hours(long_item["hours"]),
                    "short_blocked_hours": blocked_hours(short_item["hours"]),
                    "score": score_stats(stats),
                    "stats": stats,
                }
            )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results


def aggregate(trades: list[Trade]) -> dict[str, Any]:
    gross_profit = sum(trade.pnl for trade in trades if trade.pnl > 0)
    gross_loss = -sum(trade.pnl for trade in trades if trade.pnl < 0)
    pnl = gross_profit - gross_loss
    days: dict[str, float] = {}
    months: dict[str, float] = {}
    wins = []
    for trade in trades:
        days[trade.day] = days.get(trade.day, 0.0) + trade.pnl
        months[trade.month] = months.get(trade.month, 0.0) + trade.pnl
        if trade.pnl > 0:
            wins.append(trade.pnl)
    top10 = sum(sorted(wins, reverse=True)[:10])
    count = len(trades)
    win_count = sum(1 for trade in trades if trade.pnl > 0)
    return {
        "trades": count,
        "wins": win_count,
        "losses": sum(1 for trade in trades if trade.pnl < 0),
        "win_rate_pct": round((win_count / count) * 100, 2) if count else 0.0,
        "pnl": round(pnl, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else None,
        "active_days": len(days),
        "trades_per_active_day": round(count / len(days), 2) if days else 0.0,
        "months": len(months),
        "positive_months": sum(1 for value in months.values() if value > 0),
        "negative_months": sum(1 for value in months.values() if value < 0),
        "net_minus_top10": round(pnl - top10, 2),
    }


def passes_direction_floor(stats: dict[str, dict[str, Any]]) -> bool:
    oos = stats["oos"]
    current = stats["current"]
    four = stats["four_year"]
    return (
        oos["trades"] >= 250
        and current["trades"] >= 250
        and four["trades"] >= 650
        and oos["win_rate_pct"] >= 58.0
        and current["win_rate_pct"] >= 58.0
        and four["win_rate_pct"] >= 60.0
        and (oos["profit_factor"] or 0) >= 1.15
        and (current["profit_factor"] or 0) >= 1.15
        and (four["profit_factor"] or 0) >= 1.25
        and oos["pnl"] > 0
        and current["pnl"] > 0
        and four["net_minus_top10"] > 0
        and four["trades_per_active_day"] >= 2.25
    )


def passes_basic_direction_floor(stats: dict[str, dict[str, Any]]) -> bool:
    oos = stats["oos"]
    current = stats["current"]
    four = stats["four_year"]
    return (
        oos["trades"] >= 250
        and current["trades"] >= 250
        and four["trades"] >= 650
        and oos["win_rate_pct"] >= 58.0
        and current["win_rate_pct"] >= 58.0
        and four["win_rate_pct"] >= 60.0
        and (oos["profit_factor"] or 0) >= 1.15
        and (current["profit_factor"] or 0) >= 1.15
        and (four["profit_factor"] or 0) >= 1.25
        and oos["pnl"] > 0
        and current["pnl"] > 0
    )


def passes_combined_floor(stats: dict[str, dict[str, Any]]) -> bool:
    oos = stats["oos"]
    current = stats["current"]
    four = stats["four_year"]
    return (
        oos["trades"] >= 550
        and current["trades"] >= 550
        and four["trades"] >= 1200
        and oos["win_rate_pct"] >= 60.0
        and current["win_rate_pct"] >= 60.0
        and four["win_rate_pct"] >= 62.0
        and (oos["profit_factor"] or 0) >= 1.20
        and (current["profit_factor"] or 0) >= 1.20
        and (four["profit_factor"] or 0) >= 1.30
        and oos["pnl"] > 0
        and current["pnl"] > 0
        and four["net_minus_top10"] > 0
        and four["active_days"] >= 420
    )


def score_stats(stats: dict[str, dict[str, Any]]) -> float:
    oos = stats["oos"]
    current = stats["current"]
    four = stats["four_year"]
    return (
        four["pnl"]
        + 75.0 * ((four["profit_factor"] or 0.0) - 1.0)
        + 8.0 * (four["win_rate_pct"] - 50.0)
        + 0.15 * four["trades"]
        + 0.50 * min(oos["pnl"], current["pnl"])
        - 10.0 * abs(oos["profit_factor"] - current["profit_factor"])
    )


def mask_hours(mask: int) -> list[int]:
    return [hour for hour in range(24) if mask & (1 << hour)]


def blocked_hours(hours: list[int]) -> list[int]:
    kept = set(hours)
    return [hour for hour in range(24) if hour not in kept]


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 Momentum Hour-Combination Search",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "## Boundary",
        "",
        "- Offline analysis only over broad all-hours MT5 Strategy Tester trade ledgers.",
        "- No live/demo MT5 runtime was touched.",
        "- This is a ranking tool, not proof. Exact MT5 rerun is required because blocking hours can change one-position scheduling.",
        "- Goal: multiple trades per active day, win rate above 50%, positive expectancy, and both older/current split stability.",
        "",
        "## Top Combined Candidates",
        "",
        "| Rank | Long Hours | Short Hours | OOS Trades / WR / PF / Net | Current Trades / WR / PF / Net | Four-Year Trades / WR / PF / Net | Active Days | Trades / Active Day | Net minus Top 10 |",
        "| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for idx, item in enumerate(payload["combined_top25"][:10], start=1):
        oos = item["stats"]["oos"]
        cur = item["stats"]["current"]
        four = item["stats"]["four_year"]
        lines.append(
            f"| {idx} | `{csv_hours(item['long_hours'])}` | `{csv_hours(item['short_hours'])}` | "
            f"`{oos['trades']} / {oos['win_rate_pct']}% / {oos['profit_factor']} / {oos['pnl']}` | "
            f"`{cur['trades']} / {cur['win_rate_pct']}% / {cur['profit_factor']} / {cur['pnl']}` | "
            f"`{four['trades']} / {four['win_rate_pct']}% / {four['profit_factor']} / {four['pnl']}` | "
            f"`{four['active_days']}` | `{four['trades_per_active_day']}` | `{four['net_minus_top10']}` |"
        )
    if not payload["combined_top25"]:
        lines.append("| n/a | none passed combined floor | | | | | | | |")

    lines.extend(
        [
            "",
            "## Top Direction-Only Candidates",
            "",
            "| Rank | Kind | Kept Hours | OOS Trades / WR / PF / Net | Current Trades / WR / PF / Net | Four-Year Trades / WR / PF / Net | Active Days | Trades / Active Day | Net minus Top 10 |",
            "| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for idx, item in enumerate(payload["direction_top25"][:15], start=1):
        oos = item["stats"]["oos"]
        cur = item["stats"]["current"]
        four = item["stats"]["four_year"]
        lines.append(
            f"| {idx} | `{item['kind']}` | `{csv_hours(item['hours'])}` | "
            f"`{oos['trades']} / {oos['win_rate_pct']}% / {oos['profit_factor']} / {oos['pnl']}` | "
            f"`{cur['trades']} / {cur['win_rate_pct']}% / {cur['profit_factor']} / {cur['pnl']}` | "
            f"`{four['trades']} / {four['win_rate_pct']}% / {four['profit_factor']} / {four['pnl']}` | "
            f"`{four['active_days']}` | `{four['trades_per_active_day']}` | `{four['net_minus_top10']}` |"
        )
    if not payload["direction_top25"]:
        lines.append("| n/a | none passed direction floor | | | | | | | |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- If combined candidates appear here, they are candidates for exact MT5 rerun only.",
            "- If the table is empty, the current long/short all-hours base does not contain a split-stable high-frequency combination under the configured floors.",
            "- Direction-specific hour sets would need separate EA instances or direction-specific runtime inputs; do not assume one existing preset can express both sides.",
            "",
        ]
    )
    return "\n".join(lines)


def csv_hours(hours: list[int]) -> str:
    return ",".join(str(hour) for hour in hours)


if __name__ == "__main__":
    raise SystemExit(main())
