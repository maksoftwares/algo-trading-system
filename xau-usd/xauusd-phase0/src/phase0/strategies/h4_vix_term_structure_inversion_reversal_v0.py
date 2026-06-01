from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h1_vix_term_structure_inversion_reversal_v0 import _term_features_for_h1
from phase0.vix_term_structure_data import VIX_TERM_STRUCTURE_FRAME_KEY


class H4VixTermStructureInversionReversalV0Strategy(StrategyBase):
    """Research-only H4 VIX/VXV term-structure inversion reversal candidate."""

    name = "h4_vix_term_structure_inversion_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.55

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        term = data_context.get(VIX_TERM_STRUCTURE_FRAME_KEY)
        if not isinstance(term, pd.DataFrame):
            raise ConfigError(
                "h4_vix_term_structure_inversion_reversal_v0 requires "
                "data_context['vix_term_structure'] with FRED VIXCLS/VXVCLS observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(high, low, close, 14)
        h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_12"] = np.log(close / close.shift(12))

        term_features = _term_features_for_h1(h4, term)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                term_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
        used_week_direction: set[tuple[str, str]] = set()

        for position in range(120, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            iso = timestamp.isocalendar()
            direction = str(setup["direction"])
            key = (f"{iso.year}-W{iso.week:02d}", direction)
            if key in used_week_direction:
                continue
            used_week_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_VIX_TERM_STRUCTURE_INVERSION_REVERSAL_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_week": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.15 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.15 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported VIX/VXV H4 inversion reversal direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid VIX/VXV H4 inversion reversal trade plan risk.")

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
                "max_holding_bars": 288,
                "planned_time_stop_h4_bars": 6,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_12"],
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
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_12 = float(row["h4_return_12"])
        term_ratio = float(row["vix_vxv_ratio"])
        term_change = float(row["vix_vxv_ratio_change_5d"])
        term_change_z = float(row["vix_vxv_ratio_change_z126"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        inversion_panic = term_ratio >= 1.02 and (term_change >= 0.025 or term_change_z >= 0.65)
        contango_relief = term_ratio <= 0.92 and (term_change <= -0.020 or term_change_z <= -0.65)

        if (
            inversion_panic
            and h4_return_12 >= 0.006
            and close < open_price
            and close_location <= 0.40
            and close >= h4_ema40 - 0.80 * h4_atr
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        if (
            contango_relief
            and h4_return_12 <= -0.006
            and close > open_price
            and close_location >= 0.60
            and close <= h4_ema40 + 0.80 * h4_atr
        ):
            return _setup_metadata(row, "LONG", close, close_location)

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
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_12": float(row["h4_return_12"]),
        "close_location": close_location,
        "vix_close": float(row["vix_close"]),
        "vxv_close": float(row["vxv_close"]),
        "vix_vxv_ratio": float(row["vix_vxv_ratio"]),
        "vix_vxv_ratio_change_5d": float(row["vix_vxv_ratio_change_5d"]),
        "vix_vxv_ratio_change_z126": float(row["vix_vxv_ratio_change_z126"]),
    }
