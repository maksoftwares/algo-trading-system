"""Bid/ask FX execution engine.

Contract the engine enforces so results stay honest:

* A signal always names the M5 execution bar whose **open** is the fill. The
  strategy layer is responsible for pointing that at the bar *after* the
  decision bar closed, and ``tests/test_engine.py`` pins the offset.
* Longs pay the ask on entry and receive the bid on exit; shorts are the
  mirror. Stops and targets for a long are therefore tested against the *bid*
  path, and against the *ask* path for a short.
* Position size and every stop/target level are computed from information at
  the entry bar, in entry order. Nothing is resolved in exit order (an earlier
  lane lost a claimed PF 2.03 to exactly that look-ahead).
* When a bar's range spans both the stop and the target the **stop** is taken.
  Ambiguous bars are counted and reported rather than silently resolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .fxdata import INSTRUMENTS

ROLLOVER_HOUR_UTC = 21


@dataclass(frozen=True)
class CostModel:
    """Broker cost overlay applied on top of raw Dukascopy quotes.

    Dukascopy raw spreads are tighter than a retail account, so
    ``spread_markup_points`` widens both sides before any fill is priced.
    """

    spread_markup_points: float = 0.0
    slippage_points: float = 0.0
    stop_slippage_points: float = 0.0
    commission_per_lot_per_side_usd: float = 0.0
    swap_long_points_per_day: float = 0.0
    swap_short_points_per_day: float = 0.0


@dataclass(frozen=True)
class SymbolSpec:
    symbol: str
    point_size: float
    contract_size: float
    quote_ccy: str

    @classmethod
    def of(cls, symbol: str) -> "SymbolSpec":
        meta = INSTRUMENTS[symbol]
        return cls(
            symbol=symbol,
            point_size=float(meta["point_size"]),
            contract_size=float(meta["contract_size"]),
            quote_ccy=str(meta["quote_ccy"]),
        )


@dataclass
class Signals:
    """Strategy output in M5 execution-bar index space."""

    entry_index: np.ndarray
    direction: np.ndarray
    stop_min_points: np.ndarray
    stop_atr_points: np.ndarray
    stop_ref_price: np.ndarray
    rr: np.ndarray
    stop_cap_points: np.ndarray
    tag: np.ndarray | None = None

    def __len__(self) -> int:
        return int(self.entry_index.size)


@dataclass
class RunConfig:
    lot: float = 0.01
    max_hold_bars: int = 288  # one trading day of M5 bars
    max_entries_per_day: int = 20
    one_position_only: bool = True
    stop_first_on_ambiguous: bool = True
    extras: dict = field(default_factory=dict)


TRADE_COLUMNS = (
    "entry_index",
    "exit_index",
    "entry_ms",
    "exit_ms",
    "direction",
    "entry_price",
    "exit_price",
    "stop_price",
    "target_price",
    "stop_points",
    "lot",
    "exit_reason",
    "gross_usd",
    "commission_usd",
    "swap_usd",
    "net_usd",
    "r_multiple",
    "bars_held",
    "ambiguous_bar",
    "tag",
)


def point_value_usd(spec: SymbolSpec, lot: float, quote_price: np.ndarray | float) -> np.ndarray | float:
    """USD value of one point of price movement for ``lot`` lots.

    For a USD-quoted pair this is constant. For a JPY-quoted pair the quote
    currency must be converted at the prevailing rate, so it depends on price.
    """
    notional_points = spec.contract_size * lot * spec.point_size
    if spec.quote_ccy == "USD":
        return notional_points
    return notional_points / quote_price


def _swap_days(entry_ms: int, exit_ms: int) -> float:
    """Rollover crossings between entry and exit, Wednesday counting triple."""
    day_ms = 86_400_000
    first = ((entry_ms - ROLLOVER_HOUR_UTC * 3_600_000) // day_ms) + 1
    last = (exit_ms - ROLLOVER_HOUR_UTC * 3_600_000) // day_ms
    if last < first:
        return 0.0
    total = 0.0
    for index in range(int(first), int(last) + 1):
        moment = index * day_ms + ROLLOVER_HOUR_UTC * 3_600_000
        weekday = int((moment // day_ms + 4) % 7)  # 1970-01-01 was a Thursday
        total += 3.0 if weekday == 2 else 1.0
    return total


def simulate(
    bars: pd.DataFrame,
    signals: Signals,
    spec: SymbolSpec,
    costs: CostModel,
    config: RunConfig,
) -> pd.DataFrame:
    """Run signals against M5 bid/ask bars and return the closed-trade ledger."""
    point = spec.point_size
    half_markup = costs.spread_markup_points * point / 2.0
    slip = costs.slippage_points * point

    timestamp = bars["timestamp_ms"].to_numpy(np.int64)
    bid_open = bars["bid_open"].to_numpy(np.float64)
    bid_high = bars["bid_high"].to_numpy(np.float64)
    bid_low = bars["bid_low"].to_numpy(np.float64)
    bid_close = bars["bid_close"].to_numpy(np.float64)
    ask_open = bars["ask_open"].to_numpy(np.float64)
    ask_high = bars["ask_high"].to_numpy(np.float64)
    ask_low = bars["ask_low"].to_numpy(np.float64)
    ask_close = bars["ask_close"].to_numpy(np.float64)

    # Widen the quoted spread symmetrically: bids down, asks up.
    bid_open = bid_open - half_markup
    bid_high = bid_high - half_markup
    bid_low = bid_low - half_markup
    bid_close = bid_close - half_markup
    ask_open = ask_open + half_markup
    ask_high = ask_high + half_markup
    ask_low = ask_low + half_markup
    ask_close = ask_close + half_markup

    day_index = (timestamp // 86_400_000).astype(np.int64)
    total_bars = timestamp.size

    order = np.argsort(signals.entry_index, kind="stable")
    rows: list[dict] = []
    busy_until = -1
    entries_today: dict[int, int] = {}

    for slot in order:
        entry_i = int(signals.entry_index[slot])
        if entry_i < 0 or entry_i >= total_bars - 1:
            continue
        if config.one_position_only and entry_i <= busy_until:
            continue
        day = int(day_index[entry_i])
        if entries_today.get(day, 0) >= config.max_entries_per_day:
            continue

        direction = int(signals.direction[slot])
        if direction not in (1, -1):
            continue

        # ---- entry pricing (entry-bar information only) ----
        if direction == 1:
            entry_price = ask_open[entry_i] + slip
        else:
            entry_price = bid_open[entry_i] - slip

        stop_points = max(
            float(signals.stop_min_points[slot]),
            float(signals.stop_atr_points[slot]),
        )
        reference = float(signals.stop_ref_price[slot])
        if np.isfinite(reference):
            reference_points = (
                (entry_price - reference) / point if direction == 1 else (reference - entry_price) / point
            )
            stop_points = max(stop_points, reference_points)
        stop_points = min(stop_points, float(signals.stop_cap_points[slot]))
        if stop_points <= 0:
            continue

        stop_distance = stop_points * point
        target_distance = stop_distance * float(signals.rr[slot])
        if direction == 1:
            stop_price = entry_price - stop_distance
            target_price = entry_price + target_distance
        else:
            stop_price = entry_price + stop_distance
            target_price = entry_price - target_distance

        # ---- forward scan for the exit ----
        last_i = min(entry_i + config.max_hold_bars, total_bars - 1)
        window = slice(entry_i, last_i + 1)
        if direction == 1:
            hit_stop = bid_low[window] <= stop_price
            hit_target = bid_high[window] >= target_price
        else:
            hit_stop = ask_high[window] >= stop_price
            hit_target = ask_low[window] <= target_price

        stop_at = int(np.argmax(hit_stop)) if hit_stop.any() else -1
        target_at = int(np.argmax(hit_target)) if hit_target.any() else -1

        if stop_at < 0 and target_at < 0:
            exit_i = last_i
            exit_price = bid_close[exit_i] if direction == 1 else ask_close[exit_i]
            reason = "timeout"
            ambiguous = False
        else:
            if stop_at < 0:
                first, reason = target_at, "target"
            elif target_at < 0:
                first, reason = stop_at, "stop"
            elif stop_at < target_at:
                first, reason = stop_at, "stop"
            elif target_at < stop_at:
                first, reason = target_at, "target"
            else:
                first = stop_at
                reason = "stop" if config.stop_first_on_ambiguous else "target"
            ambiguous = stop_at >= 0 and target_at >= 0 and stop_at == target_at
            exit_i = entry_i + first
            if reason == "target":
                exit_price = target_price
            else:
                # Stops fill worse than the level in practice; targets are limit
                # orders and do not enjoy the mirror-image improvement.
                stop_slip = costs.stop_slippage_points * point
                exit_price = stop_price - stop_slip if direction == 1 else stop_price + stop_slip

        # ---- economics ----
        if spec.quote_ccy == "USD":
            pv = point_value_usd(spec, config.lot, 1.0)
        else:
            pv = point_value_usd(spec, config.lot, float(exit_price))
        moved_points = ((exit_price - entry_price) if direction == 1 else (entry_price - exit_price)) / point
        gross = moved_points * pv
        commission = 2.0 * costs.commission_per_lot_per_side_usd * config.lot
        swap_points = (
            costs.swap_long_points_per_day if direction == 1 else costs.swap_short_points_per_day
        ) * _swap_days(int(timestamp[entry_i]), int(timestamp[exit_i]))
        swap = swap_points * pv
        net = gross - commission + swap

        rows.append(
            {
                "entry_index": entry_i,
                "exit_index": exit_i,
                "entry_ms": int(timestamp[entry_i]),
                "exit_ms": int(timestamp[exit_i]),
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "stop_price": stop_price,
                "target_price": target_price,
                "stop_points": stop_points,
                "lot": config.lot,
                "exit_reason": reason,
                "gross_usd": gross,
                "commission_usd": commission,
                "swap_usd": swap,
                "net_usd": net,
                "r_multiple": net / max(stop_points * pv, 1e-12),
                "bars_held": exit_i - entry_i,
                "ambiguous_bar": bool(ambiguous),
                "tag": "" if signals.tag is None else str(signals.tag[slot]),
            }
        )
        busy_until = exit_i
        entries_today[day] = entries_today.get(day, 0) + 1

    if not rows:
        return pd.DataFrame({name: [] for name in TRADE_COLUMNS})
    return pd.DataFrame(rows, columns=list(TRADE_COLUMNS))
