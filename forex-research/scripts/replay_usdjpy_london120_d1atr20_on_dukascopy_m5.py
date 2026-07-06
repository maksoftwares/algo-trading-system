from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "forex-research" / "data" / "alternate_history" / "dukascopy" / "USDJPY" / "M5" / "raw"
OUT_DIR = ROOT / "forex-research" / "outputs" / "reports" / "mt5_backtests" / "session_breakout_scout"
TRADES_CSV = OUT_DIR / "FOREX_DUKASCOPY_USDJPY_LONDON120_M15_D1ATR20_ALT_HISTORY_TRADES_2026_07_04.csv"
REPORT_JSON = OUT_DIR / "FOREX_DUKASCOPY_USDJPY_LONDON120_M15_D1ATR20_ALT_HISTORY_REPLAY_2026_07_04.json"
REPORT_MD = OUT_DIR / "FOREX_DUKASCOPY_USDJPY_LONDON120_M15_D1ATR20_ALT_HISTORY_REPLAY_2026_07_04.md"

ATR_PERIOD = 14
LOTS = 0.01
CONTRACT_SIZE = 100000.0
POINT = 0.001
PIP = 0.01


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str
    entry_price: float
    exit_price: float
    sl: float
    tp: float
    stop_points: float
    exit_reason: str
    pnl: float


def load_m5() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("USDJPY_dukascopy_M5_bid_*.csv.csv"))
    if not files:
        raise RuntimeError(f"No Dukascopy M5 files found in {RAW_DIR}")
    frames = []
    for path in files:
        frame = pd.read_csv(path)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        frame["source_file"] = path.name
        frames.append(frame)
    m5 = pd.concat(frames, ignore_index=True)
    m5 = m5.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)
    m5 = m5.set_index("timestamp")
    return m5[["open", "high", "low", "close"]]


def resample_ohlc(m5: pd.DataFrame, rule: str) -> pd.DataFrame:
    out = m5.resample(rule, label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
    )
    return out.dropna()


def wilder_atr(bars: pd.DataFrame, period: int) -> pd.Series:
    prev_close = bars["close"].shift(1)
    tr = pd.concat(
        [
            bars["high"] - bars["low"],
            (bars["high"] - prev_close).abs(),
            (bars["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    values = [math.nan] * len(tr)
    tr_values = tr.to_list()
    if len(tr_values) >= period:
        values[period - 1] = sum(tr_values[:period]) / period
        for i in range(period, len(tr_values)):
            values[i] = (values[i - 1] * (period - 1) + tr_values[i]) / period
    return pd.Series(values, index=bars.index)


def usd_pnl(direction: str, entry: float, exit_price: float) -> float:
    sign = 1.0 if direction == "LONG" else -1.0
    return sign * (exit_price - entry) * LOTS * CONTRACT_SIZE / exit_price


def pip_value(exit_price: float) -> float:
    return PIP * LOTS * CONTRACT_SIZE / exit_price


def simulate_exit(m5: pd.DataFrame, entry_time: pd.Timestamp, direction: str, entry: float, sl: float, tp: float) -> tuple[pd.Timestamp, float, str]:
    future = m5.loc[m5.index >= entry_time]
    for t, row in future.iterrows():
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        if direction == "LONG":
            hit_sl = low <= sl
            hit_tp = high >= tp
            if hit_sl and hit_tp:
                return t, sl, "sl_adverse_first"
            if hit_sl:
                return t, sl, "sl"
            if hit_tp:
                return t, tp, "tp"
        else:
            hit_sl = high >= sl
            hit_tp = low <= tp
            if hit_sl and hit_tp:
                return t, sl, "sl_adverse_first"
            if hit_sl:
                return t, sl, "sl"
            if hit_tp:
                return t, tp, "tp"
        last_t = t
        last_close = close
    return last_t, last_close, "open_at_data_end"


def run_replay() -> tuple[list[Trade], dict]:
    m5 = load_m5()
    m15 = resample_ohlc(m5, "15min")
    d1 = resample_ohlc(m5, "1D")
    m15["atr"] = wilder_atr(m15, ATR_PERIOD)
    d1["atr"] = wilder_atr(d1, ATR_PERIOD)

    trades: list[Trade] = []
    open_until = pd.Timestamp.min.tz_localize("UTC")
    daily_counts: dict[str, int] = {}

    for bar_time, bar in m15.iterrows():
        if pd.isna(bar["atr"]) or bar_time < open_until:
            continue
        if not (bar_time.hour >= 8 and bar_time.hour < 12):
            continue

        day_start = bar_time.floor("D")
        day_key = day_start.strftime("%Y-%m-%d")
        if daily_counts.get(day_key, 0) >= 2:
            continue

        prev_day = day_start - pd.Timedelta(days=1)
        if prev_day not in d1.index or pd.isna(d1.loc[prev_day, "atr"]) or d1.loc[prev_day, "atr"] <= 0:
            continue

        range_start = day_start + pd.Timedelta(hours=6)
        range_end = day_start + pd.Timedelta(hours=8)
        range_bars = m15.loc[(m15.index >= range_start) & (m15.index < range_end)]
        if len(range_bars) < 8:
            continue
        range_high = float(range_bars["high"].max())
        range_low = float(range_bars["low"].min())
        session_range = range_high - range_low
        atr = float(bar["atr"])
        range_atr = session_range / atr if atr > 0 else 0.0
        if range_atr < 0.45 or range_atr > 3.20:
            continue
        if session_range / float(d1.loc[prev_day, "atr"]) < 0.20:
            continue

        bar_range = max(float(bar["high"]) - float(bar["low"]), POINT)
        body_fraction = abs(float(bar["close"]) - float(bar["open"])) / bar_range
        close_location = (float(bar["close"]) - float(bar["low"])) / bar_range
        if body_fraction < 0.30:
            continue

        direction = ""
        buffer = 0.05 * atr
        if float(bar["close"]) > range_high + buffer and close_location >= 0.65:
            direction = "LONG"
        elif float(bar["close"]) < range_low - buffer and close_location <= 0.35:
            direction = "SHORT"
        if not direction:
            continue

        entry_time = bar_time + pd.Timedelta(minutes=15)
        if entry_time not in m5.index:
            continue
        entry = float(m5.loc[entry_time, "open"])
        stop_distance = max(atr, session_range, 30 * POINT)
        stop_points = stop_distance / POINT
        if stop_points > 900:
            continue
        if direction == "LONG":
            sl = min(range_low, entry - stop_distance)
            stop_distance = entry - sl
            tp = entry + stop_distance
        else:
            sl = max(range_high, entry + stop_distance)
            stop_distance = sl - entry
            tp = entry - stop_distance
        stop_points = stop_distance / POINT
        if stop_points > 900:
            continue

        exit_time, exit_price, exit_reason = simulate_exit(m5, entry_time, direction, entry, sl, tp)
        trade = Trade(
            entry_time=entry_time,
            exit_time=exit_time,
            direction=direction,
            entry_price=entry,
            exit_price=exit_price,
            sl=sl,
            tp=tp,
            stop_points=stop_points,
            exit_reason=exit_reason,
            pnl=usd_pnl(direction, entry, exit_price),
        )
        trades.append(trade)
        open_until = exit_time
        daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

    meta = {
        "m5_rows": int(len(m5)),
        "m5_start": m5.index[0].isoformat(),
        "m5_end": m5.index[-1].isoformat(),
        "m15_rows": int(len(m15)),
        "d1_rows": int(len(d1)),
        "time_alignment": "Dukascopy UTC used directly; MT5 entry-price probes matched best at broker-server offset 0.",
        "limitations": [
            "Bid-only OHLC replay, not MT5 tick replay.",
            "No ask-side spread in raw P&L; report includes round-trip pip haircuts.",
            "M5 adverse-first exit resolution approximates tick path.",
        ],
    }
    return trades, meta


def metrics(trades: list[Trade], extra_pips: float = 0.0) -> dict:
    values = [t.pnl - extra_pips * pip_value(t.exit_price) for t in trades]
    wins = [v for v in values if v > 0]
    losses = [v for v in values if v < 0]
    gp = sum(wins)
    gl = -sum(losses)
    n = len(values)
    return {
        "trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round((len(wins) / n * 100.0) if n else 0.0, 2),
        "pnl": round(sum(values), 2),
        "gross_profit": round(gp, 2),
        "gross_loss": round(gl, 2),
        "profit_factor": round((gp / gl) if gl else math.inf, 4),
        "avg_pnl": round((sum(values) / n) if n else 0.0, 4),
        "extra_round_trip_pips": extra_pips,
    }


def filter_trades(trades: list[Trade], start: pd.Timestamp, end: pd.Timestamp) -> list[Trade]:
    return [t for t in trades if start <= t.entry_time <= end]


def grouped(trades: list[Trade], key_fn) -> dict:
    buckets: dict[str, list[Trade]] = {}
    for trade in trades:
        buckets.setdefault(key_fn(trade), []).append(trade)
    return {key: metrics(rows) for key, rows in sorted(buckets.items())}


def rolling_worst(trades: list[Trade], size: int) -> dict | None:
    if len(trades) < size:
        return None
    worst = None
    ordered = sorted(trades, key=lambda t: (t.entry_time, t.exit_time))
    for i in range(0, len(ordered) - size + 1):
        chunk = ordered[i : i + size]
        item = metrics(chunk)
        item["start_entry"] = chunk[0].entry_time.isoformat()
        item["end_exit"] = chunk[-1].exit_time.isoformat()
        if worst is None or item["pnl"] < worst["pnl"]:
            worst = item
    return worst


def top_removed(trades: list[Trade], count: int) -> dict | None:
    if len(trades) <= count:
        return None
    kept = sorted(trades, key=lambda t: t.pnl, reverse=True)[count:]
    return metrics(kept)


def write_trades(trades: list[Trade]) -> None:
    TRADES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with TRADES_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "entry_time_utc",
                "exit_time_utc",
                "direction",
                "entry_price",
                "exit_price",
                "sl",
                "tp",
                "stop_points",
                "exit_reason",
                "manual_pnl_usd",
            ],
        )
        writer.writeheader()
        for trade in trades:
            writer.writerow(
                {
                    "entry_time_utc": trade.entry_time.isoformat(),
                    "exit_time_utc": trade.exit_time.isoformat(),
                    "direction": trade.direction,
                    "entry_price": f"{trade.entry_price:.5f}",
                    "exit_price": f"{trade.exit_price:.5f}",
                    "sl": f"{trade.sl:.5f}",
                    "tp": f"{trade.tp:.5f}",
                    "stop_points": f"{trade.stop_points:.2f}",
                    "exit_reason": trade.exit_reason,
                    "manual_pnl_usd": f"{trade.pnl:.6f}",
                }
            )


def money(value: float) -> str:
    return f"${value:,.2f}"


def metric_row(label: str, row: dict) -> str:
    return f"| {label} | {row['trades']} | {row['win_rate_pct']:.2f}% | {money(row['pnl'])} | {row['profit_factor']:.4f} |"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trades, meta = run_replay()
    write_trades(trades)
    latest = max(t.entry_time for t in trades)
    trailing_start = latest - pd.Timedelta(days=365) + pd.Timedelta(days=1)
    windows = {
        "full_available_dukascopy": trades,
        "from_2020": filter_trades(trades, pd.Timestamp("2020-01-01", tz="UTC"), latest),
        "from_2022": filter_trades(trades, pd.Timestamp("2022-01-01", tz="UTC"), latest),
        "recent_2025_2026": filter_trades(trades, pd.Timestamp("2025-01-01", tz="UTC"), latest),
        f"trailing_12m_{trailing_start.date()}_to_{latest.date()}": filter_trades(trades, trailing_start, latest),
    }
    stress = {name: [metrics(rows, pips) for pips in (0.0, 0.5, 1.0)] for name, rows in windows.items()}
    payload = {
        "status": "DUKASCOPY_BID_M5_ALT_HISTORY_REPLAY_RESEARCH_ONLY",
        "candidate": "USDJPY london120_break_m15 D1 ATR20 range-quality guard",
        "meta": meta,
        "summary": {name: metrics(rows) for name, rows in windows.items()},
        "slippage_stress": stress,
        "yearly": grouped(trades, lambda t: str(t.entry_time.year) if t.entry_time.year < 2026 else "2026_partial"),
        "direction": grouped(trades, lambda t: t.direction),
        "rolling": {f"worst_{n}": rolling_worst(trades, n) for n in (50, 100, 150, 250, 400)},
        "top_winner_removal": {f"top_{n}_removed": top_removed(trades, n) for n in (10, 20, 30, 50)},
        "artifacts": {
            "trades_csv": str(TRADES_CSV.relative_to(ROOT)).replace("\\", "/"),
            "report_json": str(REPORT_JSON.relative_to(ROOT)).replace("\\", "/"),
            "report_md": str(REPORT_MD.relative_to(ROOT)).replace("\\", "/"),
        },
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Forex Dukascopy USDJPY London120 M15 D1 ATR20 Alternate-History Replay",
        "",
        "Date: 2026-07-04",
        "Status: **DUKASCOPY_BID_M5_ALT_HISTORY_REPLAY_RESEARCH_ONLY**",
        "",
        "This is a public Dukascopy M5 bid-OHLC replay of the frozen MT5 watchlist-v1 rule. It is not an MT5 tick replay.",
        "",
        "## Data",
        "",
        f"- M5 rows: `{meta['m5_rows']}`",
        f"- Coverage: `{meta['m5_start']}` through `{meta['m5_end']}`",
        "- Time alignment: Dukascopy UTC used directly; MT5 entry-price probes matched best at broker-server offset `0`.",
        "- Limitation: bid-only OHLC; spread is handled with explicit round-trip pip haircuts.",
        "",
        "## Summary",
        "",
        "| Window | Trades | WR | Net | PF |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, row in payload["summary"].items():
        lines.append(metric_row(name, row))
    lines.extend(["", "## +0.5 Pip Round-Trip Stress", "", "| Window | Trades | WR | Net | PF |", "| --- | ---: | ---: | ---: | ---: |"])
    for name, rows in stress.items():
        lines.append(metric_row(name, rows[1]))
    lines.extend(["", "## Yearly", "", "| Year | Trades | WR | Net | PF |", "| --- | ---: | ---: | ---: | ---: |"])
    for name, row in payload["yearly"].items():
        lines.append(metric_row(name, row))
    lines.extend(["", "## Direction", "", "| Direction | Trades | WR | Net | PF |", "| --- | ---: | ---: | ---: | ---: |"])
    for name, row in payload["direction"].items():
        lines.append(metric_row(name, row))
    lines.extend(["", "## Robustness Flags", ""])
    lines.append("- This replay passes as alternate-price-history evidence only if the reviewer accepts bid-M5 OHLC plus explicit cost haircuts as sufficient.")
    lines.append("- It does not replace exact MT5 tester validation or ask/tick-level Dukascopy validation.")
    lines.append("- No parameters were changed from the predeclared D1 ATR20 watchlist-v1 rule.")
    lines.extend(["", "Artifacts:", "", f"- Trades: `{payload['artifacts']['trades_csv']}`", f"- JSON: `{payload['artifacts']['report_json']}`"])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "summary": payload["summary"], "report_md": str(REPORT_MD)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
