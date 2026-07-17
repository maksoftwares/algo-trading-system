from __future__ import annotations

from datetime import time
from typing import Any

import numpy as np
import pandas as pd


CONTINUATION = "COMEX_VWAP_PULLBACK_CONTINUATION_V1"
REVERSION = "COMEX_VWAP_EXHAUSTION_REVERSION_V1"
FAMILIES = (CONTINUATION, REVERSION)


def wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["mid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["mid_high"] - frame["mid_low"],
            (frame["mid_high"] - previous).abs(),
            (frame["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return wilder(true_range, period)


def prepare_frame(
    spot_m5: pd.DataFrame,
    comex_vwap: pd.DataFrame,
    geometry: dict[str, Any],
) -> pd.DataFrame:
    spot = spot_m5.copy()
    spot["spot_atr"] = atr(spot, int(geometry["spot_atr_period"]))
    spot["spot_ema_fast"] = spot["mid_close"].ewm(
        span=int(geometry["spot_fast_ema_period"]), adjust=False
    ).mean()
    spot["spot_ema_slow"] = spot["mid_close"].ewm(
        span=int(geometry["spot_slow_ema_period"]), adjust=False
    ).mean()
    spot["spot_body_atr"] = (spot["mid_close"] - spot["mid_open"]) / spot["spot_atr"]
    span = (spot["mid_high"] - spot["mid_low"]).replace(0.0, np.nan)
    spot["spot_close_location"] = (spot["mid_close"] - spot["mid_low"]) / span

    comex = comex_vwap.copy()
    group = comex.groupby("session_date", sort=False, observed=True)
    slope_bars = int(geometry["comex_vwap_slope_bars"])
    median_bars = int(geometry["comex_volume_median_bars"])
    comex["session_vwap_lag"] = group["session_vwap"].shift(slope_bars)
    comex["volume_baseline"] = group["volume"].transform(
        lambda values: values.shift(1).rolling(median_bars, min_periods=median_bars).median()
    )
    comex["volume_ratio"] = comex["volume"] / comex["volume_baseline"].replace(0.0, np.nan)
    frame = spot.merge(
        comex,
        left_on="timestamp_utc",
        right_on="available_time_utc",
        how="inner",
        validate="one_to_one",
        suffixes=("_spot", "_comex"),
    )
    frame["vwap_deviation_atr"] = frame["vwap_deviation"] / frame["spot_atr"]
    frame["vwap_slope_atr"] = (
        frame["session_vwap"] - frame["session_vwap_lag"]
    ) / frame["spot_atr"]
    frame["ny_time"] = frame["timestamp_utc"].dt.tz_convert("America/New_York").dt.time
    start = time.fromisoformat(str(geometry["ny_session_start"]))
    end = time.fromisoformat(str(geometry["ny_session_end"]))
    frame["in_session"] = frame["ny_time"].between(start, end)
    return frame


def _candidate_rows(
    frame: pd.DataFrame,
    mask: pd.Series,
    direction_sign: pd.Series,
    family: str,
    family_settings: dict[str, Any],
) -> pd.DataFrame:
    selected = frame.loc[mask].copy()
    if selected.empty:
        return pd.DataFrame()
    selected["direction_sign"] = direction_sign.loc[selected.index].astype(int)
    selected["direction"] = np.where(selected["direction_sign"] > 0, "LONG", "SHORT")
    selected["family_id"] = family
    selected["signal_time"] = selected["timestamp_utc"]
    selected["atr_value"] = selected["spot_atr"]
    selected["stop_frozen"] = selected["mid_close"] - (
        selected["direction_sign"]
        * float(family_settings["stop_atr"])
        * selected["spot_atr"]
    )
    selected["target_r"] = float(family_settings["target_r"])
    selected["maximum_hold_hours"] = float(family_settings["maximum_hold_hours"])
    selected["quality_score"] = selected["vwap_deviation_atr"].abs()
    selected["model_score"] = selected["quality_score"]
    columns = [
        "family_id",
        "signal_time",
        "direction",
        "direction_sign",
        "stop_frozen",
        "atr_value",
        "target_r",
        "maximum_hold_hours",
        "quality_score",
        "model_score",
        "available_time_utc",
        "session_date",
        "session_vwap",
        "vwap_deviation",
        "vwap_deviation_atr",
        "vwap_slope_atr",
        "volume_ratio",
        "spot_body_atr",
        "spot_close_location",
        "spot_ema_fast",
        "spot_ema_slow",
    ]
    return selected[columns]


def generate_candidates(
    spot_m5: pd.DataFrame,
    comex_vwap: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    geometry = config["feature_geometry"]
    frame = prepare_frame(spot_m5, comex_vwap, geometry)
    deviation_direction = np.sign(frame["vwap_deviation_atr"]).fillna(0).astype(int)
    continuation_body = deviation_direction * frame["spot_body_atr"]
    continuation_close = pd.Series(
        np.where(
            deviation_direction > 0,
            frame["spot_close_location"],
            1.0 - frame["spot_close_location"],
        ),
        index=frame.index,
    )
    aligned_trend = pd.Series(
        np.where(
            deviation_direction > 0,
            frame["spot_ema_fast"] > frame["spot_ema_slow"],
            frame["spot_ema_fast"] < frame["spot_ema_slow"],
        ),
        index=frame.index,
    )
    continuation_mask = (
        frame["in_session"]
        & deviation_direction.ne(0)
        & frame["vwap_deviation_atr"].abs().between(
            float(geometry["continuation_deviation_atr_min"]),
            float(geometry["continuation_deviation_atr_max"]),
        )
        & (
            deviation_direction * frame["vwap_slope_atr"]
            >= float(geometry["continuation_directional_vwap_slope_atr_min"])
        )
        & aligned_trend
        & (continuation_body >= float(geometry["continuation_spot_body_atr_min"]))
        & (
            continuation_close
            >= float(geometry["continuation_directional_close_location_min"])
        )
        & (frame["volume_ratio"] >= float(geometry["continuation_volume_ratio_min"]))
    )

    reversion_direction = -deviation_direction
    reversion_body = reversion_direction * frame["spot_body_atr"]
    reversion_close = pd.Series(
        np.where(
            reversion_direction > 0,
            frame["spot_close_location"],
            1.0 - frame["spot_close_location"],
        ),
        index=frame.index,
    )
    reversion_mask = (
        frame["in_session"]
        & reversion_direction.ne(0)
        & (
            frame["vwap_deviation_atr"].abs()
            >= float(geometry["reversion_deviation_atr_min"])
        )
        & (
            frame["vwap_slope_atr"].abs()
            <= float(geometry["reversion_absolute_vwap_slope_atr_max"])
        )
        & (reversion_body >= float(geometry["reversion_spot_body_atr_min"]))
        & (reversion_close >= float(geometry["reversion_directional_close_location_min"]))
        & (frame["volume_ratio"] >= float(geometry["reversion_volume_ratio_min"]))
    )
    candidates = pd.concat(
        [
            _candidate_rows(
                frame,
                continuation_mask,
                deviation_direction,
                CONTINUATION,
                config["families"][CONTINUATION],
            ),
            _candidate_rows(
                frame,
                reversion_mask,
                reversion_direction,
                REVERSION,
                config["families"][REVERSION],
            ),
        ],
        ignore_index=True,
    )
    if candidates.empty:
        return candidates
    numeric = ["stop_frozen", "atr_value", "vwap_deviation_atr", "vwap_slope_atr", "volume_ratio"]
    candidates = candidates.loc[np.isfinite(candidates[numeric]).all(axis=1)]
    return candidates.sort_values(["signal_time", "family_id"], kind="mergesort").reset_index(drop=True)
