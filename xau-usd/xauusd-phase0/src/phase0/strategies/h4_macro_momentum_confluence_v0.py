from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h4_macro_composite_risk_state_v0 import (
    _macro_features_for_h4,
    _require_macro_inputs,
)


class H4MacroMomentumConfluenceV0Strategy(StrategyBase):
    """Research-only H4 macro-regime plus D1/H4 momentum confluence candidate."""

    name = "h4_macro_momentum_confluence_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.60
    throttle_days = 2

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")
        macro_inputs = _require_macro_inputs(data_context)

        h4_close = pd.to_numeric(h4["close"], errors="coerce")
        h4_high = pd.to_numeric(h4["high"], errors="coerce")
        h4_low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(h4_high, h4_low, h4_close, 14)
        h4["h4_ema50"] = ema(h4_close, 50)
        h4["h4_return_3"] = np.log(h4_close / h4_close.shift(3))
        h4["h4_return_12"] = np.log(h4_close / h4_close.shift(12))

        d1_features = _d1_features_for_h4(h4, d1)
        macro_features = _macro_features_for_h4(h4, macro_inputs)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                d1_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
                macro_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
            ],
            axis=1,
        )
        context["H4"] = h4
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_two_day_direction: set[tuple[str, str]] = set()

        for position in range(180, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            bucket_start = timestamp.floor("D") - pd.Timedelta(days=timestamp.dayofyear % self.throttle_days)
            direction = str(setup["direction"])
            key = (bucket_start.strftime("%Y-%m-%d"), direction)
            if key in used_two_day_direction:
                continue
            used_two_day_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"{self.name.upper()}_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_bucket": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.55 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.55 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported macro momentum confluence direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid macro momentum confluence trade plan risk.")

        return TradePlan(
            expert=self.name,
            symbol=signal.symbol,
            direction=direction,
            signal_time_utc=signal.timestamp_utc,
            entry_type="MARKET",
            entry_price=None,
            stop_loss=stop_loss,
            take_profit=take_profit,
            invalidation_level=stop_loss,
            risk_reward=self.risk_reward,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "max_holding_bars": 432, "planned_time_stop_h4_bars": 10},
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema50"],
            row["h4_return_3"],
            row["h4_return_12"],
            row["d1_close"],
            row["d1_ema20"],
            row["d1_return_5"],
            row["macro_composite_score"],
            row["macro_bull_votes"],
            row["macro_bear_votes"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema50 = float(row["h4_ema50"])
        h4_return_3 = float(row["h4_return_3"])
        h4_return_12 = float(row["h4_return_12"])
        d1_close = float(row["d1_close"])
        d1_ema20 = float(row["d1_ema20"])
        d1_return_5 = float(row["d1_return_5"])
        composite_score = float(row["macro_composite_score"])
        bull_votes = float(row["macro_bull_votes"])
        bear_votes = float(row["macro_bear_votes"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema50_distance_atr = (close - h4_ema50) / h4_atr

        if (
            composite_score >= 2.0
            and bull_votes >= 3.0
            and bear_votes <= 1.0
            and d1_close > d1_ema20
            and d1_return_5 >= 0.0015
            and low <= h4_ema50 + 0.75 * h4_atr
            and close > h4_ema50
            and close > open_price
            and h4_return_3 >= 0.0008
            and h4_return_12 >= -0.0120
            and close_location >= 0.55
            and ema50_distance_atr <= 2.75
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema50_distance_atr)

        if (
            composite_score <= -2.0
            and bear_votes >= 3.0
            and bull_votes <= 1.0
            and d1_close < d1_ema20
            and d1_return_5 <= -0.0015
            and high >= h4_ema50 - 0.75 * h4_atr
            and close < h4_ema50
            and close < open_price
            and h4_return_3 <= -0.0008
            and h4_return_12 <= 0.0120
            and close_location <= 0.45
            and ema50_distance_atr >= -2.75
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema50_distance_atr)

        return None


def _d1_features_for_h4(h4: pd.DataFrame, d1: pd.DataFrame) -> pd.DataFrame:
    frame = d1[["timestamp_utc", "high", "low", "close"]].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in ("high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "close"]).sort_values("timestamp_utc")
    frame = frame.drop_duplicates("timestamp_utc").reset_index(drop=True)
    close = frame["close"]
    frame["d1_close"] = close
    frame["d1_atr14"] = atr(frame["high"], frame["low"], close, 14)
    frame["d1_ema20"] = ema(close, 20)
    frame["d1_return_5"] = np.log(close / close.shift(5))
    feature_columns = ["d1_close", "d1_atr14", "d1_ema20", "d1_return_5"]
    frame[feature_columns] = frame[feature_columns].shift(1)

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
    ema50_distance_atr: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema50": float(row["h4_ema50"]),
        "h4_return_3": float(row["h4_return_3"]),
        "h4_return_12": float(row["h4_return_12"]),
        "close_location": close_location,
        "ema50_distance_atr": ema50_distance_atr,
        "d1_close": float(row["d1_close"]),
        "d1_atr14": float(row["d1_atr14"]),
        "d1_ema20": float(row["d1_ema20"]),
        "d1_return_5": float(row["d1_return_5"]),
        "macro_bull_votes": int(row["macro_bull_votes"]),
        "macro_bear_votes": int(row["macro_bear_votes"]),
        "macro_composite_score": int(row["macro_composite_score"]),
        "real_yield_change_20d": float(row["real_yield_change_20d"]),
        "dollar_change_20d": float(row["dollar_change_20d"]),
        "breakeven_5y_change_20d": float(row["breakeven_5y_change_20d"]),
        "dgs2_change_20d": float(row["dgs2_change_20d"]),
        "treasury_10y2y_change_20d": float(row["treasury_10y2y_change_20d"]),
        "baa10y_change_20d": float(row["baa10y_change_20d"]),
        "vix_change_20d": float(row["vix_change_20d"]),
        "gvz_change_20d": float(row["gvz_change_20d"]),
        "nfci_change_4obs": float(row["nfci_change_4obs"]),
    }
