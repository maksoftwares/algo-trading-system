from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


TREND = "H4_ADAPTIVE_TREND_CONTINUATION_V1"
SHOCK = "H4_ADAPTIVE_POST_SHOCK_REVERSAL_V1"
BREAKOUT = "H4_ADAPTIVE_RANGE_BREAKOUT_V1"
FAMILIES = (TREND, SHOCK, BREAKOUT)
FEATURE_COLUMNS = (
    "dir_return_1_atr",
    "dir_return_3_atr",
    "dir_return_6_atr",
    "dir_return_18_atr",
    "dir_ema_fast_distance_atr",
    "dir_ema_spread_atr",
    "dir_close_location",
    "range_atr",
    "body_fraction",
    "efficiency_ratio",
    "atr_ratio",
    "quote_intensity_ratio",
    "spread_atr",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
)


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


def prepare_h4(h4: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    frame = h4.copy()
    frame["atr14"] = atr(frame, int(settings["atr_period"]))
    frame["return_1"] = frame["mid_close"].diff(1)
    frame["return_3"] = frame["mid_close"].diff(3)
    frame["return_6"] = frame["mid_close"].diff(6)
    frame["return_18"] = frame["mid_close"].diff(18)
    frame["ema_fast"] = frame["mid_close"].ewm(
        span=int(settings["ema_fast_period"]), adjust=False
    ).mean()
    frame["ema_slow"] = frame["mid_close"].ewm(
        span=int(settings["ema_slow_period"]), adjust=False
    ).mean()
    lookback = int(settings["efficiency_lookback"])
    movement = frame["mid_close"].diff().abs().rolling(lookback, min_periods=lookback).sum()
    frame["efficiency_ratio"] = frame["return_18"].abs() / movement.replace(0.0, np.nan)
    span = (frame["mid_high"] - frame["mid_low"]).replace(0.0, np.nan)
    frame["range_atr"] = span / frame["atr14"]
    frame["body_fraction"] = (frame["mid_close"] - frame["mid_open"]).abs() / span
    frame["close_location"] = (frame["mid_close"] - frame["mid_low"]) / span
    frame["atr_ratio"] = frame["atr14"] / frame["atr14"].shift(1).rolling(
        126, min_periods=63
    ).median()
    frame["quote_intensity_ratio"] = frame["tick_count"] / frame["tick_count"].shift(
        1
    ).rolling(63, min_periods=30).median()
    frame["spread_atr"] = (frame["ask_close"] - frame["bid_close"]) / frame["atr14"]
    prior = int(settings["prior_range_bars"])
    frame["prior_high"] = frame["mid_high"].shift(1).rolling(
        prior, min_periods=prior
    ).max()
    frame["prior_low"] = frame["mid_low"].shift(1).rolling(
        prior, min_periods=prior
    ).min()
    hour = frame["timestamp_utc"].dt.hour
    weekday = frame["timestamp_utc"].dt.weekday
    frame["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    frame["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    frame["weekday_sin"] = np.sin(2.0 * np.pi * weekday / 7.0)
    frame["weekday_cos"] = np.cos(2.0 * np.pi * weekday / 7.0)
    return frame


def candidate_rows(
    frame: pd.DataFrame,
    mask: pd.Series,
    direction: pd.Series,
    family: str,
    config: dict[str, Any],
) -> pd.DataFrame:
    selected = frame.loc[mask & direction.ne(0)].copy()
    if selected.empty:
        return pd.DataFrame()
    selected["direction_sign"] = direction.loc[selected.index].astype(int)
    selected["direction"] = np.where(selected["direction_sign"] > 0, "LONG", "SHORT")
    selected["family_id"] = family
    selected["signal_time"] = selected["timestamp_utc"]
    selected["atr_value"] = selected["atr14"]
    family_settings = config["families"][family]
    selected["stop_frozen"] = selected["mid_close"] - (
        selected["direction_sign"]
        * float(family_settings["stop_atr"])
        * selected["atr14"]
    )
    selected["target_r"] = float(family_settings["target_r"])
    selected["maximum_hold_hours"] = float(family_settings["maximum_hold_hours"])
    selected["dir_return_1_atr"] = (
        selected["direction_sign"] * selected["return_1"] / selected["atr14"]
    )
    selected["dir_return_3_atr"] = (
        selected["direction_sign"] * selected["return_3"] / selected["atr14"]
    )
    selected["dir_return_6_atr"] = (
        selected["direction_sign"] * selected["return_6"] / selected["atr14"]
    )
    selected["dir_return_18_atr"] = (
        selected["direction_sign"] * selected["return_18"] / selected["atr14"]
    )
    selected["dir_ema_fast_distance_atr"] = selected["direction_sign"] * (
        selected["mid_close"] - selected["ema_fast"]
    ) / selected["atr14"]
    selected["dir_ema_spread_atr"] = selected["direction_sign"] * (
        selected["ema_fast"] - selected["ema_slow"]
    ) / selected["atr14"]
    selected["dir_close_location"] = np.where(
        selected["direction_sign"] > 0,
        selected["close_location"],
        1.0 - selected["close_location"],
    )
    return selected[
        [
            "family_id",
            "signal_time",
            "direction",
            "direction_sign",
            "stop_frozen",
            "atr_value",
            "target_r",
            "maximum_hold_hours",
            *FEATURE_COLUMNS,
        ]
    ]


def generate_candidates(h4: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    frame = prepare_h4(h4, config["signal"])
    settings = config["signal"]
    trend_direction = pd.Series(
        np.sign(frame["ema_fast"] - frame["ema_slow"]), index=frame.index
    )
    trend_mask = (
        np.isfinite(frame["atr14"])
        & (
            (frame["ema_fast"] - frame["ema_slow"]).abs() / frame["atr14"]
            >= float(settings["trend_minimum_ema_spread_atr"])
        )
        & (frame["efficiency_ratio"] >= float(settings["trend_minimum_efficiency"]))
        & (frame["body_fraction"] >= float(settings["trend_minimum_body_fraction"]))
        & (trend_direction * frame["return_1"] > 0)
        & (trend_direction * (frame["mid_close"] - frame["ema_fast"]) > 0)
    )

    impulse_direction = pd.Series(np.sign(frame["return_1"]), index=frame.index)
    shock_direction = -impulse_direction
    extreme = (
        ((impulse_direction > 0) & (frame["close_location"] >= float(settings["shock_extreme_close_location"])))
        | ((impulse_direction < 0) & (frame["close_location"] <= 1.0 - float(settings["shock_extreme_close_location"])))
    )
    shock_mask = (
        np.isfinite(frame["atr14"])
        & (frame["range_atr"] >= float(settings["shock_minimum_range_atr"]))
        & (
            frame["quote_intensity_ratio"]
            >= float(settings["shock_minimum_quote_intensity_ratio"])
        )
        & extreme
    )

    breakout_up = frame["mid_close"] > frame["prior_high"]
    breakout_down = frame["mid_close"] < frame["prior_low"]
    breakout_direction = pd.Series(
        np.select([breakout_up, breakout_down], [1, -1], default=0), index=frame.index
    )
    breakout_mask = (
        np.isfinite(frame["atr14"])
        & (frame["range_atr"] >= float(settings["breakout_minimum_range_atr"]))
        & (frame["body_fraction"] >= float(settings["breakout_minimum_body_fraction"]))
        & (breakout_direction * frame["return_1"] > 0)
    )
    candidates = pd.concat(
        [
            candidate_rows(frame, trend_mask, trend_direction, TREND, config),
            candidate_rows(frame, shock_mask, shock_direction, SHOCK, config),
            candidate_rows(frame, breakout_mask, breakout_direction, BREAKOUT, config),
        ],
        ignore_index=True,
    )
    if candidates.empty:
        return pd.DataFrame(columns=["family_id", "signal_time", "direction"])
    finite = np.isfinite(candidates[list(FEATURE_COLUMNS)]).all(axis=1)
    return candidates.loc[finite].sort_values(
        ["signal_time", "family_id"], kind="mergesort"
    ).reset_index(drop=True)


def model(config: dict[str, Any]) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        learning_rate=float(config["learning_rate"]),
        max_iter=int(config["max_iter"]),
        max_leaf_nodes=int(config["max_leaf_nodes"]),
        min_samples_leaf=int(config["min_samples_leaf"]),
        l2_regularization=float(config["l2_regularization"]),
        random_state=int(config["random_state"]),
    )


def select_trades(trades: pd.DataFrame, execution: dict[str, Any]) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    eligible = trades.sort_values(
        ["entry_time", "model_score"], ascending=[True, False], kind="mergesort"
    )
    selected: list[pd.Series] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for _, trade in eligible.iterrows():
        day = trade["entry_time"].date()
        if trade["entry_time"] < position_until or trade["entry_time"] < cooldown_until:
            continue
        if daily_count.get(day, 0) >= int(execution["maximum_trades_per_family_utc_day"]):
            continue
        selected.append(trade)
        position_until = trade["exit_time"]
        cooldown_until = trade["exit_time"] + pd.Timedelta(
            hours=float(execution["cooldown_hours"])
        )
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(selected)


def score_stage(
    rows: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    model_config = config["model"]
    block_months = int(model_config["evaluation_block_months"])
    starts = pd.date_range(start, end, freq=f"{block_months}MS", inclusive="left")
    scored_blocks: list[pd.DataFrame] = []
    diagnostics: list[dict[str, Any]] = []
    purge = pd.Timedelta(hours=float(model_config["purge_hours"]))
    history_span = pd.DateOffset(years=int(model_config["history_years"]))
    for block_start in starts:
        block_end = min(block_start + pd.DateOffset(months=block_months), end)
        history = rows.loc[
            (rows["exit_time"] < block_start - purge)
            & (rows["signal_time"] >= block_start - history_span)
        ].sort_values("signal_time", kind="mergesort")
        evaluation = rows.loc[
            (rows["entry_time"] >= block_start) & (rows["entry_time"] < block_end)
        ].copy()
        split = int(len(history) * float(model_config["fit_history_share"]))
        if split <= 0 or split >= len(history):
            diagnostics.append(
                {
                    "block_start": block_start,
                    "status": "INSUFFICIENT_HISTORY",
                    "history_rows": int(len(history)),
                    "evaluation_rows": int(len(evaluation)),
                }
            )
            continue
        calibration_start = history.iloc[split]["signal_time"]
        fit = history.loc[history["exit_time"] < calibration_start - purge]
        calibration = history.loc[history["signal_time"] >= calibration_start]
        if (
            len(fit) < int(model_config["minimum_fit_rows"])
            or len(calibration) < int(model_config["minimum_calibration_rows"])
        ):
            diagnostics.append(
                {
                    "block_start": block_start,
                    "status": "INSUFFICIENT_FIT_OR_CALIBRATION",
                    "history_rows": int(len(history)),
                    "fit_rows": int(len(fit)),
                    "calibration_rows": int(len(calibration)),
                    "evaluation_rows": int(len(evaluation)),
                }
            )
            continue
        estimator = model(model_config)
        estimator.fit(fit[list(FEATURE_COLUMNS)], fit["stress_net_r"])
        calibration_scores = estimator.predict(calibration[list(FEATURE_COLUMNS)])
        threshold = max(
            0.0,
            float(
                np.quantile(
                    calibration_scores, float(model_config["calibration_quantile"])
                )
            ),
        )
        evaluation["model_score"] = estimator.predict(evaluation[list(FEATURE_COLUMNS)])
        evaluation["model_threshold"] = threshold
        passed = evaluation.loc[evaluation["model_score"] >= threshold]
        if not passed.empty:
            scored_blocks.append(passed)
        correlation = pd.Series(calibration_scores).corr(
            calibration["stress_net_r"].reset_index(drop=True), method="spearman"
        )
        diagnostics.append(
            {
                "block_start": block_start,
                "status": "SCORED",
                "history_rows": int(len(history)),
                "fit_rows": int(len(fit)),
                "calibration_rows": int(len(calibration)),
                "evaluation_rows": int(len(evaluation)),
                "threshold": threshold,
                "calibration_spearman": (
                    float(correlation) if np.isfinite(correlation) else 0.0
                ),
                "threshold_pass_rows": int(len(passed)),
            }
        )
    scored = pd.concat(scored_blocks, ignore_index=True) if scored_blocks else pd.DataFrame()
    return select_trades(scored, config["execution"]), diagnostics
