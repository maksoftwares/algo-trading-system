from __future__ import annotations

import hashlib
from itertools import product
import json
from typing import Any, Callable, Iterable, Mapping

import numpy as np
import pandas as pd


MECHANICS = {
    "CHOP": (
        "CHOP_MACRO_CONSENSUS_CATCHUP",
        "CHOP_DXY_ISOLATED_CATCHUP",
        "CHOP_BOND_ISOLATED_CATCHUP",
        "CHOP_MACRO_CONSENSUS_EXHAUSTION_FADE",
        "CHOP_MACRO_DISAGREEMENT_GOLD_FADE",
    ),
    "TRANSITION": (
        "TRANS_MACRO_CONSENSUS_CATCHUP",
        "TRANS_DXY_ISOLATED_RESOLUTION",
        "TRANS_BOND_ISOLATED_RESOLUTION",
        "TRANS_ANCESTRY_MACRO_REACCELERATION",
        "TRANS_ANCESTRY_MACRO_REVERSAL",
    ),
}

HOUR_WINDOWS = ("ALL", "LONDON_NY", "NEW_YORK")
GOLD_HORIZONS = ("H1", "H4", "H12")
TRANSITION_SOURCES = ("ANY", "ANY_TREND", "COMPRESSION", "CHOP")


def _space(**values: Iterable[Any]) -> Iterable[dict[str, Any]]:
    names = tuple(values)
    for combination in product(*(tuple(values[name]) for name in names)):
        yield dict(zip(names, combination, strict=True))


def macro_keys(config: Mapping[str, Any]) -> tuple[str, ...]:
    features = config["macro_features"]
    return tuple(
        f"{horizon}_{scale}"
        for horizon in features["horizons"]
        for scale in features["scales"]
    )


def parameter_space(
    owner: str, mechanic: str, config: Mapping[str, Any]
) -> Iterable[dict[str, Any]]:
    keys = macro_keys(config)
    geometries = tuple(config["geometries"][owner])
    shared = {
        "macro_key": keys,
        "gold_horizon": GOLD_HORIZONS,
        "hour_window": HOUR_WINDOWS,
        "geometry_id": geometries,
    }
    if mechanic == "CHOP_MACRO_CONSENSUS_CATCHUP":
        return _space(
            pressure_min=(0.50, 0.75, 1.00, 1.25),
            maximum_alignment_atr=(-0.25, 0.00, 0.25, 0.50),
            require_confirmation=(False, True),
            body_min=(0.00, 0.20, 0.40),
            **shared,
        )
    if mechanic in (
        "CHOP_DXY_ISOLATED_CATCHUP",
        "CHOP_BOND_ISOLATED_CATCHUP",
    ):
        return _space(
            pressure_min=(0.50, 0.75, 1.00, 1.25),
            other_pressure_max=(0.25, 0.50, 0.75, 1.00),
            maximum_alignment_atr=(-0.25, 0.00, 0.25, 0.50),
            require_confirmation=(False, True),
            body_min=(0.00, 0.20, 0.40),
            **shared,
        )
    if mechanic == "CHOP_MACRO_CONSENSUS_EXHAUSTION_FADE":
        return _space(
            pressure_min=(0.50, 0.75, 1.00, 1.25),
            minimum_extension_atr=(0.50, 0.75, 1.25, 1.75),
            require_confirmation=(True,),
            body_min=(0.00, 0.20, 0.40),
            **shared,
        )
    if mechanic == "CHOP_MACRO_DISAGREEMENT_GOLD_FADE":
        return _space(
            pressure_min=(0.50, 0.75, 1.00),
            balance_ratio_max=(1.25, 1.50, 2.00),
            minimum_extension_atr=(0.50, 0.75, 1.25),
            require_confirmation=(False, True),
            body_min=(0.00, 0.20, 0.40),
            **shared,
        )
    if mechanic == "TRANS_MACRO_CONSENSUS_CATCHUP":
        return _space(
            pressure_min=(0.50, 0.75, 1.00, 1.25),
            maximum_alignment_atr=(-0.25, 0.00, 0.25, 0.50),
            transition_age_max=(16, 48, 96, 192),
            source=TRANSITION_SOURCES,
            require_confirmation=(False, True),
            body_min=(0.00, 0.20, 0.40),
            **shared,
        )
    if mechanic in (
        "TRANS_DXY_ISOLATED_RESOLUTION",
        "TRANS_BOND_ISOLATED_RESOLUTION",
    ):
        return _space(
            pressure_min=(0.50, 0.75, 1.00, 1.25),
            other_pressure_max=(0.25, 0.50, 0.75, 1.00),
            maximum_alignment_atr=(-0.25, 0.00, 0.25, 0.50),
            transition_age_max=(16, 48, 96, 192),
            source=TRANSITION_SOURCES,
            require_confirmation=(False, True),
            body_min=(0.00, 0.20, 0.40),
            **shared,
        )
    if mechanic == "TRANS_ANCESTRY_MACRO_REACCELERATION":
        return _space(
            pressure_min=(0.50, 0.75, 1.00, 1.25),
            maximum_alignment_atr=(-0.25, 0.00, 0.25, 0.50),
            transition_age_max=(16, 48, 96, 192),
            require_confirmation=(False, True),
            body_min=(0.00, 0.20, 0.40),
            **shared,
        )
    if mechanic == "TRANS_ANCESTRY_MACRO_REVERSAL":
        return _space(
            pressure_min=(0.50, 0.75, 1.00, 1.25),
            maximum_alignment_atr=(-0.25, 0.00, 0.25, 0.50),
            transition_age_min=(4, 16, 32),
            transition_age_max=(48, 96, 192),
            require_confirmation=(False, True),
            body_min=(0.00, 0.20, 0.40),
            **shared,
        )
    raise KeyError(f"Unknown mechanic for {owner}: {mechanic}")


def _contiguous_log_return(
    close: pd.Series, timestamp: pd.Series, bars: int
) -> pd.Series:
    elapsed = timestamp - timestamp.shift(bars)
    expected = pd.Timedelta(minutes=15 * bars)
    values = np.log(close / close.shift(bars))
    return values.where(elapsed.eq(expected))


def build_macro_features(
    macro_m15: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    frame = macro_m15.copy().sort_values("timestamp_utc", kind="mergesort")
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate macro decision timestamps")
    settings = config["macro_features"]
    minimum_fraction = float(settings["minimum_scale_fraction"])
    output = frame[["timestamp_utc"]].copy()
    for horizon, raw_bars in settings["horizons"].items():
        bars = int(raw_bars)
        for symbol, pressure_sign in (
            ("dollaridxusd", -1.0),
            ("ustbondtrusd", 1.0),
        ):
            returns = _contiguous_log_return(
                frame[f"{symbol}_close"], frame["timestamp_utc"], bars
            )
            for scale, raw_scale_bars in settings["scales"].items():
                scale_bars = int(raw_scale_bars)
                minimum = max(2, int(scale_bars * minimum_fraction))
                prior_scale = (
                    returns.shift(1)
                    .rolling(scale_bars, min_periods=minimum)
                    .std(ddof=0)
                )
                prefix = "dxy" if symbol == "dollaridxusd" else "bond"
                output[f"{prefix}_pressure_{horizon}_{scale}"] = (
                    pressure_sign * returns / prior_scale.replace(0.0, np.nan)
                )
    return output


def enrich_frame(
    gold: pd.DataFrame, macro_m15: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    frame = gold.copy().sort_values("timestamp_utc", kind="mergesort")
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate gold decision timestamps")
    frame["execution_index"] = np.arange(len(frame), dtype=np.int64)
    atr = frame["atr14"].replace(0.0, np.nan)
    for horizon, raw_bars in config["macro_features"]["gold_return_horizons"].items():
        bars = int(raw_bars)
        elapsed = frame["timestamp_utc"] - frame["timestamp_utc"].shift(bars)
        contiguous = elapsed.eq(pd.Timedelta(minutes=15 * bars))
        frame[f"gold_return_{horizon}_atr"] = (
            (frame["mid_close"] - frame["mid_close"].shift(bars)) / atr
        ).where(contiguous)
    macro = build_macro_features(macro_m15, config)
    result = frame.merge(macro, on="timestamp_utc", how="inner", validate="one_to_one")
    first = min(pd.Timestamp(pair[0]) for pair in config["windows"].values())
    final = max(pd.Timestamp(pair[1]) for pair in config["windows"].values())
    result = result.loc[
        result["timestamp_utc"].ge(first) & result["timestamp_utc"].lt(final)
    ].copy()
    result["hour_utc"] = result["timestamp_utc"].dt.hour
    return result.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)


def _hour_mask(frame: pd.DataFrame, window: str) -> pd.Series:
    if window == "ALL":
        return pd.Series(True, index=frame.index)
    if window == "LONDON_NY":
        return frame["hour_utc"].between(6, 18)
    if window == "NEW_YORK":
        return frame["hour_utc"].between(12, 18)
    raise KeyError(window)


def _source_mask(frame: pd.DataFrame, source: str) -> pd.Series:
    ancestry = frame["last_resolved_regime"]
    if source == "ANY":
        return pd.Series(True, index=frame.index)
    if source == "ANY_TREND":
        return ancestry.isin(("TREND_UP", "TREND_DOWN"))
    if source in ("COMPRESSION", "CHOP"):
        return ancestry.eq(source)
    raise KeyError(source)


def _confirmation(
    frame: pd.DataFrame, direction: pd.Series, params: Mapping[str, Any]
) -> pd.Series:
    result = frame["body"].ge(float(params["body_min"]))
    if bool(params["require_confirmation"]):
        result &= direction.mul(frame["candle_direction"]).gt(0)
    return result


def _pressures(
    frame: pd.DataFrame, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series, pd.Series]:
    key = str(params["macro_key"])
    dxy = frame[f"dxy_pressure_{key}"]
    bond = frame[f"bond_pressure_{key}"]
    gold = frame[f"gold_return_{params['gold_horizon']}_atr"]
    return dxy, bond, gold


def _consensus_direction(dxy: pd.Series, bond: pd.Series) -> pd.Series:
    same = np.sign(dxy) == np.sign(bond)
    return pd.Series(np.where(same, np.sign(dxy), 0).astype(int), index=dxy.index)


def signal_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series]:
    dxy, bond, gold = _pressures(frame, params)
    pressure_min = float(params["pressure_min"])
    owner = "CHOP" if mechanic.startswith("CHOP_") else "TRANSITION"
    regime_name = "CHOP" if owner == "CHOP" else "TRANSITION_UNKNOWN"
    direction = pd.Series(0, index=frame.index, dtype=int)

    if "CONSENSUS" in mechanic or "ANCESTRY" in mechanic:
        pressure_direction = _consensus_direction(dxy, bond)
        pressure_ready = (
            pressure_direction.ne(0)
            & dxy.abs().ge(pressure_min)
            & bond.abs().ge(pressure_min)
        )
    else:
        pressure_direction = pd.Series(0, index=frame.index, dtype=int)
        pressure_ready = pd.Series(False, index=frame.index)

    if mechanic in (
        "CHOP_MACRO_CONSENSUS_CATCHUP",
        "TRANS_MACRO_CONSENSUS_CATCHUP",
    ):
        direction = pressure_direction
        aligned = direction.mul(gold)
        mask = (
            pressure_ready
            & aligned.between(-1.50, float(params["maximum_alignment_atr"]))
            & _confirmation(frame, direction, params)
        )
    elif mechanic in (
        "CHOP_DXY_ISOLATED_CATCHUP",
        "TRANS_DXY_ISOLATED_RESOLUTION",
    ):
        direction = pd.Series(np.sign(dxy).fillna(0).astype(int), index=frame.index)
        aligned = direction.mul(gold)
        mask = (
            dxy.abs().ge(pressure_min)
            & bond.abs().le(float(params["other_pressure_max"]))
            & aligned.between(-1.50, float(params["maximum_alignment_atr"]))
            & _confirmation(frame, direction, params)
        )
    elif mechanic in (
        "CHOP_BOND_ISOLATED_CATCHUP",
        "TRANS_BOND_ISOLATED_RESOLUTION",
    ):
        direction = pd.Series(np.sign(bond).fillna(0).astype(int), index=frame.index)
        aligned = direction.mul(gold)
        mask = (
            bond.abs().ge(pressure_min)
            & dxy.abs().le(float(params["other_pressure_max"]))
            & aligned.between(-1.50, float(params["maximum_alignment_atr"]))
            & _confirmation(frame, direction, params)
        )
    elif mechanic == "CHOP_MACRO_CONSENSUS_EXHAUSTION_FADE":
        direction = -pressure_direction
        extension = pressure_direction.mul(gold)
        mask = (
            pressure_ready
            & extension.ge(float(params["minimum_extension_atr"]))
            & _confirmation(frame, direction, params)
        )
    elif mechanic == "CHOP_MACRO_DISAGREEMENT_GOLD_FADE":
        disagreement = np.sign(dxy).ne(np.sign(bond))
        smaller = pd.concat((dxy.abs(), bond.abs()), axis=1).min(axis=1)
        larger = pd.concat((dxy.abs(), bond.abs()), axis=1).max(axis=1)
        ratio = larger / smaller.replace(0.0, np.nan)
        gold_direction = pd.Series(
            np.sign(gold).fillna(0).astype(int), index=frame.index
        )
        direction = -gold_direction
        mask = (
            disagreement
            & smaller.ge(pressure_min)
            & ratio.le(float(params["balance_ratio_max"]))
            & gold.abs().ge(float(params["minimum_extension_atr"]))
            & _confirmation(frame, direction, params)
        )
    elif mechanic == "TRANS_ANCESTRY_MACRO_REACCELERATION":
        ancestry = frame["ancestry_direction"].astype(int)
        direction = ancestry
        aligned = direction.mul(gold)
        mask = (
            ancestry.ne(0)
            & pressure_ready
            & pressure_direction.eq(ancestry)
            & aligned.between(-1.50, float(params["maximum_alignment_atr"]))
            & _confirmation(frame, direction, params)
        )
    elif mechanic == "TRANS_ANCESTRY_MACRO_REVERSAL":
        ancestry = frame["ancestry_direction"].astype(int)
        direction = pressure_direction
        aligned = direction.mul(gold)
        mask = (
            ancestry.ne(0)
            & pressure_ready
            & pressure_direction.eq(-ancestry)
            & aligned.between(-1.50, float(params["maximum_alignment_atr"]))
            & frame["transition_age_m15"].ge(int(params["transition_age_min"]))
            & _confirmation(frame, direction, params)
        )
    else:
        raise KeyError(mechanic)

    if owner == "TRANSITION":
        mask &= frame["transition_age_m15"].le(int(params["transition_age_max"]))
        if "source" in params:
            mask &= _source_mask(frame, str(params["source"]))
    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & frame["regime"].eq(regime_name)
        & direction.ne(0)
        & _hour_mask(frame, str(params["hour_window"]))
        & np.isfinite(frame["atr14"])
        & frame["atr14"].gt(0.0)
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
                signal_key = json.dumps(
                    signal_params, sort_keys=True, separators=(",", ":")
                )
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
                canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
                rows.append(
                    {
                        "attempt_no": attempt,
                        "variant_id": variant_hash[:16],
                        "regime_owner": owner,
                        "mechanic": mechanic,
                        "geometry_id": str(params["geometry_id"]),
                        "raw_signal_count": total,
                        "minimum_era_raw_signal_count": minimum_era,
                        "parameters_json": canonical,
                    }
                )
                attempt += 1
                admitted += 1
                if admitted == int(selection["attempts_per_mechanic"]):
                    break
            if admitted != int(selection["attempts_per_mechanic"]):
                raise ValueError(
                    f"Only {admitted} coverage-eligible definitions for {mechanic}"
                )
        owner_count = len(rows) - owner_start
        if owner_count != int(selection["attempts_per_owner"]):
            raise ValueError(f"Owner count mismatch for {owner}: {owner_count}")
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
    for raw_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        decision_index = int(raw_index)
        signal_index = int(frame["execution_index"].iat[decision_index])
        sign = int(direction.iat[decision_index])
        key = (signal_index, sign, geometry_id)
        if key not in outcome_cache:
            outcome_cache[key] = outcome_function(
                arrays,
                signal_index,
                sign,
                geometry,
                config["execution"],
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
                "regime_owner": str(manifest_row.regime_owner),
                "mechanic": str(manifest_row.mechanic),
                "geometry_id": geometry_id,
                **outcome,
            }
        )
        position_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(selected)
