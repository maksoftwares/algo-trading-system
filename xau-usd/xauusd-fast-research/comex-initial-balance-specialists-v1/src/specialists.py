from __future__ import annotations

import numpy as np
import pandas as pd


EXPANSION = "COMEX_INITIAL_BALANCE_EXPANSION_V1"
FAILED_EXPANSION = "COMEX_INITIAL_BALANCE_FAILED_EXPANSION_V1"
POC_MIGRATION = "COMEX_DEVELOPING_POC_MIGRATION_V1"
FAMILIES = (EXPANSION, FAILED_EXPANSION, POC_MIGRATION)


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


def prepare_frame(spot_m5: pd.DataFrame, auction_m5: pd.DataFrame, config: dict) -> pd.DataFrame:
    spot = spot_m5.copy()
    spot["spot_atr"] = atr(spot, int(config["signal"]["spot_atr_period"]))
    frame = spot.merge(
        auction_m5,
        left_on="timestamp_utc",
        right_on="available_time_utc",
        how="inner",
        validate="one_to_one",
        suffixes=("_spot", "_futures"),
    ).sort_values(["session_date", "available_time_utc"])
    setting = config["signal"]
    initial = frame.loc[
        frame["available_local_time"] <= setting["initial_balance_complete_local"]
    ]
    levels = initial.groupby("session_date", observed=True).agg(
        initial_balance_high=("high", "max"),
        initial_balance_low=("low", "min"),
    )
    opening = frame.loc[
        frame["available_local_time"].eq(setting["opening_poc_local"]),
        ["session_date", "running_poc"],
    ].rename(columns={"running_poc": "opening_poc"})
    frame = frame.merge(levels, on="session_date", how="left", validate="many_to_one")
    frame = frame.merge(opening, on="session_date", how="left", validate="many_to_one")
    frame["initial_balance_mid"] = (
        frame["initial_balance_high"] + frame["initial_balance_low"]
    ) / 2.0
    return frame.reset_index(drop=True)


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
    selected["atr_value"] = selected["spot_atr"]
    settings = config["families"][family]
    selected["stop_frozen"] = selected["mid_close"] - (
        selected["direction_sign"] * float(settings["stop_atr"]) * selected["spot_atr"]
    )
    selected["target_r"] = float(settings["target_r"])
    selected["maximum_hold_hours"] = float(settings["maximum_hold_hours"])
    selected = selected.drop_duplicates(["session_date", "direction"], keep="first")
    return selected[
        [
            "family_id",
            "signal_time",
            "session_date",
            "direction",
            "direction_sign",
            "stop_frozen",
            "atr_value",
            "target_r",
            "maximum_hold_hours",
            "initial_balance_high",
            "initial_balance_low",
            "opening_poc",
            "running_poc",
            "cumulative_delta_ratio",
            "cumulative_volume_ratio",
        ]
    ]


def generate_candidates(
    spot_m5: pd.DataFrame, auction_m5: pd.DataFrame, config: dict
) -> pd.DataFrame:
    frame = prepare_frame(spot_m5, auction_m5, config)
    settings = config["signal"]
    atr_value = frame["spot_atr"]
    local = frame["available_local_time"]
    after_initial = local.ge(settings["initial_balance_complete_local"])
    within_decision = local.le(settings["decision_end_local"])

    expansion_high = frame["close"] >= frame["initial_balance_high"] + (
        float(settings["expansion_boundary_buffer_atr"]) * atr_value
    )
    expansion_low = frame["close"] <= frame["initial_balance_low"] - (
        float(settings["expansion_boundary_buffer_atr"]) * atr_value
    )
    expansion_direction = pd.Series(
        np.select([expansion_high, expansion_low], [1, -1], default=0), index=frame.index
    )
    poc_displacement = expansion_direction * (
        frame["running_poc"] - frame["initial_balance_mid"]
    ) / atr_value
    expansion_mask = (
        after_initial
        & within_decision
        & np.isfinite(atr_value)
        & (poc_displacement >= float(settings["expansion_minimum_poc_displacement_atr"]))
        & (
            expansion_direction * frame["cumulative_delta_ratio"]
            >= float(settings["expansion_minimum_directional_delta_ratio"])
        )
        & (frame["cumulative_volume_ratio"] >= float(settings["expansion_minimum_volume_ratio"]))
    )

    high_failure = (
        (frame["high"] >= frame["initial_balance_high"] + float(settings["failure_minimum_excursion_atr"]) * atr_value)
        & (frame["close"] <= frame["initial_balance_high"] - float(settings["failure_minimum_reentry_atr"]) * atr_value)
        & (frame["close"] < frame["open"])
    )
    low_failure = (
        (frame["low"] <= frame["initial_balance_low"] - float(settings["failure_minimum_excursion_atr"]) * atr_value)
        & (frame["close"] >= frame["initial_balance_low"] + float(settings["failure_minimum_reentry_atr"]) * atr_value)
        & (frame["close"] > frame["open"])
    )
    failed_direction = pd.Series(
        np.select([high_failure, low_failure], [-1, 1], default=0), index=frame.index
    )
    failed_mask = (
        after_initial
        & within_decision
        & np.isfinite(atr_value)
        & (
            frame["cumulative_delta_ratio"].abs()
            <= float(settings["failure_maximum_absolute_delta_ratio"])
        )
    )

    migration = frame["running_poc"] - frame["opening_poc"]
    migration_direction = pd.Series(
        np.sign(migration.fillna(0.0)).astype(int), index=frame.index
    )
    poc_mask = (
        local.eq(settings["poc_decision_local"])
        & np.isfinite(atr_value)
        & (migration.abs() / atr_value >= float(settings["poc_minimum_migration_atr"]))
        & (migration_direction * (frame["close"] - frame["opening_poc"]) > 0)
        & (
            migration_direction * frame["cumulative_delta_ratio"]
            >= float(settings["poc_minimum_directional_delta_ratio"])
        )
        & (frame["cumulative_volume_ratio"] >= float(settings["poc_minimum_volume_ratio"]))
    )
    candidates = pd.concat(
        [
            candidate_rows(frame, expansion_mask, expansion_direction, EXPANSION, config),
            candidate_rows(frame, failed_mask, failed_direction, FAILED_EXPANSION, config),
            candidate_rows(frame, poc_mask, migration_direction, POC_MIGRATION, config),
        ],
        ignore_index=True,
    )
    if candidates.empty:
        return pd.DataFrame(
            columns=[
                "family_id",
                "signal_time",
                "session_date",
                "direction",
                "direction_sign",
                "stop_frozen",
                "atr_value",
                "target_r",
                "maximum_hold_hours",
            ]
        )
    return candidates.sort_values(["signal_time", "family_id"], kind="mergesort").reset_index(drop=True)
