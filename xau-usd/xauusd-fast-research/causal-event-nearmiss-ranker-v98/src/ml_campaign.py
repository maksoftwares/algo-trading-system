from __future__ import annotations

import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent
MECHANICS = (
    "PRICE_EVENT_STATE",
    "MICRO_EVENT_STATE",
    "PRICE_MICRO_EVENT_STATE",
    "PRICE_TIME_EVENT_STATE",
    "ALL_EVENT_STATE",
)
EVENT_TYPES = (
    "RANGE_BREAK_CONTINUATION",
    "TREND_PULLBACK_RESUME",
    "COMPRESSION_EXPANSION",
    "IMPULSE_RETEST",
    "FAILED_RANGE_BREAK",
)
EXECUTION_PROFILES = (
    (0.6, 1.0, 1),
    (0.8, 1.25, 2),
    (1.0, 1.5, 3),
    (1.0, 2.0, 6),
    (1.2, 2.0, 12),
)
MODEL_SPECS = (
    (7, 0.04, 2.0, 50, 40),
    (15, 0.04, 5.0, 60, 40),
    (7, 0.07, 5.0, 50, 60),
    (15, 0.07, 10.0, 60, 60),
)
TARGET_FREQUENCIES = tuple(round(0.9 + 0.1 * index, 1) for index in range(10))

PRICE_SIGNED = (
    "body_atr",
    "return_1_atr",
    "return_4_atr",
    "return_16_atr",
    "channel_location_centered",
    "break_distance_atr",
)
MICRO_SIGNED = (
    "book_imbalance",
    "microprice_edge_atr",
    "tick_imbalance_5m",
    "tick_imbalance_15m",
    "close_location_centered",
)
PRICE_UNSIGNED = (
    "atr_ratio",
    "range_width_atr",
    "compression_ratio",
)
MICRO_UNSIGNED = (
    "quote_intensity_ratio",
    "price_efficiency",
    "spread_atr",
    "realized_variance_atr2",
)
TIME_UNSIGNED = ("hour_sin", "hour_cos", "weekday_sin", "weekday_cos")
EVENT_ONE_HOT = tuple(f"event_{name}" for name in EVENT_TYPES)
ALL_FEATURES = (
    *PRICE_SIGNED,
    *MICRO_SIGNED,
    *PRICE_UNSIGNED,
    *MICRO_UNSIGNED,
    *TIME_UNSIGNED,
    *EVENT_ONE_HOT,
)
OUTCOME_COLUMNS = (
    "signal_time",
    "entry_time",
    "exit_time",
    "direction",
    "entry_price",
    "exit_price",
    "stop",
    "target",
    "risk_price",
    "risk_usd",
    "stop_atr",
    "target_r",
    "entry_spread_r",
    "net_r",
    "stress_net_r",
    "holding_minutes",
    "exit_reason",
    "ambiguous_m5",
    "current_account_feasible",
    "exit_index",
)


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V89 = _load_module(
    "causal_event_nearmiss_ranker_v98_v89_metrics",
    RESEARCH_ROOT / "cboe-gvz-routed-intraday-v89" / "src" / "campaign.py",
)
BASE = V89.BASE
summarize = V89.summarize
benjamini_hochberg = V89.benjamini_hochberg
select_advancers = V89.select_advancers


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    if mechanic not in MECHANICS:
        raise KeyError(mechanic)
    rows: list[dict[str, Any]] = []
    for model_id, (stop, target, hold), frequency in product(
        range(len(MODEL_SPECS)), EXECUTION_PROFILES, TARGET_FREQUENCIES
    ):
        rows.append(
            {
                "feature_set": mechanic,
                "model_id": model_id,
                "stop_atr": stop,
                "target_r": target,
                "hold_hours": hold,
                "target_addon_trades_per_weekday": frequency,
            }
        )
    return rows


def _complete_m15(m5: pd.DataFrame) -> pd.DataFrame:
    required = {
        "bar_start_utc",
        "bar_end_utc",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
        "atr",
        "atr_ratio",
        "quote_intensity_ratio",
        "tick_book_imbalance_mean",
        "tick_microprice_edge_mean",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "price_efficiency_5m",
        "tick_spread_mean",
        "tick_realized_variance",
        "close_location",
    }
    missing = sorted(required.difference(m5.columns))
    if missing:
        raise ValueError(f"V98 M5 source is missing columns: {missing}")
    source = m5.sort_values("bar_start_utc", kind="mergesort").copy()
    source["m15_start"] = source["bar_start_utc"].dt.floor("15min")
    grouped = source.groupby("m15_start", sort=True, observed=True)
    frame = grouped.agg(
        bars=("bar_start_utc", "size"),
        first_start=("bar_start_utc", "first"),
        bar_end_utc=("bar_end_utc", "last"),
        mid_open=("mid_open", "first"),
        mid_high=("mid_high", "max"),
        mid_low=("mid_low", "min"),
        mid_close=("mid_close", "last"),
        atr=("atr", "last"),
        atr_ratio=("atr_ratio", "last"),
        quote_intensity_ratio=("quote_intensity_ratio", "mean"),
        book_imbalance=("tick_book_imbalance_mean", "mean"),
        microprice_edge=("tick_microprice_edge_mean", "mean"),
        tick_imbalance_5m=("tick_imbalance_5m", "last"),
        tick_imbalance_15m=("tick_imbalance_15m", "last"),
        price_efficiency=("price_efficiency_5m", "mean"),
        spread=("tick_spread_mean", "mean"),
        realized_variance=("tick_realized_variance", "sum"),
        close_location=("close_location", "last"),
    ).reset_index(drop=True)
    complete = (
        frame["bars"].eq(3)
        & frame["bar_end_utc"].sub(frame["first_start"]).eq(pd.Timedelta(minutes=15))
    )
    return frame.loc[complete].sort_values("bar_end_utc", kind="mergesort").reset_index(
        drop=True
    )


def _candidate_frame(m5: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    frame = _complete_m15(m5)
    protocol = config["candidate_protocol"]
    atr = frame["atr"].replace(0.0, np.nan)
    range_lookback = int(protocol["range_lookback_bars"])
    trend_lookback = int(protocol["trend_lookback_bars"])
    impulse_lookback = int(protocol["impulse_lookback_bars"])
    compression_lookback = int(protocol["compression_lookback_bars"])
    quantile_lookback = int(protocol["compression_quantile_lookback_bars"])
    frame["body_atr"] = (frame["mid_close"] - frame["mid_open"]) / atr
    frame["return_1_atr"] = frame["mid_close"].diff() / atr
    frame["return_4_atr"] = frame["mid_close"].diff(impulse_lookback) / atr
    frame["return_16_atr"] = frame["mid_close"].diff(trend_lookback) / atr
    frame["prior_high"] = frame["mid_high"].shift(1).rolling(range_lookback).max()
    frame["prior_low"] = frame["mid_low"].shift(1).rolling(range_lookback).min()
    width = frame["prior_high"] - frame["prior_low"]
    frame["range_width_atr"] = width / atr
    frame["channel_location_centered"] = (
        2.0 * (frame["mid_close"] - frame["prior_low"]) / width.replace(0.0, np.nan)
        - 1.0
    )
    above = (frame["mid_close"] - frame["prior_high"]) / atr
    below = (frame["prior_low"] - frame["mid_close"]) / atr
    frame["break_distance_atr"] = np.maximum(above, below)
    compressed_width = (
        frame["mid_high"].rolling(compression_lookback).max()
        - frame["mid_low"].rolling(compression_lookback).min()
    ) / atr
    frame["compression_ratio"] = compressed_width
    frame["compression_threshold"] = (
        compressed_width.shift(1)
        .rolling(quantile_lookback, min_periods=quantile_lookback)
        .quantile(float(protocol["compression_quantile"]))
    )
    frame["microprice_edge_atr"] = frame["microprice_edge"] / atr
    frame["spread_atr"] = frame["spread"] / atr
    frame["realized_variance_atr2"] = frame["realized_variance"] / atr.pow(2)
    frame["close_location_centered"] = 2.0 * frame["close_location"] - 1.0
    hour = frame["bar_end_utc"].dt.hour + frame["bar_end_utc"].dt.minute / 60.0
    weekday = frame["bar_end_utc"].dt.weekday.astype(float)
    frame["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    frame["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    frame["weekday_sin"] = np.sin(2.0 * np.pi * weekday / 5.0)
    frame["weekday_cos"] = np.cos(2.0 * np.pi * weekday / 5.0)
    frame["session_slot"] = np.select(
        [hour.ge(1) & hour.lt(7), hour.ge(7) & hour.lt(13), hour.ge(13) & hour.lt(19)],
        ["ASIA", "LONDON", "NY"],
        default="OUTSIDE",
    )

    minimum_body = float(protocol["minimum_body_atr"])
    minimum_impulse = float(protocol["minimum_impulse_atr"])
    minimum_trend = float(protocol["minimum_trend_atr"])
    masks: list[tuple[str, pd.Series, int]] = [
        (
            "RANGE_BREAK_CONTINUATION",
            frame["mid_close"].gt(frame["prior_high"]) & frame["body_atr"].ge(minimum_body),
            1,
        ),
        (
            "RANGE_BREAK_CONTINUATION",
            frame["mid_close"].lt(frame["prior_low"]) & frame["body_atr"].le(-minimum_body),
            -1,
        ),
        (
            "TREND_PULLBACK_RESUME",
            frame["return_16_atr"].ge(minimum_trend)
            & frame["body_atr"].shift(1).lt(-0.10)
            & frame["body_atr"].ge(minimum_body),
            1,
        ),
        (
            "TREND_PULLBACK_RESUME",
            frame["return_16_atr"].le(-minimum_trend)
            & frame["body_atr"].shift(1).gt(0.10)
            & frame["body_atr"].le(-minimum_body),
            -1,
        ),
        (
            "COMPRESSION_EXPANSION",
            frame["compression_ratio"].shift(1).le(frame["compression_threshold"].shift(1))
            & frame["body_atr"].ge(minimum_body),
            1,
        ),
        (
            "COMPRESSION_EXPANSION",
            frame["compression_ratio"].shift(1).le(frame["compression_threshold"].shift(1))
            & frame["body_atr"].le(-minimum_body),
            -1,
        ),
        (
            "IMPULSE_RETEST",
            frame["return_4_atr"].shift(1).ge(minimum_impulse)
            & frame["body_atr"].between(-0.80, -0.10),
            1,
        ),
        (
            "IMPULSE_RETEST",
            frame["return_4_atr"].shift(1).le(-minimum_impulse)
            & frame["body_atr"].between(0.10, 0.80),
            -1,
        ),
        (
            "FAILED_RANGE_BREAK",
            frame["mid_high"].shift(1).gt(frame["prior_high"].shift(1))
            & frame["mid_close"].lt(frame["prior_high"].shift(1))
            & frame["body_atr"].le(-0.10),
            -1,
        ),
        (
            "FAILED_RANGE_BREAK",
            frame["mid_low"].shift(1).lt(frame["prior_low"].shift(1))
            & frame["mid_close"].gt(frame["prior_low"].shift(1))
            & frame["body_atr"].ge(0.10),
            1,
        ),
    ]
    rows: list[pd.DataFrame] = []
    keep = [
        "bar_end_utc",
        "atr",
        "session_slot",
        *PRICE_SIGNED,
        *MICRO_SIGNED,
        *PRICE_UNSIGNED,
        *MICRO_UNSIGNED,
        *TIME_UNSIGNED,
    ]
    for event_type, mask, direction in masks:
        selected = frame.loc[mask.fillna(False), keep].copy()
        if selected.empty:
            continue
        selected["event_type"] = event_type
        selected["direction_value"] = direction
        rows.append(selected)
    if not rows:
        raise ValueError("V98 candidate protocol produced no events")
    events = pd.concat(rows, ignore_index=True)
    events = events.drop_duplicates(
        ["bar_end_utc", "event_type", "direction_value"], keep="first"
    )
    for event_type in EVENT_TYPES:
        events[f"event_{event_type}"] = events["event_type"].eq(event_type).astype(float)
    events[list(ALL_FEATURES)] = events.loc[:, ALL_FEATURES].replace(
        [np.inf, -np.inf], np.nan
    )
    return events.sort_values(
        ["bar_end_utc", "event_type", "direction_value"], kind="mergesort"
    ).reset_index(drop=True)


def prepare_features(
    h1: pd.DataFrame,
    m5: pd.DataFrame,
    unused_source: pd.DataFrame | None,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    del h1, unused_source
    return _candidate_frame(m5, config)


def generate_manifest(
    events: pd.DataFrame,
    discovery_start: pd.Timestamp,
    discovery_end: pd.Timestamp,
    attempt_first: int,
    policies_per_mechanic: int,
    minimum_raw_signals: int,
) -> pd.DataFrame:
    stage = events["bar_end_utc"].ge(discovery_start) & events["bar_end_utc"].lt(
        discovery_end
    )
    raw_signals = int(events.loc[stage, "bar_end_utc"].nunique())
    if raw_signals < minimum_raw_signals:
        raise ValueError("V98 event universe lacks preregistered Discovery density")
    long_count = int(events.loc[stage & events["direction_value"].eq(1), "bar_end_utc"].nunique())
    short_count = int(events.loc[stage & events["direction_value"].eq(-1), "bar_end_utc"].nunique())
    rows: list[dict[str, Any]] = []
    attempt = attempt_first
    for mechanic in MECHANICS:
        policies = parameter_space(mechanic)
        if len(policies) != policies_per_mechanic:
            raise ValueError(f"V98 policy count changed for {mechanic}")
        for params in policies:
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            rows.append(
                {
                    "attempt_no": attempt,
                    "policy_id": hashlib.sha256(
                        f"{mechanic}|{canonical}".encode("ascii")
                    ).hexdigest()[:16],
                    "mechanic": mechanic,
                    "raw_discovery_signal_count": raw_signals,
                    "raw_discovery_long_count": long_count,
                    "raw_discovery_short_count": short_count,
                    "parameters_json": canonical,
                }
            )
            attempt += 1
    manifest = pd.DataFrame(rows)
    expected = len(MECHANICS) * policies_per_mechanic
    if len(manifest) != expected or manifest["policy_id"].duplicated().any():
        raise ValueError("Invalid V98 policy manifest")
    return manifest


def feature_columns(feature_set: str) -> list[str]:
    if feature_set == "PRICE_EVENT_STATE":
        return [*PRICE_SIGNED, *PRICE_UNSIGNED, *EVENT_ONE_HOT]
    if feature_set == "MICRO_EVENT_STATE":
        return [*MICRO_SIGNED, *MICRO_UNSIGNED, *EVENT_ONE_HOT]
    if feature_set == "PRICE_MICRO_EVENT_STATE":
        return [
            *PRICE_SIGNED,
            *MICRO_SIGNED,
            *PRICE_UNSIGNED,
            *MICRO_UNSIGNED,
            *EVENT_ONE_HOT,
        ]
    if feature_set == "PRICE_TIME_EVENT_STATE":
        return [*PRICE_SIGNED, *PRICE_UNSIGNED, *TIME_UNSIGNED, *EVENT_ONE_HOT]
    if feature_set == "ALL_EVENT_STATE":
        return list(ALL_FEATURES)
    raise KeyError(feature_set)


def _business_days(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(
        np.busday_count(
            np.datetime64(start.tz_convert("UTC").date(), "D"),
            np.datetime64(end.tz_convert("UTC").date(), "D"),
        )
    )


def _profile_key(params: Mapping[str, Any]) -> tuple[float, float, int]:
    return (
        float(params["stop_atr"]),
        float(params["target_r"]),
        int(params["hold_hours"]),
    )


def _build_action_outcomes(
    events: pd.DataFrame,
    m5: pd.DataFrame,
    config: Mapping[str, Any],
    params: Mapping[str, Any],
    stage: str,
) -> pd.DataFrame:
    folds = config["model_protocol"]["folds"][stage]
    start = min(pd.Timestamp(item["train_start"]) for item in folds)
    end = max(pd.Timestamp(item["test_end_exclusive"]) for item in folds)
    eligible = events["bar_end_utc"].ge(start) & events["bar_end_utc"].lt(end)
    arrays = BASE.execution_arrays(m5)
    execution = config["execution"]
    rows: list[dict[str, Any]] = []
    for source in events.loc[eligible].itertuples(index=False):
        outcome = BASE.simulate_trade(
            arrays,
            pd.Timestamp(source.bar_end_utc),
            float(source.atr),
            int(source.direction_value),
            params,
            execution,
            end,
        )
        if outcome is None:
            continue
        row = {name: getattr(source, name) for name in ALL_FEATURES}
        row.update(outcome)
        row["direction_value"] = int(source.direction_value)
        row["event_type"] = str(source.event_type)
        row["session_slot"] = str(source.session_slot)
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    actions = pd.DataFrame(rows)
    direction = actions["direction_value"].astype(float)
    for column in (*PRICE_SIGNED, *MICRO_SIGNED):
        actions[column] = pd.to_numeric(actions[column], errors="coerce") * direction
    actions[list(ALL_FEATURES)] = actions.loc[:, ALL_FEATURES].replace(
        [np.inf, -np.inf], np.nan
    )
    actions["label"] = actions["stress_net_r"].gt(0.0).astype(int)
    multiplicity = actions.groupby("signal_time")["signal_time"].transform("size")
    actions["sample_weight"] = 1.0 / multiplicity.astype(float)
    return actions.sort_values(
        ["signal_time", "event_type", "direction_value"], kind="mergesort"
    ).reset_index(drop=True)


def _build_model(model_id: int) -> HistGradientBoostingClassifier:
    leaves, rate, l2, minimum_leaf, iterations = MODEL_SPECS[model_id]
    return HistGradientBoostingClassifier(
        learning_rate=rate,
        max_iter=iterations,
        max_leaf_nodes=leaves,
        min_samples_leaf=minimum_leaf,
        l2_regularization=l2,
        early_stopping=False,
        random_state=9800 + model_id,
    )


def _best_action_per_signal(scored: pd.DataFrame) -> pd.DataFrame:
    ordered = scored.sort_values(
        ["signal_time", "score", "event_type", "direction_value"],
        ascending=[True, False, True, False],
        kind="mergesort",
    )
    return ordered.drop_duplicates("signal_time", keep="first").reset_index(drop=True)


def _calibrate_threshold(
    scored: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    target_frequency: float,
) -> float:
    candidates = _best_action_per_signal(scored)
    target = int(round(target_frequency * _business_days(start, end)))
    if target <= 0 or target >= len(candidates):
        raise ValueError("V98 calibration target is outside candidate support")
    values = np.sort(candidates["score"].to_numpy(dtype=float))[::-1]
    upper = float(values[target - 1])
    lower = float(values[target])
    return upper if upper == lower else (upper + lower) / 2.0


def _route_candidates(
    scored: pd.DataFrame,
    threshold: float,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    candidates = _best_action_per_signal(scored)
    candidates = candidates.loc[candidates["score"].ge(threshold)].copy()
    candidates = candidates.sort_values(
        ["entry_time", "score", "event_type"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    daily: dict[Any, int] = {}
    slots: dict[tuple[Any, str], int] = {}
    open_until: list[pd.Timestamp] = []
    selected: list[dict[str, Any]] = []
    execution = config["execution"]
    maximum_open = int(execution["maximum_model_open_positions"])
    maximum_daily = int(execution["maximum_trades_per_policy_utc_day"])
    maximum_slot = int(execution["maximum_trades_per_session_slot"])
    for row in candidates.to_dict(orient="records"):
        entry = pd.Timestamp(row["entry_time"])
        open_until = [value for value in open_until if value > entry]
        day = entry.date()
        slot = str(row["session_slot"])
        if len(open_until) >= maximum_open:
            continue
        if daily.get(day, 0) >= maximum_daily:
            continue
        if slots.get((day, slot), 0) >= maximum_slot:
            continue
        selected.append(row)
        open_until.append(pd.Timestamp(row["exit_time"]))
        daily[day] = daily.get(day, 0) + 1
        slots[(day, slot)] = slots.get((day, slot), 0) + 1
    if not selected:
        return pd.DataFrame()
    return pd.DataFrame(selected).sort_values("entry_time", kind="mergesort").reset_index(
        drop=True
    )


def _score_folds(
    actions: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
    feature_set: str,
    model_id: int,
) -> list[dict[str, Any]]:
    columns = feature_columns(feature_set)
    results: list[dict[str, Any]] = []
    for fold in config["model_protocol"]["folds"][stage]:
        train_start = pd.Timestamp(fold["train_start"])
        train_end = pd.Timestamp(fold["train_end_exclusive"])
        calibration_start = pd.Timestamp(fold["calibration_start"])
        calibration_end = pd.Timestamp(fold["calibration_end_exclusive"])
        test_start = pd.Timestamp(fold["test_start"])
        test_end = pd.Timestamp(fold["test_end_exclusive"])
        train = actions.loc[
            actions["entry_time"].ge(train_start) & actions["exit_time"].lt(train_end)
        ].copy()
        calibration = actions.loc[
            actions["entry_time"].ge(calibration_start)
            & actions["entry_time"].lt(calibration_end)
        ].copy()
        test = actions.loc[
            actions["entry_time"].ge(test_start)
            & actions["entry_time"].lt(test_end)
            & actions["exit_time"].lt(test_end)
        ].copy()
        if (
            train.empty
            or calibration.empty
            or test.empty
            or train["label"].nunique() != 2
        ):
            raise ValueError(f"V98 fold lacks model support: {fold['fold_id']}")
        model = _build_model(model_id)
        model.fit(
            train[columns],
            train["label"].to_numpy(dtype=int),
            sample_weight=train["sample_weight"].to_numpy(dtype=float),
        )
        calibration["score"] = model.predict_proba(calibration[columns])[:, 1]
        test["score"] = model.predict_proba(test[columns])[:, 1]
        auc = (
            float(
                roc_auc_score(
                    test["label"],
                    test["score"],
                    sample_weight=test["sample_weight"],
                )
            )
            if test["label"].nunique() == 2
            else 0.5
        )
        results.append(
            {
                "fold_id": str(fold["fold_id"]),
                "calibration_start": calibration_start,
                "calibration_end": calibration_end,
                "test_start": test_start,
                "test_end": test_end,
                "auc": auc,
                "calibration": calibration,
                "test": test,
            }
        )
    return results


def _policy_trades_from_scored_folds(
    scored_folds: list[dict[str, Any]],
    params: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    diagnostics: list[dict[str, Any]] = []
    target_frequency = float(params["target_addon_trades_per_weekday"])
    for fold in scored_folds:
        threshold = _calibrate_threshold(
            fold["calibration"],
            fold["calibration_start"],
            fold["calibration_end"],
            target_frequency,
        )
        routed = _route_candidates(fold["test"], threshold, config)
        weekdays = _business_days(fold["test_start"], fold["test_end"])
        frequency = len(routed) / weekdays if weekdays else 0.0
        diagnostics.append(
            {
                "fold_id": fold["fold_id"],
                "auc": float(fold["auc"]),
                "threshold": threshold,
                "trades": int(len(routed)),
                "trades_per_weekday": float(frequency),
            }
        )
        if not routed.empty:
            frames.append(routed.assign(fold_id=fold["fold_id"]))
    trades = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return trades, diagnostics


def _gate_checks(row: Mapping[str, Any], gate: Mapping[str, Any]) -> dict[str, bool]:
    base = V89.gate_checks(row, gate)
    total_direction = int(row["long_trades"]) + int(row["short_trades"])
    minority = (
        min(int(row["long_trades"]), int(row["short_trades"])) / total_direction
        if total_direction
        else 0.0
    )
    base.update(
        {
            "minimum_fold_auc": float(row["minimum_fold_auc"])
            >= float(gate["minimum_fold_auc"]),
            "minimum_fold_frequency": float(row["minimum_fold_frequency"])
            >= float(gate["minimum_fold_frequency"]),
            "minimum_direction_share": minority
            >= float(gate["minimum_direction_share"]),
        }
    )
    return base


def evaluate_policies(
    frame: pd.DataFrame,
    m5: pd.DataFrame,
    manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    stage_start, stage_end = map(pd.Timestamp, config["windows"][stage])
    action_cache: dict[tuple[float, float, int], pd.DataFrame] = {}
    ledger_cache: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    grouped: dict[tuple[tuple[float, float, int], str, int], list[Any]] = {}
    for policy in manifest.itertuples(index=False):
        params = json.loads(policy.parameters_json)
        key = (_profile_key(params), str(policy.mechanic), int(params["model_id"]))
        grouped.setdefault(key, []).append(policy)
    for (profile, feature_set, model_id), policies in grouped.items():
        representative = json.loads(policies[0].parameters_json)
        actions = action_cache.get(profile)
        if actions is None:
            actions = _build_action_outcomes(frame, m5, config, representative, stage)
            action_cache[profile] = actions
        scored_folds = _score_folds(actions, config, stage, feature_set, model_id)
        for policy in policies:
            params = json.loads(policy.parameters_json)
            trades, diagnostics = _policy_trades_from_scored_folds(
                scored_folds, params, config
            )
            if not trades.empty:
                trades = trades.assign(
                    attempt_no=int(policy.attempt_no),
                    policy_id=str(policy.policy_id),
                    mechanic=str(policy.mechanic),
                    model_id=int(params["model_id"]),
                    target_addon_trades_per_weekday=float(
                        params["target_addon_trades_per_weekday"]
                    ),
                )
            ledger_cache[str(policy.policy_id)] = trades
            summary = summarize(
                trades,
                stage_start,
                stage_end,
                config["segments"][stage],
                int(config["gates"][stage]["top_winners_removed"]),
            )
            rows.append(
                {
                    "attempt_no": int(policy.attempt_no),
                    "policy_id": str(policy.policy_id),
                    "mechanic": str(policy.mechanic),
                    "parameters_json": str(policy.parameters_json),
                    **summary,
                    "minimum_fold_auc": min(item["auc"] for item in diagnostics),
                    "minimum_fold_frequency": min(
                        item["trades_per_weekday"] for item in diagnostics
                    ),
                    "fold_diagnostics": diagnostics,
                }
            )
    metrics = pd.DataFrame(rows).sort_values("attempt_no", kind="mergesort").reset_index(
        drop=True
    )
    metrics["fdr_qvalue"] = benjamini_hochberg(metrics["block_pvalue"])
    checks: list[dict[str, bool]] = []
    passes: list[bool] = []
    for row in metrics.to_dict(orient="records"):
        values = _gate_checks(row, config["gates"][stage])
        checks.append(values)
        passes.append(all(values.values()))
    metrics["gate_checks_json"] = [
        json.dumps(value, sort_keys=True, separators=(",", ":")) for value in checks
    ]
    metrics["fold_diagnostics_json"] = metrics["fold_diagnostics"].map(
        lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    )
    metrics["gate_pass"] = passes
    return metrics.drop(columns=["fold_diagnostics"]), ledger_cache


def selected_trade_ledger(
    frame: pd.DataFrame,
    m5: pd.DataFrame,
    selected_manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
    cache: dict[str, pd.DataFrame] | None = None,
) -> pd.DataFrame:
    if selected_manifest.empty:
        return pd.DataFrame()
    if cache is None:
        _, cache = evaluate_policies(frame, m5, selected_manifest, config, stage)
    frames = [
        cache[str(policy_id)]
        for policy_id in selected_manifest["policy_id"].astype(str)
        if str(policy_id) in cache and not cache[str(policy_id)].empty
    ]
    if not frames:
        return pd.DataFrame()
    keep = [
        "attempt_no",
        "policy_id",
        "mechanic",
        "model_id",
        "target_addon_trades_per_weekday",
        "fold_id",
        "event_type",
        "session_slot",
        "score",
        *OUTCOME_COLUMNS,
    ]
    return pd.concat(frames, ignore_index=True).loc[:, keep].sort_values(
        ["entry_time", "attempt_no"], kind="mergesort"
    ).reset_index(drop=True)


__all__ = [
    "MECHANICS",
    "EVENT_TYPES",
    "EXECUTION_PROFILES",
    "MODEL_SPECS",
    "TARGET_FREQUENCIES",
    "parameter_space",
    "prepare_features",
    "generate_manifest",
    "feature_columns",
    "evaluate_policies",
    "selected_trade_ledger",
    "select_advancers",
    "summarize",
    "benjamini_hochberg",
]
