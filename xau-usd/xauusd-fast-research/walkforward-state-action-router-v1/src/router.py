from __future__ import annotations

import hashlib
import heapq
import itertools
import json
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ANCESTRY_CODES = {
    "TREND_UP": 0,
    "TREND_DOWN": 1,
    "COMPRESSION": 2,
    "CHOP": 3,
}


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _policy_space(
    owner: str, schema_id: str, config: Mapping[str, Any]
) -> Iterable[dict[str, Any]]:
    selection = config["selection"]
    walk_forward = config["walk_forward"]
    keys = (
        "geometry_id",
        "history_mode",
        "minimum_cell_rows",
        "prior_strength",
        "lcb_z",
        "minimum_lcb_r",
        "minimum_action_gap_r",
        "maximum_trades_per_utc_day",
    )
    values = (
        tuple(config["geometries"][owner]),
        tuple(walk_forward["history_modes"]),
        tuple(selection["minimum_cell_rows"]),
        tuple(selection["prior_strength"]),
        tuple(selection["lcb_z"]),
        tuple(selection["minimum_lcb_r"]),
        tuple(selection["minimum_action_gap_r"]),
        tuple(selection["maximum_trades_per_utc_day"]),
    )
    for combination in itertools.product(*values):
        row = dict(zip(keys, combination, strict=True))
        row["regime_owner"] = owner
        row["schema_id"] = schema_id
        yield row


def generate_manifest(config: Mapping[str, Any]) -> pd.DataFrame:
    selection = config["selection"]
    attempt = int(selection["attempt_first"])
    per_schema = int(selection["attempts_per_schema"])
    rows: list[dict[str, Any]] = []
    for owner, schemas in config["schemas"].items():
        owner_start = len(rows)
        for schema_id in schemas:
            candidates = heapq.nsmallest(
                per_schema,
                _policy_space(str(owner), str(schema_id), config),
                key=lambda item: _canonical_hash(item),
            )
            if len(candidates) != per_schema:
                raise ValueError(f"Insufficient policy space for {owner}/{schema_id}")
            for policy in candidates:
                variant_id = _canonical_hash(policy)[:16]
                rows.append(
                    {
                        "attempt_no": attempt,
                        "variant_id": variant_id,
                        **policy,
                    }
                )
                attempt += 1
        owner_count = len(rows) - owner_start
        if owner_count != int(selection["attempts_per_owner"]):
            raise ValueError(f"Owner attempt count mismatch for {owner}: {owner_count}")
    result = pd.DataFrame(rows)
    if len(result) != int(selection["total_attempts"]):
        raise ValueError("Total attempt count differs from contract")
    if result.empty or int(result["attempt_no"].iat[-1]) != int(
        selection["attempt_last"]
    ):
        raise ValueError("Attempt boundary differs from contract")
    if result["variant_id"].duplicated().any():
        raise ValueError("Duplicate policy variant IDs")
    return result


def decision_indices(
    frame: pd.DataFrame, owner: str, config: Mapping[str, Any]
) -> np.ndarray:
    if owner not in config["owners"]:
        raise KeyError(owner)
    signal_time = pd.to_datetime(frame["timestamp_utc"], utc=True)
    minute = int(config["decision"]["completed_bar_end_minute"])
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    atr = frame["atr14"].to_numpy(dtype=float)
    mask = (
        frame["regime"].eq(config["owners"][owner]).to_numpy(dtype=bool)
        & signal_time.dt.minute.eq(minute).to_numpy(dtype=bool)
        & signal_time.ge(start).to_numpy(dtype=bool)
        & signal_time.lt(end).to_numpy(dtype=bool)
        & np.isfinite(atr)
        & (atr > 0.0)
    )
    return np.flatnonzero(mask).astype(np.int64)


def _fixed_bin(values: np.ndarray, edges: Iterable[float]) -> tuple[np.ndarray, int]:
    boundaries = np.asarray(tuple(edges), dtype=float)
    result = np.searchsorted(boundaries, values, side="right").astype(np.int32)
    result[~np.isfinite(values)] = -1
    return result, len(boundaries) + 1


def _feature_categories(
    frame: pd.DataFrame,
    signal_indices: np.ndarray,
    directions: np.ndarray,
    config: Mapping[str, Any],
) -> dict[str, tuple[np.ndarray, int]]:
    if len(signal_indices) != len(directions):
        raise ValueError("Signal and direction arrays differ in length")

    def take(column: str) -> np.ndarray:
        return frame[column].to_numpy()[signal_indices]

    atr = take("atr14").astype(float)
    close = take("mid_close").astype(float)
    direction = directions.astype(float)
    signal_time = pd.to_datetime(frame["timestamp_utc"].iloc[signal_indices], utc=True)
    signal_hour = signal_time.dt.hour.to_numpy(dtype=np.int16)
    session = np.select(
        [signal_hour <= 5, signal_hour <= 11, signal_hour <= 17],
        [0, 1, 2],
        default=3,
    ).astype(np.int32)
    weekday = signal_time.dt.weekday.to_numpy(dtype=np.int32)

    prior_low = take("prior_low_24").astype(float)
    prior_high = take("prior_high_24").astype(float)
    width = prior_high - prior_low
    range_location = np.divide(
        close - prior_low,
        width,
        out=np.full(len(close), np.nan, dtype=float),
        where=np.isfinite(width) & (width > 0.0),
    )
    aligned_momentum = direction * np.divide(
        take("return_16_local").astype(float),
        atr,
        out=np.full(len(atr), np.nan, dtype=float),
        where=atr > 0.0,
    )
    aligned_vwap = direction * take("vwap_deviation_atr").astype(float)
    aligned_ema = direction * np.divide(
        close - take("ema_fast").astype(float),
        atr,
        out=np.full(len(atr), np.nan, dtype=float),
        where=atr > 0.0,
    )
    aligned_candle = (
        direction.astype(np.int32) * take("candle_direction").astype(np.int32)
    ) + 1
    invalid_candle = ~np.isin(aligned_candle, (0, 1, 2))
    aligned_candle[invalid_candle] = -1
    ancestry = (
        frame["last_resolved_regime"]
        .iloc[signal_indices]
        .map(ANCESTRY_CODES)
        .fillna(4)
        .to_numpy(dtype=np.int32)
    )

    raw = {
        "aligned_momentum": aligned_momentum,
        "aligned_vwap": aligned_vwap,
        "range_location": range_location,
        "h4_adx": take("adx_h4").astype(float),
        "h4_er": take("er_h4").astype(float),
        "atr_ratio": take("atr_ratio").astype(float),
        "spread_atr": take("spread_atr").astype(float),
        "quote_intensity": take("quote_intensity_ratio").astype(float),
        "body": take("body").astype(float),
        "transition_age": take("transition_age_m15").astype(float),
        "range_atr": take("range_atr").astype(float),
        "aligned_ema": aligned_ema,
    }
    categories: dict[str, tuple[np.ndarray, int]] = {
        "session": (session, 4),
        "weekday": (weekday, 5),
        "aligned_candle": (aligned_candle.astype(np.int32), 3),
        "ancestry": (ancestry, 5),
    }
    for name, values in raw.items():
        categories[name] = _fixed_bin(values, config["feature_bins"][name])
    return categories


def state_codes(
    frame: pd.DataFrame,
    signal_indices: np.ndarray,
    directions: np.ndarray,
    owner: str,
    schema_id: str,
    config: Mapping[str, Any],
) -> tuple[np.ndarray, int]:
    features = tuple(config["schemas"][owner][schema_id])
    categories = _feature_categories(frame, signal_indices, directions, config)
    code = np.zeros(len(signal_indices), dtype=np.int32)
    valid = np.ones(len(signal_indices), dtype=bool)
    multiplier = 1
    for name in features:
        values, cardinality = categories[str(name)]
        valid &= (values >= 0) & (values < cardinality)
        code += np.maximum(values, 0) * multiplier
        multiplier *= cardinality
    code[~valid] = -1
    return code, multiplier


def simulate_fixed_trade(
    arrays: Mapping[str, np.ndarray],
    signal_index: int,
    direction: int,
    geometry: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> dict[str, Any] | None:
    if direction not in (-1, 1):
        raise ValueError("Direction must be -1 or +1")
    entry_index = signal_index + 1
    starts = arrays["starts"]
    if entry_index >= len(starts):
        return None
    gap_minutes = (
        int(starts[entry_index]) - int(arrays["signals"][signal_index])
    ) / 60_000_000_000
    if gap_minutes < 0.0 or gap_minutes > float(execution["maximum_entry_gap_minutes"]):
        return None
    atr_value = float(arrays["atr14"][signal_index])
    risk = float(geometry["stop_atr"]) * atr_value
    if not np.isfinite(risk) or risk <= 0.0:
        return None
    entry = float(
        arrays["ask_open"][entry_index]
        if direction > 0
        else arrays["bid_open"][entry_index]
    )
    spread = float(arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index])
    if spread < 0.0 or spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    stop = entry - direction * risk
    target = entry + direction * float(geometry["target_r"]) * risk
    deadline = int(starts[entry_index]) + int(
        float(geometry["maximum_hold_hours"]) * 3_600_000_000_000
    )
    exit_index = -1
    exit_price = float("nan")
    exit_reason = "NO_EXIT"
    for position in range(entry_index, len(starts)):
        start = int(starts[position])
        executable_open = float(
            arrays["bid_open"][position]
            if direction > 0
            else arrays["ask_open"][position]
        )
        if start >= deadline:
            horizon_gap = (start - deadline) / 3_600_000_000_000
            if horizon_gap > float(execution["maximum_horizon_gap_hours"]):
                return None
            exit_index, exit_price, exit_reason = (
                position,
                executable_open,
                "FIXED_HORIZON",
            )
            break
        stop_at_open = (
            executable_open <= stop if direction > 0 else executable_open >= stop
        )
        target_at_open = (
            executable_open >= target if direction > 0 else executable_open <= target
        )
        if stop_at_open:
            exit_index, exit_price, exit_reason = (
                position,
                executable_open,
                "GAP_THROUGH_STOP",
            )
            break
        if target_at_open:
            exit_index, exit_price, exit_reason = position, target, "TARGET_AT_OPEN"
            break
        stop_hit = (
            float(arrays["bid_low"][position]) <= stop
            if direction > 0
            else float(arrays["ask_high"][position]) >= stop
        )
        target_hit = (
            float(arrays["bid_high"][position]) >= target
            if direction > 0
            else float(arrays["ask_low"][position]) <= target
        )
        if stop_hit:
            exit_index, exit_price = position, stop
            exit_reason = "STOP_AMBIGUOUS" if target_hit else "STOP"
            break
        if target_hit:
            exit_index, exit_price, exit_reason = position, target, "TARGET"
            break
    if exit_index < 0:
        return None
    entry_time = pd.Timestamp(int(starts[entry_index]), unit="ns", tz="UTC")
    at_open = exit_reason in ("FIXED_HORIZON", "GAP_THROUGH_STOP", "TARGET_AT_OPEN")
    exit_ns = int(starts[exit_index]) if at_open else int(arrays["ends"][exit_index])
    exit_time = pd.Timestamp(exit_ns, unit="ns", tz="UTC")
    gross_r = direction * (exit_price - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86_400.0)
    costs_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "signal_time": pd.Timestamp(
            int(arrays["signals"][signal_index]), unit="ns", tz="UTC"
        ),
        "entry_time": entry_time,
        "exit_time": exit_time,
        "direction": "LONG" if direction > 0 else "SHORT",
        "direction_sign": direction,
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread_r": spread / risk,
        "gross_r": gross_r,
        "stress_net_r": gross_r - costs_r - float(execution["stress_slippage_r"]),
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "exit_reason": exit_reason,
    }


def label_geometry(
    arrays: Mapping[str, np.ndarray],
    signal_indices: np.ndarray,
    owner: str,
    geometry_id: str,
    geometry: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for signal_index in signal_indices:
        pair = [
            simulate_fixed_trade(
                arrays, int(signal_index), direction, geometry, execution
            )
            for direction in (-1, 1)
        ]
        if any(outcome is None for outcome in pair):
            continue
        for outcome in pair:
            assert outcome is not None
            rows.append(
                {
                    "signal_index": int(signal_index),
                    "regime_owner": owner,
                    "geometry_id": geometry_id,
                    **outcome,
                }
            )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result = result.sort_values(
        ["signal_index", "direction_sign"], kind="mergesort"
    ).reset_index(drop=True)
    counts = result.groupby("signal_index", sort=False).size()
    if not counts.eq(2).all():
        raise ValueError("Geometry labels must contain complete LONG/SHORT pairs")
    return result


def _walkforward_blocks(
    config: Mapping[str, Any],
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    walk = config["walk_forward"]
    start = pd.Timestamp(walk["oos_start_utc"])
    final = pd.Timestamp(walk["oos_end_exclusive_utc"])
    months = int(walk["evaluation_block_months"])
    blocks: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    while start < final:
        end = min(start + pd.DateOffset(months=months), final)
        blocks.append((start, end))
        start = end
    return blocks


def walkforward_statistics(
    labels: pd.DataFrame,
    codes: np.ndarray,
    state_count: int,
    history_mode: str,
    config: Mapping[str, Any],
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    if len(labels) != len(codes):
        raise ValueError("Label and state-code arrays differ in length")
    if history_mode not in config["walk_forward"]["history_modes"]:
        raise KeyError(history_mode)
    size = len(labels)
    stats = {
        "oos": np.zeros(size, dtype=bool),
        "cell_n": np.zeros(size, dtype=np.int32),
        "cell_sum": np.zeros(size, dtype=float),
        "cell_sumsq": np.zeros(size, dtype=float),
        "global_n": np.zeros(size, dtype=np.int32),
        "global_sum": np.zeros(size, dtype=float),
        "global_sumsq": np.zeros(size, dtype=float),
    }
    signal_time = pd.to_datetime(labels["signal_time"], utc=True)
    exit_time = pd.to_datetime(labels["exit_time"], utc=True)
    values = labels["stress_net_r"].to_numpy(dtype=float)
    action = labels["direction_sign"].gt(0).to_numpy(dtype=np.int32)
    valid_code = codes >= 0
    source_start = pd.Timestamp(config["source"]["start_utc"])
    purge = pd.Timedelta(hours=float(config["walk_forward"]["purge_hours"]))
    diagnostics: list[dict[str, Any]] = []
    for block_number, (start, end) in enumerate(_walkforward_blocks(config), 1):
        if history_mode == "EXPANDING":
            history_start = source_start
        elif history_mode == "ROLLING_4Y":
            history_start = start - pd.DateOffset(years=4)
        elif history_mode == "ROLLING_8Y":
            history_start = start - pd.DateOffset(years=8)
        else:
            raise KeyError(history_mode)
        cutoff = start - purge
        train = (
            exit_time.lt(cutoff).to_numpy(dtype=bool)
            & signal_time.ge(history_start).to_numpy(dtype=bool)
            & valid_code
            & np.isfinite(values)
        )
        test = (
            signal_time.ge(start).to_numpy(dtype=bool)
            & signal_time.lt(end).to_numpy(dtype=bool)
            & valid_code
        )
        train_key = codes[train] * 2 + action[train]
        key_count = state_count * 2
        cell_n = np.bincount(train_key, minlength=key_count)
        cell_sum = np.bincount(train_key, weights=values[train], minlength=key_count)
        cell_sumsq = np.bincount(
            train_key, weights=np.square(values[train]), minlength=key_count
        )
        global_n = np.bincount(action[train], minlength=2)
        global_sum = np.bincount(action[train], weights=values[train], minlength=2)
        global_sumsq = np.bincount(
            action[train], weights=np.square(values[train]), minlength=2
        )
        positions = np.flatnonzero(test)
        if len(positions):
            keys = codes[positions] * 2 + action[positions]
            actions = action[positions]
            stats["oos"][positions] = True
            stats["cell_n"][positions] = cell_n[keys].astype(np.int32)
            stats["cell_sum"][positions] = cell_sum[keys]
            stats["cell_sumsq"][positions] = cell_sumsq[keys]
            stats["global_n"][positions] = global_n[actions].astype(np.int32)
            stats["global_sum"][positions] = global_sum[actions]
            stats["global_sumsq"][positions] = global_sumsq[actions]
        diagnostics.append(
            {
                "block_number": block_number,
                "block_start": start,
                "block_end": end,
                "history_start": history_start,
                "purge_cutoff": cutoff,
                "training_action_rows": int(train.sum()),
                "test_action_rows": int(test.sum()),
                "populated_state_actions": int(np.count_nonzero(cell_n)),
                "short_global_rows": int(global_n[0]),
                "long_global_rows": int(global_n[1]),
            }
        )
    return stats, diagnostics


def posterior_lcb(
    stats: Mapping[str, np.ndarray],
    minimum_cell_rows: int,
    prior_strength: float,
    lcb_z: float,
    minimum_global_rows: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = stats["cell_n"].astype(float)
    global_n = stats["global_n"].astype(float)
    global_mean = np.divide(
        stats["global_sum"],
        global_n,
        out=np.zeros_like(global_n, dtype=float),
        where=global_n > 0.0,
    )
    global_second = np.divide(
        stats["global_sumsq"],
        global_n,
        out=np.zeros_like(global_n, dtype=float),
        where=global_n > 0.0,
    )
    global_variance = np.maximum(global_second - np.square(global_mean), 0.0)
    posterior_n = n + float(prior_strength)
    posterior_mean = np.divide(
        stats["cell_sum"] + float(prior_strength) * global_mean,
        posterior_n,
        out=np.zeros_like(n, dtype=float),
        where=posterior_n > 0.0,
    )
    posterior_second = np.divide(
        stats["cell_sumsq"]
        + float(prior_strength) * (global_variance + np.square(global_mean)),
        posterior_n,
        out=np.zeros_like(n, dtype=float),
        where=posterior_n > 0.0,
    )
    posterior_variance = np.maximum(posterior_second - np.square(posterior_mean), 0.0)
    standard_error = np.sqrt(
        np.divide(
            posterior_variance,
            posterior_n,
            out=np.full_like(n, np.inf, dtype=float),
            where=posterior_n > 0.0,
        )
    )
    lcb = posterior_mean - float(lcb_z) * standard_error
    eligible = (
        stats["oos"].astype(bool)
        & (stats["cell_n"] >= int(minimum_cell_rows))
        & (stats["global_n"] >= int(minimum_global_rows))
        & np.isfinite(lcb)
    )
    lcb = np.where(eligible, lcb, -np.inf)
    return lcb, posterior_mean, standard_error


def select_trades(
    labels: pd.DataFrame,
    stats: Mapping[str, np.ndarray],
    policy: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if labels.empty:
        return labels.copy(), {
            "eligible_action_rows": 0,
            "direction_selected_rows": 0,
            "portfolio_selected_rows": 0,
            "overlap_rejections": 0,
            "daily_cap_rejections": 0,
        }
    counts = labels.groupby("signal_index", sort=False).size()
    if not counts.eq(2).all() or len(labels) % 2:
        raise ValueError("Selection requires complete action pairs")
    directions = labels["direction_sign"].to_numpy(dtype=int).reshape(-1, 2)
    if not np.all(directions[:, 0] == -1) or not np.all(directions[:, 1] == 1):
        raise ValueError("Action pairs must be ordered SHORT then LONG")
    lcb, posterior_mean, standard_error = posterior_lcb(
        stats,
        int(policy["minimum_cell_rows"]),
        float(policy["prior_strength"]),
        float(policy["lcb_z"]),
        int(config["walk_forward"]["minimum_global_action_rows"]),
    )
    score = lcb.reshape(-1, 2)
    score = np.where(score >= float(policy["minimum_lcb_r"]), score, -np.inf)
    best_column = np.argmax(score, axis=1)
    row_number = np.arange(len(best_column))
    best = score[row_number, best_column]
    second = score[row_number, 1 - best_column]
    action_gap = best - second
    minimum_gap = max(float(policy["minimum_action_gap_r"]), 1e-12)
    choose = np.isfinite(best) & (~np.isfinite(second) | (action_gap > minimum_gap))
    chosen_positions = 2 * row_number[choose] + best_column[choose]
    chosen = labels.iloc[chosen_positions].copy()
    chosen["state_cell_rows"] = stats["cell_n"][chosen_positions]
    chosen["posterior_mean_r"] = posterior_mean[chosen_positions]
    chosen["posterior_standard_error_r"] = standard_error[chosen_positions]
    chosen["posterior_lcb_r"] = lcb[chosen_positions]
    chosen["opposite_action_lcb_r"] = second[choose]
    chosen["action_gap_r"] = action_gap[choose]
    chosen = chosen.sort_values(["entry_time", "signal_index"], kind="mergesort")

    accepted: list[int] = []
    position_until = pd.Timestamp("1900-01-01T00:00:00Z")
    daily_count: dict[Any, int] = {}
    overlap_rejections = 0
    daily_cap_rejections = 0
    daily_cap = int(policy["maximum_trades_per_utc_day"])
    for index, row in chosen.iterrows():
        entry_time = pd.Timestamp(row["entry_time"])
        if entry_time < position_until:
            overlap_rejections += 1
            continue
        day = entry_time.date()
        if daily_count.get(day, 0) >= daily_cap:
            daily_cap_rejections += 1
            continue
        accepted.append(index)
        position_until = pd.Timestamp(row["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    selected = chosen.loc[accepted].reset_index(drop=True)
    finite_lcb = np.isfinite(lcb)
    diagnostics = {
        "eligible_action_rows": int(
            np.sum(finite_lcb & (lcb >= float(policy["minimum_lcb_r"])))
        ),
        "direction_selected_rows": int(len(chosen)),
        "portfolio_selected_rows": int(len(selected)),
        "overlap_rejections": overlap_rejections,
        "daily_cap_rejections": daily_cap_rejections,
        "median_selected_cell_rows": (
            float(selected["state_cell_rows"].median()) if not selected.empty else 0.0
        ),
        "mean_selected_lcb_r": (
            float(selected["posterior_lcb_r"].mean()) if not selected.empty else 0.0
        ),
    }
    return selected, diagnostics
