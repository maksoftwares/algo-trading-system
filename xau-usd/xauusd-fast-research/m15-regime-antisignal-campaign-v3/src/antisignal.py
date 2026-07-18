from __future__ import annotations

import hashlib
import heapq
import itertools
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


MECHANICS: dict[str, tuple[str, ...]] = {
    "CHOP": (
        "CHOP_VWAP_ESCAPE",
        "CHOP_ASIAN_EDGE_ESCAPE",
        "CHOP_FAILED_FADE_CONTINUATION",
        "CHOP_ROLLING_EXTREME_ESCAPE",
        "CHOP_PRIOR_DAY_BREAKOUT",
    ),
    "TRANSITION": (
        "TRANS_POST_CHOP_BREAKOUT_FADE",
        "TRANS_REACTIVATION_FADE",
        "TRANS_SESSION_EXPANSION_FADE",
        "TRANS_POST_CHOP_MOMENTUM_FADE",
        "TRANS_ANCESTRY_EXHAUSTION_FADE",
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
        (root / "config" / "m15_regime_antisignal_campaign_v3.json").read_text(
            encoding="utf-8"
        )
    )
    base_path = (root / str(overlay["base"]["config_path"])).resolve()
    if sha256_file(base_path) != str(overlay["base"]["config_sha256"]):
        raise ValueError("Base config hash mismatch")
    config = json.loads(base_path.read_text(encoding="utf-8"))
    for key in ("schema_version", "selection", "outputs", "research_controls"):
        config[key] = overlay[key]
    config["base"] = overlay["base"]
    return config


def _space(**values: list[Any]) -> Iterable[dict[str, Any]]:
    keys = tuple(values)
    return (
        dict(zip(keys, combination, strict=True))
        for combination in itertools.product(*(values[key] for key in keys))
    )


def parameter_space(mechanic: str) -> Iterable[dict[str, Any]]:
    stops = [0.75, 1.0, 1.25, 1.5, 2.0]
    targets = [1.0, 1.25, 1.5, 2.0, 2.5]
    holds = [1, 2, 3, 4, 6, 8, 12]
    windows = ["ALL", "POST_ASIA", "LONDON", "LONDON_NY", "NEW_YORK"]
    if mechanic == "CHOP_VWAP_ESCAPE":
        return _space(
            deviation_atr=[0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            minimum_day_bars=[16, 24, 32, 40],
            hour_window=windows,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "CHOP_ASIAN_EDGE_ESCAPE":
        return _space(
            edge_fraction=[0.0, 0.05, 0.1, 0.15, 0.2],
            asia_range_atr_min=[1.0, 1.5, 2.0, 2.5],
            asia_range_atr_max=[4.0, 6.0, 8.0, 12.0],
            body_min=[0.1, 0.2, 0.3, 0.4],
            hour_window=["POST_ASIA", "LONDON", "LONDON_NY", "NEW_YORK"],
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "CHOP_FAILED_FADE_CONTINUATION":
        common = {
            "sweep_atr": [0.0, 0.05, 0.1, 0.2, 0.3],
            "close_back_atr": [0.0, 0.05, 0.1, 0.2],
            "wick_min": [0.1, 0.2, 0.3, 0.4],
            "hour_window": windows,
            "stop_atr": stops,
            "target_r": targets,
            "hold_hours": holds,
        }
        return itertools.chain(
            _space(lookback_source=["ASIAN"], **common),
            _space(
                lookback_source=["ROLLING"],
                lookback=[16, 24, 32, 48],
                **common,
            ),
        )
    if mechanic == "CHOP_ROLLING_EXTREME_ESCAPE":
        return _space(
            lookback=[16, 24, 32, 48, 72, 96],
            deviation_atr=[0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=windows,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "CHOP_PRIOR_DAY_BREAKOUT":
        return _space(
            breakout_atr=[0.0, 0.05, 0.1, 0.2, 0.3],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=windows,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "TRANS_POST_CHOP_BREAKOUT_FADE":
        return _space(
            transition_age_max=[4, 8, 16, 32, 48],
            lookback=[8, 12, 16, 24, 32, 48],
            breakout_atr=[0.0, 0.05, 0.1, 0.2, 0.3],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=windows,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "TRANS_REACTIVATION_FADE":
        return _space(
            transition_age_max=[4, 8, 16, 32, 48],
            touch_atr=[-0.1, 0.0, 0.1, 0.2, 0.35, 0.5],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=windows,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "TRANS_SESSION_EXPANSION_FADE":
        return _space(
            source=["ANY", "COMPRESSION", "CHOP", "ANY_TREND"],
            transition_age_max=[8, 16, 32, 48],
            breakout_atr=[0.0, 0.05, 0.1, 0.2, 0.3],
            asia_range_atr_max=[4.0, 6.0, 8.0, 12.0],
            body_min=[0.1, 0.2, 0.3, 0.4],
            hour_window=["POST_ASIA", "LONDON", "LONDON_NY", "NEW_YORK"],
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "TRANS_POST_CHOP_MOMENTUM_FADE":
        return _space(
            transition_age_max=[8, 16, 32, 48],
            momentum_bars=[2, 4, 8, 16, 24],
            momentum_atr=[0.4, 0.6, 0.8, 1.0, 1.25],
            rsi_period=[2, 3, 4, 6, 9],
            rsi_tail=[10, 15, 20, 25, 30, 35],
            hour_window=windows,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "TRANS_ANCESTRY_EXHAUSTION_FADE":
        return _space(
            transition_age_max=[8, 16, 32, 48],
            momentum_bars=[2, 4, 8, 16, 24],
            momentum_atr=[0.4, 0.6, 0.8, 1.0, 1.25],
            wick_min=[0.0, 0.1, 0.2, 0.3, 0.4],
            hour_window=windows,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    raise KeyError(mechanic)


def generate_manifest(selection: Mapping[str, Any]) -> pd.DataFrame:
    per_mechanic = int(selection["variants_per_mechanic"])
    attempt = int(selection["attempt_first"])
    rows: list[dict[str, Any]] = []
    for owner, mechanics in MECHANICS.items():
        for mechanic in mechanics:
            candidates = heapq.nsmallest(
                per_mechanic,
                parameter_space(mechanic),
                key=lambda params: hashlib.sha256(
                    f"{owner}|{mechanic}|{json.dumps(params, sort_keys=True)}".encode("ascii")
                ).hexdigest(),
            )
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
    if len(result) != int(selection["total_attempts"]):
        raise ValueError("Attempt count does not match contract")
    if int(result["attempt_no"].iat[-1]) != int(selection["attempt_last"]):
        raise ValueError("Attempt boundary does not match contract")
    if result["variant_id"].duplicated().any():
        raise ValueError("Duplicate variant IDs")
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


def _break_direction(frame: pd.DataFrame, high: pd.Series, low: pd.Series, buffer_atr: float) -> pd.Series:
    up = frame["mid_close"].gt(high + buffer_atr * frame["atr14"])
    down = frame["mid_close"].lt(low - buffer_atr * frame["atr14"])
    return pd.Series(np.select([up, down], [1, -1], default=0), index=frame.index, dtype=int)


def _false_break_fade(
    frame: pd.DataFrame,
    high: pd.Series,
    low: pd.Series,
    sweep_atr: float,
    close_back_atr: float,
    wick_min: float,
) -> pd.Series:
    atr = frame["atr14"]
    high_sweep = (
        frame["mid_high"].gt(high + sweep_atr * atr)
        & frame["mid_close"].lt(high - close_back_atr * atr)
        & frame["upper_wick"].ge(wick_min)
    )
    low_sweep = (
        frame["mid_low"].lt(low - sweep_atr * atr)
        & frame["mid_close"].gt(low + close_back_atr * atr)
        & frame["lower_wick"].ge(wick_min)
    )
    return pd.Series(
        np.select([high_sweep, low_sweep], [-1, 1], default=0),
        index=frame.index,
        dtype=int,
    )


def signal_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series, pd.Series]:
    close = frame["mid_close"]
    atr = frame["atr14"]
    candle = frame["candle_direction"]
    regime = frame["regime"]
    direction = pd.Series(0, index=frame.index, dtype=int)

    if mechanic == "CHOP_VWAP_ESCAPE":
        deviation = frame["vwap_deviation_atr"]
        direction = np.sign(deviation).fillna(0).astype(int)
        mask = (
            regime.eq("CHOP")
            & deviation.abs().ge(float(params["deviation_atr"]))
            & frame["day_bar_number"].ge(int(params["minimum_day_bars"]))
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "CHOP_ASIAN_EDGE_ESCAPE":
        width = (frame["asian_high"] - frame["asian_low"]).replace(0.0, np.nan)
        location = (close - frame["asian_low"]) / width
        edge = float(params["edge_fraction"])
        direction = pd.Series(
            np.select([location.le(edge), location.ge(1.0 - edge)], [-1, 1], default=0),
            index=frame.index,
            dtype=int,
        )
        mask = (
            regime.eq("CHOP")
            & frame["asian_range_atr"].between(
                float(params["asia_range_atr_min"]), float(params["asia_range_atr_max"]), inclusive="both"
            )
            & direction.ne(0)
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
        )
    elif mechanic == "CHOP_FAILED_FADE_CONTINUATION":
        if str(params["lookback_source"]) == "ASIAN":
            high, low = frame["asian_high"], frame["asian_low"]
        else:
            lookback = int(params["lookback"])
            high, low = frame[f"prior_high_{lookback}"], frame[f"prior_low_{lookback}"]
        fade = _false_break_fade(
            frame, high, low, float(params["sweep_atr"]),
            float(params["close_back_atr"]), float(params["wick_min"]),
        )
        direction = -fade
        mask = regime.eq("CHOP") & direction.ne(0)
    elif mechanic == "CHOP_ROLLING_EXTREME_ESCAPE":
        lookback = int(params["lookback"])
        deviation = (close - frame[f"prior_mean_{lookback}"]) / atr
        direction = np.sign(deviation).fillna(0).astype(int)
        mask = (
            regime.eq("CHOP")
            & deviation.abs().ge(float(params["deviation_atr"]))
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "CHOP_PRIOR_DAY_BREAKOUT":
        direction = _break_direction(
            frame, frame["prior_day_high"], frame["prior_day_low"], float(params["breakout_atr"])
        )
        mask = (
            regime.eq("CHOP")
            & direction.ne(0)
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_POST_CHOP_BREAKOUT_FADE":
        breakout = _break_direction(
            frame,
            frame[f"prior_high_{int(params['lookback'])}"],
            frame[f"prior_low_{int(params['lookback'])}"],
            float(params["breakout_atr"]),
        )
        direction = -breakout
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & frame["last_resolved_regime"].eq("CHOP")
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & direction.ne(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_REACTIVATION_FADE":
        ancestry = frame["ancestry_direction"].astype(int)
        direction = -ancestry
        touch = pd.Series(
            np.where(
                ancestry.gt(0),
                frame["mid_low"].le(frame["ema_fast"] + float(params["touch_atr"]) * atr),
                frame["mid_high"].ge(frame["ema_fast"] - float(params["touch_atr"]) * atr),
            ),
            index=frame.index,
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & touch
            & ancestry.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_SESSION_EXPANSION_FADE":
        breakout = _break_direction(
            frame, frame["asian_high"], frame["asian_low"], float(params["breakout_atr"])
        )
        direction = -breakout
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & _source_mask(frame, str(params["source"]))
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & frame["asian_range_atr"].le(float(params["asia_range_atr_max"]))
            & direction.ne(0)
            & frame["body"].ge(float(params["body_min"]))
        )
    elif mechanic == "TRANS_POST_CHOP_MOMENTUM_FADE":
        momentum = frame[f"return_{int(params['momentum_bars'])}_local"]
        move_direction = np.sign(momentum).fillna(0).astype(int)
        direction = -move_direction
        rsi = frame[f"rsi_{int(params['rsi_period'])}"]
        tail = float(params["rsi_tail"])
        extreme = pd.Series(
            np.where(move_direction.gt(0), rsi.ge(100.0 - tail), rsi.le(tail)), index=frame.index
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & frame["last_resolved_regime"].eq("CHOP")
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & momentum.abs().div(atr).ge(float(params["momentum_atr"]))
            & direction.ne(0)
            & extreme
        )
    elif mechanic == "TRANS_ANCESTRY_EXHAUSTION_FADE":
        ancestry = frame["ancestry_direction"].astype(int)
        momentum = frame[f"return_{int(params['momentum_bars'])}_local"] / atr
        direction = -ancestry
        wick = pd.Series(
            np.where(direction.gt(0), frame["lower_wick"], frame["upper_wick"]), index=frame.index
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & ancestry.mul(momentum).ge(float(params["momentum_atr"]))
            & wick.ge(float(params["wick_min"]))
        )
    else:
        raise KeyError(mechanic)

    target = close + direction * float(params["target_r"]) * float(params["stop_atr"]) * atr
    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & pd.Series(direction, index=frame.index).ne(0)
        & _hour_mask(frame, str(params["hour_window"]))
        & np.isfinite(target)
        & np.isfinite(atr)
        & atr.gt(0.0)
    )
    return valid.astype(bool), pd.Series(direction, index=frame.index).astype(int), target.astype(float)


def simulate_variant(
    frame: pd.DataFrame,
    arrays: Mapping[str, np.ndarray],
    manifest_row: Any,
    execution: Mapping[str, Any],
    outcome_cache: dict[tuple[Any, ...], dict[str, Any] | None],
    base_campaign: Any,
) -> pd.DataFrame:
    params = json.loads(str(manifest_row.parameters_json))
    mask, direction, targets = signal_mask_direction(frame, str(manifest_row.mechanic), params)
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        target = float(targets.iat[int(signal_index)])
        key = (
            int(signal_index), sign, round(target, 8),
            float(params["stop_atr"]), float(params["hold_hours"]),
        )
        if key not in outcome_cache:
            outcome_cache[key] = base_campaign.simulate_trade(
                arrays, int(signal_index), sign, target,
                float(params["stop_atr"]), float(params["hold_hours"]), execution,
            )
        outcome = outcome_cache[key]
        if outcome is None:
            continue
        entry_time = pd.Timestamp(outcome["entry_time"])
        if entry_time < position_until:
            continue
        day = entry_time.date()
        if daily_count.get(day, 0) >= int(execution["maximum_trades_per_variant_utc_day"]):
            continue
        selected.append(outcome)
        position_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(selected)
