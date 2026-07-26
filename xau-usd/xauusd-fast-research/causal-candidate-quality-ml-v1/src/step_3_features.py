from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from step_3_common import (
    HOUR_MS,
    M5_MS,
    sha256_file,
    stable_parquet,
    timestamp_ms,
    write_json,
)
from step_3_sources import ComexTradeStore, LockedDukascopyStore, SourceDataError


def _aggregate_hour_to_m5(
    times: np.ndarray, bids: np.ndarray, asks: np.ndarray
) -> pd.DataFrame:
    if not len(times):
        return pd.DataFrame(
            columns=["timestamp_ms", "mid_high", "mid_low", "mid_close"]
        )
    mids = (bids + asks) / 2.0
    bins = (times // M5_MS) * M5_MS
    unique, starts = np.unique(bins, return_index=True)
    highs = np.maximum.reduceat(mids, starts)
    lows = np.minimum.reduceat(mids, starts)
    ends = np.r_[starts[1:] - 1, len(mids) - 1]
    return pd.DataFrame(
        {
            "timestamp_ms": unique.astype(np.int64),
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": mids[ends],
        }
    )


def build_atr_reference(
    *,
    output_path: Path,
    manifest_path: Path,
    xau_store: LockedDukascopyStore,
    post2016_cache_path: Path,
    source_corpus_sha256: str,
    pre2016_end_ms: int,
) -> pd.DataFrame:
    if output_path.is_file() and manifest_path.is_file():
        manifest = pd.read_json(manifest_path, typ="series")
        if (
            str(manifest["source_corpus_sha256"]) == source_corpus_sha256
            and str(manifest["post2016_cache_sha256"])
            == sha256_file(post2016_cache_path)
            and str(manifest["atr_reference_sha256"]) == sha256_file(output_path)
        ):
            return pd.read_parquet(output_path)

    pieces: list[pd.DataFrame] = []
    first_hour = xau_store.start_ms // HOUR_MS
    final_hour = (pre2016_end_ms - 1) // HOUR_MS
    for count, hour_key in enumerate(range(first_hour, final_hour + 1), start=1):
        times, bids, asks = xau_store.load_hour(hour_key)
        frame = _aggregate_hour_to_m5(times, bids, asks)
        if not frame.empty:
            pieces.append(frame)
        if count % 10_000 == 0:
            print(
                f"pre2016_atr_hours={count}/{final_hour - first_hour + 1}", flush=True
            )
    pre = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
    post = pd.read_parquet(
        post2016_cache_path,
        columns=["timestamp_ms", "mid_high", "mid_low", "mid_close"],
    )
    bars = pd.concat([pre, post], ignore_index=True)
    bars = bars.sort_values("timestamp_ms", kind="stable").reset_index(drop=True)
    if bars["timestamp_ms"].duplicated().any():
        raise ValueError("XAU M5 ATR reference contains duplicate bar starts")
    previous_close = bars["mid_close"].shift(1)
    true_range = pd.concat(
        [
            bars["mid_high"] - bars["mid_low"],
            (bars["mid_high"] - previous_close).abs(),
            (bars["mid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    bars["atr"] = true_range.ewm(alpha=1.0 / 14.0, adjust=False, min_periods=14).mean()
    result = bars[["timestamp_ms", "atr"]].copy()
    stable_parquet(result, output_path)
    write_json(
        manifest_path,
        {
            "schema_version": "xauusd_step_3_m5_atr_reference_v1",
            "source_corpus_sha256": source_corpus_sha256,
            "post2016_cache_sha256": sha256_file(post2016_cache_path),
            "pre2016_end_exclusive_utc": pd.Timestamp(
                pre2016_end_ms, unit="ms", tz="UTC"
            ).isoformat(),
            "rows": len(result),
            "first_bar_start": pd.Timestamp(
                int(result["timestamp_ms"].iloc[0]), unit="ms", tz="UTC"
            ).isoformat(),
            "last_bar_start": pd.Timestamp(
                int(result["timestamp_ms"].iloc[-1]), unit="ms", tz="UTC"
            ).isoformat(),
            "atr_reference_sha256": sha256_file(output_path),
        },
    )
    return result


class CompletedAtrReference:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.times = frame["timestamp_ms"].to_numpy(dtype=np.int64)
        self.values = frame["atr"].to_numpy(dtype=float)

    def at_cutoff(self, cutoff_ms: int) -> float | None:
        latest_completed_start = int(cutoff_ms) - M5_MS
        index = int(
            np.searchsorted(self.times, latest_completed_start, side="right") - 1
        )
        if (
            index < 0
            or not np.isfinite(self.values[index])
            or self.values[index] <= 0.0
        ):
            return None
        return float(self.values[index])


def _window(
    times: np.ndarray,
    bids: np.ndarray,
    asks: np.ndarray,
    *,
    cutoff_ms: int,
    width_ms: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    left = int(np.searchsorted(times, cutoff_ms - width_ms, side="right"))
    right = int(np.searchsorted(times, cutoff_ms, side="right"))
    return times[left:right], bids[left:right], asks[left:right]


def _mid_change_at_completed_endpoints(
    times: np.ndarray, mids: np.ndarray, cutoff_ms: int, width_ms: int
) -> float | None:
    current_endpoint = (cutoff_ms // HOUR_MS) * HOUR_MS
    prior_endpoint = current_endpoint - width_ms
    current_index = int(np.searchsorted(times, current_endpoint, side="right") - 1)
    prior_index = int(np.searchsorted(times, prior_endpoint, side="right") - 1)
    if current_index < 0 or prior_index < 0:
        return None
    return float(mids[current_index] - mids[prior_index])


def _raw_window_stats(
    times: np.ndarray,
    bids: np.ndarray,
    asks: np.ndarray,
    *,
    cutoff_ms: int,
    width_ms: int,
) -> dict[str, float | int | None]:
    local_times, local_bids, local_asks = _window(
        times, bids, asks, cutoff_ms=cutoff_ms, width_ms=width_ms
    )
    if not len(local_times):
        return {
            "count": 0,
            "change": None,
            "range": None,
            "variance": None,
            "efficiency": None,
            "imbalance": None,
        }
    mids = (local_bids + local_asks) / 2.0
    differences = np.diff(mids)
    nonzero = differences[differences != 0.0]
    path = float(np.abs(differences).sum())
    change = float(mids[-1] - mids[0])
    return {
        "count": len(local_times),
        "change": change,
        "range": float(np.max(mids) - np.min(mids)),
        "variance": float(np.square(differences).sum()),
        "efficiency": abs(change) / path if path > 0.0 else None,
        "imbalance": (
            float((np.sum(nonzero > 0.0) - np.sum(nonzero < 0.0)) / len(nonzero))
            if len(nonzero)
            else None
        ),
    }


def _xau_feature_status(values: Mapping[str, Any], quote_age: float) -> str:
    if any(value is None or pd.isna(value) for value in values.values()):
        return "ABSTAIN_MISSING_MANDATORY_XAU"
    if quote_age > 300.0:
        return "ABSTAIN_STALE_XAU"
    return "PASS"


def xau_features(
    row: Mapping[str, Any],
    *,
    store: LockedDukascopyStore,
    atr_source: CompletedAtrReference,
) -> tuple[dict[str, Any], str]:
    cutoff_ms = timestamp_ms(row["feature_cutoff_time"])
    direction = 1.0 if str(row["direction"]) == "LONG" else -1.0
    atr = atr_source.at_cutoff(cutoff_ms)
    try:
        times, bids, asks = store.ticks_between(cutoff_ms - 26 * HOUR_MS, cutoff_ms)
    except SourceDataError:
        return {}, "ABSTAIN_CORRUPT_XAU"
    if not len(times) or atr is None:
        return {}, "ABSTAIN_MISSING_MANDATORY_XAU"
    last_index = int(np.searchsorted(times, cutoff_ms, side="right") - 1)
    if last_index < 0:
        return {}, "ABSTAIN_MISSING_MANDATORY_XAU"
    quote_age = (cutoff_ms - int(times[last_index])) / 1000.0
    spreads = asks - bids
    mids = (bids + asks) / 2.0
    stats = {
        width: _raw_window_stats(times, bids, asks, cutoff_ms=cutoff_ms, width_ms=width)
        for width in (30_000, 300_000, 900_000, 3_600_000)
    }
    spread_30 = _window(times, bids, asks, cutoff_ms=cutoff_ms, width_ms=30_000)
    spread_5m = _window(times, bids, asks, cutoff_ms=cutoff_ms, width_ms=300_000)
    count_15m = int(stats[900_000]["count"] or 0)
    count_60m = int(stats[3_600_000]["count"] or 0)

    def divided(value: Any, denominator: float) -> float | None:
        return (
            float(value) / denominator
            if value is not None and denominator > 0.0
            else None
        )

    values: dict[str, Any] = {
        "xau_spread_last_atr": float(spreads[last_index]) / atr,
        "xau_spread_mean_30s_atr": (
            float(np.mean(spread_30[2] - spread_30[1])) / atr
            if len(spread_30[0])
            else None
        ),
        "xau_spread_max_5m_atr": (
            float(np.max(spread_5m[2] - spread_5m[1])) / atr
            if len(spread_5m[0])
            else None
        ),
        "xau_quote_age_seconds": quote_age,
        "xau_tick_count_log1p_30s": math.log1p(int(stats[30_000]["count"] or 0)),
        "xau_tick_count_log1p_5m": math.log1p(int(stats[300_000]["count"] or 0)),
        "xau_quote_intensity_ratio_15m_60m": count_15m / max(count_60m / 4.0, 1.0),
    }
    labels = {30_000: "30s", 300_000: "5m", 900_000: "15m", 3_600_000: "60m"}
    for width, suffix in labels.items():
        if suffix in {"30s", "5m", "15m", "60m"}:
            values[f"dir_xau_return_{suffix}_atr"] = (
                direction * divided(stats[width]["change"], atr)
                if stats[width]["change"] is not None
                else None
            )
        if suffix in {"5m", "15m", "60m"}:
            values[f"xau_range_{suffix}_atr"] = divided(stats[width]["range"], atr)
            values[f"xau_realized_variance_{suffix}_atr2"] = divided(
                stats[width]["variance"], atr * atr
            )
            values[f"xau_efficiency_{suffix}"] = stats[width]["efficiency"]
        if suffix in {"5m", "15m"}:
            imbalance = stats[width]["imbalance"]
            values[f"dir_xau_tick_imbalance_{suffix}"] = (
                direction * float(imbalance) if imbalance is not None else None
            )
    for hours, suffix in ((4, "4h"), (24, "24h")):
        change = _mid_change_at_completed_endpoints(
            times, mids, cutoff_ms, hours * HOUR_MS
        )
        values[f"dir_xau_return_{suffix}_atr"] = (
            direction * change / atr if change is not None else None
        )
    status = _xau_feature_status(values, quote_age)
    return values, status


def _quote_at_or_before(
    times: np.ndarray, mids: np.ndarray, timestamp: int
) -> tuple[int, float] | None:
    index = int(np.searchsorted(times, timestamp, side="right") - 1)
    if index < 0:
        return None
    return int(times[index]), float(mids[index])


def crossasset_features(
    row: Mapping[str, Any],
    *,
    dollar_store: LockedDukascopyStore,
    bond_store: LockedDukascopyStore,
) -> tuple[dict[str, Any], str]:
    cutoff_ms = timestamp_ms(row["feature_cutoff_time"])
    direction = 1.0 if str(row["direction"]) == "LONG" else -1.0
    endpoint = (cutoff_ms // HOUR_MS) * HOUR_MS
    values: dict[str, Any] = {}
    ages: list[float] = []
    available = 0
    for name, store, sign in (
        ("inverse_dollar", dollar_store, -direction),
        ("bond", bond_store, direction),
    ):
        if endpoint < store.start_ms:
            for hours in (1, 4, 24):
                values[f"dir_{name}_return_{hours}h"] = None
            continue
        try:
            times, bids, asks = store.ticks_between(endpoint - 26 * HOUR_MS, endpoint)
        except SourceDataError:
            times = np.array([], dtype=np.int64)
            bids = asks = np.array([], dtype=float)
        mids = (bids + asks) / 2.0
        current = _quote_at_or_before(times, mids, endpoint)
        if current is None:
            for hours in (1, 4, 24):
                values[f"dir_{name}_return_{hours}h"] = None
            continue
        ages.append((cutoff_ms - current[0]) / 1000.0)
        for hours in (1, 4, 24):
            previous = _quote_at_or_before(times, mids, endpoint - hours * HOUR_MS)
            feature = f"dir_{name}_return_{hours}h"
            if previous is None or previous[1] <= 0.0 or current[1] <= 0.0:
                values[feature] = None
            else:
                values[feature] = sign * math.log(current[1] / previous[1])
                available += 1
    values["crossasset_max_staleness_seconds"] = max(ages) if ages else None
    values["crossasset_coverage_fraction"] = available / 6.0
    if not ages:
        status = "UNAVAILABLE_BEFORE_SOURCE_START"
    elif max(ages) > 7200.0:
        status = "ABSTAIN_STALE_CROSSASSET"
    elif available < 6:
        status = "ABSTAIN_INCOMPLETE_CROSSASSET"
    else:
        status = "PASS"
    return values, status


def _log_return(frame: pd.DataFrame) -> float | None:
    if len(frame) < 2:
        return None
    first = float(frame["price"].iloc[0])
    last = float(frame["price"].iloc[-1])
    if first <= 0.0 or last <= 0.0:
        return None
    return math.log(last / first)


def comex_features(
    row: Mapping[str, Any],
    *,
    store: ComexTradeStore,
    xau_store: LockedDukascopyStore,
) -> tuple[dict[str, Any], str]:
    cutoff = pd.Timestamp(row["feature_cutoff_time"])
    eligible_end = cutoff - pd.Timedelta(seconds=1)
    if eligible_end.strftime("%Y%m%d") < min(store.records):
        return {}, "UNAVAILABLE_BEFORE_COMEX_START"
    direction = 1.0 if str(row["direction"]) == "LONG" else -1.0
    try:
        frame = store.window(eligible_end - pd.Timedelta(hours=24), eligible_end)
    except SourceDataError:
        return {}, "ABSTAIN_CORRUPT_COMEX"
    if frame.empty:
        return {}, "ABSTAIN_MISSING_COMEX"
    last_instrument = frame["instrument_id"].iloc[-1]
    current = frame.loc[frame["instrument_id"].eq(last_instrument)].copy()
    last_age = (eligible_end - pd.Timestamp(frame["ts_event"].iloc[-1])).total_seconds()
    values: dict[str, Any] = {
        "gc_roll_boundary_24h_flag": float(frame["instrument_id"].nunique() > 1),
        "gc_last_event_age_seconds": last_age,
    }
    windows: dict[int, pd.DataFrame] = {}
    for minutes in (5, 60):
        local = current.loc[
            current["ts_event"].gt(eligible_end - pd.Timedelta(minutes=minutes))
        ]
        windows[minutes] = local
        values[f"gc_trade_count_log1p_{minutes}m"] = math.log1p(len(local))
        values[f"gc_volume_log1p_{minutes}m"] = math.log1p(
            float(pd.to_numeric(local["size"], errors="coerce").sum())
        )
        side = local["side"].astype(str)
        sizes = pd.to_numeric(local["size"], errors="coerce").to_numpy(dtype=float)
        buy = float(sizes[side.eq("B").to_numpy()].sum())
        sell = float(sizes[side.eq("A").to_numpy()].sum())
        known = buy + sell
        values[f"dir_gc_delta_ratio_{minutes}m"] = (
            direction * (buy - sell) / known if known > 0.0 else None
        )
        ret = _log_return(local)
        values[f"dir_gc_return_{minutes}m"] = (
            direction * ret if ret is not None else None
        )
    gc_15 = current.loc[current["ts_event"].gt(eligible_end - pd.Timedelta(minutes=15))]
    gc_return_15 = _log_return(gc_15)
    end_ms = timestamp_ms(eligible_end)
    try:
        x_times, x_bids, x_asks = xau_store.ticks_between(end_ms - 900_000, end_ms)
    except SourceDataError:
        x_times = np.array([], dtype=np.int64)
        x_bids = x_asks = np.array([], dtype=float)
    xau_return_15 = None
    if len(x_times) >= 2:
        mids = (x_bids + x_asks) / 2.0
        if mids[0] > 0.0 and mids[-1] > 0.0:
            xau_return_15 = math.log(float(mids[-1] / mids[0]))
    values["dir_gc_minus_spot_return_15m"] = (
        direction * (gc_return_15 - xau_return_15)
        if gc_return_15 is not None and xau_return_15 is not None
        else None
    )
    status = "PASS" if last_age <= 300.0 else "ABSTAIN_STALE_COMEX"
    return values, status


def deterministic_features(
    row: Mapping[str, Any], *, mechanic_mapping: Mapping[str, str], atr: float | None
) -> dict[str, Any]:
    decision = pd.Timestamp(row["decision_time"])
    minute = decision.hour * 60 + decision.minute + decision.second / 60.0
    angle = 2.0 * math.pi * minute / 1440.0
    weekday_angle = 2.0 * math.pi * decision.weekday() / 7.0
    stop_price = float(row["planned_stop_price"])
    target_absent = str(row["target_mode"]) == "NONE"
    return {
        "family_id": str(row["family_id"]),
        "broad_mechanic": str(mechanic_mapping[str(row["family_id"])]),
        "direction_sign": 1.0 if str(row["direction"]) == "LONG" else -1.0,
        "stop_mode": str(row["stop_mode"]),
        "target_mode": str(row["target_mode"]),
        "planned_stop_atr": stop_price / atr if atr is not None and atr > 0.0 else None,
        "planned_stop_price": stop_price,
        "stop_floor_price": (
            float(row["stop_floor_price"]) if pd.notna(row["stop_floor_price"]) else 0.0
        ),
        "target_r_filled": float(row["target_r"]) if pd.notna(row["target_r"]) else 0.0,
        "target_absent_flag": float(target_absent),
        "log1p_observation_cap_minutes": math.log1p(
            float(row["label_observation_cap_minutes"])
        ),
        "barrier_only_flag": float(
            str(row["maximum_hold_mode"]) == "BARRIER_ONLY_NO_TIME_STOP"
        ),
        "utc_hour_sin": math.sin(angle),
        "utc_hour_cos": math.cos(angle),
        "utc_weekday_sin": math.sin(weekday_angle),
        "utc_weekday_cos": math.cos(weekday_angle),
    }


def build_feature_frame(
    canonical: pd.DataFrame,
    *,
    contract: Mapping[str, Any],
    atr_source: CompletedAtrReference,
    xau_store: LockedDukascopyStore,
    dollar_store: LockedDukascopyStore,
    bond_store: LockedDukascopyStore,
    comex_store: ComexTradeStore,
) -> pd.DataFrame:
    feature_names = [
        name
        for block in contract["feature_contract"]["ordered_blocks"]
        for name in block["features"]
    ]
    rows: list[dict[str, Any]] = []
    ordered = canonical.sort_values(
        ["feature_cutoff_time", "candidate_id"], kind="stable"
    )
    for index, row in enumerate(ordered.to_dict("records"), start=1):
        cutoff_ms = timestamp_ms(row["feature_cutoff_time"])
        atr = atr_source.at_cutoff(cutoff_ms)
        b1 = deterministic_features(
            row, mechanic_mapping=contract["broad_mechanic_mapping"], atr=atr
        )
        b2, xau_status = xau_features(row, store=xau_store, atr_source=atr_source)
        b3, cross_status = crossasset_features(
            row, dollar_store=dollar_store, bond_store=bond_store
        )
        b4, comex_status = comex_features(row, store=comex_store, xau_store=xau_store)
        values = {name: None for name in feature_names}
        values.update(b1)
        values.update(b2)
        values.update(b3)
        values.update(b4)
        rows.append(
            {
                "candidate_id": str(row["candidate_id"]),
                **values,
                "xau_feature_status": xau_status,
                "crossasset_feature_status": cross_status,
                "comex_feature_status": comex_status,
            }
        )
        if index % 250 == 0:
            print(f"feature_rows={index}/{len(ordered)}", flush=True)
    result = pd.DataFrame(rows)
    result = result[
        [
            "candidate_id",
            *feature_names,
            "xau_feature_status",
            "crossasset_feature_status",
            "comex_feature_status",
        ]
    ]
    if len(result) != len(canonical) or result["candidate_id"].duplicated().any():
        raise ValueError("Canonical feature cardinality changed")
    numeric = result.select_dtypes(include=[np.number])
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        raise ValueError("Canonical features contain infinity")
    return result
