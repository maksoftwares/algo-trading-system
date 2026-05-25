from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.credit_spread_data import CREDIT_SPREAD_FRAME_KEY
from phase0.data_contracts import Signal, TradePlan
from phase0.financial_conditions_data import FINANCIAL_CONDITIONS_FRAME_KEY
from phase0.gvz_volatility_data import GVZ_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.inflation_expectations_data import INFLATION_EXPECTATIONS_FRAME_KEY
from phase0.macro_real_yield_data import MACRO_FRAME_KEY
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)
from phase0.treasury_curve_data import TREASURY_CURVE_FRAME_KEY
from phase0.vix_risk_data import VIX_FRAME_KEY


class H4MacroCompositeRiskStateV0Strategy(StrategyBase):
    """Research-only fixed macro composite risk-state candidate."""

    name = "h4_macro_composite_risk_state_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.65

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        macro_inputs = _require_macro_inputs(data_context)

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))

        macro_features = _macro_features_for_h4(h4, macro_inputs)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
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
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(100, len(h4)):
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
                    reason_code=f"H4_MACRO_COMPOSITE_RISK_STATE_V0_{direction}",
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
            raise ConfigError(f"Unsupported macro composite direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid macro composite trade plan risk.")

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
                "max_holding_bars": 432,
                "planned_time_stop_h4_bars": 9,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_6"],
            row["macro_composite_score"],
            row["macro_bull_votes"],
            row["macro_bear_votes"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        composite_score = float(row["macro_composite_score"])
        if h4_atr <= 0:
            return None

        if composite_score >= 3.0 and close > h4_ema40 and close > open_price and h4_return_6 > 0.0:
            return _setup_metadata(row, "LONG", close)

        if composite_score <= -3.0 and close < h4_ema40 and close < open_price and h4_return_6 < 0.0:
            return _setup_metadata(row, "SHORT", close)

        return None


def _require_macro_inputs(data_context: dict[str, Any]) -> dict[str, pd.DataFrame]:
    required = {
        MACRO_FRAME_KEY: "real-yield/dollar macro",
        INFLATION_EXPECTATIONS_FRAME_KEY: "breakeven inflation",
        TREASURY_CURVE_FRAME_KEY: "Treasury curve",
        CREDIT_SPREAD_FRAME_KEY: "credit spread",
        VIX_FRAME_KEY: "VIX",
        GVZ_FRAME_KEY: "GVZ",
        FINANCIAL_CONDITIONS_FRAME_KEY: "financial conditions",
    }
    frames: dict[str, pd.DataFrame] = {}
    for key, label in required.items():
        frame = data_context.get(key)
        if not isinstance(frame, pd.DataFrame):
            raise ConfigError(f"h4_macro_composite_risk_state_v0 requires {label} frame {key!r}.")
        frames[key] = frame
    return frames


def _macro_features_for_h4(h4: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    macro = _base_frame(frames[MACRO_FRAME_KEY], ["real_yield_10y", "dollar_index_broad"])
    inflation = _base_frame(
        frames[INFLATION_EXPECTATIONS_FRAME_KEY],
        ["breakeven_5y", "breakeven_10y"],
    )
    treasury = _base_frame(frames[TREASURY_CURVE_FRAME_KEY], ["dgs2", "dgs10", "treasury_10y2y"])
    credit = _base_frame(frames[CREDIT_SPREAD_FRAME_KEY], ["baa10y", "aaa10y"])
    vix = _base_frame(frames[VIX_FRAME_KEY], ["vix_close"])
    gvz = _base_frame(frames[GVZ_FRAME_KEY], ["gvz_close"])
    conditions = _base_frame(frames[FINANCIAL_CONDITIONS_FRAME_KEY], ["nfci", "anfci"])

    daily = macro
    for frame in (inflation, treasury, credit, vix, gvz, conditions):
        daily = pd.merge_asof(
            daily.sort_values("timestamp_utc"),
            frame.sort_values("timestamp_utc"),
            on="timestamp_utc",
            direction="backward",
        )
    daily = daily.ffill().dropna().reset_index(drop=True)
    daily["credit_quality_spread"] = daily["baa10y"] - daily["aaa10y"]

    daily["real_yield_change_20d"] = daily["real_yield_10y"] - daily["real_yield_10y"].shift(20)
    daily["dollar_change_20d"] = (
        daily["dollar_index_broad"] - daily["dollar_index_broad"].shift(20)
    )
    daily["breakeven_5y_change_20d"] = daily["breakeven_5y"] - daily["breakeven_5y"].shift(20)
    daily["dgs2_change_20d"] = daily["dgs2"] - daily["dgs2"].shift(20)
    daily["treasury_10y2y_change_20d"] = (
        daily["treasury_10y2y"] - daily["treasury_10y2y"].shift(20)
    )
    daily["baa10y_change_20d"] = daily["baa10y"] - daily["baa10y"].shift(20)
    daily["vix_change_20d"] = daily["vix_close"] - daily["vix_close"].shift(20)
    daily["gvz_change_20d"] = daily["gvz_close"] - daily["gvz_close"].shift(20)
    daily["nfci_change_4obs"] = daily["nfci"] - daily["nfci"].shift(4)

    daily["macro_bull_votes"] = (
        (daily["real_yield_change_20d"] <= -0.15).astype(int)
        + (daily["dollar_change_20d"] <= -1.00).astype(int)
        + (daily["breakeven_5y_change_20d"] >= 0.10).astype(int)
        + (
            (daily["dgs2_change_20d"] <= -0.15)
            & (daily["treasury_10y2y_change_20d"] >= 0.03)
        ).astype(int)
        + (daily["baa10y_change_20d"] >= 0.10).astype(int)
        + ((daily["vix_change_20d"] >= 3.00) | (daily["gvz_change_20d"] >= 3.00)).astype(int)
        + (daily["nfci_change_4obs"] >= 0.10).astype(int)
    )
    daily["macro_bear_votes"] = (
        (daily["real_yield_change_20d"] >= 0.15).astype(int)
        + (daily["dollar_change_20d"] >= 1.00).astype(int)
        + (daily["breakeven_5y_change_20d"] <= -0.10).astype(int)
        + (
            (daily["dgs2_change_20d"] >= 0.15)
            & (daily["treasury_10y2y_change_20d"] <= -0.03)
        ).astype(int)
        + (daily["baa10y_change_20d"] <= -0.10).astype(int)
        + ((daily["vix_change_20d"] <= -3.00) | (daily["gvz_change_20d"] <= -3.00)).astype(int)
        + (daily["nfci_change_4obs"] <= -0.10).astype(int)
    )
    daily["macro_composite_score"] = daily["macro_bull_votes"] - daily["macro_bear_votes"]

    feature_columns = [
        "macro_bull_votes",
        "macro_bear_votes",
        "macro_composite_score",
        "real_yield_change_20d",
        "dollar_change_20d",
        "breakeven_5y_change_20d",
        "dgs2_change_20d",
        "treasury_10y2y_change_20d",
        "baa10y_change_20d",
        "vix_change_20d",
        "gvz_change_20d",
        "nfci_change_4obs",
    ]
    daily[feature_columns] = daily[feature_columns].shift(1)

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        daily[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _base_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    output = frame[["timestamp_utc", *columns]].copy()
    output["timestamp_utc"] = pd.to_datetime(output["timestamp_utc"], utc=True, errors="coerce")
    for column in columns:
        output[column] = pd.to_numeric(output[column], errors="coerce")
    return output.dropna().sort_values("timestamp_utc").reset_index(drop=True)


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_6": float(row["h4_return_6"]),
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
