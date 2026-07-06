from __future__ import annotations

import argparse
import csv
import json
import lzma
import math
import struct
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_M5_DIR = ROOT / "forex-research" / "data" / "alternate_history" / "dukascopy" / "USDJPY" / "M5" / "raw"
TICK_CACHE_DIR = ROOT / "forex-research" / "data" / "alternate_history" / "dukascopy" / "USDJPY" / "tick_bidask" / "raw"
OUT_DIR = ROOT / "forex-research" / "outputs" / "reports" / "mt5_backtests" / "session_breakout_scout"

ATR_PERIOD = 14
LOTS = 0.01
CONTRACT_SIZE = 100000.0
POINT = 0.001
PIP = 0.01


@dataclass(frozen=True)
class Tick:
    timestamp: pd.Timestamp
    bid: float
    ask: float


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
    entry_bid: float
    entry_ask: float
    exit_bid: float
    exit_ask: float
    spread_points_entry: float
    exit_reason: str
    pnl: float
    downloaded_hours: int


def load_m5_bid() -> pd.DataFrame:
    files = sorted(path for path in RAW_M5_DIR.glob("USDJPY_dukascopy_M5_bid_*.csv.csv") if path.stat().st_size > 0)
    if not files:
        raise RuntimeError(f"No Dukascopy M5 bid files found in {RAW_M5_DIR}")
    frames = []
    for path in files:
        frame = pd.read_csv(path)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        frame["source_file"] = path.name
        frames.append(frame)
    m5 = pd.concat(frames, ignore_index=True)
    m5 = m5.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)
    return m5.set_index("timestamp")[["open", "high", "low", "close"]]


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


def hour_floor(value: pd.Timestamp) -> pd.Timestamp:
    return value.floor("h")


def tick_cache_path(hour: pd.Timestamp) -> Path:
    return TICK_CACHE_DIR / f"USDJPY_{hour.strftime('%Y%m%d_%H')}_ticks.bi5"


def dukascopy_tick_url(hour: pd.Timestamp) -> str:
    # Dukascopy datafeed months are zero-indexed.
    return (
        "https://datafeed.dukascopy.com/datafeed/USDJPY/"
        f"{hour.year:04d}/{hour.month - 1:02d}/{hour.day:02d}/{hour.hour:02d}h_ticks.bi5"
    )


def download_hour(hour: pd.Timestamp, retries: int = 8) -> bytes:
    TICK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = tick_cache_path(hour)
    if path.exists():
        return path.read_bytes()

    url = dukascopy_tick_url(hour)
    request = urllib.request.Request(url, headers={"User-Agent": "forex-research-lane/1.0"})
    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
            if data:
                path.write_bytes(data)
                time.sleep(0.03)
            return data
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                path.write_bytes(b"")
                return b""
            last_error = exc
        except Exception as exc:  # pragma: no cover - network exception details vary.
            last_error = exc
        time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"Failed to download {url}: {last_error}")


@lru_cache(maxsize=4096)
def load_hour_ticks(hour_iso: str) -> tuple[Tick, ...]:
    hour = pd.Timestamp(hour_iso)
    compressed = download_hour(hour)
    if not compressed:
        return ()
    raw = lzma.decompress(compressed)
    ticks: list[Tick] = []
    base = hour.tz_convert("UTC") if hour.tzinfo is not None else hour.tz_localize("UTC")
    for offset in range(0, len(raw) - len(raw) % 20, 20):
        ms, ask_raw, bid_raw, _ask_vol, _bid_vol = struct.unpack(">IIIff", raw[offset : offset + 20])
        timestamp = base + pd.Timedelta(milliseconds=int(ms))
        ask = round(ask_raw / 1000.0, 3)
        bid = round(bid_raw / 1000.0, 3)
        if bid <= 0.0 or ask <= 0.0:
            continue
        ticks.append(Tick(timestamp=timestamp, bid=bid, ask=ask))
    return tuple(ticks)


def iter_ticks(start: pd.Timestamp, end: pd.Timestamp) -> Iterator[Tick]:
    hour = hour_floor(start)
    while hour <= end:
        for tick in load_hour_ticks(hour.isoformat()):
            if tick.timestamp >= start and tick.timestamp <= end:
                yield tick
        hour += pd.Timedelta(hours=1)


def first_tick_at_or_after(start: pd.Timestamp, end: pd.Timestamp) -> Tick | None:
    for tick in iter_ticks(start, end):
        return tick
    return None


def usd_pnl(direction: str, entry: float, exit_price: float) -> float:
    sign = 1.0 if direction == "LONG" else -1.0
    return sign * (exit_price - entry) * LOTS * CONTRACT_SIZE / exit_price


def pip_value(exit_price: float) -> float:
    return PIP * LOTS * CONTRACT_SIZE / exit_price


def simulate_tick_trade(
    *,
    entry_time: pd.Timestamp,
    data_end: pd.Timestamp,
    direction: str,
    atr: float,
    range_high: float,
    range_low: float,
) -> Trade | None:
    entry_tick = first_tick_at_or_after(entry_time, data_end)
    if entry_tick is None:
        return None

    session_range = range_high - range_low
    stop_distance = max(atr, session_range, 30 * POINT)
    if direction == "LONG":
        entry = entry_tick.ask
        sl = round(min(range_low, entry - stop_distance), 3)
        stop_distance = entry - sl
        stop_points = stop_distance / POINT
        if stop_points > 900:
            return None
        tp = round(entry + stop_distance, 3)
    else:
        entry = entry_tick.bid
        sl = round(max(range_high, entry + stop_distance), 3)
        stop_distance = sl - entry
        stop_points = stop_distance / POINT
        if stop_points > 900:
            return None
        tp = round(entry - stop_distance, 3)

    downloaded_hours_before = load_hour_ticks.cache_info().misses
    last_tick = entry_tick
    for tick in iter_ticks(entry_tick.timestamp, data_end):
        last_tick = tick
        if direction == "LONG":
            exit_stream_price = tick.bid
            if exit_stream_price <= sl:
                return make_trade(entry_tick, tick, direction, entry, sl, tp, stop_points, sl, "sl", downloaded_hours_before)
            if exit_stream_price >= tp:
                return make_trade(entry_tick, tick, direction, entry, sl, tp, stop_points, tp, "tp", downloaded_hours_before)
        else:
            exit_stream_price = tick.ask
            if exit_stream_price >= sl:
                return make_trade(entry_tick, tick, direction, entry, sl, tp, stop_points, sl, "sl", downloaded_hours_before)
            if exit_stream_price <= tp:
                return make_trade(entry_tick, tick, direction, entry, sl, tp, stop_points, tp, "tp", downloaded_hours_before)

    exit_price = last_tick.bid if direction == "LONG" else last_tick.ask
    return make_trade(entry_tick, last_tick, direction, entry, sl, tp, stop_points, exit_price, "open_at_data_end", downloaded_hours_before)


def make_trade(
    entry_tick: Tick,
    exit_tick: Tick,
    direction: str,
    entry: float,
    sl: float,
    tp: float,
    stop_points: float,
    exit_price: float,
    exit_reason: str,
    downloaded_hours_before: int,
) -> Trade:
    return Trade(
        entry_time=entry_tick.timestamp,
        exit_time=exit_tick.timestamp,
        direction=direction,
        entry_price=entry,
        exit_price=exit_price,
        sl=sl,
        tp=tp,
        stop_points=stop_points,
        entry_bid=entry_tick.bid,
        entry_ask=entry_tick.ask,
        exit_bid=exit_tick.bid,
        exit_ask=exit_tick.ask,
        spread_points_entry=(entry_tick.ask - entry_tick.bid) / POINT,
        exit_reason=exit_reason,
        pnl=usd_pnl(direction, entry, exit_price),
        downloaded_hours=load_hour_ticks.cache_info().misses - downloaded_hours_before,
    )


def run_replay(start: pd.Timestamp, end: pd.Timestamp) -> tuple[list[Trade], dict]:
    m5 = load_m5_bid()
    m15 = resample_ohlc(m5, "15min")
    d1 = resample_ohlc(m5, "1D")
    m15["atr"] = wilder_atr(m15, ATR_PERIOD)
    d1["atr"] = wilder_atr(d1, ATR_PERIOD)

    data_end = min(end, m5.index[-1])
    trades: list[Trade] = []
    open_until = pd.Timestamp.min.tz_localize("UTC")
    daily_counts: dict[str, int] = {}
    skipped_no_tick = 0

    for bar_time, bar in m15.iterrows():
        entry_time = bar_time + pd.Timedelta(minutes=15)
        if entry_time < start or entry_time > data_end:
            continue
        if pd.isna(bar["atr"]) or bar_time < open_until:
            continue
        if not (8 <= bar_time.hour < 12):
            continue

        day_start = bar_time.floor("D")
        day_key = day_start.strftime("%Y-%m-%d")
        if daily_counts.get(day_key, 0) >= 2:
            continue

        prev_day = day_start - pd.Timedelta(days=1)
        if prev_day not in d1.index or pd.isna(d1.loc[prev_day, "atr"]) or d1.loc[prev_day, "atr"] <= 0:
            continue

        range_bars = m15.loc[(m15.index >= day_start + pd.Timedelta(hours=6)) & (m15.index < day_start + pd.Timedelta(hours=8))]
        if len(range_bars) < 8:
            continue
        range_high = float(range_bars["high"].max())
        range_low = float(range_bars["low"].min())
        session_range = range_high - range_low
        atr = float(bar["atr"])
        range_atr = session_range / atr if atr > 0.0 else 0.0
        if range_atr < 0.45 or range_atr > 3.20:
            continue
        if session_range / float(d1.loc[prev_day, "atr"]) < 0.20:
            continue

        bar_range = max(float(bar["high"]) - float(bar["low"]), POINT)
        body_fraction = abs(float(bar["close"]) - float(bar["open"])) / bar_range
        close_location = (float(bar["close"]) - float(bar["low"])) / bar_range
        if body_fraction < 0.30:
            continue

        buffer = 0.05 * atr
        direction = ""
        if float(bar["close"]) > range_high + buffer and close_location >= 0.65:
            direction = "LONG"
        elif float(bar["close"]) < range_low - buffer and close_location <= 0.35:
            direction = "SHORT"
        if not direction:
            continue

        trade = simulate_tick_trade(
            entry_time=entry_time,
            data_end=data_end,
            direction=direction,
            atr=atr,
            range_high=range_high,
            range_low=range_low,
        )
        if trade is None:
            skipped_no_tick += 1
            continue
        trades.append(trade)
        open_until = trade.exit_time
        daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

    meta = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "m5_bid_rows": int(len(m5)),
        "m5_bid_start": m5.index[0].isoformat(),
        "m5_bid_end": m5.index[-1].isoformat(),
        "requested_start": start.isoformat(),
        "requested_end": end.isoformat(),
        "effective_end": data_end.isoformat(),
        "tick_cache_dir": str(TICK_CACHE_DIR.relative_to(ROOT)).replace("\\", "/"),
        "tick_hours_downloaded_or_loaded": load_hour_ticks.cache_info().misses,
        "skipped_no_tick": skipped_no_tick,
        "time_alignment": "Dukascopy UTC used directly, matching the prior MT5 price-probe alignment.",
        "execution_model": "Signals from Dukascopy bid M5-derived M15/D1 bars; buy entry at ask and buy exits on bid; sell entry at bid and sell exits on ask.",
        "limitations": [
            "Direct Dukascopy tick replay, not MT5 Strategy Tester custom-symbol replay.",
            "No MT5 broker commission/swap model.",
            "No parameter, threshold, direction, hour, RR, or session changes from frozen watchlist-v1 rule.",
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


def grouped(trades: list[Trade], key_fn) -> dict:
    buckets: dict[str, list[Trade]] = {}
    for trade in trades:
        buckets.setdefault(key_fn(trade), []).append(trade)
    return {key: metrics(rows) for key, rows in sorted(buckets.items())}


def top_removed(trades: list[Trade], count: int) -> dict | None:
    if len(trades) <= count:
        return None
    kept = sorted(trades, key=lambda t: t.pnl, reverse=True)[count:]
    return metrics(kept)


def write_trades(path: Path, trades: list[Trade]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "entry_time_utc",
                "exit_time_utc",
                "direction",
                "entry_price",
                "exit_price",
                "entry_bid",
                "entry_ask",
                "exit_bid",
                "exit_ask",
                "spread_points_entry",
                "sl",
                "tp",
                "stop_points",
                "exit_reason",
                "manual_pnl_usd",
                "downloaded_hours",
            ],
        )
        writer.writeheader()
        for trade in trades:
            writer.writerow(
                {
                    "entry_time_utc": trade.entry_time.isoformat(),
                    "exit_time_utc": trade.exit_time.isoformat(),
                    "direction": trade.direction,
                    "entry_price": f"{trade.entry_price:.3f}",
                    "exit_price": f"{trade.exit_price:.3f}",
                    "entry_bid": f"{trade.entry_bid:.3f}",
                    "entry_ask": f"{trade.entry_ask:.3f}",
                    "exit_bid": f"{trade.exit_bid:.3f}",
                    "exit_ask": f"{trade.exit_ask:.3f}",
                    "spread_points_entry": f"{trade.spread_points_entry:.1f}",
                    "sl": f"{trade.sl:.3f}",
                    "tp": f"{trade.tp:.3f}",
                    "stop_points": f"{trade.stop_points:.2f}",
                    "exit_reason": trade.exit_reason,
                    "manual_pnl_usd": f"{trade.pnl:.6f}",
                    "downloaded_hours": trade.downloaded_hours,
                }
            )


def money(value: float) -> str:
    return f"${value:,.2f}"


def metric_row(label: str, row: dict) -> str:
    return f"| {label} | {row['trades']} | {row['win_rate_pct']:.2f}% | {money(row['pnl'])} | {row['profit_factor']:.4f} |"


def render_markdown(payload: dict) -> str:
    lines = [
        "# Forex Dukascopy USDJPY London120 M15 D1 ATR20 Direct Tick Replay",
        "",
        "Date: 2026-07-04",
        f"Status: **{payload['status']}**",
        "",
        "This is a direct Dukascopy bid/ask tick replay of the frozen MT5 watchlist-v1 rule. It does not touch MT5 runtime.",
        "",
        "## Scope",
        "",
        f"- Window: `{payload['meta']['requested_start']}` through `{payload['meta']['requested_end']}`",
        "- Symbol: `USDJPY`",
        "- Rule: `london120_break_m15_d1atr20_guard`",
        "- Signal bars: Dukascopy bid ticks aggregated to M5, then M15/D1.",
        "- Execution: buy at ask and exit on bid; sell at bid and exit on ask.",
        "",
        "## Summary",
        "",
        "| Window | Trades | WR | Net | PF |",
        "| --- | ---: | ---: | ---: | ---: |",
        metric_row("direct_tick_bidask", payload["summary"]),
        metric_row("+0.5 pip extra stress", payload["stress_plus_0p5_pip"]),
        "",
        "## Direction",
        "",
        "| Direction | Trades | WR | Net | PF |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, row in payload["direction"].items():
        lines.append(metric_row(name, row))
    lines.extend(["", "## Yearly", "", "| Year | Trades | WR | Net | PF |", "| --- | ---: | ---: | ---: | ---: |"])
    for name, row in payload["yearly"].items():
        lines.append(metric_row(name, row))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "## Boundary",
            "",
            "- Forex only.",
            "- No MT5 terminal, chart, profile, preset, order, position, or XAU EA was touched.",
            "- No parameter, threshold, hour, direction, RR, or session change was made.",
            "- This is stricter than the earlier bid-M5 OHLC replay because it uses actual Dukascopy bid/ask ticks for entry and exit streams.",
            "",
            "Artifacts:",
            "",
            f"- Trades CSV: `{payload['artifacts']['trades_csv']}`",
            f"- JSON: `{payload['artifacts']['report_json']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay frozen USDJPY London120 D1 ATR20 rule on direct Dukascopy bid/ask ticks.")
    parser.add_argument("--from-date", default="2025-01-01")
    parser.add_argument("--to-date", default="2026-06-27")
    parser.add_argument("--tag", default="RECENT_2025_2026")
    args = parser.parse_args()

    start = pd.Timestamp(args.from_date, tz="UTC")
    end = pd.Timestamp(args.to_date, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)
    tag = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in args.tag.upper())
    report_json = OUT_DIR / f"FOREX_DUKASCOPY_USDJPY_LONDON120_M15_D1ATR20_DIRECT_TICK_BIDASK_REPLAY_{tag}_2026_07_04.json"
    report_md = report_json.with_suffix(".md")
    trades_csv = OUT_DIR / f"FOREX_DUKASCOPY_USDJPY_LONDON120_M15_D1ATR20_DIRECT_TICK_BIDASK_TRADES_{tag}_2026_07_04.csv"

    trades, meta = run_replay(start, end)
    write_trades(trades_csv, trades)
    summary = metrics(trades)
    payload = {
        "status": "DUKASCOPY_DIRECT_TICK_BIDASK_REPLAY_RESEARCH_ONLY",
        "candidate": "USDJPY london120_break_m15_d1atr20_guard",
        "meta": meta,
        "summary": summary,
        "stress_plus_0p5_pip": metrics(trades, 0.5),
        "stress_plus_1p0_pip": metrics(trades, 1.0),
        "direction": grouped(trades, lambda t: t.direction),
        "yearly": grouped(trades, lambda t: str(t.entry_time.year) if t.entry_time.year < 2026 else "2026_partial"),
        "top_winner_removal": {f"top_{n}_removed": top_removed(trades, n) for n in (5, 10, 20, 30)},
        "interpretation": (
            "Direct Dukascopy bid/ask tick replay remains research-only. "
            "If the recent slice is negative or materially weak here, it reinforces the current no-demo decision; "
            "if positive, it still requires reviewer acceptance because this is not an MT5 custom-symbol tester run."
        ),
        "artifacts": {
            "trades_csv": str(trades_csv.relative_to(ROOT)).replace("\\", "/"),
            "report_json": str(report_json.relative_to(ROOT)).replace("\\", "/"),
            "report_md": str(report_md.relative_to(ROOT)).replace("\\", "/"),
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "summary": summary, "stress_plus_0p5_pip": payload["stress_plus_0p5_pip"], "report_md": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
