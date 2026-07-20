from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path
from typing import Any, Iterator, Mapping

import numpy as np
import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_m5(config: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    )
    path = storage / str(source["feature_cache"])
    actual = sha256_file(path)
    if actual != str(source["feature_sha256"]):
        raise ValueError(f"Feature cache hash mismatch: {actual}")
    cutoff = pd.Timestamp(config["selection_cutoff_exclusive_utc"])
    cutoff_ms = int(cutoff.timestamp() * 1000)
    columns = [
        "timestamp_ms",
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
    ]
    frame = pd.read_parquet(
        path,
        columns=columns,
        filters=[("timestamp_ms", "<", cutoff_ms)],
    )
    frame["bar_start_utc"] = pd.to_datetime(
        frame.pop("timestamp_ms"), unit="ms", utc=True
    )
    frame["timestamp_utc"] = frame["bar_start_utc"] + pd.Timedelta(minutes=5)
    frame = frame.sort_values("bar_start_utc", kind="mergesort").reset_index(drop=True)
    if frame["bar_start_utc"].duplicated().any():
        raise ValueError("Duplicate M5 bar starts")
    if not frame["bar_start_utc"].lt(cutoff).all():
        raise ValueError("Final-year M5 rows entered V65 selection")
    return frame, {
        "path": str(path),
        "sha256": actual,
        "rows_loaded": int(len(frame)),
        "first_bar_start_utc": str(frame["bar_start_utc"].min()),
        "last_bar_start_utc": str(frame["bar_start_utc"].max()),
    }


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


def aggregate_bars(
    m5: pd.DataFrame, minutes: int, minimum_share: float
) -> pd.DataFrame:
    source = m5.copy()
    source["_bucket"] = source["bar_start_utc"].dt.floor(f"{minutes}min")
    aggregations: dict[str, str] = {"bar_start_utc": "size"}
    for side in ("bid", "ask", "mid"):
        aggregations.update(
            {
                f"{side}_open": "first",
                f"{side}_high": "max",
                f"{side}_low": "min",
                f"{side}_close": "last",
            }
        )
    grouped = source.groupby("_bucket", sort=True, observed=True).agg(aggregations)
    grouped = grouped.rename(columns={"bar_start_utc": "source_rows"})
    minimum_rows = int(np.ceil((minutes / 5.0) * float(minimum_share)))
    grouped = grouped.loc[grouped["source_rows"].ge(minimum_rows)].reset_index()
    grouped["bar_start_utc"] = grouped.pop("_bucket")
    grouped["timestamp_utc"] = grouped["bar_start_utc"] + pd.Timedelta(
        minutes=minutes
    )
    return grouped


def trend_features(
    frame: pd.DataFrame,
    fast: int,
    slow: int,
    slope_lag: int,
) -> pd.DataFrame:
    result = frame.copy()
    result["ema_fast"] = result["mid_close"].ewm(
        span=fast, adjust=False, min_periods=fast
    ).mean()
    result["ema_slow"] = result["mid_close"].ewm(
        span=slow, adjust=False, min_periods=slow
    ).mean()
    result["trend_up"] = (
        result["mid_close"].gt(result["ema_fast"])
        & result["ema_fast"].gt(result["ema_slow"])
        & result["ema_fast"].ge(result["ema_fast"].shift(slope_lag))
        & result["ema_slow"].ge(result["ema_slow"].shift(slope_lag))
    )
    result["trend_down"] = (
        result["mid_close"].lt(result["ema_fast"])
        & result["ema_fast"].lt(result["ema_slow"])
        & result["ema_fast"].le(result["ema_fast"].shift(slope_lag))
        & result["ema_slow"].le(result["ema_slow"].shift(slope_lag))
    )
    result["supportive_up"] = result["mid_close"].gt(result["ema_fast"]) & result[
        "ema_fast"
    ].ge(result["ema_fast"].shift(slope_lag))
    result["supportive_down"] = result["mid_close"].lt(result["ema_fast"]) & result[
        "ema_fast"
    ].le(result["ema_fast"].shift(slope_lag))
    return result


def prepare_scale_features(
    m5: pd.DataFrame,
    scale: Mapping[str, Any],
    settings: Mapping[str, Any],
    box_bars: list[int],
) -> pd.DataFrame:
    share = float(settings["minimum_calendar_bucket_share"])
    parent = aggregate_bars(m5, int(scale["parent_minutes"]), share)
    signal = aggregate_bars(m5, int(scale["signal_minutes"]), share)
    period = int(settings["atr_period"])
    parent["atr_parent"] = atr(parent, period)
    parent["range_parent"] = parent["mid_high"] - parent["mid_low"]
    median_lookback = int(settings["range_median_lookback_bars"])
    parent["median_range_parent"] = parent["range_parent"].rolling(
        median_lookback, min_periods=median_lookback
    ).median()
    percentile_lookback = int(settings["atr_percentile_lookback_bars"])
    parent["atr_percentile_parent"] = (
        parent["atr_parent"]
        .rolling(percentile_lookback, min_periods=percentile_lookback)
        .rank(pct=True)
        * 100.0
    )
    parent = trend_features(
        parent,
        int(settings["fast_ema_period"]),
        int(settings["slow_ema_period"]),
        int(settings["slope_lag_bars"]),
    )
    persistence = int(settings["parent_trend_persistence_bars"])
    for direction in ("up", "down"):
        persistent = parent[f"trend_{direction}"].copy()
        for shift in range(1, persistence):
            persistent &= parent[f"trend_{direction}"].shift(shift).fillna(False)
        parent[f"persistent_{direction}"] = persistent
    for bars in box_bars:
        parent[f"box_high_{bars}"] = parent["mid_high"].rolling(
            int(bars), min_periods=int(bars)
        ).max()
        parent[f"box_low_{bars}"] = parent["mid_low"].rolling(
            int(bars), min_periods=int(bars)
        ).min()

    signal["atr_signal"] = atr(signal, period)
    signal_range = (signal["mid_high"] - signal["mid_low"]).replace(0.0, np.nan)
    signal["body_fraction"] = (
        signal["mid_close"] - signal["mid_open"]
    ).abs() / signal_range
    signal["candle_direction"] = np.sign(
        signal["mid_close"] - signal["mid_open"]
    ).astype(int)
    signal = trend_features(
        signal,
        int(settings["fast_ema_period"]),
        int(settings["slow_ema_period"]),
        int(settings["slope_lag_bars"]),
    )
    signal["shock"] = signal_range.ge(
        float(settings["shock_range_atr_multiple"]) * signal["atr_signal"]
    )
    parent_columns = [
        "timestamp_utc",
        "atr_parent",
        "median_range_parent",
        "atr_percentile_parent",
        "persistent_up",
        "persistent_down",
    ]
    for bars in box_bars:
        parent_columns.extend([f"box_high_{bars}", f"box_low_{bars}"])
    merged = pd.merge_asof(
        signal.sort_values("timestamp_utc"),
        parent[parent_columns].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    merged["scale_id"] = str(scale["scale_id"])
    return merged


def parameter_grid(config: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    grid = config["parameter_grid"]
    keys = [
        "directions",
        "regime_modes",
        "box_bars",
        "atr_percentile_max",
        "box_average_to_median_max",
        "minimum_signal_body_fraction",
        "target_r",
    ]
    for values in itertools.product(*(grid[key] for key in keys)):
        yield {
            "direction": values[0],
            "regime_mode": values[1],
            "box_bars": int(values[2]),
            "atr_percentile_max": float(values[3]),
            "box_average_to_median_max": float(values[4]),
            "minimum_signal_body_fraction": float(values[5]),
            "target_r": float(values[6]),
            "stop_atr_floor": float(grid["stop_atr_floor"]),
        }


def variant_id(scale_id: str, params: Mapping[str, Any]) -> str:
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(f"V65|{scale_id}|{payload}".encode("ascii")).hexdigest()
    return f"V65_{scale_id}_{digest[:16]}"


def candidate_signals(
    features: pd.DataFrame, params: Mapping[str, Any]
) -> pd.DataFrame:
    bars = int(params["box_bars"])
    direction = str(params["direction"])
    sign = 1 if direction == "LONG" else -1
    box_high = features[f"box_high_{bars}"]
    box_low = features[f"box_low_{bars}"]
    box_average = (box_high - box_low) / bars
    parent_trend = features["persistent_up"] if sign > 0 else features["persistent_down"]
    signal_trend = features["trend_up"] if sign > 0 else features["trend_down"]
    supportive = features["supportive_up"] if sign > 0 else features["supportive_down"]
    regime = parent_trend & (
        signal_trend if params["regime_mode"] == "STRICT" else supportive
    )
    break_mask = (
        features["mid_close"].gt(box_high)
        if sign > 0
        else features["mid_close"].lt(box_low)
    )
    candle = features["candle_direction"].eq(sign)
    mask = (
        regime.fillna(False)
        & ~features["shock"].fillna(True)
        & features["atr_percentile_parent"].le(
            float(params["atr_percentile_max"])
        )
        & box_average.le(
            float(params["box_average_to_median_max"])
            * features["median_range_parent"]
        )
        & features["body_fraction"].ge(
            float(params["minimum_signal_body_fraction"])
        )
        & break_mask
        & candle
        & np.isfinite(features["atr_signal"])
    )
    selected = features.loc[mask].copy()
    structural = (
        selected["mid_close"] - selected[f"box_low_{bars}"]
        if sign > 0
        else selected[f"box_high_{bars}"] - selected["mid_close"]
    )
    selected["stop_distance"] = np.maximum(
        structural,
        float(params["stop_atr_floor"]) * selected["atr_signal"],
    )
    selected["direction"] = direction
    selected["target_r"] = float(params["target_r"])
    selected["signal_time"] = selected["timestamp_utc"]
    return selected.loc[
        selected["stop_distance"].gt(0.0),
        ["signal_time", "direction", "stop_distance", "target_r"],
    ].reset_index(drop=True)


def market_arrays(m5: pd.DataFrame) -> dict[str, np.ndarray]:
    arrays = {
        "starts": m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]"),
        "ends": m5["timestamp_utc"].to_numpy(dtype="datetime64[ns]"),
    }
    for side in ("bid", "ask"):
        for field in ("open", "high", "low", "close"):
            arrays[f"{side}_{field}"] = m5[f"{side}_{field}"].to_numpy(dtype=float)
    return arrays


def simulate_signal(
    arrays: Mapping[str, np.ndarray],
    signal_time: pd.Timestamp,
    direction: str,
    stop_distance: float,
    target_r: float,
    maximum_hold_hours: float,
    execution: Mapping[str, Any],
) -> dict[str, Any] | None:
    starts = arrays["starts"]
    signal_np = np.datetime64(signal_time.tz_convert(None))
    entry_index = int(np.searchsorted(starts, signal_np, side="left"))
    if entry_index >= len(starts):
        return None
    entry_time = pd.Timestamp(starts[entry_index], tz="UTC")
    delay = (entry_time - signal_time).total_seconds() / 60.0
    if delay < 0.0 or delay > float(execution["maximum_entry_gap_minutes"]):
        return None
    sign = 1 if direction == "LONG" else -1
    entry = float(
        arrays["ask_open"][entry_index]
        if sign > 0
        else arrays["bid_open"][entry_index]
    )
    spread = float(arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index])
    risk = float(stop_distance)
    if risk <= 0.0 or spread < 0.0:
        return None
    if spread > float(execution["maximum_spread_price"]):
        return None
    if spread / risk > float(execution["maximum_spread_r"]):
        return None
    stop = entry - sign * risk
    target = entry + sign * float(target_r) * risk
    maximum_bars = int(np.ceil(float(maximum_hold_hours) * 12.0))
    end_index = min(len(starts), entry_index + maximum_bars)
    side = "bid" if sign > 0 else "ask"
    opens = arrays[f"{side}_open"]
    highs = arrays[f"{side}_high"]
    lows = arrays[f"{side}_low"]
    closes = arrays[f"{side}_close"]
    exit_index = end_index - 1
    exit_price = float(closes[exit_index])
    exit_reason = "MAX_HOLD"
    ambiguous = False
    for index in range(entry_index, end_index):
        open_price = float(opens[index])
        if sign > 0:
            if open_price < stop:
                exit_index, exit_price, exit_reason = index, open_price, "GAP_STOP"
                break
            if open_price >= target:
                exit_index, exit_price, exit_reason = index, target, "TARGET_GAP"
                break
            stop_hit = float(lows[index]) <= stop
            target_hit = float(highs[index]) >= target
        else:
            if open_price > stop:
                exit_index, exit_price, exit_reason = index, open_price, "GAP_STOP"
                break
            if open_price <= target:
                exit_index, exit_price, exit_reason = index, target, "TARGET_GAP"
                break
            stop_hit = float(highs[index]) >= stop
            target_hit = float(lows[index]) <= target
        if stop_hit:
            exit_index, exit_price = index, stop
            ambiguous = bool(target_hit)
            exit_reason = "AMBIGUOUS_STOP_FIRST" if ambiguous else "STOP"
            break
        if target_hit:
            exit_index, exit_price, exit_reason = index, target, "TARGET"
            break
    exit_time = pd.Timestamp(arrays["ends"][exit_index], tz="UTC")
    net_r = sign * (exit_price - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    extra_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk
    stress_net_r = net_r - extra_cost_r - float(execution["stress_slippage_r"])
    return {
        "entry_time": entry_time,
        "exit_time": exit_time,
        "entry_price": entry,
        "exit_price": exit_price,
        "direction": direction,
        "initial_risk_price": risk,
        "risk_usd": risk,
        "entry_spread": spread,
        "entry_spread_r": spread / risk,
        "net_r": net_r,
        "stress_net_r": stress_net_r,
        "pnl_usd": stress_net_r * risk,
        "exit_reason": exit_reason,
        "ambiguous_m5": ambiguous,
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
    }


def simulate_candidates(
    candidates: pd.DataFrame,
    arrays: Mapping[str, np.ndarray],
    maximum_hold_hours: float,
    execution: Mapping[str, Any],
    cache: dict[tuple[Any, ...], dict[str, Any] | None],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for signal in candidates.itertuples(index=False):
        key = (
            int(pd.Timestamp(signal.signal_time).value),
            str(signal.direction),
            round(float(signal.stop_distance), 8),
            round(float(signal.target_r), 8),
            float(maximum_hold_hours),
        )
        if key not in cache:
            cache[key] = simulate_signal(
                arrays,
                pd.Timestamp(signal.signal_time),
                str(signal.direction),
                float(signal.stop_distance),
                float(signal.target_r),
                maximum_hold_hours,
                execution,
            )
        outcome = cache[key]
        if outcome is not None:
            rows.append({"signal_time": signal.signal_time, **outcome})
    return pd.DataFrame(rows)


def apply_policy(
    trades: pd.DataFrame, maximum_open: int, maximum_daily: int
) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    ordered = trades.sort_values(["entry_time", "signal_time"], kind="mergesort")
    active: list[pd.Timestamp] = []
    daily: dict[Any, int] = {}
    accepted: list[int] = []
    for index, trade in ordered.iterrows():
        active = [value for value in active if value > trade["entry_time"]]
        day = trade["entry_time"].date()
        if len(active) >= int(maximum_open) or daily.get(day, 0) >= int(maximum_daily):
            continue
        accepted.append(index)
        active.append(trade["exit_time"])
        daily[day] = daily.get(day, 0) + 1
    return ordered.loc[accepted].reset_index(drop=True)


def profit_factor(values: pd.Series) -> float:
    gain = float(values.loc[values > 0.0].sum())
    loss = float(-values.loc[values < 0.0].sum())
    if loss == 0.0:
        return float("inf") if gain > 0.0 else 0.0
    return gain / loss


def window_metrics(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    top_winners: int,
) -> dict[str, Any]:
    selected = trades.loc[
        trades["entry_time"].ge(start) & trades["entry_time"].lt(end)
    ].copy()
    stress = selected["stress_net_r"].astype(float)
    ordered = selected.sort_values(["exit_time", "signal_time"], kind="mergesort")
    equity = ordered["stress_net_r"].astype(float).cumsum()
    peak = equity.cummax().clip(lower=0.0)
    removed = stress.drop(stress.nlargest(min(int(top_winners), len(stress))).index)
    month_index = pd.period_range(
        start.tz_localize(None).to_period("M"),
        (end - pd.Timedelta(nanoseconds=1)).tz_localize(None).to_period("M"),
        freq="M",
    )
    monthly = (
        selected.assign(month=selected["entry_time"].dt.tz_localize(None).dt.to_period("M"))
        .groupby("month", sort=True)["stress_net_r"]
        .sum()
        .reindex(month_index, fill_value=0.0)
    )
    weekdays = int(
        np.busday_count(
            np.datetime64(start.date(), "D"), np.datetime64(end.date(), "D")
        )
    )
    return {
        "trades": int(len(selected)),
        "trades_per_weekday": float(len(selected) / weekdays),
        "stress_net_r": float(stress.sum()),
        "stress_profit_factor": profit_factor(stress),
        "average_stress_r": float(stress.mean()) if len(stress) else 0.0,
        "closed_drawdown_r": float((peak - equity).max()) if len(equity) else 0.0,
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "positive_month_share": float(monthly.gt(0.0).mean()),
    }


def passes_gates(
    metrics: Mapping[str, Mapping[str, Any]], gates: Mapping[str, Any]
) -> bool:
    for window_name, value in metrics.items():
        if not all(
            [
                value["trades"] >= int(gates["minimum_trades"][window_name]),
                value["trades_per_weekday"]
                >= float(gates["minimum_trades_per_weekday"]),
                value["stress_profit_factor"]
                >= float(gates["minimum_stress_profit_factor"]),
                value["average_stress_r"]
                >= float(gates["minimum_average_stress_r"]),
                value["closed_drawdown_r"]
                <= float(gates["maximum_closed_drawdown_r"]),
                value["positive_month_share"]
                >= float(gates["minimum_positive_month_share"]),
                value["top_winners_removed_stress_net_r"] > 0.0,
            ]
        ):
            return False
    return True
