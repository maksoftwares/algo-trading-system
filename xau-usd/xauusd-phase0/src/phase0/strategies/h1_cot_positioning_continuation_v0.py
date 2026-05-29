from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.cot_gold_data import COT_FRAME_KEY
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H1CotPositioningContinuationV0Strategy(StrategyBase):
    """Research-only CFTC gold positioning continuation candidate with H1 timing."""

    name = "h1_cot_positioning_continuation_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50
    decision_hours_utc = {7, 11, 15, 19}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        cot = data_context.get(COT_FRAME_KEY)
        if not isinstance(cot, pd.DataFrame):
            raise ConfigError(
                "h1_cot_positioning_continuation_v0 requires data_context['cot_gold'] "
                "with CFTC gold COT observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        if "h1_atr14" not in h1:
            h1["h1_atr14"] = atr(high, low, close, 14)
        if "h1_ema21" not in h1:
            h1["h1_ema21"] = ema(close, 21)
        if "h1_ema50" not in h1:
            h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_24"] = np.log(close / close.shift(24))

        cot_features = _cot_features_for_h1(h1, cot)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                cot_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(180, len(h1)):
            row = h1.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            signal_day = timestamp.strftime("%Y-%m-%d")
            direction = str(setup["direction"])
            key = (signal_day, direction)
            if key in used_day_direction:
                continue
            used_day_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H1_COT_POSITIONING_CONTINUATION_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": signal_day},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["h1_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.15 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.15 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported COT continuation direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid COT continuation trade plan risk.")

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
        timestamp = pd.Timestamp(row["timestamp_utc"])
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        if timestamp.hour not in self.decision_hours_utc:
            return None

        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h1_atr14"],
            row["h1_ema21"],
            row["h1_ema50"],
            row["h1_return_24"],
            row["mm_net_oi_share"],
            row["producer_net_oi_share"],
            row["mm_net_percentile156"],
            row["producer_net_percentile156"],
            row["mm_net_change_4w"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        ema21 = float(row["h1_ema21"])
        ema50 = float(row["h1_ema50"])
        h1_return_24 = float(row["h1_return_24"])
        mm_percentile = float(row["mm_net_percentile156"])
        producer_percentile = float(row["producer_net_percentile156"])
        mm_net_change_4w = float(row["mm_net_change_4w"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        near_ema21 = low <= ema21 + 0.45 * h1_atr and high >= ema21 - 0.35 * h1_atr

        if (
            mm_percentile >= 0.60
            and producer_percentile <= 0.55
            and mm_net_change_4w > 0.0
            and close >= ema50
            and ema21 >= ema50
            and close >= ema21 - 0.10 * h1_atr
            and h1_return_24 >= -0.0020
            and near_ema21
            and close > open_price
            and close_location >= 0.55
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            mm_percentile <= 0.40
            and producer_percentile >= 0.45
            and mm_net_change_4w < 0.0
            and close <= ema50
            and ema21 <= ema50
            and close <= ema21 + 0.10 * h1_atr
            and h1_return_24 <= 0.0020
            and near_ema21
            and close < open_price
            and close_location <= 0.45
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _cot_features_for_h1(h1: pd.DataFrame, cot: pd.DataFrame) -> pd.DataFrame:
    cot_frame = cot.copy()
    cot_frame["report_date"] = pd.to_datetime(cot_frame["report_date"], utc=True, errors="coerce")
    numeric_columns = [
        "open_interest_all",
        "producer_long_all",
        "producer_short_all",
        "managed_money_long_all",
        "managed_money_short_all",
    ]
    for column in numeric_columns:
        cot_frame[column] = pd.to_numeric(cot_frame[column], errors="coerce")
    cot_frame = cot_frame.dropna(subset=["report_date", *numeric_columns]).sort_values("report_date")
    cot_frame = cot_frame.drop_duplicates("report_date").reset_index(drop=True)

    open_interest = cot_frame["open_interest_all"].replace(0.0, np.nan)
    cot_frame["mm_net_oi_share"] = (
        cot_frame["managed_money_long_all"] - cot_frame["managed_money_short_all"]
    ) / open_interest
    cot_frame["producer_net_oi_share"] = (
        cot_frame["producer_long_all"] - cot_frame["producer_short_all"]
    ) / open_interest
    cot_frame["mm_net_percentile156"] = _rolling_last_percentile(cot_frame["mm_net_oi_share"], 156)
    cot_frame["producer_net_percentile156"] = _rolling_last_percentile(
        cot_frame["producer_net_oi_share"],
        156,
    )
    cot_frame["mm_net_change_4w"] = cot_frame["mm_net_oi_share"] - cot_frame[
        "mm_net_oi_share"
    ].shift(4)
    cot_frame["usable_from_utc"] = cot_frame["report_date"] + pd.Timedelta(days=6)
    feature_columns = [
        "report_date",
        "mm_net_oi_share",
        "producer_net_oi_share",
        "mm_net_percentile156",
        "producer_net_percentile156",
        "mm_net_change_4w",
        "open_interest_all",
    ]

    h1_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h1)),
        }
    )
    merged = pd.merge_asof(
        h1_times.sort_values("timestamp_utc"),
        cot_frame[["usable_from_utc", *feature_columns]].sort_values("usable_from_utc"),
        left_on="timestamp_utc",
        right_on="usable_from_utc",
        direction="backward",
    )
    merged = merged.rename(columns={"report_date": "cot_report_date"})
    return (
        merged.sort_values("_row_order")
        .drop(columns=["_row_order", "usable_from_utc"])
        .reset_index(drop=True)
    )


def _rolling_last_percentile(series: pd.Series, window: int) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")

    def percentile(window_values: np.ndarray) -> float:
        valid = window_values[np.isfinite(window_values)]
        if len(valid) == 0:
            return np.nan
        current = valid[-1]
        return float((valid <= current).sum() / len(valid))

    return values.rolling(window, min_periods=max(52, window // 2)).apply(percentile, raw=True)


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
        "h1_ema21": float(row["h1_ema21"]),
        "h1_ema50": float(row["h1_ema50"]),
        "h1_return_24": float(row["h1_return_24"]),
        "cot_report_date": str(row["cot_report_date"])[:10],
        "open_interest_all": float(row["open_interest_all"]),
        "mm_net_oi_share": float(row["mm_net_oi_share"]),
        "producer_net_oi_share": float(row["producer_net_oi_share"]),
        "mm_net_percentile156": float(row["mm_net_percentile156"]),
        "producer_net_percentile156": float(row["producer_net_percentile156"]),
        "mm_net_change_4w": float(row["mm_net_change_4w"]),
        "close_location": close_location,
    }
