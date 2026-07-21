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
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent
PREFIXES = ("spx", "copper", "usdcnh")
MECHANICS = (
    "PRICE_STATE",
    "MICROSTRUCTURE_STATE",
    "CROSSASSET_STATE",
    "PRICE_CROSSASSET_STATE",
    "ALL_CAUSAL_STATE",
)
EXECUTION_PROFILES = (
    (0.6, 1.0, 2),
    (0.8, 1.25, 4),
    (1.0, 1.5, 6),
    (1.0, 2.0, 8),
    (1.2, 2.0, 8),
)
MODEL_C_VALUES = (0.01, 0.03, 0.1, 0.3)
TARGET_FREQUENCIES = tuple(round(0.9 + 0.1 * index, 1) for index in range(10))

PRICE_SIGNED = (
    "body_atr",
    "impulse_1_atr",
    "impulse_3_atr",
    "impulse_6_atr",
    "channel_location_centered",
)
MICRO_SIGNED = (
    "m5_return_atr",
    "m5_book_imbalance",
    "m5_microprice_edge_atr",
    "m5_tick_imbalance_5m",
    "m5_tick_imbalance_15m",
    "m5_close_location_centered",
)
CROSS_SIGNED = tuple(
    [f"{prefix}_z_{horizon}h_240" for prefix in PREFIXES for horizon in (1, 3, 6)]
    + [f"risk_score_{horizon}h_240" for horizon in (1, 3, 6)]
    + [f"growth_score_{horizon}h_240" for horizon in (1, 3, 6)]
)
PRICE_UNSIGNED = ("h1_atr_ratio_causal",)
MICRO_UNSIGNED = (
    "m5_atr_ratio",
    "m5_quote_intensity_ratio",
    "m5_price_efficiency",
    "m5_spread_atr",
)
CROSS_UNSIGNED = tuple(f"source_energy_{horizon}h_240" for horizon in (1, 3, 6))
TIME_UNSIGNED = ("hour_sin", "hour_cos", "weekday_sin", "weekday_cos")
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
    "causal_hourly_action_router_v97_v89_metrics",
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
    for model_c, (stop, target, hold), frequency in product(
        MODEL_C_VALUES, EXECUTION_PROFILES, TARGET_FREQUENCIES
    ):
        rows.append(
            {
                "feature_set": mechanic,
                "model_c": model_c,
                "stop_atr": stop,
                "target_r": target,
                "hold_hours": hold,
                "target_addon_trades_per_weekday": frequency,
                "source_lookback": 240,
                "minimum_active_m5": 9,
                "maximum_source_staleness_minutes": 15,
            }
        )
    return rows


def _causal_z(values: pd.Series, lookback: int) -> pd.Series:
    observed = values.dropna()
    prior = observed.shift(1).rolling(lookback, min_periods=lookback)
    scored = (observed - prior.mean()) / prior.std(ddof=0).replace(0.0, np.nan)
    return scored.reindex(values.index)


def _atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["mid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["mid_high"] - frame["mid_low"],
            (frame["mid_high"] - previous).abs(),
            (frame["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def _contiguous_lag(frame: pd.DataFrame, bars: int) -> pd.Series:
    return frame["bar_end_utc"].diff(bars).eq(pd.Timedelta(hours=bars))


def _aggregate_source_prefix(source_m5: pd.DataFrame, prefix: str) -> pd.DataFrame:
    required = {
        "bar_open_timestamp_ms",
        f"{prefix}_available_timestamp_ms",
        f"{prefix}_source_last_timestamp_ms",
        f"{prefix}_mid_open",
        f"{prefix}_mid_high",
        f"{prefix}_mid_low",
        f"{prefix}_mid_close",
        f"{prefix}_tick_count",
    }
    missing = sorted(required.difference(source_m5.columns))
    if missing:
        raise ValueError(f"Growth-risk source is missing columns: {missing}")
    selected = source_m5.loc[
        source_m5[f"{prefix}_mid_close"].notna(), list(required)
    ].copy()
    selected["bar_open_utc"] = pd.to_datetime(
        selected["bar_open_timestamp_ms"], unit="ms", utc=True
    )
    selected["available_utc"] = pd.to_datetime(
        selected[f"{prefix}_available_timestamp_ms"], unit="ms", utc=True
    )
    selected["source_last_tick_utc"] = pd.to_datetime(
        selected[f"{prefix}_source_last_timestamp_ms"], unit="ms", utc=True
    )
    if (selected["source_last_tick_utc"] >= selected["available_utc"]).any():
        raise ValueError(f"Noncausal {prefix} source tick availability")
    selected["h1_open_utc"] = selected["bar_open_utc"].dt.floor("h")
    grouped = selected.groupby("h1_open_utc", sort=True, observed=True)
    result = grouped.agg(
        **{
            f"{prefix}_mid_open": (f"{prefix}_mid_open", "first"),
            f"{prefix}_mid_high": (f"{prefix}_mid_high", "max"),
            f"{prefix}_mid_low": (f"{prefix}_mid_low", "min"),
            f"{prefix}_mid_close": (f"{prefix}_mid_close", "last"),
            f"{prefix}_tick_count": (f"{prefix}_tick_count", "sum"),
            f"{prefix}_active_m5": ("bar_open_timestamp_ms", "size"),
            f"{prefix}_source_last_available_utc": ("available_utc", "max"),
            f"{prefix}_source_last_tick_utc": ("source_last_tick_utc", "max"),
        }
    ).reset_index()
    result["bar_end_utc"] = result["h1_open_utc"] + pd.Timedelta(hours=1)
    if (result[f"{prefix}_source_last_available_utc"] > result["bar_end_utc"]).any():
        raise ValueError(f"Future {prefix} M5 bar entered completed H1 state")
    result[f"{prefix}_staleness_minutes"] = (
        result["bar_end_utc"] - result[f"{prefix}_source_last_tick_utc"]
    ).dt.total_seconds() / 60.0
    return result.drop(columns=["h1_open_utc"])


def prepare_source_h1(
    source_m5: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    frames = [_aggregate_source_prefix(source_m5, prefix) for prefix in PREFIXES]
    result = frames[0]
    for frame in frames[1:]:
        result = result.merge(frame, on="bar_end_utc", how="outer", validate="one_to_one")
    result = result.sort_values("bar_end_utc", kind="mergesort").reset_index(drop=True)
    result["hour_utc"] = result["bar_end_utc"].dt.hour
    result["session_slot"] = np.select(
        [
            result["hour_utc"].ge(1) & result["hour_utc"].lt(7),
            result["hour_utc"].ge(7) & result["hour_utc"].lt(13),
            result["hour_utc"].ge(13) & result["hour_utc"].lt(19),
        ],
        ["ASIA", "LONDON", "NY"],
        default="OUTSIDE",
    )
    lookbacks = tuple(map(int, config["features"]["source_normalization_lookbacks"]))
    for prefix in PREFIXES:
        log_close = np.log(
            result[f"{prefix}_mid_close"].where(result[f"{prefix}_mid_close"].gt(0))
        )
        for horizon in (1, 3, 6):
            contiguous = _contiguous_lag(result, horizon)
            returns = log_close.diff(horizon).where(contiguous)
            result[f"{prefix}_return_{horizon}h"] = returns
            for lookback in lookbacks:
                result[f"{prefix}_z_{horizon}h_{lookback}"] = _causal_z(
                    returns, lookback
                )
    for horizon in (1, 3, 6):
        for lookback in lookbacks:
            spx = result[f"spx_z_{horizon}h_{lookback}"]
            copper = result[f"copper_z_{horizon}h_{lookback}"]
            usdcnh = result[f"usdcnh_z_{horizon}h_{lookback}"]
            result[f"risk_score_{horizon}h_{lookback}"] = (
                -spx - copper + usdcnh
            ) / 3.0
            result[f"growth_score_{horizon}h_{lookback}"] = (
                copper - usdcnh
            ) / 2.0
            result[f"source_energy_{horizon}h_{lookback}"] = pd.concat(
                [spx.abs(), copper.abs(), usdcnh.abs()], axis=1
            ).max(axis=1, skipna=False)
    return result


def _prepare_last_m5(m5: pd.DataFrame) -> pd.DataFrame:
    required = {
        "bar_end_utc",
        "mid_open",
        "mid_close",
        "bid_close",
        "ask_close",
        "atr",
        "atr_ratio",
        "quote_intensity_ratio",
        "tick_book_imbalance_mean",
        "tick_microprice_edge_mean",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "price_efficiency_5m",
        "close_location",
    }
    missing = sorted(required.difference(m5.columns))
    if missing:
        raise ValueError(f"XAU M5 source is missing columns: {missing}")
    selected = m5.loc[:, sorted(required)].copy()
    atr = selected["atr"].replace(0.0, np.nan)
    selected["m5_return_atr"] = (selected["mid_close"] - selected["mid_open"]) / atr
    selected["m5_book_imbalance"] = selected["tick_book_imbalance_mean"]
    selected["m5_microprice_edge_atr"] = selected["tick_microprice_edge_mean"] / atr
    selected["m5_tick_imbalance_5m"] = selected["tick_imbalance_5m"]
    selected["m5_tick_imbalance_15m"] = selected["tick_imbalance_15m"]
    selected["m5_close_location_centered"] = 2.0 * selected["close_location"] - 1.0
    selected["m5_atr_ratio"] = selected["atr_ratio"]
    selected["m5_quote_intensity_ratio"] = selected["quote_intensity_ratio"]
    selected["m5_price_efficiency"] = selected["price_efficiency_5m"]
    selected["m5_spread_atr"] = (selected["ask_close"] - selected["bid_close"]) / atr
    keep = ["bar_end_utc", *MICRO_SIGNED, *MICRO_UNSIGNED]
    return selected.loc[:, keep]


def prepare_features(
    h1: pd.DataFrame,
    m5: pd.DataFrame,
    source_m5: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    required = {
        "bar_start_utc",
        "bar_end_utc",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
    }
    missing = sorted(required.difference(h1.columns))
    if missing:
        raise ValueError(f"H1 source is missing columns: {missing}")
    frame = h1.copy().sort_values("bar_end_utc", kind="mergesort").reset_index(drop=True)
    frame["atr14"] = _atr(frame, int(config["features"]["h1_atr_period"]))
    scale = frame["atr14"].replace(0.0, np.nan)
    frame["body_atr"] = (frame["mid_close"] - frame["mid_open"]) / scale
    for horizon in (1, 3, 6):
        contiguous = _contiguous_lag(frame, horizon)
        frame[f"impulse_{horizon}_atr"] = (
            frame["mid_close"] - frame["mid_close"].shift(horizon)
        ).div(scale).where(contiguous)
    contiguous = _contiguous_lag(frame, 12)
    prior_high = frame["mid_high"].shift(1).rolling(12, min_periods=12).max()
    prior_low = frame["mid_low"].shift(1).rolling(12, min_periods=12).min()
    width = (prior_high - prior_low).replace(0.0, np.nan)
    frame["channel_location_centered"] = (
        2.0 * (frame["mid_close"] - prior_low) / width - 1.0
    ).where(contiguous)
    prior_atr = frame["atr14"].shift(1).rolling(240, min_periods=120).median()
    frame["h1_atr_ratio_causal"] = frame["atr14"] / prior_atr.replace(0.0, np.nan)
    source_h1 = prepare_source_h1(source_m5, config)
    frame = frame.merge(source_h1, on="bar_end_utc", how="left", validate="one_to_one")
    frame = frame.merge(
        _prepare_last_m5(m5), on="bar_end_utc", how="left", validate="one_to_one"
    )
    hour = frame["bar_end_utc"].dt.hour.astype(float)
    weekday = frame["bar_end_utc"].dt.weekday.astype(float)
    frame["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    frame["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    frame["weekday_sin"] = np.sin(2.0 * np.pi * weekday / 5.0)
    frame["weekday_cos"] = np.cos(2.0 * np.pi * weekday / 5.0)
    return frame


def source_lattice_mask(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.Series:
    mask = frame["session_slot"].isin(("ASIA", "LONDON", "NY"))
    for prefix in PREFIXES:
        mask &= frame[f"{prefix}_active_m5"].ge(int(params["minimum_active_m5"]))
        mask &= frame[f"{prefix}_staleness_minutes"].le(
            float(params["maximum_source_staleness_minutes"])
        )
    required_features = [
        *PRICE_SIGNED,
        *MICRO_SIGNED,
        *CROSS_SIGNED,
        *PRICE_UNSIGNED,
        *MICRO_UNSIGNED,
        *CROSS_UNSIGNED,
        *TIME_UNSIGNED,
        "atr14",
    ]
    mask &= frame[required_features].replace([np.inf, -np.inf], np.nan).notna().all(axis=1)
    return mask.fillna(False)


def generate_manifest(
    source_h1: pd.DataFrame,
    discovery_start: pd.Timestamp,
    discovery_end: pd.Timestamp,
    attempt_first: int,
    policies_per_mechanic: int,
    minimum_raw_signals: int,
) -> pd.DataFrame:
    stage = source_h1["bar_end_utc"].ge(discovery_start) & source_h1[
        "bar_end_utc"
    ].lt(discovery_end)
    source_mask = source_h1["session_slot"].isin(("ASIA", "LONDON", "NY"))
    for prefix in PREFIXES:
        source_mask &= source_h1[f"{prefix}_active_m5"].ge(9)
        source_mask &= source_h1[f"{prefix}_staleness_minutes"].le(15)
    raw_signals = int((stage & source_mask.fillna(False)).sum())
    if raw_signals < minimum_raw_signals:
        raise ValueError("V97 source lattice lacks preregistered Discovery density")
    rows: list[dict[str, Any]] = []
    attempt = attempt_first
    for mechanic in MECHANICS:
        policies = parameter_space(mechanic)
        if len(policies) != policies_per_mechanic:
            raise ValueError(f"V97 policy count changed for {mechanic}")
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
                    "raw_discovery_long_count": raw_signals,
                    "raw_discovery_short_count": raw_signals,
                    "parameters_json": canonical,
                }
            )
            attempt += 1
    manifest = pd.DataFrame(rows)
    expected = len(MECHANICS) * policies_per_mechanic
    if len(manifest) != expected or manifest["policy_id"].duplicated().any():
        raise ValueError("Invalid V97 policy manifest")
    return manifest


def feature_columns(feature_set: str) -> list[str]:
    if feature_set == "PRICE_STATE":
        return [*PRICE_SIGNED, *PRICE_UNSIGNED, *TIME_UNSIGNED]
    if feature_set == "MICROSTRUCTURE_STATE":
        return [*MICRO_SIGNED, *MICRO_UNSIGNED, *TIME_UNSIGNED]
    if feature_set == "CROSSASSET_STATE":
        return [*CROSS_SIGNED, *CROSS_UNSIGNED, *TIME_UNSIGNED]
    if feature_set == "PRICE_CROSSASSET_STATE":
        return [
            *PRICE_SIGNED,
            *CROSS_SIGNED,
            *PRICE_UNSIGNED,
            *CROSS_UNSIGNED,
            *TIME_UNSIGNED,
        ]
    if feature_set == "ALL_CAUSAL_STATE":
        return [
            *PRICE_SIGNED,
            *MICRO_SIGNED,
            *CROSS_SIGNED,
            *PRICE_UNSIGNED,
            *MICRO_UNSIGNED,
            *CROSS_UNSIGNED,
            *TIME_UNSIGNED,
        ]
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
    frame: pd.DataFrame,
    m5: pd.DataFrame,
    config: Mapping[str, Any],
    params: Mapping[str, Any],
    stage_end: pd.Timestamp,
) -> pd.DataFrame:
    start = pd.Timestamp(config["model_protocol"]["training_start_utc"])
    eligible = source_lattice_mask(frame, params)
    eligible &= frame["bar_end_utc"].ge(start) & frame["bar_end_utc"].lt(stage_end)
    arrays = BASE.execution_arrays(m5)
    execution = config["execution"]
    rows: list[dict[str, Any]] = []
    raw_features = [
        *PRICE_SIGNED,
        *MICRO_SIGNED,
        *CROSS_SIGNED,
        *PRICE_UNSIGNED,
        *MICRO_UNSIGNED,
        *CROSS_UNSIGNED,
        *TIME_UNSIGNED,
    ]
    for index in np.flatnonzero(eligible.to_numpy()):
        source = frame.iloc[int(index)]
        signal_time = pd.Timestamp(source["bar_end_utc"])
        for direction in (1, -1):
            outcome = BASE.simulate_trade(
                arrays,
                signal_time,
                float(source["atr14"]),
                direction,
                params,
                execution,
                stage_end,
            )
            if outcome is None:
                continue
            row = {
                **{name: source[name] for name in raw_features},
                **outcome,
                "direction_value": direction,
                "session_slot": str(source["session_slot"]),
            }
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    actions = pd.DataFrame(rows)
    direction = actions["direction_value"].astype(float)
    for column in (*PRICE_SIGNED, *MICRO_SIGNED, *CROSS_SIGNED):
        actions[column] = pd.to_numeric(actions[column], errors="coerce") * direction
    all_features = [
        *PRICE_SIGNED,
        *MICRO_SIGNED,
        *CROSS_SIGNED,
        *PRICE_UNSIGNED,
        *MICRO_UNSIGNED,
        *CROSS_UNSIGNED,
        *TIME_UNSIGNED,
    ]
    actions[all_features] = actions[all_features].replace([np.inf, -np.inf], np.nan)
    actions["label"] = actions["stress_net_r"].gt(0.0).astype(int)
    actions["sample_weight"] = 0.5
    return actions.sort_values(
        ["signal_time", "direction_value"], ascending=[True, False], kind="mergesort"
    ).reset_index(drop=True)


def _build_model(model_c: float) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(C=model_c, solver="lbfgs", max_iter=2000),
            ),
        ]
    )


def _best_action_per_signal(scored: pd.DataFrame) -> pd.DataFrame:
    ordered = scored.sort_values(
        ["signal_time", "score", "direction_value"],
        ascending=[True, False, False],
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
        raise ValueError("V97 calibration target is outside candidate support")
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
    candidates = candidates.sort_values("entry_time", kind="mergesort")
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
        if len(open_until) >= maximum_open:
            continue
        day = entry.date()
        slot = str(row["session_slot"])
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
    return pd.DataFrame(selected).sort_values("entry_time", kind="mergesort").reset_index(drop=True)


def _score_folds(
    actions: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
    feature_set: str,
    model_c: float,
) -> list[dict[str, Any]]:
    columns = feature_columns(feature_set)
    results: list[dict[str, Any]] = []
    for fold in config["model_protocol"]["folds"][stage]:
        calibration_start = pd.Timestamp(fold["calibration_start"])
        calibration_end = pd.Timestamp(fold["calibration_end_exclusive"])
        test_start = pd.Timestamp(fold["test_start"])
        test_end = pd.Timestamp(fold["test_end_exclusive"])
        train = actions.loc[actions["exit_time"].lt(calibration_start)].copy()
        calibration = actions.loc[
            actions["entry_time"].ge(calibration_start)
            & actions["entry_time"].lt(calibration_end)
        ].copy()
        test = actions.loc[
            actions["entry_time"].ge(test_start)
            & actions["entry_time"].lt(test_end)
            & actions["exit_time"].lt(test_end)
        ].copy()
        if train.empty or calibration.empty or test.empty or train["label"].nunique() != 2:
            raise ValueError(f"V97 fold lacks model support: {fold['fold_id']}")
        model = _build_model(model_c)
        model.fit(
            train[columns],
            train["label"].to_numpy(dtype=int),
            model__sample_weight=train["sample_weight"].to_numpy(dtype=float),
        )
        calibration = calibration.copy()
        test = test.copy()
        calibration["score"] = model.predict_proba(calibration[columns])[:, 1]
        test["score"] = model.predict_proba(test[columns])[:, 1]
        auc = (
            float(roc_auc_score(test["label"], test["score"], sample_weight=test["sample_weight"]))
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


def _gate_checks(
    row: Mapping[str, Any], gate: Mapping[str, Any]
) -> dict[str, bool]:
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
    grouped: dict[tuple[tuple[float, float, int], str, float], list[Any]] = {}
    for policy in manifest.itertuples(index=False):
        params = json.loads(policy.parameters_json)
        key = (_profile_key(params), str(policy.mechanic), float(params["model_c"]))
        grouped.setdefault(key, []).append(policy)
    for (profile, feature_set, model_c), policies in grouped.items():
        representative = json.loads(policies[0].parameters_json)
        actions = action_cache.get(profile)
        if actions is None:
            actions = _build_action_outcomes(
                frame, m5, config, representative, stage_end
            )
            action_cache[profile] = actions
        scored_folds = _score_folds(actions, config, stage, feature_set, model_c)
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
                    model_c=float(params["model_c"]),
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
    metrics = pd.DataFrame(rows).sort_values("attempt_no", kind="mergesort").reset_index(drop=True)
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
        "model_c",
        "target_addon_trades_per_weekday",
        "fold_id",
        "session_slot",
        "score",
        *OUTCOME_COLUMNS,
    ]
    return pd.concat(frames, ignore_index=True).loc[:, keep].sort_values(
        ["entry_time", "attempt_no"], kind="mergesort"
    ).reset_index(drop=True)


__all__ = [
    "MECHANICS",
    "EXECUTION_PROFILES",
    "MODEL_C_VALUES",
    "TARGET_FREQUENCIES",
    "parameter_space",
    "prepare_source_h1",
    "prepare_features",
    "source_lattice_mask",
    "generate_manifest",
    "feature_columns",
    "evaluate_policies",
    "selected_trade_ledger",
    "select_advancers",
    "summarize",
    "benjamini_hochberg",
]
