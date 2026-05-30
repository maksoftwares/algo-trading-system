from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.financial_conditions_data import FINANCIAL_CONDITIONS_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H1FinancialConditionsShockReversalV0Strategy(StrategyBase):
    """Research-only H1 financial-conditions shock reversal candidate."""

    name = "h1_financial_conditions_shock_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.45
    decision_hours_utc = frozenset({7, 9, 11, 13, 15, 17, 19, 21})

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        conditions = data_context.get(FINANCIAL_CONDITIONS_FRAME_KEY)
        if not isinstance(conditions, pd.DataFrame):
            raise ConfigError(
                "h1_financial_conditions_shock_reversal_v0 requires "
                "data_context['financial_conditions'] with FRED NFCI/ANFCI observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        if "h1_atr14" not in h1:
            h1["h1_atr14"] = atr(high, low, close, 14)
        if "h1_ema50" not in h1:
            h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_8"] = np.log(close / close.shift(8))
        h1["h1_return_24"] = np.log(close / close.shift(24))

        condition_features = _financial_conditions_features_for_h1(h1, conditions)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                condition_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
                    reason_code=f"H1_FINANCIAL_CONDITIONS_SHOCK_REVERSAL_V0_{direction}",
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
            stop_loss = estimated_entry - 1.00 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.00 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(
                f"Unsupported financial-conditions shock reversal direction {signal.direction!r}."
            )

        if risk_price <= 0:
            raise ConfigError("Invalid financial-conditions shock reversal trade plan risk.")

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
                "max_holding_bars": 216,
                "planned_time_stop_h1_bars": 18,
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
            row["h1_return_8"],
            row["h1_return_24"],
            row["nfci"],
            row["anfci"],
            row["nfci_change_4w"],
            row["anfci_change_4w"],
            row["nfci_percentile156"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        h1_ema50 = float(row["h1_ema50"])
        h1_return_8 = float(row["h1_return_8"])
        h1_return_24 = float(row["h1_return_24"])
        nfci_change_4w = float(row["nfci_change_4w"])
        anfci_change_4w = float(row["anfci_change_4w"])
        nfci_percentile = float(row["nfci_percentile156"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        tightening_shock = (
            nfci_change_4w >= 0.12
            or anfci_change_4w >= 0.10
            or nfci_percentile >= 0.65
        )
        easing_shock = (
            nfci_change_4w <= -0.12
            or anfci_change_4w <= -0.10
            or nfci_percentile <= 0.35
        )

        if (
            tightening_shock
            and h1_return_24 <= -0.004
            and h1_return_8 >= -0.002
            and close > open_price
            and close_location >= 0.60
            and close <= h1_ema50 * 1.015
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            easing_shock
            and h1_return_24 >= 0.004
            and h1_return_8 <= 0.002
            and close < open_price
            and close_location <= 0.40
            and close >= h1_ema50 * 0.985
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _financial_conditions_features_for_h1(
    h1: pd.DataFrame,
    financial_conditions: pd.DataFrame,
) -> pd.DataFrame:
    conditions_frame = financial_conditions[["timestamp_utc", "nfci", "anfci"]].copy()
    conditions_frame["timestamp_utc"] = pd.to_datetime(
        conditions_frame["timestamp_utc"],
        utc=True,
        errors="coerce",
    )
    conditions_frame["nfci"] = pd.to_numeric(conditions_frame["nfci"], errors="coerce")
    conditions_frame["anfci"] = pd.to_numeric(conditions_frame["anfci"], errors="coerce")
    conditions_frame = conditions_frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    conditions_frame["nfci_change_4w"] = (
        conditions_frame["nfci"] - conditions_frame["nfci"].shift(4)
    )
    conditions_frame["anfci_change_4w"] = (
        conditions_frame["anfci"] - conditions_frame["anfci"].shift(4)
    )
    conditions_frame["nfci_percentile156"] = _rolling_percentile(conditions_frame["nfci"], 156)

    feature_columns = [
        "nfci",
        "anfci",
        "nfci_change_4w",
        "anfci_change_4w",
        "nfci_percentile156",
    ]
    conditions_frame[feature_columns] = conditions_frame[feature_columns].shift(1)

    h1_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h1)),
        }
    )
    merged = pd.merge_asof(
        h1_times.sort_values("timestamp_utc"),
        conditions_frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _rolling_percentile(series: pd.Series, window: int) -> pd.Series:
    minimum = max(40, window // 2)

    def percentile(values: np.ndarray) -> float:
        current = values[-1]
        return float(np.sum(values <= current) / len(values))

    return series.rolling(window, min_periods=minimum).apply(percentile, raw=True)


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
        "h1_return_8": float(row["h1_return_8"]),
        "h1_return_24": float(row["h1_return_24"]),
        "close_location": close_location,
        "nfci": float(row["nfci"]),
        "anfci": float(row["anfci"]),
        "nfci_change_4w": float(row["nfci_change_4w"]),
        "anfci_change_4w": float(row["anfci_change_4w"]),
        "nfci_percentile156": float(row["nfci_percentile156"]),
    }
