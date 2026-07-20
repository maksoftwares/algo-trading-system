from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


def canonical_hash(payload: Mapping[str, Any], field: str) -> str:
    clean = {key: value for key, value in payload.items() if key != field}
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def timestamp_milliseconds(values: pd.Series) -> np.ndarray:
    timestamps = pd.to_datetime(values, utc=True)
    return timestamps.dt.as_unit("ms").astype("int64").to_numpy(dtype=np.int64)


def _clock_minutes(value: str) -> int:
    hour, minute = (int(part) for part in value.split(":"))
    return hour * 60 + minute


def normalize_received_trades(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "ts_recv" not in result.columns and result.index.name == "ts_recv":
        result = result.reset_index()
    required = {
        "ts_recv",
        "ts_event",
        "instrument_id",
        "side",
        "price",
        "size",
    }
    if missing := sorted(required - set(result.columns)):
        raise ValueError(f"Received trade data is missing columns: {missing}")
    result["ts_recv"] = pd.to_datetime(result["ts_recv"], utc=True)
    result["ts_event"] = pd.to_datetime(result["ts_event"], utc=True)
    if (result["ts_recv"] < result["ts_event"]).any():
        raise ValueError("A COMEX trade was received before its event timestamp")
    result["instrument_id"] = pd.to_numeric(
        result["instrument_id"], errors="raise"
    ).astype("int64")
    result["price"] = pd.to_numeric(result["price"], errors="raise").astype(float)
    result["size"] = pd.to_numeric(result["size"], errors="raise").astype(float)
    if (result["size"] <= 0).any():
        raise ValueError("COMEX trade size must be positive")
    result["side"] = result["side"].astype(str).str.upper().str[0]
    if not result["side"].isin(["A", "B", "N"]).all():
        raise ValueError("Unsupported COMEX aggressor side")
    result["aggressor_sign"] = result["side"].map({"B": 1.0, "A": -1.0, "N": 0.0})
    return result.sort_values(
        ["ts_recv", "instrument_id", "ts_event"], kind="stable"
    ).reset_index(drop=True)


def received_session(frame: pd.DataFrame, rule: Mapping[str, Any]) -> pd.DataFrame:
    normalized = normalize_received_trades(frame)
    local = normalized["ts_recv"].dt.tz_convert(str(rule["timezone"]))
    minutes = local.dt.hour * 60 + local.dt.minute + local.dt.second / 60.0
    start = _clock_minutes(str(rule["session_start"]))
    end = _clock_minutes(str(rule["session_end"]))
    return normalized.loc[(minutes >= start) & (minutes < end)].copy()


def bucket_received_trades(frame: pd.DataFrame, *, bucket_ms: int) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    normalized = normalize_received_trades(frame)
    width = pd.Timedelta(milliseconds=int(bucket_ms))
    normalized["feature_time_utc"] = (
        normalized["ts_recv"].dt.floor(f"{int(bucket_ms)}ms") + width
    )
    normalized["signed_volume"] = normalized["size"] * normalized["aggressor_sign"]
    grouped = normalized.groupby(
        ["instrument_id", "feature_time_utc"], sort=True, observed=True
    )
    buckets = grouped.agg(
        last_source_recv_utc=("ts_recv", "max"),
        last_source_event_utc=("ts_event", "max"),
        comex_price=("price", "last"),
        received_volume=("size", "sum"),
        received_signed_volume=("signed_volume", "sum"),
        received_trade_count=("size", "size"),
    ).reset_index()
    if not (buckets["last_source_recv_utc"] < buckets["feature_time_utc"]).all():
        raise ValueError("A receipt bucket contains unavailable source data")
    return buckets


def spot_quote_frame(
    tick_store: Any, *, start_timestamp_ms: int, end_timestamp_ms: int
) -> pd.DataFrame:
    rows = [
        {
            "timestamp_ms": int(tick.timestamp_ms),
            "bid": float(tick.bid),
            "ask": float(tick.ask),
        }
        for tick in tick_store.ticks_between(start_timestamp_ms, end_timestamp_ms)
    ]
    if not rows:
        return pd.DataFrame(columns=["timestamp_ms", "bid", "ask", "mid"])
    quotes = pd.DataFrame(rows)
    if (quotes["ask"] < quotes["bid"]).any():
        raise ValueError("Dukascopy quote stream contains a crossed quote")
    quotes = quotes.sort_values("timestamp_ms", kind="stable")
    quotes = quotes.drop_duplicates("timestamp_ms", keep="last").reset_index(drop=True)
    quotes["mid"] = (quotes["bid"] + quotes["ask"]) / 2.0
    return quotes


def _strict_asof(
    timestamps_ms: np.ndarray, values: np.ndarray, targets_ms: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    indices = np.searchsorted(timestamps_ms, targets_ms, side="left") - 1
    found = indices >= 0
    selected = np.full(len(targets_ms), np.nan, dtype=float)
    selected_time = np.full(len(targets_ms), -1, dtype=np.int64)
    selected[found] = values[indices[found]]
    selected_time[found] = timestamps_ms[indices[found]]
    return selected, selected_time


def build_innovation_features(
    buckets: pd.DataFrame,
    quotes: pd.DataFrame,
    *,
    horizon_ms: int,
    maximum_spot_quote_staleness_ms: int,
    maximum_comex_baseline_staleness_ms: int,
) -> pd.DataFrame:
    if buckets.empty or quotes.empty:
        return pd.DataFrame()
    quote_times = quotes["timestamp_ms"].to_numpy(dtype=np.int64)
    quote_mid = quotes["mid"].to_numpy(dtype=float)
    groups: list[pd.DataFrame] = []
    for _, raw_group in buckets.groupby("instrument_id", sort=False, observed=True):
        group = raw_group.sort_values("feature_time_utc", kind="stable").copy()
        decision_ms = timestamp_milliseconds(group["feature_time_utc"])
        target_ms = decision_ms - int(horizon_ms)
        bucket_times = decision_ms
        baseline_indices = np.searchsorted(bucket_times, target_ms, side="right") - 1
        baseline_found = baseline_indices >= 0
        baseline_price = np.full(len(group), np.nan, dtype=float)
        baseline_time = np.full(len(group), -1, dtype=np.int64)
        prices = group["comex_price"].to_numpy(dtype=float)
        baseline_price[baseline_found] = prices[baseline_indices[baseline_found]]
        baseline_time[baseline_found] = bucket_times[baseline_indices[baseline_found]]
        current_mid, current_quote_time = _strict_asof(
            quote_times, quote_mid, decision_ms
        )
        prior_mid, prior_quote_time = _strict_asof(quote_times, quote_mid, target_ms)
        indexed = group.set_index("feature_time_utc")
        volume = (
            indexed["received_volume"]
            .rolling(f"{int(horizon_ms)}ms", closed="right")
            .sum()
            .to_numpy()
        )
        signed = (
            indexed["received_signed_volume"]
            .rolling(f"{int(horizon_ms)}ms", closed="right")
            .sum()
            .to_numpy()
        )
        imbalance = np.divide(
            signed,
            volume,
            out=np.zeros_like(signed, dtype=float),
            where=volume > 0,
        )
        comex_move = prices - baseline_price
        spot_move = current_mid - prior_mid
        direction_sign = np.sign(comex_move)
        innovation = direction_sign * (comex_move - spot_move)
        group["horizon_ms"] = int(horizon_ms)
        group["decision_timestamp_ms"] = decision_ms
        group["comex_baseline_timestamp_ms"] = baseline_time
        group["current_spot_quote_timestamp_ms"] = current_quote_time
        group["prior_spot_quote_timestamp_ms"] = prior_quote_time
        group["comex_move_usd"] = comex_move
        group["spot_move_usd"] = spot_move
        group["directional_innovation_usd"] = innovation
        group["horizon_received_volume"] = volume
        group["horizon_signed_volume"] = signed
        group["flow_imbalance"] = imbalance
        group["direction"] = np.where(direction_sign > 0, "LONG", "SHORT")
        valid = baseline_found
        valid &= decision_ms - baseline_time - int(horizon_ms) <= int(
            maximum_comex_baseline_staleness_ms
        )
        valid &= current_quote_time >= 0
        valid &= prior_quote_time >= 0
        valid &= decision_ms - current_quote_time <= int(
            maximum_spot_quote_staleness_ms
        )
        valid &= target_ms - prior_quote_time <= int(maximum_spot_quote_staleness_ms)
        valid &= direction_sign != 0
        valid &= innovation > 0
        valid &= np.sign(imbalance) == direction_sign
        groups.append(group.loc[valid].copy())
    if not groups:
        return pd.DataFrame()
    return (
        pd.concat(groups, ignore_index=True)
        .sort_values(["feature_time_utc", "instrument_id", "horizon_ms"], kind="stable")
        .reset_index(drop=True)
    )


def policy_grid(calibration: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for values in itertools.product(
        calibration["horizon_ms_grid"],
        calibration["minimum_absolute_comex_move_usd_grid"],
        calibration["minimum_directional_innovation_usd_grid"],
        calibration["minimum_absolute_flow_imbalance_grid"],
        calibration["minimum_received_volume_grid"],
    ):
        horizon, move, innovation, imbalance, volume = values
        rows.append(
            {
                "horizon_ms": int(horizon),
                "minimum_absolute_comex_move_usd": float(move),
                "minimum_directional_innovation_usd": float(innovation),
                "minimum_absolute_flow_imbalance": float(imbalance),
                "minimum_received_volume": int(volume),
            }
        )
    return rows


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"H{int(policy['horizon_ms']):04d}"
        f"__CM{int(round(float(policy['minimum_absolute_comex_move_usd']) * 100)):03d}"
        f"__IN{int(round(float(policy['minimum_directional_innovation_usd']) * 100)):03d}"
        f"__FI{int(round(float(policy['minimum_absolute_flow_imbalance']) * 100)):02d}"
        f"__VO{int(policy['minimum_received_volume']):02d}"
    )


def generate_candidates(
    features: pd.DataFrame, *, policy: Mapping[str, Any], family: str
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    mask = features["horizon_ms"].eq(int(policy["horizon_ms"]))
    mask &= features["comex_move_usd"].abs() >= float(
        policy["minimum_absolute_comex_move_usd"]
    )
    mask &= features["directional_innovation_usd"] >= float(
        policy["minimum_directional_innovation_usd"]
    )
    mask &= features["flow_imbalance"].abs() >= float(
        policy["minimum_absolute_flow_imbalance"]
    )
    mask &= features["horizon_received_volume"] >= int(
        policy["minimum_received_volume"]
    )
    selected = features.loc[mask].copy()
    if selected.empty:
        return selected
    selected["date_utc"] = selected["feature_time_utc"].dt.date.astype(str)
    selected = selected.sort_values(
        ["feature_time_utc", "instrument_id"], kind="stable"
    )
    selected = selected.groupby("date_utc", sort=True, as_index=False).head(1).copy()
    selected["family"] = family
    selected["policy_id"] = policy_id(policy)
    decision_ms = selected["decision_timestamp_ms"].astype("int64")
    selected.insert(
        0,
        "candidate_id",
        "V69:"
        + selected["policy_id"].astype(str)
        + ":"
        + decision_ms.astype(str)
        + ":"
        + selected["direction"].astype(str),
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V69 candidate IDs are not unique")
    return selected.reset_index(drop=True)


def summarize_candidate_facts(
    candidates: pd.DataFrame,
    *,
    eligible_dates: Sequence[str],
    policy: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> dict[str, Any]:
    trades = len(candidates)
    active_days = int(candidates["date_utc"].nunique()) if trades else 0
    longs = int((candidates["direction"] == "LONG").sum()) if trades else 0
    shorts = int((candidates["direction"] == "SHORT").sum()) if trades else 0
    full_days = len(eligible_dates)
    frequency = trades / full_days if full_days else 0.0
    active_share = active_days / full_days if full_days else 0.0
    minority_share = min(longs, shorts) / trades if trades else 0.0
    selectable = bool(
        float(calibration["minimum_candidates_per_full_weekday"])
        <= frequency
        <= float(calibration["maximum_candidates_per_full_weekday"])
        and active_share >= float(calibration["minimum_active_day_share"])
        and minority_share >= float(calibration["minimum_direction_share"])
    )
    return {
        "policy_id": policy_id(policy),
        **dict(policy),
        "eligible_full_weekdays": full_days,
        "candidates": trades,
        "candidates_per_full_weekday": frequency,
        "active_days": active_days,
        "active_day_share": active_share,
        "long_candidates": longs,
        "short_candidates": shorts,
        "minority_direction_share": minority_share,
        "selection_eligible": selectable,
    }


def select_policy(
    rows: Iterable[Mapping[str, Any]], calibration: Mapping[str, Any]
) -> dict[str, Any] | None:
    eligible = [dict(row) for row in rows if bool(row["selection_eligible"])]
    if not eligible:
        return None
    target = float(calibration["target_candidates_per_full_weekday"])
    eligible.sort(
        key=lambda row: (
            abs(float(row["candidates_per_full_weekday"]) - target),
            -float(row["minimum_absolute_comex_move_usd"]),
            -float(row["minimum_directional_innovation_usd"]),
            -float(row["minimum_absolute_flow_imbalance"]),
            -int(row["minimum_received_volume"]),
            int(row["horizon_ms"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "horizon_ms",
        "minimum_absolute_comex_move_usd",
        "minimum_directional_innovation_usd",
        "minimum_absolute_flow_imbalance",
        "minimum_received_volume",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}
