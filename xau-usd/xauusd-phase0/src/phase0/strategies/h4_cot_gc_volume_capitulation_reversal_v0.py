from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.cot_gold_data import COT_FRAME_KEY
from phase0.data_contracts import Signal, TradePlan
from phase0.gc_futures_volume_data import GC_FUTURES_VOLUME_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.cot_gold_positioning_reversal_v0 import _cot_features_for_h4
from phase0.strategies.h4_gold_futures_volume_climax_v0 import (
    _d1_features_for_h4,
    _gc_volume_features_for_h4,
)


class H4CotGcVolumeCapitulationReversalV0Strategy(StrategyBase):
    """Research-only H4 reversal after COT extreme and GC futures volume capitulation."""

    name = "h4_cot_gc_volume_capitulation_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.55
    volume_percentile_threshold = 0.78
    volume_z_threshold = 0.75
    prior_day_return_threshold = 0.0035

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")
        cot = data_context.get(COT_FRAME_KEY)
        gc_volume = data_context.get(GC_FUTURES_VOLUME_FRAME_KEY)
        if not isinstance(cot, pd.DataFrame):
            raise ConfigError(
                "h4_cot_gc_volume_capitulation_reversal_v0 requires data_context['cot_gold']."
            )
        if not isinstance(gc_volume, pd.DataFrame):
            raise ConfigError(
                "h4_cot_gc_volume_capitulation_reversal_v0 requires "
                "data_context['gc_futures_volume']."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(high, low, close, 14)
        h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))

        cot_features = _cot_features_for_h4(h4, cot)
        d1_features = _d1_features_for_h4(h4, d1)
        volume_features = _gc_volume_features_for_h4(h4, gc_volume)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                cot_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
                d1_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
                volume_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
        used_cot_week_direction: set[tuple[str, str]] = set()

        for position in range(260, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            cot_week = str(row["cot_report_date"])[:10]
            direction = str(setup["direction"])
            key = (cot_week, direction)
            if key in used_cot_week_direction:
                continue
            used_cot_week_direction.add(key)

            timestamp = pd.Timestamp(row["timestamp_utc"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_COT_GC_VOLUME_CAPITULATION_REVERSAL_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "cot_week": cot_week},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.20 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.20 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported COT/GC volume reversal direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid COT/GC volume reversal trade plan risk.")

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
            metadata={**signal.metadata, "max_holding_bars": 384, "planned_time_stop_h4_bars": 8},
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_6"],
            row["mm_net_percentile156"],
            row["producer_net_percentile156"],
            row["mm_net_change_4w"],
            row["prior_d1_return"],
            row["prior_d1_range_atr"],
            row["gc_volume_percentile252"],
            row["gc_volume_z126"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        mm_percentile = float(row["mm_net_percentile156"])
        producer_percentile = float(row["producer_net_percentile156"])
        mm_net_change_4w = float(row["mm_net_change_4w"])
        prior_d1_return = float(row["prior_d1_return"])
        prior_d1_range_atr = float(row["prior_d1_range_atr"])
        volume_percentile = float(row["gc_volume_percentile252"])
        volume_z = float(row["gc_volume_z126"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema_distance_atr = (close - h4_ema40) / h4_atr
        volume_climax = (
            volume_percentile >= self.volume_percentile_threshold
            and volume_z >= self.volume_z_threshold
            and prior_d1_range_atr >= 1.05
        )
        if not volume_climax:
            return None

        if (
            mm_percentile <= 0.35
            and producer_percentile >= 0.65
            and mm_net_change_4w > 0.0
            and prior_d1_return <= -self.prior_day_return_threshold
            and close > open_price
            and close_location >= 0.56
            and h4_return_6 >= -0.0200
            and ema_distance_atr <= 1.20
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema_distance_atr)

        if (
            mm_percentile >= 0.65
            and producer_percentile <= 0.35
            and mm_net_change_4w < 0.0
            and prior_d1_return >= self.prior_day_return_threshold
            and close < open_price
            and close_location <= 0.44
            and h4_return_6 <= 0.0200
            and ema_distance_atr >= -1.20
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema_distance_atr)

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
    ema_distance_atr: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_6": float(row["h4_return_6"]),
        "cot_report_date": str(row["cot_report_date"])[:10],
        "mm_net_oi_share": float(row["mm_net_oi_share"]),
        "producer_net_oi_share": float(row["producer_net_oi_share"]),
        "mm_net_percentile156": float(row["mm_net_percentile156"]),
        "producer_net_percentile156": float(row["producer_net_percentile156"]),
        "mm_net_change_4w": float(row["mm_net_change_4w"]),
        "prior_d1_return": float(row["prior_d1_return"]),
        "prior_d1_range_atr": float(row["prior_d1_range_atr"]),
        "gc_volume": float(row["gc_volume"]),
        "gc_volume_percentile252": float(row["gc_volume_percentile252"]),
        "gc_volume_z126": float(row["gc_volume_z126"]),
        "close_location": close_location,
        "ema_distance_atr": ema_distance_atr,
        "planned_time_stop_h4_bars": 8,
    }
