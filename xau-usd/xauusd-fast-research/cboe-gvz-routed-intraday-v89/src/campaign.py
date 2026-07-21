from __future__ import annotations

import hashlib
import importlib.util
from itertools import product
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent
MECHANICS = (
    "GVZ_HIGH_BREAKOUT",
    "GVZ_RISING_BREAKOUT",
    "GVZ_LOW_REVERSION",
    "GVZ_FALLING_REVERSION",
    "GVZ_PREMIUM_EXPANSION",
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


BASE = _load_module(
    "cboe_gvz_v89_base_simulator",
    RESEARCH_ROOT / "cftc-options-positioning-mechanics-v1" / "src" / "campaign.py",
)


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    common = {
        "lookback": (20, 60, 120),
        "state_threshold_z": (0.0, 0.5, 1.0, 1.5),
        "session": SESSIONS,
        "stop_atr": (0.6, 0.8, 1.0, 1.25),
        "target_r": (1.0, 1.25, 1.5, 2.0),
        "hold_hours": (2, 4, 6, 8),
    }
    if mechanic in {
        "GVZ_HIGH_BREAKOUT",
        "GVZ_RISING_BREAKOUT",
        "GVZ_PREMIUM_EXPANSION",
    }:
        return _space(
            **common,
            channel_bars=(3, 6, 12, 24),
            breakout_buffer_atr=(0.0, 0.05, 0.10),
            compression_max=(0.85, 1.0, 1.25, 99.0),
            impulse_hours=(6,),
            impulse_min_atr=(0.0,),
            confirmation_min_atr=(0.0,),
        )
    if mechanic in {"GVZ_LOW_REVERSION", "GVZ_FALLING_REVERSION"}:
        return _space(
            **common,
            channel_bars=(6,),
            breakout_buffer_atr=(0.0,),
            compression_max=(99.0,),
            impulse_hours=(3, 6, 12, 24),
            impulse_min_atr=(0.35, 0.6, 1.0, 1.5),
            confirmation_min_atr=(0.0, 0.10, 0.25, 0.40),
        )
    raise KeyError(mechanic)


def _causal_z(values: pd.Series, lookback: int) -> pd.Series:
    prior = values.shift(1).rolling(lookback, min_periods=lookback)
    return (values - prior.mean()) / prior.std(ddof=0).replace(0.0, np.nan)


def load_gvz(path: Path, availability_lag_days: int) -> pd.DataFrame:
    raw = pd.read_csv(path)
    if list(raw.columns) != ["DATE", "GVZ"]:
        raise ValueError("Unexpected Cboe GVZ schema")
    frame = raw.rename(columns={"DATE": "gvz_date", "GVZ": "gvz"}).copy()
    frame["gvz_date"] = pd.to_datetime(frame["gvz_date"], format="%m/%d/%Y")
    frame["gvz"] = pd.to_numeric(frame["gvz"], errors="raise")
    if frame["gvz_date"].duplicated().any() or frame["gvz"].isna().any():
        raise ValueError("Duplicate or missing Cboe GVZ observation")
    if not frame["gvz_date"].is_monotonic_increasing:
        raise ValueError("Cboe GVZ dates are not ordered")
    frame["available_utc"] = (
        frame["gvz_date"] + pd.Timedelta(days=int(availability_lag_days))
    ).dt.tz_localize("UTC")
    if (frame["available_utc"].dt.date <= frame["gvz_date"].dt.date).any():
        raise ValueError("Same-day Cboe GVZ use is forbidden")
    return frame


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
    return true_range.ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()


def prepare_features(
    h1: pd.DataFrame, gvz: pd.DataFrame, config: Mapping[str, Any]
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
    daily = gvz.copy().sort_values("available_utc", kind="mergesort")
    daily["gvz_change"] = daily["gvz"].diff()
    for lookback in map(int, features["gvz_lookbacks"]):
        daily[f"gvz_level_z_{lookback}"] = _causal_z(daily["gvz"], lookback)
        daily[f"gvz_change_z_{lookback}"] = _causal_z(
            daily["gvz_change"], lookback
        )

    frame = h1.copy().sort_values("bar_end_utc", kind="mergesort").reset_index(drop=True)
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

    baseline = frame["atr14"].shift(1).rolling(
        int(features["intraday_baseline_hours"]),
        min_periods=int(features["intraday_baseline_minimum_hours"]),
    )
    frame["atr_ratio_causal"] = frame["atr14"] / baseline.median().replace(
        0.0, np.nan
    )
    log_return = np.log(
        frame["mid_close"] / frame["mid_close"].shift(1)
    ).replace([np.inf, -np.inf], np.nan)
    realized = log_return.rolling(
        int(features["realized_volatility_hours"]),
        min_periods=int(features["realized_volatility_minimum_hours"]),
    ).std(ddof=0) * math.sqrt(24.0 * 252.0)
    frame["realized_volatility"] = realized

    daily_columns = [
        "gvz_date",
        "available_utc",
        "gvz",
        *[
            f"{prefix}_{lookback}"
            for lookback in map(int, features["gvz_lookbacks"])
            for prefix in ("gvz_level_z", "gvz_change_z")
        ],
    ]
    frame = pd.merge_asof(
        frame,
        daily[daily_columns],
        left_on="bar_end_utc",
        right_on="available_utc",
        direction="backward",
        tolerance=pd.Timedelta(days=float(features["maximum_gvz_staleness_days"])),
    )
    observed = frame["available_utc"].notna()
    if (frame.loc[observed, "available_utc"] > frame.loc[observed, "bar_end_utc"]).any():
        raise ValueError("Future Cboe GVZ close joined to H1 decision")
    if (
        frame.loc[observed, "gvz_date"].dt.date
        >= frame.loc[observed, "bar_end_utc"].dt.date
    ).any():
        raise ValueError("Same-date Cboe GVZ close joined to XAU decision")

    frame["implied_realized_premium"] = frame["gvz"] / 100.0 - frame[
        "realized_volatility"
    ]
    for lookback in map(int, features["gvz_lookbacks"]):
        hours = lookback * 24
        prior = frame["implied_realized_premium"].shift(1).rolling(
            hours, min_periods=min(hours, max(24, hours // 2))
        )
        frame[f"gvz_premium_z_{lookback}"] = (
            frame["implied_realized_premium"] - prior.mean()
        ) / prior.std(ddof=0).replace(0.0, np.nan)
    return frame


def _state_feature(mechanic: str, lookback: int) -> str:
    if mechanic in {"GVZ_HIGH_BREAKOUT", "GVZ_LOW_REVERSION"}:
        return f"gvz_level_z_{lookback}"
    if mechanic in {"GVZ_RISING_BREAKOUT", "GVZ_FALLING_REVERSION"}:
        return f"gvz_change_z_{lookback}"
    if mechanic == "GVZ_PREMIUM_EXPANSION":
        return f"gvz_premium_z_{lookback}"
    raise KeyError(mechanic)


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
    state = frame[_state_feature(mechanic, lookback)]
    threshold = float(params["state_threshold_z"])
    if mechanic in {"GVZ_LOW_REVERSION", "GVZ_FALLING_REVERSION"}:
        impulse = frame[f"impulse_{int(params['impulse_hours'])}_atr"]
        direction = pd.Series(
            -np.sign(impulse.fillna(0.0)).astype(int), index=frame.index
        )
        mask = state.le(-threshold)
        mask &= impulse.abs().ge(float(params["impulse_min_atr"]))
        mask &= (direction * frame["body_atr"]).ge(
            float(params["confirmation_min_atr"])
        )
        mask &= direction.ne(0)
    else:
        bars = int(params["channel_bars"])
        buffer = float(params["breakout_buffer_atr"]) * frame["atr14"]
        long_mask = frame["mid_close"].ge(frame[f"prior_high_{bars}"] + buffer)
        short_mask = frame["mid_close"].le(frame[f"prior_low_{bars}"] - buffer)
        direction = pd.Series(
            np.select([long_mask, short_mask], [1, -1], default=0).astype(int),
            index=frame.index,
        )
        mask = state.ge(threshold) & direction.ne(0)
        mask &= frame["atr_ratio_causal"].le(float(params["compression_max"]))
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
            if min(long_signals, short_signals) < max(20, minimum_raw_signals // 10):
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
                f"Only {admitted} coverage-eligible V89 policies for {mechanic}; "
                f"required {policies_per_mechanic}"
            )
    manifest = pd.DataFrame(rows)
    expected = len(MECHANICS) * policies_per_mechanic
    if len(manifest) != expected or manifest["policy_id"].duplicated().any():
        raise ValueError("Invalid V89 policy manifest")
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
    state_column = _state_feature(mechanic, int(params["lookback"]))
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
                "gvz_date": pd.Timestamp(row["gvz_date"]),
                "gvz_available_utc": pd.Timestamp(row["available_utc"]),
                "gvz": float(row["gvz"]),
                "gvz_state_feature": state_column,
                "gvz_state_value": float(row[state_column]),
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
    return pd.DataFrame(selected).sort_values(
        "entry_time", kind="mergesort"
    ).reset_index(drop=True)


def _profit_factor(values: pd.Series) -> float | None:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return None if gains == 0.0 else float("inf")
    return gains / losses


def _closed_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(([0.0], values.fillna(0.0).to_numpy(dtype=float).cumsum()))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity)) if len(equity) else 0.0


def _calendar_weekdays(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(
        np.busday_count(
            np.datetime64(start.date()), np.datetime64(end.date())
        )
    )


def _weekly_pvalue(
    trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> float:
    days = pd.date_range(start.normalize(), end.normalize(), inclusive="left", freq="B")
    blocks = pd.Index(days.tz_localize(None).to_period("W-SUN").unique())
    if trades.empty:
        values = np.zeros(len(blocks), dtype=float)
    else:
        observed = trades.groupby(
            trades["entry_time"].dt.tz_localize(None).dt.to_period("W-SUN")
        )["stress_net_r"].sum()
        values = observed.reindex(blocks, fill_value=0.0).to_numpy(dtype=float)
    if len(values) == 0 or float(values.mean()) <= 0.0:
        return 1.0
    standard = float(values.std(ddof=1)) if len(values) > 1 else 0.0
    if standard == 0.0:
        return 0.0
    result = stats.ttest_1samp(values, popmean=0.0, alternative="greater")
    return float(result.pvalue) if np.isfinite(result.pvalue) else 1.0


def summarize(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    segments: list[list[str]],
    top_winners: int,
) -> dict[str, Any]:
    values = (
        trades["stress_net_r"].astype(float)
        if not trades.empty
        else pd.Series(dtype=float)
    )
    weekdays = _calendar_weekdays(start, end)
    months = pd.period_range(
        start.tz_localize(None).to_period("M"),
        (end - pd.Timedelta(nanoseconds=1)).tz_localize(None).to_period("M"),
        freq="M",
    )
    if trades.empty:
        monthly = pd.Series(0.0, index=months)
    else:
        observed = trades.groupby(
            trades["entry_time"].dt.tz_localize(None).dt.to_period("M")
        )["stress_net_r"].sum()
        monthly = observed.reindex(months, fill_value=0.0)
    removed = (
        values.drop(values.nlargest(min(top_winners, len(values))).index)
        if len(values)
        else values
    )
    segment_metrics: list[dict[str, Any]] = []
    for raw_start, raw_end in segments:
        segment_start, segment_end = pd.Timestamp(raw_start), pd.Timestamp(raw_end)
        segment = (
            trades.loc[
                trades["entry_time"].ge(segment_start)
                & trades["entry_time"].lt(segment_end)
            ]
            if not trades.empty
            else trades
        )
        segment_values = (
            segment["stress_net_r"].astype(float)
            if not segment.empty
            else pd.Series(dtype=float)
        )
        segment_metrics.append(
            {
                "start": segment_start.isoformat(),
                "end": segment_end.isoformat(),
                "trades": int(len(segment)),
                "net_r": float(segment_values.sum()),
                "stress_pf": _profit_factor(segment_values),
                "profitable": bool(segment_values.sum() > 0.0),
            }
        )
    finite_pfs = [
        float(item["stress_pf"])
        if item["stress_pf"] is not None
        and math.isfinite(float(item["stress_pf"]))
        else (float("inf") if item["net_r"] > 0.0 else 0.0)
        for item in segment_metrics
    ]
    return {
        "trades": int(len(trades)),
        "calendar_weekdays": weekdays,
        "trades_per_source_day": len(trades) / weekdays if weekdays else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": _profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "positive_month_share": float((monthly > 0.0).mean()) if len(monthly) else 0.0,
        "closed_drawdown_r": _closed_drawdown(values),
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "block_pvalue": _weekly_pvalue(trades, start, end),
        "profitable_segments": int(sum(item["profitable"] for item in segment_metrics)),
        "worst_segment_pf": float(min(finite_pfs)) if finite_pfs else 0.0,
        "segment_metrics": segment_metrics,
        "current_account_feasible_share": (
            float(trades["current_account_feasible"].mean())
            if not trades.empty
            else 0.0
        ),
        "long_trades": (
            int(trades["direction"].eq("LONG").sum()) if not trades.empty else 0
        ),
        "short_trades": (
            int(trades["direction"].eq("SHORT").sum()) if not trades.empty else 0
        ),
    }


def benjamini_hochberg(pvalues: pd.Series) -> pd.Series:
    values = pvalues.fillna(1.0).clip(0.0, 1.0).to_numpy(dtype=float)
    count = len(values)
    if count == 0:
        return pd.Series(dtype=float, index=pvalues.index)
    order = np.argsort(values, kind="mergesort")
    ranked = values[order] * count / np.arange(1, count + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1]
    result = np.empty(count, dtype=float)
    result[order] = np.minimum(adjusted, 1.0)
    return pd.Series(result, index=pvalues.index)


def gate_checks(metrics: Mapping[str, Any], gate: Mapping[str, Any]) -> dict[str, bool]:
    pf = metrics["stress_pf"]
    return {
        "minimum_trades": int(metrics["trades"]) >= int(gate["minimum_trades"]),
        "minimum_trades_per_source_day": float(metrics["trades_per_source_day"])
        >= float(gate["minimum_trades_per_source_day"]),
        "minimum_stress_pf": pf is not None
        and float(pf) >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": float(metrics["average_stress_r"])
        >= float(gate["minimum_average_stress_r"]),
        "minimum_positive_month_share": float(metrics["positive_month_share"])
        >= float(gate["minimum_positive_month_share"]),
        "maximum_closed_drawdown_r": float(metrics["closed_drawdown_r"])
        <= float(gate["maximum_closed_drawdown_r"]),
        "top_winners_removed_positive": float(
            metrics["top_winners_removed_stress_net_r"]
        )
        > 0.0,
        "minimum_profitable_segments": int(metrics["profitable_segments"])
        >= int(gate["minimum_profitable_segments"]),
        "minimum_worst_segment_pf": float(metrics["worst_segment_pf"])
        >= float(gate["minimum_worst_segment_pf"]),
        "maximum_fdr_qvalue": float(metrics["fdr_qvalue"])
        <= float(gate["maximum_fdr_qvalue"]),
    }


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
        trades = select_policy_trades(
            frame, arrays, policy, config, start, end, cache
        )
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
        json.dumps(value, sort_keys=True, separators=(",", ":"))
        for value in checks
    ]
    metrics["gate_pass"] = passes
    return metrics, cache


def select_advancers(metrics: pd.DataFrame, gate: Mapping[str, Any]) -> pd.DataFrame:
    eligible = metrics.loc[metrics["gate_pass"]].copy()
    if eligible.empty:
        return eligible
    eligible = eligible.sort_values(
        ["mechanic", "fdr_qvalue", "worst_segment_pf", "average_stress_r", "policy_id"],
        ascending=[True, True, False, False, True],
        kind="mergesort",
    )
    return (
        eligible.groupby("mechanic", sort=True, observed=True)
        .head(int(gate.get("maximum_advancers_per_mechanic", 1)))
        .reset_index(drop=True)
    )


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
