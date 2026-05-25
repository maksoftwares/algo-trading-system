from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.cot_gold_data import COT_FRAME_KEY
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class CotGoldPositioningReversalV0Strategy(StrategyBase):
    """Research-only CFTC gold positioning reversal candidate."""

    name = "cot_gold_positioning_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.70

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        cot = data_context.get(COT_FRAME_KEY)
        if not isinstance(cot, pd.DataFrame):
            raise ConfigError(
                "cot_gold_positioning_reversal_v0 requires data_context['cot_gold'] "
                "with CFTC gold COT observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))

        cot_features = _cot_features_for_h4(h4, cot)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                cot_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(180, len(h4)):
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
                    reason_code=f"COT_GOLD_POSITIONING_REVERSAL_V0_{direction}",
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
            stop_loss = estimated_entry - 1.25 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.25 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported COT gold direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid COT gold trade plan risk.")

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
                "max_holding_bars": 576,
                "planned_time_stop_h4_bars": 12,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_6"],
            row["mm_net_oi_share"],
            row["producer_net_oi_share"],
            row["mm_net_percentile156"],
            row["producer_net_percentile156"],
            row["mm_net_change_4w"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        mm_percentile = float(row["mm_net_percentile156"])
        producer_percentile = float(row["producer_net_percentile156"])
        mm_net_change_4w = float(row["mm_net_change_4w"])
        if h4_atr <= 0:
            return None

        if (
            mm_percentile <= 0.30
            and producer_percentile >= 0.70
            and mm_net_change_4w > 0.0
            and close > h4_ema40
            and close > open_price
            and h4_return_6 > 0.0
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            mm_percentile >= 0.70
            and producer_percentile <= 0.30
            and mm_net_change_4w < 0.0
            and close < h4_ema40
            and close < open_price
            and h4_return_6 < 0.0
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _cot_features_for_h4(h4: pd.DataFrame, cot: pd.DataFrame) -> pd.DataFrame:
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
    cot_frame["mm_net_percentile156"] = _rolling_last_percentile(
        cot_frame["mm_net_oi_share"],
        156,
    )
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

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
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


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_6": float(row["h4_return_6"]),
        "cot_report_date": str(row["cot_report_date"])[:10],
        "open_interest_all": float(row["open_interest_all"]),
        "mm_net_oi_share": float(row["mm_net_oi_share"]),
        "producer_net_oi_share": float(row["producer_net_oi_share"]),
        "mm_net_percentile156": float(row["mm_net_percentile156"]),
        "producer_net_percentile156": float(row["producer_net_percentile156"]),
        "mm_net_change_4w": float(row["mm_net_change_4w"]),
    }
