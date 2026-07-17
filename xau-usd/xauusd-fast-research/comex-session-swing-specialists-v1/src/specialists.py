from __future__ import annotations

import numpy as np
import pandas as pd


VALUE_MIGRATION = "COMEX_SESSION_VALUE_MIGRATION_SWING_V1"
TREND_DAY = "COMEX_SESSION_TREND_DAY_CARRY_V1"
BALANCED_REVERSAL = "COMEX_SESSION_BALANCED_EXCESS_REVERSAL_V1"
FAMILIES = (VALUE_MIGRATION, TREND_DAY, BALANCED_REVERSAL)


def wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def completed_h1_atr(m5: pd.DataFrame, period: int) -> pd.DataFrame:
    frame = m5.copy()
    frame["bucket_h1"] = frame["bar_start_utc"].dt.floor("1h")
    grouped = frame.groupby("bucket_h1", sort=True, observed=True)
    counts = grouped.size()
    h1 = grouped.agg(
        mid_open=("mid_open", "first"),
        mid_high=("mid_high", "max"),
        mid_low=("mid_low", "min"),
        mid_close=("mid_close", "last"),
    ).loc[counts.eq(12)].reset_index()
    h1["timestamp_h1"] = h1["bucket_h1"] + pd.Timedelta(hours=1)
    previous = h1["mid_close"].shift(1)
    true_range = pd.concat(
        [
            h1["mid_high"] - h1["mid_low"],
            (h1["mid_high"] - previous).abs(),
            (h1["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    h1["h1_atr"] = wilder(true_range, period)
    return h1[["timestamp_h1", "h1_atr"]]


def prepare_sessions(spot_m5: pd.DataFrame, auction_m5: pd.DataFrame, config: dict) -> pd.DataFrame:
    finals = auction_m5.sort_values("available_time_utc").groupby(
        "session_date", observed=True
    ).tail(1).copy()
    aggregates = auction_m5.groupby("session_date", sort=True, observed=True).agg(
        session_open=("open", "first"),
        session_high=("high", "max"),
        session_low=("low", "min"),
        session_close=("close", "last"),
    ).reset_index()
    finals = finals.merge(aggregates, on="session_date", how="left", validate="one_to_one")
    finals["session_range"] = finals["session_high"] - finals["session_low"]
    lookback = int(config["signal"]["session_range_median_lookback"])
    finals["prior_session_range_median"] = finals["session_range"].shift(1).rolling(
        lookback, min_periods=lookback
    ).median()
    span = finals["session_range"].replace(0.0, np.nan)
    finals["session_close_location"] = (
        finals["session_close"] - finals["session_low"]
    ) / span
    spot = spot_m5[
        ["timestamp_utc", "mid_close", "bid_open", "ask_open"]
    ].merge(
        finals,
        left_on="timestamp_utc",
        right_on="available_time_utc",
        how="inner",
        validate="one_to_one",
    )
    h1 = completed_h1_atr(spot_m5, int(config["signal"]["h1_atr_period"]))
    return pd.merge_asof(
        spot.sort_values("timestamp_utc"),
        h1.sort_values("timestamp_h1"),
        left_on="timestamp_utc",
        right_on="timestamp_h1",
        direction="backward",
        allow_exact_matches=True,
    )


def candidate_rows(
    frame: pd.DataFrame,
    mask: pd.Series,
    direction: pd.Series,
    family: str,
    config: dict,
) -> pd.DataFrame:
    selected = frame.loc[mask & direction.ne(0)].copy()
    if selected.empty:
        return pd.DataFrame()
    selected["direction_sign"] = direction.loc[selected.index].astype(int)
    selected["direction"] = np.where(selected["direction_sign"] > 0, "LONG", "SHORT")
    selected["family_id"] = family
    selected["signal_time"] = selected["available_time_utc"]
    selected["atr_value"] = selected["h1_atr"]
    settings = config["families"][family]
    selected["stop_frozen"] = selected["mid_close"] - (
        selected["direction_sign"] * float(settings["stop_atr"]) * selected["h1_atr"]
    )
    selected["target_r"] = float(settings["target_r"])
    selected["maximum_hold_hours"] = float(settings["maximum_hold_hours"])
    return selected[
        [
            "family_id", "signal_time", "session_date", "direction", "direction_sign",
            "stop_frozen", "atr_value", "target_r", "maximum_hold_hours",
            "session_poc", "prior_session_poc", "session_value_low", "session_value_high",
            "prior_session_value_low", "prior_session_value_high", "session_close_location",
            "cumulative_delta_ratio", "cumulative_volume_ratio", "session_range",
            "prior_session_range_median",
        ]
    ]


def generate_candidates(
    spot_m5: pd.DataFrame, auction_m5: pd.DataFrame, config: dict
) -> pd.DataFrame:
    frame = prepare_sessions(spot_m5, auction_m5, config)
    setting = config["signal"]
    atr_value = frame["h1_atr"]
    migration_up = frame["session_poc"] > frame["prior_session_value_high"]
    migration_down = frame["session_poc"] < frame["prior_session_value_low"]
    migration_direction = pd.Series(
        np.select([migration_up, migration_down], [1, -1], default=0), index=frame.index
    )
    migration_mask = (
        np.isfinite(atr_value)
        & (migration_direction * (frame["session_close"] - frame["session_poc"]) > 0)
        & (
            migration_direction * frame["cumulative_delta_ratio"]
            >= float(setting["value_migration_minimum_directional_delta"])
        )
        & (frame["cumulative_volume_ratio"] >= float(setting["minimum_volume_ratio"]))
    )

    close_location = frame["session_close_location"]
    trend_up = close_location >= float(setting["trend_day_minimum_close_location"])
    trend_down = close_location <= 1.0 - float(setting["trend_day_minimum_close_location"])
    trend_direction = pd.Series(
        np.select([trend_up, trend_down], [1, -1], default=0), index=frame.index
    )
    trend_mask = (
        np.isfinite(atr_value)
        & (
            frame["session_range"] / frame["prior_session_range_median"]
            >= float(setting["trend_day_minimum_range_ratio"])
        )
        & (
            trend_direction * frame["cumulative_delta_ratio"]
            >= float(setting["trend_day_minimum_directional_delta"])
        )
        & (
            trend_direction * (frame["session_poc"] - frame["prior_session_poc"]) / atr_value
            >= float(setting["trend_day_minimum_poc_shift_h1_atr"])
        )
        & (frame["cumulative_volume_ratio"] >= float(setting["minimum_volume_ratio"]))
    )

    balanced = frame["session_poc"].between(
        frame["prior_session_value_low"], frame["prior_session_value_high"]
    )
    excess_high = frame["session_close"] >= frame["prior_session_value_high"] + (
        float(setting["balanced_excess_minimum_extension_h1_atr"]) * atr_value
    )
    excess_low = frame["session_close"] <= frame["prior_session_value_low"] - (
        float(setting["balanced_excess_minimum_extension_h1_atr"]) * atr_value
    )
    reversal_direction = pd.Series(
        np.select([excess_high, excess_low], [-1, 1], default=0), index=frame.index
    )
    reversal_mask = (
        np.isfinite(atr_value)
        & balanced
        & (
            frame["cumulative_delta_ratio"].abs()
            <= float(setting["balanced_excess_maximum_absolute_delta"])
        )
    )
    candidates = pd.concat(
        [
            candidate_rows(frame, migration_mask, migration_direction, VALUE_MIGRATION, config),
            candidate_rows(frame, trend_mask, trend_direction, TREND_DAY, config),
            candidate_rows(frame, reversal_mask, reversal_direction, BALANCED_REVERSAL, config),
        ],
        ignore_index=True,
    )
    if candidates.empty:
        return pd.DataFrame(
            columns=["family_id", "signal_time", "direction", "direction_sign", "stop_frozen", "atr_value", "target_r", "maximum_hold_hours"]
        )
    return candidates.sort_values(["signal_time", "family_id"], kind="mergesort").reset_index(drop=True)
