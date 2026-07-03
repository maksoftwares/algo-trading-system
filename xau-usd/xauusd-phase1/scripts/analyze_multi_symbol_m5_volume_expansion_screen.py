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
BARS_ROOT = PHASE1_ROOT.parents[0] / "xauusd-phase0" / "data" / "processed" / "bars" / "capital_com"
OUTPUT_STEM = "MULTI_SYMBOL_M5_VOLUME_EXPANSION_SCREEN_2026_07_03"

SCREEN_START = pd.Timestamp("2024-07-01T00:00:00Z")
SCREEN_END = pd.Timestamp("2025-06-30T23:59:59Z")


@dataclass(frozen=True)
class Params:
    name: str
    symbol: str
    family: str
    direction_mode: str
    rr: float
    min_volume_ratio: float
    min_range_atr: float
    max_range_atr: float
    min_move_atr: float
    min_body: float
    close_loc: float
    min_compression_atr: float
    min_risk_atr: float
    max_risk_atr: float
    max_cost_r: float
    time_stop_bars: int
    blocked_hours: tuple[int, ...]
    trend_filter: bool


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


def bar_path(symbol: str) -> Path:
    return BARS_ROOT / symbol / "M5" / f"{symbol}_capital_com_M5_20160103_20250701.csv"


def load_bars(symbol: str) -> pd.DataFrame:
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
        "tick_count",
        "volume_sum",
    ]
    path = bar_path(symbol)
    df = pd.read_csv(path, usecols=usecols)
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
    df["ema20_slope_atr"] = (df["ema20"] - df["ema20"].shift(6)) / df["atr14"]
    candle_range = (df["mid_high"] - df["mid_low"]).replace(0, pd.NA)
    body = (df["mid_close"] - df["mid_open"]).abs()
    df["body_frac"] = (body / candle_range).fillna(0.0)
    df["close_location"] = ((df["mid_close"] - df["mid_low"]) / candle_range).fillna(0.5)
    df["range_atr"] = candle_range / df["atr14"]
    df["move3_atr"] = (df["mid_close"] - df["mid_close"].shift(3)) / df["atr14"]
    df["move6_atr"] = (df["mid_close"] - df["mid_close"].shift(6)) / df["atr14"]
    df["spread_price"] = (df["ask_open"] - df["bid_open"]).abs()
    volume = df["volume_sum"].where(df["volume_sum"] > 0, df["tick_count"]).fillna(1.0).clip(lower=1.0)
    df["volume_ratio"] = volume / volume.rolling(48, min_periods=24).median()
    df["prior_high_12"] = df["mid_high"].shift(1).rolling(12, min_periods=12).max()
    df["prior_low_12"] = df["mid_low"].shift(1).rolling(12, min_periods=12).min()
    df["prior_range_12_atr"] = (df["prior_high_12"] - df["prior_low_12"]) / df["atr14"]
    df["dubai_hour"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.hour
    df["entry_date"] = (df["timestamp_utc"] + pd.Timedelta(hours=4)).dt.date.astype(str)
    required = [
        "atr14",
        "ema20_slope_atr",
        "body_frac",
        "close_location",
        "range_atr",
        "move3_atr",
        "move6_atr",
        "spread_price",
        "volume_ratio",
        "prior_high_12",
        "prior_low_12",
        "prior_range_12_atr",
    ]
    return df.dropna(subset=required).reset_index(drop=True)


def trend_ok(row: dict[str, Any], direction: str, params: Params) -> bool:
    if not params.trend_filter:
        return True
    if direction == "LONG":
        return float(row["ema20"]) > float(row["ema50"]) and float(row["ema20_slope_atr"]) > 0
    return float(row["ema20"]) < float(row["ema50"]) and float(row["ema20_slope_atr"]) < 0


def signal_for(row: dict[str, Any], params: Params) -> str | None:
    if int(row["dubai_hour"]) in params.blocked_hours:
        return None
    if float(row["volume_ratio"]) < params.min_volume_ratio:
        return None
    if not (params.min_range_atr <= float(row["range_atr"]) <= params.max_range_atr):
        return None
    if float(row["body_frac"]) < params.min_body:
        return None
    long_allowed = params.direction_mode in {"both", "long"}
    short_allowed = params.direction_mode in {"both", "short"}
    close_loc = float(row["close_location"])

    if params.family == "volume_impulse":
        if (
            long_allowed
            and float(row["move3_atr"]) >= params.min_move_atr
            and close_loc >= params.close_loc
            and trend_ok(row, "LONG", params)
        ):
            return "LONG"
        if (
            short_allowed
            and float(row["move3_atr"]) <= -params.min_move_atr
            and close_loc <= 1.0 - params.close_loc
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT"

    if params.family == "compressed_expansion":
        compressed = float(row["prior_range_12_atr"]) <= params.min_compression_atr
        if (
            long_allowed
            and compressed
            and float(row["mid_close"]) > float(row["prior_high_12"])
            and close_loc >= params.close_loc
            and trend_ok(row, "LONG", params)
        ):
            return "LONG"
        if (
            short_allowed
            and compressed
            and float(row["mid_close"]) < float(row["prior_low_12"])
            and close_loc <= 1.0 - params.close_loc
            and trend_ok(row, "SHORT", params)
        ):
            return "SHORT"

    if params.family == "volume_reversal":
        if (
            long_allowed
            and float(row["move3_atr"]) <= -params.min_move_atr
            and close_loc >= params.close_loc
            and not trend_ok(row, "SHORT", params)
        ):
            return "LONG"
        if (
            short_allowed
            and float(row["move3_atr"]) >= params.min_move_atr
            and close_loc <= 1.0 - params.close_loc
            and not trend_ok(row, "LONG", params)
        ):
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
            structure = min(float(row["mid_low"]), float(row["prior_low_12"]))
            risk = max(entry - structure, params.min_risk_atr * atr, 3.0 * spread)
        else:
            entry = float(entry_row["bid_open"])
            structure = max(float(row["mid_high"]), float(row["prior_high_12"]))
            risk = max(structure - entry, params.min_risk_atr * atr, 3.0 * spread)
        if risk <= 0 or risk > params.max_risk_atr * atr or (spread / risk) > params.max_cost_r:
            index += 1
            continue
        exit_index, exit_price, reason = simulate_exit(rows, entry_index, direction, entry, risk, params.rr, params.time_stop_bars)
        profit = (exit_price - entry) if direction == "LONG" else (entry - exit_price)
        trades.append(
            {
                "symbol": params.symbol,
                "variant": params.name,
                "family": params.family,
                "entry_time": entry_row["timestamp_utc"].isoformat(),
                "entry_date": entry_row["entry_date"],
                "entry_hour": int(entry_row["dubai_hour"]),
                "entry_session": session_bucket(int(entry_row["dubai_hour"])),
                "direction": direction,
                "entry": round(entry, 6),
                "exit_time": rows[exit_index]["timestamp_utc"].isoformat(),
                "exit": round(exit_price, 6),
                "r": round(profit / risk, 4),
                "risk": round(risk, 8),
                "atr14": round(atr, 8),
                "spread": round(spread, 8),
                "cost_r": round(spread / risk, 4),
                "exit_reason": reason,
                "volume_ratio": round(float(row["volume_ratio"]), 4),
                "range_atr": round(float(row["range_atr"]), 4),
                "move3_atr": round(float(row["move3_atr"]), 4),
                "prior_range_12_atr": round(float(row["prior_range_12_atr"]), 4),
                "body_frac": round(float(row["body_frac"]), 4),
                "close_location": round(float(row["close_location"]), 4),
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
    values = [float(row["r"]) for row in trades]
    ordered = [float(row["r"]) for row in sorted(trades, key=lambda item: item["exit_time"])]
    by_day: dict[str, list[float]] = defaultdict(list)
    by_month: dict[str, list[float]] = defaultdict(list)
    by_direction: dict[str, list[float]] = defaultdict(list)
    for row in trades:
        by_day[row["entry_date"]].append(float(row["r"]))
        by_month[row["entry_date"][:7]].append(float(row["r"]))
        by_direction[row["direction"]].append(float(row["r"]))
    start = min(pd.Timestamp(row["entry_time"]).date() for row in trades)
    end = max(pd.Timestamp(row["entry_time"]).date() for row in trades)
    days = market_days(start, end)
    wins = sum(value > 0 for value in values)
    return {
        "name": name,
        "symbol": trades[0]["symbol"],
        "family": trades[0]["family"],
        "trades": len(trades),
        "wins": wins,
        "losses": sum(value < 0 for value in values),
        "win_rate_pct": round(100.0 * wins / len(trades), 2),
        "net_r": round(sum(values), 2),
        "profit_factor_r": profit_factor(values),
        "market_days": days,
        "active_days": len(by_day),
        "trades_per_market_day": round(len(trades) / days, 2),
        "trades_per_active_day": round(len(trades) / len(by_day), 2),
        "three_plus_market_day_pct": round(100.0 * sum(len(day_values) >= 3 for day_values in by_day.values()) / days, 2),
        "positive_months": sum(sum(month_values) > 0 for month_values in by_month.values()),
        "negative_months": sum(sum(month_values) < 0 for month_values in by_month.values()),
        "top100_removed_r": top_removed(values, 100),
        "top200_removed_r": top_removed(values, 200),
        "top300_removed_r": top_removed(values, 300),
        "rolling100": rolling_negative(ordered, 100),
        "rolling250": rolling_negative(ordered, 250),
        "direction": {
            direction: {"trades": len(direction_values), "net_r": round(sum(direction_values), 2), "pf_r": profit_factor(direction_values)}
            for direction, direction_values in sorted(by_direction.items())
        },
    }


def decision(row: dict[str, Any]) -> str:
    if row.get("trades", 0) < 500:
        return "FAIL_SAMPLE"
    if row.get("trades_per_market_day", 0.0) < 3.0:
        return "FAIL_CADENCE"
    if row.get("win_rate_pct", 0.0) < 60.0:
        return "FAIL_WR"
    if (row.get("profit_factor_r") or 0.0) < 1.25:
        return "FAIL_PF"
    if row.get("top200_removed_r", 0.0) <= 0:
        return "FAIL_TOP200"
    if row.get("top300_removed_r", 0.0) <= 0:
        return "REVISE_TOP300"
    if row.get("rolling250", {}).get("negative", 1) > 0:
        return "REVISE_ROLLING250"
    return "VOLUME_EXPANSION_REVIEW_CANDIDATE"


def build_params(symbols: list[str]) -> list[Params]:
    # Keep this first pass intentionally bounded. The goal is to find whether
    # a non-XAU/high-frequency volume mechanism is worth exact MT5 testing,
    # not to do another broad optimizer sweep.
    blocked_sets = {"all": ()}
    rows: list[Params] = []
    for symbol in symbols:
        for family in ("volume_impulse", "compressed_expansion", "volume_reversal"):
            for direction in ("both", "long", "short"):
                for rr in (0.7,):
                    for blocked_name, blocked_hours in blocked_sets.items():
                        for trend in (False, True):
                            name = (
                                f"{symbol}_{family}_{direction}_rr{str(rr).replace('.', 'p')}_"
                                f"{blocked_name}_{'trend' if trend else 'raw'}"
                            )
                            rows.append(
                                Params(
                                    name=name,
                                    symbol=symbol,
                                    family=family,
                                    direction_mode=direction,
                                    rr=rr,
                                    min_volume_ratio=1.25,
                                    min_range_atr=0.35,
                                    max_range_atr=3.5,
                                    min_move_atr=0.65,
                                    min_body=0.30,
                                    close_loc=0.65,
                                    min_compression_atr=1.2,
                                    min_risk_atr=0.60,
                                    max_risk_atr=2.8,
                                    max_cost_r=0.12,
                                    time_stop_bars=10 if rr < 0.8 else 14,
                                    blocked_hours=blocked_hours,
                                    trend_filter=trend,
                                )
                            )
    return rows


def available_symbols() -> list[str]:
    symbols = []
    for symbol_dir in sorted(BARS_ROOT.iterdir()):
        if (symbol_dir / "M5" / f"{symbol_dir.name}_capital_com_M5_20160103_20250701.csv").exists():
            symbols.append(symbol_dir.name)
    return symbols


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload["best_result"]
    lines = [
        "# Multi-Symbol M5 Volume Expansion Screen - 2026-07-03",
        "",
        "Scope: offline bar-level discovery only. No MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Best Result",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision')}` |",
        f"| Symbol | `{best.get('symbol')}` |",
        f"| Variant | `{best.get('name')}` |",
        f"| Trades | {best.get('trades')} |",
        f"| Win rate | {best.get('win_rate_pct')}% |",
        f"| PF R | {best.get('profit_factor_r')} |",
        f"| Net R | {best.get('net_r')} |",
        f"| Trades / market day | {best.get('trades_per_market_day')} |",
        f"| Top200 R | {best.get('top200_removed_r')} |",
        f"| Top300 R | {best.get('top300_removed_r')} |",
        f"| Rolling250 negative | {best.get('rolling250', {}).get('negative')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Symbol | Variant | Trades | WR | PF R | Net R | T/day | Top300 R | Roll250 neg |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_results"][:25], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{symbol}` | `{name}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {top300:.2f} | {roll} |".format(
                rank=index,
                decision=row.get("decision"),
                symbol=row.get("symbol"),
                name=row.get("name"),
                trades=row.get("trades", 0),
                wr=row.get("win_rate_pct", 0.0),
                pf=row.get("profit_factor_r"),
                net=row.get("net_r", 0.0),
                tmd=row.get("trades_per_market_day", 0.0),
                top300=row.get("top300_removed_r", 0.0),
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
            "Any review candidate must be exact-tested in MT5 Strategy Tester before demo use.",
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
    symbols = available_symbols()
    data = {symbol: load_bars(symbol) for symbol in symbols}
    summaries: list[dict[str, Any]] = []
    trades_by_name: dict[str, list[dict[str, Any]]] = {}
    params_list = build_params(symbols)
    print(f"screening {len(params_list)} variants across {', '.join(symbols)}", flush=True)
    for offset, params in enumerate(params_list, start=1):
        if offset == 1 or offset % 10 == 0:
            print(f"variant {offset}/{len(params_list)}: {params.name}", flush=True)
        trades = simulate(data[params.symbol], params)
        summary = summarize(params.name, trades) if trades else {"name": params.name, "symbol": params.symbol, "family": params.family, "trades": 0}
        summary["params"] = asdict(params)
        summary["decision"] = decision(summary)
        summaries.append(summary)
        trades_by_name[params.name] = trades
    summaries.sort(
        key=lambda row: (
            row["decision"].startswith("FAIL"),
            row["decision"].startswith("REVISE"),
            -float(row.get("trades_per_market_day") or 0.0),
            -float(row.get("profit_factor_r") or 0.0),
            -float(row.get("net_r") or 0.0),
        )
    )
    best = summaries[0]
    verdict = (
        "FOUND_VOLUME_EXPANSION_REVIEW_CANDIDATE"
        if str(best.get("decision")).endswith("CANDIDATE")
        else "NO_VOLUME_EXPANSION_CANDIDATE"
    )
    next_action = "port_to_exact_mt5_strategy_tester" if verdict.startswith("FOUND") else "continue_different_entry_family_or_timeframe"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_trades = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_TRADES.csv"
    payload = {
        "status": "PASS_VOLUME_EXPANSION_SCREEN_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_bar_discovery_only_no_runtime_change",
        "symbols": symbols,
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
            "symbol",
            "family",
            "name",
            "trades",
            "win_rate_pct",
            "profit_factor_r",
            "net_r",
            "trades_per_market_day",
            "top100_removed_r",
            "top200_removed_r",
            "top300_removed_r",
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
                "symbol",
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
                "r",
                "risk",
                "atr14",
                "spread",
                "cost_r",
                "exit_reason",
                "volume_ratio",
                "range_atr",
                "move3_atr",
                "prior_range_12_atr",
                "body_frac",
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
                "symbol": best.get("symbol"),
                "variant": best.get("name"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor_r": best.get("profit_factor_r"),
                "net_r": best.get("net_r"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top300_removed_r": best.get("top300_removed_r"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
