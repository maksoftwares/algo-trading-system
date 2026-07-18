from __future__ import annotations

import hashlib
from itertools import product
import json
from typing import Any, Mapping

import numpy as np
import pandas as pd


def _space(**values: list[Any]) -> list[dict[str, Any]]:
    keys = tuple(values)
    return [
        dict(zip(keys, combination, strict=True))
        for combination in product(*(values[key] for key in keys))
    ]


def parameter_space(mechanic: str, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    geometries = list(config["geometries"])
    hours = ["ALL_LIQUID", "LONDON", "LONDON_NY", "NEW_YORK"]
    if mechanic == "CHOP_PREVIOUS_DAY_EXTREME_RECLAIM":
        return _space(
            sweep_atr=[0.0, 0.03, 0.07, 0.12],
            reentry_atr=[0.0, 0.03, 0.07],
            wick_min=[0.1, 0.25, 0.4],
            anchor=["MID", "CLOSE"],
            hour_window=hours,
            geometry_id=geometries,
        )
    if mechanic == "CHOP_ASIA_EXTREME_RECLAIM":
        return [
            params
            for params in _space(
                sweep_atr=[0.0, 0.03, 0.07, 0.12],
                reentry_atr=[0.0, 0.03, 0.07],
                wick_min=[0.1, 0.25, 0.4],
                asia_range_atr_min=[0.5, 0.9, 1.3],
                asia_range_atr_max=[2.0, 3.5, 5.0],
                hour_window=["LONDON", "LONDON_NY", "NEW_YORK"],
                geometry_id=geometries,
            )
            if float(params["asia_range_atr_min"])
            < float(params["asia_range_atr_max"])
        ]
    if mechanic == "CHOP_DAY_VWAP_ROTATION":
        return _space(
            deviation_atr=[0.25, 0.4, 0.6, 0.8, 1.0],
            confirmation=["CANDLE", "WICK", "EITHER"],
            wick_min=[0.1, 0.25, 0.4],
            minimum_day_bars=[8, 16, 24, 32],
            maximum_day_displacement_atr=[1.0, 2.0, 3.0],
            hour_window=hours,
            geometry_id=geometries,
        )
    if mechanic == "CHOP_WEEK_OPEN_ROTATION":
        return _space(
            deviation_atr=[0.4, 0.6, 0.9, 1.2, 1.6],
            confirmation=["CANDLE", "WICK", "EITHER"],
            wick_min=[0.1, 0.25, 0.4],
            minimum_week_bars=[8, 24, 48],
            hour_window=hours,
            geometry_id=geometries,
        )
    if mechanic == "CHOP_ROLLING_BALANCE_REENTRY":
        return [
            params
            for params in _space(
                lookback=[24, 48, 96, 192],
                sweep_atr=[0.0, 0.03, 0.07, 0.12],
                reentry_atr=[0.0, 0.03, 0.07],
                wick_min=[0.1, 0.25, 0.4],
                width_atr_min=[0.75, 1.5, 2.5],
                width_atr_max=[4.0, 6.0, 8.0],
                hour_window=hours,
                geometry_id=geometries,
            )
            if float(params["width_atr_min"]) < float(params["width_atr_max"])
        ]
    raise KeyError(mechanic)


def add_anchor_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(
        drop=True
    ).copy()
    starts = pd.to_datetime(result["bar_start_utc"], utc=True)
    day = starts.dt.normalize()
    hour = starts.dt.hour
    result["utc_day"] = day
    result["hour"] = hour
    grouped = result.groupby("utc_day", sort=False)
    result["day_bar_number"] = grouped.cumcount() + 1
    typical = (result["mid_high"] + result["mid_low"] + result["mid_close"]) / 3.0
    weight = result["tick_count"].astype(float).clip(lower=1.0)
    cumulative_weight = weight.groupby(day, sort=False).cumsum()
    result["day_vwap"] = (typical * weight).groupby(day, sort=False).cumsum() / cumulative_weight
    result["day_displacement_atr"] = (
        result["mid_close"] - grouped["mid_open"].transform("first")
    ) / result["atr14"]

    daily = grouped.agg(
        current_day_high=("mid_high", "max"),
        current_day_low=("mid_low", "min"),
        current_day_close=("mid_close", "last"),
    )
    previous = daily.shift(1).rename(
        columns={
            "current_day_high": "previous_day_high",
            "current_day_low": "previous_day_low",
            "current_day_close": "previous_day_close",
        }
    )
    result = result.join(previous, on="utc_day")
    result["previous_day_mid"] = (
        result["previous_day_high"] + result["previous_day_low"]
    ) / 2.0

    asian = result.loc[hour.between(0, 5)].groupby("utc_day", sort=False).agg(
        asia_high=("mid_high", "max"),
        asia_low=("mid_low", "min"),
    )
    result = result.join(asian, on="utc_day")
    unavailable = hour.lt(6)
    result.loc[unavailable, ["asia_high", "asia_low"]] = np.nan
    result["asia_mid"] = (result["asia_high"] + result["asia_low"]) / 2.0
    result["asia_range_atr"] = (
        result["asia_high"] - result["asia_low"]
    ) / result["atr14"]

    week = day - pd.to_timedelta(day.dt.weekday, unit="D")
    result["utc_week"] = week
    week_group = result.groupby("utc_week", sort=False)
    result["week_open"] = week_group["mid_open"].transform("first")
    result["week_bar_number"] = week_group.cumcount() + 1

    for lookback in (24, 48, 96, 192):
        result[f"balance_high_{lookback}"] = (
            result["mid_high"].shift(1).rolling(lookback, min_periods=lookback).max()
        )
        result[f"balance_low_{lookback}"] = (
            result["mid_low"].shift(1).rolling(lookback, min_periods=lookback).min()
        )
        result[f"balance_mid_{lookback}"] = (
            result[f"balance_high_{lookback}"]
            + result[f"balance_low_{lookback}"]
        ) / 2.0
    return result


def prepare_frame(
    m15: pd.DataFrame,
    h4: pd.DataFrame,
    config: Mapping[str, Any],
    adaptive_module: Any,
    regime_module: Any,
    base_module: Any,
) -> pd.DataFrame:
    return add_anchor_features(
        base_module.prepare_features(
            m15, h4, config, adaptive_module, regime_module
        )
    )


def _hour_mask(frame: pd.DataFrame, name: str) -> pd.Series:
    hour = frame["hour"]
    if name == "ALL_LIQUID":
        return hour.between(6, 19)
    if name == "LONDON":
        return hour.between(6, 11)
    if name == "LONDON_NY":
        return hour.between(6, 16)
    if name == "NEW_YORK":
        return hour.between(12, 19)
    raise KeyError(name)


def _false_break_direction(
    frame: pd.DataFrame,
    high: pd.Series,
    low: pd.Series,
    sweep_atr: float,
    reentry_atr: float,
    wick_min: float,
) -> pd.Series:
    atr = frame["atr14"]
    upper = (
        frame["mid_high"].gt(high + sweep_atr * atr)
        & frame["mid_close"].lt(high - reentry_atr * atr)
        & frame["upper_wick"].ge(wick_min)
    )
    lower = (
        frame["mid_low"].lt(low - sweep_atr * atr)
        & frame["mid_close"].gt(low + reentry_atr * atr)
        & frame["lower_wick"].ge(wick_min)
    )
    return pd.Series(
        np.select([upper, lower], [-1, 1], default=0),
        index=frame.index,
        dtype=int,
    )


def _rotation_confirmation(
    frame: pd.DataFrame,
    direction: pd.Series,
    mode: str,
    wick_min: float,
) -> pd.Series:
    candle = direction.mul(frame["candle_direction"]).gt(0)
    wick = pd.Series(
        np.where(
            direction.gt(0),
            frame["lower_wick"].ge(wick_min),
            frame["upper_wick"].ge(wick_min),
        ),
        index=frame.index,
    )
    if mode == "CANDLE":
        return candle
    if mode == "WICK":
        return wick
    if mode == "EITHER":
        return candle | wick
    raise KeyError(mode)


def signal_mask_direction_target(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series, pd.Series]:
    atr = frame["atr14"]
    close = frame["mid_close"]
    direction = pd.Series(0, index=frame.index, dtype=int)
    target = pd.Series(np.nan, index=frame.index, dtype=float)

    if mechanic == "CHOP_PREVIOUS_DAY_EXTREME_RECLAIM":
        direction = _false_break_direction(
            frame,
            frame["previous_day_high"],
            frame["previous_day_low"],
            float(params["sweep_atr"]),
            float(params["reentry_atr"]),
            float(params["wick_min"]),
        )
        target = frame[
            "previous_day_mid"
            if str(params["anchor"]) == "MID"
            else "previous_day_close"
        ].astype(float)
        structure = pd.Series(True, index=frame.index)
    elif mechanic == "CHOP_ASIA_EXTREME_RECLAIM":
        direction = _false_break_direction(
            frame,
            frame["asia_high"],
            frame["asia_low"],
            float(params["sweep_atr"]),
            float(params["reentry_atr"]),
            float(params["wick_min"]),
        )
        target = frame["asia_mid"].astype(float)
        structure = frame["asia_range_atr"].between(
            float(params["asia_range_atr_min"]),
            float(params["asia_range_atr_max"]),
            inclusive="both",
        )
    elif mechanic == "CHOP_DAY_VWAP_ROTATION":
        deviation = (close - frame["day_vwap"]) / atr
        direction = -np.sign(deviation).fillna(0).astype(int)
        target = frame["day_vwap"].astype(float)
        structure = (
            deviation.abs().ge(float(params["deviation_atr"]))
            & frame["day_bar_number"].ge(int(params["minimum_day_bars"]))
            & frame["day_displacement_atr"].abs().le(
                float(params["maximum_day_displacement_atr"])
            )
            & _rotation_confirmation(
                frame,
                direction,
                str(params["confirmation"]),
                float(params["wick_min"]),
            )
        )
    elif mechanic == "CHOP_WEEK_OPEN_ROTATION":
        deviation = (close - frame["week_open"]) / atr
        direction = -np.sign(deviation).fillna(0).astype(int)
        target = frame["week_open"].astype(float)
        structure = (
            deviation.abs().ge(float(params["deviation_atr"]))
            & frame["week_bar_number"].ge(int(params["minimum_week_bars"]))
            & _rotation_confirmation(
                frame,
                direction,
                str(params["confirmation"]),
                float(params["wick_min"]),
            )
        )
    elif mechanic == "CHOP_ROLLING_BALANCE_REENTRY":
        lookback = int(params["lookback"])
        high = frame[f"balance_high_{lookback}"]
        low = frame[f"balance_low_{lookback}"]
        direction = _false_break_direction(
            frame,
            high,
            low,
            float(params["sweep_atr"]),
            float(params["reentry_atr"]),
            float(params["wick_min"]),
        )
        target = frame[f"balance_mid_{lookback}"].astype(float)
        width = (high - low) / atr
        structure = width.between(
            float(params["width_atr_min"]),
            float(params["width_atr_max"]),
            inclusive="both",
        )
    else:
        raise KeyError(mechanic)

    valid = (
        frame["regime"].eq("CHOP")
        & direction.ne(0)
        & pd.Series(structure, index=frame.index).fillna(False)
        & _hour_mask(frame, str(params["hour_window"]))
        & np.isfinite(target)
        & np.isfinite(atr)
        & atr.gt(0.0)
    )
    return valid.astype(bool), direction.astype(int), target.astype(float)


def generate_manifest(frame: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    selection = config["selection"]
    seed = str(selection["hash_selection_seed"])
    per_mechanic = int(selection["attempts_per_mechanic"])
    windows = {
        name: (pd.Timestamp(start), pd.Timestamp(end))
        for name, (start, end) in config["windows"].items()
    }
    attempt = int(selection["attempt_first"])
    rows: list[dict[str, Any]] = []
    for mechanic in selection["mechanics"]:
        candidates: list[tuple[str, str, dict[str, Any]]] = []
        for params in parameter_space(str(mechanic), config):
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(
                f"{seed}|{mechanic}|{canonical}".encode("ascii")
            ).hexdigest()
            candidates.append((digest, canonical, params))
        accepted = 0
        for digest, canonical, params in sorted(candidates):
            mask, _, _ = signal_mask_direction_target(frame, str(mechanic), params)
            total = int(mask.sum())
            era_counts = {
                name: int(
                    (
                        mask
                        & frame["entry_time_key"].ge(start)
                        & frame["entry_time_key"].lt(end)
                    ).sum()
                )
                for name, (start, end) in windows.items()
            }
            if total < int(selection["minimum_raw_signals_total"]):
                continue
            if min(era_counts.values()) < int(
                selection["minimum_raw_signals_each_era"]
            ):
                continue
            rows.append(
                {
                    "attempt_no": attempt,
                    "variant_id": digest[:16],
                    "regime_owner": "CHOP",
                    "mechanic": str(mechanic),
                    "geometry_id": str(params["geometry_id"]),
                    "raw_signal_count": total,
                    "minimum_era_raw_signal_count": min(era_counts.values()),
                    "parameters_json": canonical,
                }
            )
            attempt += 1
            accepted += 1
            if accepted == per_mechanic:
                break
        if accepted != per_mechanic:
            raise ValueError(
                f"Only {accepted} signal-covered definitions for {mechanic}"
            )
    result = pd.DataFrame(rows)
    if len(result) != int(selection["total_attempts"]):
        raise ValueError("Manifest count differs from contract")
    if int(result["attempt_no"].iat[-1]) != int(selection["attempt_last"]):
        raise ValueError("Manifest attempt range differs from contract")
    if result["variant_id"].duplicated().any():
        raise ValueError("Duplicate variant IDs")
    return result


def simulate_anchor_outcome(
    frame: pd.DataFrame,
    signal_index: int,
    direction: int,
    target: float,
    geometry: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> dict[str, Any] | None:
    entry_index = signal_index + 1
    if entry_index >= len(frame):
        return None
    signal = frame.iloc[signal_index]
    entry_bar = frame.iloc[entry_index]
    signal_time = pd.Timestamp(signal["timestamp_utc"])
    entry_time = pd.Timestamp(entry_bar["bar_start_utc"])
    gap = (entry_time - signal_time).total_seconds() / 60.0
    if gap < 0.0 or gap > float(execution["maximum_entry_gap_minutes"]):
        return None
    atr = float(signal["atr14"])
    if not np.isfinite(atr) or atr <= 0.0 or not np.isfinite(target):
        return None
    entry = float(entry_bar["ask_open"] if direction > 0 else entry_bar["bid_open"])
    risk = float(geometry["stop_atr"]) * atr
    spread = float(entry_bar["ask_open"] - entry_bar["bid_open"])
    if risk <= 0.0 or spread < 0.0:
        return None
    if spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    target_r = direction * (float(target) - entry) / risk
    if target_r < float(geometry["minimum_target_r"]) or target_r > float(
        geometry["maximum_target_r"]
    ):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    stop = entry - direction * risk
    deadline = entry_time + pd.Timedelta(
        hours=float(geometry["maximum_hold_hours"])
    )
    exit_time = pd.Timestamp(entry_bar["timestamp_utc"])
    exit_price = float(
        entry_bar["bid_close"] if direction > 0 else entry_bar["ask_close"]
    )
    exit_reason = "END_OF_DATA"
    for position in range(entry_index, len(frame)):
        bar = frame.iloc[position]
        start = pd.Timestamp(bar["bar_start_utc"])
        executable_open = float(
            bar["bid_open"] if direction > 0 else bar["ask_open"]
        )
        if start >= deadline:
            exit_time = start
            exit_price = executable_open
            exit_reason = "FIXED_HORIZON"
            break
        if (direction > 0 and executable_open <= stop) or (
            direction < 0 and executable_open >= stop
        ):
            exit_time = start
            exit_price = executable_open
            exit_reason = "GAP_THROUGH_STOP"
            break
        if (direction > 0 and executable_open >= target) or (
            direction < 0 and executable_open <= target
        ):
            exit_time = start
            exit_price = float(target)
            exit_reason = "GAP_THROUGH_TARGET"
            break
        stop_hit = (
            float(bar["bid_low"]) <= stop
            if direction > 0
            else float(bar["ask_high"]) >= stop
        )
        target_hit = (
            float(bar["bid_high"]) >= target
            if direction > 0
            else float(bar["ask_low"]) <= target
        )
        if stop_hit:
            exit_time = pd.Timestamp(bar["timestamp_utc"])
            exit_price = stop
            exit_reason = "STOP"
            break
        if target_hit:
            exit_time = pd.Timestamp(bar["timestamp_utc"])
            exit_price = float(target)
            exit_reason = "ANCHOR_TARGET"
            break
        exit_time = pd.Timestamp(bar["timestamp_utc"])
        exit_price = float(
            bar["bid_close"] if direction > 0 else bar["ask_close"]
        )
    gross_r = direction * (exit_price - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "signal_time": signal_time,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "direction": "LONG" if direction > 0 else "SHORT",
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": float(target),
        "target_r": target_r,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread_r": spread / risk,
        "gross_r": gross_r,
        "stress_net_r": gross_r
        - cost_r
        - float(execution["stress_slippage_r"]),
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "exit_reason": exit_reason,
    }


def simulate_variant(
    frame: pd.DataFrame,
    manifest_row: Any,
    config: Mapping[str, Any],
    outcome_cache: dict[tuple[Any, ...], dict[str, Any] | None],
) -> pd.DataFrame:
    params = json.loads(str(manifest_row.parameters_json))
    mask, direction, targets = signal_mask_direction_target(
        frame, str(manifest_row.mechanic), params
    )
    if int(mask.sum()) != int(manifest_row.raw_signal_count):
        raise ValueError(f"Raw signal count changed for {manifest_row.attempt_no}")
    geometry = config["geometries"][str(manifest_row.geometry_id)]
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    rows: list[dict[str, Any]] = []
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        target = float(targets.iat[int(signal_index)])
        key = (int(signal_index), sign, target, str(manifest_row.geometry_id))
        if key not in outcome_cache:
            outcome_cache[key] = simulate_anchor_outcome(
                frame,
                int(signal_index),
                sign,
                target,
                geometry,
                config["execution"],
            )
        outcome = outcome_cache[key]
        if outcome is None:
            continue
        entry = pd.Timestamp(outcome["entry_time"])
        if entry < position_until:
            continue
        day = entry.date()
        maximum = int(config["execution"]["maximum_trades_per_variant_utc_day"])
        if daily_count.get(day, 0) >= maximum:
            continue
        row = dict(outcome)
        row["attempt_no"] = int(manifest_row.attempt_no)
        row["variant_id"] = str(manifest_row.variant_id)
        row["mechanic"] = str(manifest_row.mechanic)
        row["geometry_id"] = str(manifest_row.geometry_id)
        rows.append(row)
        position_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(rows)
