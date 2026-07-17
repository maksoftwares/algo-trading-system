from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


DXY = "M15_DXY_LEAD_CONTINUATION_V1"
BOND = "M15_BOND_LEAD_CONTINUATION_V1"
DISLOCATION = "M15_MACRO_DISLOCATION_REVERSAL_V1"
FAMILIES = (DXY, BOND, DISLOCATION)


def wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
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
    gold_m15: pd.DataFrame, macro_m15: pd.DataFrame, geometry: dict[str, Any]
) -> pd.DataFrame:
    frame = gold_m15.merge(macro_m15, on="timestamp_utc", how="inner", validate="one_to_one")
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    frame["atr14"] = atr(frame, 14)
    span = (frame["mid_high"] - frame["mid_low"]).replace(0.0, np.nan)
    frame["body_fraction"] = (frame["mid_close"] - frame["mid_open"]).abs() / span
    frame["body_atr"] = (frame["mid_close"] - frame["mid_open"]) / frame["atr14"]
    frame["close_location"] = (frame["mid_close"] - frame["mid_low"]) / span
    return_bars = int(geometry["macro_return_bars"])
    scale_bars = int(geometry["macro_scale_bars"])
    scale_min = int(geometry["macro_scale_minimum_bars"])
    for prefix in ("dollaridxusd", "ustbondtrusd"):
        one_hour = np.log(frame[f"{prefix}_close"] / frame[f"{prefix}_close"].shift(return_bars))
        scale = one_hour.shift(1).rolling(scale_bars, min_periods=scale_min).std(ddof=0)
        frame[f"{prefix}_return_1h"] = one_hour
        frame[f"{prefix}_return_z"] = one_hour / scale.replace(0.0, np.nan)
    frame["dxy_gold_pressure_z"] = -frame["dollaridxusd_return_z"]
    frame["bond_gold_pressure_z"] = frame["ustbondtrusd_return_z"]
    frame["gold_return_1h_atr"] = (
        frame["mid_close"] - frame["mid_close"].shift(return_bars)
    ) / frame["atr14"]
    frame["gold_prior_1h_atr"] = (
        frame["mid_close"].shift(1) - frame["mid_close"].shift(return_bars + 1)
    ) / frame["atr14"]
    movement = frame["mid_close"].diff().abs().rolling(16, min_periods=16).sum()
    frame["efficiency_ratio_16"] = (
        frame["mid_close"] - frame["mid_close"].shift(16)
    ).abs() / movement.replace(0.0, np.nan)
    return frame


def _build(
    frame: pd.DataFrame,
    mask: pd.Series,
    direction: pd.Series,
    family: str,
    settings: dict[str, Any],
    quality: pd.Series,
) -> pd.DataFrame:
    selected = frame.loc[mask].copy()
    if selected.empty:
        return pd.DataFrame()
    selected["direction_sign"] = direction.loc[selected.index].astype(int)
    selected["direction"] = np.where(selected["direction_sign"] > 0, "LONG", "SHORT")
    selected["family_id"] = family
    selected["signal_time"] = selected["timestamp_utc"]
    selected["atr_value"] = selected["atr14"]
    selected["stop_frozen"] = selected["mid_close"] - (
        selected["direction_sign"] * float(settings["stop_atr"]) * selected["atr14"]
    )
    selected["target_r"] = float(settings["target_r"])
    selected["maximum_hold_hours"] = float(settings["maximum_hold_hours"])
    selected["quality_score"] = quality.loc[selected.index].astype(float)
    selected["model_score"] = selected["quality_score"]
    selected["dir_gold_return_1h_atr"] = selected["direction_sign"] * selected["gold_return_1h_atr"]
    selected["dir_gold_prior_1h_atr"] = selected["direction_sign"] * selected["gold_prior_1h_atr"]
    selected["dir_body_atr"] = selected["direction_sign"] * selected["body_atr"]
    selected["dir_close_location"] = np.where(
        selected["direction_sign"] > 0,
        selected["close_location"],
        1.0 - selected["close_location"],
    )
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
        "dollaridxusd_return_z",
        "ustbondtrusd_return_z",
        "dxy_gold_pressure_z",
        "bond_gold_pressure_z",
        "dir_gold_return_1h_atr",
        "dir_gold_prior_1h_atr",
        "dir_body_atr",
        "body_fraction",
        "dir_close_location",
        "efficiency_ratio_16",
    ]
    return selected[columns].reset_index(drop=True)


def generate_candidates(
    gold_m15: pd.DataFrame, macro_m15: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    geometry = config["feature_geometry"]
    frame = prepare_frame(gold_m15, macro_m15, geometry)
    dxy_pressure = frame["dxy_gold_pressure_z"]
    bond_pressure = frame["bond_gold_pressure_z"]
    dxy_direction = np.sign(dxy_pressure).astype("Int64")
    bond_direction = np.sign(bond_pressure).astype("Int64")
    continuation_min = float(geometry["continuation_gold_move_atr_min"])
    continuation_max = float(geometry["continuation_gold_move_atr_max"])
    body_min = float(geometry["minimum_body_atr"])
    body_fraction_min = float(geometry["minimum_body_fraction"])
    efficiency_min = float(geometry["minimum_efficiency_ratio"])
    quiet_max = float(geometry["quiet_other_asset_z_max"])
    opposing_max = float(geometry["maximum_opposing_other_pressure_z"])

    dxy_gold_move = dxy_direction * frame["gold_return_1h_atr"]
    dxy_body = dxy_direction * frame["body_atr"]
    dxy_mask = (
        np.isfinite(frame["atr14"])
        & (dxy_direction != 0)
        & (dxy_pressure.abs() >= float(geometry["continuation_impulse_z_min"]))
        & (bond_pressure.abs() < quiet_max)
        & (dxy_direction * bond_pressure >= -opposing_max)
        & dxy_gold_move.between(continuation_min, continuation_max)
        & (dxy_body >= body_min)
        & (frame["body_fraction"] >= body_fraction_min)
        & (frame["efficiency_ratio_16"] >= efficiency_min)
    )

    bond_gold_move = bond_direction * frame["gold_return_1h_atr"]
    bond_body = bond_direction * frame["body_atr"]
    bond_mask = (
        np.isfinite(frame["atr14"])
        & (bond_direction != 0)
        & (bond_pressure.abs() >= float(geometry["continuation_impulse_z_min"]))
        & (dxy_pressure.abs() < quiet_max)
        & (bond_direction * dxy_pressure >= -opposing_max)
        & bond_gold_move.between(continuation_min, continuation_max)
        & (bond_body >= body_min)
        & (frame["body_fraction"] >= body_fraction_min)
        & (frame["efficiency_ratio_16"] >= efficiency_min)
    )

    consensus = (
        (np.sign(dxy_pressure) == np.sign(bond_pressure))
        & (dxy_pressure.abs() >= float(geometry["consensus_impulse_z_min"]))
        & (bond_pressure.abs() >= float(geometry["consensus_impulse_z_min"]))
    )
    consensus_direction = np.sign(dxy_pressure).astype("Int64")
    dislocation_prior = consensus_direction * frame["gold_prior_1h_atr"]
    dislocation_body = consensus_direction * frame["body_atr"]
    directional_close = pd.Series(
        np.where(consensus_direction > 0, frame["close_location"], 1.0 - frame["close_location"]),
        index=frame.index,
    )
    dislocation_mask = (
        np.isfinite(frame["atr14"])
        & consensus
        & (consensus_direction != 0)
        & (dislocation_prior <= float(geometry["maximum_prior_gold_alignment_atr"]))
        & (dislocation_body >= body_min)
        & (frame["body_fraction"] >= body_fraction_min)
        & (directional_close >= float(geometry["minimum_directional_close_location"]))
        & (frame["efficiency_ratio_16"] <= float(geometry["maximum_dislocation_efficiency_ratio"]))
    )

    candidates = pd.concat(
        [
            _build(frame, dxy_mask, dxy_direction, DXY, config["families"][DXY], dxy_pressure.abs()),
            _build(frame, bond_mask, bond_direction, BOND, config["families"][BOND], bond_pressure.abs()),
            _build(
                frame,
                dislocation_mask,
                consensus_direction,
                DISLOCATION,
                config["families"][DISLOCATION],
                dxy_pressure.abs() + bond_pressure.abs(),
            ),
        ],
        ignore_index=True,
    )
    if candidates.empty:
        return candidates
    numeric = [
        "stop_frozen",
        "atr_value",
        "quality_score",
        "dollaridxusd_return_z",
        "ustbondtrusd_return_z",
        "dir_body_atr",
    ]
    candidates = candidates.loc[np.isfinite(candidates[numeric]).all(axis=1)]
    return candidates.sort_values(["signal_time", "family_id"], kind="mergesort").reset_index(drop=True)
