from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import numpy as np
import pandas as pd


HOUR_MS = 3_600_000


@dataclass(frozen=True)
class Tick:
    timestamp_ms: int
    bid: float
    ask: float
    bid_volume: float
    ask_volume: float


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], field: str) -> str:
    clean = {key: value for key, value in payload.items() if key != field}
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def month_keys(first: str, last: str) -> list[tuple[int, int]]:
    current = pd.Period(first, freq="M")
    finish = pd.Period(last, freq="M")
    return [(period.year, period.month) for period in pd.period_range(current, finish, freq="M")]


def _month_root(storage: Path, symbol: str, year: int, month: int) -> Path:
    return storage / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"


def validate_month_manifest(
    storage: Path,
    symbol: str,
    spec: Mapping[str, Any],
    year: int,
    month: int,
) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    root = _month_root(storage, symbol, year, month)
    manifest_path = root / "_ACQUISITION_MANIFEST.json"
    frozen_path = root / "_FROZEN_MANIFEST.json"
    manifest = load_json(manifest_path)
    frozen = load_json(frozen_path)
    expected = calendar.monthrange(year, month)[1] * 24
    rows = manifest.get("rows")
    if manifest.get("symbol") != symbol or manifest.get("month") != f"{year:04d}-{month:02d}":
        raise ValueError(f"cross-symbol or cross-month manifest: {manifest_path}")
    if not isinstance(rows, list) or len(rows) != expected:
        raise ValueError(f"incomplete acquisition manifest: {manifest_path}")
    if (
        frozen.get("symbol") != symbol
        or frozen.get("month") != f"{year:04d}-{month:02d}"
        or int(frozen.get("expected_hour_files", -1)) != expected
        or int(frozen.get("observed_hour_files", -1)) != expected
        or not bool(frozen.get("complete"))
        or not bool(frozen.get("frozen"))
    ):
        raise ValueError(f"invalid frozen manifest: {frozen_path}")
    by_hour: dict[int, dict[str, Any]] = {}
    source_code = str(spec["source_code"])
    for row in rows:
        hour = pd.Timestamp(row.get("hour_utc"))
        if hour.tzinfo is None:
            raise ValueError(f"manifest hour is timezone naive: {manifest_path}")
        hour = hour.tz_convert("UTC")
        hour_ms = int(hour.timestamp() * 1000)
        expected_url = (
            f"https://jetta.dukascopy.com/v1/ticks/{source_code}/"
            f"{hour.year}/{hour.month}/{hour.day}/{hour.hour}"
        )
        expected_relative = (
            f"raw/{symbol}/year={year:04d}/month={month:02d}/{hour:%Y%m%d%H}.json"
        )
        if (
            row.get("symbol") != symbol
            or row.get("status") not in {"DOWNLOADED_VALID", "RESUMED_VALID"}
            or int(row.get("http_status", -1)) != 200
            or row.get("url") != expected_url
            or str(row.get("path", "")).replace("\\", "/") != expected_relative
            or len(str(row.get("sha256", ""))) != 64
            or hour_ms in by_hour
        ):
            raise ValueError(f"invalid acquisition row in {manifest_path}")
        by_hour[hour_ms] = dict(row)
    first_hour = int(datetime(year, month, 1, tzinfo=UTC).timestamp() * 1000)
    expected_hours = {first_hour + offset * HOUR_MS for offset in range(expected)}
    if set(by_hour) != expected_hours:
        raise ValueError(f"hour coverage mismatch: {manifest_path}")
    return by_hour, {
        "symbol": symbol,
        "month": f"{year:04d}-{month:02d}",
        "hours": expected,
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "frozen_manifest_path": str(frozen_path),
        "frozen_manifest_sha256": sha256_file(frozen_path),
        "declared_bytes": int(sum(int(row["bytes"]) for row in rows)),
        "declared_ticks": int(sum(int(row["tick_count"]) for row in rows)),
    }


def _rounded(value: float, scale: int) -> float:
    factor = 10**scale
    return math.floor(value * factor + 0.5 + 1e-9) / factor


def decode_payload(raw: bytes, *, scale: int, hour_ms: int) -> tuple[Tick, ...]:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("tick payload is not an object")
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    required = ("timestamp", "multiplier", "bid", "ask", *arrays)
    if missing := [key for key in required if key not in payload]:
        raise ValueError(f"tick payload is missing {missing}")
    lengths = [len(payload[key]) if isinstance(payload[key], list) else -1 for key in arrays]
    if len(set(lengths)) != 1 or lengths[0] < 0:
        raise ValueError("tick arrays have inconsistent lengths")
    if lengths[0] == 0:
        return ()
    timestamp = int(payload["timestamp"])
    multiplier = float(payload["multiplier"])
    bid = float(payload["bid"])
    ask = float(payload["ask"])
    if multiplier <= 0:
        raise ValueError("tick multiplier must be positive")
    ticks: list[Tick] = []
    previous = -1
    for index in range(lengths[0]):
        timestamp += int(payload["times"][index])
        bid = _rounded(bid + float(payload["bids"][index]) * multiplier, scale)
        ask = _rounded(ask + float(payload["asks"][index]) * multiplier, scale)
        if timestamp < previous or not hour_ms <= timestamp < hour_ms + HOUR_MS or ask < bid:
            raise ValueError("invalid timestamp order, hour boundary, or crossed quote")
        ticks.append(
            Tick(
                timestamp_ms=timestamp,
                bid=bid,
                ask=ask,
                bid_volume=float(payload["bidVolumes"][index]),
                ask_volume=float(payload["askVolumes"][index]),
            )
        )
        previous = timestamp
    return tuple(ticks)


class ManifestTickStore:
    def __init__(self, storage: Path, symbol: str, spec: Mapping[str, Any]) -> None:
        self.storage = storage.resolve()
        self.symbol = symbol
        self.spec = dict(spec)
        self.manifests: dict[tuple[int, int], dict[int, dict[str, Any]]] = {}
        self.audit_rows: dict[tuple[int, int], dict[str, Any]] = {}

    def ensure_month(self, year: int, month: int) -> None:
        key = (year, month)
        if key in self.manifests:
            return
        rows, audit = validate_month_manifest(
            self.storage, self.symbol, self.spec, year, month
        )
        self.manifests[key] = rows
        self.audit_rows[key] = audit

    @lru_cache(maxsize=256)
    def load_hour(self, hour_ms: int) -> tuple[Tick, ...]:
        hour_ms -= hour_ms % HOUR_MS
        hour = datetime.fromtimestamp(hour_ms / 1000, UTC)
        self.ensure_month(hour.year, hour.month)
        row = self.manifests[(hour.year, hour.month)][hour_ms]
        path = self.storage / str(row["path"])
        if not path.is_file() or sha256_file(path) != str(row["sha256"]):
            raise ValueError(f"raw tick file missing or hash changed: {path}")
        return decode_payload(
            path.read_bytes(), scale=int(self.spec["price_scale"]), hour_ms=hour_ms
        )

    def ticks_between(self, start_ms: int, end_ms: int) -> Iterator[Tick]:
        hour = start_ms - start_ms % HOUR_MS
        while hour <= end_ms:
            for tick in self.load_hour(hour):
                if start_ms <= tick.timestamp_ms <= end_ms:
                    yield tick
            hour += HOUR_MS

    def first_tick_strictly_after(self, timestamp_ms: int, maximum_delay_ms: int) -> Tick | None:
        for tick in self.ticks_between(timestamp_ms, timestamp_ms + maximum_delay_ms):
            if tick.timestamp_ms > timestamp_ms:
                return tick
        return None

    def quote_frame(self, start_ms: int, end_ms: int) -> pd.DataFrame:
        rows = [
            (tick.timestamp_ms, tick.bid, tick.ask)
            for tick in self.ticks_between(start_ms, end_ms)
        ]
        if not rows:
            return pd.DataFrame(columns=["timestamp_ms", "bid", "ask", "mid"])
        frame = pd.DataFrame(rows, columns=["timestamp_ms", "bid", "ask"])
        frame = frame.sort_values("timestamp_ms", kind="stable")
        frame = frame.drop_duplicates("timestamp_ms", keep="last").reset_index(drop=True)
        frame["mid"] = (frame["bid"] + frame["ask"]) / 2.0
        return frame


def clock_ms(date: pd.Timestamp, value: str) -> int:
    hour, minute = (int(part) for part in value.split(":"))
    return int((date.normalize() + pd.Timedelta(hours=hour, minutes=minute)).timestamp() * 1000)


def session_quality(
    date: pd.Timestamp,
    xag: pd.DataFrame,
    xau: pd.DataFrame,
    rule: Mapping[str, Any],
) -> dict[str, Any]:
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    xag_session = xag.loc[xag["timestamp_ms"].between(start_ms, end_ms - 1)]
    xau_session = xau.loc[xau["timestamp_ms"].between(start_ms, end_ms - 1)]

    def coverage(frame: pd.DataFrame) -> float:
        if frame.empty:
            return 0.0
        return (int(frame["timestamp_ms"].iloc[-1]) - int(frame["timestamp_ms"].iloc[0])) / 60_000

    xag_coverage = coverage(xag_session)
    xau_coverage = coverage(xau_session)
    eligible = bool(
        date.weekday() < 5
        and len(xag_session) >= int(rule["minimum_xag_quotes"])
        and len(xau_session) >= int(rule["minimum_xau_quotes"])
        and xag_coverage >= float(rule["minimum_session_coverage_minutes"])
        and xau_coverage >= float(rule["minimum_session_coverage_minutes"])
    )
    return {
        "date_utc": date.date().isoformat(),
        "weekday": int(date.weekday()),
        "xag_quotes": int(len(xag_session)),
        "xau_quotes": int(len(xau_session)),
        "xag_coverage_minutes": xag_coverage,
        "xau_coverage_minutes": xau_coverage,
        "eligible_full_weekday": eligible,
    }


def build_event_features(
    date: pd.Timestamp,
    xag: pd.DataFrame,
    xau: pd.DataFrame,
    *,
    horizons_ms: Sequence[int],
    rule: Mapping[str, Any],
    prefilter: Mapping[str, Any],
) -> pd.DataFrame:
    if xag.empty or xau.empty:
        return pd.DataFrame()
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    xag_times_all = xag["timestamp_ms"].to_numpy(dtype=np.int64)
    xag_mid_all = xag["mid"].to_numpy(dtype=float)
    event_indices = np.flatnonzero((xag_times_all >= start_ms) & (xag_times_all < end_ms))
    if event_indices.size == 0:
        return pd.DataFrame()
    event_times = xag_times_all[event_indices]
    event_mid = xag_mid_all[event_indices]
    xau_times = xau["timestamp_ms"].to_numpy(dtype=np.int64)
    xau_mid = xau["mid"].to_numpy(dtype=float)
    max_staleness = int(rule["maximum_baseline_staleness_ms"])
    current_staleness = int(rule["maximum_current_xau_staleness_ms"])
    output: list[pd.DataFrame] = []
    for horizon in horizons_ms:
        targets = event_times - int(horizon)
        xag_base_i = np.searchsorted(xag_times_all, targets, side="right") - 1
        xau_base_i = np.searchsorted(xau_times, targets, side="right") - 1
        xau_current_i = np.searchsorted(xau_times, event_times, side="left") - 1
        valid = (xag_base_i >= 0) & (xau_base_i >= 0) & (xau_current_i >= 0)
        safe_xag = np.maximum(xag_base_i, 0)
        safe_xau_base = np.maximum(xau_base_i, 0)
        safe_xau_current = np.maximum(xau_current_i, 0)
        valid &= targets - xag_times_all[safe_xag] <= max_staleness
        valid &= targets - xau_times[safe_xau_base] <= max_staleness
        valid &= event_times - xau_times[safe_xau_current] <= current_staleness
        xag_move = (event_mid / xag_mid_all[safe_xag] - 1.0) * 10_000.0
        xau_move = (
            xau_mid[safe_xau_current] / xau_mid[safe_xau_base] - 1.0
        ) * 10_000.0
        direction_sign = np.sign(xag_move)
        absolute_xag = np.abs(xag_move)
        signed_xau = direction_sign * xau_move
        innovation = absolute_xag - signed_xau
        response = np.divide(
            signed_xau,
            absolute_xag,
            out=np.full_like(signed_xau, np.inf),
            where=absolute_xag > 0,
        )
        quote_count = event_indices - xag_base_i
        valid &= direction_sign != 0
        valid &= absolute_xag >= float(prefilter["minimum_absolute_xag_move_bps"])
        valid &= innovation >= float(prefilter["minimum_directional_innovation_bps"])
        valid &= response <= float(prefilter["maximum_signed_xau_response_ratio"])
        valid &= quote_count >= int(prefilter["minimum_xag_quote_count"])
        if not valid.any():
            continue
        chosen = np.flatnonzero(valid)
        frame = pd.DataFrame(
            {
                "feature_time_utc": pd.to_datetime(event_times[chosen], unit="ms", utc=True),
                "decision_timestamp_ms": event_times[chosen],
                "horizon_ms": int(horizon),
                "xag_baseline_timestamp_ms": xag_times_all[safe_xag[chosen]],
                "xau_baseline_timestamp_ms": xau_times[safe_xau_base[chosen]],
                "xau_current_timestamp_ms": xau_times[safe_xau_current[chosen]],
                "xag_move_bps": xag_move[chosen],
                "xau_move_bps": xau_move[chosen],
                "directional_innovation_bps": innovation[chosen],
                "signed_xau_response_ratio": response[chosen],
                "xag_quote_count": quote_count[chosen],
                "direction": np.where(direction_sign[chosen] > 0, "LONG", "SHORT"),
            }
        )
        output.append(frame)
    if not output:
        return pd.DataFrame()
    return (
        pd.concat(output, ignore_index=True)
        .sort_values(["feature_time_utc", "horizon_ms"], kind="stable")
        .reset_index(drop=True)
    )


def policy_grid(calibration: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for values in itertools.product(
        calibration["horizon_ms_grid"],
        calibration["minimum_absolute_xag_move_bps_grid"],
        calibration["minimum_directional_innovation_bps_grid"],
        calibration["maximum_signed_xau_response_ratio_grid"],
        calibration["minimum_xag_quote_count_grid"],
    ):
        horizon, move, innovation, response, count = values
        rows.append(
            {
                "horizon_ms": int(horizon),
                "minimum_absolute_xag_move_bps": float(move),
                "minimum_directional_innovation_bps": float(innovation),
                "maximum_signed_xau_response_ratio": float(response),
                "minimum_xag_quote_count": int(count),
            }
        )
    return rows


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"H{int(policy['horizon_ms']):05d}"
        f"__XM{int(round(float(policy['minimum_absolute_xag_move_bps']) * 10)):03d}"
        f"__IN{int(round(float(policy['minimum_directional_innovation_bps']) * 10)):03d}"
        f"__RR{int(round(float(policy['maximum_signed_xau_response_ratio']) * 100)):03d}"
        f"__QC{int(policy['minimum_xag_quote_count']):02d}"
    )


def generate_candidates(
    features: pd.DataFrame, *, policy: Mapping[str, Any], family: str
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    mask = features["horizon_ms"].eq(int(policy["horizon_ms"]))
    mask &= features["xag_move_bps"].abs() >= float(
        policy["minimum_absolute_xag_move_bps"]
    )
    mask &= features["directional_innovation_bps"] >= float(
        policy["minimum_directional_innovation_bps"]
    )
    mask &= features["signed_xau_response_ratio"] <= float(
        policy["maximum_signed_xau_response_ratio"]
    )
    mask &= features["xag_quote_count"] >= int(policy["minimum_xag_quote_count"])
    selected = features.loc[mask].copy()
    if selected.empty:
        return selected
    selected["date_utc"] = selected["feature_time_utc"].dt.date.astype(str)
    selected = selected.sort_values(["feature_time_utc", "horizon_ms"], kind="stable")
    selected = selected.groupby("date_utc", sort=True, as_index=False).head(1).copy()
    selected["family"] = family
    selected["policy_id"] = policy_id(policy)
    selected.insert(
        0,
        "candidate_id",
        "V72:"
        + selected["policy_id"]
        + ":"
        + selected["decision_timestamp_ms"].astype(str)
        + ":"
        + selected["direction"],
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V72 candidate IDs are not unique")
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
    days = len(eligible_dates)
    frequency = trades / days if days else 0.0
    active_share = active_days / days if days else 0.0
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
        "eligible_full_weekdays": days,
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
            -float(row["minimum_absolute_xag_move_bps"]),
            -float(row["minimum_directional_innovation_bps"]),
            float(row["maximum_signed_xau_response_ratio"]),
            -int(row["minimum_xag_quote_count"]),
            int(row["horizon_ms"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "horizon_ms",
        "minimum_absolute_xag_move_bps",
        "minimum_directional_innovation_bps",
        "maximum_signed_xau_response_ratio",
        "minimum_xag_quote_count",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}


def calibration_prefilter(calibration: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "minimum_absolute_xag_move_bps": min(
            calibration["minimum_absolute_xag_move_bps_grid"]
        ),
        "minimum_directional_innovation_bps": min(
            calibration["minimum_directional_innovation_bps_grid"]
        ),
        "maximum_signed_xau_response_ratio": max(
            calibration["maximum_signed_xau_response_ratio_grid"]
        ),
        "minimum_xag_quote_count": min(calibration["minimum_xag_quote_count_grid"]),
    }
