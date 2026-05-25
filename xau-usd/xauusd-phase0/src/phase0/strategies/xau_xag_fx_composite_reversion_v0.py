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


class XauXagFxCompositeReversionV0Strategy(StrategyBase):
    """Research-only XAU/XAG plus FX-proxy composite reversion candidate."""

    name = "xau_xag_fx_composite_reversion_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.55

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        relative_value = data_context.get("relative_value")
        intermarket_proxy = data_context.get("intermarket_proxy")
        if not isinstance(relative_value, dict):
            raise ConfigError(
                "xau_xag_fx_composite_reversion_v0 requires data_context['relative_value'] "
                "with an XAGUSD H1 frame."
            )
        if not isinstance(intermarket_proxy, dict):
            raise ConfigError(
                "xau_xag_fx_composite_reversion_v0 requires data_context['intermarket_proxy'] "
                "with EURUSD and USDJPY H1 frames."
            )

        xag = _proxy_frame(relative_value, "XAGUSD", self.name)
        eurusd = _proxy_frame(intermarket_proxy, "EURUSD", self.name)
        usdjpy = _proxy_frame(intermarket_proxy, "USDJPY", self.name)

        if "xau_atr14" not in h1:
            h1["xau_atr14"] = atr(h1["high"], h1["low"], h1["close"], 14)
        if "xau_ema20" not in h1:
            h1["xau_ema20"] = ema(h1["close"], 20)

        features = _composite_features(h1, xag, eurusd, usdjpy)
        h1 = h1.merge(features, on="timestamp_utc", how="left")
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

        for position in range(500, len(h1)):
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
                    reason_code=f"XAU_XAG_FX_COMPOSITE_REVERSION_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["xau_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.05 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.05 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported XAU/XAG FX composite direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid XAU/XAG FX composite trade plan risk.")

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
                "planned_time_stop_h1_bars": 24,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["close"],
            row["xau_atr14"],
            row["xau_ema20"],
            row["xau_xag_ratio_z"],
            row["xau_xag_residual_z"],
            row["ratio_z_change_3h"],
            row["usd_proxy_return_24h"],
            row["usd_proxy_z"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        xau_atr14 = float(row["xau_atr14"])
        xau_ema20 = float(row["xau_ema20"])
        ratio_z = float(row["xau_xag_ratio_z"])
        residual_z = float(row["xau_xag_residual_z"])
        ratio_z_change_3h = float(row["ratio_z_change_3h"])
        usd_proxy_return_24h = float(row["usd_proxy_return_24h"])
        usd_proxy_z = float(row["usd_proxy_z"])
        if xau_atr14 <= 0:
            return None

        xau_cheap = residual_z <= -0.70 or ratio_z <= -0.95
        xau_rich = residual_z >= 0.70 or ratio_z >= 0.95
        usd_weak = usd_proxy_return_24h <= 0.0 or usd_proxy_z <= -0.35
        usd_strong = usd_proxy_return_24h >= 0.0 or usd_proxy_z >= 0.35

        if (
            xau_cheap
            and usd_weak
            and ratio_z_change_3h > -0.15
            and close > open_price
            and close >= xau_ema20 - 0.85 * xau_atr14
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            xau_rich
            and usd_strong
            and ratio_z_change_3h < 0.15
            and close < open_price
            and close <= xau_ema20 + 0.85 * xau_atr14
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _proxy_frame(proxy: dict[str, Any], symbol: str, expert: str) -> pd.DataFrame:
    frame = proxy.get(symbol)
    if not isinstance(frame, pd.DataFrame):
        raise ConfigError(f"{expert} missing {symbol} H1 proxy frame.")
    return require_frame({symbol: frame}, symbol)


def _composite_features(
    h1: pd.DataFrame,
    xag: pd.DataFrame,
    eurusd: pd.DataFrame,
    usdjpy: pd.DataFrame,
) -> pd.DataFrame:
    xau_frame = _close_frame(h1, "xau")
    xag_frame = _close_frame(xag, "xag")
    eur_frame = _close_frame(eurusd, "eurusd")
    jpy_frame = _close_frame(usdjpy, "usdjpy")
    frame = (
        xau_frame.merge(xag_frame, on="timestamp_utc", how="inner")
        .merge(eur_frame, on="timestamp_utc", how="inner")
        .merge(jpy_frame, on="timestamp_utc", how="inner")
    )

    frame["xau_return_24h"] = np.log(frame["xau_close"] / frame["xau_close"].shift(24))
    frame["xag_return_24h"] = np.log(frame["xag_close"] / frame["xag_close"].shift(24))
    eurusd_return_24h = np.log(frame["eurusd_close"] / frame["eurusd_close"].shift(24))
    usdjpy_return_24h = np.log(frame["usdjpy_close"] / frame["usdjpy_close"].shift(24))
    frame["usd_proxy_return_24h"] = pd.concat(
        [-eurusd_return_24h, usdjpy_return_24h],
        axis=1,
    ).mean(axis=1)

    covariance = frame["xau_return_24h"].rolling(250, min_periods=120).cov(
        frame["xag_return_24h"]
    )
    variance = frame["xag_return_24h"].rolling(250, min_periods=120).var()
    frame["xau_xag_beta"] = covariance / variance.replace(0.0, np.nan)
    frame["xau_expected_return"] = frame["xau_xag_beta"] * frame["xag_return_24h"]
    frame["xau_xag_residual_return"] = frame["xau_return_24h"] - frame["xau_expected_return"]
    frame["xau_xag_residual_z"] = _rolling_zscore(frame["xau_xag_residual_return"], 250)
    frame["xau_xag_log_ratio"] = np.log(frame["xau_close"] / frame["xag_close"])
    frame["xau_xag_ratio_z"] = _rolling_zscore(frame["xau_xag_log_ratio"], 500)
    frame["ratio_z_change_3h"] = frame["xau_xag_ratio_z"] - frame["xau_xag_ratio_z"].shift(3)
    frame["usd_proxy_z"] = _rolling_zscore(frame["usd_proxy_return_24h"], 250)

    return frame[
        [
            "timestamp_utc",
            "xag_close",
            "xau_return_24h",
            "xag_return_24h",
            "usd_proxy_return_24h",
            "usd_proxy_z",
            "xau_xag_beta",
            "xau_expected_return",
            "xau_xag_residual_return",
            "xau_xag_residual_z",
            "xau_xag_log_ratio",
            "xau_xag_ratio_z",
            "ratio_z_change_3h",
        ]
    ]


def _close_frame(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    prepared = frame[["timestamp_utc", "close"]].copy()
    prepared["timestamp_utc"] = pd.to_datetime(prepared["timestamp_utc"], utc=True, errors="coerce")
    prepared[f"{prefix}_close"] = pd.to_numeric(prepared["close"], errors="coerce")
    return prepared.drop(columns="close").dropna().sort_values("timestamp_utc")


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    minimum = max(30, window // 2)
    mean = series.rolling(window, min_periods=minimum).mean()
    std = series.rolling(window, min_periods=minimum).std()
    return (series - mean) / std.replace(0.0, np.nan)


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "xau_atr14": float(row["xau_atr14"]),
        "xau_ema20": float(row["xau_ema20"]),
        "xag_close": float(row["xag_close"]),
        "xau_return_24h": float(row["xau_return_24h"]),
        "xag_return_24h": float(row["xag_return_24h"]),
        "usd_proxy_return_24h": float(row["usd_proxy_return_24h"]),
        "usd_proxy_z": float(row["usd_proxy_z"]),
        "xau_xag_beta": float(row["xau_xag_beta"]),
        "xau_expected_return": float(row["xau_expected_return"]),
        "xau_xag_residual_return": float(row["xau_xag_residual_return"]),
        "xau_xag_residual_z": float(row["xau_xag_residual_z"]),
        "xau_xag_log_ratio": float(row["xau_xag_log_ratio"]),
        "xau_xag_ratio_z": float(row["xau_xag_ratio_z"]),
        "ratio_z_change_3h": float(row["ratio_z_change_3h"]),
    }
