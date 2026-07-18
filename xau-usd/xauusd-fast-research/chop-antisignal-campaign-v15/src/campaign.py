from __future__ import annotations

import hashlib
from itertools import product
import json
from typing import Any, Mapping

import numpy as np
import pandas as pd


SOURCE_MECHANICS = {
    "CHOP_MATURE_EDGE_REENTRY_REVERSE": "CHOP_MATURE_EPISODE_EDGE_REENTRY",
    "CHOP_MATURE_EDGE_BOUNCE_REVERSE": "CHOP_MATURE_EPISODE_EDGE_BOUNCE",
    "CHOP_FRESH_ANCESTRY_CONTINUATION_REVERSE": (
        "CHOP_FRESH_ANCESTRY_CONTINUATION"
    ),
    "CHOP_FRESH_ANCESTRY_REVERSAL_REVERSE": "CHOP_FRESH_ANCESTRY_REVERSAL",
    "CHOP_MATURE_BREAKOUT_REVERSE": "CHOP_MATURE_EPISODE_BREAKOUT",
}


def _space(**values: list[Any]) -> list[dict[str, Any]]:
    keys = tuple(values)
    return [
        dict(zip(keys, combination, strict=True))
        for combination in product(*(values[key] for key in keys))
    ]


def _bounded_space(**values: list[Any]) -> list[dict[str, Any]]:
    return [
        params
        for params in _space(**values)
        if float(params["width_atr_min"]) < float(params["width_atr_max"])
    ]


def parameter_space(mechanic: str, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_mechanic = SOURCE_MECHANICS[mechanic]
    geometries = list(config["geometries"])
    hours = ["ALL_LIQUID", "LONDON", "LONDON_NY", "NEW_YORK"]
    if source_mechanic == "CHOP_MATURE_EPISODE_EDGE_REENTRY":
        return _bounded_space(
            age_min=[8, 16, 32, 64],
            sweep_atr=[0.0, 0.03, 0.07, 0.12],
            reentry_atr=[0.0, 0.03, 0.07],
            wick_min=[0.1, 0.25, 0.4],
            width_atr_min=[1.0, 2.0, 3.0],
            width_atr_max=[4.0, 6.0, 8.0],
            hour_window=hours,
            geometry_id=geometries,
        )
    if source_mechanic == "CHOP_MATURE_EPISODE_EDGE_BOUNCE":
        return _bounded_space(
            age_min=[8, 16, 32, 64],
            edge_fraction=[0.05, 0.1, 0.2, 0.3],
            confirmation=["CANDLE", "WICK", "EITHER"],
            wick_min=[0.1, 0.25, 0.4],
            width_atr_min=[1.0, 2.0, 3.0],
            width_atr_max=[4.0, 6.0, 8.0],
            hour_window=hours,
            geometry_id=geometries,
        )
    if source_mechanic == "CHOP_FRESH_ANCESTRY_CONTINUATION":
        return _space(
            age_max=[8, 16, 32, 64],
            ancestry_max_bars=[128, 256, 512, 1024, 2048],
            pullback_distance_atr=[0.1, 0.25, 0.5, 1.0],
            body_min=[0.1, 0.25, 0.4],
            efficiency_min=[0.1, 0.25, 0.4],
            require_slow_side=[False, True],
            hour_window=hours,
            geometry_id=geometries,
        )
    if source_mechanic == "CHOP_FRESH_ANCESTRY_REVERSAL":
        return _space(
            age_max=[8, 16, 32, 64],
            ancestry_max_bars=[128, 256, 512, 1024, 2048],
            momentum_bars=[2, 4, 8, 12],
            reversal_momentum_atr=[0.25, 0.5, 0.75, 1.0],
            body_min=[0.1, 0.25, 0.4],
            efficiency_min=[0.1, 0.25, 0.4],
            hour_window=hours,
            geometry_id=geometries,
        )
    if source_mechanic == "CHOP_MATURE_EPISODE_BREAKOUT":
        return _bounded_space(
            age_min=[8, 16, 32, 64],
            breakout_atr=[0.0, 0.03, 0.07, 0.12],
            body_min=[0.1, 0.25, 0.4],
            efficiency_min=[0.1, 0.25, 0.4],
            width_atr_min=[1.0, 2.0, 3.0],
            width_atr_max=[4.0, 6.0, 8.0],
            hour_window=hours,
            geometry_id=geometries,
        )
    raise KeyError(mechanic)


def add_episode_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(
        drop=True
    ).copy()
    regime = result["regime"].astype("object")
    chop = regime.eq("CHOP")
    run_id = regime.ne(regime.shift(1)).fillna(True).astype("int64").cumsum()

    result["hour"] = pd.to_datetime(result["bar_start_utc"], utc=True).dt.hour
    result["regime_run_id"] = run_id.astype(int)
    result["chop_age_m15"] = 0
    result.loc[chop, "chop_age_m15"] = (
        result.loc[chop].groupby(run_id.loc[chop], sort=False).cumcount() + 1
    )

    directional = regime.isin(["TREND_UP", "TREND_DOWN"])
    last_trend = regime.where(directional).ffill()
    trend_position = pd.Series(
        np.where(directional, np.arange(len(result)), np.nan), index=result.index
    ).ffill()
    result["chop_ancestor"] = last_trend.where(chop)
    result["bars_since_ancestor"] = (
        pd.Series(np.arange(len(result)), index=result.index) - trend_position
    ).where(chop)
    result["ancestry_direction"] = result["chop_ancestor"].map(
        {"TREND_UP": 1, "TREND_DOWN": -1}
    ).fillna(0).astype(int)

    running_high = result["mid_high"].where(chop).groupby(run_id).cummax()
    running_low = result["mid_low"].where(chop).groupby(run_id).cummin()
    result["episode_high_prior"] = running_high.groupby(run_id).shift(1)
    result["episode_low_prior"] = running_low.groupby(run_id).shift(1)
    result["episode_mid_prior"] = (
        result["episode_high_prior"] + result["episode_low_prior"]
    ) / 2.0
    result["episode_width_atr"] = (
        result["episode_high_prior"] - result["episode_low_prior"]
    ) / result["atr14"]
    return result


def prepare_frame(
    m15: pd.DataFrame,
    h4: pd.DataFrame,
    config: Mapping[str, Any],
    adaptive_module: Any,
    regime_module: Any,
    base_module: Any,
) -> pd.DataFrame:
    prepared = base_module.prepare_features(
        m15, h4, config, adaptive_module, regime_module
    )
    return add_episode_features(prepared)


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
    sweep_atr: float,
    reentry_atr: float,
    wick_min: float,
) -> pd.Series:
    atr = frame["atr14"]
    high = frame["episode_high_prior"]
    low = frame["episode_low_prior"]
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


def _edge_direction(frame: pd.DataFrame, edge_fraction: float) -> pd.Series:
    width = frame["episode_high_prior"] - frame["episode_low_prior"]
    near_low = frame["mid_low"].le(
        frame["episode_low_prior"] + edge_fraction * width
    )
    near_high = frame["mid_high"].ge(
        frame["episode_high_prior"] - edge_fraction * width
    )
    below_mid = frame["mid_close"].le(frame["episode_mid_prior"])
    long_edge = near_low & (~near_high | below_mid)
    short_edge = near_high & (~near_low | ~below_mid)
    return pd.Series(
        np.select([long_edge, short_edge], [1, -1], default=0),
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


def _episode_width_mask(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.Series:
    return frame["episode_width_atr"].between(
        float(params["width_atr_min"]),
        float(params["width_atr_max"]),
        inclusive="both",
    )


def signal_mask_direction(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series]:
    atr = frame["atr14"]
    close = frame["mid_close"]
    direction = pd.Series(0, index=frame.index, dtype=int)

    source_mechanic = SOURCE_MECHANICS[mechanic]
    if source_mechanic == "CHOP_MATURE_EPISODE_EDGE_REENTRY":
        direction = _false_break_direction(
            frame,
            float(params["sweep_atr"]),
            float(params["reentry_atr"]),
            float(params["wick_min"]),
        )
        structure = (
            frame["chop_age_m15"].ge(int(params["age_min"]))
            & _episode_width_mask(frame, params)
        )
    elif source_mechanic == "CHOP_MATURE_EPISODE_EDGE_BOUNCE":
        direction = _edge_direction(frame, float(params["edge_fraction"]))
        structure = (
            frame["chop_age_m15"].ge(int(params["age_min"]))
            & _episode_width_mask(frame, params)
            & _rotation_confirmation(
                frame,
                direction,
                str(params["confirmation"]),
                float(params["wick_min"]),
            )
        )
    elif source_mechanic == "CHOP_FRESH_ANCESTRY_CONTINUATION":
        direction = frame["ancestry_direction"].astype(int)
        slow_side = (
            direction.mul(close - frame["ema_slow"]).ge(0.0)
            if bool(params["require_slow_side"])
            else pd.Series(True, index=frame.index)
        )
        structure = (
            frame["chop_age_m15"].le(int(params["age_max"]))
            & frame["bars_since_ancestor"].le(int(params["ancestry_max_bars"]))
            & close.sub(frame["ema_fast"]).abs().div(atr).le(
                float(params["pullback_distance_atr"])
            )
            & direction.mul(frame["candle_direction"]).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
            & slow_side
        )
    elif source_mechanic == "CHOP_FRESH_ANCESTRY_REVERSAL":
        direction = -frame["ancestry_direction"].astype(int)
        momentum = frame[
            f"return_{int(params['momentum_bars'])}_local"
        ].div(atr)
        structure = (
            frame["chop_age_m15"].le(int(params["age_max"]))
            & frame["bars_since_ancestor"].le(int(params["ancestry_max_bars"]))
            & direction.mul(momentum).ge(float(params["reversal_momentum_atr"]))
            & direction.mul(frame["candle_direction"]).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif source_mechanic == "CHOP_MATURE_EPISODE_BREAKOUT":
        up = close.gt(
            frame["episode_high_prior"]
            + float(params["breakout_atr"]) * atr
        )
        down = close.lt(
            frame["episode_low_prior"]
            - float(params["breakout_atr"]) * atr
        )
        direction = pd.Series(
            np.select([up, down], [1, -1], default=0),
            index=frame.index,
            dtype=int,
        )
        structure = (
            frame["chop_age_m15"].ge(int(params["age_min"]))
            & _episode_width_mask(frame, params)
            & direction.mul(frame["candle_direction"]).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    else:
        raise KeyError(mechanic)

    valid = (
        frame["regime"].eq("CHOP")
        & direction.ne(0)
        & pd.Series(structure, index=frame.index).fillna(False)
        & _hour_mask(frame, str(params["hour_window"]))
        & np.isfinite(atr)
        & atr.gt(0.0)
    )
    return valid.astype(bool), (-direction).astype(int)


def generate_manifest(frame: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    selection = config["selection"]
    seed = str(selection["hash_selection_seed"])
    source_seed = str(selection["source_policy_order_seed"])
    per_mechanic = int(selection["attempts_per_mechanic"])
    windows = {
        name: (pd.Timestamp(start), pd.Timestamp(end))
        for name, (start, end) in config["windows"].items()
    }
    attempt = int(selection["attempt_first"])
    rows: list[dict[str, Any]] = []
    for mechanic in selection["mechanics"]:
        source_mechanic = SOURCE_MECHANICS[str(mechanic)]
        candidates: list[tuple[str, str, str, dict[str, Any]]] = []
        for params in parameter_space(str(mechanic), config):
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            source_digest = hashlib.sha256(
                f"{source_seed}|{source_mechanic}|{canonical}".encode("ascii")
            ).hexdigest()
            variant_digest = hashlib.sha256(
                f"{seed}|{mechanic}|{canonical}".encode("ascii")
            ).hexdigest()
            candidates.append((source_digest, variant_digest, canonical, params))
        accepted = 0
        for _, variant_digest, canonical, params in sorted(candidates):
            mask, _ = signal_mask_direction(frame, str(mechanic), params)
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
                    "variant_id": variant_digest[:16],
                    "paired_source_attempt_no": attempt - 1000,
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


def simulate_fixed_outcome(
    frame: pd.DataFrame,
    signal_index: int,
    direction: int,
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
    if not np.isfinite(atr) or atr <= 0.0:
        return None
    entry = float(entry_bar["ask_open"] if direction > 0 else entry_bar["bid_open"])
    risk = float(geometry["stop_atr"]) * atr
    spread = float(entry_bar["ask_open"] - entry_bar["bid_open"])
    if risk <= 0.0 or spread < 0.0:
        return None
    if spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    target_r = float(geometry["target_r"])
    stop = entry - direction * risk
    target = entry + direction * target_r * risk
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
            exit_price = target
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
            exit_price = target
            exit_reason = "LOCKED_TARGET"
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
        "target": target,
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
    mask, direction = signal_mask_direction(
        frame, str(manifest_row.mechanic), params
    )
    if int(mask.sum()) != int(manifest_row.raw_signal_count):
        raise ValueError(f"Raw signal count changed for {manifest_row.attempt_no}")
    geometry_id = str(manifest_row.geometry_id)
    geometry = config["geometries"][geometry_id]
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    rows: list[dict[str, Any]] = []
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        key = (int(signal_index), sign, geometry_id)
        if key not in outcome_cache:
            outcome_cache[key] = simulate_fixed_outcome(
                frame,
                int(signal_index),
                sign,
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
        row["geometry_id"] = geometry_id
        rows.append(row)
        position_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(rows)
