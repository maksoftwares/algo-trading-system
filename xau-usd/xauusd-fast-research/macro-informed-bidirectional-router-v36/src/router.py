from __future__ import annotations

from itertools import product
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


def boundaries(
    start: pd.Timestamp, end: pd.Timestamp, months: int
) -> list[pd.Timestamp]:
    values = list(
        pd.date_range(start=start, end=end, freq=f"{months}MS", inclusive="left")
    )
    if not values or values[0] != start:
        values.insert(0, start)
    if values[-1] != end:
        values.append(end)
    return values


def recency_weights(
    exit_times: pd.Series, fit_time: pd.Timestamp, half_life_months: int
) -> np.ndarray:
    age_days = (fit_time - exit_times).dt.total_seconds().to_numpy() / 86_400.0
    return np.maximum(0.5 ** (age_days / (half_life_months * 30.4375)), 0.01)


def best_actions(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.sort_values(
            ["event_id", "model_score", "action_id"],
            ascending=[True, False, True],
            kind="mergesort",
        )
        .drop_duplicates("event_id", keep="first")
        .sort_values(["signal_time", "event_id"], kind="mergesort")
    )


def score_actions(
    actions: pd.DataFrame,
    features: list[str],
    config: dict[str, Any],
) -> pd.DataFrame:
    walk = config["walkforward"]
    periods = boundaries(
        pd.Timestamp(walk["score_start"]),
        pd.Timestamp(walk["score_end"]),
        int(walk["refit_months"]),
    )
    outputs: list[pd.DataFrame] = []
    diagnostics: list[dict[str, Any]] = []
    for period_start, period_end in zip(periods[:-1], periods[1:]):
        calibration_start = period_start - pd.DateOffset(
            months=int(walk["calibration_months"])
        )
        fit_start = period_start - pd.DateOffset(months=int(walk["lookback_months"]))
        fit = actions.loc[
            (actions["signal_time"] >= fit_start)
            & (actions["signal_time"] < calibration_start)
            & (actions["exit_time"] < calibration_start)
        ]
        calibration = actions.loc[
            (actions["signal_time"] >= calibration_start)
            & (actions["signal_time"] < period_start)
            & (actions["exit_time"] < period_start)
        ]
        current = actions.loc[
            (actions["signal_time"] >= period_start)
            & (actions["signal_time"] < period_end)
        ]
        fit_rows = len(fit)
        calibration_events = calibration["event_id"].nunique()
        if fit_rows < int(walk["minimum_fit_rows"]):
            raise ValueError(f"Insufficient fit rows at {period_start}: {fit_rows}")
        if calibration_events < int(walk["minimum_calibration_events"]):
            raise ValueError(
                f"Insufficient calibration events at {period_start}: {calibration_events}"
            )
        params = config["model"]
        model = HistGradientBoostingRegressor(
            learning_rate=float(params["learning_rate"]),
            max_iter=int(params["max_iter"]),
            max_leaf_nodes=int(params["max_leaf_nodes"]),
            min_samples_leaf=int(params["min_samples_leaf"]),
            l2_regularization=float(params["l2_regularization"]),
            max_bins=int(params["max_bins"]),
            random_state=int(params["random_state"]),
        )
        target = fit["stress_usd"].clip(
            float(walk["target_clip_low_usd"]),
            float(walk["target_clip_high_usd"]),
        )
        weights = recency_weights(
            fit["exit_time"], calibration_start, int(walk["half_life_months"])
        )
        model.fit(fit[features], target, sample_weight=weights)
        keep = [
            "event_id",
            "action_id",
            "base_action_id",
            "signal_time",
            "entry_time",
            "exit_time",
            "signal_direction",
            "direction",
            "direction_flipped",
            "regime",
            "stress_usd",
            "stress_net_r",
        ]
        calibration_scored = calibration[keep].copy()
        calibration_scored["model_score"] = model.predict(calibration[features])
        calibration_best = best_actions(calibration_scored)
        current_scored = current[keep].copy()
        current_scored["model_score"] = model.predict(current[features])
        current_best = best_actions(current_scored)
        ordered = np.sort(calibration_best["model_score"].to_numpy(dtype=float))
        current_best["score_percentile"] = np.searchsorted(
            ordered,
            current_best["model_score"].to_numpy(dtype=float),
            side="right",
        ) / len(ordered)
        current_best["fit_time"] = period_start
        outputs.append(current_best)
        diagnostics.append(
            {
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "fit_start": fit_start.isoformat(),
                "fit_end_exclusive": calibration_start.isoformat(),
                "calibration_start": calibration_start.isoformat(),
                "calibration_end_exclusive": period_start.isoformat(),
                "maximum_fit_exit": fit["exit_time"].max().isoformat(),
                "maximum_calibration_exit": calibration["exit_time"].max().isoformat(),
                "fit_rows": fit_rows,
                "fit_events": int(fit["event_id"].nunique()),
                "calibration_events": int(calibration_events),
                "current_events": int(current["event_id"].nunique()),
            }
        )
    result = pd.concat(outputs, ignore_index=True).sort_values(
        ["signal_time", "event_id"], kind="mergesort"
    )
    if result["event_id"].duplicated().any():
        raise ValueError("Scored router output contains duplicate events")
    result = result.reset_index(drop=True)
    result.attrs["walkforward_diagnostics"] = diagnostics
    return result


def policy_definitions(config: dict[str, Any]) -> list[dict[str, Any]]:
    spec = config["policies"]
    policies = []
    for percentile, daily_cap, separation, maximum_active, risk_weight in product(
        spec["score_percentiles"],
        spec["daily_caps"],
        spec["entry_separation_minutes"],
        spec["maximum_active_expansion"],
        spec["expansion_risk_weights"],
    ):
        policies.append(
            {
                "policy_id": (
                    f"MACRO_Q{int(percentile * 100):02d}__D{daily_cap}__S{separation}"
                    f"__A{maximum_active}__W{str(risk_weight).replace('.', 'P')}"
                ),
                "score_percentile": float(percentile),
                "daily_cap": int(daily_cap),
                "entry_separation_minutes": int(separation),
                "maximum_active_expansion": int(maximum_active),
                "expansion_risk_weight": float(risk_weight),
            }
        )
    expected = int(spec["parameter_search_count"])
    if len(policies) != expected:
        raise ValueError(f"Expected {expected} policies, found {len(policies)}")
    return policies


def execute_policy(scored: pd.DataFrame, policy: dict[str, Any]) -> pd.DataFrame:
    eligible = scored.loc[
        scored["score_percentile"].ge(float(policy["score_percentile"]))
    ].sort_values(
        ["entry_time", "model_score", "event_id"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    active: list[pd.Timestamp] = []
    daily: dict[Any, int] = {}
    accepted: list[int] = []
    last_entry = pd.Timestamp.min.tz_localize("UTC")
    separation = pd.Timedelta(minutes=int(policy["entry_separation_minutes"]))
    for index, row in eligible.iterrows():
        active = [exit_time for exit_time in active if exit_time > row["entry_time"]]
        date = row["entry_time"].date()
        if len(active) >= int(policy["maximum_active_expansion"]):
            continue
        if daily.get(date, 0) >= int(policy["daily_cap"]):
            continue
        if row["entry_time"] < last_entry + separation:
            continue
        accepted.append(index)
        active.append(row["exit_time"])
        daily[date] = daily.get(date, 0) + 1
        last_entry = row["entry_time"]
    return eligible.loc[accepted].copy().reset_index(drop=True)
