from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


FAMILY = "H4_MACRO_COMPOSITE_RISK_STATE_V0_PORTABILITY"


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


def prepare_h4(
    h4: pd.DataFrame,
    macro_state: pd.DataFrame,
    settings: dict[str, Any],
) -> pd.DataFrame:
    frame = h4.copy().sort_values("timestamp_utc", kind="mergesort")
    frame["atr14"] = atr(frame, int(settings["atr_period"]))
    frame["ema40"] = frame["mid_close"].ewm(
        span=int(settings["ema_period"]),
        adjust=False,
        min_periods=int(settings["ema_period"]),
    ).mean()
    frame["return_6"] = np.log(
        frame["mid_close"] / frame["mid_close"].shift(int(settings["return_bars"]))
    )
    return pd.merge_asof(
        frame,
        macro_state.sort_values("available_at", kind="mergesort"),
        left_on="timestamp_utc",
        right_on="available_at",
        direction="backward",
        allow_exact_matches=True,
    )


def generate_candidates(
    h4: pd.DataFrame,
    macro_state: pd.DataFrame,
    settings: dict[str, Any],
) -> pd.DataFrame:
    frame = prepare_h4(h4, macro_state, settings)
    threshold = int(settings["composite_threshold"])
    long_mask = (
        (frame["macro_composite_score"] >= threshold)
        & (frame["mid_close"] > frame["ema40"])
        & (frame["mid_close"] > frame["mid_open"])
        & (frame["return_6"] > 0)
    )
    short_mask = (
        (frame["macro_composite_score"] <= -threshold)
        & (frame["mid_close"] < frame["ema40"])
        & (frame["mid_close"] < frame["mid_open"])
        & (frame["return_6"] < 0)
    )
    selected = frame.loc[long_mask | short_mask].copy()
    if selected.empty:
        return pd.DataFrame()
    selected["direction"] = np.where(long_mask.loc[selected.index], "LONG", "SHORT")
    selected["direction_sign"] = np.where(selected["direction"].eq("LONG"), 1, -1)
    selected["signal_day"] = selected["timestamp_utc"].dt.date
    if bool(settings["one_candidate_per_day_and_direction"]):
        selected = selected.drop_duplicates(
            ["signal_day", "direction"], keep="first"
        )
    selected["family_id"] = FAMILY
    selected["signal_time"] = selected["timestamp_utc"]
    selected["atr_value"] = selected["atr14"]
    selected["stop_frozen"] = selected["mid_close"] - (
        selected["direction_sign"]
        * float(settings["stop_atr"])
        * selected["atr14"]
    )
    selected["target_r"] = float(settings["target_r"])
    selected["maximum_hold_hours"] = float(settings["maximum_hold_hours"])
    selected["quality_score"] = selected["macro_composite_score"].abs().astype(float)
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
        "available_at",
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
        "ema40",
        "return_6",
    ]
    numeric = ["stop_frozen", "atr_value", "macro_composite_score", "ema40", "return_6"]
    selected = selected.loc[np.isfinite(selected[numeric]).all(axis=1)]
    return selected[columns].sort_values("signal_time", kind="mergesort").reset_index(drop=True)
