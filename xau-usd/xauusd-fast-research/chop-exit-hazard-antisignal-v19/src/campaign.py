from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


V18_MECHANICS = {
    "CHOP_ADX_ER_FAILED_BREAK_FADE": "CHOP_ADX_ER_EXIT_PRESSURE",
    "CHOP_SLOPE_INFLECTION_FADE": "CHOP_SLOPE_INFLECTION",
    "CHOP_RANGE_EDGE_FADE": "CHOP_RANGE_EDGE_PRESSURE",
    "CHOP_VOLATILITY_LIFT_FADE": "CHOP_VOLATILITY_LIFT",
    "CHOP_BOUNDARY_CONFLUENCE_FADE": "CHOP_BOUNDARY_CONFLUENCE",
}
SOURCE_MECHANICS = {
    "CHOP_ADX_ER_FAILED_BREAK_FADE": "ADX_ER_EXIT_PRESSURE",
    "CHOP_SLOPE_INFLECTION_FADE": "SLOPE_INFLECTION",
    "CHOP_RANGE_EDGE_FADE": "RANGE_EDGE_PRESSURE",
    "CHOP_VOLATILITY_LIFT_FADE": "VOLATILITY_LIFT",
    "CHOP_BOUNDARY_CONFLUENCE_FADE": "BOUNDARY_CONFLUENCE",
}
SESSIONS = ("ALL", "ASIA", "LONDON", "NY")
GEOMETRIES = ("FAST", "BALANCED", "TREND", "EXTENDED")


def _deterministic_design(
    mechanic: str,
    count: int,
    **values: Iterable[Any],
) -> list[dict[str, Any]]:
    options = {name: tuple(items) for name, items in values.items()}
    if any(not items for items in options.values()):
        raise ValueError("Every design dimension must contain at least one value")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    nonce = 0
    while len(result) < count:
        row: dict[str, Any] = {}
        for name, items in options.items():
            digest = hashlib.sha256(
                f"chop-exit-v18|{mechanic}|{nonce}|{name}".encode("ascii")
            ).digest()
            row[name] = items[int.from_bytes(digest[:8], "big") % len(items)]
        canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
        if canonical not in seen:
            seen.add(canonical)
            result.append(row)
        nonce += 1
        if nonce > count * 1000:
            raise ValueError(f"Could not construct {count} unique {mechanic} rows")
    return result


def parameter_space(mechanic: str, candidate_count: int = 400) -> list[dict[str, Any]]:
    source = SOURCE_MECHANICS[mechanic]
    source_mechanic = V18_MECHANICS[mechanic]
    if source == "ADX_ER_EXIT_PRESSURE":
        options = dict(
            adx_min=(10.0, 14.0, 18.0),
            adx_delta_min=(-2.0, -0.5, 0.0),
            er_min=(0.05, 0.12, 0.20),
            er_delta_min=(-0.10, -0.03, 0.0),
            slope_alignment_min=(-0.15, -0.05, 0.0),
            m5_window=(3, 12),
            m5_move_h1_atr_min=(-0.03, 0.0, 0.03),
            imbalance_min=(-0.03, 0.0, 0.01),
        )
    elif source == "SLOPE_INFLECTION":
        options = dict(
            slope_delta_abs_min=(0.0, 0.01, 0.03),
            current_slope_alignment_min=(-0.15, -0.05, 0.0),
            price_ema_alignment_min=(-0.30, -0.10, 0.0),
            adx_delta_min=(-2.0, -0.5, 0.0),
            m5_window=(3, 12),
            m5_move_h1_atr_min=(-0.03, 0.0, 0.03),
            imbalance_min=(-0.03, 0.0, 0.01),
        )
    elif source == "RANGE_EDGE_PRESSURE":
        options = dict(
            price_ema_abs_min=(0.0, 0.10, 0.25),
            displacement_min=(0.10, 0.35, 0.70),
            range_width_min=(1.0, 2.0, 3.5),
            range_width_delta_min=(-0.75, -0.25, 0.0),
            m5_window=(3, 12),
            m5_move_h1_atr_min=(-0.03, 0.0, 0.03),
            imbalance_min=(-0.03, 0.0, 0.01),
        )
    elif source == "VOLATILITY_LIFT":
        options = dict(
            atr_ratio_min=(0.45, 0.65, 0.85),
            atr_ratio_delta_min=(-0.10, -0.03, 0.0),
            adx_delta_min=(-2.0, -0.5, 0.0),
            variance_ratio_min=(0.3, 0.6, 1.0),
            m5_window=(3, 12),
            m5_move_h1_atr_min=(0.0, 0.02, 0.05),
            flow_alignment_min=(-0.03, 0.0, 0.01),
        )
    elif source == "BOUNDARY_CONFLUENCE":
        options = dict(
            state_profile=("LOOSE", "MID", "TIGHT"),
            minimum_state_factors=(1, 2, 3),
            minimum_direction_votes=(1, 2, 3),
            m5_window=(3, 12),
            m5_move_h1_atr_min=(-0.03, 0.0, 0.03),
            imbalance_min=(-0.03, 0.0, 0.01),
            intensity_min=(0.3, 0.5, 0.9),
        )
    else:
        raise KeyError(mechanic)
    return _deterministic_design(
        source_mechanic,
        candidate_count,
        **options,
        h4_state_age_m5_max=(3, 11, 23),
        chop_episode_age_h4_min=(1, 2, 4),
        session=SESSIONS,
        geometry_id=GEOMETRIES,
    )


def add_h4_state_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(
        drop=True
    ).copy()
    regime = result["regime"].astype("object")
    chop = regime.eq("CHOP")
    run_id = regime.ne(regime.shift(1)).fillna(True).astype("int64").cumsum()
    result["regime_run_id"] = run_id.astype(int)
    result["chop_episode_age_h4"] = 0
    result.loc[chop, "chop_episode_age_h4"] = (
        result.loc[chop].groupby(run_id.loc[chop], sort=False).cumcount() + 1
    )
    result["h4_price_ema_atr"] = (
        result["mid_close"] - result["ema_h4"]
    ) / result["atr_h4"].replace(0.0, np.nan)
    for column in (
        "adx_h4",
        "er_h4",
        "ema_slope_atr_h4",
        "range_width_atr_h4",
        "displacement_atr_h4",
        "atr_ratio_h4",
    ):
        result[f"{column}_delta"] = result[column].diff()
    return result


def prepare_frame(
    m5: pd.DataFrame,
    h1: pd.DataFrame,
    h4: pd.DataFrame,
    config: Mapping[str, Any],
    micro_module: Any,
    regime_module: Any,
) -> pd.DataFrame:
    frame = micro_module.prepare_features(m5, config)
    classified = add_h4_state_features(
        regime_module.classify_h4(h4, config["regime"])
    )
    h4_columns = [
        "timestamp_utc",
        "regime",
        "atr_h4",
        "adx_h4",
        "er_h4",
        "ema_slope_atr_h4",
        "range_width_atr_h4",
        "displacement_atr_h4",
        "atr_ratio_h4",
        "h4_price_ema_atr",
        "chop_episode_age_h4",
        "adx_h4_delta",
        "er_h4_delta",
        "ema_slope_atr_h4_delta",
        "range_width_atr_h4_delta",
        "displacement_atr_h4_delta",
        "atr_ratio_h4_delta",
    ]
    h4_state = classified[h4_columns].rename(
        columns={"timestamp_utc": "h4_state_time"}
    )
    attached = pd.merge_asof(
        frame.sort_values("timestamp_utc"),
        h4_state.sort_values("h4_state_time"),
        left_on="timestamp_utc",
        right_on="h4_state_time",
        direction="backward",
        allow_exact_matches=True,
    )
    h1_state = h1[["timestamp_utc"]].copy()
    h1_state["atr_h1"] = regime_module.atr(
        h1, int(config["features"]["h1_atr_period"])
    )
    attached = pd.merge_asof(
        attached.sort_values("timestamp_utc"),
        h1_state.sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
    ).sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    attached["h4_state_age_m5"] = (
        (attached["timestamp_utc"] - attached["h4_state_time"])
        .dt.total_seconds()
        .div(300.0)
        .round()
    )
    attached["risk_atr"] = attached["atr_h1"]
    return attached


def _session_mask(frame: pd.DataFrame, session: str) -> pd.Series:
    hour = frame["hour_utc_custom"]
    if session == "ALL":
        return pd.Series(True, index=frame.index)
    bounds = {
        "ASIA": (0, 6),
        "LONDON": (6, 12),
        "NY": (12, 18),
        "LATE": (18, 24),
    }
    if session not in bounds:
        raise KeyError(session)
    start, end = bounds[session]
    return hour.ge(start) & hour.lt(end)


def _signed_location(frame: pd.DataFrame, direction: pd.Series) -> pd.Series:
    return pd.Series(
        np.where(
            direction > 0,
            frame["close_location_custom"],
            1.0 - frame["close_location_custom"],
        ),
        index=frame.index,
    )


def signal_mask_direction(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series]:
    source = SOURCE_MECHANICS[mechanic]
    risk_atr = frame["risk_atr"].replace(0.0, np.nan)
    session = _session_mask(frame, str(params["session"]))
    m5_move = frame[f"return_{int(params['m5_window'])}"].div(risk_atr)
    imbalance = frame["tick_imbalance_15m"]
    if source == "ADX_ER_EXIT_PRESSURE":
        direction = pd.Series(
            np.sign(frame["h4_price_ema_atr"].fillna(0.0)).astype(int),
            index=frame.index,
        )
        mask = (
            frame["adx_h4"].ge(float(params["adx_min"]))
            & frame["adx_h4_delta"].ge(float(params["adx_delta_min"]))
            & frame["er_h4"].ge(float(params["er_min"]))
            & frame["er_h4_delta"].ge(float(params["er_delta_min"]))
            & direction.mul(frame["ema_slope_atr_h4"]).ge(
                float(params["slope_alignment_min"])
            )
            & direction.mul(m5_move).ge(float(params["m5_move_h1_atr_min"]))
            & direction.mul(imbalance).ge(float(params["imbalance_min"]))
        )
    elif source == "SLOPE_INFLECTION":
        direction = pd.Series(
            np.sign(frame["ema_slope_atr_h4_delta"].fillna(0.0)).astype(int),
            index=frame.index,
        )
        mask = (
            frame["ema_slope_atr_h4_delta"].abs().ge(
                float(params["slope_delta_abs_min"])
            )
            & direction.mul(frame["ema_slope_atr_h4"]).ge(
                float(params["current_slope_alignment_min"])
            )
            & direction.mul(frame["h4_price_ema_atr"]).ge(
                float(params["price_ema_alignment_min"])
            )
            & frame["adx_h4_delta"].ge(float(params["adx_delta_min"]))
            & direction.mul(m5_move).ge(float(params["m5_move_h1_atr_min"]))
            & direction.mul(imbalance).ge(float(params["imbalance_min"]))
        )
    elif source == "RANGE_EDGE_PRESSURE":
        direction = pd.Series(
            np.sign(frame["h4_price_ema_atr"].fillna(0.0)).astype(int),
            index=frame.index,
        )
        mask = (
            frame["h4_price_ema_atr"].abs().ge(
                float(params["price_ema_abs_min"])
            )
            & frame["displacement_atr_h4"].ge(
                float(params["displacement_min"])
            )
            & frame["range_width_atr_h4"].ge(float(params["range_width_min"]))
            & frame["range_width_atr_h4_delta"].ge(
                float(params["range_width_delta_min"])
            )
            & direction.mul(m5_move).ge(float(params["m5_move_h1_atr_min"]))
            & direction.mul(imbalance).ge(float(params["imbalance_min"]))
        )
    elif source == "VOLATILITY_LIFT":
        direction = pd.Series(
            np.sign(m5_move.fillna(0.0)).astype(int), index=frame.index
        )
        mask = (
            frame["atr_ratio_h4"].ge(float(params["atr_ratio_min"]))
            & frame["atr_ratio_h4_delta"].ge(
                float(params["atr_ratio_delta_min"])
            )
            & frame["adx_h4_delta"].ge(float(params["adx_delta_min"]))
            & frame["variance_ratio"].ge(float(params["variance_ratio_min"]))
            & m5_move.abs().ge(float(params["m5_move_h1_atr_min"]))
            & direction.mul(imbalance).ge(float(params["flow_alignment_min"]))
        )
    elif source == "BOUNDARY_CONFLUENCE":
        thresholds = {
            "LOOSE": (15.0, 0.12, 0.02, 0.0, 0.50),
            "MID": (18.0, 0.20, 0.06, 0.02, 0.85),
            "TIGHT": (21.0, 0.28, 0.10, 0.05, 1.15),
        }[str(params["state_profile"])]
        adx_min, er_min, slope_min, atr_delta_min, displacement_min = thresholds
        votes = (
            np.sign(frame["h4_price_ema_atr"].fillna(0.0)).astype(int)
            + np.sign(frame["ema_slope_atr_h4"].fillna(0.0)).astype(int)
            + np.sign(m5_move.fillna(0.0)).astype(int)
        )
        direction = pd.Series(
            np.sign(votes).astype(int), index=frame.index
        )
        factor_count = (
            frame["adx_h4"].ge(adx_min).astype(int)
            + frame["er_h4"].ge(er_min).astype(int)
            + frame["ema_slope_atr_h4"].abs().ge(slope_min).astype(int)
            + frame["atr_ratio_h4_delta"].ge(atr_delta_min).astype(int)
            + frame["displacement_atr_h4"].ge(displacement_min).astype(int)
        )
        mask = (
            factor_count.ge(int(params["minimum_state_factors"]))
            & votes.abs().ge(int(params["minimum_direction_votes"]))
            & direction.mul(m5_move).ge(float(params["m5_move_h1_atr_min"]))
            & direction.mul(imbalance).ge(float(params["imbalance_min"]))
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
        )
    else:
        raise KeyError(mechanic)

    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & frame["regime"].eq("CHOP")
        & frame["h4_state_age_m5"].between(
            0, int(params["h4_state_age_m5_max"]), inclusive="both"
        )
        & frame["chop_episode_age_h4"].ge(
            int(params["chop_episode_age_h4_min"])
        )
        & session
        & direction.ne(0)
        & np.isfinite(frame["risk_atr"])
        & np.isfinite(frame["spread_ratio"])
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
    coverage_cache: dict[str, tuple[int, dict[str, int]]] = {}
    for mechanic in selection["mechanics"]:
        source_mechanic = V18_MECHANICS[str(mechanic)]
        candidates: list[tuple[str, str, str, dict[str, Any]]] = []
        for params in parameter_space(
            str(mechanic),
            int(selection["candidate_definitions_per_mechanic"]),
        ):
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            source_digest = hashlib.sha256(
                f"{source_seed}|{source_mechanic}|{canonical}".encode("ascii")
            ).hexdigest()
            variant_digest = hashlib.sha256(
                f"{seed}|{mechanic}|{canonical}".encode("ascii")
            ).hexdigest()
            candidates.append(
                (source_digest, variant_digest, canonical, params)
            )
        accepted = 0
        for _, variant_digest, canonical, params in sorted(candidates):
            signal_params = {
                key: value for key, value in params.items() if key != "geometry_id"
            }
            signal_key = f"{mechanic}|" + json.dumps(
                signal_params, sort_keys=True, separators=(",", ":")
            )
            if signal_key not in coverage_cache:
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
                coverage_cache[signal_key] = (total, era_counts)
            total, era_counts = coverage_cache[signal_key]
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


def execution_arrays(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "starts": frame["bar_start_utc"].dt.tz_localize(None).to_numpy(),
        "ends": frame["bar_end_utc"].dt.tz_localize(None).to_numpy(),
        "atr": frame["risk_atr"].to_numpy(dtype=float),
        **{
            column: frame[column].to_numpy(dtype=float)
            for column in (
                "bid_open",
                "bid_high",
                "bid_low",
                "bid_close",
                "ask_open",
                "ask_high",
                "ask_low",
                "ask_close",
            )
        },
    }


def simulate_trade(
    arrays: Mapping[str, Any],
    signal_index: int,
    direction: int,
    geometry: Mapping[str, Any],
    execution: Mapping[str, Any],
    end_exclusive: pd.Timestamp,
) -> dict[str, Any] | None:
    entry_index = signal_index + 1
    hold_bars = int(geometry["hold_bars"])
    final_index = entry_index + hold_bars
    if entry_index >= len(arrays["starts"]) or final_index >= len(arrays["starts"]):
        return None
    if arrays["starts"][entry_index] != arrays["ends"][signal_index]:
        return None
    expected = arrays["starts"][entry_index] + np.arange(
        hold_bars + 1
    ) * np.timedelta64(5, "m")
    if not np.array_equal(arrays["starts"][entry_index : final_index + 1], expected):
        return None
    if pd.Timestamp(arrays["starts"][final_index], tz="UTC") >= end_exclusive:
        return None
    atr = float(arrays["atr"][signal_index])
    if not np.isfinite(atr) or atr <= 0.0:
        return None
    entry = float(
        arrays["ask_open"][entry_index]
        if direction > 0
        else arrays["bid_open"][entry_index]
    )
    risk = float(geometry["stop_atr"]) * atr
    spread = float(arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index])
    if not np.isfinite(risk) or risk <= 0.0 or spread < 0.0:
        return None
    if spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    stop = entry - direction * risk
    target = entry + direction * float(geometry["target_r"]) * risk
    exit_time = arrays["starts"][final_index]
    exit_price = float(
        arrays["bid_open"][final_index]
        if direction > 0
        else arrays["ask_open"][final_index]
    )
    exit_reason = "MAX_HOLD"
    ambiguous = False
    for position in range(entry_index, final_index):
        if direction > 0:
            executable_open = float(arrays["bid_open"][position])
            gap_stop = executable_open < stop
            gap_target = executable_open >= target
            stop_hit = float(arrays["bid_low"][position]) <= stop
            target_hit = float(arrays["bid_high"][position]) >= target
        else:
            executable_open = float(arrays["ask_open"][position])
            gap_stop = executable_open > stop
            gap_target = executable_open <= target
            stop_hit = float(arrays["ask_high"][position]) >= stop
            target_hit = float(arrays["ask_low"][position]) <= target
        if gap_stop:
            exit_time, exit_price, exit_reason = (
                arrays["starts"][position],
                executable_open,
                "GAP_THROUGH_STOP",
            )
            break
        if gap_target:
            exit_time, exit_price, exit_reason = (
                arrays["starts"][position],
                target,
                "TARGET_GAP_FROZEN_TARGET",
            )
            break
        if stop_hit:
            exit_time, exit_price = arrays["ends"][position], stop
            ambiguous = bool(target_hit)
            exit_reason = "AMBIGUOUS_M5_STOP_FIRST" if ambiguous else "STOP"
            break
        if target_hit:
            exit_time, exit_price, exit_reason = (
                arrays["ends"][position],
                target,
                "TARGET",
            )
            break
    entry_time = pd.Timestamp(arrays["starts"][entry_index], tz="UTC")
    exit_timestamp = pd.Timestamp(exit_time, tz="UTC")
    gross_r = direction * (exit_price - entry) / risk
    holding_days = max(0.0, (exit_timestamp - entry_time).total_seconds() / 86400.0)
    cost_r = (
        float(execution["extra_execution_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "signal_time": pd.Timestamp(arrays["ends"][signal_index], tz="UTC"),
        "entry_time": entry_time,
        "exit_time": exit_timestamp,
        "direction": "LONG" if direction > 0 else "SHORT",
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "stop_atr": float(geometry["stop_atr"]),
        "target_r": float(geometry["target_r"]),
        "entry_spread_r": spread / risk,
        "gross_r": gross_r,
        "stress_net_r": gross_r
        - cost_r
        - float(execution["stress_slippage_r"]),
        "holding_minutes": (exit_timestamp - entry_time).total_seconds() / 60.0,
        "exit_reason": exit_reason,
        "ambiguous_m5": ambiguous,
    }


def simulate_variant(
    frame: pd.DataFrame,
    arrays: Mapping[str, Any],
    manifest_row: Any,
    config: Mapping[str, Any],
    outcome_cache: dict[tuple[Any, ...], dict[str, Any] | None],
) -> pd.DataFrame:
    params = json.loads(str(manifest_row.parameters_json))
    mechanic = str(manifest_row.mechanic)
    mask, direction = signal_mask_direction(frame, mechanic, params)
    if int(mask.sum()) != int(manifest_row.raw_signal_count):
        raise ValueError(f"Raw signal count changed for {manifest_row.attempt_no}")
    geometry_id = str(params["geometry_id"])
    geometry = config["geometries"][geometry_id]
    execution = config["execution"]
    end_exclusive = pd.Timestamp(config["source"]["end_exclusive_utc"])
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown = pd.Timedelta(minutes=5 * int(execution["cooldown_bars"]))
    daily_count: dict[Any, int] = {}
    rows: list[dict[str, Any]] = []
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        key = (mechanic, geometry_id, int(signal_index), sign)
        if key not in outcome_cache:
            outcome_cache[key] = simulate_trade(
                arrays,
                int(signal_index),
                sign,
                geometry,
                execution,
                end_exclusive,
            )
        outcome = outcome_cache[key]
        if outcome is None:
            continue
        entry = pd.Timestamp(outcome["entry_time"])
        if entry < position_until or entry < cooldown_until:
            continue
        day = entry.date()
        maximum = int(execution["maximum_trades_per_policy_utc_day"])
        if daily_count.get(day, 0) >= maximum:
            continue
        row = dict(outcome)
        row["attempt_no"] = int(manifest_row.attempt_no)
        row["variant_id"] = str(manifest_row.variant_id)
        row["mechanic"] = mechanic
        row["geometry_id"] = geometry_id
        rows.append(row)
        position_until = pd.Timestamp(outcome["exit_time"])
        cooldown_until = position_until + cooldown
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(rows)
