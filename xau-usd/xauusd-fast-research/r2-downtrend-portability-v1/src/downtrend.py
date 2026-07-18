from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

import numpy as np
import pandas as pd
from scipy import stats


PRICE_COLUMNS = tuple(
    f"{side}_{field}"
    for side in ("bid", "ask", "mid")
    for field in ("open", "high", "low", "close")
)
EXIT_SCAN_BLOCK = 16_384


@dataclass(frozen=True)
class ResearchData:
    m5: pd.DataFrame
    bars: dict[str, pd.DataFrame]
    evidence: dict[str, Any]


@dataclass(frozen=True)
class TickQuote:
    timestamp_ms: int
    bid: float
    ask: float


class VerifiedTickStore:
    def __init__(self, root: Path, config: Mapping[str, Any]) -> None:
        source = config["source"]
        self.old_replay = (root / str(source["old_replay_root"])).resolve()
        self.raw_root = (root / str(source["raw_tick_root"])).resolve()
        self.raw_start_ms = int(
            pd.Timestamp(source["raw_tick_start_utc"]).value // 1_000_000
        )

    @lru_cache(maxsize=4)
    def _load_old_month(
        self, year: int, month: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        path = (
            self.old_replay
            / "normalized"
            / "XAUUSD"
            / f"year={year:04d}"
            / f"month={month:02d}"
            / "ticks.parquet"
        )
        if not path.is_file():
            raise FileNotFoundError(path)
        frame = pd.read_parquet(path, columns=["timestamp_ms", "bid", "ask"])
        return self._validate_arrays(
            frame["timestamp_ms"].to_numpy(dtype=np.int64),
            frame["bid"].to_numpy(dtype=float),
            frame["ask"].to_numpy(dtype=float),
            path,
        )

    @lru_cache(maxsize=12)
    def _load_raw_hour(
        self, year: int, month: int, day: int, hour: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        path = (
            self.raw_root
            / f"year={year:04d}"
            / f"month={month:02d}"
            / f"{year:04d}{month:02d}{day:02d}{hour:02d}.json"
        )
        if not path.is_file():
            raise FileNotFoundError(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
        missing = [
            key
            for key in ("timestamp", "multiplier", "bid", "ask", *arrays)
            if key not in payload
        ]
        if missing:
            raise ValueError(f"Raw tick fields missing in {path}: {missing}")
        lengths = [len(payload[key]) if isinstance(payload[key], list) else -1 for key in arrays]
        if len(set(lengths)) != 1 or lengths[0] < 0:
            raise ValueError(f"Raw tick array lengths differ in {path}: {lengths}")
        if lengths[0] == 0:
            empty_i = np.array([], dtype=np.int64)
            empty_f = np.array([], dtype=float)
            return empty_i, empty_f, empty_f.copy()
        multiplier = float(payload["multiplier"])
        if multiplier <= 0.0:
            raise ValueError(f"Invalid raw tick multiplier in {path}")
        times = int(payload["timestamp"]) + np.cumsum(
            np.asarray(payload["times"], dtype=np.int64), dtype=np.int64
        )
        factor = 1_000.0
        bids = np.floor(
            (
                float(payload["bid"])
                + np.cumsum(np.asarray(payload["bids"], dtype=float)) * multiplier
            )
            * factor
            + 0.5
            + 1e-9
        ) / factor
        asks = np.floor(
            (
                float(payload["ask"])
                + np.cumsum(np.asarray(payload["asks"], dtype=float)) * multiplier
            )
            * factor
            + 0.5
            + 1e-9
        ) / factor
        expected_start = int(
            pd.Timestamp(
                year=year, month=month, day=day, hour=hour, tz="UTC"
            ).value
            // 1_000_000
        )
        if len(times) and (times[0] < expected_start or times[-1] >= expected_start + 3_600_000):
            raise ValueError(f"Raw ticks escape requested hour in {path}")
        return self._validate_arrays(times, bids, asks, path)

    @staticmethod
    def _validate_arrays(
        times: np.ndarray, bids: np.ndarray, asks: np.ndarray, path: Path
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if len(times) != len(bids) or len(times) != len(asks):
            raise ValueError(f"Tick columns differ in length: {path}")
        if len(times) and np.any(np.diff(times) < 0):
            raise ValueError(f"Tick timestamps are not sorted: {path}")
        if np.any(~np.isfinite(bids)) or np.any(~np.isfinite(asks)):
            raise ValueError(f"Non-finite tick quote: {path}")
        if np.any(bids <= 0.0) or np.any(asks <= 0.0) or np.any(asks < bids):
            raise ValueError(f"Invalid tick quote: {path}")
        return times, bids, asks

    def _old_segments(
        self, start_ms: int, end_ms: int
    ) -> Iterator[tuple[np.ndarray, np.ndarray, np.ndarray]]:
        start = pd.Timestamp(start_ms, unit="ms", tz="UTC").tz_localize(None)
        end = pd.Timestamp(end_ms, unit="ms", tz="UTC").tz_localize(None)
        for period in pd.period_range(start.to_period("M"), end.to_period("M"), freq="M"):
            times, bids, asks = self._load_old_month(period.year, period.month)
            left = int(np.searchsorted(times, start_ms, side="left"))
            right = int(np.searchsorted(times, end_ms, side="right"))
            if right > left:
                yield times[left:right], bids[left:right], asks[left:right]

    def _raw_segments(
        self, start_ms: int, end_ms: int
    ) -> Iterator[tuple[np.ndarray, np.ndarray, np.ndarray]]:
        first = pd.Timestamp(start_ms, unit="ms", tz="UTC").floor("h")
        last = pd.Timestamp(end_ms, unit="ms", tz="UTC").floor("h")
        for hour in pd.date_range(first, last, freq="1h"):
            times, bids, asks = self._load_raw_hour(
                hour.year, hour.month, hour.day, hour.hour
            )
            left = int(np.searchsorted(times, start_ms, side="left"))
            right = int(np.searchsorted(times, end_ms, side="right"))
            if right > left:
                yield times[left:right], bids[left:right], asks[left:right]

    def _segments(
        self, start_ms: int, end_ms: int
    ) -> Iterator[tuple[np.ndarray, np.ndarray, np.ndarray]]:
        if end_ms < start_ms:
            return
        if start_ms < self.raw_start_ms:
            yield from self._old_segments(
                start_ms, min(end_ms, self.raw_start_ms - 1)
            )
        if end_ms >= self.raw_start_ms:
            yield from self._raw_segments(max(start_ms, self.raw_start_ms), end_ms)

    def first_quote_at_or_after(
        self, timestamp_ms: int, maximum_delay_ms: int
    ) -> TickQuote | None:
        for times, bids, asks in self._segments(
            timestamp_ms, timestamp_ms + maximum_delay_ms
        ):
            if len(times):
                return TickQuote(int(times[0]), float(bids[0]), float(asks[0]))
        return None

    def first_short_hit(
        self, start_ms: int, end_ms: int, stop: float, target: float
    ) -> tuple[TickQuote, float, str] | None:
        for times, bids, asks in self._segments(start_ms, end_ms):
            hits = np.flatnonzero((asks >= stop) | (asks <= target))
            if len(hits) == 0:
                continue
            index = int(hits[0])
            quote = TickQuote(
                int(times[index]), float(bids[index]), float(asks[index])
            )
            if quote.ask >= stop:
                reason = "STOP" if quote.ask == stop else "STOP_SLIPPAGE"
                return quote, quote.ask, reason
            return quote, target, "TARGET"
        return None

    def last_quote_at_or_before(
        self, timestamp_ms: int, minimum_timestamp_ms: int
    ) -> TickQuote | None:
        if timestamp_ms < minimum_timestamp_ms:
            return None
        if timestamp_ms >= self.raw_start_ms:
            lower = max(minimum_timestamp_ms, self.raw_start_ms)
            first_hour = pd.Timestamp(lower, unit="ms", tz="UTC").floor("h")
            hour = pd.Timestamp(timestamp_ms, unit="ms", tz="UTC").floor("h")
            while hour >= first_hour:
                times, bids, asks = self._load_raw_hour(
                    hour.year, hour.month, hour.day, hour.hour
                )
                right = int(np.searchsorted(times, timestamp_ms, side="right"))
                left = int(np.searchsorted(times, lower, side="left"))
                if right > left:
                    index = right - 1
                    return TickQuote(
                        int(times[index]), float(bids[index]), float(asks[index])
                    )
                hour -= pd.Timedelta(hours=1)
        if minimum_timestamp_ms < self.raw_start_ms:
            upper = min(timestamp_ms, self.raw_start_ms - 1)
            first = pd.Timestamp(
                minimum_timestamp_ms, unit="ms", tz="UTC"
            ).tz_localize(None).to_period("M")
            period = pd.Timestamp(upper, unit="ms", tz="UTC").tz_localize(
                None
            ).to_period("M")
            while period >= first:
                times, bids, asks = self._load_old_month(period.year, period.month)
                right = int(np.searchsorted(times, upper, side="right"))
                left = int(
                    np.searchsorted(times, minimum_timestamp_ms, side="left")
                )
                if right > left:
                    index = right - 1
                    return TickQuote(
                        int(times[index]), float(bids[index]), float(asks[index])
                    )
                period -= 1
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def timestamp_series_ms(values: pd.Series) -> np.ndarray:
    timestamps = pd.to_datetime(values, utc=True).dt.as_unit("ms")
    return timestamps.astype("int64").to_numpy(dtype=np.int64)


def storage_root(config: Mapping[str, Any]) -> Path:
    source = config["source"]
    return Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()


def _load_old_m5(root: Path, config: Mapping[str, Any]) -> pd.DataFrame:
    replay = root / str(config["source"]["old_replay_root"])
    status = json.loads((replay / "status.json").read_text(encoding="utf-8"))
    months = [str(value) for value in status.get("normalized_months", [])]
    if len(months) != 78 or months[0] != "2010-01" or months[-1] != "2016-06":
        raise ValueError("Old replay must contain exactly 2010-01 through 2016-06")
    sides: dict[str, pd.DataFrame] = {}
    for side in ("bid", "ask", "mid"):
        frames: list[pd.DataFrame] = []
        for month in months:
            year, number = month.split("-")
            path = (
                replay
                / "bars"
                / "XAUUSD"
                / side
                / "M5"
                / f"year={year}"
                / f"month={number}"
                / "bars.parquet"
            )
            frame = pd.read_parquet(path)
            frame["bar_start_utc"] = pd.to_datetime(
                frame["timestamp_utc"], utc=True, errors="raise"
            )
            frame = frame.rename(
                columns={field: f"{side}_{field}" for field in ("open", "high", "low", "close")}
            )
            frames.append(
                frame[["bar_start_utc", "tick_count", *[f"{side}_{x}" for x in ("open", "high", "low", "close")]]]
            )
        combined = pd.concat(frames, ignore_index=True).sort_values(
            "bar_start_utc", kind="mergesort"
        )
        if combined["bar_start_utc"].duplicated().any():
            raise ValueError(f"Duplicate old {side} M5 timestamps")
        sides[side] = combined.reset_index(drop=True)
    merged = sides["bid"].rename(columns={"tick_count": "tick_count_bid"})
    merged = merged.merge(
        sides["ask"].rename(columns={"tick_count": "tick_count_ask"}),
        on="bar_start_utc",
        how="inner",
        validate="one_to_one",
    )
    merged = merged.merge(
        sides["mid"].rename(columns={"tick_count": "tick_count_mid"}),
        on="bar_start_utc",
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != len(sides["bid"]):
        raise ValueError("Old Bid/Ask/Mid M5 timestamps do not align")
    merged["tick_count"] = merged["tick_count_mid"]
    return merged[["bar_start_utc", "tick_count", *PRICE_COLUMNS]].copy()


def _load_new_m5(root: Path, config: Mapping[str, Any]) -> pd.DataFrame:
    source = config["source"]
    path = root / str(source["new_feature_cache"])
    manifest_path = root / str(source["new_feature_manifest"])
    actual = sha256_file(path)
    if actual != str(source["new_feature_sha256"]):
        raise ValueError(f"New feature cache SHA-256 mismatch: {actual}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if str(manifest.get("feature_sha256")) != str(source["new_feature_sha256"]):
        raise ValueError("New feature manifest cache hash mismatch")
    if str(manifest.get("source_digest")) != str(source["new_source_digest"]):
        raise ValueError("New feature manifest source digest mismatch")
    if int(manifest.get("rows", -1)) != int(source["new_expected_rows"]):
        raise ValueError("New feature manifest row count mismatch")
    frame = pd.read_parquet(
        path, columns=["timestamp_ms", "xau_tick_count", *PRICE_COLUMNS]
    )
    if len(frame) != int(source["new_expected_rows"]):
        raise ValueError("Unexpected new M5 row count")
    result = frame.rename(columns={"xau_tick_count": "tick_count"}).copy()
    result["bar_start_utc"] = pd.to_datetime(
        result.pop("timestamp_ms"), unit="ms", utc=True, errors="raise"
    )
    return result[["bar_start_utc", "tick_count", *PRICE_COLUMNS]]


def load_continuous_m5(config: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = storage_root(config)
    old = _load_old_m5(root, config)
    new = _load_new_m5(root, config)
    frame = pd.concat([old, new], ignore_index=True).sort_values(
        "bar_start_utc", kind="mergesort"
    )
    frame = frame.reset_index(drop=True)
    if frame["bar_start_utc"].duplicated().any():
        raise ValueError("Duplicate continuous M5 bar starts")
    values = frame[list(PRICE_COLUMNS)]
    if (~np.isfinite(values) | (values <= 0.0)).any().any():
        raise ValueError("Invalid side-specific M5 prices")
    if (frame["ask_open"] < frame["bid_open"]).any():
        raise ValueError("Crossed opening quotes")
    frame["bar_end_utc"] = frame["bar_start_utc"] + pd.Timedelta(minutes=5)
    frame["timestamp_utc"] = frame["bar_end_utc"]
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    frame = frame.loc[
        frame["bar_start_utc"].ge(start) & frame["bar_start_utc"].lt(end)
    ].reset_index(drop=True)
    if frame.empty or frame["bar_start_utc"].iat[0] < start:
        raise ValueError("Continuous M5 start is invalid")
    return frame, {
        "storage_root": str(root),
        "old_rows": int(len(old)),
        "new_rows": int(len(new)),
        "continuous_rows": int(len(frame)),
        "first_bar_start_utc": frame["bar_start_utc"].iat[0].isoformat(),
        "last_bar_end_utc": frame["bar_end_utc"].iat[-1].isoformat(),
        "new_feature_sha256": str(config["source"]["new_feature_sha256"]),
        "new_source_digest": str(config["source"]["new_source_digest"]),
        "execution_source": "RAW_DUKASCOPY_BID_ASK_TICKS",
        "old_final_contract_sha256": str(config["source"]["old_final_contract_sha256"]),
    }


def _localize_naive(values: Iterable[Any], timezone: str) -> pd.DatetimeIndex:
    index = pd.DatetimeIndex(values)
    try:
        return index.tz_localize(
            timezone, ambiguous="infer", nonexistent="shift_forward"
        )
    except ValueError:
        return pd.DatetimeIndex(
            [
                pd.Timestamp(value).tz_localize(
                    timezone, ambiguous=False, nonexistent="shift_forward"
                )
                for value in index
            ]
        )


def aggregate_broker_bars(
    m5: pd.DataFrame, minutes: int, label: str, timezone: str
) -> pd.DataFrame:
    source = m5.copy()
    local = source["bar_start_utc"].dt.tz_convert(timezone)
    local_naive = local.dt.tz_localize(None)
    source["_bucket"] = local_naive.dt.floor(f"{minutes}min")
    group_keys = ["_bucket"]
    if minutes == 60:
        source["_utc_offset_seconds"] = local.map(
            lambda value: int(value.utcoffset().total_seconds())
        )
        group_keys.append("_utc_offset_seconds")
    aggregations: dict[str, str] = {"tick_count": "sum"}
    for side in ("bid", "ask", "mid"):
        aggregations.update(
            {
                f"{side}_open": "first",
                f"{side}_high": "max",
                f"{side}_low": "min",
                f"{side}_close": "last",
            }
        )
    grouped_source = source.groupby(group_keys, sort=True, observed=True)
    grouped = grouped_source.agg(aggregations)
    grouped["source_rows"] = grouped_source.size()
    grouped = grouped.reset_index()
    if minutes == 60:
        starts = pd.DatetimeIndex(
            grouped["_bucket"]
            - pd.to_timedelta(grouped["_utc_offset_seconds"], unit="s")
        ).tz_localize("UTC")
        ends = starts + pd.Timedelta(minutes=minutes)
    else:
        starts = _localize_naive(grouped["_bucket"], timezone).tz_convert("UTC")
        ends = _localize_naive(
            grouped["_bucket"] + pd.Timedelta(minutes=minutes), timezone
        ).tz_convert("UTC")
    grouped["bar_start_utc"] = starts
    grouped["bar_end_utc"] = ends
    grouped["timestamp_utc"] = grouped["bar_end_utc"]
    grouped["timeframe"] = label
    return grouped.drop(columns=group_keys).sort_values(
        "bar_start_utc", kind="mergesort"
    ).reset_index(drop=True)


def wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["bid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous).abs(),
            (frame["bid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return wilder(true_range, period)


def _percentile_rank_last(window: np.ndarray) -> float:
    if len(window) == 0 or not np.isfinite(window).all():
        return np.nan
    return float(100.0 * np.count_nonzero(window <= window[-1]) / len(window))


def _trend_stack(frame: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    fast = int(config["ema_fast_period"])
    slow = int(config["ema_slow_period"])
    lag = int(config["slope_lag_bars"])
    result = frame.copy()
    result["ema_fast"] = result["bid_close"].ewm(
        span=fast, adjust=False, min_periods=fast
    ).mean()
    result["ema_slow"] = result["bid_close"].ewm(
        span=slow, adjust=False, min_periods=slow
    ).mean()
    result["trend_down"] = (
        result["bid_close"].lt(result["ema_fast"])
        & result["ema_fast"].lt(result["ema_slow"])
        & result["ema_fast"].le(result["ema_fast"].shift(lag))
        & result["ema_slow"].le(result["ema_slow"].shift(lag))
    )
    return result


def prepare_research_data(config: Mapping[str, Any]) -> ResearchData:
    m5, evidence = load_continuous_m5(config)
    timezone = str(config["source"]["broker_timezone"])
    bars = {
        "M5": m5,
        "H1": aggregate_broker_bars(m5, 60, "H1", timezone),
        "H4": aggregate_broker_bars(m5, 240, "H4", timezone),
        "D1": aggregate_broker_bars(m5, 1440, "D1", timezone),
    }
    evidence["timeframes"] = {
        key: {
            "rows": int(len(value)),
            "first": value["bar_start_utc"].iat[0].isoformat(),
            "last": value["bar_end_utc"].iat[-1].isoformat(),
        }
        for key, value in bars.items()
    }
    return ResearchData(m5=m5, bars=bars, evidence=evidence)


def prepare_regime_states(
    data: ResearchData, config: Mapping[str, Any]
) -> dict[str, pd.DataFrame]:
    settings = config["regime"]
    period = int(settings["atr_period"])
    d1 = _trend_stack(data.bars["D1"], settings)
    d1["atr_d1"] = atr(d1, period)
    lookback = int(settings["shock_d1_atr_lookback"])
    d1["atr_percentile_d1"] = d1["atr_d1"].rolling(
        lookback, min_periods=lookback
    ).apply(_percentile_rank_last, raw=True)
    d1["shock_d1"] = d1["atr_percentile_d1"].ge(
        float(settings["shock_d1_atr_percentile_min"])
    )
    persistence = int(settings["d1_persistence_bars"])
    persistent = d1["trend_down"].copy()
    for shift in range(1, persistence):
        persistent &= d1["trend_down"].shift(shift).fillna(False).astype(bool)
    d1["persistent_down"] = persistent

    h4 = _trend_stack(data.bars["H4"], settings)
    h1 = data.bars["H1"].copy()
    h1["atr_h1"] = atr(h1, period)
    h1["shock_h1"] = h1["bid_high"].sub(h1["bid_low"]).ge(
        float(settings["shock_h1_range_atr_multiple"]) * h1["atr_h1"]
    )
    return {"D1": d1, "H4": h4, "H1": h1}


def attach_r2_regime(
    candidates: pd.DataFrame, states: Mapping[str, pd.DataFrame]
) -> pd.DataFrame:
    if candidates.empty:
        return candidates.assign(r2_allowed=pd.Series(dtype=bool))
    result = candidates.sort_values("decision_time", kind="mergesort").copy()
    d1 = states["D1"][["timestamp_utc", "persistent_down", "shock_d1", "atr_percentile_d1"]].rename(
        columns={"timestamp_utc": "d1_feature_time"}
    )
    h4 = states["H4"][["timestamp_utc", "trend_down"]].rename(
        columns={"timestamp_utc": "h4_feature_time", "trend_down": "h4_down"}
    )
    h1 = states["H1"][["timestamp_utc", "shock_h1"]].rename(
        columns={"timestamp_utc": "h1_feature_time"}
    )
    result = pd.merge_asof(
        result,
        d1.sort_values("d1_feature_time"),
        left_on="decision_time",
        right_on="d1_feature_time",
        direction="backward",
        allow_exact_matches=True,
    )
    result = pd.merge_asof(
        result,
        h4.sort_values("h4_feature_time"),
        left_on="decision_time",
        right_on="h4_feature_time",
        direction="backward",
        allow_exact_matches=True,
    )
    result = pd.merge_asof(
        result,
        h1.sort_values("h1_feature_time"),
        left_on="decision_time",
        right_on="h1_feature_time",
        direction="backward",
        allow_exact_matches=True,
    )
    future = (
        result["d1_feature_time"].gt(result["decision_time"])
        | result["h4_feature_time"].gt(result["decision_time"])
        | result["h1_feature_time"].gt(result["decision_time"])
    )
    if future.fillna(False).any():
        raise ValueError("Future regime state attached to candidate")
    result["regime_shock"] = result["shock_d1"].fillna(False) | result[
        "shock_h1"
    ].fillna(False)
    result["r2_allowed"] = (
        ~result["regime_shock"]
        & result["persistent_down"].fillna(False)
        & result["h4_down"].fillna(False)
    )
    return result


def _bar_shape(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    bar_range = frame["bid_high"].sub(frame["bid_low"]).replace(0.0, np.nan)
    body = frame["bid_close"].sub(frame["bid_open"]).abs().div(bar_range)
    close_location = frame["bid_close"].sub(frame["bid_low"]).div(bar_range)
    return body, close_location


def generate_pullback_candidates(
    data: ResearchData,
    states: Mapping[str, pd.DataFrame],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    settings = config["pullback"]
    regime = config["regime"]
    h1 = data.bars["H1"].copy()
    fast = int(settings["h1_fast_ema_period"])
    slow = int(settings["h1_slow_ema_period"])
    lag = int(regime["slope_lag_bars"])
    h1["ema_fast_pullback"] = h1["bid_close"].ewm(
        span=fast, adjust=False, min_periods=fast
    ).mean()
    h1["ema_slow_pullback"] = h1["bid_close"].ewm(
        span=slow, adjust=False, min_periods=slow
    ).mean()
    h1["atr_pullback"] = atr(h1, int(regime["atr_period"]))
    h1["body_fraction"], h1["close_location"] = _bar_shape(h1)
    base = (
        h1["bid_close"].lt(h1["ema_fast_pullback"])
        & h1["ema_fast_pullback"].lt(h1["ema_slow_pullback"])
        & h1["ema_fast_pullback"].le(h1["ema_fast_pullback"].shift(lag))
        & h1["bid_close"].lt(h1["bid_open"])
        & h1["body_fraction"].ge(float(settings["minimum_h1_body_fraction"]))
        & h1["close_location"].le(float(settings["maximum_h1_close_location"]))
    )
    m5 = data.m5.copy()
    m5_body, _ = _bar_shape(m5)
    m5_body_at_end = pd.Series(
        m5_body.to_numpy(dtype=float), index=pd.DatetimeIndex(m5["bar_end_utc"])
    )
    lookback = int(settings["lookback_bars"])
    rows: list[dict[str, Any]] = []
    for index in np.flatnonzero(base.fillna(False).to_numpy(dtype=bool)):
        if index + 1 < lookback:
            continue
        row = h1.iloc[index]
        history = h1.iloc[index - lookback + 1 : index + 1]
        zone = float(settings["touch_atr"]) * float(row["atr_pullback"])
        fast_value = float(row["ema_fast_pullback"])
        slow_value = float(row["ema_slow_pullback"])
        touched_fast = (
            history["bid_high"].ge(fast_value - zone)
            & history["bid_low"].le(fast_value + zone)
        ).any()
        touched_slow = (
            history["bid_high"].ge(slow_value - zone)
            & history["bid_low"].le(slow_value + zone)
        ).any()
        if not (touched_fast or touched_slow):
            continue
        decision = pd.Timestamp(row["timestamp_utc"])
        m5_body_value = m5_body_at_end.get(decision, np.nan)
        if not np.isfinite(m5_body_value) or m5_body_value < float(
            settings["minimum_m5_body_fraction"]
        ):
            continue
        swing_high = float(history["bid_high"].max())
        raw_stop = swing_high + float(settings["stop_buffer_atr"]) * float(
            row["atr_pullback"]
        ) - float(row["bid_close"])
        if raw_stop <= 0.0:
            continue
        rows.append(
            {
                "decision_time": decision,
                "signal_time": decision - pd.Timedelta(minutes=5),
                "direction": "SHORT",
                "raw_stop_distance": raw_stop,
                "signal_atr": float(row["atr_pullback"]),
                "signal_body_fraction": float(row["body_fraction"]),
                "signal_close_location": float(row["close_location"]),
                "m5_execution_body_fraction": float(m5_body_value),
                "source_engine": "H1_PULLBACK_REJECTION",
            }
        )
    if not rows:
        return pd.DataFrame()
    base_candidates = attach_r2_regime(pd.DataFrame(rows), states)
    base_candidates = base_candidates.loc[base_candidates["r2_allowed"]].copy()
    timezone = str(config["source"]["broker_timezone"])
    local_hour = base_candidates["decision_time"].dt.tz_convert(timezone).dt.hour
    variants: list[pd.DataFrame] = []
    for attempt in config["attempts"]:
        if attempt["engine"] != "H1_PULLBACK_REJECTION":
            continue
        start = int(attempt["server_hour_start"])
        end = int(attempt["server_hour_end_exclusive"])
        selected = base_candidates.loc[local_hour.ge(start) & local_hour.lt(end)].copy()
        selected["candidate_id"] = str(attempt["candidate_id"])
        selected["mechanism_family"] = str(attempt["mechanism_family"])
        selected["attempt_no"] = int(attempt["attempt_no"])
        variants.append(selected)
    return pd.concat(variants, ignore_index=True) if variants else pd.DataFrame()


def generate_impulse_candidates(
    data: ResearchData,
    states: Mapping[str, pd.DataFrame],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    settings = config["impulse_retest"]
    m5 = data.m5.copy()
    m5["signal_atr"] = atr(m5, int(config["regime"]["atr_period"]))
    m5["signal_body_fraction"], m5["signal_close_location"] = _bar_shape(m5)
    minimum_atr = min(
        float(item["minimum_m5_atr"])
        for item in config["attempts"]
        if item["engine"] == "M5_IMPULSE_RETEST"
    )
    initial = m5.loc[
        m5["signal_atr"].gt(minimum_atr)
        & m5["bid_close"].lt(m5["bid_open"])
        & m5["signal_body_fraction"].ge(
            float(settings["minimum_signal_body_fraction"])
        )
        & m5["signal_close_location"].le(
            float(settings["maximum_signal_close_location"])
        ),
        [
            "bar_end_utc",
            "bar_start_utc",
            "signal_atr",
            "signal_body_fraction",
            "signal_close_location",
        ],
    ].rename(columns={"bar_end_utc": "decision_time", "bar_start_utc": "signal_time"})
    initial = attach_r2_regime(initial, states)
    initial = initial.loc[initial["r2_allowed"]].copy()

    lows = m5["bid_low"].to_numpy(dtype=float)
    highs = m5["bid_high"].to_numpy(dtype=float)
    opens = m5["bid_open"].to_numpy(dtype=float)
    closes = m5["bid_close"].to_numpy(dtype=float)
    ranges = highs - lows
    support_lookback = int(settings["support_lookback_bars"])
    support_before = (
        pd.Series(lows).shift(1).rolling(
            support_lookback, min_periods=support_lookback
        ).min().to_numpy(dtype=float)
    )
    index_by_time = pd.Series(
        np.arange(len(m5), dtype=int), index=pd.DatetimeIndex(m5["bar_end_utc"])
    )
    rows: list[dict[str, Any]] = []
    break_lookback = int(settings["break_lookback_bars"])
    impulse_bars = int(settings["impulse_bars"])
    for signal in initial.itertuples(index=False):
        i = int(index_by_time.loc[pd.Timestamp(signal.decision_time)])
        current_atr = float(signal.signal_atr)
        selected: dict[str, Any] | None = None
        for break_shift in range(2, break_lookback + 2):
            break_index = i - break_shift + 1
            start_index = break_index - impulse_bars
            if break_index < 0 or start_index < 0:
                continue
            support = float(support_before[break_index])
            if not np.isfinite(support):
                continue
            break_close = closes[break_index]
            if break_close > support - float(settings["break_atr"]) * current_atr:
                continue
            if break_close >= opens[break_index] or ranges[break_index] <= 0.0:
                continue
            impulse_atr = (closes[start_index] - break_close) / current_atr
            break_body = abs(break_close - opens[break_index]) / ranges[break_index]
            if impulse_atr < float(settings["minimum_impulse_atr"]):
                continue
            if break_body < float(settings["minimum_break_body_fraction"]):
                continue
            retest_slice = slice(break_index + 1, i + 1)
            if np.any(
                closes[retest_slice]
                >= support + float(settings["reclaim_atr"]) * current_atr
            ):
                continue
            retest_high = float(np.max(highs[retest_slice]))
            if retest_high < support - float(settings["touch_atr"]) * current_atr:
                continue
            if closes[i] > support - float(settings["reclaim_atr"]) * current_atr:
                continue
            raw_stop = (
                retest_high
                + float(settings["stop_buffer_atr"]) * current_atr
                - closes[i]
            )
            if raw_stop <= 0.0:
                continue
            selected = {
                **signal._asdict(),
                "direction": "SHORT",
                "raw_stop_distance": raw_stop,
                "support": support,
                "break_time": m5["bar_end_utc"].iat[break_index],
                "break_body_fraction": break_body,
                "impulse_atr": impulse_atr,
                "source_engine": "M5_IMPULSE_RETEST",
            }
            break
        if selected is not None:
            rows.append(selected)
    base_candidates = pd.DataFrame(rows)
    if base_candidates.empty:
        return base_candidates
    variants: list[pd.DataFrame] = []
    for attempt in config["attempts"]:
        if attempt["engine"] != "M5_IMPULSE_RETEST":
            continue
        selected = base_candidates.loc[
            base_candidates["signal_atr"].gt(float(attempt["minimum_m5_atr"]))
        ].copy()
        selected["candidate_id"] = str(attempt["candidate_id"])
        selected["mechanism_family"] = str(attempt["mechanism_family"])
        selected["attempt_no"] = int(attempt["attempt_no"])
        variants.append(selected)
    return pd.concat(variants, ignore_index=True) if variants else pd.DataFrame()


def generate_all_candidates(
    data: ResearchData,
    states: Mapping[str, pd.DataFrame],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    frames = [
        generate_pullback_candidates(data, states, config),
        generate_impulse_candidates(data, states, config),
    ]
    usable = [frame for frame in frames if not frame.empty]
    if not usable:
        return pd.DataFrame(
            columns=[
                "decision_time",
                "candidate_id",
                "mechanism_family",
                "attempt_no",
                "candidate_row_id",
            ]
        )
    result = pd.concat(usable, ignore_index=True)
    result = result.sort_values(
        ["decision_time", "attempt_no"], kind="mergesort"
    ).reset_index(drop=True)
    result["candidate_row_id"] = np.arange(len(result), dtype=int)
    return result


def _simulate_short(
    m5: pd.DataFrame,
    starts_ms: np.ndarray,
    ends_ms: np.ndarray,
    ask_high: np.ndarray,
    ask_low: np.ndarray,
    candidate: pd.Series,
    config: Mapping[str, Any],
    tick_store: VerifiedTickStore,
) -> dict[str, Any]:
    execution = config["execution"]
    decision = pd.Timestamp(candidate["decision_time"])
    decision_ms = int(decision.value // 1_000_000)
    entry_quote = tick_store.first_quote_at_or_after(
        decision_ms, int(float(execution["maximum_entry_gap_minutes"]) * 60_000)
    )
    if entry_quote is None:
        return {"accepted": False, "rejection_reason": "NO_TIMELY_TICK_ENTRY"}
    entry_index = int(np.searchsorted(starts_ms, entry_quote.timestamp_ms, side="right") - 1)
    if (
        entry_index < 0
        or entry_index >= len(m5)
        or entry_quote.timestamp_ms >= int(ends_ms[entry_index])
    ):
        return {"accepted": False, "rejection_reason": "NO_MATCHING_M5_ENTRY_BAR"}
    entry_time = pd.Timestamp(entry_quote.timestamp_ms, unit="ms", tz="UTC")
    delay = (entry_quote.timestamp_ms - decision_ms) / 60_000.0
    entry = float(entry_quote.bid)
    spread = float(entry_quote.ask - entry_quote.bid)
    risk = max(
        float(candidate["raw_stop_distance"]),
        float(execution["stop_floor_price"]),
    )
    if risk > float(execution["stop_ceiling_price"]):
        return {"accepted": False, "rejection_reason": "STOP_CEILING_EXCEEDED"}
    if spread < 0.0 or spread > float(execution["maximum_spread_price"]):
        return {"accepted": False, "rejection_reason": "SPREAD_PRICE_LIMIT"}
    if spread / risk > float(execution["maximum_spread_r"]):
        return {"accepted": False, "rejection_reason": "SPREAD_R_LIMIT"}
    stop = entry + risk
    target = entry - float(execution["target_r"]) * risk
    hit: tuple[TickQuote, float, str] | None = None
    m5_both_thresholds = False
    for left in range(entry_index, len(m5), EXIT_SCAN_BLOCK):
        right = min(len(m5), left + EXIT_SCAN_BLOCK)
        events = (ask_high[left:right] >= stop) | (ask_low[left:right] <= target)
        for relative in np.flatnonzero(events):
            index = left + int(relative)
            scan_start = max(entry_quote.timestamp_ms, int(starts_ms[index]))
            scan_end = int(ends_ms[index]) - 1
            observed = tick_store.first_short_hit(
                scan_start, scan_end, stop, target
            )
            if observed is not None:
                hit = observed
                m5_both_thresholds = bool(
                    ask_high[index] >= stop and ask_low[index] <= target
                )
                break
            if index != entry_index:
                raise ValueError(
                    "M5 ask threshold has no matching raw tick in a complete bar"
                )
        if hit is not None:
            break
    if hit is None:
        final_quote = tick_store.last_quote_at_or_before(
            int(ends_ms[-1]) - 1, entry_quote.timestamp_ms
        )
        if final_quote is None:
            raise ValueError("Accepted entry has no raw exit quote")
        exit_quote = final_quote
        exit_price = float(final_quote.ask)
        exit_reason = "END_OF_DATA"
    else:
        exit_quote, exit_price, exit_reason = hit
    exit_time = pd.Timestamp(exit_quote.timestamp_ms, unit="ms", tz="UTC")
    net_r = (entry - exit_price) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    risk_usd = risk * float(execution["ounces_at_0_01_lot"])
    extra_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    stress_net_r = net_r - extra_cost_r - float(execution["stress_slippage_r"])
    return {
        "accepted": True,
        "rejection_reason": "",
        "entry_time": entry_time,
        "exit_time": exit_time,
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "initial_risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread": spread,
        "entry_spread_r": spread / risk,
        "exit_reason": exit_reason,
        "entry_delay_ms": int(entry_quote.timestamp_ms - decision_ms),
        "entry_tick_timestamp_ms": int(entry_quote.timestamp_ms),
        "exit_tick_timestamp_ms": int(exit_quote.timestamp_ms),
        "raw_tick_execution": True,
        "net_r": net_r,
        "stress_net_r": stress_net_r,
        "extra_cost_r": extra_cost_r,
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "m5_both_thresholds_resolved_by_ticks": m5_both_thresholds,
    }


def simulate_candidates(
    m5: pd.DataFrame,
    candidates: pd.DataFrame,
    config: Mapping[str, Any],
    tick_store: VerifiedTickStore,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if candidates.empty:
        ledger = candidates.copy()
        ledger["accepted"] = pd.Series(dtype=bool)
        ledger["rejection_reason"] = pd.Series(dtype=str)
        return ledger, ledger.copy()
    starts_ms = timestamp_series_ms(m5["bar_start_utc"])
    ends_ms = timestamp_series_ms(m5["bar_end_utc"])
    arrays = {
        name: m5[name].to_numpy(dtype=float)
        for name in ("ask_high", "ask_low")
    }
    ledger: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    for _, candidate in candidates.iterrows():
        outcome = _simulate_short(
            m5,
            starts_ms,
            ends_ms,
            arrays["ask_high"],
            arrays["ask_low"],
            candidate,
            config,
            tick_store,
        )
        row = {**candidate.to_dict(), **outcome}
        ledger.append(row)
        if outcome["accepted"]:
            trades.append(row)
    return pd.DataFrame(ledger), pd.DataFrame(trades)


def apply_account_policy(
    trades: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    if trades.empty:
        return trades
    execution = config["execution"]
    timezone = str(config["source"]["broker_timezone"])
    selected: list[pd.Series] = []
    for candidate_id, group in trades.groupby("candidate_id", sort=False):
        active: list[pd.Timestamp] = []
        daily: dict[Any, int] = {}
        for _, trade in group.sort_values(
            ["entry_time", "candidate_row_id"], kind="mergesort"
        ).iterrows():
            active = [value for value in active if value > trade["entry_time"]]
            broker_day = pd.Timestamp(trade["entry_time"]).tz_convert(timezone).date()
            if len(active) >= int(execution["maximum_concurrent_positions"]):
                continue
            if daily.get(broker_day, 0) >= int(
                execution["maximum_entries_per_broker_day"]
            ):
                continue
            selected.append(trade)
            active.append(pd.Timestamp(trade["exit_time"]))
            daily[broker_day] = daily.get(broker_day, 0) + 1
    if not selected:
        return trades.iloc[0:0].copy()
    return pd.DataFrame(selected).sort_values(
        ["entry_time", "candidate_id"], kind="mergesort"
    ).reset_index(drop=True)


def profit_factor(values: pd.Series) -> float:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(([0.0], values.fillna(0.0).to_numpy(dtype=float).cumsum()))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity)) if len(equity) else 0.0


def source_days(
    m5: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DatetimeIndex:
    observed = m5.loc[
        m5["bar_start_utc"].ge(start) & m5["bar_start_utc"].lt(end),
        "bar_start_utc",
    ].dt.floor("D")
    return pd.DatetimeIndex(sorted(observed.unique()))


def daily_pvalue(trades: pd.DataFrame, days: pd.DatetimeIndex) -> float:
    if trades.empty or len(days) < 2:
        return 1.0
    daily = (
        trades.assign(day=pd.to_datetime(trades["entry_time"], utc=True).dt.floor("D"))
        .groupby("day", sort=True)["stress_net_r"]
        .sum()
        .reindex(days, fill_value=0.0)
        .to_numpy(dtype=float)
    )
    if float(daily.mean()) <= 0.0:
        return 1.0
    standard = float(daily.std(ddof=1))
    if standard == 0.0:
        return 0.0
    result = stats.ttest_1samp(daily, 0.0, alternative="greater")
    return float(result.pvalue) if np.isfinite(result.pvalue) else 1.0


def holm_adjust(values: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(values, key=lambda key: (float(values[key]), key))
    count = len(ordered)
    running = 0.0
    adjusted: dict[str, float] = {}
    for rank, key in enumerate(ordered):
        running = max(running, (count - rank) * float(values[key]))
        adjusted[key] = min(1.0, running)
    return adjusted


def summarize_window(
    candidate_id: str,
    trades: pd.DataFrame,
    days: pd.DatetimeIndex,
    gate: Mapping[str, Any],
) -> dict[str, Any]:
    values = trades["stress_net_r"].astype(float) if not trades.empty else pd.Series(dtype=float)
    years = (
        trades.assign(year=pd.to_datetime(trades["entry_time"], utc=True).dt.year)
        .groupby("year", sort=True)["stress_net_r"]
        .sum()
        if not trades.empty
        else pd.Series(dtype=float)
    )
    remove_count = min(int(gate["top_winners_removed"]), len(values))
    removed = values.drop(values.nlargest(remove_count).index)
    return {
        "candidate_id": candidate_id,
        "trades": int(len(trades)),
        "source_days": int(len(days)),
        "trades_per_source_day": len(trades) / len(days) if len(days) else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "positive_active_year_share": float((years > 0.0).mean()) if len(years) else 0.0,
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "daily_pvalue": daily_pvalue(trades, days),
    }


def gate_checks(
    metrics: Mapping[str, Any], gate: Mapping[str, Any], holm_pvalue: float
) -> dict[str, bool]:
    return {
        "minimum_trades": int(metrics["trades"]) >= int(gate["minimum_trades"]),
        "minimum_stress_pf": float(metrics["stress_pf"]) >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": float(metrics["average_stress_r"]) >= float(gate["minimum_average_stress_r"]),
        "maximum_closed_drawdown_r": float(metrics["closed_drawdown_r"]) <= float(gate["maximum_closed_drawdown_r"]),
        "minimum_positive_active_year_share": float(metrics["positive_active_year_share"]) >= float(gate["minimum_positive_active_year_share"]),
        "top_winners_removed_positive": float(metrics["top_winners_removed_stress_net_r"]) > 0.0,
        "maximum_holm_pvalue": float(holm_pvalue) <= float(gate["maximum_holm_pvalue"]),
    }


def evaluate_windows(
    trades: pd.DataFrame, m5: pd.DataFrame, config: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidate_ids = [str(item["candidate_id"]) for item in config["attempts"]]
    for window, boundaries in config["windows"].items():
        start, end = map(pd.Timestamp, boundaries)
        days = source_days(m5, start, end)
        summaries: dict[str, dict[str, Any]] = {}
        for candidate_id in candidate_ids:
            if trades.empty:
                selected = pd.DataFrame(columns=["entry_time", "stress_net_r"])
            else:
                selected = trades.loc[
                    trades["candidate_id"].eq(candidate_id)
                    & trades["entry_time"].ge(start)
                    & trades["entry_time"].lt(end)
                ].copy()
            summaries[candidate_id] = summarize_window(
                candidate_id, selected, days, config["gates"][window]
            )
        adjusted = holm_adjust(
            {key: float(value["daily_pvalue"]) for key, value in summaries.items()}
        )
        for candidate_id in candidate_ids:
            metrics = summaries[candidate_id]
            metrics["window"] = window
            metrics["holm_pvalue"] = adjusted[candidate_id]
            metrics["gate_checks"] = gate_checks(
                metrics, config["gates"][window], adjusted[candidate_id]
            )
            metrics["gate_pass"] = all(metrics["gate_checks"].values())
            rows.append(metrics)
    return rows


def select_qualified(
    metrics: Iterable[Mapping[str, Any]], config: Mapping[str, Any]
) -> tuple[list[str], list[str]]:
    rows = list(metrics)
    evidentiary = ("old_replication", "predevelopment_confirmation")
    passing: list[str] = []
    for attempt in config["attempts"]:
        candidate_id = str(attempt["candidate_id"])
        if all(
            any(
                row["candidate_id"] == candidate_id
                and row["window"] == window
                and bool(row["gate_pass"])
                for row in rows
            )
            for window in evidentiary
        ):
            passing.append(candidate_id)
    selected: list[str] = []
    seen_families: set[str] = set()
    for attempt in config["attempts"]:
        candidate_id = str(attempt["candidate_id"])
        family = str(attempt["mechanism_family"])
        if candidate_id in passing and family not in seen_families:
            selected.append(candidate_id)
            seen_families.add(family)
    return passing, selected
