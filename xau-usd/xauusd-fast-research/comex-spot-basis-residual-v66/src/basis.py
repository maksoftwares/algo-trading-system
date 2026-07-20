from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
from pathlib import Path
from typing import Any, Iterator, Mapping

import numpy as np
import pandas as pd


SOURCE_DATE = re.compile(r"(\d{8})\.trades\.dbn(?:\.zst)?$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_instrument_map(config: Mapping[str, Any]) -> tuple[pd.DataFrame, str]:
    import databento as db

    source = config["comex_source"]
    manifest = Path(str(source["download_manifest"]))
    if sha256_file(manifest) != str(source["download_manifest_sha256"]):
        raise ValueError("COMEX download manifest hash mismatch")
    rows: list[dict[str, Any]] = []
    for path in sorted(Path(str(source["raw_job_directory"])).rglob("*.dbn.zst")):
        match = SOURCE_DATE.search(path.name)
        if not match:
            continue
        store = db.DBNStore.from_file(path)
        intervals = store.mappings.get(str(source["symbol"]), [])
        if len(intervals) != 1:
            raise ValueError(f"Expected one continuous-symbol mapping in {path}")
        interval = intervals[0]
        source_date = pd.Timestamp(match.group(1)).date()
        if interval["start_date"] != source_date:
            raise ValueError(f"Filename and mapping date disagree in {path}")
        rows.append(
            {
                "session_date": source_date.isoformat(),
                "instrument_id": int(interval["symbol"]),
                "source_file": path.name,
            }
        )
    frame = pd.DataFrame(rows).sort_values("session_date", kind="mergesort")
    if frame.empty or frame["session_date"].duplicated().any():
        raise ValueError("Invalid COMEX instrument map")
    payload = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return frame.reset_index(drop=True), hashlib.sha256(payload).hexdigest()


def load_aligned_bars(
    config: Mapping[str, Any], instrument_map: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    cutoff = pd.Timestamp(config["selection_cutoff_exclusive_utc"])
    comex_source = config["comex_source"]
    comex_path = Path(str(comex_source["cache"]))
    if sha256_file(comex_path) != str(comex_source["cache_sha256"]):
        raise ValueError("COMEX cache hash mismatch")
    comex = pd.read_parquet(
        comex_path,
        columns=["available_time_utc", "session_date", "session_bar_index", "close"],
        filters=[("available_time_utc", "<", cutoff)],
    ).rename(columns={"close": "gc_close"})
    comex["available_time_utc"] = pd.to_datetime(comex["available_time_utc"], utc=True)
    comex = comex.merge(instrument_map, on="session_date", how="left", validate="many_to_one")
    if comex["instrument_id"].isna().any():
        missing = comex.loc[comex["instrument_id"].isna(), "session_date"].unique()
        raise ValueError(f"Missing instrument mapping for {missing[:5]}")

    spot_source = config["spot_source"]
    storage = Path(
        os.environ.get(
            str(spot_source["storage_environment_variable"]),
            str(spot_source["default_storage_root"]),
        )
    )
    spot_path = storage / str(spot_source["feature_cache"])
    if sha256_file(spot_path) != str(spot_source["feature_sha256"]):
        raise ValueError("Spot cache hash mismatch")
    cutoff_ms = int(cutoff.timestamp() * 1000)
    spot_columns = [
        "timestamp_ms",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
        "mid_close",
        "atr",
    ]
    spot = pd.read_parquet(
        spot_path,
        columns=spot_columns,
        filters=[("timestamp_ms", "<", cutoff_ms)],
    )
    spot["bar_start_utc"] = pd.to_datetime(spot.pop("timestamp_ms"), unit="ms", utc=True)
    spot["available_time_utc"] = spot["bar_start_utc"] + pd.Timedelta(minutes=5)
    spot = spot.loc[spot["available_time_utc"].lt(cutoff)].copy()
    aligned = comex.merge(
        spot,
        on="available_time_utc",
        how="inner",
        validate="one_to_one",
    ).sort_values("available_time_utc", kind="mergesort")
    aligned["instrument_id"] = aligned["instrument_id"].astype(int)
    if not aligned["available_time_utc"].lt(cutoff).all():
        raise ValueError("Final-year rows entered V66 selection")
    evidence = {
        "comex_cache": str(comex_path),
        "comex_sha256": sha256_file(comex_path),
        "spot_cache": str(spot_path),
        "spot_sha256": sha256_file(spot_path),
        "aligned_rows": int(len(aligned)),
        "spot_execution_rows": int(len(spot)),
        "sessions": int(aligned["session_date"].nunique()),
        "instruments": int(aligned["instrument_id"].nunique()),
        "first_available_utc": str(aligned["available_time_utc"].min()),
        "last_available_utc": str(aligned["available_time_utc"].max()),
    }
    return aligned.reset_index(drop=True), spot.reset_index(drop=True), evidence


def parameter_grid(config: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    grid = config["parameter_grid"]
    keys = [
        "action_modes",
        "basis_lookback_bars",
        "basis_z_threshold",
        "widening_bars",
        "minimum_return_gap_atr",
        "stop_atr",
        "target_r",
    ]
    for values in itertools.product(*(grid[key] for key in keys)):
        yield {
            "action_mode": str(values[0]),
            "basis_lookback_bars": int(values[1]),
            "basis_z_threshold": float(values[2]),
            "widening_bars": int(values[3]),
            "minimum_return_gap_atr": float(values[4]),
            "stop_atr": float(values[5]),
            "target_r": float(values[6]),
        }


def variant_id(params: Mapping[str, Any]) -> str:
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(f"V66|{payload}".encode("ascii")).hexdigest()
    return f"V66_{digest[:16]}"


def rolling_median_mad(values: pd.Series, lookback: int) -> tuple[pd.Series, pd.Series]:
    shifted = values.shift(1)
    median = shifted.rolling(lookback, min_periods=lookback).median()
    mad = shifted.rolling(lookback, min_periods=lookback).apply(
        lambda window: float(np.median(np.abs(window - np.median(window)))), raw=True
    )
    return median, mad


def prepare_features(
    aligned: pd.DataFrame, config: Mapping[str, Any]
) -> dict[int, pd.DataFrame]:
    frame = aligned.copy()
    frame["basis"] = frame["gc_close"] - frame["mid_close"]
    results: dict[int, pd.DataFrame] = {}
    for lookback in sorted(set(config["parameter_grid"]["basis_lookback_bars"])):
        parts: list[pd.DataFrame] = []
        for _, group in frame.groupby("instrument_id", sort=False, observed=True):
            group = group.sort_values("available_time_utc", kind="mergesort").copy()
            center, mad = rolling_median_mad(group["basis"], int(lookback))
            group["basis_center"] = center
            group["basis_scaled_mad"] = (
                mad * float(config["features"]["mad_scale"])
            ).clip(lower=float(config["features"]["minimum_scaled_mad_price"]))
            group["basis_z"] = (group["basis"] - center) / group["basis_scaled_mad"]
            parts.append(group)
        results[int(lookback)] = pd.concat(parts, ignore_index=True).sort_values(
            "available_time_utc", kind="mergesort"
        )
    return results


def candidate_signals(
    features: pd.DataFrame, params: Mapping[str, Any]
) -> pd.DataFrame:
    bars = int(params["widening_bars"])
    shifted = features.shift(bars)
    same_session = features["session_date"].eq(shifted["session_date"])
    same_instrument = features["instrument_id"].eq(shifted["instrument_id"])
    residual_sign = np.sign(features["basis_z"])
    basis_change = features["basis"] - shifted["basis"]
    gc_return = features["gc_close"] - shifted["gc_close"]
    spot_return = features["mid_close"] - shifted["mid_close"]
    return_gap = gc_return - spot_return
    widening = residual_sign * basis_change > 0.0
    futures_driven = residual_sign * gc_return > 0.0
    gap_large = residual_sign * return_gap >= (
        float(params["minimum_return_gap_atr"]) * features["atr"]
    )
    mask = (
        features["basis_z"].abs().ge(float(params["basis_z_threshold"]))
        & same_instrument
        & same_session
        & widening
        & futures_driven
        & gap_large
        & np.isfinite(features["atr"])
        & features["atr"].gt(0.0)
    )
    selected = features.loc[mask].copy()
    side = np.sign(selected["basis_z"]).astype(int)
    if str(params["action_mode"]) == "FADE":
        side *= -1
    selected["direction"] = np.where(side > 0, "LONG", "SHORT")
    selected["signal_time"] = selected["available_time_utc"]
    selected["stop_distance"] = float(params["stop_atr"]) * selected["atr"]
    selected["target_r"] = float(params["target_r"])
    return selected[
        [
            "signal_time",
            "direction",
            "stop_distance",
            "target_r",
            "basis",
            "basis_z",
            "instrument_id",
            "session_date",
        ]
    ].reset_index(drop=True)


def market_arrays(spot: pd.DataFrame) -> dict[str, np.ndarray]:
    ordered = spot.sort_values("bar_start_utc", kind="mergesort")
    arrays = {
        "starts": ordered["bar_start_utc"].to_numpy(dtype="datetime64[ns]"),
        "ends": ordered["available_time_utc"].to_numpy(dtype="datetime64[ns]"),
    }
    for side in ("bid", "ask"):
        for field in ("open", "high", "low", "close"):
            arrays[f"{side}_{field}"] = ordered[f"{side}_{field}"].to_numpy(dtype=float)
    return arrays


def simulate_signal(
    arrays: Mapping[str, np.ndarray],
    signal_time: pd.Timestamp,
    direction: str,
    stop_distance: float,
    target_r: float,
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
    end_index = min(len(starts), entry_index + int(execution["maximum_hold_bars"]))
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
        "entry_spread": spread,
        "entry_spread_r": spread / risk,
        "net_r": net_r,
        "stress_net_r": stress_net_r,
        "exit_reason": exit_reason,
        "ambiguous_m5": ambiguous,
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
    }


def simulate_candidates(
    candidates: pd.DataFrame,
    arrays: Mapping[str, np.ndarray],
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
        )
        if key not in cache:
            cache[key] = simulate_signal(
                arrays,
                pd.Timestamp(signal.signal_time),
                str(signal.direction),
                float(signal.stop_distance),
                float(signal.target_r),
                execution,
            )
        outcome = cache[key]
        if outcome is not None:
            rows.append({**signal._asdict(), **outcome})
    return pd.DataFrame(rows)


def apply_policy(
    trades: pd.DataFrame,
    maximum_open: int,
    maximum_daily: int,
    cooldown_bars: int,
) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    ordered = trades.sort_values(["entry_time", "signal_time"], kind="mergesort")
    active: list[pd.Timestamp] = []
    daily: dict[Any, int] = {}
    accepted: list[int] = []
    last_entry: pd.Timestamp | None = None
    cooldown = pd.Timedelta(minutes=5 * int(cooldown_bars))
    for index, trade in ordered.iterrows():
        entry_time = trade["entry_time"]
        active = [value for value in active if value > entry_time]
        day = entry_time.date()
        if len(active) >= int(maximum_open) or daily.get(day, 0) >= int(maximum_daily):
            continue
        if last_entry is not None and entry_time - last_entry < cooldown:
            continue
        accepted.append(index)
        active.append(trade["exit_time"])
        daily[day] = daily.get(day, 0) + 1
        last_entry = entry_time
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
