from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1_ROOT.parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
BAR_PATH = (
    PHASE1_ROOT.parents[0]
    / "xauusd-phase0"
    / "data"
    / "processed"
    / "bars"
    / "capital_com"
    / "XAUUSD"
    / "M5"
    / "XAUUSD_capital_com_M5_20160103_20250701.csv"
)
OUTPUT_STEM = "XAU_M5_EXHAUSTION_SNAPBACK_SCREEN_2026_07_03"

SCREEN_START = pd.Timestamp("2022-07-01T00:00:00Z")
SCREEN_END = pd.Timestamp("2025-06-30T23:59:59Z")


@dataclass(frozen=True)
class Params:
    name: str
    direction_mode: str
    distance_atr: float
    move_atr: float
    rr: float
    risk_atr: float
    time_stop_bars: int
    blocked_hours: tuple[int, ...]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def load_bars() -> pd.DataFrame:
    usecols = [
        "timestamp_utc",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
        "spread_open_points",
    ]
    df = pd.read_csv(BAR_PATH, usecols=usecols)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df = df[(df["timestamp_utc"] >= SCREEN_START) & (df["timestamp_utc"] <= SCREEN_END)].copy()
    df.sort_values("timestamp_utc", inplace=True)
    df.reset_index(drop=True, inplace=True)
    prev_close = df["mid_close"].shift(1)
    true_range = pd.concat(
        [
            df["mid_high"] - df["mid_low"],
            (df["mid_high"] - prev_close).abs(),
            (df["mid_low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr14"] = true_range.rolling(14, min_periods=14).mean()
    df["ema50"] = df["mid_close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["mid_close"].ewm(span=200, adjust=False).mean()
    candle_range = (df["mid_high"] - df["mid_low"]).replace(0, pd.NA)
    df["close_location"] = ((df["mid_close"] - df["mid_low"]) / candle_range).fillna(0.5)
    df["move3_atr"] = (df["mid_close"] - df["mid_close"].shift(3)) / df["atr14"]
    df["distance_ema50_atr"] = (df["mid_close"] - df["ema50"]) / df["atr14"]
    df["dubai_hour"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.hour
    df["entry_date"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.date.astype(str)
    df["spread_price"] = (df["ask_open"] - df["bid_open"]).abs()
    return df.dropna(subset=["atr14", "move3_atr", "distance_ema50_atr"]).reset_index(drop=True)


def signal_direction(row: dict[str, Any], params: Params) -> str | None:
    if int(row["dubai_hour"]) in params.blocked_hours:
        return None
    extended_up = row["distance_ema50_atr"] >= params.distance_atr and row["move3_atr"] >= params.move_atr
    extended_down = row["distance_ema50_atr"] <= -params.distance_atr and row["move3_atr"] <= -params.move_atr
    close_high = row["close_location"] >= 0.75
    close_low = row["close_location"] <= 0.25
    if params.direction_mode in {"both", "short"} and extended_up and close_high:
        return "SHORT"
    if params.direction_mode in {"both", "long"} and extended_down and close_low:
        return "LONG"
    return None


def simulate(rows: list[dict[str, Any]], params: Params) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    i = 0
    while i < len(rows) - params.time_stop_bars - 2:
        row = rows[i]
        direction = signal_direction(row, params)
        if direction is None:
            i += 1
            continue
        entry_index = i + 1
        entry_row = rows[entry_index]
        atr = float(row["atr14"])
        spread = float(entry_row["spread_price"])
        risk = max(params.risk_atr * atr, 3.0 * spread)
        if risk <= 0:
            i += 1
            continue
        if direction == "LONG":
            entry = float(entry_row["ask_open"])
            sl = entry - risk
            tp = entry + (params.rr * risk)
        else:
            entry = float(entry_row["bid_open"])
            sl = entry + risk
            tp = entry - (params.rr * risk)

        exit_index = min(entry_index + params.time_stop_bars, len(rows) - 1)
        exit_price = None
        exit_reason = "time_stop"
        for j in range(entry_index, exit_index + 1):
            bar = rows[j]
            if direction == "LONG":
                hit_sl = float(bar["bid_low"]) <= sl
                hit_tp = float(bar["bid_high"]) >= tp
                if hit_sl and hit_tp:
                    exit_index = j
                    exit_price = sl
                    exit_reason = "sl_adverse_first"
                    break
                if hit_sl:
                    exit_index = j
                    exit_price = sl
                    exit_reason = "sl"
                    break
                if hit_tp:
                    exit_index = j
                    exit_price = tp
                    exit_reason = "tp"
                    break
            else:
                hit_sl = float(bar["ask_high"]) >= sl
                hit_tp = float(bar["ask_low"]) <= tp
                if hit_sl and hit_tp:
                    exit_index = j
                    exit_price = sl
                    exit_reason = "sl_adverse_first"
                    break
                if hit_sl:
                    exit_index = j
                    exit_price = sl
                    exit_reason = "sl"
                    break
                if hit_tp:
                    exit_index = j
                    exit_price = tp
                    exit_reason = "tp"
                    break
        if exit_price is None:
            last = rows[exit_index]
            exit_price = float(last["bid_close"] if direction == "LONG" else last["ask_close"])
        profit = (exit_price - entry) if direction == "LONG" else (entry - exit_price)
        trades.append(
            {
                "variant": params.name,
                "entry_time": entry_row["timestamp_utc"].isoformat(),
                "entry_date": entry_row["entry_date"],
                "entry_hour": int(entry_row["dubai_hour"]),
                "direction": direction,
                "entry": round(entry, 2),
                "exit_time": rows[exit_index]["timestamp_utc"].isoformat(),
                "exit": round(exit_price, 2),
                "profit": round(profit, 2),
                "r": round(profit / risk, 4),
                "risk": round(risk, 4),
                "atr14": round(atr, 4),
                "spread": round(spread, 4),
                "exit_reason": exit_reason,
                "distance_ema50_atr": round(float(row["distance_ema50_atr"]), 4),
                "move3_atr": round(float(row["move3_atr"]), 4),
                "close_location": round(float(row["close_location"]), 4),
            }
        )
        i = exit_index + 1
    return trades


def profit_factor(values: list[float]) -> float | None:
    gross_profit = sum(v for v in values if v > 0)
    gross_loss = -sum(v for v in values if v < 0)
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


def market_days(start: str, end: str) -> int:
    days = pd.bdate_range(pd.Timestamp(start), pd.Timestamp(end))
    return len(days)


def summarize_trades(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {"name": name, "trades": 0}
    profits = [float(row["profit"]) for row in trades]
    r_values = [float(row["r"]) for row in trades]
    wins = sum(1 for value in profits if value > 0)
    by_day: dict[str, list[float]] = {}
    by_month: dict[str, list[float]] = {}
    for row in trades:
        by_day.setdefault(row["entry_date"], []).append(float(row["profit"]))
        by_month.setdefault(row["entry_date"][:7], []).append(float(row["profit"]))
    day_values = [sum(values) for values in by_day.values()]
    month_values = [sum(values) for values in by_month.values()]
    sorted_profits = sorted(profits, reverse=True)
    sorted_r = sorted(r_values, reverse=True)
    start = min(row["entry_date"] for row in trades)
    end = max(row["entry_date"] for row in trades)
    bdays = market_days(start, end)
    return {
        "name": name,
        "trades": len(trades),
        "wins": wins,
        "losses": sum(1 for value in profits if value < 0),
        "win_rate_pct": round(100.0 * wins / len(trades), 2),
        "net_usd": round(sum(profits), 2),
        "profit_factor": profit_factor(profits),
        "net_r": round(sum(r_values), 2),
        "profit_factor_r": profit_factor(r_values),
        "active_days": len(by_day),
        "market_days": bdays,
        "trades_per_market_day": round(len(trades) / bdays, 2) if bdays else 0.0,
        "trades_per_active_day": round(len(trades) / len(by_day), 2) if by_day else 0.0,
        "positive_days": sum(1 for value in day_values if value > 0),
        "negative_days": sum(1 for value in day_values if value < 0),
        "positive_months": sum(1 for value in month_values if value > 0),
        "negative_months": sum(1 for value in month_values if value < 0),
        "top25_removed_usd": round(sum(profits) - sum(sorted_profits[:25]), 2),
        "top50_removed_usd": round(sum(profits) - sum(sorted_profits[:50]), 2),
        "top100_removed_usd": round(sum(profits) - sum(sorted_profits[:100]), 2),
        "top25_removed_r": round(sum(r_values) - sum(sorted_r[:25]), 2),
        "top50_removed_r": round(sum(r_values) - sum(sorted_r[:50]), 2),
        "top100_removed_r": round(sum(r_values) - sum(sorted_r[:100]), 2),
        "worst_day_usd": round(min(day_values), 2),
        "best_day_usd": round(max(day_values), 2),
        "worst_month_usd": round(min(month_values), 2),
        "best_month_usd": round(max(month_values), 2),
    }


def decision(row: dict[str, Any]) -> str:
    if row.get("trades", 0) < 750:
        return "FAIL_SAMPLE"
    if row.get("trades_per_market_day", 0.0) < 2.0:
        return "FAIL_CADENCE"
    if row.get("win_rate_pct", 0.0) < 55.0:
        return "FAIL_WIN_RATE"
    if (row.get("profit_factor") or 0.0) < 1.20:
        return "FAIL_PF"
    if row.get("top50_removed_usd", 0.0) <= 0:
        return "FAIL_TOP50"
    if row.get("negative_months", 0) > row.get("positive_months", 0):
        return "FAIL_MONTHS"
    return "REVIEW_SNAPBACK_CANDIDATE"


def render(payload: dict[str, Any]) -> str:
    best = payload.get("best_result", {})
    lines = [
        "# XAU M5 Exhaustion Snapback Screen - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline bar-level screen only. No MT5 runtime, charts, presets, orders, or positions were touched.",
        "",
        "## Hypothesis",
        "",
        "When XAUUSD extends too far from M5 EMA50 after a fast 3-bar move and closes near the candle extreme, the immediate next move often snaps back enough for a small mean-reversion profit. This is a different entry family from continuation/retest.",
        "",
        "## Data",
        "",
        f"- Bars: `{payload['bar_path']}`",
        f"- Window: `{payload['window']}`",
        "- Entry/exit uses bid/ask bar prices and adverse-first same-bar TP/SL ordering.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision', '')}` |",
        f"| Variant | `{best.get('name', '')}` |",
        f"| Trades | {best.get('trades', 'n/a')} |",
        f"| Win rate | {best.get('win_rate_pct', 'n/a')}% |",
        f"| PF | {best.get('profit_factor', 'n/a')} |",
        f"| Net | {best.get('net_usd', 'n/a')} USD |",
        f"| Trades / market day | {best.get('trades_per_market_day', 'n/a')} |",
        f"| Top50 removed | {best.get('top50_removed_usd', 'n/a')} USD |",
        f"| Positive / negative months | {best.get('positive_months', 'n/a')} / {best.get('negative_months', 'n/a')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Variant | Trades | WR | PF | Net | T/market day | Top50 | +M | -M |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload.get("top_results", [])[:25], start=1):
        lines.append(
            f"| {index} | `{row.get('decision', '')}` | `{row.get('name', '')}` | {row.get('trades', '')} | {row.get('win_rate_pct', '')}% | {row.get('profit_factor', '')} | {row.get('net_usd', '')} | {row.get('trades_per_market_day', '')} | {row.get('top50_removed_usd', '')} | {row.get('positive_months', '')} | {row.get('negative_months', '')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Verdict: `{payload['verdict']}`",
            f"- Next action: `{payload['next_action']}`",
            "",
            "This is a fast discovery screen, not a production EA. A review candidate must be re-tested in MT5 Strategy Tester before any demo attach.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Trades CSV: `{payload['trades_csv']}`",
            f"- Report: `{payload['report']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def main() -> int:
    df = load_bars()
    params: list[Params] = []
    blocked_sets = {
        "all_hours": (),
        "no_rollover": (0, 1, 22, 23),
        "active_only": (0, 1, 2, 3, 4, 21, 22, 23),
    }
    for direction in ("both", "long", "short"):
        for distance in (1.3, 1.6, 2.0):
            for move in (1.0, 1.4, 1.8):
                for rr in (0.45, 0.60, 0.80):
                    for blocked_name, blocked in blocked_sets.items():
                        name = (
                            f"snap_{direction}_dist{str(distance).replace('.', 'p')}_"
                            f"move{str(move).replace('.', 'p')}_rr{str(rr).replace('.', 'p')}_{blocked_name}"
                        )
                        params.append(
                            Params(
                                name=name,
                                direction_mode=direction,
                                distance_atr=distance,
                                move_atr=move,
                                rr=rr,
                                risk_atr=1.0,
                                time_stop_bars=8,
                                blocked_hours=blocked,
                            )
                        )
    summaries: list[dict[str, Any]] = []
    trades_by_name: dict[str, list[dict[str, Any]]] = {}
    records = df.to_dict("records")
    for param in params:
        trades = simulate(records, param)
        summary = summarize_trades(param.name, trades)
        summary["decision"] = decision(summary)
        summary["params"] = param.__dict__
        summaries.append(summary)
        trades_by_name[param.name] = trades
    summaries.sort(
        key=lambda row: (
            0 if row.get("decision") == "REVIEW_SNAPBACK_CANDIDATE" else 1,
            -float(row.get("net_usd") or 0.0),
            -float(row.get("trades_per_market_day") or 0.0),
        )
    )
    best = summaries[0] if summaries else {}
    verdict = (
        "FOUND_REVIEW_CANDIDATE"
        if best.get("decision") == "REVIEW_SNAPBACK_CANDIDATE"
        else "NO_SNAPBACK_CANDIDATE"
    )
    next_action = (
        "port_to_mt5_strategy_tester_for_exact_test"
        if verdict == "FOUND_REVIEW_CANDIDATE"
        else "discard_snapback_or_redesign_with_structure_filter"
    )
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_trades = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_TRADES.csv"
    payload = {
        "status": "PASS_SNAPBACK_SCREEN_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_bar_screen_only_no_runtime_change",
        "bar_path": rel(BAR_PATH),
        "window": f"{SCREEN_START.date()} -> {SCREEN_END.date()}",
        "variant_count": len(params),
        "verdict": verdict,
        "next_action": next_action,
        "best_result": best,
        "top_results": summaries[:50],
        "json": rel(output_json),
        "csv": rel(output_csv),
        "trades_csv": rel(output_trades),
        "report": rel(output_md),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    write_csv(
        output_csv,
        summaries,
        [
            "decision",
            "name",
            "trades",
            "wins",
            "losses",
            "win_rate_pct",
            "net_usd",
            "profit_factor",
            "net_r",
            "profit_factor_r",
            "trades_per_market_day",
            "trades_per_active_day",
            "positive_months",
            "negative_months",
            "top25_removed_usd",
            "top50_removed_usd",
            "top100_removed_usd",
            "worst_month_usd",
            "best_month_usd",
        ],
    )
    best_trades = trades_by_name.get(str(best.get("name")), [])
    if best_trades:
        write_csv(
            output_trades,
            best_trades,
            [
                "variant",
                "entry_time",
                "entry_date",
                "entry_hour",
                "direction",
                "entry",
                "exit_time",
                "exit",
                "profit",
                "r",
                "risk",
                "atr14",
                "spread",
                "exit_reason",
                "distance_ema50_atr",
                "move3_atr",
                "close_location",
            ],
        )
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "verdict": verdict,
                "decision": best.get("decision"),
                "name": best.get("name"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor": best.get("profit_factor"),
                "net_usd": best.get("net_usd"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top50_removed_usd": best.get("top50_removed_usd"),
                "positive_months": best.get("positive_months"),
                "negative_months": best.get("negative_months"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
