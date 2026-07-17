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


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_module(
    "cftc_options_volatility_base_campaign",
    RESEARCH_ROOT / "cftc-options-positioning-mechanics-v1" / "src" / "campaign.py",
)

MECHANICS = (
    "OPTIONS_OI_EXPANSION_BREAKOUT",
    "OPTIONS_OI_CONTRACTION_REVERSAL",
    "MM_OPTIONS_SPREAD_BUILD_BREAKOUT",
    "SWAP_OPTIONS_SPREAD_BUILD_BREAKOUT",
    "GROSS_OPTION_ACTIVITY_COMPRESSION_BREAKOUT",
)
SESSIONS = ("ALL", "ASIA", "LONDON", "NY")
_MISSING = object()


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    geometry = {
        "lookback": (52, 104, 156),
        "activity_threshold_z": (0.5, 0.75, 1.0, 1.25),
        "session": SESSIONS,
        "stop_atr": (0.75, 1.0, 1.25, 1.5),
        "target_r": (1.25, 1.5, 2.0),
        "hold_hours": (4, 8, 12, 24),
    }
    if mechanic == "OPTIONS_OI_CONTRACTION_REVERSAL":
        return _space(
            **geometry,
            impulse_hours=(3, 6, 12, 24),
            impulse_min_atr=(0.25, 0.5, 1.0),
            confirmation_min_atr=(0.0, 0.1, 0.2),
            channel_bars=(6,),
            breakout_buffer_atr=(0.0,),
            compression_max=(99.0,),
        )
    if mechanic in MECHANICS:
        compression = (
            (0.75, 1.0, 1.25)
            if mechanic == "GROSS_OPTION_ACTIVITY_COMPRESSION_BREAKOUT"
            else (99.0,)
        )
        return _space(
            **geometry,
            channel_bars=(6, 12, 24, 48),
            breakout_buffer_atr=(0.0, 0.05, 0.10),
            compression_max=compression,
            impulse_hours=(6,),
            impulse_min_atr=(0.0,),
            confirmation_min_atr=(0.0,),
        )
    raise KeyError(mechanic)


def _causal_z(values: pd.Series, lookback: int) -> pd.Series:
    prior = values.shift(1).rolling(lookback, min_periods=lookback)
    return (values - prior.mean()) / prior.std(ddof=0).replace(0.0, np.nan)


def prepare_features(
    h1: pd.DataFrame,
    positioning: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    frame = BASE.prepare_features(h1, positioning, config)
    weekly = BASE.prepare_positioning(positioning, config)
    option_oi = weekly["options_open_interest_delta_equivalent"].replace(0.0, np.nan)
    weekly["options_oi_log_change"] = np.log(option_oi).diff()
    weekly["mm_spread_share"] = weekly["managed_money_options_spread"] / option_oi
    weekly["swap_spread_share"] = weekly["swap_options_spread"] / option_oi
    gross_columns = (
        "producer_options_long",
        "producer_options_short",
        "swap_options_long",
        "swap_options_short",
        "swap_options_spread",
        "managed_money_options_long",
        "managed_money_options_short",
        "managed_money_options_spread",
        "other_reportable_options_long",
        "other_reportable_options_short",
        "other_reportable_options_spread",
    )
    weekly["gross_option_activity_share"] = (
        weekly[list(gross_columns)].abs().sum(axis=1) / option_oi
    )
    lookbacks = [int(value) for value in config["features"]["positioning_z_lookbacks"]]
    for lookback in lookbacks:
        weekly[f"options_oi_growth_z_{lookback}"] = _causal_z(
            weekly["options_oi_log_change"], lookback
        )
        weekly[f"mm_spread_build_z_{lookback}"] = _causal_z(
            weekly["mm_spread_share"].diff(), lookback
        )
        weekly[f"swap_spread_build_z_{lookback}"] = _causal_z(
            weekly["swap_spread_share"].diff(), lookback
        )
        weekly[f"gross_activity_level_z_{lookback}"] = _causal_z(
            weekly["gross_option_activity_share"], lookback
        )
    activity_columns = [
        column
        for column in weekly.columns
        if column.startswith(
            (
                "options_oi_growth_z_",
                "mm_spread_build_z_",
                "swap_spread_build_z_",
                "gross_activity_level_z_",
            )
        )
    ]
    activity = weekly[["available_utc", *activity_columns]].rename(
        columns={"available_utc": "activity_available_utc"}
    )
    frame = pd.merge_asof(
        frame.sort_values("bar_end_utc", kind="mergesort"),
        activity.sort_values("activity_available_utc", kind="mergesort"),
        left_on="bar_end_utc",
        right_on="activity_available_utc",
        direction="backward",
        tolerance=pd.Timedelta(
            days=float(config["features"]["maximum_positioning_staleness_days"])
        ),
    )
    observed = frame["activity_available_utc"].notna()
    if (
        frame.loc[observed, "activity_available_utc"]
        > frame.loc[observed, "bar_end_utc"]
    ).any():
        raise ValueError("Future CFTC activity joined to H1 decision")
    features = config["features"]
    baseline = (
        frame["atr14"]
        .shift(1)
        .rolling(
            int(features["atr_baseline_bars"]),
            min_periods=int(features["atr_baseline_minimum_bars"]),
        )
        .median()
    )
    frame["atr_ratio_causal"] = frame["atr14"] / baseline.replace(0.0, np.nan)
    scale = frame["atr14"].replace(0.0, np.nan)
    for bars in (3, 6, 12, 24):
        frame[f"impulse_{bars}_atr"] = (
            frame["mid_close"] - frame["mid_close"].shift(bars)
        ) / scale
    for bars in (6, 12, 24, 48):
        frame[f"prior_high_{bars}"] = (
            frame["mid_high"].shift(1).rolling(bars, min_periods=bars).max()
        )
        frame[f"prior_low_{bars}"] = (
            frame["mid_low"].shift(1).rolling(bars, min_periods=bars).min()
        )
    return frame


def _activity_feature(mechanic: str, lookback: int) -> str:
    prefixes = {
        "OPTIONS_OI_EXPANSION_BREAKOUT": "options_oi_growth_z",
        "OPTIONS_OI_CONTRACTION_REVERSAL": "options_oi_growth_z",
        "MM_OPTIONS_SPREAD_BUILD_BREAKOUT": "mm_spread_build_z",
        "SWAP_OPTIONS_SPREAD_BUILD_BREAKOUT": "swap_spread_build_z",
        "GROSS_OPTION_ACTIVITY_COMPRESSION_BREAKOUT": "gross_activity_level_z",
    }
    return f"{prefixes[mechanic]}_{lookback}"


def signal_mask_direction(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series]:
    activity = frame[_activity_feature(mechanic, int(params["lookback"]))]
    threshold = float(params["activity_threshold_z"])
    if mechanic == "OPTIONS_OI_CONTRACTION_REVERSAL":
        impulse = frame[f"impulse_{int(params['impulse_hours'])}_atr"]
        direction = pd.Series(-np.sign(impulse.fillna(0.0)).astype(int), index=frame.index)
        mask = (
            activity.le(-threshold)
            & impulse.abs().ge(float(params["impulse_min_atr"]))
            & (direction * frame["body_atr"]).ge(float(params["confirmation_min_atr"]))
            & direction.ne(0)
        )
    else:
        bars = int(params["channel_bars"])
        buffer = float(params["breakout_buffer_atr"]) * frame["atr14"]
        long_mask = frame["mid_close"].ge(frame[f"prior_high_{bars}"] + buffer)
        short_mask = frame["mid_close"].le(frame[f"prior_low_{bars}"] - buffer)
        direction = pd.Series(
            np.select([long_mask, short_mask], [1, -1], default=0).astype(int),
            index=frame.index,
        )
        mask = activity.ge(threshold) & direction.ne(0)
        mask &= frame["atr_ratio_causal"].le(float(params["compression_max"]))
    mask &= BASE._session_mask(frame, str(params["session"]))
    return mask.fillna(False), direction


def generate_manifest(
    frame: pd.DataFrame,
    discovery_start: pd.Timestamp,
    discovery_end: pd.Timestamp,
    attempts_before: int = 9093,
    policies_per_mechanic: int = 200,
    minimum_raw_signals: int = 120,
) -> pd.DataFrame:
    stage = frame["bar_end_utc"].ge(discovery_start) & frame["bar_end_utc"].lt(discovery_end)
    rows: list[dict[str, Any]] = []
    attempt = attempts_before
    for mechanic in MECHANICS:
        ranked = sorted(
            parameter_space(mechanic),
            key=lambda params: hashlib.sha256(
                f"{mechanic}|{json.dumps(params, sort_keys=True)}".encode("ascii")
            ).hexdigest(),
        )
        admitted = 0
        for params in ranked:
            mask, _ = signal_mask_direction(frame, mechanic, params)
            raw_signals = int((mask & stage).sum())
            if raw_signals < minimum_raw_signals:
                continue
            attempt += 1
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            rows.append(
                {
                    "attempt_no": attempt,
                    "policy_id": hashlib.sha256(
                        f"{mechanic}|{canonical}".encode("ascii")
                    ).hexdigest()[:16],
                    "mechanic": mechanic,
                    "raw_discovery_signal_count": raw_signals,
                    "parameters_json": canonical,
                }
            )
            admitted += 1
            if admitted == policies_per_mechanic:
                break
        if admitted != policies_per_mechanic:
            raise ValueError(
                f"Only {admitted} coverage-eligible V2 policies for {mechanic}; "
                f"required {policies_per_mechanic}"
            )
    manifest = pd.DataFrame(rows)
    if len(manifest) != len(MECHANICS) * policies_per_mechanic:
        raise ValueError("Invalid V2 policy count")
    if manifest["policy_id"].duplicated().any():
        raise ValueError("Duplicate V2 policy IDs")
    return manifest


def select_policy_trades(
    frame: pd.DataFrame,
    arrays: Mapping[str, Any],
    policy: Any,
    config: Mapping[str, Any],
    stage_start: pd.Timestamp,
    stage_end: pd.Timestamp,
    outcome_cache: dict[tuple[Any, ...], Any],
) -> pd.DataFrame:
    params = json.loads(policy.parameters_json)
    mechanic = str(policy.mechanic)
    mask, direction = signal_mask_direction(frame, mechanic, params)
    stage = frame["bar_end_utc"].ge(stage_start) & frame["bar_end_utc"].lt(stage_end)
    indices = np.flatnonzero((mask & stage).to_numpy())
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    report_count: dict[Any, int] = {}
    execution = config["execution"]
    cooldown = pd.Timedelta(hours=float(execution["cooldown_hours"]))
    feature_column = _activity_feature(mechanic, int(params["lookback"]))
    for index in indices:
        row = frame.iloc[int(index)]
        signal_time = pd.Timestamp(row["bar_end_utc"])
        signal_direction = int(direction.iat[int(index)])
        key = (
            int(signal_time.value),
            signal_direction,
            float(params["stop_atr"]),
            float(params["target_r"]),
            int(params["hold_hours"]),
        )
        outcome = outcome_cache.get(key, _MISSING)
        if outcome is _MISSING:
            outcome = BASE.simulate_trade(
                arrays,
                signal_time,
                float(row["atr14"]),
                signal_direction,
                params,
                execution,
                stage_end,
            )
            outcome_cache[key] = outcome
        if outcome is None:
            continue
        entry_time = outcome["entry_time"]
        report_date = pd.Timestamp(row["report_date"])
        if entry_time < position_until or entry_time < cooldown_until:
            continue
        day = entry_time.date()
        if daily_count.get(day, 0) >= int(execution["maximum_trades_per_policy_utc_day"]):
            continue
        if report_count.get(report_date, 0) >= int(execution["maximum_trades_per_policy_report"]):
            continue
        selected.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": mechanic,
                "report_date": report_date,
                "available_utc": pd.Timestamp(row["available_utc"]),
                "activity_feature": feature_column,
                "activity_feature_value": float(row[feature_column]),
                **outcome,
            }
        )
        position_until = outcome["exit_time"]
        cooldown_until = outcome["exit_time"] + cooldown
        daily_count[day] = daily_count.get(day, 0) + 1
        report_count[report_date] = report_count.get(report_date, 0) + 1
    if not selected:
        return pd.DataFrame()
    return pd.DataFrame(selected).sort_values("entry_time", kind="mergesort").reset_index(drop=True)


def evaluate_policies(
    frame: pd.DataFrame,
    m5: pd.DataFrame,
    manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
) -> tuple[pd.DataFrame, dict[tuple[Any, ...], Any]]:
    start, end = map(pd.Timestamp, config["windows"][stage])
    arrays = BASE.execution_arrays(m5)
    cache: dict[tuple[Any, ...], Any] = {}
    rows: list[dict[str, Any]] = []
    for policy in manifest.itertuples(index=False):
        trades = select_policy_trades(frame, arrays, policy, config, start, end, cache)
        values = BASE.summarize(
            trades,
            frame,
            start,
            end,
            config["segments"][stage],
            int(config["gates"][stage]["top_winners_removed"]),
        )
        rows.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": str(policy.mechanic),
                "raw_discovery_signal_count": int(policy.raw_discovery_signal_count),
                "parameters_json": str(policy.parameters_json),
                **values,
            }
        )
    metrics = pd.DataFrame(rows)
    metrics["fdr_qvalue"] = BASE.benjamini_hochberg(metrics["block_pvalue"])
    checks_list: list[dict[str, bool]] = []
    passes: list[bool] = []
    for row in metrics.to_dict(orient="records"):
        checks = BASE.gate_checks(row, config["gates"][stage])
        checks_list.append(checks)
        passes.append(all(checks.values()))
    metrics["gate_checks_json"] = [
        json.dumps(checks, sort_keys=True, separators=(",", ":"))
        for checks in checks_list
    ]
    metrics["gate_pass"] = passes
    return metrics, cache


def select_advancers(metrics: pd.DataFrame, gate: Mapping[str, Any]) -> pd.DataFrame:
    return BASE.select_advancers(metrics, gate)


def selected_trade_ledger(
    frame: pd.DataFrame,
    m5: pd.DataFrame,
    selected_manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
    cache: dict[tuple[Any, ...], Any] | None = None,
) -> pd.DataFrame:
    if selected_manifest.empty:
        return pd.DataFrame()
    start, end = map(pd.Timestamp, config["windows"][stage])
    arrays = BASE.execution_arrays(m5)
    outcome_cache = cache if cache is not None else {}
    frames: list[pd.DataFrame] = []
    for policy in selected_manifest.itertuples(index=False):
        trades = select_policy_trades(
            frame, arrays, policy, config, start, end, outcome_cache
        )
        if not trades.empty:
            frames.append(trades.assign(stage=stage))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
