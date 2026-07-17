from __future__ import annotations

import hashlib
from itertools import product
import json
import math
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
from scipy import stats


MECHANICS = (
    "FLOW_CONTINUATION",
    "FLOW_EXHAUSTION",
    "BOOK_ABSORPTION",
    "LIQUIDITY_SHOCK_REVERSION",
    "POST_SHOCK_NORMALIZATION",
)
SESSIONS = ("ALL", "ASIA", "LONDON", "NY", "LATE")
_MISSING = object()


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    if mechanic == "FLOW_CONTINUATION":
        return _space(
            imbalance_window=("5m", "15m"),
            imbalance_min=(0.015, 0.025, 0.035, 0.05, 0.07),
            book_min=(0.0, 0.03, 0.06, 0.10),
            intensity_min=(0.3, 0.5, 0.7, 1.0),
            efficiency_min=(0.0, 0.015, 0.035),
            spread_ratio_max=(1.15, 1.30, 1.50),
            require_body_alignment=(False, True),
            require_trend_alignment=(False, True),
            session=SESSIONS,
        )
    if mechanic == "FLOW_EXHAUSTION":
        return _space(
            impulse_bars=(1, 3, 6, 12),
            impulse_atr_min=(0.2, 0.35, 0.55, 0.8),
            impulse_tick_min=(0.005, 0.015, 0.03),
            reversal_book_min=(0.0, 0.03, 0.06),
            reversal_location_min=(0.35, 0.45, 0.55),
            intensity_min=(0.3, 0.5, 0.8, 1.1),
            session=SESSIONS,
        )
    if mechanic == "BOOK_ABSORPTION":
        return _space(
            price_window=(1, 3, 6),
            move_atr_min=(0.2, 0.4, 0.6, 0.9),
            reversal_book_min=(0.08, 0.16, 0.24, 0.32),
            price_tick_min=(0.0, 0.03, 0.06),
            efficiency_max=(0.3, 0.5, 0.7, 1.0),
            intensity_min=(0.6, 1.0, 1.4),
            session=SESSIONS,
        )
    if mechanic == "LIQUIDITY_SHOCK_REVERSION":
        return _space(
            impulse_bars=(1, 3),
            move_atr_min=(0.25, 0.4, 0.6, 0.9),
            spread_ratio_min=(1.0, 1.05, 1.15, 1.30),
            variance_ratio_min=(0.6, 0.9, 1.2, 1.6),
            intensity_min=(0.3, 0.5, 0.8, 1.1),
            reversal_location_min=(0.25, 0.40, 0.55),
            session=SESSIONS,
        )
    if mechanic == "POST_SHOCK_NORMALIZATION":
        return _space(
            prior_spread_ratio_min=(1.02, 1.08, 1.15, 1.30),
            current_spread_ratio_max=(1.0, 1.10, 1.25, 1.50),
            imbalance_min=(0.005, 0.015, 0.03, 0.05),
            book_min=(0.0, 0.03, 0.06),
            intensity_min=(0.3, 0.5, 0.8),
            require_body_alignment=(False, True),
            session=SESSIONS,
        )
    raise KeyError(mechanic)


def generate_manifest(
    attempts_before: int = 6093,
    policies_per_mechanic: int = 200,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    attempt = attempts_before
    for mechanic in MECHANICS:
        candidates = parameter_space(mechanic)
        ranked = sorted(
            candidates,
            key=lambda params: hashlib.sha256(
                f"{mechanic}|{json.dumps(params, sort_keys=True)}".encode("ascii")
            ).hexdigest(),
        )
        if len(ranked) < policies_per_mechanic:
            raise ValueError(f"Insufficient parameter space for {mechanic}")
        for params in ranked[:policies_per_mechanic]:
            attempt += 1
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
            policy_id = hashlib.sha256(
                f"{mechanic}|{canonical}".encode("ascii")
            ).hexdigest()[:16]
            rows.append(
                {
                    "attempt_no": attempt,
                    "policy_id": policy_id,
                    "mechanic": mechanic,
                    "parameters_json": canonical,
                }
            )
    manifest = pd.DataFrame(rows)
    expected = len(MECHANICS) * policies_per_mechanic
    if len(manifest) != expected:
        raise ValueError(f"Expected {expected} policies, generated {len(manifest)}")
    if manifest["policy_id"].duplicated().any():
        raise ValueError("Duplicate policy IDs")
    return manifest


def wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["mid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["mid_high"] - frame["mid_low"],
            (frame["mid_high"] - previous).abs(),
            (frame["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return wilder(true_range, period)


def prepare_features(m5: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    required = {
        "bar_start_utc",
        "bar_end_utc",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
        "tick_signed_move",
        "tick_realized_variance",
        "tick_spread_last",
        "tick_book_imbalance_mean",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "price_efficiency_5m",
        "quote_intensity_ratio",
    }
    missing = sorted(required.difference(m5.columns))
    if missing:
        raise ValueError(f"M5 cache is missing microstructure columns: {missing}")
    frame = m5.copy().sort_values("bar_start_utc", kind="mergesort").reset_index(drop=True)
    feature_config = config["features"]
    frame["atr14"] = atr(frame, int(feature_config["atr_period"]))
    for bars in (1, 3, 6, 12):
        frame[f"return_{bars}"] = frame["mid_close"].diff(bars)
    span = (frame["mid_high"] - frame["mid_low"]).replace(0.0, np.nan)
    frame["body_move"] = frame["mid_close"] - frame["mid_open"]
    frame["body_fraction_custom"] = frame["body_move"].abs() / span
    frame["close_location_custom"] = (frame["mid_close"] - frame["mid_low"]) / span
    baseline_bars = int(feature_config["baseline_bars"])
    minimum = int(feature_config["baseline_minimum_bars"])
    spread_baseline = (
        frame["tick_spread_last"].shift(1).rolling(baseline_bars, min_periods=minimum).median()
    )
    variance_baseline = (
        frame["tick_realized_variance"].shift(1).rolling(baseline_bars, min_periods=minimum).median()
    )
    frame["spread_ratio"] = frame["tick_spread_last"] / spread_baseline.replace(0.0, np.nan)
    frame["prior_spread_ratio"] = frame["spread_ratio"].shift(1)
    frame["variance_ratio"] = (
        frame["tick_realized_variance"] / variance_baseline.replace(0.0, np.nan)
    )
    frame["hour_utc_custom"] = frame["bar_end_utc"].dt.hour
    return frame


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


def _signed_location(frame: pd.DataFrame, direction: pd.Series) -> pd.Series:
    return pd.Series(
        np.where(
            direction > 0,
            frame["close_location_custom"],
            1.0 - frame["close_location_custom"],
        ),
        index=frame.index,
    )


def signal_mask_direction(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series]:
    atr_value = frame["atr14"].replace(0.0, np.nan)
    session = _session_mask(frame, str(params["session"]))
    if mechanic == "FLOW_CONTINUATION":
        imbalance = frame[f"tick_imbalance_{params['imbalance_window']}"]
        direction = pd.Series(
            np.sign(imbalance.fillna(0.0)).astype(int), index=frame.index
        )
        mask = (
            imbalance.abs().ge(float(params["imbalance_min"]))
            & (direction * frame["tick_book_imbalance_mean"]).ge(float(params["book_min"]))
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
            & frame["price_efficiency_5m"].ge(float(params["efficiency_min"]))
            & frame["spread_ratio"].le(float(params["spread_ratio_max"]))
        )
        if bool(params["require_body_alignment"]):
            mask &= (direction * frame["body_move"]).gt(0.0)
        if bool(params["require_trend_alignment"]):
            mask &= (direction * frame["return_12"]).gt(0.0)
    elif mechanic == "FLOW_EXHAUSTION":
        impulse = frame[f"return_{int(params['impulse_bars'])}"]
        impulse_direction = pd.Series(
            np.sign(impulse.fillna(0.0)).astype(int), index=frame.index
        )
        direction = -impulse_direction
        reversal_location = _signed_location(frame, direction)
        mask = (
            (impulse.abs() / atr_value).ge(float(params["impulse_atr_min"]))
            & (impulse_direction * frame["tick_imbalance_15m"]).ge(
                float(params["impulse_tick_min"])
            )
            & (direction * frame["tick_book_imbalance_mean"]).ge(
                float(params["reversal_book_min"])
            )
            & reversal_location.ge(float(params["reversal_location_min"]))
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
        )
    elif mechanic == "BOOK_ABSORPTION":
        price_move = frame[f"return_{int(params['price_window'])}"]
        price_direction = pd.Series(
            np.sign(price_move.fillna(0.0)).astype(int), index=frame.index
        )
        direction = -price_direction
        mask = (
            (price_move.abs() / atr_value).ge(float(params["move_atr_min"]))
            & (direction * frame["tick_book_imbalance_mean"]).ge(
                float(params["reversal_book_min"])
            )
            & (price_direction * frame["tick_imbalance_15m"]).ge(
                float(params["price_tick_min"])
            )
            & frame["price_efficiency_5m"].le(float(params["efficiency_max"]))
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
        )
    elif mechanic == "LIQUIDITY_SHOCK_REVERSION":
        impulse = frame[f"return_{int(params['impulse_bars'])}"]
        direction = -pd.Series(
            np.sign(impulse.fillna(0.0)).astype(int), index=frame.index
        )
        reversal_location = _signed_location(frame, direction)
        mask = (
            (impulse.abs() / atr_value).ge(float(params["move_atr_min"]))
            & frame["spread_ratio"].ge(float(params["spread_ratio_min"]))
            & frame["variance_ratio"].ge(float(params["variance_ratio_min"]))
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
            & reversal_location.ge(float(params["reversal_location_min"]))
        )
    elif mechanic == "POST_SHOCK_NORMALIZATION":
        imbalance = frame["tick_imbalance_15m"]
        direction = pd.Series(
            np.sign(imbalance.fillna(0.0)).astype(int), index=frame.index
        )
        mask = (
            frame["prior_spread_ratio"].ge(float(params["prior_spread_ratio_min"]))
            & frame["spread_ratio"].le(float(params["current_spread_ratio_max"]))
            & imbalance.abs().ge(float(params["imbalance_min"]))
            & (direction * frame["tick_book_imbalance_mean"]).ge(float(params["book_min"]))
            & frame["quote_intensity_ratio"].ge(float(params["intensity_min"]))
        )
        if bool(params["require_body_alignment"]):
            mask &= (direction * frame["body_move"]).gt(0.0)
    else:
        raise KeyError(mechanic)
    valid = (
        mask.fillna(False)
        & session
        & direction.ne(0)
        & np.isfinite(frame["atr14"])
        & np.isfinite(frame["spread_ratio"])
    )
    return valid, direction.astype(int)


def execution_arrays(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "starts": frame["bar_start_utc"].dt.tz_localize(None).to_numpy(),
        "ends": frame["bar_end_utc"].dt.tz_localize(None).to_numpy(),
        "atr": frame["atr14"].to_numpy(dtype=float),
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
    stage_end: pd.Timestamp,
) -> dict[str, Any] | None:
    entry_index = signal_index + 1
    hold_bars = int(geometry["hold_bars"])
    final_index = entry_index + hold_bars
    if entry_index >= len(arrays["starts"]) or final_index >= len(arrays["starts"]):
        return None
    if arrays["starts"][entry_index] != arrays["ends"][signal_index]:
        return None
    expected = arrays["starts"][entry_index] + np.arange(hold_bars + 1) * np.timedelta64(5, "m")
    if not np.array_equal(arrays["starts"][entry_index : final_index + 1], expected):
        return None
    if pd.Timestamp(arrays["starts"][final_index], tz="UTC") >= stage_end:
        return None
    atr_value = float(arrays["atr"][signal_index])
    if not np.isfinite(atr_value) or atr_value <= 0.0:
        return None
    entry = float(
        arrays["ask_open"][entry_index]
        if direction > 0
        else arrays["bid_open"][entry_index]
    )
    risk = float(geometry["stop_atr"]) * atr_value
    if not np.isfinite(risk) or risk <= 0.0:
        return None
    spread = float(arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index])
    if spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    stop = entry - direction * risk
    target = entry + direction * float(geometry["target_r"]) * risk
    exit_index = final_index
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
            if executable_open < stop:
                exit_index, exit_time, exit_price = position, arrays["starts"][position], executable_open
                exit_reason = "GAP_THROUGH_STOP"
                break
            if executable_open >= target:
                exit_index, exit_time, exit_price = position, arrays["starts"][position], target
                exit_reason = "TARGET_GAP_FROZEN_TARGET"
                break
            stop_hit = float(arrays["bid_low"][position]) <= stop
            target_hit = float(arrays["bid_high"][position]) >= target
        else:
            executable_open = float(arrays["ask_open"][position])
            if executable_open > stop:
                exit_index, exit_time, exit_price = position, arrays["starts"][position], executable_open
                exit_reason = "GAP_THROUGH_STOP"
                break
            if executable_open <= target:
                exit_index, exit_time, exit_price = position, arrays["starts"][position], target
                exit_reason = "TARGET_GAP_FROZEN_TARGET"
                break
            stop_hit = float(arrays["ask_high"][position]) >= stop
            target_hit = float(arrays["ask_low"][position]) <= target
        if stop_hit:
            exit_index, exit_time, exit_price = position, arrays["ends"][position], stop
            ambiguous = bool(target_hit)
            exit_reason = "AMBIGUOUS_M5_STOP_FIRST" if ambiguous else "STOP"
            break
        if target_hit:
            exit_index, exit_time, exit_price = position, arrays["ends"][position], target
            exit_reason = "TARGET"
            break
    entry_time = pd.Timestamp(arrays["starts"][entry_index], tz="UTC")
    exit_timestamp = pd.Timestamp(exit_time, tz="UTC")
    net_r = direction * (exit_price - entry) / risk
    holding_days = max(0.0, (exit_timestamp - entry_time).total_seconds() / 86400.0)
    extra_cost_r = (
        float(execution["extra_execution_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    stress_net_r = net_r - extra_cost_r - float(execution["stress_slippage_r"])
    return {
        "signal_index": signal_index,
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
        "net_r": net_r,
        "stress_net_r": stress_net_r,
        "holding_minutes": (exit_timestamp - entry_time).total_seconds() / 60.0,
        "exit_reason": exit_reason,
        "ambiguous_m5": ambiguous,
        "current_account_feasible": risk_usd <= float(execution["current_account_risk_usd"]),
        "exit_index": exit_index,
    }


def select_policy_trades(
    frame: pd.DataFrame,
    arrays: Mapping[str, Any],
    policy: Any,
    config: Mapping[str, Any],
    stage_start: pd.Timestamp,
    stage_end: pd.Timestamp,
    outcome_cache: dict[tuple[str, int, int], Any],
) -> pd.DataFrame:
    params = json.loads(policy.parameters_json)
    mask, direction = signal_mask_direction(frame, str(policy.mechanic), params)
    stage_mask = frame["bar_end_utc"].ge(stage_start) & frame["bar_end_utc"].lt(stage_end)
    indices = np.flatnonzero((mask & stage_mask).to_numpy())
    geometry = config["mechanics"][str(policy.mechanic)]
    execution = config["execution"]
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    cooldown = pd.Timedelta(minutes=5 * int(execution["cooldown_bars"]))
    for signal_index in indices:
        signal_direction = int(direction.iat[int(signal_index)])
        key = (str(policy.mechanic), int(signal_index), signal_direction)
        outcome = outcome_cache.get(key, _MISSING)
        if outcome is _MISSING:
            outcome = simulate_trade(
                arrays,
                int(signal_index),
                signal_direction,
                geometry,
                execution,
                stage_end,
            )
            outcome_cache[key] = outcome
        if outcome is None:
            continue
        entry_time = outcome["entry_time"]
        if entry_time < position_until or entry_time < cooldown_until:
            continue
        day = entry_time.date()
        if daily_count.get(day, 0) >= int(execution["maximum_trades_per_policy_utc_day"]):
            continue
        selected.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": str(policy.mechanic),
                **outcome,
            }
        )
        position_until = outcome["exit_time"]
        cooldown_until = outcome["exit_time"] + cooldown
        daily_count[day] = daily_count.get(day, 0) + 1
    if not selected:
        return pd.DataFrame()
    return pd.DataFrame(selected).sort_values("entry_time", kind="mergesort").reset_index(drop=True)


def profit_factor(values: pd.Series) -> float | None:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return None if gains == 0.0 else float("inf")
    return gains / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(([0.0], values.fillna(0.0).to_numpy(dtype=float).cumsum()))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity)) if len(equity) else 0.0


def _source_dates(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.Index:
    dates = frame.loc[
        frame["bar_start_utc"].ge(start) & frame["bar_start_utc"].lt(end),
        "bar_start_utc",
    ].dt.date
    return pd.Index(sorted(dates.unique()))


def _daily_pvalue(trades: pd.DataFrame, source_dates: pd.Index) -> float:
    if len(source_dates) == 0:
        return 1.0
    if trades.empty:
        values = np.zeros(len(source_dates), dtype=float)
    else:
        daily = trades.groupby(trades["entry_time"].dt.date)["stress_net_r"].sum()
        values = daily.reindex(source_dates, fill_value=0.0).to_numpy(dtype=float)
    if float(values.mean()) <= 0.0:
        return 1.0
    standard = float(values.std(ddof=1)) if len(values) > 1 else 0.0
    if standard == 0.0:
        return 0.0
    result = stats.ttest_1samp(values, popmean=0.0, alternative="greater")
    return float(result.pvalue) if np.isfinite(result.pvalue) else 1.0


def summarize(
    trades: pd.DataFrame,
    frame: pd.DataFrame,
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
    source_dates = _source_dates(frame, start, end)
    start_month = start.tz_localize(None).to_period("M")
    end_month = (end - pd.Timedelta(nanoseconds=1)).tz_localize(None).to_period("M")
    months = pd.period_range(start_month, end_month, freq="M")
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
    for segment_start_raw, segment_end_raw in segments:
        segment_start = pd.Timestamp(segment_start_raw)
        segment_end = pd.Timestamp(segment_end_raw)
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
        segment_pf = profit_factor(segment_values)
        segment_metrics.append(
            {
                "start": segment_start.isoformat(),
                "end": segment_end.isoformat(),
                "trades": int(len(segment)),
                "net_r": float(segment_values.sum()),
                "average_r": float(segment_values.mean()) if len(segment_values) else 0.0,
                "stress_pf": segment_pf,
                "profitable": bool(segment_values.sum() > 0.0),
            }
        )
    finite_segment_pfs = [
        float(item["stress_pf"])
        if item["stress_pf"] is not None and math.isfinite(float(item["stress_pf"]))
        else (float("inf") if item["net_r"] > 0.0 else 0.0)
        for item in segment_metrics
    ]
    pf = profit_factor(values)
    return {
        "trades": int(len(trades)),
        "source_days": int(len(source_dates)),
        "trades_per_source_day": len(trades) / len(source_dates) if len(source_dates) else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": pf,
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "positive_month_share": float((monthly > 0.0).mean()) if len(monthly) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "daily_pvalue": _daily_pvalue(trades, source_dates),
        "profitable_segments": int(sum(bool(item["profitable"]) for item in segment_metrics)),
        "worst_segment_pf": float(min(finite_segment_pfs)) if finite_segment_pfs else 0.0,
        "segment_metrics": segment_metrics,
        "current_account_feasible_share": (
            float(trades["current_account_feasible"].mean()) if not trades.empty else 0.0
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
        "minimum_stress_pf": pf is not None and float(pf) >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": float(metrics["average_stress_r"])
        >= float(gate["minimum_average_stress_r"]),
        "minimum_positive_month_share": float(metrics["positive_month_share"])
        >= float(gate["minimum_positive_month_share"]),
        "maximum_closed_drawdown_r": float(metrics["closed_drawdown_r"])
        <= float(gate["maximum_closed_drawdown_r"]),
        "top_winners_removed_positive": float(metrics["top_winners_removed_stress_net_r"])
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
    manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
) -> tuple[pd.DataFrame, dict[tuple[str, int, int], Any]]:
    start, end = map(pd.Timestamp, config["windows"][stage])
    arrays = execution_arrays(frame)
    cache: dict[tuple[str, int, int], Any] = {}
    rows: list[dict[str, Any]] = []
    for policy in manifest.itertuples(index=False):
        trades = select_policy_trades(
            frame,
            arrays,
            policy,
            config,
            start,
            end,
            cache,
        )
        values = summarize(
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
                "parameters_json": str(policy.parameters_json),
                **values,
            }
        )
    metrics = pd.DataFrame(rows)
    metrics["fdr_qvalue"] = benjamini_hochberg(metrics["daily_pvalue"])
    checks_list: list[dict[str, bool]] = []
    passes: list[bool] = []
    for row in metrics.to_dict(orient="records"):
        checks = gate_checks(row, config["gates"][stage])
        checks_list.append(checks)
        passes.append(all(checks.values()))
    metrics["gate_checks_json"] = [
        json.dumps(checks, sort_keys=True, separators=(",", ":"))
        for checks in checks_list
    ]
    metrics["gate_pass"] = passes
    return metrics, cache


def select_advancers(metrics: pd.DataFrame, gate: Mapping[str, Any]) -> pd.DataFrame:
    eligible = metrics.loc[metrics["gate_pass"]].copy()
    if eligible.empty:
        return eligible
    limit = int(gate.get("maximum_advancers_per_mechanic", 1))
    eligible = eligible.sort_values(
        [
            "mechanic",
            "fdr_qvalue",
            "worst_segment_pf",
            "average_stress_r",
            "stress_net_r",
            "policy_id",
        ],
        ascending=[True, True, False, False, False, True],
        kind="mergesort",
    )
    return eligible.groupby("mechanic", sort=True, observed=True).head(limit).reset_index(drop=True)


def selected_trade_ledger(
    frame: pd.DataFrame,
    selected_manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
    cache: dict[tuple[str, int, int], Any] | None = None,
) -> pd.DataFrame:
    if selected_manifest.empty:
        return pd.DataFrame()
    start, end = map(pd.Timestamp, config["windows"][stage])
    arrays = execution_arrays(frame)
    outcome_cache = cache if cache is not None else {}
    frames: list[pd.DataFrame] = []
    for policy in selected_manifest.itertuples(index=False):
        trades = select_policy_trades(
            frame,
            arrays,
            policy,
            config,
            start,
            end,
            outcome_cache,
        )
        if not trades.empty:
            frames.append(trades.assign(stage=stage))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
