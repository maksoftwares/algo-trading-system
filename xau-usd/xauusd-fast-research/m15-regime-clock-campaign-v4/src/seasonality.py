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
        "CHOP_FIXED_CLOCK_CARRY",
        "CHOP_ASIA_INVENTORY_RESPONSE",
        "CHOP_PRIOR_DAY_RESPONSE",
        "CHOP_SESSION_HANDOFF_RESPONSE",
        "CHOP_WEEKDAY_CLOCK_CARRY",
    ),
    "TRANSITION": (
        "TRANS_FIXED_CLOCK_CARRY",
        "TRANS_TREND_ANCESTRY_CLOCK",
        "TRANS_POST_COMPRESSION_SESSION_RESPONSE",
        "TRANS_POST_CHOP_SESSION_RESPONSE",
        "TRANS_WEEKDAY_ANCESTRY_RESPONSE",
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
        (root / "config" / "m15_regime_clock_campaign_v4.json").read_text(
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


def _bounded_space(**values: list[Any]) -> Iterable[dict[str, Any]]:
    for params in _space(**values):
        if float(params.get("minimum_move_atr", 0.0)) <= float(
            params.get("maximum_move_atr", float("inf"))
        ):
            yield params


def parameter_space(mechanic: str) -> Iterable[dict[str, Any]]:
    stops = [1.0, 1.25, 1.5, 2.0]
    targets = [1.0, 1.25, 1.5, 2.0, 2.5]
    holds = [2, 4, 6, 8, 12]
    hours = [0, 2, 6, 8, 12, 14, 16, 20]
    responses = ["CONTINUE", "FADE"]
    weekday_groups = ["ALL", "MON_THU", "TUE_FRI"]
    move_common = {
        "response": responses,
        "minimum_move_atr": [0.0, 0.25, 0.5, 0.75, 1.0],
        "maximum_move_atr": [1.0, 1.5, 2.0, 3.0, 5.0],
        "weekday_group": weekday_groups,
        "stop_atr": stops,
        "target_r": targets,
        "hold_hours": holds,
    }
    if mechanic == "CHOP_FIXED_CLOCK_CARRY":
        return _space(
            signal_hour=hours,
            fixed_direction=[-1, 1],
            weekday_group=weekday_groups,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "CHOP_ASIA_INVENTORY_RESPONSE":
        return _bounded_space(signal_hour=[6, 7, 8, 9, 12], **move_common)
    if mechanic == "CHOP_PRIOR_DAY_RESPONSE":
        return _bounded_space(signal_hour=hours, **move_common)
    if mechanic == "CHOP_SESSION_HANDOFF_RESPONSE":
        return _bounded_space(
            signal_hour=[6, 8, 12, 14, 16, 20],
            return_bars=[8, 16, 24, 32],
            **move_common,
        )
    if mechanic == "CHOP_WEEKDAY_CLOCK_CARRY":
        return _space(
            signal_hour=hours,
            weekday=[0, 1, 2, 3, 4],
            fixed_direction=[-1, 1],
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "TRANS_FIXED_CLOCK_CARRY":
        return _space(
            signal_hour=hours,
            source=["ANY", "CHOP", "COMPRESSION", "ANY_TREND"],
            transition_age_max=[8, 16, 32, 48, 96],
            fixed_direction=[-1, 1],
            weekday_group=weekday_groups,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "TRANS_TREND_ANCESTRY_CLOCK":
        return _space(
            signal_hour=hours,
            ancestry_response=responses,
            transition_age_max=[8, 16, 32, 48, 96],
            weekday_group=weekday_groups,
            stop_atr=stops,
            target_r=targets,
            hold_hours=holds,
        )
    if mechanic == "TRANS_POST_COMPRESSION_SESSION_RESPONSE":
        return _bounded_space(
            signal_hour=[6, 8, 12, 14, 16, 20],
            return_bars=[8, 16, 24, 32],
            transition_age_max=[8, 16, 32, 48, 96],
            **move_common,
        )
    if mechanic == "TRANS_POST_CHOP_SESSION_RESPONSE":
        return _bounded_space(
            signal_hour=[6, 8, 12, 14, 16, 20],
            return_bars=[8, 16, 24, 32],
            transition_age_max=[8, 16, 32, 48, 96],
            **move_common,
        )
    if mechanic == "TRANS_WEEKDAY_ANCESTRY_RESPONSE":
        return _space(
            signal_hour=hours,
            weekday=[0, 1, 2, 3, 4],
            ancestry_response=responses,
            transition_age_max=[8, 16, 32, 48, 96],
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
                    f"{owner}|{mechanic}|{json.dumps(params, sort_keys=True)}".encode(
                        "ascii"
                    )
                ).hexdigest(),
            )
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
    if len(result) != int(selection["total_attempts"]):
        raise ValueError("Attempt count does not match contract")
    expected = list(
        range(int(selection["attempt_first"]), int(selection["attempt_last"]) + 1)
    )
    if result["attempt_no"].tolist() != expected:
        raise ValueError("Attempt boundary does not match contract")
    if result["variant_id"].duplicated().any():
        raise ValueError("Duplicate variant IDs")
    return result


def prepare_clock_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    bar_start = pd.to_datetime(result["bar_start_utc"], utc=True)
    day = bar_start.dt.normalize()
    result["minute"] = bar_start.dt.minute.astype(int)
    result["weekday"] = bar_start.dt.weekday.astype(int)

    completed_asia = bar_start.dt.hour.eq(5) & bar_start.dt.minute.eq(45)
    asia_close_by_day = result.loc[completed_asia].groupby(
        day.loc[completed_asia], sort=True
    )["mid_close"].last()
    asia_close = day.map(asia_close_by_day)
    result["asia_close"] = asia_close.where(bar_start.dt.hour.ge(6))
    result["asia_return_atr"] = (
        result["asia_close"] - result["day_open"]
    ) / result["atr14"]

    daily = result.groupby(day, sort=True).agg(
        utc_open=("mid_open", "first"), utc_close=("mid_close", "last")
    )
    prior_return = (daily["utc_close"] - daily["utc_open"]).shift(1)
    result["prior_day_return_atr"] = day.map(prior_return) / result["atr14"]
    for bars in (8, 16, 24, 32):
        result[f"session_return_{bars}_atr"] = (
            result[f"return_{bars}_local"] / result["atr14"]
        )
    return result


def _clock_mask(frame: pd.DataFrame, hour: int) -> pd.Series:
    return frame["hour"].eq(int(hour)) & frame["minute"].eq(0)


def _weekday_group_mask(frame: pd.DataFrame, name: str) -> pd.Series:
    weekday = frame["weekday"]
    if name == "ALL":
        return weekday.le(4)
    if name == "MON_THU":
        return weekday.le(3)
    if name == "TUE_FRI":
        return weekday.between(1, 4)
    raise KeyError(name)


def _source_mask(frame: pd.DataFrame, source: str) -> pd.Series:
    ancestor = frame["last_resolved_regime"]
    if source == "ANY":
        return pd.Series(True, index=frame.index)
    if source == "ANY_TREND":
        return ancestor.isin(("TREND_UP", "TREND_DOWN"))
    return ancestor.eq(source)


def _response_direction(move: pd.Series, response: str) -> pd.Series:
    sign = np.sign(move).fillna(0).astype(int)
    if response == "CONTINUE":
        return sign
    if response == "FADE":
        return -sign
    raise KeyError(response)


def _move_mask(move: pd.Series, params: Mapping[str, Any]) -> pd.Series:
    return move.abs().between(
        float(params["minimum_move_atr"]),
        float(params["maximum_move_atr"]),
        inclusive="both",
    )


def signal_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series, pd.Series]:
    regime = frame["regime"]
    direction = pd.Series(0, index=frame.index, dtype=int)
    clock = _clock_mask(frame, int(params["signal_hour"]))

    if mechanic == "CHOP_FIXED_CLOCK_CARRY":
        direction[:] = int(params["fixed_direction"])
        mask = (
            regime.eq("CHOP")
            & clock
            & _weekday_group_mask(frame, str(params["weekday_group"]))
        )
    elif mechanic == "CHOP_ASIA_INVENTORY_RESPONSE":
        move = frame["asia_return_atr"]
        direction = _response_direction(move, str(params["response"]))
        mask = (
            regime.eq("CHOP")
            & clock
            & _weekday_group_mask(frame, str(params["weekday_group"]))
            & _move_mask(move, params)
        )
    elif mechanic == "CHOP_PRIOR_DAY_RESPONSE":
        move = frame["prior_day_return_atr"]
        direction = _response_direction(move, str(params["response"]))
        mask = (
            regime.eq("CHOP")
            & clock
            & _weekday_group_mask(frame, str(params["weekday_group"]))
            & _move_mask(move, params)
        )
    elif mechanic == "CHOP_SESSION_HANDOFF_RESPONSE":
        move = frame[f"session_return_{int(params['return_bars'])}_atr"]
        direction = _response_direction(move, str(params["response"]))
        mask = (
            regime.eq("CHOP")
            & clock
            & _weekday_group_mask(frame, str(params["weekday_group"]))
            & _move_mask(move, params)
        )
    elif mechanic == "CHOP_WEEKDAY_CLOCK_CARRY":
        direction[:] = int(params["fixed_direction"])
        mask = regime.eq("CHOP") & clock & frame["weekday"].eq(int(params["weekday"]))
    elif mechanic == "TRANS_FIXED_CLOCK_CARRY":
        direction[:] = int(params["fixed_direction"])
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & clock
            & _source_mask(frame, str(params["source"]))
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & _weekday_group_mask(frame, str(params["weekday_group"]))
        )
    elif mechanic == "TRANS_TREND_ANCESTRY_CLOCK":
        direction = frame["ancestry_direction"].astype(int)
        if str(params["ancestry_response"]) == "FADE":
            direction = -direction
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & clock
            & direction.ne(0)
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & _weekday_group_mask(frame, str(params["weekday_group"]))
        )
    elif mechanic in (
        "TRANS_POST_COMPRESSION_SESSION_RESPONSE",
        "TRANS_POST_CHOP_SESSION_RESPONSE",
    ):
        move = frame[f"session_return_{int(params['return_bars'])}_atr"]
        direction = _response_direction(move, str(params["response"]))
        source = (
            "COMPRESSION"
            if mechanic == "TRANS_POST_COMPRESSION_SESSION_RESPONSE"
            else "CHOP"
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & clock
            & frame["last_resolved_regime"].eq(source)
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & _weekday_group_mask(frame, str(params["weekday_group"]))
            & _move_mask(move, params)
        )
    elif mechanic == "TRANS_WEEKDAY_ANCESTRY_RESPONSE":
        direction = frame["ancestry_direction"].astype(int)
        if str(params["ancestry_response"]) == "FADE":
            direction = -direction
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & clock
            & frame["weekday"].eq(int(params["weekday"]))
            & direction.ne(0)
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
        )
    else:
        raise KeyError(mechanic)

    direction = pd.Series(direction, index=frame.index).astype(int)
    atr = frame["atr14"]
    target = (
        frame["mid_close"]
        + direction
        * float(params["target_r"])
        * float(params["stop_atr"])
        * atr
    )
    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & direction.ne(0)
        & np.isfinite(target)
        & np.isfinite(atr)
        & atr.gt(0.0)
    )
    return valid.astype(bool), direction, target.astype(float)


def simulate_variant(
    frame: pd.DataFrame,
    arrays: Mapping[str, np.ndarray],
    manifest_row: Any,
    execution: Mapping[str, Any],
    outcome_cache: dict[tuple[Any, ...], dict[str, Any] | None],
    base_campaign: Any,
) -> pd.DataFrame:
    params = json.loads(str(manifest_row.parameters_json))
    mask, direction, targets = signal_mask_direction(
        frame, str(manifest_row.mechanic), params
    )
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        target = float(targets.iat[int(signal_index)])
        key = (
            int(signal_index),
            sign,
            round(target, 8),
            float(params["stop_atr"]),
            float(params["hold_hours"]),
        )
        if key not in outcome_cache:
            outcome_cache[key] = base_campaign.simulate_trade(
                arrays,
                int(signal_index),
                sign,
                target,
                float(params["stop_atr"]),
                float(params["hold_hours"]),
                execution,
            )
        outcome = outcome_cache[key]
        if outcome is None:
            continue
        entry_time = pd.Timestamp(outcome["entry_time"])
        if entry_time < position_until:
            continue
        day = entry_time.date()
        if daily_count.get(day, 0) >= int(
            execution["maximum_trades_per_variant_utc_day"]
        ):
            continue
        selected.append(outcome)
        position_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(selected)
