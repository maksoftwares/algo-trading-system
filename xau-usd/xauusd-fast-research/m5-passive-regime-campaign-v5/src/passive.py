from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


MECHANICS: dict[str, tuple[str, ...]] = {
    "CHOP": (
        "CHOP_VWAP_PASSIVE_FADE",
        "CHOP_ROLLING_EDGE_PASSIVE_FADE",
        "CHOP_ASIAN_EDGE_PASSIVE_FADE",
        "CHOP_PRIOR_DAY_VALUE_PASSIVE_FADE",
        "CHOP_MOMENTUM_EXHAUSTION_LIMIT",
    ),
    "TRANSITION": (
        "TRANS_ANCESTRY_EMA_PULLBACK_LIMIT",
        "TRANS_POST_COMPRESSION_RETEST_LIMIT",
        "TRANS_POST_CHOP_RETEST_LIMIT",
        "TRANS_MOMENTUM_PULLBACK_LIMIT",
        "TRANS_EXHAUSTION_PASSIVE_FADE",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(root: Path) -> dict[str, Any]:
    overlay = json.loads(
        (root / "config" / "m5_passive_regime_campaign_v5.json").read_text(
            encoding="utf-8"
        )
    )
    base_path = (root / str(overlay["base"]["config_path"])).resolve()
    if sha256_file(base_path) != str(overlay["base"]["config_sha256"]):
        raise ValueError("Base config hash mismatch")
    config = json.loads(base_path.read_text(encoding="utf-8"))
    for key in (
        "schema_version",
        "selection",
        "passive_execution",
        "outputs",
        "research_controls",
    ):
        config[key] = overlay[key]
    config["base"] = overlay["base"]
    return config


def parameter_axes(mechanic: str) -> dict[str, list[Any]]:
    stops = [0.75, 1.0, 1.25, 1.5, 2.0]
    targets = [1.0, 1.25, 1.5, 2.0, 2.5]
    expiries = [0.5, 1.0, 2.0, 4.0, 6.0]
    holds = [2, 4, 6, 8, 12]
    offsets = [0.0, 0.10, 0.20, 0.35, 0.50]
    windows = ["ALL", "POST_ASIA", "LONDON", "LONDON_NY", "NEW_YORK"]
    common = {
        "entry_offset_atr": offsets,
        "stop_atr": stops,
        "target_r": targets,
        "pending_expiry_hours": expiries,
        "hold_hours": holds,
        "hour_window": windows,
    }
    if mechanic == "CHOP_VWAP_PASSIVE_FADE":
        return {
            "deviation_atr": [0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0],
            "target_mode": ["ANCHOR", "FIXED"],
            **common,
        }
    if mechanic == "CHOP_ROLLING_EDGE_PASSIVE_FADE":
        return {
            "lookback": [16, 24, 32, 48, 72, 96],
            "deviation_atr": [0.4, 0.6, 0.8, 1.0, 1.25, 1.5],
            "limit_mode": ["EXTREME", "OFFSET"],
            "target_mode": ["ANCHOR", "FIXED"],
            **common,
        }
    if mechanic == "CHOP_ASIAN_EDGE_PASSIVE_FADE":
        return {
            "edge_fraction": [0.0, 0.05, 0.10, 0.15, 0.20],
            "range_atr_min": [1.0, 1.5, 2.0, 2.5],
            "range_atr_max": [4.0, 6.0, 8.0, 12.0],
            "target_mode": ["ANCHOR", "FIXED"],
            **common,
        }
    if mechanic == "CHOP_PRIOR_DAY_VALUE_PASSIVE_FADE":
        return {
            "edge_buffer_atr": [0.0, 0.10, 0.20, 0.35, 0.50],
            "target_mode": ["ANCHOR", "FIXED"],
            **common,
        }
    if mechanic == "CHOP_MOMENTUM_EXHAUSTION_LIMIT":
        return {
            "momentum_bars": [4, 8, 16, 24, 32],
            "momentum_atr": [0.4, 0.6, 0.8, 1.0, 1.25, 1.5],
            "target_mode": ["ANCHOR", "FIXED"],
            **common,
        }
    if mechanic == "TRANS_ANCESTRY_EMA_PULLBACK_LIMIT":
        return {
            "transition_age_max": [8, 16, 32, 48, 96],
            "ema_source": ["FAST", "SLOW"],
            "minimum_extension_atr": [0.0, 0.2, 0.4, 0.6, 0.8],
            **common,
        }
    if mechanic in (
        "TRANS_POST_COMPRESSION_RETEST_LIMIT",
        "TRANS_POST_CHOP_RETEST_LIMIT",
    ):
        return {
            "transition_age_max": [8, 16, 32, 48, 96],
            "lookback": [8, 12, 16, 24, 32, 48],
            "breakout_atr": [0.0, 0.05, 0.10, 0.20, 0.30],
            **common,
        }
    if mechanic == "TRANS_MOMENTUM_PULLBACK_LIMIT":
        return {
            "transition_age_max": [8, 16, 32, 48, 96],
            "momentum_bars": [4, 8, 16, 24, 32],
            "momentum_atr": [0.4, 0.6, 0.8, 1.0, 1.25, 1.5],
            **common,
        }
    if mechanic == "TRANS_EXHAUSTION_PASSIVE_FADE":
        return {
            "transition_age_max": [8, 16, 32, 48, 96],
            "momentum_bars": [4, 8, 16, 24, 32],
            "momentum_atr": [0.6, 0.8, 1.0, 1.25, 1.5, 2.0],
            "source": ["ANY", "CHOP", "COMPRESSION", "ANY_TREND"],
            "target_mode": ["ANCHOR", "FIXED"],
            **common,
        }
    raise KeyError(mechanic)


def _sample_parameters(owner: str, mechanic: str, count: int) -> list[dict[str, Any]]:
    axes = parameter_axes(mechanic)
    seed_bytes = hashlib.sha256(f"{owner}|{mechanic}|V5".encode("ascii")).digest()[:8]
    random = np.random.default_rng(int.from_bytes(seed_bytes, "little"))
    sampled: dict[str, dict[str, Any]] = {}
    maximum_draws = count * 100
    for _ in range(maximum_draws):
        params = {
            key: values[int(random.integers(0, len(values)))]
            for key, values in axes.items()
        }
        canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
        sampled.setdefault(canonical, params)
        if len(sampled) == count:
            break
    if len(sampled) != count:
        raise ValueError(f"Could not sample {count} unique variants for {mechanic}")
    return [
        sampled[key]
        for key in sorted(
            sampled,
            key=lambda value: hashlib.sha256(
                f"{owner}|{mechanic}|{value}".encode("ascii")
            ).hexdigest(),
        )
    ]


def generate_manifest(selection: Mapping[str, Any]) -> pd.DataFrame:
    per_mechanic = int(selection["variants_per_mechanic"])
    attempt = int(selection["attempt_first"])
    rows: list[dict[str, Any]] = []
    for owner, mechanics in MECHANICS.items():
        for mechanic in mechanics:
            candidates = _sample_parameters(owner, mechanic, per_mechanic)
            if len(candidates) != per_mechanic:
                raise ValueError(f"Insufficient parameter coverage for {mechanic}")
            for params in candidates:
                canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
                variant_id = hashlib.sha256(
                    f"{owner}|{mechanic}|{canonical}".encode("ascii")
                ).hexdigest()[:16]
                rows.append(
                    {
                        "attempt_no": attempt,
                        "variant_id": variant_id,
                        "regime_owner": owner,
                        "mechanic": mechanic,
                        "parameters_json": canonical,
                    }
                )
                attempt += 1
    result = pd.DataFrame(rows)
    expected = list(
        range(int(selection["attempt_first"]), int(selection["attempt_last"]) + 1)
    )
    if len(result) != int(selection["total_attempts"]):
        raise ValueError("Attempt count does not match contract")
    if result["attempt_no"].tolist() != expected:
        raise ValueError("Attempt boundary does not match contract")
    if result["variant_id"].duplicated().any():
        raise ValueError("Duplicate variant IDs")
    return result


def prepare_passive_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    close = result["mid_close"]
    for lookback in (16, 24, 32, 48, 72, 96):
        result[f"prior_std_{lookback}"] = close.shift(1).rolling(
            lookback, min_periods=lookback
        ).std(ddof=0)
    return result


def _hour_mask(frame: pd.DataFrame, name: str) -> pd.Series:
    hour = frame["hour"]
    if name == "ALL":
        return pd.Series(True, index=frame.index)
    if name == "POST_ASIA":
        return hour.between(6, 18)
    if name == "LONDON":
        return hour.between(6, 11)
    if name == "LONDON_NY":
        return hour.between(6, 17)
    if name == "NEW_YORK":
        return hour.between(12, 18)
    raise KeyError(name)


def _source_mask(frame: pd.DataFrame, source: str) -> pd.Series:
    ancestor = frame["last_resolved_regime"]
    if source == "ANY":
        return pd.Series(True, index=frame.index)
    if source == "ANY_TREND":
        return ancestor.isin(("TREND_UP", "TREND_DOWN"))
    return ancestor.eq(source)


def _fixed_target(
    limit: pd.Series,
    direction: pd.Series,
    atr: pd.Series,
    params: Mapping[str, Any],
) -> pd.Series:
    return (
        limit
        + direction
        * float(params["target_r"])
        * float(params["stop_atr"])
        * atr
    )


def signal_orders(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
    passive_execution: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    close = frame["mid_close"]
    atr = frame["atr14"]
    regime = frame["regime"]
    direction = pd.Series(0, index=frame.index, dtype=int)
    limit = pd.Series(np.nan, index=frame.index, dtype=float)
    anchor = pd.Series(np.nan, index=frame.index, dtype=float)
    target_mode = str(params.get("target_mode", "FIXED"))
    offset = float(params["entry_offset_atr"]) * atr

    if mechanic == "CHOP_VWAP_PASSIVE_FADE":
        move = frame["vwap_deviation_atr"]
        direction = -np.sign(move).fillna(0).astype(int)
        limit = close - direction * offset
        anchor = frame["anchored_vwap"]
        mask = regime.eq("CHOP") & move.abs().ge(float(params["deviation_atr"]))
    elif mechanic == "CHOP_ROLLING_EDGE_PASSIVE_FADE":
        lookback = int(params["lookback"])
        mean = frame[f"prior_mean_{lookback}"]
        move = (close - mean) / atr
        direction = -np.sign(move).fillna(0).astype(int)
        if str(params["limit_mode"]) == "EXTREME":
            boundary = pd.Series(
                np.where(
                    direction.gt(0),
                    frame[f"prior_low_{lookback}"],
                    frame[f"prior_high_{lookback}"],
                ),
                index=frame.index,
            )
            limit = boundary - direction * offset
        else:
            limit = close - direction * offset
        anchor = mean
        mask = regime.eq("CHOP") & move.abs().ge(float(params["deviation_atr"]))
    elif mechanic == "CHOP_ASIAN_EDGE_PASSIVE_FADE":
        width = (frame["asian_high"] - frame["asian_low"]).replace(0.0, np.nan)
        location = (close - frame["asian_low"]) / width
        edge = float(params["edge_fraction"])
        direction = pd.Series(
            np.select([location.le(edge), location.ge(1.0 - edge)], [1, -1], default=0),
            index=frame.index,
            dtype=int,
        )
        boundary = pd.Series(
            np.where(direction.gt(0), frame["asian_low"], frame["asian_high"]),
            index=frame.index,
        )
        limit = boundary - direction * offset
        anchor = frame["asian_mid"]
        mask = (
            regime.eq("CHOP")
            & frame["hour"].ge(6)
            & frame["asian_range_atr"].between(
                float(params["range_atr_min"]),
                float(params["range_atr_max"]),
                inclusive="both",
            )
            & direction.ne(0)
        )
    elif mechanic == "CHOP_PRIOR_DAY_VALUE_PASSIVE_FADE":
        upper = close.ge(
            frame["prior_day_high"]
            - float(params["edge_buffer_atr"]) * atr
        )
        lower = close.le(
            frame["prior_day_low"]
            + float(params["edge_buffer_atr"]) * atr
        )
        direction = pd.Series(
            np.select(
                [lower & ~upper, upper & ~lower], [1, -1], default=0
            ),
            index=frame.index,
            dtype=int,
        )
        boundary = pd.Series(
            np.where(
                direction.gt(0), frame["prior_day_low"], frame["prior_day_high"]
            ),
            index=frame.index,
        )
        limit = boundary - direction * offset
        anchor = frame["prior_day_mid"]
        mask = regime.eq("CHOP") & direction.ne(0)
    elif mechanic == "CHOP_MOMENTUM_EXHAUSTION_LIMIT":
        bars = int(params["momentum_bars"])
        move = frame[f"return_{bars}_local"] / atr
        direction = -np.sign(move).fillna(0).astype(int)
        limit = close - direction * offset
        anchor = frame[f"prior_mean_{max(16, bars)}"]
        mask = regime.eq("CHOP") & move.abs().ge(float(params["momentum_atr"]))
    elif mechanic == "TRANS_ANCESTRY_EMA_PULLBACK_LIMIT":
        direction = frame["ancestry_direction"].astype(int)
        ema = frame["ema_fast"] if str(params["ema_source"]) == "FAST" else frame["ema_slow"]
        extension = direction * (close - ema) / atr
        limit = ema - direction * offset
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & extension.ge(float(params["minimum_extension_atr"]))
        )
    elif mechanic in (
        "TRANS_POST_COMPRESSION_RETEST_LIMIT",
        "TRANS_POST_CHOP_RETEST_LIMIT",
    ):
        lookback = int(params["lookback"])
        high = frame[f"prior_high_{lookback}"]
        low = frame[f"prior_low_{lookback}"]
        buffer = float(params["breakout_atr"]) * atr
        up = close.gt(high + buffer)
        down = close.lt(low - buffer)
        direction = pd.Series(
            np.select([up, down], [1, -1], default=0),
            index=frame.index,
            dtype=int,
        )
        boundary = pd.Series(
            np.where(direction.gt(0), high, low), index=frame.index
        )
        limit = boundary + direction * offset
        source = (
            "COMPRESSION"
            if mechanic == "TRANS_POST_COMPRESSION_RETEST_LIMIT"
            else "CHOP"
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & frame["last_resolved_regime"].eq(source)
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & direction.ne(0)
        )
    elif mechanic == "TRANS_MOMENTUM_PULLBACK_LIMIT":
        bars = int(params["momentum_bars"])
        move = frame[f"return_{bars}_local"] / atr
        direction = np.sign(move).fillna(0).astype(int)
        limit = close - direction * offset
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & move.abs().ge(float(params["momentum_atr"]))
        )
    elif mechanic == "TRANS_EXHAUSTION_PASSIVE_FADE":
        bars = int(params["momentum_bars"])
        move = frame[f"return_{bars}_local"] / atr
        direction = -np.sign(move).fillna(0).astype(int)
        limit = close - direction * offset
        anchor = frame[f"prior_mean_{max(16, bars)}"]
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & _source_mask(frame, str(params["source"]))
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & move.abs().ge(float(params["momentum_atr"]))
        )
    else:
        raise KeyError(mechanic)

    direction = pd.Series(direction, index=frame.index).astype(int)
    limit = pd.Series(limit, index=frame.index).astype(float)
    fixed = _fixed_target(limit, direction, atr, params)
    target = anchor if target_mode == "ANCHOR" else fixed
    risk = float(params["stop_atr"]) * atr
    reward_r = direction * (target - limit) / risk
    known_entry_side = pd.Series(
        np.where(direction.gt(0), frame["ask_close"], frame["bid_close"]),
        index=frame.index,
    )
    pending_distance_r = direction * (known_entry_side - limit) / risk
    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & direction.ne(0)
        & _hour_mask(frame, str(params["hour_window"]))
        & np.isfinite(limit)
        & np.isfinite(target)
        & np.isfinite(risk)
        & risk.gt(0.0)
        & pending_distance_r.ge(
            float(passive_execution["minimum_pending_distance_r"])
        )
        & reward_r.between(
            float(passive_execution["minimum_anchor_reward_r"]),
            float(passive_execution["maximum_anchor_reward_r"]),
            inclusive="both",
        )
    )
    return valid.astype(bool), direction, limit, target.astype(float)


def m5_execution_arrays(m5: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "starts": m5["bar_start_utc"].astype("int64").to_numpy(),
        "ends": m5["bar_end_utc"].astype("int64").to_numpy(),
        **{
            column: m5[column].to_numpy(dtype=float)
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


def simulate_pending_limit(
    arrays: Mapping[str, np.ndarray],
    signal_time_ns: int,
    direction: int,
    limit: float,
    target: float,
    risk: float,
    signal_spread: float,
    pending_expiry_hours: float,
    hold_hours: float,
    execution: Mapping[str, Any],
) -> dict[str, Any] | None:
    starts = arrays["starts"]
    activation = int(np.searchsorted(starts, int(signal_time_ns), side="left"))
    if activation >= len(starts):
        return None
    gap_minutes = (int(starts[activation]) - int(signal_time_ns)) / 60_000_000_000
    if gap_minutes < 0.0 or gap_minutes > float(execution["maximum_entry_gap_minutes"]):
        return None
    if not all(np.isfinite(value) for value in (limit, target, risk, signal_spread)):
        return None
    if risk <= 0.0 or signal_spread < 0.0:
        return None
    if signal_spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    if direction * (target - limit) <= 0.0:
        return None

    pending_deadline = int(signal_time_ns) + int(
        float(pending_expiry_hours) * 3_600_000_000_000
    )
    fill_index = -1
    for position in range(activation, len(starts)):
        if int(starts[position]) >= pending_deadline:
            break
        touched = (
            float(arrays["ask_low"][position]) <= limit
            if direction > 0
            else float(arrays["bid_high"][position]) >= limit
        )
        if touched:
            fill_index = position
            break
    if fill_index < 0:
        return None

    entry = float(limit)
    stop = entry - direction * risk
    fill_start = int(starts[fill_index])
    fill_end = int(arrays["ends"][fill_index])
    entry_time = pd.Timestamp(fill_end, unit="ns", tz="UTC")
    stop_open = (
        float(arrays["bid_open"][fill_index])
        if direction > 0
        else float(arrays["ask_open"][fill_index])
    )
    stop_hit = (
        float(arrays["bid_low"][fill_index]) <= stop
        if direction > 0
        else float(arrays["ask_high"][fill_index]) >= stop
    )
    if stop_hit:
        gap_stop = stop_open <= stop if direction > 0 else stop_open >= stop
        exit_price = stop_open if gap_stop else stop
        exit_time = entry_time
        exit_reason = "FILL_BAR_GAP_STOP" if gap_stop else "FILL_BAR_STOP_AMBIGUOUS"
    else:
        deadline = fill_end + int(float(hold_hours) * 3_600_000_000_000)
        exit_index = -1
        exit_price = float("nan")
        exit_reason = "NO_EXIT"
        for position in range(fill_index + 1, len(starts)):
            start = int(starts[position])
            executable_open = (
                float(arrays["bid_open"][position])
                if direction > 0
                else float(arrays["ask_open"][position])
            )
            if start >= deadline:
                horizon_gap = (start - deadline) / 3_600_000_000_000
                if horizon_gap > float(execution["maximum_horizon_gap_hours"]):
                    return None
                exit_index = position
                exit_price = executable_open
                exit_reason = "FIXED_HORIZON"
                break
            stop_at_open = executable_open <= stop if direction > 0 else executable_open >= stop
            target_at_open = executable_open >= target if direction > 0 else executable_open <= target
            if stop_at_open:
                exit_index = position
                exit_price = executable_open
                exit_reason = "GAP_THROUGH_STOP"
                break
            if target_at_open:
                exit_index = position
                exit_price = target
                exit_reason = "TARGET_AT_OPEN"
                break
            stop_touched = (
                float(arrays["bid_low"][position]) <= stop
                if direction > 0
                else float(arrays["ask_high"][position]) >= stop
            )
            target_touched = (
                float(arrays["bid_high"][position]) >= target
                if direction > 0
                else float(arrays["ask_low"][position]) <= target
            )
            if stop_touched:
                exit_index = position
                exit_price = stop
                exit_reason = "STOP_AMBIGUOUS" if target_touched else "STOP"
                break
            if target_touched:
                exit_index = position
                exit_price = target
                exit_reason = "TARGET"
                break
        if exit_index < 0:
            return None
        exit_ns = (
            int(starts[exit_index])
            if exit_reason in ("FIXED_HORIZON", "GAP_THROUGH_STOP", "TARGET_AT_OPEN")
            else int(arrays["ends"][exit_index])
        )
        exit_time = pd.Timestamp(exit_ns, unit="ns", tz="UTC")

    gross_r = direction * (float(exit_price) - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    costs_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "signal_time": pd.Timestamp(int(signal_time_ns), unit="ns", tz="UTC"),
        "entry_time": entry_time,
        "exit_time": exit_time,
        "direction": "LONG" if direction > 0 else "SHORT",
        "entry_price": entry,
        "exit_price": float(exit_price),
        "stop": stop,
        "target": target,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread_r": signal_spread / risk,
        "gross_r": gross_r,
        "stress_net_r": gross_r - costs_r - float(execution["stress_slippage_r"]),
        "pending_minutes": (fill_end - int(signal_time_ns)) / 60_000_000_000,
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "exit_reason": exit_reason,
    }


def simulate_variant(
    frame: pd.DataFrame,
    arrays: Mapping[str, np.ndarray],
    manifest_row: Any,
    execution: Mapping[str, Any],
    passive_execution: Mapping[str, Any],
    outcome_cache: dict[tuple[Any, ...], dict[str, Any] | None],
) -> pd.DataFrame:
    params = json.loads(str(manifest_row.parameters_json))
    mask, direction, limits, targets = signal_orders(
        frame, str(manifest_row.mechanic), params, passive_execution
    )
    selected: list[dict[str, Any]] = []
    busy_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        limit = float(limits.iat[int(signal_index)])
        target = float(targets.iat[int(signal_index)])
        risk = float(params["stop_atr"]) * float(frame["atr14"].iat[int(signal_index)])
        spread = float(
            frame["ask_close"].iat[int(signal_index)]
            - frame["bid_close"].iat[int(signal_index)]
        )
        signal_time_ns = int(frame["timestamp_utc"].iat[int(signal_index)].value)
        signal_time = pd.Timestamp(signal_time_ns, unit="ns", tz="UTC")
        if signal_time < busy_until:
            continue
        pending_until = signal_time + pd.Timedelta(
            hours=float(params["pending_expiry_hours"])
        )
        key = (
            signal_time_ns,
            sign,
            round(limit, 8),
            round(target, 8),
            round(risk, 8),
            float(params["pending_expiry_hours"]),
            float(params["hold_hours"]),
        )
        if key not in outcome_cache:
            outcome_cache[key] = simulate_pending_limit(
                arrays,
                signal_time_ns,
                sign,
                limit,
                target,
                risk,
                spread,
                float(params["pending_expiry_hours"]),
                float(params["hold_hours"]),
                execution,
            )
        outcome = outcome_cache[key]
        if outcome is None:
            busy_until = pending_until
            continue
        entry_time = pd.Timestamp(outcome["entry_time"])
        day = entry_time.date()
        if daily_count.get(day, 0) >= int(
            execution["maximum_trades_per_variant_utc_day"]
        ):
            busy_until = pending_until
            continue
        selected.append(outcome)
        busy_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(selected)
