from __future__ import annotations

import hashlib
from itertools import product
import json
from typing import Any, Callable, Iterable, Mapping

import numpy as np
import pandas as pd


MECHANICS = {
    "CHOP": (
        "CHOP_MACRO_RESIDUAL_FADE",
        "CHOP_RESIDUAL_REENTRY_FADE",
        "CHOP_CONSENSUS_LAG_CATCHUP",
        "CHOP_DISAGREEMENT_GOLD_FADE",
        "CHOP_BETA_OVERSHOOT_FADE",
    ),
    "TRANSITION": (
        "TRANS_ANCESTRY_RESIDUAL_REACCELERATION",
        "TRANS_MACRO_RESIDUAL_CATCHUP",
        "TRANS_RESIDUAL_BREAKOUT",
        "TRANS_SINGLE_FACTOR_RESOLUTION",
        "TRANS_ANCESTRY_OVERSHOOT_REVERSAL",
    ),
}

HOUR_WINDOWS = ("ALL", "LIQUID", "NEW_YORK")


def _space(**values: Iterable[Any]) -> Iterable[dict[str, Any]]:
    names = tuple(values)
    for combination in product(*(tuple(values[name]) for name in names)):
        yield dict(zip(names, combination, strict=True))


def parameter_space(
    owner: str, mechanic: str, config: Mapping[str, Any]
) -> Iterable[dict[str, Any]]:
    shared = {
        "feature_key": tuple(config["residual_features"]["keys"]),
        "hour_window": HOUR_WINDOWS,
        "geometry_id": tuple(config["geometries"][owner]),
    }
    confirmation = {
        "require_confirmation": (False, True),
        "body_min": (0.0, 0.2, 0.4),
    }
    if mechanic == "CHOP_MACRO_RESIDUAL_FADE":
        return _space(
            z_min=(0.75, 1.0, 1.25, 1.5, 2.0),
            macro_mode=("ANY", "CONSENSUS", "DISAGREEMENT"),
            pressure_min=(0.0, 0.5, 1.0),
            **confirmation,
            **shared,
        )
    if mechanic == "CHOP_RESIDUAL_REENTRY_FADE":
        return _space(
            prior_z_min=(1.0, 1.25, 1.5, 2.0),
            current_z_max=(0.5, 0.75, 1.0, 1.25),
            **confirmation,
            **shared,
        )
    if mechanic == "CHOP_CONSENSUS_LAG_CATCHUP":
        return _space(
            pressure_min=(0.25, 0.5, 0.75, 1.0),
            lag_z_min=(0.25, 0.5, 0.75, 1.0, 1.25),
            maximum_gold_alignment_atr=(-0.25, 0.0, 0.25, 0.5),
            **confirmation,
            **shared,
        )
    if mechanic == "CHOP_DISAGREEMENT_GOLD_FADE":
        return _space(
            pressure_min=(0.25, 0.5, 0.75, 1.0),
            balance_min=(0.25, 0.5, 0.75),
            gold_extension_atr=(0.25, 0.5, 0.75, 1.0, 1.25),
            **confirmation,
            **shared,
        )
    if mechanic == "CHOP_BETA_OVERSHOOT_FADE":
        return _space(
            z_min=(0.75, 1.0, 1.25, 1.5, 2.0),
            beta_abs_min=(0.05, 0.15, 0.30, 0.50),
            pressure_min=(0.0, 0.25, 0.5, 0.75),
            **confirmation,
            **shared,
        )
    if mechanic == "TRANS_ANCESTRY_RESIDUAL_REACCELERATION":
        return _space(
            pressure_min=(0.25, 0.5, 0.75, 1.0),
            residual_floor=(-2.0, -1.5, -1.0, -0.5),
            residual_ceiling=(0.0, 0.25, 0.5, 0.75),
            transition_age_max=(16, 48, 96, 192),
            **confirmation,
            **shared,
        )
    if mechanic == "TRANS_MACRO_RESIDUAL_CATCHUP":
        return _space(
            pressure_min=(0.25, 0.5, 0.75, 1.0),
            lag_z_min=(0.25, 0.5, 0.75, 1.0, 1.25),
            ancestry_relation=("ANY", "AGREE", "OPPOSE"),
            transition_age_max=(16, 48, 96, 192),
            **confirmation,
            **shared,
        )
    if mechanic == "TRANS_RESIDUAL_BREAKOUT":
        return _space(
            z_min=(0.5, 0.75, 1.0, 1.25, 1.5, 2.0),
            pressure_min=(0.0, 0.25, 0.5, 0.75),
            macro_relation=("ANY", "AGREE"),
            transition_age_max=(16, 48, 96, 192),
            **confirmation,
            **shared,
        )
    if mechanic == "TRANS_SINGLE_FACTOR_RESOLUTION":
        return _space(
            dominant_pressure_min=(0.5, 0.75, 1.0, 1.25),
            other_pressure_max=(0.25, 0.5, 0.75, 1.0),
            ancestry_relation=("ANY", "AGREE", "OPPOSE"),
            transition_age_max=(16, 48, 96, 192),
            **confirmation,
            **shared,
        )
    if mechanic == "TRANS_ANCESTRY_OVERSHOOT_REVERSAL":
        return _space(
            z_min=(0.75, 1.0, 1.25, 1.5, 2.0),
            macro_pressure_max=(0.25, 0.5, 0.75, 1.0),
            transition_age_min=(4, 16, 32),
            transition_age_max=(48, 96, 192),
            **confirmation,
            **shared,
        )
    raise KeyError(f"Unknown mechanic for {owner}: {mechanic}")


def _prior_rolling(
    frame: pd.DataFrame,
    columns: list[str],
    window: str,
    minimum: int,
) -> pd.DataFrame:
    indexed = frame.set_index("timestamp_utc")[columns]
    result = indexed.rolling(window, min_periods=minimum, closed="left").mean()
    return result.reset_index(drop=True)


def enrich_residual_features(
    frame: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    result = frame.copy().sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    if result["timestamp_utc"].duplicated().any():
        raise ValueError("Residual decisions contain duplicate timestamps")
    settings = config["residual_features"]
    for key in settings["keys"]:
        horizon, scale = str(key).split("_", maxsplit=1)
        dxy = result[f"dxy_pressure_{key}"].astype(float)
        bond = result[f"bond_pressure_{key}"].astype(float)
        gold = result[f"gold_return_{horizon}_atr"].astype(float)
        consensus = (dxy + bond) / 2.0
        work = pd.DataFrame(
            {
                "timestamp_utc": result["timestamp_utc"],
                "x": consensus,
                "y": gold,
                "xy": consensus * gold,
                "xx": consensus * consensus,
                "yy": gold * gold,
            }
        )
        window = str(settings["rolling_windows"][scale])
        minimum = int(settings["minimum_observations"][scale])
        prior = _prior_rolling(work, ["x", "y", "xy", "xx", "yy"], window, minimum)
        covariance = prior["xy"] - prior["x"] * prior["y"]
        variance_x = prior["xx"] - prior["x"] * prior["x"]
        variance_y = prior["yy"] - prior["y"] * prior["y"]
        beta = (covariance / variance_x.replace(0.0, np.nan)).clip(
            -float(settings["beta_clip"]), float(settings["beta_clip"])
        )
        correlation = covariance / np.sqrt(
            variance_x.clip(lower=0.0) * variance_y.clip(lower=0.0)
        ).replace(0.0, np.nan)
        residual = gold - beta * consensus
        residual_work = pd.DataFrame(
            {
                "timestamp_utc": result["timestamp_utc"],
                "residual": residual,
                "residual_sq": residual * residual,
            }
        )
        residual_prior = _prior_rolling(
            residual_work, ["residual", "residual_sq"], window, minimum
        )
        residual_variance = residual_prior["residual_sq"] - residual_prior["residual"] ** 2
        residual_std = np.sqrt(residual_variance.clip(lower=0.0)).replace(0.0, np.nan)
        result[f"residual_{key}"] = residual
        result[f"residual_z_{key}"] = (
            residual - residual_prior["residual"]
        ) / residual_std
        result[f"macro_consensus_{key}"] = consensus
        result[f"macro_agreement_{key}"] = np.sign(dxy).eq(np.sign(bond)) & dxy.ne(0.0) & bond.ne(0.0)
        result[f"macro_min_pressure_{key}"] = pd.concat((dxy.abs(), bond.abs()), axis=1).min(axis=1)
        result[f"macro_max_pressure_{key}"] = pd.concat((dxy.abs(), bond.abs()), axis=1).max(axis=1)
        result[f"macro_balance_{key}"] = result[f"macro_min_pressure_{key}"] / result[f"macro_max_pressure_{key}"].replace(0.0, np.nan)
        result[f"residual_beta_{key}"] = beta
        result[f"residual_correlation_{key}"] = correlation
    return result


def _hour_mask(frame: pd.DataFrame, name: str) -> pd.Series:
    hour = frame["hour_utc"]
    if name == "ALL":
        return pd.Series(True, index=frame.index)
    if name == "LIQUID":
        return hour.between(5, 18)
    if name == "NEW_YORK":
        return hour.between(12, 18)
    raise KeyError(name)


def _confirmation(
    frame: pd.DataFrame, direction: pd.Series, params: Mapping[str, Any]
) -> pd.Series:
    result = frame["body"].ge(float(params["body_min"]))
    if bool(params["require_confirmation"]):
        result &= direction.mul(frame["candle_direction"]).gt(0)
    return result


def _ancestry_relation(
    direction: pd.Series, ancestry: pd.Series, relation: str
) -> pd.Series:
    if relation == "ANY":
        return pd.Series(True, index=direction.index)
    if relation == "AGREE":
        return ancestry.ne(0) & direction.eq(ancestry)
    if relation == "OPPOSE":
        return ancestry.ne(0) & direction.eq(-ancestry)
    raise KeyError(relation)


def signal_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series]:
    key = str(params["feature_key"])
    horizon = key.split("_", maxsplit=1)[0]
    z = frame[f"residual_z_{key}"]
    dxy = frame[f"dxy_pressure_{key}"]
    bond = frame[f"bond_pressure_{key}"]
    gold = frame[f"gold_return_{horizon}_atr"]
    agreement = frame[f"macro_agreement_{key}"]
    minimum_pressure = frame[f"macro_min_pressure_{key}"]
    maximum_pressure = frame[f"macro_max_pressure_{key}"]
    balance = frame[f"macro_balance_{key}"]
    consensus_direction = pd.Series(
        np.where(agreement, np.sign(frame[f"macro_consensus_{key}"]), 0).astype(int),
        index=frame.index,
    )
    ancestry = frame["ancestry_direction"].astype(int)
    direction = pd.Series(0, index=frame.index, dtype=int)
    owner = "CHOP" if mechanic.startswith("CHOP_") else "TRANSITION"

    if mechanic == "CHOP_MACRO_RESIDUAL_FADE":
        direction = -np.sign(z).fillna(0).astype(int)
        mode = str(params["macro_mode"])
        macro_ready = pd.Series(True, index=frame.index)
        if mode == "CONSENSUS":
            macro_ready = agreement & minimum_pressure.ge(float(params["pressure_min"]))
        elif mode == "DISAGREEMENT":
            macro_ready = ~agreement & minimum_pressure.ge(float(params["pressure_min"]))
        elif mode != "ANY":
            raise KeyError(mode)
        mask = z.abs().ge(float(params["z_min"])) & macro_ready
    elif mechanic == "CHOP_RESIDUAL_REENTRY_FADE":
        prior = z.shift(1)
        direction = -np.sign(prior).fillna(0).astype(int)
        mask = (
            prior.abs().ge(float(params["prior_z_min"]))
            & z.abs().le(float(params["current_z_max"]))
            & z.abs().lt(prior.abs())
            & np.sign(z).eq(np.sign(prior))
        )
    elif mechanic == "CHOP_CONSENSUS_LAG_CATCHUP":
        direction = consensus_direction
        aligned_z = direction.mul(z)
        aligned_gold = direction.mul(gold)
        mask = (
            agreement
            & minimum_pressure.ge(float(params["pressure_min"]))
            & aligned_z.le(-float(params["lag_z_min"]))
            & aligned_gold.le(float(params["maximum_gold_alignment_atr"]))
        )
    elif mechanic == "CHOP_DISAGREEMENT_GOLD_FADE":
        direction = -np.sign(gold).fillna(0).astype(int)
        mask = (
            ~agreement
            & minimum_pressure.ge(float(params["pressure_min"]))
            & balance.ge(float(params["balance_min"]))
            & gold.abs().ge(float(params["gold_extension_atr"]))
        )
    elif mechanic == "CHOP_BETA_OVERSHOOT_FADE":
        direction = -np.sign(z).fillna(0).astype(int)
        mask = (
            agreement
            & z.abs().ge(float(params["z_min"]))
            & frame[f"residual_beta_{key}"].abs().ge(float(params["beta_abs_min"]))
            & minimum_pressure.ge(float(params["pressure_min"]))
        )
    elif mechanic == "TRANS_ANCESTRY_RESIDUAL_REACCELERATION":
        direction = ancestry
        aligned_z = direction.mul(z)
        mask = (
            ancestry.ne(0)
            & agreement
            & consensus_direction.eq(ancestry)
            & minimum_pressure.ge(float(params["pressure_min"]))
            & aligned_z.between(
                float(params["residual_floor"]),
                float(params["residual_ceiling"]),
            )
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
        )
    elif mechanic == "TRANS_MACRO_RESIDUAL_CATCHUP":
        direction = consensus_direction
        mask = (
            agreement
            & minimum_pressure.ge(float(params["pressure_min"]))
            & direction.mul(z).le(-float(params["lag_z_min"]))
            & _ancestry_relation(direction, ancestry, str(params["ancestry_relation"]))
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
        )
    elif mechanic == "TRANS_RESIDUAL_BREAKOUT":
        direction = np.sign(z).fillna(0).astype(int)
        relation = str(params["macro_relation"])
        macro_ready = pd.Series(True, index=frame.index)
        if relation == "AGREE":
            macro_ready = consensus_direction.eq(direction)
        elif relation != "ANY":
            raise KeyError(relation)
        mask = (
            z.abs().ge(float(params["z_min"]))
            & maximum_pressure.ge(float(params["pressure_min"]))
            & macro_ready
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
        )
    elif mechanic == "TRANS_SINGLE_FACTOR_RESOLUTION":
        dxy_dominant = dxy.abs().gt(bond.abs())
        dominant = pd.Series(
            np.where(dxy_dominant, dxy, bond), index=frame.index
        )
        direction = np.sign(dominant).fillna(0).astype(int)
        mask = (
            maximum_pressure.ge(float(params["dominant_pressure_min"]))
            & minimum_pressure.le(float(params["other_pressure_max"]))
            & _ancestry_relation(direction, ancestry, str(params["ancestry_relation"]))
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
        )
    elif mechanic == "TRANS_ANCESTRY_OVERSHOOT_REVERSAL":
        direction = -ancestry
        mask = (
            ancestry.ne(0)
            & ancestry.mul(z).ge(float(params["z_min"]))
            & minimum_pressure.le(float(params["macro_pressure_max"]))
            & frame["transition_age_m15"].between(
                int(params["transition_age_min"]), int(params["transition_age_max"])
            )
        )
    else:
        raise KeyError(mechanic)

    regime_name = "CHOP" if owner == "CHOP" else "TRANSITION_UNKNOWN"
    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & frame["regime"].eq(regime_name)
        & direction.ne(0)
        & _confirmation(frame, direction, params)
        & _hour_mask(frame, str(params["hour_window"]))
        & np.isfinite(frame["atr14"])
        & frame["atr14"].gt(0.0)
        & np.isfinite(z)
        & np.isfinite(dxy)
        & np.isfinite(bond)
        & np.isfinite(gold)
    )
    return valid.astype(bool), direction.astype(int)


def _coverage(
    frame: pd.DataFrame, mask: pd.Series, windows: Mapping[str, Any]
) -> tuple[int, int]:
    timestamp = frame["timestamp_utc"]
    total = int(mask.sum())
    era_counts = [
        int(
            (
                mask
                & timestamp.ge(pd.Timestamp(raw_start))
                & timestamp.lt(pd.Timestamp(raw_end))
            ).sum()
        )
        for raw_start, raw_end in windows.values()
    ]
    return total, min(era_counts) if era_counts else 0


def _variant_hash(owner: str, mechanic: str, params: Mapping[str, Any]) -> str:
    canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{owner}|{mechanic}|{canonical}".encode("ascii")).hexdigest()


def generate_manifest(frame: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    selection = config["selection"]
    attempt = int(selection["attempt_first"])
    rows: list[dict[str, Any]] = []
    for owner, mechanics in MECHANICS.items():
        owner_start = len(rows)
        for mechanic in mechanics:
            ranked = sorted(
                parameter_space(owner, mechanic, config),
                key=lambda params: _variant_hash(owner, mechanic, params),
            )
            admitted = 0
            coverage_cache: dict[str, tuple[int, int]] = {}
            for params in ranked:
                signal_params = dict(params)
                signal_params.pop("geometry_id")
                signal_key = json.dumps(signal_params, sort_keys=True, separators=(",", ":"))
                coverage = coverage_cache.get(signal_key)
                if coverage is None:
                    mask, _ = signal_mask_direction(frame, mechanic, params)
                    coverage = _coverage(frame, mask, config["windows"])
                    coverage_cache[signal_key] = coverage
                total, minimum_era = coverage
                if total < int(selection["minimum_raw_signals_total"]):
                    continue
                if minimum_era < int(selection["minimum_raw_signals_each_era"]):
                    continue
                variant_hash = _variant_hash(owner, mechanic, params)
                rows.append(
                    {
                        "attempt_no": attempt,
                        "variant_id": variant_hash[:16],
                        "regime_owner": owner,
                        "mechanic": mechanic,
                        "geometry_id": str(params["geometry_id"]),
                        "raw_signal_count": total,
                        "minimum_era_raw_signal_count": minimum_era,
                        "parameters_json": json.dumps(params, sort_keys=True, separators=(",", ":")),
                    }
                )
                attempt += 1
                admitted += 1
                if admitted == int(selection["attempts_per_mechanic"]):
                    break
            if admitted != int(selection["attempts_per_mechanic"]):
                raise ValueError(f"Only {admitted} coverage-eligible definitions for {mechanic}")
        if len(rows) - owner_start != int(selection["attempts_per_owner"]):
            raise ValueError(f"Owner count mismatch for {owner}")
    manifest = pd.DataFrame(rows)
    if len(manifest) != int(selection["total_attempts"]):
        raise ValueError("Manifest attempt count differs from contract")
    if int(manifest["attempt_no"].iat[-1]) != int(selection["attempt_last"]):
        raise ValueError("Manifest attempt boundary differs from contract")
    if manifest["variant_id"].duplicated().any():
        raise ValueError("Duplicate manifest variant IDs")
    return manifest


def simulate_variant(
    frame: pd.DataFrame,
    arrays: Mapping[str, np.ndarray],
    manifest_row: Any,
    config: Mapping[str, Any],
    outcome_cache: dict[tuple[int, int, str], dict[str, Any] | None],
    outcome_function: Callable[..., dict[str, Any] | None],
) -> pd.DataFrame:
    params = json.loads(str(manifest_row.parameters_json))
    mask, direction = signal_mask_direction(frame, str(manifest_row.mechanic), params)
    geometry_id = str(manifest_row.geometry_id)
    geometry = config["geometries"][str(manifest_row.regime_owner)][geometry_id]
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for decision_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        signal_index = int(frame["execution_index"].iat[int(decision_index)])
        sign = int(direction.iat[int(decision_index)])
        key = (signal_index, sign, geometry_id)
        if key not in outcome_cache:
            outcome_cache[key] = outcome_function(
                arrays, signal_index, sign, geometry, config["execution"]
            )
        outcome = outcome_cache[key]
        if outcome is None:
            continue
        entry_time = pd.Timestamp(outcome["entry_time"])
        if entry_time < position_until:
            continue
        day = entry_time.date()
        maximum = int(config["execution"]["maximum_trades_per_variant_utc_day"])
        if daily_count.get(day, 0) >= maximum:
            continue
        selected.append(
            {
                "attempt_no": int(manifest_row.attempt_no),
                "variant_id": str(manifest_row.variant_id),
                "regime_owner": str(manifest_row.regime_owner),
                "mechanic": str(manifest_row.mechanic),
                "geometry_id": geometry_id,
                **outcome,
            }
        )
        position_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(selected)
