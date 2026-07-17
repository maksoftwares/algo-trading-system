from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd


TREND_LONG = "R1_H1_TREND_PULLBACK_LONG_V1"
TREND_SHORT = "R2_H1_TREND_PULLBACK_SHORT_V1"
COMPRESSION = "R3_H1_COMPRESSION_BREAK_RETEST_V1"
SESSION = "R4_M15_SESSION_EXPANSION_V1"
CHOP = "R5_M30_CHOP_ROTATION_V1"
SPECIALISTS = (TREND_LONG, TREND_SHORT, COMPRESSION, SESSION, CHOP)


@dataclass(frozen=True)
class BacktestResult:
    candidates: pd.DataFrame
    trades: pd.DataFrame


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


def adx(frame: pd.DataFrame, period: int) -> pd.Series:
    up = frame["mid_high"].diff()
    down = -frame["mid_low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=frame.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=frame.index)
    atr_value = atr(frame, period)
    plus_di = 100.0 * wilder(plus_dm, period) / atr_value.replace(0.0, np.nan)
    minus_di = 100.0 * wilder(minus_dm, period) / atr_value.replace(0.0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return wilder(dx, period)


def _bar_shape(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    span = (result["mid_high"] - result["mid_low"]).replace(0.0, np.nan)
    result["body_fraction"] = (result["mid_close"] - result["mid_open"]).abs() / span
    result["close_location"] = (result["mid_close"] - result["mid_low"]) / span
    result["quote_intensity_ratio"] = (
        result["tick_count"] / result["tick_count"].shift(1).rolling(20, min_periods=10).median()
    )
    return result


def classify_h4(h4: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    frame = _bar_shape(h4)
    period = int(settings["atr_period"])
    lookback = int(settings["er_lookback"])
    frame["atr_h4"] = atr(frame, period)
    frame["adx_h4"] = adx(frame, int(settings["adx_period"]))
    movement = frame["mid_close"].diff().abs().rolling(lookback, min_periods=lookback).sum()
    displacement = (frame["mid_close"] - frame["mid_close"].shift(lookback)).abs()
    frame["er_h4"] = displacement / movement.replace(0.0, np.nan)
    ema_period = int(settings["ema_period"])
    frame["ema_h4"] = frame["mid_close"].ewm(
        span=ema_period, adjust=False, min_periods=ema_period
    ).mean()
    frame["ema_slope_atr_h4"] = (
        frame["ema_h4"] - frame["ema_h4"].shift(int(settings["ema_slope_bars"]))
    ) / frame["atr_h4"]
    width = (
        frame["mid_high"].rolling(
            int(settings["range_lookback"]), min_periods=int(settings["range_lookback"])
        ).max()
        - frame["mid_low"].rolling(
            int(settings["range_lookback"]), min_periods=int(settings["range_lookback"])
        ).min()
    )
    frame["range_width_atr_h4"] = width / frame["atr_h4"]
    frame["displacement_atr_h4"] = displacement / frame["atr_h4"]
    frame["atr_ratio_h4"] = (
        frame["atr_h4"] / frame["atr_h4"].shift(1).rolling(126, min_periods=63).median()
    )
    percentile_window = int(settings["atr_percentile_lookback"])
    prior_atr_limit = frame["atr_h4"].shift(1).rolling(
        percentile_window, min_periods=percentile_window // 2
    ).quantile(float(settings["unsafe_atr_percentile"]) / 100.0)
    frame["gap_atr_h4"] = (
        frame["mid_open"] - frame["mid_close"].shift(1)
    ).abs() / frame["atr_h4"]
    finite = np.isfinite(
        frame[
            [
                "atr_h4", "adx_h4", "er_h4", "ema_h4", "ema_slope_atr_h4",
                "range_width_atr_h4", "displacement_atr_h4",
            ]
        ]
    ).all(axis=1)
    unsafe = finite & (
        (frame["atr_h4"] >= prior_atr_limit)
        | (frame["gap_atr_h4"] >= float(settings["unsafe_gap_atr"]))
    )
    trend_up = finite & (
        (frame["adx_h4"] >= float(settings["trend_adx_min"]))
        & (frame["er_h4"] >= float(settings["trend_er_min"]))
        & (frame["mid_close"] > frame["ema_h4"])
        & (frame["ema_slope_atr_h4"] >= float(settings["trend_slope_atr_min"]))
    )
    trend_down = finite & (
        (frame["adx_h4"] >= float(settings["trend_adx_min"]))
        & (frame["er_h4"] >= float(settings["trend_er_min"]))
        & (frame["mid_close"] < frame["ema_h4"])
        & (frame["ema_slope_atr_h4"] <= -float(settings["trend_slope_atr_min"]))
    )
    compression = finite & (
        (frame["adx_h4"] <= float(settings["compression_adx_max"]))
        & (frame["atr_ratio_h4"] <= float(settings["compression_atr_ratio_max"]))
        & (frame["range_width_atr_h4"] <= float(settings["compression_width_atr_max"]))
    )
    chop = finite & (
        (frame["adx_h4"] <= float(settings["chop_adx_max"]))
        & (frame["er_h4"] <= float(settings["chop_er_max"]))
        & (frame["displacement_atr_h4"] <= float(settings["chop_displacement_atr_max"]))
        & frame["range_width_atr_h4"].between(
            float(settings["chop_width_atr_min"]),
            float(settings["chop_width_atr_max"]),
            inclusive="both",
        )
    )
    frame["regime"] = np.select(
        [unsafe, trend_up, trend_down, compression, chop],
        ["UNSAFE_SHOCK", "TREND_UP", "TREND_DOWN", "COMPRESSION", "CHOP"],
        default="TRANSITION_UNKNOWN",
    )
    return frame


def attach_regime(bars: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "timestamp_utc", "regime", "atr_h4", "adx_h4", "er_h4",
        "ema_slope_atr_h4", "range_width_atr_h4", "displacement_atr_h4",
    ]
    return pd.merge_asof(
        bars.sort_values("timestamp_utc"),
        h4[columns].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
    ).sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)


def _candidate_rows(
    frame: pd.DataFrame, mask: pd.Series, values: dict[str, Any]
) -> pd.DataFrame:
    selected = frame.loc[mask].copy()
    if selected.empty:
        return pd.DataFrame()
    result = pd.DataFrame(index=selected.index)
    for key, value in values.items():
        result[key] = value.loc[selected.index] if isinstance(value, pd.Series) else value
    result["signal_time"] = selected["timestamp_utc"]
    result["regime"] = selected["regime"]
    return result.reset_index(drop=True)


def trend_candidates(h1: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    frame = _bar_shape(h1)
    frame["atr_local"] = atr(frame, int(settings["h1_atr_period"]))
    frame["ema_local"] = frame["mid_close"].ewm(
        span=int(settings["h1_ema_period"]),
        adjust=False,
        min_periods=int(settings["h1_ema_period"]),
    ).mean()
    swing_bars = int(settings["swing_bars"])
    swing_low = frame["mid_low"].rolling(swing_bars, min_periods=swing_bars).min()
    swing_high = frame["mid_high"].rolling(swing_bars, min_periods=swing_bars).max()
    common = (
        frame["body_fraction"].ge(float(settings["minimum_body_fraction"]))
        & np.isfinite(frame["atr_local"])
        & np.isfinite(frame["ema_local"])
    )
    long_mask = (
        common
        & frame["regime"].eq("TREND_UP")
        & (
            frame["mid_low"]
            <= frame["ema_local"]
            + float(settings["pullback_distance_atr"]) * frame["atr_local"]
        )
        & (frame["mid_close"] > frame["ema_local"])
        & (frame["mid_close"] > frame["mid_open"])
        & (frame["close_location"] >= float(settings["minimum_close_location"]))
    )
    short_mask = (
        common
        & frame["regime"].eq("TREND_DOWN")
        & (
            frame["mid_high"]
            >= frame["ema_local"]
            - float(settings["pullback_distance_atr"]) * frame["atr_local"]
        )
        & (frame["mid_close"] < frame["ema_local"])
        & (frame["mid_close"] < frame["mid_open"])
        & (frame["close_location"] <= 1.0 - float(settings["minimum_close_location"]))
    )
    shared = {
        "target_kind": "R_MULTIPLE",
        "target_value": float(settings["target_r"]),
        "atr_value": frame["atr_local"],
        "minimum_stop_atr": float(settings["minimum_stop_atr"]),
        "maximum_stop_atr": float(settings["maximum_stop_atr"]),
        "maximum_hold_hours": float(settings["maximum_hold_hours"]),
        "cooldown_hours": float(settings["cooldown_hours"]),
        "daily_key": frame["bar_start_utc"].dt.strftime("%Y-%m-%d"),
    }
    long = _candidate_rows(
        frame,
        long_mask,
        {
            **shared,
            "specialist_id": TREND_LONG,
            "direction": "LONG",
            "stop_frozen": swing_low
            - float(settings["stop_buffer_atr"]) * frame["atr_local"],
            "setup_id": "TREND_LONG_" + frame["timestamp_utc"].astype(str),
        },
    )
    short = _candidate_rows(
        frame,
        short_mask,
        {
            **shared,
            "specialist_id": TREND_SHORT,
            "direction": "SHORT",
            "stop_frozen": swing_high
            + float(settings["stop_buffer_atr"]) * frame["atr_local"],
            "setup_id": "TREND_SHORT_" + frame["timestamp_utc"].astype(str),
        },
    )
    return pd.concat([long, short], ignore_index=True)


def compression_candidates(
    h1: pd.DataFrame, m15: pd.DataFrame, settings: dict[str, Any]
) -> pd.DataFrame:
    frame = _bar_shape(h1)
    frame["atr_local"] = atr(frame, 14)
    lookback = int(settings["h1_lookback_bars"])
    prior_high = frame["mid_high"].shift(1).rolling(
        lookback, min_periods=lookback
    ).max()
    prior_low = frame["mid_low"].shift(1).rolling(
        lookback, min_periods=lookback
    ).min()
    prior_range = prior_high - prior_low
    atr_ratio = (
        frame["atr_local"]
        / frame["atr_local"].shift(1).rolling(48, min_periods=24).median()
    )
    common = (
        frame["regime"].eq("COMPRESSION")
        & (prior_range <= float(settings["maximum_range_atr"]) * frame["atr_local"])
        & (atr_ratio <= float(settings["maximum_atr_ratio"]))
        & (frame["body_fraction"] >= float(settings["minimum_breakout_body_fraction"]))
    )
    long_break = (
        common
        & (
            frame["mid_close"]
            >= prior_high
            + float(settings["breakout_distance_atr"]) * frame["atr_local"]
        )
        & (frame["mid_close"] > frame["mid_open"])
    )
    short_break = (
        common
        & (
            frame["mid_close"]
            <= prior_low
            - float(settings["breakout_distance_atr"]) * frame["atr_local"]
        )
        & (frame["mid_close"] < frame["mid_open"])
    )
    m15_frame = _bar_shape(m15)
    rows: list[dict[str, Any]] = []
    timestamps = m15_frame["timestamp_utc"].to_numpy(dtype="datetime64[ns]")
    for index in frame.index[long_break | short_break]:
        direction = "LONG" if bool(long_break.loc[index]) else "SHORT"
        breakout_time = frame.at[index, "timestamp_utc"]
        start = int(
            np.searchsorted(
                timestamps,
                np.datetime64(breakout_time.tz_convert(None)),
                side="right",
            )
        )
        end = min(len(m15_frame), start + int(settings["retest_window_m15_bars"]))
        boundary = float(prior_high.loc[index] if direction == "LONG" else prior_low.loc[index])
        local_atr = float(frame.at[index, "atr_local"])
        for _, bar in m15_frame.iloc[start:end].iterrows():
            if direction == "LONG":
                touched = (
                    float(bar["mid_low"])
                    <= boundary
                    + float(settings["maximum_retest_distance_atr"]) * local_atr
                )
                held = (
                    float(bar["mid_close"])
                    >= boundary
                    + float(settings["minimum_retest_close_atr"]) * local_atr
                )
                stop = (
                    min(float(bar["mid_low"]), boundary)
                    - float(settings["stop_buffer_atr"]) * local_atr
                )
            else:
                touched = (
                    float(bar["mid_high"])
                    >= boundary
                    - float(settings["maximum_retest_distance_atr"]) * local_atr
                )
                held = (
                    float(bar["mid_close"])
                    <= boundary
                    - float(settings["minimum_retest_close_atr"]) * local_atr
                )
                stop = (
                    max(float(bar["mid_high"]), boundary)
                    + float(settings["stop_buffer_atr"]) * local_atr
                )
            if touched and held:
                rows.append(
                    {
                        "specialist_id": COMPRESSION,
                        "direction": direction,
                        "signal_time": bar["timestamp_utc"],
                        "stop_frozen": stop,
                        "target_kind": "R_MULTIPLE",
                        "target_value": float(settings["target_r"]),
                        "atr_value": local_atr,
                        "minimum_stop_atr": float(settings["minimum_stop_atr"]),
                        "maximum_stop_atr": float(settings["maximum_stop_atr"]),
                        "maximum_hold_hours": float(settings["maximum_hold_hours"]),
                        "cooldown_hours": float(settings["cooldown_hours"]),
                        "daily_key": "",
                        "setup_id": f"COMPRESSION_{breakout_time.isoformat()}",
                        "regime": "COMPRESSION",
                    }
                )
                break
    return pd.DataFrame(rows)


def session_candidates(m15: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    frame = _bar_shape(m15)
    frame["atr_local"] = atr(frame, 14)
    frame["date_key"] = frame["bar_start_utc"].dt.strftime("%Y-%m-%d")
    frame["hour"] = frame["bar_start_utc"].dt.hour
    rows: list[pd.DataFrame] = []
    resolved = frame["regime"].isin(
        ["TREND_UP", "TREND_DOWN", "COMPRESSION", "CHOP"]
    )
    for profile in settings["profiles"]:
        reference_mask = frame["hour"].between(
            int(profile["reference_start_hour"]),
            int(profile["reference_end_hour"]) - 1,
        )
        reference = frame.loc[reference_mask].groupby("date_key", sort=True).agg(
            reference_high=("mid_high", "max"),
            reference_low=("mid_low", "min"),
            reference_bars=("mid_close", "size"),
        )
        work = frame.join(reference, on="date_key")
        decision = work["hour"].between(
            int(profile["decision_start_hour"]),
            int(profile["decision_end_hour"]) - 1,
        )
        common = (
            decision
            & resolved
            & (work["reference_bars"] >= int(settings["minimum_reference_m15_bars"]))
            & (work["body_fraction"] >= float(settings["minimum_body_fraction"]))
            & (
                work["quote_intensity_ratio"]
                >= float(settings["minimum_quote_intensity_ratio"])
            )
        )
        long_mask = (
            common
            & ~work["regime"].eq("TREND_DOWN")
            & (
                work["mid_close"]
                >= work["reference_high"]
                + float(settings["breakout_distance_atr"]) * work["atr_local"]
            )
            & (work["mid_close"] > work["mid_open"])
        )
        short_mask = (
            common
            & ~work["regime"].eq("TREND_UP")
            & (
                work["mid_close"]
                <= work["reference_low"]
                - float(settings["breakout_distance_atr"]) * work["atr_local"]
            )
            & (work["mid_close"] < work["mid_open"])
        )
        for direction, mask in (("LONG", long_mask), ("SHORT", short_mask)):
            eligible_indices = work.index[mask]
            first_indices = work.loc[eligible_indices].groupby("date_key", sort=True).head(1).index
            first_mask = work.index.isin(first_indices)
            stop = (
                work["reference_low"]
                - float(settings["stop_buffer_atr"]) * work["atr_local"]
                if direction == "LONG"
                else work["reference_high"]
                + float(settings["stop_buffer_atr"]) * work["atr_local"]
            )
            rows.append(
                _candidate_rows(
                    work,
                    pd.Series(first_mask, index=work.index),
                    {
                        "specialist_id": SESSION,
                        "direction": direction,
                        "stop_frozen": stop,
                        "target_kind": "R_MULTIPLE",
                        "target_value": float(settings["target_r"]),
                        "atr_value": work["atr_local"],
                        "minimum_stop_atr": float(settings["minimum_stop_atr"]),
                        "maximum_stop_atr": float(settings["maximum_stop_atr"]),
                        "maximum_hold_hours": float(settings["maximum_hold_hours"]),
                        "cooldown_hours": float(settings["cooldown_hours"]),
                        "daily_key": (
                            profile["profile_id"]
                            + "_"
                            + direction
                            + "_"
                            + work["date_key"]
                        ),
                        "setup_id": (
                            profile["profile_id"]
                            + "_"
                            + direction
                            + "_"
                            + work["date_key"]
                        ),
                    },
                )
            )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def chop_candidates(m30: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    frame = _bar_shape(m30)
    center_bars = int(settings["center_bars"])
    frame["center"] = frame["mid_close"].shift(1).rolling(
        center_bars, min_periods=center_bars
    ).mean()
    frame["scale"] = frame["mid_close"].shift(1).rolling(
        center_bars, min_periods=center_bars
    ).std(ddof=0)
    frame["atr_local"] = atr(frame, int(settings["atr_bars"]))
    frame["z"] = (frame["mid_close"] - frame["center"]) / frame["scale"].replace(
        0.0, np.nan
    )
    memory = int(settings["memory_bars"])
    prior_low_z = frame["z"].shift(1).rolling(memory, min_periods=memory).min()
    prior_high_z = frame["z"].shift(1).rolling(memory, min_periods=memory).max()
    confirmation = int(settings["confirmation_bars"])
    return_n = frame["mid_close"] - frame["mid_close"].shift(confirmation)
    long_mask = (
        frame["regime"].eq("CHOP")
        & (prior_low_z <= -float(settings["excursion_z"]))
        & (frame["mid_close"].shift(1) <= frame["center"].shift(1))
        & (frame["mid_close"] > frame["center"])
        & (return_n > 0)
        & (frame["mid_close"] > frame["mid_open"])
    )
    short_mask = (
        frame["regime"].eq("CHOP")
        & (prior_high_z >= float(settings["excursion_z"]))
        & (frame["mid_close"].shift(1) >= frame["center"].shift(1))
        & (frame["mid_close"] < frame["center"])
        & (return_n < 0)
        & (frame["mid_close"] < frame["mid_open"])
    )
    shared = {
        "atr_value": frame["atr_local"],
        "minimum_stop_atr": float(settings["stop_atr"]),
        "maximum_stop_atr": float(settings["stop_atr"]) + 0.35,
        "maximum_hold_hours": float(settings["maximum_hold_hours"]),
        "cooldown_hours": float(settings["cooldown_hours"]),
        "daily_key": "",
    }
    long = _candidate_rows(
        frame,
        long_mask,
        {
            **shared,
            "specialist_id": CHOP,
            "direction": "LONG",
            "stop_frozen": frame["mid_close"]
            - float(settings["stop_atr"]) * frame["atr_local"],
            "target_kind": "FROZEN_PRICE",
            "target_value": frame["center"]
            + float(settings["target_band_z"]) * frame["scale"],
            "setup_id": "CHOP_LONG_" + frame["timestamp_utc"].astype(str),
        },
    )
    short = _candidate_rows(
        frame,
        short_mask,
        {
            **shared,
            "specialist_id": CHOP,
            "direction": "SHORT",
            "stop_frozen": frame["mid_close"]
            + float(settings["stop_atr"]) * frame["atr_local"],
            "target_kind": "FROZEN_PRICE",
            "target_value": frame["center"]
            - float(settings["target_band_z"]) * frame["scale"],
            "setup_id": "CHOP_SHORT_" + frame["timestamp_utc"].astype(str),
        },
    )
    return pd.concat([long, short], ignore_index=True)


def generate_candidates(
    bars: dict[str, pd.DataFrame], config: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    h4 = classify_h4(bars["H4"], config["regime"])
    routed = {
        name: attach_regime(frame, h4)
        for name, frame in bars.items()
        if name != "H4"
    }
    routed["H4"] = h4
    specialists = config["specialists"]
    candidates = pd.concat(
        [
            trend_candidates(routed["H1"], specialists["trend_pullback"]),
            compression_candidates(
                routed["H1"],
                routed["M15"],
                specialists["compression_break_retest"],
            ),
            session_candidates(routed["M15"], specialists["session_expansion"]),
            chop_candidates(routed["M30"], specialists["chop_rotation"]),
        ],
        ignore_index=True,
    )
    candidates = candidates.sort_values(
        ["signal_time", "specialist_id", "direction"], kind="mergesort"
    ).reset_index(drop=True)
    return candidates, routed


def _simulate_trade(
    m5: pd.DataFrame,
    entry_index: int,
    signal: pd.Series,
    execution: dict[str, Any],
) -> dict[str, Any]:
    direction = str(signal["direction"])
    entry_row = m5.iloc[entry_index]
    entry = float(
        entry_row["ask_open"] if direction == "LONG" else entry_row["bid_open"]
    )
    stop = float(signal["stop_frozen"])
    risk = entry - stop if direction == "LONG" else stop - entry
    atr_value = float(signal["atr_value"])
    if not np.isfinite(risk) or risk <= 0 or not np.isfinite(atr_value) or atr_value <= 0:
        return {"accepted": False, "rejection_reason": "INVALID_STOP"}
    stop_atr = risk / atr_value
    if not (
        float(signal["minimum_stop_atr"])
        <= stop_atr
        <= float(signal["maximum_stop_atr"])
    ):
        return {
            "accepted": False,
            "rejection_reason": "STOP_OUTSIDE_FROZEN_ATR_RANGE",
            "stop_atr": stop_atr,
        }
    if str(signal["target_kind"]) == "R_MULTIPLE":
        expected_reward_r = float(signal["target_value"])
        target = (
            entry + expected_reward_r * risk
            if direction == "LONG"
            else entry - expected_reward_r * risk
        )
    else:
        target = float(signal["target_value"])
        expected_reward_r = (
            target - entry if direction == "LONG" else entry - target
        ) / risk
    if not np.isfinite(target) or expected_reward_r < 1.0:
        return {
            "accepted": False,
            "rejection_reason": "EXPECTED_REWARD_BELOW_1R",
            "stop_atr": stop_atr,
        }
    spread = float(entry_row["ask_open"] - entry_row["bid_open"])
    if spread / risk > float(execution["maximum_entry_spread_r"]):
        return {
            "accepted": False,
            "rejection_reason": "ENTRY_SPREAD_R_LIMIT",
            "stop_atr": stop_atr,
        }
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return {
            "accepted": False,
            "rejection_reason": "RESEARCH_RISK_LIMIT",
            "stop_atr": stop_atr,
        }
    deadline = entry_row["bar_start_utc"] + pd.Timedelta(
        hours=float(signal["maximum_hold_hours"])
    )
    starts = m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    end_index = min(
        len(m5),
        int(
            np.searchsorted(
                starts, np.datetime64(deadline.tz_convert(None)), side="right"
            )
        )
        + 1,
    )
    exit_index = entry_index
    exit_price = entry
    exit_reason = "END_OF_DATA"
    exit_at_open = False
    ambiguous = False
    for index in range(entry_index, end_index):
        row = m5.iloc[index]
        if row["bar_start_utc"] >= deadline:
            exit_index, exit_reason, exit_at_open = index, "MAX_HOLD", True
            exit_price = float(
                row["bid_open"] if direction == "LONG" else row["ask_open"]
            )
            break
        if direction == "LONG":
            if float(row["bid_open"]) < stop:
                exit_index, exit_reason, exit_price, exit_at_open = (
                    index,
                    "GAP_THROUGH_STOP",
                    float(row["bid_open"]),
                    True,
                )
                break
            if float(row["bid_open"]) >= target:
                exit_index, exit_reason, exit_price, exit_at_open = (
                    index,
                    "TARGET_GAP_FROZEN_TARGET",
                    target,
                    True,
                )
                break
            stop_hit = float(row["bid_low"]) <= stop
            target_hit = float(row["bid_high"]) >= target
        else:
            if float(row["ask_open"]) > stop:
                exit_index, exit_reason, exit_price, exit_at_open = (
                    index,
                    "GAP_THROUGH_STOP",
                    float(row["ask_open"]),
                    True,
                )
                break
            if float(row["ask_open"]) <= target:
                exit_index, exit_reason, exit_price, exit_at_open = (
                    index,
                    "TARGET_GAP_FROZEN_TARGET",
                    target,
                    True,
                )
                break
            stop_hit = float(row["ask_high"]) >= stop
            target_hit = float(row["ask_low"]) <= target
        if stop_hit:
            exit_index, exit_price = index, stop
            ambiguous = bool(target_hit)
            exit_reason = "AMBIGUOUS_M5_STOP_FIRST" if ambiguous else "STOP"
            break
        if target_hit:
            exit_index, exit_price, exit_reason = index, target, "TARGET"
            break
        exit_index = index
        exit_price = float(
            row["bid_close"] if direction == "LONG" else row["ask_close"]
        )
    exit_row = m5.iloc[exit_index]
    exit_time = (
        exit_row["bar_start_utc"] if exit_at_open else exit_row["timestamp_utc"]
    )
    sign = 1.0 if direction == "LONG" else -1.0
    net_r = sign * (exit_price - entry) / risk
    holding_days = max(
        0.0,
        (exit_time - entry_row["bar_start_utc"]).total_seconds() / 86400.0,
    )
    extra_cost_r = (
        float(execution["extra_execution_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    stress_r = net_r - extra_cost_r - float(execution["stress_slippage_r"])
    return {
        "accepted": True,
        "entry_time": entry_row["bar_start_utc"],
        "exit_time": exit_time,
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "initial_risk_price": risk,
        "risk_usd": risk_usd,
        "stop_atr": stop_atr,
        "expected_reward_r": expected_reward_r,
        "entry_spread": spread,
        "entry_spread_r": spread / risk,
        "exit_reason": exit_reason,
        "net_r": net_r,
        "stress_net_r": stress_r,
        "extra_cost_r": extra_cost_r,
        "holding_minutes": (
            exit_time - entry_row["bar_start_utc"]
        ).total_seconds()
        / 60.0,
        "ambiguous_m5": ambiguous,
        "current_account_feasible": risk_usd
        <= float(execution["current_account_risk_usd"]),
    }


def run_backtest(
    m5: pd.DataFrame, candidates: pd.DataFrame, config: dict[str, Any]
) -> BacktestResult:
    starts = m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    candidate_rows: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    for _, signals in candidates.groupby("specialist_id", sort=True):
        position_until = pd.Timestamp.min.tz_localize("UTC")
        cooldown_until = pd.Timestamp.min.tz_localize("UTC")
        daily_keys: set[str] = set()
        for _, signal in signals.sort_values("signal_time", kind="mergesort").iterrows():
            ledger = signal.to_dict()
            signal_time = pd.Timestamp(signal["signal_time"])
            entry_index = int(
                np.searchsorted(
                    starts,
                    np.datetime64(signal_time.tz_convert(None)),
                    side="left",
                )
            )
            reason = ""
            if entry_index >= len(m5):
                reason = "NO_M5_ENTRY"
            else:
                entry_time = m5.iloc[entry_index]["bar_start_utc"]
                delay = (entry_time - signal_time).total_seconds() / 60.0
                if delay < 0 or delay > float(
                    config["execution"]["maximum_entry_gap_minutes"]
                ):
                    reason = "NONCONTIGUOUS_M5_ENTRY"
                elif entry_time < position_until:
                    reason = "SPECIALIST_POSITION_OPEN"
                elif entry_time < cooldown_until:
                    reason = "SPECIALIST_COOLDOWN"
                elif (
                    str(signal.get("daily_key", ""))
                    and str(signal["daily_key"]) in daily_keys
                ):
                    reason = "FROZEN_DAILY_CAP"
            if reason:
                ledger.update(
                    {"signal_accepted": False, "rejection_reason": reason}
                )
                candidate_rows.append(ledger)
                continue
            outcome = _simulate_trade(m5, entry_index, signal, config["execution"])
            if not outcome["accepted"]:
                ledger.update(
                    {
                        "signal_accepted": False,
                        "rejection_reason": outcome["rejection_reason"],
                    }
                )
                candidate_rows.append(ledger)
                continue
            ledger.update(
                {
                    "signal_accepted": True,
                    "rejection_reason": "",
                    "entry_time": outcome["entry_time"],
                }
            )
            candidate_rows.append(ledger)
            trade = dict(ledger)
            trade.update(
                {key: value for key, value in outcome.items() if key != "accepted"}
            )
            trades.append(trade)
            position_until = outcome["exit_time"]
            cooldown_until = outcome["exit_time"] + pd.Timedelta(
                hours=float(signal["cooldown_hours"])
            )
            if str(signal.get("daily_key", "")):
                daily_keys.add(str(signal["daily_key"]))
    candidate_frame = pd.DataFrame(candidate_rows)
    trade_frame = pd.DataFrame(trades)
    if not candidate_frame.empty:
        candidate_frame = candidate_frame.sort_values(
            ["signal_time", "specialist_id"], kind="mergesort"
        ).reset_index(drop=True)
    if not trade_frame.empty:
        trade_frame = trade_frame.sort_values(
            ["entry_time", "specialist_id"], kind="mergesort"
        ).reset_index(drop=True)
    return BacktestResult(candidate_frame, trade_frame)


def closed_drawdown(values: pd.Series) -> float:
    equity = values.fillna(0.0).cumsum()
    if equity.empty:
        return 0.0
    return float((equity.cummax() - equity).max())


def profit_factor(values: pd.Series) -> float | None:
    positive = float(values.loc[values > 0].sum())
    negative = float(-values.loc[values < 0].sum())
    if negative == 0:
        return None if positive == 0 else float("inf")
    return positive / negative


def metrics(
    trades: pd.DataFrame, source_days: int, top_winners: int
) -> dict[str, Any]:
    values = (
        trades["stress_net_r"].astype(float)
        if not trades.empty
        else pd.Series(dtype=float)
    )
    monthly = (
        trades.assign(month=trades["entry_time"].dt.tz_localize(None).dt.to_period("M"))
        .groupby("month", sort=True)["stress_net_r"]
        .sum()
        if not trades.empty
        else pd.Series(dtype=float)
    )
    top_removed = (
        values.drop(values.nlargest(min(top_winners, len(values))).index)
        if len(values)
        else values
    )
    return {
        "trades": int(len(trades)),
        "source_days": int(source_days),
        "trades_per_source_day": float(len(trades) / source_days)
        if source_days
        else 0.0,
        "net_r": float(trades["net_r"].sum()) if not trades.empty else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "win_rate": float((values > 0).mean()) if len(values) else 0.0,
        "positive_active_month_share": float((monthly > 0).mean())
        if len(monthly)
        else 0.0,
        "active_months": int(len(monthly)),
        "closed_drawdown_r": closed_drawdown(values),
        "top_winners_removed": int(min(top_winners, len(values))),
        "top_winners_removed_stress_net_r": float(top_removed.sum()),
    }


def evaluate_gate(
    value: dict[str, Any], gate: dict[str, Any]
) -> tuple[bool, dict[str, bool]]:
    pf = value["stress_pf"]
    checks = {
        "minimum_trades": value["trades"] >= int(gate["minimum_trades"]),
        "minimum_stress_pf": pf is not None
        and pf >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": value["average_stress_r"]
        >= float(gate["minimum_average_stress_r"]),
        "minimum_positive_active_month_share": value[
            "positive_active_month_share"
        ]
        >= float(gate["minimum_positive_active_month_share"]),
        "maximum_closed_drawdown_r": value["closed_drawdown_r"]
        <= float(gate["maximum_closed_drawdown_r"]),
        "top_winners_removed_positive": value[
            "top_winners_removed_stress_net_r"
        ]
        > 0,
    }
    if "minimum_trades_per_source_day" in gate:
        checks["minimum_trades_per_source_day"] = value[
            "trades_per_source_day"
        ] >= float(gate["minimum_trades_per_source_day"])
    return all(checks.values()), checks


def stage_audit(
    trades: pd.DataFrame, m5: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    metric_rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {}
    source_dates = m5.assign(date=m5["bar_start_utc"].dt.date)
    for specialist_id in SPECIALISTS:
        eligible = True
        audit[specialist_id] = {}
        own = (
            trades.loc[trades["specialist_id"].eq(specialist_id)]
            if not trades.empty
            else trades
        )
        for stage, (start_text, end_text) in config["windows"].items():
            start, end = pd.Timestamp(start_text), pd.Timestamp(end_text)
            subset = (
                own.loc[(own["entry_time"] >= start) & (own["entry_time"] < end)]
                if not own.empty
                else own
            )
            days = int(
                source_dates.loc[
                    (source_dates["bar_start_utc"] >= start)
                    & (source_dates["bar_start_utc"] < end),
                    "date",
                ].nunique()
            )
            gate = config["gates"][stage]
            value = metrics(subset, days, int(gate["top_winners_removed"]))
            passed, checks = evaluate_gate(value, gate)
            decision_eligible = bool(eligible)
            promoted = bool(decision_eligible and passed)
            audit[specialist_id][stage] = {
                "decision_eligible": decision_eligible,
                "raw_gate_pass": passed,
                "promoted": promoted,
                "checks": checks,
                "metrics": value,
            }
            metric_rows.append(
                {
                    "specialist_id": specialist_id,
                    "stage": stage,
                    "decision_eligible": decision_eligible,
                    "raw_gate_pass": passed,
                    "promoted": promoted,
                    **value,
                }
            )
            eligible = promoted
    return pd.DataFrame(metric_rows), audit


def independence_audit(
    trades: pd.DataFrame, survivor_ids: list[str], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    limits = config["portfolio_gates"]
    threshold = pd.Timedelta(minutes=float(limits["same_opportunity_minutes"]))
    all_pass = True
    for left_id, right_id in combinations(survivor_ids, 2):
        left = trades.loc[trades["specialist_id"].eq(left_id)].sort_values(
            "entry_time"
        )
        right = trades.loc[trades["specialist_id"].eq(right_id)].sort_values(
            "entry_time"
        )
        overlap = 0
        for _, trade in left.iterrows():
            delta = (
                right.loc[
                    right["direction"].eq(trade["direction"]), "entry_time"
                ]
                - trade["entry_time"]
            ).abs()
            overlap += int(bool(len(delta) and delta.min() <= threshold))
        overlap_share = overlap / max(1, min(len(left), len(right)))
        left_daily = (
            left.assign(date=left["entry_time"].dt.date)
            .groupby("date")["stress_net_r"]
            .sum()
        )
        right_daily = (
            right.assign(date=right["entry_time"].dt.date)
            .groupby("date")["stress_net_r"]
            .sum()
        )
        joined = pd.concat(
            [left_daily, right_daily], axis=1, keys=["left", "right"]
        ).fillna(0.0)
        correlation = (
            float(joined["left"].corr(joined["right"]))
            if len(joined) >= 3
            else 0.0
        )
        if not np.isfinite(correlation):
            correlation = 0.0
        passed = overlap_share <= float(
            limits["maximum_same_direction_overlap_share"]
        ) and abs(correlation) <= float(
            limits["maximum_absolute_daily_pnl_correlation"]
        )
        all_pass &= passed
        rows.append(
            {
                "left": left_id,
                "right": right_id,
                "same_direction_overlap_share": overlap_share,
                "daily_stress_pnl_correlation": correlation,
                "pass": bool(passed),
            }
        )
    return rows, all_pass


def portfolio_exam(
    trades: pd.DataFrame,
    survivor_ids: list[str],
    m5: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    start, end = map(pd.Timestamp, config["windows"]["exam"])
    source = trades.loc[
        trades["specialist_id"].isin(survivor_ids)
        & (trades["entry_time"] >= start)
        & (trades["entry_time"] < end)
    ].sort_values(["entry_time", "specialist_id"], kind="mergesort")
    accepted: list[pd.Series] = []
    active: list[pd.Timestamp] = []
    daily_counts: dict[Any, int] = {}
    limits = config["portfolio_gates"]
    for _, trade in source.iterrows():
        active = [exit_time for exit_time in active if exit_time > trade["entry_time"]]
        day = trade["entry_time"].date()
        if len(active) >= int(limits["maximum_concurrent_trades"]):
            continue
        if daily_counts.get(day, 0) >= int(limits["maximum_trades_per_utc_day"]):
            continue
        accepted.append(trade)
        active.append(trade["exit_time"])
        daily_counts[day] = daily_counts.get(day, 0) + 1
    portfolio = pd.DataFrame(accepted)
    days = int(
        m5.loc[
            (m5["bar_start_utc"] >= start) & (m5["bar_start_utc"] < end),
            "bar_start_utc",
        ].dt.date.nunique()
    )
    value = metrics(portfolio, days, 5)
    checks = {
        "minimum_exam_trades_per_source_day": value["trades_per_source_day"]
        >= float(limits["minimum_exam_trades_per_source_day"]),
        "minimum_exam_stress_pf": value["stress_pf"] is not None
        and value["stress_pf"] >= float(limits["minimum_exam_stress_pf"]),
        "minimum_exam_average_stress_r": value["average_stress_r"]
        >= float(limits["minimum_exam_average_stress_r"]),
        "maximum_exam_closed_drawdown_r": value["closed_drawdown_r"]
        <= float(limits["maximum_exam_closed_drawdown_r"]),
    }
    return portfolio, {
        "metrics": value,
        "checks": checks,
        "pass": all(checks.values()),
    }
