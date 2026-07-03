from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
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
OUTPUT_STEM = "XAU_M5_CANDLE_STATE_SCREEN_2026_07_03"

SCREEN_START = pd.Timestamp("2024-07-01T00:00:00Z")
SCREEN_END = pd.Timestamp("2025-06-30T23:59:59Z")


@dataclass(frozen=True)
class Params:
    name: str
    family: str
    direction_mode: str
    rr: float
    move_atr: float
    min_body: float
    close_loc: float
    wick_ratio: float
    min_range_atr: float
    max_range_atr: float
    min_risk_atr: float
    max_risk_atr: float
    max_cost_r: float
    time_stop_bars: int
    blocked_hours: tuple[int, ...]
    trend_filter: str


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def market_days(start: date, end: date) -> int:
    total = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            total += 1
        current += timedelta(days=1)
    return total


def session_bucket(hour: int) -> str:
    if 0 <= hour <= 5:
        return "night"
    if 6 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 15:
        return "afternoon"
    if 16 <= hour <= 19:
        return "evening"
    return "late"


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
    df["ema20"] = df["mid_close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["mid_close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["mid_close"].ewm(span=200, adjust=False).mean()
    df["ema20_slope_atr"] = (df["ema20"] - df["ema20"].shift(6)) / df["atr14"]
    candle_range = (df["mid_high"] - df["mid_low"]).replace(0, pd.NA)
    body = (df["mid_close"] - df["mid_open"]).abs()
    upper_wick = df["mid_high"] - df[["mid_open", "mid_close"]].max(axis=1)
    lower_wick = df[["mid_open", "mid_close"]].min(axis=1) - df["mid_low"]
    df["body_frac"] = (body / candle_range).fillna(0.0)
    df["close_location"] = ((df["mid_close"] - df["mid_low"]) / candle_range).fillna(0.5)
    df["range_atr"] = candle_range / df["atr14"]
    df["move2_atr"] = (df["mid_close"] - df["mid_close"].shift(2)) / df["atr14"]
    df["move3_atr"] = (df["mid_close"] - df["mid_close"].shift(3)) / df["atr14"]
    df["upper_wick_body"] = (upper_wick / body.replace(0, pd.NA)).fillna(0.0)
    df["lower_wick_body"] = (lower_wick / body.replace(0, pd.NA)).fillna(0.0)
    df["prev_close_location"] = df["close_location"].shift(1)
    df["prev_body_frac"] = df["body_frac"].shift(1)
    df["prev_range_atr"] = df["range_atr"].shift(1)
    df["spread_price"] = (df["ask_open"] - df["bid_open"]).abs()
    df["dubai_hour"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.hour
    df["entry_date"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.date.astype(str)
    return df.dropna(
        subset=[
            "atr14",
            "ema20_slope_atr",
            "body_frac",
            "close_location",
            "range_atr",
            "move2_atr",
            "move3_atr",
            "upper_wick_body",
            "lower_wick_body",
            "prev_close_location",
            "prev_body_frac",
            "prev_range_atr",
        ]
    ).reset_index(drop=True)


def trend_ok(row: dict[str, Any], direction: str, params: Params) -> bool:
    if params.trend_filter == "none":
        return True
    slope = float(row["ema20_slope_atr"])
    if params.trend_filter == "ema20":
        return slope > 0 if direction == "LONG" else slope < 0
    if params.trend_filter == "ema_stack":
        if direction == "LONG":
            return float(row["ema20"]) > float(row["ema50"]) > float(row["ema200"]) and slope > 0
        return float(row["ema20"]) < float(row["ema50"]) < float(row["ema200"]) and slope < 0
    return True


def signal_for(row: dict[str, Any], params: Params) -> str | None:
    if int(row["dubai_hour"]) in params.blocked_hours:
        return None
    if not (params.min_range_atr <= float(row["range_atr"]) <= params.max_range_atr):
        return None
    long_allowed = params.direction_mode in {"both", "long"}
    short_allowed = params.direction_mode in {"both", "short"}
    close_loc = float(row["close_location"])

    if params.family == "streak_continue":
        if (
            long_allowed
            and float(row["move3_atr"]) >= params.move_atr
            and float(row["body_frac"]) >= params.min_body
            and close_loc >= params.close_loc
            and trend_ok(row, "LONG", params)
        ):
            return "LONG"
        if (
            short_allowed
            and float(row["move3_atr"]) <= -params.move_atr
            and float(row["body_frac"]) >= params.min_body
            and close_loc <= 1.0 - params.close_loc
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT"

    if params.family == "wick_reject":
        if (
            long_allowed
            and float(row["lower_wick_body"]) >= params.wick_ratio
            and close_loc >= params.close_loc
            and float(row["move2_atr"]) <= params.move_atr
            and trend_ok(row, "LONG", params)
        ):
            return "LONG"
        if (
            short_allowed
            and float(row["upper_wick_body"]) >= params.wick_ratio
            and close_loc <= 1.0 - params.close_loc
            and float(row["move2_atr"]) >= -params.move_atr
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT"

    if params.family == "two_bar_flip":
        previous_bear = float(row["prev_close_location"]) <= 0.25 and float(row["prev_body_frac"]) >= params.min_body
        previous_bull = float(row["prev_close_location"]) >= 0.75 and float(row["prev_body_frac"]) >= params.min_body
        if long_allowed and previous_bear and close_loc >= params.close_loc and trend_ok(row, "LONG", params):
            return "LONG"
        if short_allowed and previous_bull and close_loc <= 1.0 - params.close_loc and trend_ok(row, "SHORT", params):
            return "SHORT"
    return None


def simulate_exit(
    rows: list[dict[str, Any]], entry_index: int, direction: str, entry: float, risk: float, rr: float, time_stop_bars: int
) -> tuple[int, float, str]:
    if direction == "LONG":
        sl = entry - risk
        tp = entry + rr * risk
    else:
        sl = entry + risk
        tp = entry - rr * risk
    end = min(entry_index + time_stop_bars, len(rows) - 1)
    for index in range(entry_index, end + 1):
        bar = rows[index]
        if direction == "LONG":
            hit_sl = float(bar["bid_low"]) <= sl
            hit_tp = float(bar["bid_high"]) >= tp
            if hit_sl and hit_tp:
                return index, sl, "sl_adverse_first"
            if hit_sl:
                return index, sl, "sl"
            if hit_tp:
                return index, tp, "tp"
        else:
            hit_sl = float(bar["ask_high"]) >= sl
            hit_tp = float(bar["ask_low"]) <= tp
            if hit_sl and hit_tp:
                return index, sl, "sl_adverse_first"
            if hit_sl:
                return index, sl, "sl"
            if hit_tp:
                return index, tp, "tp"
    last = rows[end]
    return end, float(last["bid_close"] if direction == "LONG" else last["ask_close"]), "time_stop"


def simulate(df: pd.DataFrame, params: Params) -> list[dict[str, Any]]:
    rows = df.to_dict("records")
    trades: list[dict[str, Any]] = []
    index = 260
    while index < len(rows) - params.time_stop_bars - 2:
        row = rows[index]
        direction = signal_for(row, params)
        if direction is None:
            index += 1
            continue
        entry_index = index + 1
        entry_row = rows[entry_index]
        atr = float(row["atr14"])
        spread = float(entry_row["spread_price"])
        if direction == "LONG":
            entry = float(entry_row["ask_open"])
            structure = float(row["mid_low"])
            risk = max(entry - structure, params.min_risk_atr * atr, 3.0 * spread)
        else:
            entry = float(entry_row["bid_open"])
            structure = float(row["mid_high"])
            risk = max(structure - entry, params.min_risk_atr * atr, 3.0 * spread)
        if risk <= 0 or risk > params.max_risk_atr * atr or (spread / risk) > params.max_cost_r:
            index += 1
            continue
        exit_index, exit_price, reason = simulate_exit(rows, entry_index, direction, entry, risk, params.rr, params.time_stop_bars)
        profit = (exit_price - entry) if direction == "LONG" else (entry - exit_price)
        trades.append(
            {
                "variant": params.name,
                "family": params.family,
                "entry_time": entry_row["timestamp_utc"].isoformat(),
                "entry_date": entry_row["entry_date"],
                "entry_hour": int(entry_row["dubai_hour"]),
                "entry_session": session_bucket(int(entry_row["dubai_hour"])),
                "direction": direction,
                "entry": round(entry, 2),
                "exit_time": rows[exit_index]["timestamp_utc"].isoformat(),
                "exit": round(exit_price, 2),
                "profit": round(profit, 2),
                "r": round(profit / risk, 4),
                "risk": round(risk, 4),
                "atr14": round(atr, 4),
                "spread": round(spread, 4),
                "cost_r": round(spread / risk, 4),
                "exit_reason": reason,
                "close_location": round(float(row["close_location"]), 4),
                "body_frac": round(float(row["body_frac"]), 4),
                "range_atr": round(float(row["range_atr"]), 4),
                "move3_atr": round(float(row["move3_atr"]), 4),
                "upper_wick_body": round(float(row["upper_wick_body"]), 4),
                "lower_wick_body": round(float(row["lower_wick_body"]), 4),
            }
        )
        index = exit_index + 1
    return trades


def profit_factor(values: list[float]) -> float | None:
    gross_profit = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


def top_removed(values: list[float], count: int) -> float:
    wins = sorted((value for value in values if value > 0), reverse=True)
    return round(sum(values) - sum(wins[:count]), 2)


def rolling_negative(values: list[float], window: int) -> dict[str, Any]:
    if len(values) < window:
        return {"window": window, "available": False}
    nets = [sum(values[index : index + window]) for index in range(len(values) - window + 1)]
    return {"window": window, "available": True, "worst": round(min(nets), 2), "negative": sum(value < 0 for value in nets)}


def summarize(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {"name": name, "trades": 0}
    values = [float(row["profit"]) for row in trades]
    ordered = [float(row["profit"]) for row in sorted(trades, key=lambda item: item["exit_time"])]
    by_day: dict[str, list[float]] = defaultdict(list)
    by_month: dict[str, list[float]] = defaultdict(list)
    for row in trades:
        by_day[row["entry_date"]].append(float(row["profit"]))
        by_month[row["entry_date"][:7]].append(float(row["profit"]))
    start = min(pd.Timestamp(row["entry_time"]).date() for row in trades)
    end = max(pd.Timestamp(row["entry_time"]).date() for row in trades)
    days = market_days(start, end)
    wins = sum(value > 0 for value in values)
    return {
        "name": name,
        "family": trades[0]["family"],
        "trades": len(trades),
        "wins": wins,
        "losses": sum(value < 0 for value in values),
        "win_rate_pct": round(100.0 * wins / len(trades), 2),
        "net": round(sum(values), 2),
        "profit_factor": profit_factor(values),
        "market_days": days,
        "active_days": len(by_day),
        "trades_per_market_day": round(len(trades) / days, 2),
        "trades_per_active_day": round(len(trades) / len(by_day), 2),
        "three_plus_market_day_pct": round(100.0 * sum(len(day_values) >= 3 for day_values in by_day.values()) / days, 2),
        "positive_months": sum(sum(month_values) > 0 for month_values in by_month.values()),
        "negative_months": sum(sum(month_values) < 0 for month_values in by_month.values()),
        "top50_removed": top_removed(values, 50),
        "top100_removed": top_removed(values, 100),
        "top200_removed": top_removed(values, 200),
        "rolling100": rolling_negative(ordered, 100),
        "rolling250": rolling_negative(ordered, 250),
    }


def decision(row: dict[str, Any]) -> str:
    if row.get("trades", 0) < 500:
        return "FAIL_SAMPLE"
    if row.get("trades_per_market_day", 0.0) < 3.0:
        return "FAIL_CADENCE"
    if row.get("win_rate_pct", 0.0) < 60.0:
        return "FAIL_WR"
    if (row.get("profit_factor") or 0.0) < 1.25:
        return "FAIL_PF"
    if row.get("top100_removed", 0.0) <= 0:
        return "FAIL_TOP100"
    if row.get("top200_removed", 0.0) <= 0:
        return "FAIL_TOP200"
    if row.get("rolling250", {}).get("negative", 1) > 0:
        return "REVISE_ROLLING250"
    return "CANDLE_STATE_REVIEW_CANDIDATE"


def build_params() -> list[Params]:
    blocked_sets = {"all": (), "no_rollover": (0, 1, 22, 23)}
    rows: list[Params] = []
    for family in ("streak_continue", "wick_reject", "two_bar_flip"):
        for direction in ("both", "long", "short"):
            for rr in (0.7, 1.0):
                for blocked_name, blocked_hours in blocked_sets.items():
                    for trend in ("none", "ema20"):
                        name = f"candle_{family}_{direction}_rr{str(rr).replace('.', 'p')}_{blocked_name}_{trend}"
                        rows.append(
                            Params(
                                name=name,
                                family=family,
                                direction_mode=direction,
                                rr=rr,
                                move_atr=0.65,
                                min_body=0.35,
                                close_loc=0.68,
                                wick_ratio=1.25,
                                min_range_atr=0.25,
                                max_range_atr=3.2,
                                min_risk_atr=0.55,
                                max_risk_atr=2.4,
                                max_cost_r=0.12,
                                time_stop_bars=12 if rr < 1.0 else 18,
                                blocked_hours=blocked_hours,
                                trend_filter=trend,
                            )
                        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload["best_result"]
    lines = [
        "# XAU M5 Candle-State Screen - 2026-07-03",
        "",
        "Scope: offline bar-level discovery only. No MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision')}` |",
        f"| Variant | `{best.get('name')}` |",
        f"| Trades | {best.get('trades')} |",
        f"| Win rate | {best.get('win_rate_pct')}% |",
        f"| PF | {best.get('profit_factor')} |",
        f"| Net | {best.get('net')} |",
        f"| Trades / market day | {best.get('trades_per_market_day')} |",
        f"| Top100 removed | {best.get('top100_removed')} |",
        f"| Top200 removed | {best.get('top200_removed')} |",
        f"| Rolling250 negative | {best.get('rolling250', {}).get('negative')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Variant | Trades | WR | PF | Net | T/market day | Top200 | Roll250 neg |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_results"][:25], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{name}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {top200:.2f} | {roll} |".format(
                rank=index,
                decision=row.get("decision"),
                name=row.get("name"),
                trades=row.get("trades", 0),
                wr=row.get("win_rate_pct", 0.0),
                pf=row.get("profit_factor"),
                net=row.get("net", 0.0),
                tmd=row.get("trades_per_market_day", 0.0),
                top200=row.get("top200_removed", 0.0),
                roll=row.get("rolling250", {}).get("negative", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Verdict: `{payload['verdict']}`",
            f"- Next action: `{payload['next_action']}`",
            "",
            "A candle-state candidate must be exact-tested in MT5 Strategy Tester before any demo use.",
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Best trades CSV: `{payload['best_trades_csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    df = load_bars()
    summaries: list[dict[str, Any]] = []
    trades_by_name: dict[str, list[dict[str, Any]]] = {}
    for params in build_params():
        trades = simulate(df, params)
        summary = summarize(params.name, trades) if trades else {"name": params.name, "family": params.family, "trades": 0}
        summary["params"] = asdict(params)
        summary["decision"] = decision(summary)
        summaries.append(summary)
        trades_by_name[params.name] = trades
    summaries.sort(
        key=lambda row: (
            row["decision"].startswith("FAIL"),
            row["decision"].startswith("REVISE"),
            -float(row.get("trades_per_market_day") or 0.0),
            -float(row.get("profit_factor") or 0.0),
            -float(row.get("net") or 0.0),
        )
    )
    best = summaries[0]
    verdict = "FOUND_CANDLE_STATE_CANDIDATE" if str(best.get("decision")).endswith("CANDIDATE") else "NO_CANDLE_STATE_CANDIDATE"
    next_action = "port_to_exact_mt5_strategy_tester" if verdict.startswith("FOUND") else "continue_different_entry_family"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_trades = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_TRADES.csv"
    payload = {
        "status": "PASS_CANDLE_STATE_SCREEN_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_bar_discovery_only_no_runtime_change",
        "bar_path": rel(BAR_PATH),
        "window": f"{SCREEN_START.date()} -> {SCREEN_END.date()}",
        "variant_count": len(summaries),
        "verdict": verdict,
        "next_action": next_action,
        "best_result": best,
        "top_results": summaries[:50],
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
        "best_trades_csv": rel(output_trades),
    }
    output_md.write_text(render(payload), encoding="utf-8")
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(
        output_csv,
        summaries,
        [
            "decision",
            "family",
            "name",
            "trades",
            "win_rate_pct",
            "profit_factor",
            "net",
            "trades_per_market_day",
            "top100_removed",
            "top200_removed",
            "positive_months",
            "negative_months",
        ],
    )
    best_trades = trades_by_name.get(str(best.get("name")), [])
    if best_trades:
        write_csv(
            output_trades,
            best_trades,
            [
                "variant",
                "family",
                "entry_time",
                "entry_date",
                "entry_hour",
                "entry_session",
                "direction",
                "entry",
                "exit_time",
                "exit",
                "profit",
                "r",
                "risk",
                "atr14",
                "spread",
                "cost_r",
                "exit_reason",
                "close_location",
                "body_frac",
                "range_atr",
                "move3_atr",
                "upper_wick_body",
                "lower_wick_body",
            ],
        )
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "verdict": verdict,
                "decision": best.get("decision"),
                "variant": best.get("name"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor": best.get("profit_factor"),
                "net": best.get("net"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top200_removed": best.get("top200_removed"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
