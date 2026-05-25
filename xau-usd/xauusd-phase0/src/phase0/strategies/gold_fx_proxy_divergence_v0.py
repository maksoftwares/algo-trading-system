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


class GoldFxProxyDivergenceV0Strategy(StrategyBase):
    """Research-only intermarket relative-strength candidate."""

    name = "gold_fx_proxy_divergence_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        proxy = data_context.get("intermarket_proxy")
        if not isinstance(proxy, dict):
            raise ConfigError(
                "gold_fx_proxy_divergence_v0 requires data_context['intermarket_proxy'] "
                "with EURUSD and USDJPY H1 frames."
            )
        eurusd = _proxy_frame(proxy, "EURUSD")
        usdjpy = _proxy_frame(proxy, "USDJPY")

        if "xau_ema20" not in h1:
            h1["xau_ema20"] = ema(h1["close"], 20)
        if "xau_atr14" not in h1:
            h1["xau_atr14"] = atr(h1["high"], h1["low"], h1["close"], 14)

        features = _intermarket_features(h1, eurusd, usdjpy)
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
        used_week_direction: set[tuple[str, str]] = set()

        for position in range(300, len(h1)):
            row = h1.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue
            timestamp = pd.Timestamp(row["timestamp_utc"])
            iso = timestamp.isocalendar()
            week_direction = (f"{iso.year}-W{iso.week:02d}", str(setup["direction"]))
            if week_direction in used_week_direction:
                continue
            used_week_direction.add(week_direction)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"GOLD_FX_PROXY_DIVERGENCE_V0_{direction}",
                    metadata={**setup, "h1_index": int(position)},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["xau_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.10 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.80 * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.10 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.80 * risk_price
        else:
            raise ConfigError(f"Unsupported gold FX proxy direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid gold FX proxy trade plan risk.")

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
            risk_reward=1.80,
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
            row["close"],
            row["xau_ema20"],
            row["xau_atr14"],
            row["usd_proxy_z"],
            row["xau_residual_z"],
            row["xau_return_24h"],
            row["usd_proxy_return_24h"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        xau_ema20 = float(row["xau_ema20"])
        xau_atr14 = float(row["xau_atr14"])
        usd_proxy_z = float(row["usd_proxy_z"])
        xau_residual_z = float(row["xau_residual_z"])
        if xau_atr14 <= 0:
            return None

        if (
            usd_proxy_z >= 1.00
            and xau_residual_z >= 0.75
            and close > xau_ema20
            and close > open_price
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            usd_proxy_z <= -1.00
            and xau_residual_z <= -0.75
            and close < xau_ema20
            and close < open_price
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _proxy_frame(proxy: dict[str, Any], symbol: str) -> pd.DataFrame:
    frame = proxy.get(symbol)
    if not isinstance(frame, pd.DataFrame):
        raise ConfigError(f"gold_fx_proxy_divergence_v0 missing {symbol} H1 proxy frame.")
    return require_frame({symbol: frame}, symbol)


def _intermarket_features(
    h1: pd.DataFrame,
    eurusd: pd.DataFrame,
    usdjpy: pd.DataFrame,
) -> pd.DataFrame:
    xau = _close_frame(h1, "xau")
    eur = _close_frame(eurusd, "eurusd")
    jpy = _close_frame(usdjpy, "usdjpy")
    frame = xau.merge(eur, on="timestamp_utc", how="inner").merge(jpy, on="timestamp_utc", how="inner")

    frame["xau_return_24h"] = np.log(frame["xau_close"] / frame["xau_close"].shift(24))
    eurusd_return_24h = np.log(frame["eurusd_close"] / frame["eurusd_close"].shift(24))
    usdjpy_return_24h = np.log(frame["usdjpy_close"] / frame["usdjpy_close"].shift(24))
    frame["usd_proxy_return_24h"] = pd.concat(
        [-eurusd_return_24h, usdjpy_return_24h],
        axis=1,
    ).mean(axis=1)

    covariance = frame["xau_return_24h"].rolling(250, min_periods=120).cov(
        frame["usd_proxy_return_24h"]
    )
    variance = frame["usd_proxy_return_24h"].rolling(250, min_periods=120).var()
    frame["rolling_beta"] = covariance / variance.replace(0.0, np.nan)
    frame["xau_expected_return"] = frame["rolling_beta"] * frame["usd_proxy_return_24h"]
    frame["xau_residual_return"] = frame["xau_return_24h"] - frame["xau_expected_return"]
    frame["usd_proxy_z"] = _rolling_zscore(frame["usd_proxy_return_24h"], 250)
    frame["xau_residual_z"] = _rolling_zscore(frame["xau_residual_return"], 250)
    return frame[
        [
            "timestamp_utc",
            "xau_return_24h",
            "usd_proxy_return_24h",
            "rolling_beta",
            "xau_expected_return",
            "xau_residual_return",
            "usd_proxy_z",
            "xau_residual_z",
        ]
    ]


def _close_frame(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    prepared = frame[["timestamp_utc", "close"]].copy()
    prepared["timestamp_utc"] = pd.to_datetime(prepared["timestamp_utc"], utc=True, errors="coerce")
    prepared[f"{prefix}_close"] = pd.to_numeric(prepared["close"], errors="coerce")
    return prepared.drop(columns="close").dropna().sort_values("timestamp_utc")


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    mean = series.rolling(window, min_periods=max(30, window // 2)).mean()
    std = series.rolling(window, min_periods=max(30, window // 2)).std()
    return (series - mean) / std.replace(0.0, np.nan)


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "xau_atr14": float(row["xau_atr14"]),
        "xau_ema20": float(row["xau_ema20"]),
        "xau_return_24h": float(row["xau_return_24h"]),
        "usd_proxy_return_24h": float(row["usd_proxy_return_24h"]),
        "rolling_beta": float(row["rolling_beta"]),
        "xau_expected_return": float(row["xau_expected_return"]),
        "xau_residual_return": float(row["xau_residual_return"]),
        "usd_proxy_z": float(row["usd_proxy_z"]),
        "xau_residual_z": float(row["xau_residual_z"]),
    }
