from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .research import add_h4_regimes

POINT = 0.00001
PIP = 0.0001


@dataclass(frozen=True)
class FrequencyCandidate:
    candidate_id: str
    family: str
    regime: str
    direction: str
    threshold: float
    stop_atr: float
    target_r: float
    max_hold_bars: int
    lookback: int = 0
    body_min: float = 0.0
    session: str = "all"

    @property
    def parameter_sha256(self) -> str:
        payload = asdict(self).copy()
        payload.pop("candidate_id")
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def load_capital_m15(path: Path, regime_contract: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(path)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    if frame["timestamp"].isna().any() or frame["timestamp"].duplicated().any():
        raise ValueError("M15 source contains invalid or duplicate timestamps")
    spread = frame["spread_points"].astype(float) * POINT
    for field in ("open", "high", "low", "close"):
        frame[f"ask_{field}"] = frame[f"bid_{field}"].astype(float) + spread
    frame, h4 = add_h4_regimes(frame, regime_contract)
    previous_close = frame["bid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous_close).abs(),
            (frame["bid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    frame["atr14"] = wilder(true_range, 14)
    delta = frame["bid_close"].diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    relative_strength = wilder(gains, 14) / wilder(losses, 14).replace(0.0, np.nan)
    frame["rsi14"] = 100.0 - (100.0 / (1.0 + relative_strength))
    frame["ema20"] = frame["bid_close"].ewm(span=20, adjust=False).mean()
    frame["ema50"] = frame["bid_close"].ewm(span=50, adjust=False).mean()
    frame["ema200"] = frame["bid_close"].ewm(span=200, adjust=False).mean()
    frame["band_mid"] = frame["bid_close"].rolling(20).mean()
    frame["band_std"] = frame["bid_close"].rolling(20).std(ddof=0)
    frame["body_fraction"] = (
        (frame["bid_close"] - frame["bid_open"]).abs()
        / (frame["bid_high"] - frame["bid_low"]).replace(0.0, np.nan)
    ).fillna(0.0)
    frame["hour"] = frame["timestamp"].dt.hour
    frame["minute"] = frame["timestamp"].dt.minute
    frame["active_date"] = frame["timestamp"].dt.strftime("%Y-%m-%d")
    return frame, h4


def _session_mask(frame: pd.DataFrame, session: str) -> np.ndarray:
    hour = frame["hour"].to_numpy()
    sessions = {
        "all": np.ones(len(frame), dtype=bool),
        "asia": (hour >= 0) & (hour < 6),
        "london": (hour >= 6) & (hour < 12),
        "new_york": (hour >= 12) & (hour < 18),
        "late": (hour >= 18) & (hour < 22),
        "liquid": (hour >= 6) & (hour < 18),
    }
    return sessions[session]


def signal_mask(frame: pd.DataFrame, candidate: FrequencyCandidate) -> np.ndarray:
    close = frame["bid_close"]
    high = frame["bid_high"]
    low = frame["bid_low"]
    direction = candidate.direction
    if candidate.family == "rsi_fade":
        if direction == "long":
            mask = (frame["rsi14"] <= candidate.threshold) & (close < frame["band_mid"])
        else:
            mask = (frame["rsi14"] >= 100.0 - candidate.threshold) & (close > frame["band_mid"])
    elif candidate.family == "bb_fade":
        distance = candidate.threshold * frame["band_std"]
        if direction == "long":
            mask = close <= frame["band_mid"] - distance
        else:
            mask = close >= frame["band_mid"] + distance
    elif candidate.family == "bb_reclaim":
        distance = candidate.threshold * frame["band_std"]
        lower = frame["band_mid"] - distance
        upper = frame["band_mid"] + distance
        if direction == "long":
            mask = (low <= lower) & (close > lower) & (close > frame["bid_open"])
        else:
            mask = (high >= upper) & (close < upper) & (close < frame["bid_open"])
    elif candidate.family == "trend_break":
        prior_high = high.shift(1).rolling(candidate.lookback).max()
        prior_low = low.shift(1).rolling(candidate.lookback).min()
        if direction == "long":
            mask = (close > prior_high) & (frame["ema20"] > frame["ema50"])
        else:
            mask = (close < prior_low) & (frame["ema20"] < frame["ema50"])
    elif candidate.family == "trend_pullback":
        if direction == "long":
            mask = (
                (frame["ema20"] > frame["ema50"])
                & (low <= frame["ema20"])
                & (close > frame["ema20"])
                & (close > frame["bid_open"])
            )
        else:
            mask = (
                (frame["ema20"] < frame["ema50"])
                & (high >= frame["ema20"])
                & (close < frame["ema20"])
                & (close < frame["bid_open"])
            )
    elif candidate.family == "compression_break":
        prior_high = high.shift(1).rolling(candidate.lookback).max()
        prior_low = low.shift(1).rolling(candidate.lookback).min()
        if direction == "long":
            mask = close > prior_high
        else:
            mask = close < prior_low
    elif candidate.family.startswith("scheduled_"):
        decision_hour = int(candidate.threshold)
        if candidate.family in (
            "scheduled_momentum",
            "scheduled_reversal",
            "scheduled_up_follow",
            "scheduled_up_fade",
            "scheduled_down_follow",
            "scheduled_down_fade",
        ):
            signed_move = close - close.shift(candidate.lookback)
            displacement = signed_move.abs() / frame["atr14"]
        else:
            displacement = (frame["ema20"] - frame["ema50"]).abs() / frame["atr14"]
        mask = (
            (frame["hour"] == decision_hour)
            & (frame["minute"] == 0)
            & (displacement >= candidate.body_min)
        )
        if candidate.family in ("scheduled_up_follow", "scheduled_up_fade"):
            mask &= signed_move > 0
        elif candidate.family in ("scheduled_down_follow", "scheduled_down_fade"):
            mask &= signed_move < 0
    else:
        raise ValueError(f"Unsupported family: {candidate.family}")
    return (
        mask.fillna(False).to_numpy()
        & (frame["regime"].to_numpy() == candidate.regime)
        & (frame["body_fraction"].to_numpy() >= candidate.body_min)
        & _session_mask(frame, candidate.session)
    )


def resolved_direction(
    frame: pd.DataFrame, candidate: FrequencyCandidate, signal_index: int
) -> str | None:
    if candidate.direction in ("long", "short"):
        return candidate.direction
    close = float(frame.at[signal_index, "bid_close"])
    if candidate.family in (
        "scheduled_momentum",
        "scheduled_reversal",
        "scheduled_up_follow",
        "scheduled_up_fade",
        "scheduled_down_follow",
        "scheduled_down_fade",
    ):
        reference_index = signal_index - candidate.lookback
        if reference_index < 0:
            return None
        reference = float(frame.at[reference_index, "bid_close"])
        momentum = "long" if close > reference else ("short" if close < reference else None)
        if candidate.family == "scheduled_reversal" and momentum is not None:
            return "short" if momentum == "long" else "long"
        if candidate.family == "scheduled_up_follow":
            return "long"
        if candidate.family == "scheduled_up_fade":
            return "short"
        if candidate.family == "scheduled_down_follow":
            return "short"
        if candidate.family == "scheduled_down_fade":
            return "long"
        return momentum
    if candidate.family in ("scheduled_ema_follow", "scheduled_ema_fade"):
        fast = float(frame.at[signal_index, "ema20"])
        slow = float(frame.at[signal_index, "ema50"])
        following = "long" if fast > slow else ("short" if fast < slow else None)
        if candidate.family == "scheduled_ema_fade" and following is not None:
            return "short" if following == "long" else "long"
        return following
    return None


def simulate(
    frame: pd.DataFrame,
    candidate: FrequencyCandidate,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    maximum_trades_per_day: int = 4,
    entry_slippage_points: float = 1.0,
    exit_slippage_points: float = 1.0,
) -> list[dict]:
    mask = signal_mask(frame, candidate)
    in_window = ((frame["timestamp"] >= start) & (frame["timestamp"] < end)).to_numpy()
    selected = np.flatnonzero(mask & in_window)
    trades: list[dict] = []
    next_available = 0
    daily_count: dict[str, int] = {}
    for signal_index in selected:
        entry_index = signal_index + 1
        if entry_index <= next_available or entry_index >= len(frame):
            continue
        entry_time = frame.at[entry_index, "timestamp"]
        if entry_time >= end:
            continue
        day = frame.at[entry_index, "active_date"]
        if daily_count.get(day, 0) >= maximum_trades_per_day:
            continue
        atr = float(frame.at[signal_index, "atr14"])
        if not math.isfinite(atr) or atr <= 0:
            continue
        direction = resolved_direction(frame, candidate, signal_index)
        if direction is None:
            continue
        window_start = max(0, signal_index - 5)
        if direction == "long":
            entry = float(frame.at[entry_index, "ask_open"]) + entry_slippage_points * POINT
            recent = float(frame.loc[window_start:signal_index, "bid_low"].min())
            stop = min(recent, entry - candidate.stop_atr * atr)
            target = entry + candidate.target_r * (entry - stop)
        else:
            entry = float(frame.at[entry_index, "bid_open"]) - entry_slippage_points * POINT
            ask_high = frame.loc[window_start:signal_index, "ask_high"]
            recent = float(ask_high.max())
            stop = max(recent, entry + candidate.stop_atr * atr)
            target = entry - candidate.target_r * (stop - entry)
        stop_distance = abs(entry - stop)
        if stop_distance <= 0:
            continue
        exit_index = min(entry_index + candidate.max_hold_bars, len(frame) - 1)
        exit_price = None
        reason = "time"
        for bar_index in range(entry_index, exit_index + 1):
            if frame.at[bar_index, "timestamp"] >= end:
                exit_index = bar_index
                break
            if direction == "long":
                stop_hit = float(frame.at[bar_index, "bid_low"]) <= stop
                target_hit = float(frame.at[bar_index, "bid_high"]) >= target
            else:
                stop_hit = float(frame.at[bar_index, "ask_high"]) >= stop
                target_hit = float(frame.at[bar_index, "ask_low"]) <= target
            if stop_hit:
                exit_index = bar_index
                exit_price = stop
                reason = "stop"
                break
            if target_hit:
                exit_index = bar_index
                exit_price = target
                reason = "target"
                break
        if exit_price is None:
            if direction == "long":
                exit_price = float(frame.at[exit_index, "bid_close"])
            else:
                exit_price = float(frame.at[exit_index, "ask_close"])
        if direction == "long":
            exit_price -= exit_slippage_points * POINT
            net_price = exit_price - entry
        else:
            exit_price += exit_slippage_points * POINT
            net_price = entry - exit_price
        trades.append(
            {
                "candidate_id": candidate.candidate_id,
                "family": candidate.family,
                "regime": candidate.regime,
                "direction": direction,
                "entry_time": entry_time,
                "exit_time": frame.at[exit_index, "timestamp"],
                "entry": entry,
                "stop": stop,
                "target": target,
                "exit": exit_price,
                "exit_reason": reason,
                "net_pips": net_price / PIP,
                "net_r": net_price / stop_distance,
            }
        )
        daily_count[day] = daily_count.get(day, 0) + 1
        next_available = exit_index
    return trades


def profit_factor(values: Iterable[float]) -> float:
    values = np.asarray(list(values), dtype=float)
    gross_profit = float(values[values > 0].sum())
    gross_loss = float(-values[values < 0].sum())
    return gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)


def metrics(trades: list[dict], active_days: int) -> dict:
    values = np.asarray([trade["net_r"] for trade in trades], dtype=float)
    pips = np.asarray([trade["net_pips"] for trade in trades], dtype=float)
    if len(values):
        equity = np.cumsum(values)
        peak = np.maximum.accumulate(np.insert(equity, 0, 0.0))[1:]
        drawdown = float(np.max(peak - equity))
        remove_count = max(1, int(math.ceil(len(values) * 0.05)))
        removed = np.delete(values, np.argsort(values)[-remove_count:])
    else:
        drawdown = 0.0
        removed = values
    months: dict[str, float] = {}
    for trade in trades:
        key = pd.Timestamp(trade["exit_time"]).strftime("%Y-%m")
        months[key] = months.get(key, 0.0) + float(trade["net_r"])
    return {
        "trades": len(trades),
        "trades_per_active_day": len(trades) / active_days if active_days else 0.0,
        "wins": int((values > 0).sum()),
        "win_rate": float((values > 0).mean()) if len(values) else 0.0,
        "net_r": float(values.sum()),
        "average_r": float(values.mean()) if len(values) else 0.0,
        "net_pips": float(pips.sum()),
        "profit_factor": profit_factor(values),
        "maximum_drawdown_r": drawdown,
        "positive_active_month_share": (
            sum(value > 0 for value in months.values()) / len(months) if months else 0.0
        ),
        "top_5pct_removed_profit_factor": profit_factor(removed),
    }


def route_portfolio(
    candidate_trades: dict[str, list[dict]],
    priority: list[str],
    *,
    maximum_trades_per_day: int = 2,
) -> list[dict]:
    rank = {candidate_id: index for index, candidate_id in enumerate(priority)}
    events = [
        trade
        for candidate_id in priority
        for trade in candidate_trades.get(candidate_id, [])
    ]
    events.sort(key=lambda trade: (trade["entry_time"], rank[trade["candidate_id"]]))
    routed: list[dict] = []
    available_time = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[str, int] = {}
    for trade in events:
        entry_time = pd.Timestamp(trade["entry_time"])
        day = entry_time.strftime("%Y-%m-%d")
        if entry_time < available_time or daily_count.get(day, 0) >= maximum_trades_per_day:
            continue
        routed.append(trade)
        daily_count[day] = daily_count.get(day, 0) + 1
        available_time = pd.Timestamp(trade["exit_time"])
    return routed
