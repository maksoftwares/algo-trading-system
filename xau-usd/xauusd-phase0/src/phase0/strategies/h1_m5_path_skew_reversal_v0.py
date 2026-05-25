from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H1M5PathSkewReversalV0Strategy(StrategyBase):
    """Research-only H1/M5 path-skew reversal candidate."""

    name = "h1_m5_path_skew_reversal_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        m5 = require_frame(context, "M5")

        if "atr14" not in h1:
            h1["atr14"] = atr(h1["high"], h1["low"], h1["close"], 14)

        path_features = _m5_path_features(m5)
        h1 = h1.merge(path_features, on="timestamp_utc", how="left")
        h1["m5_first_third_return_atr"] = pd.to_numeric(
            h1["m5_first_third_return"],
            errors="coerce",
        ) / pd.to_numeric(h1["atr14"], errors="coerce").replace(0.0, pd.NA)
        h1["m5_last_third_return_atr"] = pd.to_numeric(
            h1["m5_last_third_return"],
            errors="coerce",
        ) / pd.to_numeric(h1["atr14"], errors="coerce").replace(0.0, pd.NA)
        h1["h1_range_atr"] = (
            pd.to_numeric(h1["high"], errors="coerce") - pd.to_numeric(h1["low"], errors="coerce")
        ) / pd.to_numeric(h1["atr14"], errors="coerce").replace(0.0, pd.NA)
        h1["h1_close_position"] = (
            pd.to_numeric(h1["close"], errors="coerce") - pd.to_numeric(h1["low"], errors="coerce")
        ) / (
            pd.to_numeric(h1["high"], errors="coerce") - pd.to_numeric(h1["low"], errors="coerce")
        ).replace(0.0, pd.NA)

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

        for position in range(40, len(h1)):
            row = h1.iloc[position]
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
                    reason_code=f"H1_M5_PATH_SKEW_REVERSAL_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["atr14"])

        if direction == "LONG":
            stop_loss = float(signal.metadata["h1_low"]) - 0.25 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.45 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["h1_high"]) + 0.25 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.45 * risk_price
        else:
            raise ConfigError(f"Unsupported H1/M5 path-skew direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1/M5 path-skew trade plan risk.")

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
            risk_reward=1.45,
            reason_code=signal.reason_code,
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "max_holding_bars": 288,
                "planned_time_stop_h1_bars": 24,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["m5_count"],
            row["h1_range_atr"],
            row["h1_close_position"],
            row["m5_first_third_return_atr"],
            row["m5_last_third_return_atr"],
            row["m5_path_efficiency"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        atr14 = float(row["atr14"])
        m5_count = int(row["m5_count"])
        h1_range_atr = float(row["h1_range_atr"])
        h1_close_position = float(row["h1_close_position"])
        first_third = float(row["m5_first_third_return_atr"])
        last_third = float(row["m5_last_third_return_atr"])
        path_efficiency = float(row["m5_path_efficiency"])
        if atr14 <= 0 or m5_count < 10:
            return None
        if not (0.80 <= h1_range_atr <= 3.80):
            return None
        if path_efficiency >= 0.88:
            return None

        h1_move_atr = (close - open_price) / atr14
        if (
            h1_move_atr <= -0.35
            and first_third <= -0.20
            and last_third >= 0.16
            and h1_close_position >= 0.28
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            h1_move_atr >= 0.35
            and first_third >= 0.20
            and last_third <= -0.16
            and h1_close_position <= 0.72
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _m5_path_features(m5: pd.DataFrame) -> pd.DataFrame:
    prepared = m5.copy()
    prepared["timestamp_utc"] = pd.to_datetime(prepared["timestamp_utc"], utc=True, errors="coerce")
    prepared = prepared.dropna(subset=["timestamp_utc"]).sort_values("timestamp_utc")
    prepared["_h1_timestamp_utc"] = prepared["timestamp_utc"].dt.ceil("h")

    rows: list[dict[str, object]] = []
    for timestamp, group in prepared.groupby("_h1_timestamp_utc", sort=True):
        chunk = group.sort_values("timestamp_utc").reset_index(drop=True)
        if len(chunk) < 2:
            continue
        open_first = float(chunk.iloc[0]["open"])
        close_last = float(chunk.iloc[-1]["close"])
        close_steps = pd.to_numeric(chunk["close"], errors="coerce")
        path_distance = close_steps.diff().abs().sum()
        path_distance += abs(float(chunk.iloc[0]["close"]) - open_first)
        if path_distance <= 0:
            path_efficiency = 1.0
        else:
            path_efficiency = abs(close_last - open_first) / path_distance

        first_end_position = max(0, min(len(chunk) - 1, 3))
        last_start_position = max(0, len(chunk) - 4)
        high = float(pd.to_numeric(chunk["high"], errors="coerce").max())
        low = float(pd.to_numeric(chunk["low"], errors="coerce").min())
        bar_range = max(high - low, 0.0)
        rows.append(
            {
                "timestamp_utc": pd.Timestamp(timestamp),
                "m5_count": int(len(chunk)),
                "m5_first_third_return": float(chunk.iloc[first_end_position]["close"]) - open_first,
                "m5_last_third_return": close_last - float(chunk.iloc[last_start_position]["open"]),
                "m5_path_efficiency": float(path_efficiency),
                "m5_internal_range": bar_range,
            }
        )

    features = pd.DataFrame(rows)
    if features.empty:
        return pd.DataFrame(
            columns=[
                "timestamp_utc",
                "m5_count",
                "m5_first_third_return",
                "m5_last_third_return",
                "m5_path_efficiency",
                "m5_internal_range",
            ]
        )
    return features


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h1_open": float(row["open"]),
        "h1_high": float(row["high"]),
        "h1_low": float(row["low"]),
        "h1_close": float(row["close"]),
        "atr14": float(row["atr14"]),
        "m5_count": int(row["m5_count"]),
        "h1_range_atr": float(row["h1_range_atr"]),
        "h1_close_position": float(row["h1_close_position"]),
        "m5_first_third_return_atr": float(row["m5_first_third_return_atr"]),
        "m5_last_third_return_atr": float(row["m5_last_third_return_atr"]),
        "m5_path_efficiency": float(row["m5_path_efficiency"]),
    }
