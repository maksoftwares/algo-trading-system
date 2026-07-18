from __future__ import annotations

import hashlib
from itertools import product
import json
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


SOURCE_MECHANICS = {
    "CHOP_FLOW_CONTINUATION": "FLOW_CONTINUATION",
    "CHOP_FLOW_EXHAUSTION": "FLOW_EXHAUSTION",
    "CHOP_BOOK_ABSORPTION": "BOOK_ABSORPTION",
    "CHOP_LIQUIDITY_SHOCK_REVERSION": "LIQUIDITY_SHOCK_REVERSION",
    "CHOP_POST_SHOCK_NORMALIZATION": "POST_SHOCK_NORMALIZATION",
}
SESSIONS = ("ALL", "ASIA", "LONDON", "NY", "LATE")


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def _with_episode_age(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        for minimum, maximum in product((1, 12, 48), (48, 144, 432, 2000)):
            if minimum <= maximum:
                result.append(
                    {**row, "chop_age_min": minimum, "chop_age_max": maximum}
                )
    return result


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    source = SOURCE_MECHANICS[mechanic]
    if source == "FLOW_CONTINUATION":
        rows = _space(
            imbalance_window=("5m", "15m"),
            imbalance_min=(0.015, 0.025, 0.035, 0.05, 0.07),
            book_min=(0.0, 0.03, 0.06, 0.10),
            intensity_min=(0.3, 0.5, 0.7, 1.0),
            efficiency_min=(0.0, 0.015, 0.035),
            spread_ratio_max=(1.15, 1.30, 1.50),
            require_body_alignment=(False, True),
            require_trend_alignment=(False, True),
            session=SESSIONS,
        )
    elif source == "FLOW_EXHAUSTION":
        rows = _space(
            impulse_bars=(1, 3, 6, 12),
            impulse_atr_min=(0.2, 0.35, 0.55, 0.8),
            impulse_tick_min=(0.005, 0.015, 0.03),
            reversal_book_min=(0.0, 0.03, 0.06),
            reversal_location_min=(0.35, 0.45, 0.55),
            intensity_min=(0.3, 0.5, 0.8, 1.1),
            session=SESSIONS,
        )
    elif source == "BOOK_ABSORPTION":
        rows = _space(
            price_window=(1, 3, 6),
            move_atr_min=(0.2, 0.4, 0.6, 0.9),
            reversal_book_min=(0.08, 0.16, 0.24, 0.32),
            price_tick_min=(0.0, 0.03, 0.06),
            efficiency_max=(0.3, 0.5, 0.7, 1.0),
            intensity_min=(0.6, 1.0, 1.4),
            session=SESSIONS,
        )
    elif source == "LIQUIDITY_SHOCK_REVERSION":
        rows = _space(
            impulse_bars=(1, 3),
            move_atr_min=(0.25, 0.4, 0.6, 0.9),
            spread_ratio_min=(1.0, 1.05, 1.15, 1.30),
            variance_ratio_min=(0.6, 0.9, 1.2, 1.6),
            intensity_min=(0.3, 0.5, 0.8, 1.1),
            reversal_location_min=(0.25, 0.40, 0.55),
            session=SESSIONS,
        )
    elif source == "POST_SHOCK_NORMALIZATION":
        rows = _space(
            prior_spread_ratio_min=(1.02, 1.08, 1.15, 1.30),
            current_spread_ratio_max=(1.0, 1.10, 1.25, 1.50),
            imbalance_min=(0.005, 0.015, 0.03, 0.05),
            book_min=(0.0, 0.03, 0.06),
            intensity_min=(0.3, 0.5, 0.8),
            require_body_alignment=(False, True),
            session=SESSIONS,
        )
    else:
        raise KeyError(mechanic)
    return _with_episode_age(rows)


def add_chop_episode_age(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(
        drop=True
    ).copy()
    regime = result["regime"].astype("object")
    chop = regime.eq("CHOP")
    run_id = regime.ne(regime.shift(1)).fillna(True).astype("int64").cumsum()
    result["regime_run_id"] = run_id.astype(int)
    result["chop_age_m5"] = 0
    result.loc[chop, "chop_age_m5"] = (
        result.loc[chop].groupby(run_id.loc[chop], sort=False).cumcount() + 1
    )
    return result


def prepare_frame(
    m5: pd.DataFrame,
    h4: pd.DataFrame,
    config: Mapping[str, Any],
    micro_module: Any,
    regime_module: Any,
) -> pd.DataFrame:
    frame = micro_module.prepare_features(m5, config)
    classified = regime_module.classify_h4(h4, config["regime"])
    attached = regime_module.attach_regime(frame, classified)
    return add_chop_episode_age(attached)


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
    atr = frame["atr14"].replace(0.0, np.nan)
    session = _session_mask(frame, str(params["session"]))
    if source == "FLOW_CONTINUATION":
        imbalance = frame[f"tick_imbalance_{params['imbalance_window']}"]
        direction = pd.Series(
            np.sign(imbalance.fillna(0.0)).astype(int), index=frame.index
        )
        mask = (
            imbalance.abs().ge(float(params["imbalance_min"]))
            & direction.mul(frame["tick_book_imbalance_mean"]).ge(
                float(params["book_min"])
            )
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
            & frame["price_efficiency_5m"].ge(float(params["efficiency_min"]))
            & frame["spread_ratio"].le(float(params["spread_ratio_max"]))
        )
        if bool(params["require_body_alignment"]):
            mask &= direction.mul(frame["body_move"]).gt(0.0)
        if bool(params["require_trend_alignment"]):
            mask &= direction.mul(frame["return_12"]).gt(0.0)
    elif source == "FLOW_EXHAUSTION":
        impulse = frame[f"return_{int(params['impulse_bars'])}"]
        impulse_direction = pd.Series(
            np.sign(impulse.fillna(0.0)).astype(int), index=frame.index
        )
        direction = -impulse_direction
        mask = (
            impulse.abs().div(atr).ge(float(params["impulse_atr_min"]))
            & impulse_direction.mul(frame["tick_imbalance_15m"]).ge(
                float(params["impulse_tick_min"])
            )
            & direction.mul(frame["tick_book_imbalance_mean"]).ge(
                float(params["reversal_book_min"])
            )
            & _signed_location(frame, direction).ge(
                float(params["reversal_location_min"])
            )
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
        )
    elif source == "BOOK_ABSORPTION":
        move = frame[f"return_{int(params['price_window'])}"]
        price_direction = pd.Series(
            np.sign(move.fillna(0.0)).astype(int), index=frame.index
        )
        direction = -price_direction
        mask = (
            move.abs().div(atr).ge(float(params["move_atr_min"]))
            & direction.mul(frame["tick_book_imbalance_mean"]).ge(
                float(params["reversal_book_min"])
            )
            & price_direction.mul(frame["tick_imbalance_15m"]).ge(
                float(params["price_tick_min"])
            )
            & frame["price_efficiency_5m"].le(float(params["efficiency_max"]))
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
        )
    elif source == "LIQUIDITY_SHOCK_REVERSION":
        impulse = frame[f"return_{int(params['impulse_bars'])}"]
        direction = -pd.Series(
            np.sign(impulse.fillna(0.0)).astype(int), index=frame.index
        )
        mask = (
            impulse.abs().div(atr).ge(float(params["move_atr_min"]))
            & frame["spread_ratio"].ge(float(params["spread_ratio_min"]))
            & frame["variance_ratio"].ge(float(params["variance_ratio_min"]))
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
            & _signed_location(frame, direction).ge(
                float(params["reversal_location_min"])
            )
        )
    elif source == "POST_SHOCK_NORMALIZATION":
        imbalance = frame["tick_imbalance_15m"]
        direction = pd.Series(
            np.sign(imbalance.fillna(0.0)).astype(int), index=frame.index
        )
        mask = (
            frame["prior_spread_ratio"].ge(
                float(params["prior_spread_ratio_min"])
            )
            & frame["spread_ratio"].le(float(params["current_spread_ratio_max"]))
            & imbalance.abs().ge(float(params["imbalance_min"]))
            & direction.mul(frame["tick_book_imbalance_mean"]).ge(
                float(params["book_min"])
            )
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
        )
        if bool(params["require_body_alignment"]):
            mask &= direction.mul(frame["body_move"]).gt(0.0)
    else:
        raise KeyError(mechanic)

    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & frame["regime"].eq("CHOP")
        & frame["chop_age_m5"].between(
            int(params["chop_age_min"]),
            int(params["chop_age_max"]),
            inclusive="both",
        )
        & session
        & direction.ne(0)
        & np.isfinite(frame["atr14"])
        & np.isfinite(frame["spread_ratio"])
    )
    return valid.astype(bool), direction.astype(int)


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
        for params in parameter_space(str(mechanic)):
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(
                f"{seed}|{mechanic}|{canonical}".encode("ascii")
            ).hexdigest()
            candidates.append((digest, canonical, params))
        accepted = 0
        for digest, canonical, params in sorted(candidates):
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
                    "variant_id": digest[:16],
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
        "atr": frame["atr14"].to_numpy(dtype=float),
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
    geometry = config["mechanics"][mechanic]
    execution = config["execution"]
    end_exclusive = pd.Timestamp(config["source"]["end_exclusive_utc"])
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown = pd.Timedelta(minutes=5 * int(execution["cooldown_bars"]))
    daily_count: dict[Any, int] = {}
    rows: list[dict[str, Any]] = []
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        key = (mechanic, int(signal_index), sign)
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
        rows.append(row)
        position_until = pd.Timestamp(outcome["exit_time"])
        cooldown_until = position_until + cooldown
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(rows)
