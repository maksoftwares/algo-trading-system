from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


V21_MECHANICS = {
    "CHOP_M15_AR1_STATIONARITY_CONTINUATION": "CHOP_M15_AR1_MEAN_REVERSION",
    "CHOP_M15_VARIANCE_RATIO_CONTINUATION": "CHOP_M15_VARIANCE_RATIO_REVERSION",
    "CHOP_M15_HURST_CONTINUATION": "CHOP_M15_HURST_REVERSION",
    "CHOP_M15_RETURN_AUTOCORRELATION_CONTINUATION": "CHOP_M15_RETURN_AUTOCORRELATION_FADE",
    "CHOP_M15_MULTISCALE_STATIONARITY_CONTINUATION": "CHOP_M15_MULTISCALE_STATIONARITY_REVERSION",
}
SOURCE_MECHANICS = {
    "CHOP_M15_AR1_STATIONARITY_CONTINUATION": "AR1_MEAN_REVERSION",
    "CHOP_M15_VARIANCE_RATIO_CONTINUATION": "VARIANCE_RATIO_REVERSION",
    "CHOP_M15_HURST_CONTINUATION": "HURST_REVERSION",
    "CHOP_M15_RETURN_AUTOCORRELATION_CONTINUATION": "RETURN_AUTOCORRELATION_FADE",
    "CHOP_M15_MULTISCALE_STATIONARITY_CONTINUATION": "MULTISCALE_STATIONARITY_REVERSION",
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
                f"chop-m15-stationarity-v21|{mechanic}|{nonce}|{name}".encode(
                    "ascii"
                )
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
    source_mechanic = V21_MECHANICS[mechanic]
    if source == "AR1_MEAN_REVERSION":
        options = dict(
            stationarity_window=(192, 384, 768),
            z_abs_min=(0.75, 1.25, 1.75),
            phi_min=(0.30, 0.60, 0.80),
            phi_max=(0.90, 0.97, 0.995),
            half_life_max=(12.0, 36.0, 96.0),
            mean_slope_abs_max=(0.15, 0.35, 0.70),
        )
    elif source == "VARIANCE_RATIO_REVERSION":
        options = dict(
            stationarity_window=(192, 384, 768),
            variance_horizon=(4, 16),
            variance_ratio_max=(0.70, 0.90, 1.10),
            z_abs_min=(0.75, 1.25, 1.75),
            mean_slope_abs_max=(0.15, 0.35, 0.70),
            return_acf_max=(-0.10, 0.0, 0.10),
        )
    elif source == "HURST_REVERSION":
        options = dict(
            stationarity_window=(192, 384, 768),
            hurst_max=(0.35, 0.50, 0.65),
            z_abs_min=(0.75, 1.25, 1.75),
            zero_crossing_min=(0.02, 0.05, 0.10),
            mean_slope_abs_max=(0.15, 0.35, 0.70),
            return_acf_max=(-0.10, 0.0, 0.10),
        )
    elif source == "RETURN_AUTOCORRELATION_FADE":
        options = dict(
            stationarity_window=(192, 384, 768),
            autocorrelation_lag=(1, 16),
            return_acf_max=(-0.20, -0.05, 0.10),
            impulse_h1_atr_min=(0.10, 0.30, 0.60),
            z_alignment_min=(0.0, 0.50, 1.0),
            mean_slope_abs_max=(0.15, 0.35, 0.70),
        )
    elif source == "MULTISCALE_STATIONARITY_REVERSION":
        options = dict(
            window_pair=("192_384", "192_768", "384_768"),
            fast_z_abs_min=(0.50, 1.00, 1.50),
            slow_z_abs_min=(0.25, 0.75, 1.25),
            variance_ratio_max=(0.70, 0.90, 1.10),
            slow_slope_abs_max=(0.15, 0.35, 0.70),
            zero_crossing_min=(0.02, 0.05, 0.10),
        )
    else:
        raise KeyError(mechanic)
    return _deterministic_design(
        source_mechanic,
        candidate_count,
        **options,
        m15_state_age_m5_max=(0, 1, 2),
        m5_confirmation_window=(3, 12),
        m5_alignment_min=(-0.03, 0.0, 0.03),
        flow_alignment_min=(-0.03, 0.0, 0.01),
        session=SESSIONS,
        geometry_id=GEOMETRIES,
    )


def _rolling_ar_phi(series: pd.Series, window: int) -> pd.Series:
    current = series.astype(float)
    lagged = current.shift(1)
    minimum = window
    current_mean = current.rolling(window, min_periods=minimum).mean()
    lagged_mean = lagged.rolling(window, min_periods=minimum).mean()
    covariance = (current * lagged).rolling(
        window, min_periods=minimum
    ).mean() - current_mean * lagged_mean
    variance = lagged.pow(2).rolling(
        window, min_periods=minimum
    ).mean() - lagged_mean.pow(2)
    return covariance / variance.replace(0.0, np.nan)


def _half_life(phi: pd.Series) -> pd.Series:
    valid = phi.where(phi.gt(0.0) & phi.lt(1.0))
    return -np.log(2.0) / np.log(valid)


def add_m15_stationarity_features(
    m15: pd.DataFrame,
    config: Mapping[str, Any],
    regime_module: Any,
) -> pd.DataFrame:
    result = m15.sort_values("timestamp_utc", kind="mergesort").reset_index(
        drop=True
    ).copy()
    close = result["mid_close"].astype(float)
    result["atr_state"] = regime_module.atr(
        result, int(config["features"]["state_atr_period"])
    )
    atr = result["atr_state"].replace(0.0, np.nan)
    returns = close.diff()
    result["return_state"] = returns
    for window in (192, 384, 768):
        prior = close.shift(1)
        mean = prior.rolling(window, min_periods=window).mean()
        standard = prior.rolling(window, min_periods=window).std(ddof=0)
        deviation = close - mean
        result[f"z_{window}"] = deviation / standard.replace(0.0, np.nan)
        result[f"mean_slope_atr_{window}"] = (mean - mean.shift(6)) / atr
        phi = _rolling_ar_phi(close, window)
        result[f"phi_{window}"] = phi
        result[f"half_life_{window}"] = _half_life(phi)
        for lag in (1, 16):
            result[f"return_acf_{lag}_{window}"] = returns.rolling(
                window, min_periods=window
            ).corr(returns.shift(lag))
        one_variance = returns.rolling(
            window, min_periods=window
        ).var(ddof=0)
        for horizon in (4, 16):
            horizon_variance = close.diff(horizon).rolling(
                window, min_periods=window
            ).var(ddof=0)
            result[f"variance_ratio_{horizon}_{window}"] = horizon_variance / (
                horizon * one_variance.replace(0.0, np.nan)
            )
        variance_4 = close.diff(4).rolling(window, min_periods=window).var(ddof=0)
        variance_16 = close.diff(16).rolling(window, min_periods=window).var(ddof=0)
        ratio = variance_16 / variance_4.replace(0.0, np.nan)
        result[f"hurst_{window}"] = 0.5 * np.log(ratio) / np.log(4.0)
        sign = np.sign(deviation).replace(0.0, np.nan)
        crossings = sign.mul(sign.shift(1)).lt(0.0).astype(float)
        result[f"zero_crossing_{window}"] = crossings.rolling(
            window, min_periods=window
        ).mean()
    for span in (96, 192, 384):
        level = close.ewm(span=span, adjust=False, min_periods=span).mean().shift(1)
        residual = close - level
        residual_standard = residual.shift(1).rolling(
            span * 2, min_periods=span
        ).std(ddof=0)
        result[f"adaptive_residual_z_{span}"] = residual / residual_standard.replace(
            0.0, np.nan
        )
        residual_phi = _rolling_ar_phi(residual, span * 2)
        result[f"adaptive_residual_phi_{span}"] = residual_phi
        result[f"adaptive_residual_half_life_{span}"] = _half_life(residual_phi)
        result[f"adaptive_level_slope_atr_{span}"] = (
            level - level.shift(6)
        ) / atr
        residual_sign = np.sign(residual).replace(0.0, np.nan)
        residual_crossing = residual_sign.mul(residual_sign.shift(1)).lt(0.0)
        result[f"adaptive_zero_crossing_{span}"] = residual_crossing.astype(
            float
        ).rolling(span * 2, min_periods=span).mean()
    return result


def prepare_frame(
    m5: pd.DataFrame,
    m15: pd.DataFrame,
    h1: pd.DataFrame,
    h4: pd.DataFrame,
    config: Mapping[str, Any],
    micro_module: Any,
    regime_module: Any,
) -> pd.DataFrame:
    frame = micro_module.prepare_features(m5, config)
    classified = regime_module.classify_h4(h4, config["regime"])
    attached = regime_module.attach_regime(frame, classified)
    m15_state = add_m15_stationarity_features(m15, config, regime_module)
    m15_state = m15_state.drop(
        columns=[
            column
            for column in m15_state.columns
            if column not in {"timestamp_utc", "atr_state", "return_state"}
            and not column.startswith(
                (
                    "z_",
                    "mean_slope_atr_",
                    "phi_",
                    "half_life_",
                    "return_acf_",
                    "variance_ratio_",
                    "hurst_",
                    "zero_crossing_",
                    "adaptive_",
                )
            )
        ]
    ).rename(columns={"timestamp_utc": "m15_state_time"})
    attached = pd.merge_asof(
        attached.sort_values("timestamp_utc"),
        m15_state.sort_values("m15_state_time"),
        left_on="timestamp_utc",
        right_on="m15_state_time",
        direction="backward",
        allow_exact_matches=True,
    ).sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    attached["m15_state_age_m5"] = (
        (attached["timestamp_utc"] - attached["m15_state_time"])
        .dt.total_seconds()
        .div(300.0)
        .round()
    )
    h1_risk = h1[["timestamp_utc"]].copy()
    h1_risk["atr_h1"] = regime_module.atr(
        h1, int(config["features"]["h1_atr_period"])
    )
    attached = pd.merge_asof(
        attached.sort_values("timestamp_utc"),
        h1_risk.sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
    ).sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
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


def signal_mask_direction(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series]:
    source = SOURCE_MECHANICS[mechanic]
    risk_atr = frame["risk_atr"].replace(0.0, np.nan)
    session = _session_mask(frame, str(params["session"]))
    m5_move = frame[
        f"return_{int(params['m5_confirmation_window'])}"
    ].div(risk_atr)
    imbalance = frame["tick_imbalance_15m"]
    if source == "AR1_MEAN_REVERSION":
        window = int(params["stationarity_window"])
        z = frame[f"z_{window}"]
        direction = pd.Series(
            -np.sign(z.fillna(0.0)).astype(int), index=frame.index
        )
        phi = frame[f"phi_{window}"]
        mask = (
            z.abs().ge(float(params["z_abs_min"]))
            & phi.ge(float(params["phi_min"]))
            & phi.le(float(params["phi_max"]))
            & frame[f"half_life_{window}"].le(float(params["half_life_max"]))
            & frame[f"mean_slope_atr_{window}"].abs().le(
                float(params["mean_slope_abs_max"])
            )
        )
    elif source == "VARIANCE_RATIO_REVERSION":
        window = int(params["stationarity_window"])
        horizon = int(params["variance_horizon"])
        z = frame[f"z_{window}"]
        direction = pd.Series(
            -np.sign(z.fillna(0.0)).astype(int), index=frame.index
        )
        mask = (
            z.abs().ge(float(params["z_abs_min"]))
            & frame[f"variance_ratio_{horizon}_{window}"].le(
                float(params["variance_ratio_max"])
            )
            & frame[f"return_acf_1_{window}"].le(
                float(params["return_acf_max"])
            )
            & frame[f"mean_slope_atr_{window}"].abs().le(
                float(params["mean_slope_abs_max"])
            )
        )
    elif source == "HURST_REVERSION":
        window = int(params["stationarity_window"])
        z = frame[f"z_{window}"]
        direction = pd.Series(
            -np.sign(z.fillna(0.0)).astype(int), index=frame.index
        )
        mask = (
            z.abs().ge(float(params["z_abs_min"]))
            & frame[f"hurst_{window}"].le(float(params["hurst_max"]))
            & frame[f"zero_crossing_{window}"].ge(
                float(params["zero_crossing_min"])
            )
            & frame[f"return_acf_1_{window}"].le(
                float(params["return_acf_max"])
            )
            & frame[f"mean_slope_atr_{window}"].abs().le(
                float(params["mean_slope_abs_max"])
            )
        )
    elif source == "RETURN_AUTOCORRELATION_FADE":
        window = int(params["stationarity_window"])
        lag = int(params["autocorrelation_lag"])
        impulse = frame["return_state"].div(risk_atr)
        impulse_direction = pd.Series(
            np.sign(impulse.fillna(0.0)).astype(int), index=frame.index
        )
        direction = -impulse_direction
        z = frame[f"z_{window}"]
        mask = (
            frame[f"return_acf_{lag}_{window}"].le(
                float(params["return_acf_max"])
            )
            & impulse.abs().ge(float(params["impulse_h1_atr_min"]))
            & impulse_direction.mul(z).ge(float(params["z_alignment_min"]))
            & frame[f"mean_slope_atr_{window}"].abs().le(
                float(params["mean_slope_abs_max"])
            )
        )
    elif source == "MULTISCALE_STATIONARITY_REVERSION":
        fast_window, slow_window = (
            int(value) for value in str(params["window_pair"]).split("_")
        )
        fast_z = frame[f"z_{fast_window}"]
        slow_z = frame[f"z_{slow_window}"]
        direction = pd.Series(
            -np.sign(fast_z.fillna(0.0)).astype(int), index=frame.index
        )
        mask = (
            fast_z.abs().ge(float(params["fast_z_abs_min"]))
            & slow_z.abs().ge(float(params["slow_z_abs_min"]))
            & fast_z.mul(slow_z).gt(0.0)
            & frame[f"variance_ratio_4_{fast_window}"].le(
                float(params["variance_ratio_max"])
            )
            & frame[f"mean_slope_atr_{slow_window}"].abs().le(
                float(params["slow_slope_abs_max"])
            )
            & frame[f"zero_crossing_{fast_window}"].ge(
                float(params["zero_crossing_min"])
            )
        )
    else:
        raise KeyError(mechanic)

    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & frame["regime"].eq("CHOP")
        & frame["m15_state_age_m5"].between(
            0, int(params["m15_state_age_m5_max"]), inclusive="both"
        )
        & session
        & direction.mul(m5_move).ge(float(params["m5_alignment_min"]))
        & direction.mul(imbalance).ge(float(params["flow_alignment_min"]))
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
        source_mechanic = V21_MECHANICS[str(mechanic)]
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
