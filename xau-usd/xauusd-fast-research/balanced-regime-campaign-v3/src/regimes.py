from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


RESEARCH_ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FEATURES = _load_module(
    "balanced_regime_feature_base",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)

BASE_STATES = ("TREND_UP", "TREND_DOWN", "COMPRESSION", "CHOP")
OUTPUT_STATES = (*BASE_STATES, "TRANSITION", "UNSAFE_SHOCK", "WARMUP")


def _prior_quantile(
    values: pd.Series, window: int, minimum: int, quantile: float
) -> pd.Series:
    return values.shift(1).rolling(window, min_periods=minimum).quantile(quantile)


def _stabilize_states(
    raw_state: pd.Series,
    unsafe: pd.Series,
    eligible: pd.Series,
    confirmation_bars: int,
) -> pd.Series:
    if confirmation_bars < 1:
        raise ValueError("confirmation_bars must be positive")

    labels: list[str] = []
    stable: str | None = None
    pending: str | None = None
    pending_count = 0
    for position, candidate in enumerate(raw_state.astype(str)):
        if not bool(eligible.iloc[position]):
            labels.append("WARMUP")
            continue
        if bool(unsafe.iloc[position]):
            labels.append("UNSAFE_SHOCK")
            pending = None
            pending_count = 0
            continue
        if stable is None:
            stable = candidate
            labels.append(candidate)
            continue
        if candidate == stable:
            pending = None
            pending_count = 0
            labels.append(stable)
            continue
        if candidate == pending:
            pending_count += 1
        else:
            pending = candidate
            pending_count = 1
        if pending_count >= confirmation_bars:
            stable = candidate
            pending = None
            pending_count = 0
            labels.append("TRANSITION")
        else:
            labels.append(stable)
    return pd.Series(labels, index=raw_state.index, dtype="string")


def classify_h4(h4: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    """Classify each completed H4 bar using only that bar and prior history."""
    frame = FEATURES.classify_h4(h4, settings).copy()
    lookback = int(settings["er_lookback"])
    frame["directional_displacement_atr_h4"] = (
        frame["mid_close"] - frame["mid_close"].shift(lookback)
    ) / frame["atr_h4"]
    frame["ema_position_atr_h4"] = (
        frame["mid_close"] - frame["ema_h4"]
    ) / frame["atr_h4"]
    weights = settings["balanced_score_weights"]
    frame["trend_score_h4"] = (
        float(weights["ema_slope"]) * frame["ema_slope_atr_h4"]
        + float(weights["directional_displacement"])
        * frame["directional_displacement_atr_h4"]
        + float(weights["ema_position"]) * frame["ema_position_atr_h4"]
    )

    window = int(settings["balanced_quantile_lookback"])
    minimum = int(settings["balanced_quantile_minimum"])
    quantiles = settings["balanced_quantiles"]
    frame["trend_score_low"] = _prior_quantile(
        frame["trend_score_h4"], window, minimum, float(quantiles["trend_low"])
    )
    frame["trend_score_high"] = _prior_quantile(
        frame["trend_score_h4"], window, minimum, float(quantiles["trend_high"])
    )
    frame["adx_floor"] = _prior_quantile(
        frame["adx_h4"], window, minimum, float(quantiles["adx_floor"])
    )
    frame["efficiency_floor"] = _prior_quantile(
        frame["er_h4"], window, minimum, float(quantiles["efficiency_floor"])
    )
    frame["compression_atr_ceiling"] = _prior_quantile(
        frame["atr_ratio_h4"],
        window,
        minimum,
        float(quantiles["compression_atr_ceiling"]),
    )
    frame["compression_width_ceiling"] = _prior_quantile(
        frame["range_width_atr_h4"],
        window,
        minimum,
        float(quantiles["compression_width_ceiling"]),
    )

    required = [
        "atr_h4",
        "adx_h4",
        "er_h4",
        "atr_ratio_h4",
        "range_width_atr_h4",
        "trend_score_h4",
        "trend_score_low",
        "trend_score_high",
        "adx_floor",
        "efficiency_floor",
        "compression_atr_ceiling",
        "compression_width_ceiling",
    ]
    eligible = pd.Series(
        np.isfinite(frame[required]).all(axis=1), index=frame.index, dtype=bool
    )
    unsafe = eligible & (
        frame["atr_h4"].ge(
            _prior_quantile(
                frame["atr_h4"],
                window,
                minimum,
                float(quantiles["unsafe_atr"]),
            )
        )
        | frame["gap_atr_h4"].ge(float(settings["unsafe_gap_atr"]))
    )
    compression = eligible & ~unsafe & (
        frame["atr_ratio_h4"].le(frame["compression_atr_ceiling"])
        & frame["range_width_atr_h4"].le(frame["compression_width_ceiling"])
    )
    strong = (
        frame["adx_h4"].ge(frame["adx_floor"])
        & frame["er_h4"].ge(frame["efficiency_floor"])
    )
    trend_up = eligible & ~unsafe & ~compression & strong & frame[
        "trend_score_h4"
    ].ge(frame["trend_score_high"])
    trend_down = eligible & ~unsafe & ~compression & strong & frame[
        "trend_score_h4"
    ].le(frame["trend_score_low"])
    frame["raw_regime"] = np.select(
        [compression, trend_up, trend_down],
        ["COMPRESSION", "TREND_UP", "TREND_DOWN"],
        default="CHOP",
    )
    frame.loc[~eligible, "raw_regime"] = "WARMUP"
    frame["regime"] = _stabilize_states(
        frame["raw_regime"],
        unsafe,
        eligible,
        int(settings["state_confirmation_bars"]),
    )
    return frame


def regime_run_lengths(classified: pd.DataFrame) -> pd.DataFrame:
    eligible = classified.loc[
        classified["regime"].isin((*BASE_STATES, "TRANSITION")),
        ["timestamp_utc", "regime"],
    ].copy()
    if eligible.empty:
        return pd.DataFrame(columns=["regime", "start_utc", "end_utc", "bars"])
    group = eligible["regime"].ne(eligible["regime"].shift()).cumsum()
    return (
        eligible.groupby(group, sort=False)
        .agg(
            regime=("regime", "first"),
            start_utc=("timestamp_utc", "first"),
            end_utc=("timestamp_utc", "last"),
            bars=("regime", "size"),
        )
        .reset_index(drop=True)
    )
