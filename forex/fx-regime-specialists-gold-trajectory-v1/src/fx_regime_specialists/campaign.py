from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


UTC = "UTC"
PIP_SIZE = {"EURUSD": 0.0001, "GBPUSD": 0.0001, "USDJPY": 0.01}
SPECIALIST_NAMES = {
    "r1_usd_trend_synchronization": "R1 USD trend synchronization",
    "r2_crossasset_compression_release": "R2 cross-asset compression release",
}
CACHE_SCHEMA_VERSION = "v2_source_rounded"


@dataclass(frozen=True)
class Paths:
    package_root: Path
    output_root: Path
    cache_root: Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_preregistration(package_root: Path) -> dict[str, str]:
    lock_path = package_root / "FOREX_REGIME_SPECIALIST_CAMPAIGN_PREREG_2026_07_27.sha256.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("locked_before_outcome_inspection") is not True:
        raise RuntimeError("Preregistration lock does not assert pre-outcome locking")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(package_root / relative)
        if actual != expected:
            raise RuntimeError(f"Preregistration hash mismatch: {relative}")
        checked[relative] = actual
    return checked


def _decode_hour_bar(path: Path) -> dict[str, Any] | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    if any(key not in payload for key in ("timestamp", "multiplier", "bid", "ask", *arrays)):
        raise ValueError(f"Malformed raw response: {path}")
    lengths = {len(payload[key]) for key in arrays}
    if len(lengths) != 1:
        raise ValueError(f"Inconsistent tick arrays: {path}")
    count = len(payload["times"])
    if count == 0:
        return None
    if payload["bid"] is None or payload["ask"] is None:
        raise ValueError(f"Nonempty response has null base price: {path}")
    multiplier = float(payload["multiplier"])
    bids = float(payload["bid"]) + np.cumsum(np.asarray(payload["bids"], dtype=np.float64)) * multiplier
    asks = float(payload["ask"]) + np.cumsum(np.asarray(payload["asks"], dtype=np.float64)) * multiplier
    scale = max(0, int(round(-math.log10(multiplier))))
    factor = 10**scale
    bids = np.floor(bids * factor + 0.5 + 1e-9) / factor
    asks = np.floor(asks * factor + 0.5 + 1e-9) / factor
    if np.any(asks < bids) or np.any(bids <= 0):
        raise ValueError(f"Invalid decoded price: {path}")
    mid = (bids + asks) / 2.0
    return {
        "timestamp_ms": int(payload["timestamp"]),
        "open": float(mid[0]),
        "high": float(mid.max()),
        "low": float(mid.min()),
        "close": float(mid[-1]),
        "bid_open": float(bids[0]),
        "bid_high": float(bids.max()),
        "bid_low": float(bids.min()),
        "bid_close": float(bids[-1]),
        "ask_open": float(asks[0]),
        "ask_high": float(asks.max()),
        "ask_low": float(asks.min()),
        "ask_close": float(asks[-1]),
        "tick_count": count,
    }


def load_context_h1(
    raw_root: Path,
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cache_root: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    cache_root.mkdir(parents=True, exist_ok=True)
    cache_path = cache_root / f"{symbol}_H1_MID_{CACHE_SCHEMA_VERSION}.parquet"
    manifest_path = cache_root / f"{symbol}_H1_MID_{CACHE_SCHEMA_VERSION}.manifest.json"
    if cache_path.exists() and manifest_path.exists():
        frame = pd.read_parquet(cache_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return _timestamp_index(frame), manifest

    symbol_root = raw_root / symbol
    rows: list[dict[str, Any]] = []
    source_digest = hashlib.sha256()
    files_seen = 0
    empty_hours = 0
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    for path in sorted(symbol_root.glob("year=*/month=*/*.json")):
        stamp_text = path.stem
        if len(stamp_text) != 10 or not stamp_text.isdigit():
            continue
        hour = pd.to_datetime(stamp_text, format="%Y%m%d%H", utc=True)
        hour_ms = int(hour.timestamp() * 1000)
        if hour_ms < start_ms or hour_ms > end_ms:
            continue
        raw = path.read_bytes()
        source_digest.update(path.relative_to(raw_root).as_posix().encode("utf-8"))
        source_digest.update(hashlib.sha256(raw).digest())
        files_seen += 1
        bar = _decode_hour_bar(path)
        if bar is None:
            empty_hours += 1
        else:
            rows.append(bar)
    if not rows:
        raise RuntimeError(f"No populated raw context hours for {symbol}")
    frame = _timestamp_index(pd.DataFrame(rows).sort_values("timestamp_ms"))
    frame.reset_index().to_parquet(cache_path, index=False, compression="zstd")
    manifest = {
        "symbol": symbol,
        "source_root": str(symbol_root),
        "source_chain_sha256": source_digest.hexdigest(),
        "files_seen": files_seen,
        "empty_hours": empty_hours,
        "populated_hours": len(frame),
        "first_utc": frame.index.min().isoformat(),
        "last_utc": frame.index.max().isoformat(),
        "cache_path": str(cache_path),
        "cache_sha256": sha256_file(cache_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return frame, manifest


def _timestamp_index(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "timestamp_utc" in result.columns:
        timestamps = pd.to_datetime(result.pop("timestamp_utc"), utc=True)
    else:
        timestamps = pd.to_datetime(result["timestamp_ms"], unit="ms", utc=True)
    result.index = pd.DatetimeIndex(timestamps, name="timestamp_utc")
    return result[~result.index.duplicated(keep="last")].sort_index()


def load_fx_m5(bar_root: Path, symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    path = bar_root / f"{symbol}_M5_BIDASK.parquet"
    frame = pd.read_parquet(path)
    frame = _timestamp_index(frame)
    frame = frame.loc[(frame.index >= start) & (frame.index <= end)]
    if frame.empty:
        raise RuntimeError(f"No M5 bars for {symbol}")
    return frame


def aggregate_fx_h1(m5: pd.DataFrame) -> pd.DataFrame:
    agg = {
        "timestamp_ms": "first",
        "bid_open": "first",
        "bid_high": "max",
        "bid_low": "min",
        "bid_close": "last",
        "ask_open": "first",
        "ask_high": "max",
        "ask_low": "min",
        "ask_close": "last",
        "tick_count": "sum",
    }
    h1 = m5.resample("1h", label="left", closed="left").agg(agg).dropna()
    h1["open"] = (h1["bid_open"] + h1["ask_open"]) / 2.0
    h1["high"] = (h1["bid_high"] + h1["ask_high"]) / 2.0
    h1["low"] = (h1["bid_low"] + h1["ask_low"]) / 2.0
    h1["close"] = (h1["bid_close"] + h1["ask_close"]) / 2.0
    return h1


def true_range(frame: pd.DataFrame) -> pd.Series:
    previous = frame["close"].shift(1)
    return pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous).abs(),
            (frame["low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)


def add_features(frame: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    result = frame.copy()
    result["ema_fast"] = result["close"].ewm(span=cfg["ema_fast_h1"], adjust=False).mean()
    result["ema_slow"] = result["close"].ewm(span=cfg["ema_slow_h1"], adjust=False).mean()
    result["tr"] = true_range(result)
    result["atr"] = result["tr"].rolling(cfg["atr_h1"], min_periods=cfg["atr_h1"]).mean()
    shock_lookback = cfg["shock_lookback_h1"]
    result["shock_threshold"] = (
        result["tr"].rolling(shock_lookback, min_periods=shock_lookback).quantile(cfg["shock_range_quantile"]).shift(1)
    )
    hours = cfg["compression_hours"]
    result["range_12"] = result["high"].rolling(hours, min_periods=hours).max() - result["low"].rolling(hours, min_periods=hours).min()
    result["range_12_atr"] = result["range_12"] / result["atr"]
    result["compression_threshold"] = (
        result["range_12_atr"]
        .rolling(cfg["compression_lookback_h1"], min_periods=cfg["compression_lookback_h1"])
        .quantile(cfg["compression_quantile"])
        .shift(1)
    )
    result["compressed"] = result["range_12_atr"] <= result["compression_threshold"]
    return result


def build_state_table(
    dxy: pd.DataFrame,
    bond: pd.DataFrame,
    fx_h1: dict[str, pd.DataFrame],
    cfg: dict[str, Any],
) -> pd.DataFrame:
    featured = {"DXY": add_features(dxy, cfg), "BOND": add_features(bond, cfg)}
    featured.update({symbol: add_features(frame, cfg) for symbol, frame in fx_h1.items()})
    common = featured["DXY"].index
    for frame in featured.values():
        common = common.intersection(frame.index)
    common = common.sort_values()
    state = pd.DataFrame(index=common)
    for key, frame in featured.items():
        for column in (
            "open", "high", "low", "close", "ema_fast", "ema_slow", "tr", "atr",
            "shock_threshold", "range_12_atr", "compression_threshold", "compressed",
        ):
            state[f"{key}_{column}"] = frame.loc[common, column]

    separation = cfg["trend_separation_atr"]
    dxy_up = state["DXY_ema_fast"] > state["DXY_ema_slow"] + separation * state["DXY_atr"]
    dxy_down = state["DXY_ema_fast"] < state["DXY_ema_slow"] - separation * state["DXY_atr"]
    bond_down = state["BOND_ema_fast"] < state["BOND_ema_slow"] - separation * state["BOND_atr"]
    bond_up = state["BOND_ema_fast"] > state["BOND_ema_slow"] + separation * state["BOND_atr"]
    breadth_up = (
        (state["EURUSD_ema_fast"] < state["EURUSD_ema_slow"]).astype(int)
        + (state["GBPUSD_ema_fast"] < state["GBPUSD_ema_slow"]).astype(int)
        + (state["USDJPY_ema_fast"] > state["USDJPY_ema_slow"]).astype(int)
    )
    breadth_down = (
        (state["EURUSD_ema_fast"] > state["EURUSD_ema_slow"]).astype(int)
        + (state["GBPUSD_ema_fast"] > state["GBPUSD_ema_slow"]).astype(int)
        + (state["USDJPY_ema_fast"] < state["USDJPY_ema_slow"]).astype(int)
    )
    state["direction"] = "NEUTRAL"
    state.loc[dxy_up & bond_down & (breadth_up >= 2), "direction"] = "USD_UP"
    state.loc[dxy_down & bond_up & (breadth_down >= 2), "direction"] = "USD_DOWN"

    shock_columns = ["DXY", "BOND", "EURUSD", "GBPUSD", "USDJPY"]
    shock = pd.Series(False, index=state.index)
    for key in shock_columns:
        shock |= state[f"{key}_tr"] > state[f"{key}_shock_threshold"]
    state["shock"] = shock
    same = state["direction"].ne("NEUTRAL")
    for lag in range(1, cfg["established_bars"]):
        same &= state["direction"].eq(state["direction"].shift(lag))
    state["phase"] = np.where(
        state["direction"].eq("NEUTRAL"),
        "UNRESOLVED",
        np.where(same, "ESTABLISHED", "TRANSITION"),
    )
    state["volatility"] = np.where(state["shock"], "SHOCK", "NORMAL")
    return state


def generate_signals(state: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, pd.DataFrame]:
    signals: dict[str, pd.DataFrame] = {}
    r1_cfg = cfg["specialists"]["r1_usd_trend_synchronization"]
    hours = r1_cfg["breakout_hours"]
    dxy_high = state["DXY_high"].rolling(hours, min_periods=hours).max().shift(1)
    dxy_low = state["DXY_low"].rolling(hours, min_periods=hours).min().shift(1)
    jpy_high = state["USDJPY_high"].rolling(hours, min_periods=hours).max().shift(1)
    jpy_low = state["USDJPY_low"].rolling(hours, min_periods=hours).min().shift(1)
    r1_up = (
        state["direction"].eq("USD_UP")
        & state["phase"].eq("ESTABLISHED")
        & ~state["shock"]
        & (state["DXY_close"] > dxy_high)
        & (state["USDJPY_close"] > jpy_high)
    )
    r1_down = (
        state["direction"].eq("USD_DOWN")
        & state["phase"].eq("ESTABLISHED")
        & ~state["shock"]
        & (state["DXY_close"] < dxy_low)
        & (state["USDJPY_close"] < jpy_low)
    )
    r1_raw = r1_up | r1_down
    r1_first = r1_raw & ~r1_raw.shift(1, fill_value=False)
    r1 = state.loc[r1_first, ["direction", "USDJPY_atr"]].copy()
    r1["specialist"] = "r1_usd_trend_synchronization"
    r1["symbol"] = "USDJPY"
    r1["side"] = np.where(r1["direction"].eq("USD_UP"), "LONG", "SHORT")
    r1["atr"] = r1["USDJPY_atr"]
    signals["r1_usd_trend_synchronization"] = r1

    r2_cfg = cfg["specialists"]["r2_crossasset_compression_release"]
    hours = r2_cfg["breakout_hours"]
    dxy_high = state["DXY_high"].rolling(hours, min_periods=hours).max().shift(1)
    dxy_low = state["DXY_low"].rolling(hours, min_periods=hours).min().shift(1)
    gbp_high = state["GBPUSD_high"].rolling(hours, min_periods=hours).max().shift(1)
    gbp_low = state["GBPUSD_low"].rolling(hours, min_periods=hours).min().shift(1)
    was_compressed = state["DXY_compressed"].shift(1, fill_value=False) & state["GBPUSD_compressed"].shift(1, fill_value=False)
    release_up = (
        was_compressed
        & state["direction"].eq("USD_UP")
        & ~state["shock"]
        & (state["DXY_close"] > dxy_high)
        & (state["GBPUSD_close"] < gbp_low)
    )
    release_down = (
        was_compressed
        & state["direction"].eq("USD_DOWN")
        & ~state["shock"]
        & (state["DXY_close"] < dxy_low)
        & (state["GBPUSD_close"] > gbp_high)
    )
    r2_raw = release_up | release_down
    r2_first = r2_raw & ~r2_raw.shift(1, fill_value=False)
    r2 = state.loc[r2_first, ["direction", "GBPUSD_atr"]].copy()
    r2["specialist"] = "r2_crossasset_compression_release"
    r2["symbol"] = "GBPUSD"
    r2["side"] = np.where(r2["direction"].eq("USD_UP"), "SHORT", "LONG")
    r2["atr"] = r2["GBPUSD_atr"]
    signals["r2_crossasset_compression_release"] = r2
    return signals


def _next_bar_position(index: pd.DatetimeIndex, timestamp: pd.Timestamp) -> int | None:
    position = int(index.searchsorted(timestamp, side="left"))
    return position if position < len(index) else None


def simulate_specialist(
    signals: pd.DataFrame,
    m5: pd.DataFrame,
    specialist_cfg: dict[str, Any],
    execution_cfg: dict[str, Any],
    quarantine: list[dict[str, Any]],
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    symbol = specialist_cfg["symbol"]
    pip = PIP_SIZE[symbol]
    slip = execution_cfg["extra_slippage_pips_per_side"] * pip
    blocked_hours = set(execution_cfg["blocked_entry_hours_utc"])
    for signal_time, signal in signals.iterrows():
        eligibility_time = signal_time + pd.Timedelta(hours=1)
        position = _next_bar_position(m5.index, eligibility_time)
        if position is None:
            continue
        entry_time = m5.index[position]
        if entry_time.hour in blocked_hours:
            continue
        if open_until is not None and entry_time < open_until:
            continue
        if is_quarantined(entry_time, symbol, quarantine):
            continue
        side = signal["side"]
        risk_distance = float(signal["atr"]) * float(specialist_cfg["stop_atr"])
        if not math.isfinite(risk_distance) or risk_distance <= 0:
            continue
        entry_bar = m5.iloc[position]
        if side == "LONG":
            entry_price = float(entry_bar["ask_open"]) + slip
            stop = entry_price - risk_distance
            target = entry_price + float(specialist_cfg["target_r"]) * risk_distance
        else:
            entry_price = float(entry_bar["bid_open"]) - slip
            stop = entry_price + risk_distance
            target = entry_price - float(specialist_cfg["target_r"]) * risk_distance
        deadline = entry_time + pd.Timedelta(hours=int(specialist_cfg["max_hold_h1"]))
        exit_time, exit_price, reason = _walk_exit(
            m5, position, deadline, side, stop, target, slip
        )
        pnl_price = exit_price - entry_price if side == "LONG" else entry_price - exit_price
        r_multiple = pnl_price / risk_distance
        records.append(
            {
                "specialist": signal["specialist"],
                "symbol": symbol,
                "signal_time_utc": signal_time,
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "side": side,
                "entry_price": entry_price,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk_distance,
                "r": r_multiple,
                "extra_half_pip_stress_r": r_multiple - (0.5 * pip / risk_distance),
            }
        )
        open_until = exit_time
    return pd.DataFrame(records)


def _walk_exit(
    m5: pd.DataFrame,
    start_position: int,
    deadline: pd.Timestamp,
    side: str,
    stop: float,
    target: float,
    slip: float,
) -> tuple[pd.Timestamp, float, str]:
    last_position = min(int(m5.index.searchsorted(deadline, side="left")), len(m5) - 1)
    for position in range(start_position, last_position + 1):
        timestamp = m5.index[position]
        bar = m5.iloc[position]
        if side == "LONG":
            stop_hit = float(bar["bid_low"]) <= stop
            target_hit = float(bar["bid_high"]) >= target
            if stop_hit:
                raw = min(float(bar["bid_open"]), stop)
                return timestamp, raw - slip, "STOP"
            if target_hit:
                raw = max(float(bar["bid_open"]), target)
                return timestamp, raw - slip, "TARGET"
        else:
            stop_hit = float(bar["ask_high"]) >= stop
            target_hit = float(bar["ask_low"]) <= target
            if stop_hit:
                raw = max(float(bar["ask_open"]), stop)
                return timestamp, raw + slip, "STOP"
            if target_hit:
                raw = min(float(bar["ask_open"]), target)
                return timestamp, raw + slip, "TARGET"
    bar = m5.iloc[last_position]
    if side == "LONG":
        return m5.index[last_position], float(bar["bid_close"]) - slip, "TIME"
    return m5.index[last_position], float(bar["ask_close"]) + slip, "TIME"


def is_quarantined(timestamp: pd.Timestamp, symbol: str, quarantine: Iterable[dict[str, Any]]) -> bool:
    for interval in quarantine:
        if symbol not in interval["symbols"]:
            continue
        start = pd.Timestamp(interval["start_utc"])
        end = pd.Timestamp(interval["end_utc"])
        if start <= timestamp <= end:
            return True
    return False


def metric_block(trades: pd.DataFrame, value_column: str = "r") -> dict[str, Any]:
    values = trades[value_column].astype(float) if not trades.empty else pd.Series(dtype=float)
    wins = values[values > 0].sum()
    losses = -values[values < 0].sum()
    profit_factor = float(wins / losses) if losses > 0 else (float("inf") if wins > 0 else 0.0)
    equity = values.cumsum()
    drawdown = equity.cummax().sub(equity)
    return {
        "trades": int(len(values)),
        "net_r": float(values.sum()),
        "profit_factor": profit_factor,
        "expectancy_r": float(values.mean()) if len(values) else 0.0,
        "win_rate": float((values > 0).mean()) if len(values) else 0.0,
        "max_drawdown_r": float(drawdown.max()) if len(drawdown) else 0.0,
    }


def remove_top_winners(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    count = max(1, math.ceil(len(trades) * 0.05))
    drop_index = trades.nlargest(count, "r").index
    return trades.drop(index=drop_index)


def summarize_specialist(
    trades: pd.DataFrame,
    windows: dict[str, list[str]],
    admission_cfg: dict[str, Any],
) -> dict[str, Any]:
    overall = metric_block(trades)
    top_removed = metric_block(remove_top_winners(trades))
    stressed = metric_block(trades, "extra_half_pip_stress_r")
    by_window: dict[str, Any] = {}
    for name, (start_text, end_text) in windows.items():
        start = pd.Timestamp(start_text)
        end = pd.Timestamp(end_text)
        subset = trades[
            (trades["entry_time_utc"] >= start) & (trades["entry_time_utc"] <= end)
        ] if not trades.empty else trades
        by_window[name] = metric_block(subset)
    window_pass = all(
        block["trades"] >= admission_cfg["minimum_trades_each_window"]
        and block["profit_factor"] >= admission_cfg["minimum_profit_factor_each_window"]
        and block["expectancy_r"] > admission_cfg["minimum_expectancy_r_each_window"]
        for block in by_window.values()
    )
    admitted = (
        window_pass
        and overall["max_drawdown_r"] <= admission_cfg["maximum_drawdown_r_overall"]
        and top_removed["net_r"] > 0
        and stressed["net_r"] > 0
    )
    return {
        "status": "ADMITTED_RESEARCH_COMPONENT" if admitted else "REJECTED_STANDALONE",
        "admitted": admitted,
        "overall": overall,
        "windows": by_window,
        "top_5_percent_winners_removed": top_removed,
        "extra_half_pip_round_trip": stressed,
    }


def route_portfolio(
    trades_by_specialist: dict[str, pd.DataFrame],
    admitted: list[str],
    router_cfg: dict[str, Any],
) -> pd.DataFrame:
    if not admitted:
        return pd.DataFrame()
    priorities = {name: rank for rank, name in enumerate(router_cfg["priority"])}
    candidates = pd.concat([trades_by_specialist[name] for name in admitted], ignore_index=True)
    candidates["priority"] = candidates["specialist"].map(priorities)
    candidates = candidates.sort_values(["entry_time_utc", "priority"]).reset_index(drop=True)
    accepted: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    closed_daily: dict[str, float] = {}
    closed_weekly: dict[str, float] = {}
    settled = 0
    for _, row in candidates.iterrows():
        entry_time = row["entry_time_utc"]
        while settled < len(accepted) and accepted[settled]["exit_time_utc"] <= entry_time:
            closed = accepted[settled]
            exit_time = closed["exit_time_utc"]
            day_key = exit_time.strftime("%Y-%m-%d")
            iso = exit_time.isocalendar()
            week_key = f"{iso.year}-W{iso.week:02d}"
            closed_daily[day_key] = closed_daily.get(day_key, 0.0) + float(closed["r"])
            closed_weekly[week_key] = closed_weekly.get(week_key, 0.0) + float(closed["r"])
            settled += 1
        if open_until is not None and entry_time < open_until:
            continue
        day_key = entry_time.strftime("%Y-%m-%d")
        iso = entry_time.isocalendar()
        week_key = f"{iso.year}-W{iso.week:02d}"
        if closed_daily.get(day_key, 0.0) <= router_cfg["daily_loss_stop_r"]:
            continue
        if closed_weekly.get(week_key, 0.0) <= router_cfg["weekly_loss_stop_r"]:
            continue
        accepted_row = row.drop(labels=["priority"]).to_dict()
        accepted.append(accepted_row)
        open_until = row["exit_time_utc"]
    return pd.DataFrame(accepted)


def active_fx_days(m5_by_symbol: dict[str, pd.DataFrame], start: pd.Timestamp, end: pd.Timestamp) -> int:
    dates: set[Any] = set()
    for frame in m5_by_symbol.values():
        eligible = frame.loc[(frame.index >= start) & (frame.index <= end)]
        dates.update(eligible.index.date)
    return len(dates)


def serialize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else "-Infinity"
    return value
