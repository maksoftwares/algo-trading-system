from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.cme_cvol_gold_data import CME_CVOL_GOLD_FRAME_KEY
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


class H4CmeCvolSkewReversalV0Strategy(StrategyBase):
    """Research-only H4 reversal candidate using CME Gold CVOL skew/variance data."""

    name = "h4_cme_cvol_skew_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.60

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        cvol = data_context.get(CME_CVOL_GOLD_FRAME_KEY)
        if not isinstance(cvol, pd.DataFrame):
            raise ConfigError(
                "h4_cme_cvol_skew_reversal_v0 requires "
                "data_context['cme_cvol_gold'] with licensed CME Gold CVOL/skew observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_12"] = np.log(close / close.shift(12))

        cvol_features = _cme_cvol_features_for_h4(h4, cvol)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                cvol_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(80, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
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
                    reason_code=f"H4_CME_CVOL_SKEW_REVERSAL_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_day": day_direction[0]},
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
            raise ConfigError(f"Unsupported CME CVOL skew direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid CME CVOL skew trade plan risk.")

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
            row["gold_cvol"],
            row["gold_upvar"],
            row["gold_downvar"],
            row["gold_skew"],
            row["cvol_percentile252"],
            row["down_up_imbalance_z126"],
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
        cvol_percentile = float(row["cvol_percentile252"])
        imbalance_z = float(row["down_up_imbalance_z126"])
        down_up_ratio = float(row["down_up_ratio"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        elevated_options_risk = cvol_percentile >= 0.55
        downside_skew_stress = imbalance_z >= 0.70 or down_up_ratio >= 1.12
        upside_skew_stress = imbalance_z <= -0.70 or down_up_ratio <= 0.90

        if (
            elevated_options_risk
            and downside_skew_stress
            and h4_return_12 <= -0.0035
            and close > open_price
            and close_location >= 0.55
            and close <= h4_ema40 + 0.45 * h4_atr
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            elevated_options_risk
            and upside_skew_stress
            and h4_return_12 >= 0.0035
            and close < open_price
            and close_location <= 0.45
            and close >= h4_ema40 - 0.45 * h4_atr
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _cme_cvol_features_for_h4(h4: pd.DataFrame, cvol: pd.DataFrame) -> pd.DataFrame:
    cvol_frame = cvol[
        [
            "timestamp_utc",
            "gold_cvol",
            "gold_upvar",
            "gold_downvar",
            "gold_skew",
            "gold_atm",
            "gold_convexity",
        ]
    ].copy()
    cvol_frame["timestamp_utc"] = pd.to_datetime(
        cvol_frame["timestamp_utc"],
        utc=True,
        errors="coerce",
    )
    for column in (
        "gold_cvol",
        "gold_upvar",
        "gold_downvar",
        "gold_skew",
        "gold_atm",
        "gold_convexity",
    ):
        cvol_frame[column] = pd.to_numeric(cvol_frame[column], errors="coerce")
    cvol_frame = cvol_frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    cvol_frame["down_up_imbalance"] = cvol_frame["gold_downvar"] - cvol_frame["gold_upvar"]
    cvol_frame["down_up_ratio"] = cvol_frame["gold_downvar"] / cvol_frame["gold_upvar"].replace(
        0.0, np.nan
    )
    cvol_frame["cvol_percentile252"] = _rolling_percentile(cvol_frame["gold_cvol"], 252)
    cvol_frame["down_up_imbalance_z126"] = _rolling_zscore(
        cvol_frame["down_up_imbalance"],
        126,
    )
    cvol_frame["gold_skew_z126"] = _rolling_zscore(cvol_frame["gold_skew"], 126)

    feature_columns = [
        "gold_cvol",
        "gold_upvar",
        "gold_downvar",
        "gold_skew",
        "gold_atm",
        "gold_convexity",
        "down_up_imbalance",
        "down_up_ratio",
        "cvol_percentile252",
        "down_up_imbalance_z126",
        "gold_skew_z126",
    ]
    cvol_frame[feature_columns] = cvol_frame[feature_columns].shift(1)

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        cvol_frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
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


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    minimum = max(30, window // 2)
    mean = series.rolling(window, min_periods=minimum).mean()
    std = series.rolling(window, min_periods=minimum).std()
    return (series - mean) / std.replace(0.0, np.nan)


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
        "gold_cvol": float(row["gold_cvol"]),
        "gold_upvar": float(row["gold_upvar"]),
        "gold_downvar": float(row["gold_downvar"]),
        "gold_skew": float(row["gold_skew"]),
        "gold_atm": float(row["gold_atm"]),
        "gold_convexity": float(row["gold_convexity"]),
        "down_up_imbalance": float(row["down_up_imbalance"]),
        "down_up_ratio": float(row["down_up_ratio"]),
        "cvol_percentile252": float(row["cvol_percentile252"]),
        "down_up_imbalance_z126": float(row["down_up_imbalance_z126"]),
        "gold_skew_z126": float(row["gold_skew_z126"]),
    }
