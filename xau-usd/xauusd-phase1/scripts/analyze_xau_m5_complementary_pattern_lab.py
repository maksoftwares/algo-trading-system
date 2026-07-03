from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
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
OUTPUT_STEM = "XAU_M5_COMPLEMENTARY_PATTERN_LAB_2026_07_03"

SCREEN_START = pd.Timestamp("2024-07-01T00:00:00Z")
SCREEN_END = pd.Timestamp("2025-06-30T23:59:59Z")


@dataclass(frozen=True)
class Params:
    name: str
    family: str
    direction_mode: str
    lookback: int
    rr: float
    min_body: float
    close_loc: float
    buffer_atr: float
    min_range_atr: float
    max_range_atr: float
    min_risk_atr: float
    max_risk_atr: float
    max_cost_r: float
    time_stop_bars: int
    blocked_hours: tuple[int, ...]
    h1_trend: bool = True


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
    df["ema8"] = df["mid_close"].ewm(span=8, adjust=False).mean()
    df["ema20"] = df["mid_close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["mid_close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["mid_close"].ewm(span=200, adjust=False).mean()
    df["ema20_slope_atr"] = (df["ema20"] - df["ema20"].shift(6)) / df["atr14"]
    df["ema50_slope_atr"] = (df["ema50"] - df["ema50"].shift(12)) / df["atr14"]
    candle_range = (df["mid_high"] - df["mid_low"]).replace(0, pd.NA)
    df["body_frac"] = ((df["mid_close"] - df["mid_open"]).abs() / candle_range).fillna(0.0)
    df["close_location"] = ((df["mid_close"] - df["mid_low"]) / candle_range).fillna(0.5)
    df["upper_wick_frac"] = ((df["mid_high"] - df[["mid_open", "mid_close"]].max(axis=1)) / candle_range).fillna(0.0)
    df["lower_wick_frac"] = ((df[["mid_open", "mid_close"]].min(axis=1) - df["mid_low"]) / candle_range).fillna(0.0)
    df["range_atr"] = candle_range / df["atr14"]
    df["move3_atr"] = (df["mid_close"] - df["mid_close"].shift(3)) / df["atr14"]
    df["move6_atr"] = (df["mid_close"] - df["mid_close"].shift(6)) / df["atr14"]
    df["spread_price"] = (df["ask_open"] - df["bid_open"]).abs()
    df["dubai_hour"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.hour
    df["entry_date"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.date.astype(str)

    # Completed H1 trend context, merged causally.
    h1 = df.set_index("timestamp_utc").resample("1h").agg({"mid_close": "last"}).dropna()
    h1["h1_ema20"] = h1["mid_close"].ewm(span=20, adjust=False).mean()
    h1["h1_ema50"] = h1["mid_close"].ewm(span=50, adjust=False).mean()
    h1["h1_slope_atr_proxy"] = h1["h1_ema20"] - h1["h1_ema20"].shift(3)
    h1 = h1[["h1_ema20", "h1_ema50", "h1_slope_atr_proxy"]].reset_index()
    df = pd.merge_asof(df.sort_values("timestamp_utc"), h1, on="timestamp_utc", direction="backward")

    for lookback in (8, 12, 18, 24):
        df[f"prior_high_{lookback}"] = df["mid_high"].shift(1).rolling(lookback, min_periods=lookback).max()
        df[f"prior_low_{lookback}"] = df["mid_low"].shift(1).rolling(lookback, min_periods=lookback).min()
        df[f"prior_range_{lookback}"] = df[f"prior_high_{lookback}"] - df[f"prior_low_{lookback}"]

    required = [
        "atr14",
        "ema20_slope_atr",
        "ema50_slope_atr",
        "body_frac",
        "close_location",
        "upper_wick_frac",
        "lower_wick_frac",
        "range_atr",
        "move3_atr",
        "move6_atr",
        "spread_price",
        "h1_ema20",
        "h1_ema50",
        "h1_slope_atr_proxy",
        "prior_high_24",
        "prior_low_24",
        "prior_range_24",
    ]
    return df.dropna(subset=required).reset_index(drop=True)


def trend_ok(row: dict[str, Any], direction: str, params: Params) -> bool:
    if not params.h1_trend:
        return True
    if direction == "LONG":
        return (
            float(row["h1_ema20"]) > float(row["h1_ema50"])
            and float(row["h1_slope_atr_proxy"]) > 0
            and float(row["ema20"]) > float(row["ema50"])
        )
    return (
        float(row["h1_ema20"]) < float(row["h1_ema50"])
        and float(row["h1_slope_atr_proxy"]) < 0
        and float(row["ema20"]) < float(row["ema50"])
    )


def signal_for(row: dict[str, Any], previous: dict[str, Any], params: Params) -> str | None:
    if int(row["dubai_hour"]) in params.blocked_hours:
        return None
    if not (params.min_range_atr <= float(row["range_atr"]) <= params.max_range_atr):
        return None
    if float(row["body_frac"]) < params.min_body:
        return None
    prior_high = float(row[f"prior_high_{params.lookback}"])
    prior_low = float(row[f"prior_low_{params.lookback}"])
    prior_range_atr = float(row[f"prior_range_{params.lookback}"]) / float(row["atr14"])
    close = float(row["mid_close"])
    high = float(row["mid_high"])
    low = float(row["mid_low"])
    atr = float(row["atr14"])
    buffer = params.buffer_atr * atr

    long_allowed = params.direction_mode in {"both", "long"}
    short_allowed = params.direction_mode in {"both", "short"}

    if params.family == "micro_breakout":
        if (
            long_allowed
            and close > prior_high + buffer
            and float(row["close_location"]) >= params.close_loc
            and float(row["move3_atr"]) > 0.35
            and trend_ok(row, "LONG", params)
        ):
            return "LONG"
        if (
            short_allowed
            and close < prior_low - buffer
            and float(row["close_location"]) <= 1.0 - params.close_loc
            and float(row["move3_atr"]) < -0.35
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT"

    if params.family == "ema_reclaim":
        reclaimed_long = float(previous["mid_close"]) < float(previous["ema20"]) and close > float(row["ema20"])
        reclaimed_short = float(previous["mid_close"]) > float(previous["ema20"]) and close < float(row["ema20"])
        if (
            long_allowed
            and reclaimed_long
            and float(row["close_location"]) >= params.close_loc
            and abs(close - float(row["ema20"])) <= params.max_range_atr * atr
            and trend_ok(row, "LONG", params)
        ):
            return "LONG"
        if (
            short_allowed
            and reclaimed_short
            and float(row["close_location"]) <= 1.0 - params.close_loc
            and abs(close - float(row["ema20"])) <= params.max_range_atr * atr
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT"

    if params.family == "failed_break_reversal":
        if (
            long_allowed
            and low < prior_low - buffer
            and close > prior_low
            and float(row["lower_wick_frac"]) >= 0.35
            and float(row["close_location"]) >= params.close_loc
            and prior_range_atr <= 3.0
        ):
            return "LONG"
        if (
            short_allowed
            and high > prior_high + buffer
            and close < prior_high
            and float(row["upper_wick_frac"]) >= 0.35
            and float(row["close_location"]) <= 1.0 - params.close_loc
            and prior_range_atr <= 3.0
        ):
            return "SHORT"

    if params.family == "compression_breakout":
        compressed = prior_range_atr <= params.max_range_atr
        if (
            long_allowed
            and compressed
            and close > prior_high + buffer
            and float(row["close_location"]) >= params.close_loc
            and trend_ok(row, "LONG", params)
        ):
            return "LONG"
        if (
            short_allowed
            and compressed
            and close < prior_low - buffer
            and float(row["close_location"]) <= 1.0 - params.close_loc
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT"
    return None


def simulate_exit(
    rows: list[dict[str, Any]],
    entry_index: int,
    direction: str,
    entry: float,
    risk: float,
    rr: float,
    time_stop_bars: int,
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
    start = max(260, params.lookback + 3)
    index = start
    while index < len(rows) - params.time_stop_bars - 2:
        row = rows[index]
        previous = rows[index - 1]
        direction = signal_for(row, previous, params)
        if direction is None:
            index += 1
            continue
        atr = float(row["atr14"])
        entry_index = index + 1
        entry_row = rows[entry_index]
        spread = float(entry_row["spread_price"])
        if direction == "LONG":
            entry = float(entry_row["ask_open"])
            structure_stop = min(float(row["mid_low"]), float(row[f"prior_low_{params.lookback}"]))
            risk = max(entry - structure_stop + params.buffer_atr * atr, params.min_risk_atr * atr, 3.0 * spread)
        else:
            entry = float(entry_row["bid_open"])
            structure_stop = max(float(row["mid_high"]), float(row[f"prior_high_{params.lookback}"]))
            risk = max(structure_stop - entry + params.buffer_atr * atr, params.min_risk_atr * atr, 3.0 * spread)
        if risk <= 0 or risk > params.max_risk_atr * atr or (spread / risk) > params.max_cost_r:
            index += 1
            continue
        exit_index, exit_price, exit_reason = simulate_exit(rows, entry_index, direction, entry, risk, params.rr, params.time_stop_bars)
        profit = (exit_price - entry) if direction == "LONG" else (entry - exit_price)
        trades.append(
            {
                "variant": params.name,
                "family": params.family,
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
                "cost_r": round(spread / risk, 4),
                "exit_reason": exit_reason,
                "close_location": round(float(row["close_location"]), 4),
                "body_frac": round(float(row["body_frac"]), 4),
                "range_atr": round(float(row["range_atr"]), 4),
                "move3_atr": round(float(row["move3_atr"]), 4),
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
    return {
        "window": window,
        "available": True,
        "worst": round(min(nets), 2),
        "negative": sum(value < 0 for value in nets),
    }


def market_days(start: str, end: str) -> int:
    return len(pd.bdate_range(pd.Timestamp(start), pd.Timestamp(end)))


def summarize(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {"name": name, "trades": 0}
    r_values = [float(row["r"]) for row in trades]
    price_values = [float(row["profit"]) for row in trades]
    by_day: dict[str, list[float]] = {}
    by_month: dict[str, list[float]] = {}
    by_direction: dict[str, list[float]] = {}
    for row in trades:
        by_day.setdefault(row["entry_date"], []).append(float(row["r"]))
        by_month.setdefault(row["entry_date"][:7], []).append(float(row["r"]))
        by_direction.setdefault(row["direction"], []).append(float(row["r"]))
    start = min(row["entry_date"] for row in trades)
    end = max(row["entry_date"] for row in trades)
    market_day_count = market_days(start, end)
    ordered_r = [float(row["r"]) for row in sorted(trades, key=lambda item: item["exit_time"])]
    wins = sum(value > 0 for value in r_values)
    return {
        "name": name,
        "family": trades[0]["family"],
        "trades": len(trades),
        "wins": wins,
        "losses": sum(value < 0 for value in r_values),
        "win_rate_pct": round(100.0 * wins / len(trades), 2),
        "net_r": round(sum(r_values), 2),
        "profit_factor_r": profit_factor(r_values),
        "net_price": round(sum(price_values), 2),
        "profit_factor_price": profit_factor(price_values),
        "active_days": len(by_day),
        "market_days": market_day_count,
        "trades_per_market_day": round(len(trades) / market_day_count, 2),
        "trades_per_active_day": round(len(trades) / len(by_day), 2),
        "three_plus_market_day_pct": round(100.0 * sum(len(values) >= 3 for values in by_day.values()) / market_day_count, 2),
        "positive_active_day_pct": round(100.0 * sum(sum(values) > 0 for values in by_day.values()) / len(by_day), 2),
        "positive_months": sum(sum(values) > 0 for values in by_month.values()),
        "negative_months": sum(sum(values) < 0 for values in by_month.values()),
        "top25_removed_r": top_removed(r_values, 25),
        "top50_removed_r": top_removed(r_values, 50),
        "top100_removed_r": top_removed(r_values, 100),
        "top200_removed_r": top_removed(r_values, 200),
        "rolling100": rolling_negative(ordered_r, 100),
        "rolling250": rolling_negative(ordered_r, 250),
        "direction": {
            direction: {
                "trades": len(values),
                "net_r": round(sum(values), 2),
                "profit_factor_r": profit_factor(values),
            }
            for direction, values in sorted(by_direction.items())
        },
    }


def decision(row: dict[str, Any]) -> str:
    if row.get("trades", 0) < 500:
        return "FAIL_SAMPLE"
    if row.get("trades_per_market_day", 0.0) < 3.0:
        return "FAIL_CADENCE"
    if row.get("win_rate_pct", 0.0) < 60.0:
        return "FAIL_WIN_RATE"
    if (row.get("profit_factor_r") or 0.0) < 1.25:
        return "FAIL_PF_R"
    if row.get("top200_removed_r", 0.0) <= 0:
        return "FAIL_TOP200_R"
    if row.get("rolling250", {}).get("negative", 1) > 0:
        return "REVISE_ROLLING250"
    return "REVIEW_COMPLEMENTARY_PATTERN_CANDIDATE"


def build_params() -> list[Params]:
    params: list[Params] = []
    blocked_sets = {
        "all": (),
        "no_rollover": (0, 1, 22, 23),
    }
    for family in ("micro_breakout", "ema_reclaim", "failed_break_reversal", "compression_breakout"):
        for direction in ("both", "long", "short"):
            for lookback in (12,):
                for rr in (0.55,):
                    for blocked_name, blocked_hours in blocked_sets.items():
                        if family == "compression_breakout":
                            max_ranges = (1.5,)
                        elif family == "failed_break_reversal":
                            max_ranges = (2.4,)
                        else:
                            max_ranges = (3.2,)
                        for max_range_atr in max_ranges:
                            name = (
                                f"{family}_{direction}_lb{lookback}_rr{str(rr).replace('.', 'p')}_"
                                f"rng{str(max_range_atr).replace('.', 'p')}_{blocked_name}"
                            )
                            params.append(
                                Params(
                                    name=name,
                                    family=family,
                                    direction_mode=direction,
                                    lookback=lookback,
                                    rr=rr,
                                    min_body=0.28 if family != "failed_break_reversal" else 0.15,
                                    close_loc=0.58 if family != "failed_break_reversal" else 0.62,
                                    buffer_atr=0.04 if family != "ema_reclaim" else 0.02,
                                    min_range_atr=0.20,
                                    max_range_atr=max_range_atr,
                                    min_risk_atr=0.55,
                                    max_risk_atr=2.20,
                                    max_cost_r=0.12,
                                    time_stop_bars=12 if rr < 0.8 else 18,
                                    blocked_hours=blocked_hours,
                                    h1_trend=family != "failed_break_reversal",
                                )
                            )
    return params


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload.get("best_result", {})
    lines = [
        "# XAU M5 Complementary Pattern Lab - 2026-07-03",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Scope: offline bar-level discovery only. No MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Purpose",
        "",
        "The exact MT5 risk-normalized momentum package is close to the owner goal but still fails robustness. This lab tests genuinely different entry families instead of more hour-pruning of the same momentum stream.",
        "",
        "Families tested: `micro_breakout`, `ema_reclaim`, `failed_break_reversal`, and `compression_breakout`.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision', '')}` |",
        f"| Family | `{best.get('family', '')}` |",
        f"| Variant | `{best.get('name', '')}` |",
        f"| Trades | {best.get('trades', 'n/a')} |",
        f"| Win rate | {best.get('win_rate_pct', 'n/a')}% |",
        f"| PF R | {best.get('profit_factor_r', 'n/a')} |",
        f"| Net R | {best.get('net_r', 'n/a')} |",
        f"| Trades / market day | {best.get('trades_per_market_day', 'n/a')} |",
        f"| Top200 removed R | {best.get('top200_removed_r', 'n/a')} |",
        f"| Rolling250 negative windows | {best.get('rolling250', {}).get('negative', 'n/a')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Family | Variant | Trades | WR | PF R | Net R | T/market day | Top200 R | Roll250 neg |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_results"][:25], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{family}` | `{name}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {top200:.2f} | {roll} |".format(
                rank=index,
                decision=row.get("decision", ""),
                family=row.get("family", ""),
                name=str(row.get("name", ""))[:80],
                trades=row.get("trades", 0),
                wr=row.get("win_rate_pct", 0.0),
                pf=row.get("profit_factor_r"),
                net=row.get("net_r", 0.0),
                tmd=row.get("trades_per_market_day", 0.0),
                top200=row.get("top200_removed_r", 0.0),
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
            "A bar-level review candidate still needs exact MT5 Strategy Tester implementation before any demo use.",
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
    params = build_params()
    summaries: list[dict[str, Any]] = []
    trades_by_name: dict[str, list[dict[str, Any]]] = {}
    for param in params:
        trades = simulate(df, param)
        summary = summarize(param.name, trades) if trades else {"name": param.name, "family": param.family, "trades": 0}
        summary["params"] = asdict(param)
        summary["decision"] = decision(summary)
        summaries.append(summary)
        trades_by_name[param.name] = trades
    summaries.sort(
        key=lambda row: (
            row["decision"].startswith("FAIL"),
            row["decision"].startswith("REVISE"),
            -float(row.get("trades_per_market_day") or 0.0),
            -float(row.get("net_r") or 0.0),
        )
    )
    best = summaries[0] if summaries else {}
    verdict = (
        "FOUND_REVIEW_CANDIDATE"
        if str(best.get("decision", "")).startswith("REVIEW")
        else "NO_COMPLEMENTARY_PATTERN_CANDIDATE"
    )
    next_action = (
        "port_best_candidate_to_exact_mt5_strategy_tester"
        if verdict == "FOUND_REVIEW_CANDIDATE"
        else "continue_with_different_family_or_ml_feature_ranked_signal"
    )
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_trades = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_TRADES.csv"
    best_trades = trades_by_name.get(str(best.get("name")), [])
    payload = {
        "status": "PASS_PATTERN_LAB_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_bar_discovery_only_no_runtime_change",
        "bar_path": rel(BAR_PATH),
        "window": f"{SCREEN_START.date()} -> {SCREEN_END.date()}",
        "variant_count": len(params),
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
            "profit_factor_r",
            "net_r",
            "trades_per_market_day",
            "three_plus_market_day_pct",
            "positive_active_day_pct",
            "top100_removed_r",
            "top200_removed_r",
            "positive_months",
            "negative_months",
        ],
    )
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
            ],
        )
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "verdict": verdict,
                "decision": best.get("decision"),
                "family": best.get("family"),
                "name": best.get("name"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor_r": best.get("profit_factor_r"),
                "net_r": best.get("net_r"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top200_removed_r": best.get("top200_removed_r"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
