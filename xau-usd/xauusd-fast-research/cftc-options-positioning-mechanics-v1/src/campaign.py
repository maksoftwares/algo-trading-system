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
    "MM_OPTIONS_FLOW_CONTINUATION",
    "MM_OPTIONS_CROWDING_REVERSAL",
    "PRODUCER_MM_OPTIONS_DIVERGENCE",
    "SWAP_OPTIONS_HEDGE_PRESSURE",
    "OPTIONS_FUTURES_DISLOCATION",
)
SESSIONS = ("ALL", "ASIA", "LONDON", "NY")
PRICE_FILTERS = ("NONE", "H1_ALIGN", "H6_ALIGN", "REVERSAL_CONFIRM")
_MISSING = object()


def _space(**values: Iterable[Any]) -> list[dict[str, Any]]:
    names = tuple(values)
    return [
        dict(zip(names, combination, strict=True))
        for combination in product(*(values[name] for name in names))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    if mechanic not in MECHANICS:
        raise KeyError(mechanic)
    price_pairs = [
        (price_filter, minimum)
        for price_filter in PRICE_FILTERS
        for minimum in ((0.0,) if price_filter == "NONE" else (0.0, 0.15, 0.30))
    ]
    common = _space(
        lookback=(52, 104, 156),
        threshold_z=(0.75, 1.0, 1.25, 1.5),
        price_filter_min=price_pairs,
        session=SESSIONS,
        stop_atr=(0.75, 1.0, 1.25, 1.5),
        target_r=(1.25, 1.5, 2.0),
        hold_hours=(4, 8, 12, 24),
    )
    extensions = (0.0, 0.5, 1.0) if mechanic == "MM_OPTIONS_CROWDING_REVERSAL" else (0.0,)
    opposites = (False, True) if mechanic == "PRODUCER_MM_OPTIONS_DIVERGENCE" else (False,)
    rows: list[dict[str, Any]] = []
    for base in common:
        price_filter, price_min = base.pop("price_filter_min")
        for extension, opposite in product(extensions, opposites):
            rows.append(
                {
                    **base,
                    "price_filter": price_filter,
                    "price_min_atr": price_min,
                    "crowd_extension_atr_min": extension,
                    "require_opposite_option_sides": opposite,
                }
            )
    return rows


def _causal_z(values: pd.Series, lookback: int) -> pd.Series:
    prior = values.shift(1).rolling(lookback, min_periods=lookback)
    scale = prior.std(ddof=0).replace(0.0, np.nan)
    return (values - prior.mean()) / scale


def prepare_positioning(positioning: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    required = {
        "report_date",
        "available_utc",
        "open_interest_all_combined",
        "open_interest_all_futures",
        "options_open_interest_delta_equivalent",
        *{
            f"{category}_{kind}_net"
            for category in (
                "producer",
                "swap",
                "managed_money",
                "other_reportable",
                "nonreportable",
            )
            for kind in ("combined", "futures", "options")
        },
    }
    missing = sorted(required.difference(positioning.columns))
    if missing:
        raise ValueError(f"CFTC positioning is missing columns: {missing}")
    frame = positioning.copy().sort_values("available_utc", kind="mergesort").reset_index(drop=True)
    for column in ("report_date", "available_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="raise")
    if frame["report_date"].duplicated().any() or frame["available_utc"].duplicated().any():
        raise ValueError("Duplicate CFTC report or availability timestamp")
    option_oi = frame["options_open_interest_delta_equivalent"].replace(0.0, np.nan)
    futures_oi = frame["open_interest_all_futures"].replace(0.0, np.nan)
    for category in (
        "producer",
        "swap",
        "managed_money",
        "other_reportable",
        "nonreportable",
    ):
        frame[f"{category}_options_net_share"] = frame[f"{category}_options_net"] / option_oi
        frame[f"{category}_futures_net_share"] = frame[f"{category}_futures_net"] / futures_oi
    frame["producer_mm_options_divergence"] = (
        frame["managed_money_options_net_share"]
        - frame["producer_options_net_share"]
    )
    frame["mm_options_futures_dislocation"] = (
        frame["managed_money_options_net_share"]
        - frame["managed_money_futures_net_share"]
    )
    lookbacks = [int(value) for value in config["features"]["positioning_z_lookbacks"]]
    for lookback in lookbacks:
        frame[f"mm_options_level_z_{lookback}"] = _causal_z(
            frame["managed_money_options_net_share"], lookback
        )
        frame[f"mm_options_flow_z_{lookback}"] = _causal_z(
            frame["managed_money_options_net_share"].diff(), lookback
        )
        frame[f"producer_mm_divergence_z_{lookback}"] = _causal_z(
            frame["producer_mm_options_divergence"], lookback
        )
        frame[f"swap_options_flow_z_{lookback}"] = _causal_z(
            frame["swap_options_net_share"].diff(), lookback
        )
        frame[f"options_futures_dislocation_z_{lookback}"] = _causal_z(
            frame["mm_options_futures_dislocation"], lookback
        )
    return frame


def _wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


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
    return _wilder(true_range, period)


def prepare_features(
    h1: pd.DataFrame,
    positioning: pd.DataFrame,
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
    frame["prior_body_atr"] = frame["body_atr"].shift(1)
    frame["return_6h_atr"] = (frame["mid_close"] - frame["mid_close"].shift(6)) / scale
    frame["hour_utc"] = frame["bar_end_utc"].dt.hour
    prepared_positioning = prepare_positioning(positioning, config)
    result = pd.merge_asof(
        frame,
        prepared_positioning,
        left_on="bar_end_utc",
        right_on="available_utc",
        direction="backward",
        tolerance=pd.Timedelta(days=float(config["features"]["maximum_positioning_staleness_days"])),
    )
    observed = result["available_utc"].notna()
    if (result.loc[observed, "available_utc"] > result.loc[observed, "bar_end_utc"]).any():
        raise ValueError("Future CFTC report joined to H1 decision")
    return result


def _feature_column(mechanic: str, lookback: int) -> str:
    prefixes = {
        "MM_OPTIONS_FLOW_CONTINUATION": "mm_options_flow_z",
        "MM_OPTIONS_CROWDING_REVERSAL": "mm_options_level_z",
        "PRODUCER_MM_OPTIONS_DIVERGENCE": "producer_mm_divergence_z",
        "SWAP_OPTIONS_HEDGE_PRESSURE": "swap_options_flow_z",
        "OPTIONS_FUTURES_DISLOCATION": "options_futures_dislocation_z",
    }
    return f"{prefixes[mechanic]}_{lookback}"


def _session_mask(frame: pd.DataFrame, session: str) -> pd.Series:
    if session == "ALL":
        return pd.Series(True, index=frame.index)
    bounds = {"ASIA": (0, 6), "LONDON": (6, 12), "NY": (12, 18)}
    if session not in bounds:
        raise KeyError(session)
    start, end = bounds[session]
    return frame["hour_utc"].ge(start) & frame["hour_utc"].lt(end)


def signal_mask_direction(
    frame: pd.DataFrame,
    mechanic: str,
    params: Mapping[str, Any],
) -> tuple[pd.Series, pd.Series]:
    feature = frame[_feature_column(mechanic, int(params["lookback"]))]
    raw_direction = pd.Series(np.sign(feature.fillna(0.0)).astype(int), index=frame.index)
    direction = -raw_direction if mechanic in {
        "MM_OPTIONS_CROWDING_REVERSAL",
        "SWAP_OPTIONS_HEDGE_PRESSURE",
    } else raw_direction
    mask = feature.abs().ge(float(params["threshold_z"])) & direction.ne(0)
    if mechanic == "MM_OPTIONS_CROWDING_REVERSAL":
        crowd_direction = -direction
        mask &= (crowd_direction * frame["return_6h_atr"]).ge(
            float(params["crowd_extension_atr_min"])
        )
    if mechanic == "PRODUCER_MM_OPTIONS_DIVERGENCE" and bool(
        params["require_opposite_option_sides"]
    ):
        mask &= (
            frame["managed_money_options_net_share"]
            * frame["producer_options_net_share"]
        ).lt(0.0)
    minimum = float(params["price_min_atr"])
    price_filter = str(params["price_filter"])
    if price_filter == "H1_ALIGN":
        mask &= (direction * frame["body_atr"]).ge(minimum)
    elif price_filter == "H6_ALIGN":
        mask &= (direction * frame["return_6h_atr"]).ge(minimum)
    elif price_filter == "REVERSAL_CONFIRM":
        mask &= (direction * frame["body_atr"]).ge(minimum)
        mask &= (direction * frame["prior_body_atr"]).le(0.0)
    elif price_filter != "NONE":
        raise KeyError(price_filter)
    mask &= _session_mask(frame, str(params["session"]))
    return mask.fillna(False), direction


def generate_manifest(
    frame: pd.DataFrame,
    discovery_start: pd.Timestamp,
    discovery_end: pd.Timestamp,
    attempts_before: int = 8093,
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
            policy_id = hashlib.sha256(
                f"{mechanic}|{canonical}".encode("ascii")
            ).hexdigest()[:16]
            rows.append(
                {
                    "attempt_no": attempt,
                    "policy_id": policy_id,
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
                f"Only {admitted} coverage-eligible policies for {mechanic}; "
                f"required {policies_per_mechanic}"
            )
    manifest = pd.DataFrame(rows)
    expected = len(MECHANICS) * policies_per_mechanic
    if len(manifest) != expected or manifest["policy_id"].duplicated().any():
        raise ValueError("Invalid CFTC options policy manifest")
    return manifest


def execution_arrays(m5: pd.DataFrame) -> dict[str, Any]:
    frame = m5.sort_values("bar_start_utc", kind="mergesort").reset_index(drop=True)
    return {
        "starts": frame["bar_start_utc"].dt.tz_localize(None).to_numpy(dtype="datetime64[ns]"),
        "ends": frame["bar_end_utc"].dt.tz_localize(None).to_numpy(dtype="datetime64[ns]"),
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
    signal_time: pd.Timestamp,
    atr_value: float,
    direction: int,
    params: Mapping[str, Any],
    execution: Mapping[str, Any],
    stage_end: pd.Timestamp,
) -> dict[str, Any] | None:
    naive_signal = np.datetime64(signal_time.tz_convert(None))
    entry_index = int(np.searchsorted(arrays["starts"], naive_signal, side="left"))
    hold_bars = int(params["hold_hours"]) * 12
    final_index = entry_index + hold_bars
    if entry_index >= len(arrays["starts"]) or final_index >= len(arrays["starts"]):
        return None
    if arrays["starts"][entry_index] != naive_signal:
        return None
    expected = arrays["starts"][entry_index] + np.arange(hold_bars + 1) * np.timedelta64(5, "m")
    if not np.array_equal(arrays["starts"][entry_index : final_index + 1], expected):
        return None
    if pd.Timestamp(arrays["starts"][final_index], tz="UTC") >= stage_end:
        return None
    if not np.isfinite(atr_value) or atr_value <= 0.0:
        return None
    entry = float(arrays["ask_open"][entry_index] if direction > 0 else arrays["bid_open"][entry_index])
    risk = float(params["stop_atr"]) * atr_value
    spread = float(arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index])
    if risk <= 0.0 or spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    stop = entry - direction * risk
    target = entry + direction * float(params["target_r"]) * risk
    exit_index = final_index
    exit_time = arrays["starts"][final_index]
    exit_price = float(
        arrays["bid_open"][final_index] if direction > 0 else arrays["ask_open"][final_index]
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
        "signal_time": signal_time,
        "entry_time": entry_time,
        "exit_time": exit_timestamp,
        "direction": "LONG" if direction > 0 else "SHORT",
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "stop_atr": float(params["stop_atr"]),
        "target_r": float(params["target_r"]),
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
    feature_column = _feature_column(mechanic, int(params["lookback"]))
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
            outcome = simulate_trade(
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
                "positioning_feature": feature_column,
                "positioning_feature_value": float(row[feature_column]),
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


def _weekly_pvalue(
    trades: pd.DataFrame,
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> float:
    stage = frame.loc[
        frame["bar_end_utc"].ge(start) & frame["bar_end_utc"].lt(end), "report_date"
    ].dropna()
    blocks = pd.Index(sorted(pd.to_datetime(stage, utc=True).unique()))
    if len(blocks) == 0:
        return 1.0
    if trades.empty:
        values = np.zeros(len(blocks), dtype=float)
    else:
        weekly = trades.groupby("report_date")["stress_net_r"].sum()
        values = weekly.reindex(blocks, fill_value=0.0).to_numpy(dtype=float)
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
    values = trades["stress_net_r"].astype(float) if not trades.empty else pd.Series(dtype=float)
    source_days = int(
        frame.loc[
            frame["bar_start_utc"].ge(start) & frame["bar_start_utc"].lt(end),
            "bar_start_utc",
        ].dt.date.nunique()
    )
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
    return {
        "trades": int(len(trades)),
        "source_days": source_days,
        "trades_per_source_day": len(trades) / source_days if source_days else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "positive_month_share": float((monthly > 0.0).mean()) if len(monthly) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "block_pvalue": _weekly_pvalue(trades, frame, start, end),
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
    m5: pd.DataFrame,
    manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
) -> tuple[pd.DataFrame, dict[tuple[Any, ...], Any]]:
    start, end = map(pd.Timestamp, config["windows"][stage])
    arrays = execution_arrays(m5)
    cache: dict[tuple[Any, ...], Any] = {}
    rows: list[dict[str, Any]] = []
    for policy in manifest.itertuples(index=False):
        trades = select_policy_trades(frame, arrays, policy, config, start, end, cache)
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
                "raw_discovery_signal_count": int(policy.raw_discovery_signal_count),
                "parameters_json": str(policy.parameters_json),
                **values,
            }
        )
    metrics = pd.DataFrame(rows)
    metrics["fdr_qvalue"] = benjamini_hochberg(metrics["block_pvalue"])
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
        ["mechanic", "fdr_qvalue", "worst_segment_pf", "average_stress_r", "policy_id"],
        ascending=[True, True, False, False, True],
        kind="mergesort",
    )
    return eligible.groupby("mechanic", sort=True, observed=True).head(limit).reset_index(drop=True)


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
    arrays = execution_arrays(m5)
    outcome_cache = cache if cache is not None else {}
    frames: list[pd.DataFrame] = []
    for policy in selected_manifest.itertuples(index=False):
        trades = select_policy_trades(
            frame, arrays, policy, config, start, end, outcome_cache
        )
        if not trades.empty:
            frames.append(trades.assign(stage=stage))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
