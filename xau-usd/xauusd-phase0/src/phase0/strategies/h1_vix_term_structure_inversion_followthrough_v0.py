from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)
from phase0.strategies.h1_vix_term_structure_inversion_reversal_v0 import _term_features_for_h1
from phase0.vix_term_structure_data import VIX_TERM_STRUCTURE_FRAME_KEY


class H1VixTermStructureInversionFollowthroughV0Strategy(StrategyBase):
    """Research-only H1 VIX term-structure inversion followthrough candidate."""

    name = "h1_vix_term_structure_inversion_followthrough_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50
    decision_hours_utc = frozenset({7, 9, 11, 13, 15, 17, 19, 21})

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        term = data_context.get(VIX_TERM_STRUCTURE_FRAME_KEY)
        if not isinstance(term, pd.DataFrame):
            raise ConfigError(
                "h1_vix_term_structure_inversion_followthrough_v0 requires "
                "data_context['vix_term_structure'] with FRED VIXCLS/VXVCLS observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        if "h1_atr14" not in h1:
            h1["h1_atr14"] = atr(high, low, close, 14)
        if "h1_ema50" not in h1:
            h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_24"] = np.log(close / close.shift(24))
        h1["h1_return_72"] = np.log(close / close.shift(72))

        term_features = _term_features_for_h1(h1, term)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                term_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
            ],
            axis=1,
        )
        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(100, len(h1)):
            row = h1.iloc[position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            if timestamp.hour not in self.decision_hours_utc:
                continue

            setup = self._setup_at_row(row)
            if setup is None:
                continue

            day_direction = (timestamp.strftime("%Y-%m-%d"), str(setup["direction"]))
            if day_direction in used_day_direction:
                continue
            used_day_direction.add(day_direction)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H1_VIX_TERM_STRUCTURE_INVERSION_FOLLOWTHROUGH_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["h1_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.05 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.05 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported VIX term-structure followthrough direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid VIX term-structure followthrough trade plan risk.")

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
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "max_holding_bars": 144,
                "planned_time_stop_h1_bars": 12,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h1_atr14"],
            row["h1_ema50"],
            row["h1_return_24"],
            row["h1_return_72"],
            row["vix_close"],
            row["vxv_close"],
            row["vix_vxv_ratio"],
            row["vix_vxv_ratio_change_5d"],
            row["vix_vxv_ratio_change_z126"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        h1_ema50 = float(row["h1_ema50"])
        h1_return_24 = float(row["h1_return_24"])
        h1_return_72 = float(row["h1_return_72"])
        term_ratio = float(row["vix_vxv_ratio"])
        term_change = float(row["vix_vxv_ratio_change_5d"])
        term_change_z = float(row["vix_vxv_ratio_change_z126"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        inversion_panic = term_ratio >= 1.02 and (term_change >= 0.025 or term_change_z >= 0.65)
        contango_relief = term_ratio <= 0.92 and (term_change <= -0.020 or term_change_z <= -0.65)

        if (
            inversion_panic
            and h1_return_24 >= 0.004
            and h1_return_72 <= 0.055
            and close > h1_ema50
            and close > open_price
            and close_location >= 0.58
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            contango_relief
            and h1_return_24 <= -0.004
            and h1_return_72 >= -0.055
            and close < h1_ema50
            and close < open_price
            and close_location <= 0.42
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema50": float(row["h1_ema50"]),
        "h1_return_24": float(row["h1_return_24"]),
        "h1_return_72": float(row["h1_return_72"]),
        "close_location": close_location,
        "vix_close": float(row["vix_close"]),
        "vxv_close": float(row["vxv_close"]),
        "vix_vxv_ratio": float(row["vix_vxv_ratio"]),
        "vix_vxv_ratio_change_5d": float(row["vix_vxv_ratio_change_5d"]),
        "vix_vxv_ratio_change_z126": float(row["vix_vxv_ratio_change_z126"]),
    }
