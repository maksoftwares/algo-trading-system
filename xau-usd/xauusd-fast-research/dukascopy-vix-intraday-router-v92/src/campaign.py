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
MECHANICS = (
    "VIX_SHOCK_BREAKOUT",
    "VIX_SAFE_HAVEN_CATCHUP",
    "VIX_DIVERGENCE_REJECTION",
    "VIX_NORMALIZATION_TREND",
    "VIX_XAU_COEXPANSION",
)
SESSIONS = ("BOTH", "LONDON", "NY")
_MISSING = object()


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V89 = _load_module(
    "dukascopy_vix_v92_v89_metrics",
    RESEARCH_ROOT / "cboe-gvz-routed-intraday-v89" / "src" / "campaign.py",
)
BASE = V89.BASE
summarize = V89.summarize
benjamini_hochberg = V89.benjamini_hochberg
gate_checks = V89.gate_checks
select_advancers = V89.select_advancers


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    common = {
        "lookback": (24, 72, 120),
        "state_threshold_z": (0.0, 0.5, 1.0, 1.5),
        "minimum_active_m5": (3, 6, 9),
        "maximum_vix_staleness_minutes": (15,),
        "session": SESSIONS,
        "stop_atr": (0.6, 0.8, 1.0, 1.25),
        "target_r": (1.0, 1.25, 1.5, 2.0),
        "hold_hours": (2, 4, 6, 8),
    }
    if mechanic in {"VIX_SHOCK_BREAKOUT", "VIX_XAU_COEXPANSION"}:
        return _space(
            **common,
            channel_bars=(3, 6, 12, 24),
            breakout_buffer_atr=(0.0, 0.05, 0.10),
            impulse_hours=(3,),
            impulse_min_atr=(0.0,),
            confirmation_min_atr=(0.0,),
        )
    return _space(
        **common,
        channel_bars=(6,),
        breakout_buffer_atr=(0.0,),
        impulse_hours=(3, 6, 12),
        impulse_min_atr=(0.20, 0.40, 0.70, 1.0),
        confirmation_min_atr=(0.0, 0.10, 0.20, 0.35),
    )


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


def prepare_vix_h1(vix_m5: pd.DataFrame, lookbacks: Iterable[int]) -> pd.DataFrame:
    required = {
        "bar_open_timestamp_ms",
        "available_timestamp_ms",
        "source_last_timestamp_ms",
        "vol_mid_open",
        "vol_mid_high",
        "vol_mid_low",
        "vol_mid_close",
        "vol_tick_count",
        "vol_spread_mean",
    }
    missing = sorted(required.difference(vix_m5.columns))
    if missing:
        raise ValueError(f"VIX M5 source is missing columns: {missing}")
    frame = vix_m5.copy()
    frame["bar_open_utc"] = pd.to_datetime(
        frame["bar_open_timestamp_ms"], unit="ms", utc=True
    )
    frame["available_utc"] = pd.to_datetime(
        frame["available_timestamp_ms"], unit="ms", utc=True
    )
    frame["h1_open_utc"] = frame["bar_open_utc"].dt.floor("h")
    grouped = frame.groupby("h1_open_utc", sort=True, observed=True)
    result = grouped.agg(
        vix_mid_open=("vol_mid_open", "first"),
        vix_mid_high=("vol_mid_high", "max"),
        vix_mid_low=("vol_mid_low", "min"),
        vix_mid_close=("vol_mid_close", "last"),
        vix_tick_count=("vol_tick_count", "sum"),
        vix_active_m5=("bar_open_timestamp_ms", "size"),
        vix_spread_mean=("vol_spread_mean", "mean"),
        source_last_available_utc=("available_utc", "max"),
    ).reset_index()
    result["bar_end_utc"] = result["h1_open_utc"] + pd.Timedelta(hours=1)
    if (result["source_last_available_utc"] > result["bar_end_utc"]).any():
        raise ValueError("Future VIX M5 bar entered completed H1 state")
    result["vix_staleness_minutes"] = (
        result["bar_end_utc"] - result["source_last_available_utc"]
    ).dt.total_seconds() / 60.0

    log_close = np.log(result["vix_mid_close"].where(result["vix_mid_close"].gt(0)))
    for hours in (1, 4, 12):
        contiguous = result["h1_open_utc"].diff(hours).eq(pd.Timedelta(hours=hours))
        result[f"vix_return_{hours}h"] = log_close.diff(hours).where(contiguous)
    result["vix_abs_return_1h"] = result["vix_return_1h"].abs()
    for lookback in map(int, lookbacks):
        result[f"vix_return_z_{lookback}"] = _causal_z(
            result["vix_return_1h"], lookback
        )
        result[f"vix_abs_return_z_{lookback}"] = _causal_z(
            result["vix_abs_return_1h"], lookback
        )
        result[f"vix_level_z_{lookback}"] = _causal_z(log_close, lookback)
    return result


def prepare_features(
    h1: pd.DataFrame, vix_m5: pd.DataFrame, config: Mapping[str, Any]
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
    features = config["features"]
    frame = (
        h1.copy().sort_values("bar_end_utc", kind="mergesort").reset_index(drop=True)
    )
    frame["atr14"] = _atr(frame, int(features["h1_atr_period"]))
    scale = frame["atr14"].replace(0.0, np.nan)
    frame["body_atr"] = (frame["mid_close"] - frame["mid_open"]) / scale
    frame["hour_utc"] = frame["bar_end_utc"].dt.hour
    frame["session_slot"] = np.select(
        [
            frame["hour_utc"].ge(7) & frame["hour_utc"].lt(12),
            frame["hour_utc"].ge(13) & frame["hour_utc"].lt(18),
        ],
        ["LONDON", "NY"],
        default="OUTSIDE",
    )
    for bars in (3, 6, 12, 24):
        frame[f"impulse_{bars}_atr"] = (
            frame["mid_close"] - frame["mid_close"].shift(bars)
        ) / scale
        frame[f"prior_high_{bars}"] = (
            frame["mid_high"].shift(1).rolling(bars, min_periods=bars).max()
        )
        frame[f"prior_low_{bars}"] = (
            frame["mid_low"].shift(1).rolling(bars, min_periods=bars).min()
        )

    vix_h1 = prepare_vix_h1(vix_m5, features["vix_lookbacks"])
    frame = frame.merge(
        vix_h1.drop(columns=["h1_open_utc"]),
        on="bar_end_utc",
        how="left",
        validate="one_to_one",
    )
    observed = frame["source_last_available_utc"].notna()
    if (
        frame.loc[observed, "source_last_available_utc"]
        > frame.loc[observed, "bar_end_utc"]
    ).any():
        raise ValueError("Future VIX state joined to XAU decision")
    return frame


def _session_mask(frame: pd.DataFrame, session: str) -> pd.Series:
    if session == "BOTH":
        return frame["session_slot"].isin(("LONDON", "NY"))
    if session not in {"LONDON", "NY"}:
        raise KeyError(session)
    return frame["session_slot"].eq(session)


def signal_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series]:
    lookback = int(params["lookback"])
    threshold = float(params["state_threshold_z"])
    impulse = frame[f"impulse_{int(params['impulse_hours'])}_atr"]
    state_direction = pd.Series(
        np.sign(frame["vix_return_1h"].fillna(0.0)).astype(int), index=frame.index
    )
    bars = int(params["channel_bars"])
    buffer = float(params["breakout_buffer_atr"]) * frame["atr14"]
    long_break = frame["mid_close"].ge(frame[f"prior_high_{bars}"] + buffer)
    short_break = frame["mid_close"].le(frame[f"prior_low_{bars}"] - buffer)
    breakout_direction = pd.Series(
        np.select([long_break, short_break], [1, -1], default=0).astype(int),
        index=frame.index,
    )

    if mechanic == "VIX_SHOCK_BREAKOUT":
        state = frame[f"vix_return_z_{lookback}"].abs()
        direction = breakout_direction
        mask = state.ge(threshold) & direction.ne(0)
    elif mechanic == "VIX_SAFE_HAVEN_CATCHUP":
        state = frame[f"vix_return_z_{lookback}"].abs()
        direction = state_direction
        mask = state.ge(threshold) & direction.ne(0)
        mask &= (direction * impulse).le(float(params["impulse_min_atr"]))
        mask &= (direction * frame["body_atr"]).ge(
            float(params["confirmation_min_atr"])
        )
    elif mechanic == "VIX_DIVERGENCE_REJECTION":
        state = frame[f"vix_return_z_{lookback}"].abs()
        direction = state_direction
        mask = state.ge(threshold) & direction.ne(0)
        mask &= (direction * impulse).le(-float(params["impulse_min_atr"]))
        mask &= (direction * frame["body_atr"]).ge(
            float(params["confirmation_min_atr"])
        )
    elif mechanic == "VIX_NORMALIZATION_TREND":
        state = frame[f"vix_level_z_{lookback}"]
        direction = pd.Series(
            np.sign(impulse.fillna(0.0)).astype(int), index=frame.index
        )
        mask = state.ge(threshold) & frame["vix_return_1h"].lt(0.0)
        mask &= impulse.abs().ge(float(params["impulse_min_atr"]))
        mask &= (direction * frame["body_atr"]).ge(
            float(params["confirmation_min_atr"])
        )
        mask &= direction.ne(0)
    elif mechanic == "VIX_XAU_COEXPANSION":
        state = frame[f"vix_abs_return_z_{lookback}"]
        direction = breakout_direction
        mask = state.ge(threshold) & direction.ne(0)
    else:
        raise KeyError(mechanic)
    mask &= frame["vix_active_m5"].ge(int(params["minimum_active_m5"]))
    mask &= frame["vix_staleness_minutes"].le(
        float(params["maximum_vix_staleness_minutes"])
    )
    mask &= _session_mask(frame, str(params["session"]))
    return mask.fillna(False), direction


def generate_manifest(
    frame: pd.DataFrame,
    discovery_start: pd.Timestamp,
    discovery_end: pd.Timestamp,
    attempt_first: int,
    policies_per_mechanic: int,
    minimum_raw_signals: int,
) -> pd.DataFrame:
    stage = frame["bar_end_utc"].ge(discovery_start) & frame["bar_end_utc"].lt(
        discovery_end
    )
    rows: list[dict[str, Any]] = []
    attempt = attempt_first - 1
    for mechanic in MECHANICS:
        ranked = sorted(
            parameter_space(mechanic),
            key=lambda params: hashlib.sha256(
                f"{mechanic}|{json.dumps(params, sort_keys=True)}".encode("ascii")
            ).hexdigest(),
        )
        admitted = 0
        for params in ranked:
            mask, direction = signal_mask_direction(frame, mechanic, params)
            selected = mask & stage
            raw_signals = int(selected.sum())
            if raw_signals < minimum_raw_signals:
                continue
            long_signals = int((selected & direction.gt(0)).sum())
            short_signals = int((selected & direction.lt(0)).sum())
            if min(long_signals, short_signals) < max(30, minimum_raw_signals // 10):
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
                    "raw_discovery_long_count": long_signals,
                    "raw_discovery_short_count": short_signals,
                    "parameters_json": canonical,
                }
            )
            admitted += 1
            if admitted == policies_per_mechanic:
                break
        if admitted != policies_per_mechanic:
            raise ValueError(
                f"Only {admitted} coverage-eligible V92 policies for {mechanic}; "
                f"required {policies_per_mechanic}"
            )
    manifest = pd.DataFrame(rows)
    expected = len(MECHANICS) * policies_per_mechanic
    if len(manifest) != expected or manifest["policy_id"].duplicated().any():
        raise ValueError("Invalid V92 policy manifest")
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
    slot_count: dict[tuple[Any, str], int] = {}
    execution = config["execution"]
    cooldown = pd.Timedelta(hours=float(execution["cooldown_hours"]))
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
        entry_time = pd.Timestamp(outcome["entry_time"])
        if entry_time < position_until or entry_time < cooldown_until:
            continue
        day = entry_time.date()
        slot = str(row["session_slot"])
        if daily_count.get(day, 0) >= int(
            execution["maximum_trades_per_policy_utc_day"]
        ):
            continue
        if slot_count.get((day, slot), 0) >= int(
            execution["maximum_trades_per_session_slot"]
        ):
            continue
        selected.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": mechanic,
                "vix_source_available_utc": pd.Timestamp(
                    row["source_last_available_utc"]
                ),
                "vix_mid_close": float(row["vix_mid_close"]),
                "vix_active_m5": int(row["vix_active_m5"]),
                "session_slot": slot,
                **outcome,
            }
        )
        position_until = pd.Timestamp(outcome["exit_time"])
        cooldown_until = position_until + cooldown
        daily_count[day] = daily_count.get(day, 0) + 1
        slot_count[(day, slot)] = slot_count.get((day, slot), 0) + 1
    if not selected:
        return pd.DataFrame()
    return (
        pd.DataFrame(selected)
        .sort_values("entry_time", kind="mergesort")
        .reset_index(drop=True)
    )


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
        rows.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": str(policy.mechanic),
                "parameters_json": str(policy.parameters_json),
                **summarize(
                    trades,
                    start,
                    end,
                    config["segments"][stage],
                    int(config["gates"][stage]["top_winners_removed"]),
                ),
            }
        )
    metrics = pd.DataFrame(rows)
    metrics["fdr_qvalue"] = benjamini_hochberg(metrics["block_pvalue"])
    checks: list[dict[str, bool]] = []
    passes: list[bool] = []
    for row in metrics.to_dict(orient="records"):
        values = gate_checks(row, config["gates"][stage])
        checks.append(values)
        passes.append(all(values.values()))
    metrics["gate_checks_json"] = [
        json.dumps(value, sort_keys=True, separators=(",", ":")) for value in checks
    ]
    metrics["gate_pass"] = passes
    return metrics, cache


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
    frames = []
    for policy in selected_manifest.itertuples(index=False):
        trades = select_policy_trades(
            frame, arrays, policy, config, start, end, outcome_cache
        )
        if not trades.empty:
            frames.append(trades.assign(stage=stage))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
