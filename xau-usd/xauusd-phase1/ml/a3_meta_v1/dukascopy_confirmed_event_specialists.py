from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_label_factory import (
    HOUR_MS,
    VerifiedTickStore,
    _load_foundation,
    _month_range,
    _month_source_identity,
    _sha256_file,
    prepare_verified_h1_bars,
)
from ml.a3_meta_v1.dukascopy_microstructure_regime import _aggregate_tick_arrays


BAR_WIDTH_MS = 5 * 60_000
DEFAULT_CONTRACT = Path(
    "config/ml/a3_ml_dukascopy_confirmed_event_specialists_v1.json"
)
CACHE_SCHEMA = "a3_ml_dukascopy_confirmed_event_m5_cache_v1"
MONTH_CACHE_SCHEMA = "a3_ml_dukascopy_confirmed_event_m5_month_v1"


class ConfirmedEventSpecialistError(RuntimeError):
    pass


def run_confirmed_event_specialists(
    phase1_root: Path, contract_path: Path | None = None
) -> Path:
    phase1_root = phase1_root.resolve()
    contract_file = (contract_path or phase1_root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    validate_contract(contract)
    _validate_source_locks(phase1_root, contract)

    storage_root = _resolve_storage_root(contract)
    foundation = _load_foundation(phase1_root.parents[1])
    months = _month_range(
        str(contract["period"]["start_month"]),
        str(contract["period"]["end_month"]),
    )
    features, cache_manifest, source_audits = load_or_build_m5_features(
        storage_root, foundation, months, contract
    )
    h1_bars, h1_audits = prepare_verified_h1_bars(
        storage_root,
        storage_root / str(contract["external_output_subdirectory"]) / "h1-bars",
        str(contract["symbol"]),
        months,
        foundation,
    )

    candidates = generate_candidates(features, contract)
    validate_candidates(candidates)
    tick_store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=set(months),
    )
    labels = replay_candidates(candidates, h1_bars, tick_store, contract)
    report = build_report(
        phase1_root=phase1_root,
        contract_file=contract_file,
        contract=contract,
        source_audits=source_audits,
        h1_audits=h1_audits,
        cache_manifest=cache_manifest,
        features=features,
        candidates=candidates,
        labels=labels,
    )

    outputs = {
        key: (phase1_root / value).resolve() for key, value in contract["outputs"].items()
    }
    _write_csv(outputs["candidates_csv"], candidates)
    _write_csv(outputs["labels_csv"], labels)
    _write_csv(outputs["family_metrics_csv"], report.pop("_family_metric_rows"))
    _write_csv(outputs["portfolio_trades_csv"], report.pop("_portfolio_rows"))
    report["artifacts"] = {
        name: _artifact(outputs[name])
        for name in (
            "candidates_csv",
            "labels_csv",
            "family_metrics_csv",
            "portfolio_trades_csv",
        )
    }
    outputs["report_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report_json"].write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outputs["report_markdown"].write_text(render_report(report), encoding="utf-8")
    return outputs["report_json"]


def validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_confirmed_event_specialists_v1":
        raise ValueError("unexpected confirmed-event specialist contract version")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("confirmed-event V1 is locked to XAUUSD")
    period = contract["period"]
    if int(period["expected_months"]) != 120:
        raise ValueError("confirmed-event V1 requires the locked 120-month source")
    controls = contract["research_controls"]
    if controls.get("parameter_grid_search_authorized"):
        raise ValueError("parameter grid search is forbidden")
    if controls.get("same_iteration_post_outcome_tuning_authorized"):
        raise ValueError("post-outcome V1 tuning is forbidden")
    if not controls.get("exam_requires_train_validation_and_internal_test_pass"):
        raise ValueError("chronological exam firewall is required")
    if not controls.get("known_program_level_history_contamination"):
        raise ValueError("known program-level contamination must be disclosed")
    if controls.get("claims_untouched_holdout"):
        raise ValueError("V1 cannot claim an untouched historical holdout")
    authorization = contract["authorization"]
    if not authorization.get("research_only"):
        raise ValueError("confirmed-event campaign must remain research-only")
    for key in (
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ):
        if authorization.get(key):
            raise ValueError(f"forbidden confirmed-event authorization: {key}")
    windows = contract["windows"]
    boundaries = [
        _parse_ms(windows["train_start_utc"]),
        _parse_ms(windows["train_end_exclusive_utc"]),
        _parse_ms(windows["validation_end_exclusive_utc"]),
        _parse_ms(windows["internal_test_end_exclusive_utc"]),
        _parse_ms(windows["exam_end_exclusive_utc"]),
    ]
    if boundaries != sorted(set(boundaries)):
        raise ValueError("confirmed-event windows are not strictly chronological")
    families = contract["families"]
    expected = {
        "session_boundary_sweep_reclaim_v1",
        "compression_break_retest_v1",
        "shock_failure_reclaim_v1",
    }
    if {str(row["family_id"]) for row in families} != expected:
        raise ValueError("confirmed-event family set differs from the preregistration")
    for family in families:
        if not 0 < float(family["minimum_stop_atr"]) <= float(family["maximum_stop_atr"]):
            raise ValueError(f"invalid stop bounds for {family['family_id']}")
        if float(family["reward_r"]) <= 0 or int(family["maximum_hold_hours"]) <= 0:
            raise ValueError(f"invalid exit contract for {family['family_id']}")
    execution = contract["execution"]
    if float(execution["maximum_initial_risk_usd"]) != 50.0:
        raise ValueError("V1 risk ceiling must remain $50 at 0.01 lot")
    if execution.get("same_tick_collision_policy") != "FIRST_EXECUTABLE_TOUCH":
        raise ValueError("unexpected tick collision policy")


def _validate_source_locks(phase1_root: Path, contract: Mapping[str, Any]) -> None:
    for locked in contract["source_lock"]:
        path = (phase1_root / str(locked["path"])).resolve()
        if not path.is_file() or _sha256_file(path) != str(locked["sha256"]):
            raise ConfirmedEventSpecialistError(f"source lock mismatch: {path}")


def _resolve_storage_root(contract: Mapping[str, Any]) -> Path:
    env_name = str(contract["storage_environment_variable"])
    configured = os.environ.get(env_name, "").strip() or str(
        contract["default_storage_root"]
    )
    root = Path(configured).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    return root


def load_or_build_m5_features(
    storage_root: Path,
    foundation: Any,
    months: Sequence[tuple[int, int]],
    contract: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, Any]]]:
    symbol = str(contract["symbol"])
    source_audits = []
    for year, month in months:
        foundation.validate_month_acquisition_manifest(storage_root, symbol, year, month)
        identity = _month_source_identity(storage_root, symbol, year, month)
        source_audits.append({"month": f"{year:04d}-{month:02d}", **identity})
    source_digest = _canonical_sha256(source_audits)
    aggregation = contract["aggregation"]
    cache_path = storage_root / str(aggregation["external_bar_cache"])
    manifest_path = storage_root / str(aggregation["external_bar_manifest"])
    if cache_path.is_file() and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (
            manifest.get("schema_version") == CACHE_SCHEMA
            and manifest.get("source_digest") == source_digest
            and manifest.get("feature_sha256") == _sha256_file(cache_path)
            and int(manifest.get("rows", -1)) > 0
        ):
            frame = pd.read_parquet(cache_path)
            _validate_feature_frame(frame)
            return frame, {**manifest, "reused": True, "path": str(cache_path)}, source_audits

    external_root = storage_root / str(contract["external_output_subdirectory"])
    parts = []
    reused_months = 0
    for audit, (year, month) in zip(source_audits, months, strict=True):
        partition = (
            external_root
            / "m5-months"
            / symbol
            / f"year={year:04d}"
            / f"month={month:02d}"
        )
        part_path = partition / "features.parquet"
        metadata_path = partition / "metadata.json"
        part = _load_month_cache(part_path, metadata_path, audit)
        if part is None:
            part = _derive_month_m5(storage_root, symbol, year, month, foundation)
            partition.mkdir(parents=True, exist_ok=True)
            part.to_parquet(part_path, index=False, compression="zstd")
            metadata = {
                "schema_version": MONTH_CACHE_SCHEMA,
                **audit,
                "rows": len(part),
                "feature_sha256": _sha256_file(part_path),
            }
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        else:
            reused_months += 1
        parts.append(part)
    frame = pd.concat(parts, ignore_index=True)
    frame = enrich_m5_features(frame, contract)
    _validate_feature_frame(frame)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(cache_path, index=False, compression="zstd")
    manifest = {
        "schema_version": CACHE_SCHEMA,
        "source_digest": source_digest,
        "feature_sha256": _sha256_file(cache_path),
        "rows": len(frame),
        "columns": list(frame.columns),
        "monthly_caches_reused": reused_months,
        "monthly_caches_total": len(months),
        "reused": False,
        "path": str(cache_path),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return frame, manifest, source_audits


def _load_month_cache(
    path: Path, metadata_path: Path, audit: Mapping[str, Any]
) -> pd.DataFrame | None:
    if not path.is_file() or not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for key in (
        "month",
        "manifest_sha256",
        "source_files_composite_sha256",
        "raw_hour_files",
    ):
        if metadata.get(key) != audit.get(key):
            return None
    if (
        metadata.get("schema_version") != MONTH_CACHE_SCHEMA
        or metadata.get("feature_sha256") != _sha256_file(path)
    ):
        return None
    frame = pd.read_parquet(path)
    if len(frame) != int(metadata.get("rows", -1)):
        return None
    return frame


def _derive_month_m5(
    storage_root: Path,
    symbol: str,
    year: int,
    month: int,
    foundation: Any,
) -> pd.DataFrame:
    parts = []
    for path, raw in foundation.iter_raw_month(storage_root, symbol, year, month):
        ticks = foundation.decode_payload(raw, symbol, path.name)
        if not ticks:
            continue
        timestamp = np.fromiter(
            (tick.timestamp_ms for tick in ticks), dtype=np.int64, count=len(ticks)
        )
        bid = np.fromiter((tick.bid for tick in ticks), dtype=float, count=len(ticks))
        ask = np.fromiter((tick.ask for tick in ticks), dtype=float, count=len(ticks))
        bid_volume = np.fromiter(
            (tick.bid_volume for tick in ticks), dtype=float, count=len(ticks)
        )
        ask_volume = np.fromiter(
            (tick.ask_volume for tick in ticks), dtype=float, count=len(ticks)
        )
        micro = _aggregate_tick_arrays(timestamp, bid, ask, bid_volume, ask_volume)
        ohlc = _aggregate_ohlc_arrays(timestamp, bid, ask)
        parts.append(micro.merge(ohlc, on="timestamp_ms", validate="one_to_one"))
    if not parts:
        return pd.DataFrame()
    frame = pd.concat(parts, ignore_index=True).sort_values("timestamp_ms").reset_index(drop=True)
    if frame["timestamp_ms"].duplicated().any():
        raise ConfirmedEventSpecialistError(f"duplicate M5 bars in {year:04d}-{month:02d}")
    return frame


def _aggregate_ohlc_arrays(
    timestamp_ms: np.ndarray, bid: np.ndarray, ask: np.ndarray
) -> pd.DataFrame:
    if not len(timestamp_ms):
        return pd.DataFrame()
    bucket = timestamp_ms - timestamp_ms % BAR_WIDTH_MS
    starts = np.r_[0, np.flatnonzero(np.diff(bucket)) + 1]
    counts = np.diff(np.r_[starts, len(bucket)])
    ends = starts + counts - 1
    mid = (bid + ask) / 2.0
    values: dict[str, Any] = {"timestamp_ms": bucket[starts].astype(np.int64)}
    for name, series in (("bid", bid), ("ask", ask), ("mid", mid)):
        values[f"{name}_open"] = series[starts]
        values[f"{name}_high"] = np.maximum.reduceat(series, starts)
        values[f"{name}_low"] = np.minimum.reduceat(series, starts)
        values[f"{name}_close"] = series[ends]
    return pd.DataFrame(values)


def enrich_m5_features(frame: pd.DataFrame, contract: Mapping[str, Any]) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    result = frame.sort_values("timestamp_ms").reset_index(drop=True).copy()
    aggregation = contract["aggregation"]
    period = int(aggregation["atr_period_bars"])
    previous_close = result["mid_close"].shift(1)
    true_range = pd.concat(
        [
            result["mid_high"] - result["mid_low"],
            (result["mid_high"] - previous_close).abs(),
            (result["mid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result["atr"] = true_range.ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()
    atr_baseline = int(aggregation["atr_baseline_bars"])
    result["atr_ratio"] = result["atr"] / result["atr"].rolling(
        atr_baseline, min_periods=atr_baseline // 2
    ).median()
    quote_baseline = int(aggregation["quote_intensity_baseline_bars"])
    result["quote_intensity_ratio"] = result["xau_tick_count"] / result[
        "xau_tick_count"
    ].rolling(quote_baseline, min_periods=quote_baseline // 2).median()
    move_count = result["tick_move_count"].replace(0, np.nan)
    result["tick_imbalance_5m"] = result["tick_signed_move"] / move_count
    result["tick_imbalance_15m"] = result["tick_signed_move"].rolling(3).sum() / result[
        "tick_move_count"
    ].rolling(3).sum().replace(0, np.nan)
    contiguous_15m = result["timestamp_ms"] - result["timestamp_ms"].shift(2) == 2 * BAR_WIDTH_MS
    result.loc[~contiguous_15m, "tick_imbalance_15m"] = np.nan
    bar_range = result["mid_high"] - result["mid_low"]
    result["body_fraction"] = (
        (result["mid_close"] - result["mid_open"]).abs()
        / bar_range.replace(0, np.nan)
    ).fillna(0.0)
    result["close_location"] = (
        (result["mid_close"] - result["mid_low"]) / bar_range.replace(0, np.nan)
    ).fillna(0.5)
    timestamps = pd.to_datetime(result["timestamp_ms"], unit="ms", utc=True)
    result["date_utc"] = timestamps.dt.strftime("%Y-%m-%d")
    result["hour_utc"] = timestamps.dt.hour.astype(int)
    return result.replace([np.inf, -np.inf], np.nan)


def _validate_feature_frame(frame: pd.DataFrame) -> None:
    required = {
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
        "atr",
        "atr_ratio",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "quote_intensity_ratio",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ConfirmedEventSpecialistError(f"M5 feature cache missing columns: {sorted(missing)}")
    timestamps = frame["timestamp_ms"].to_numpy(dtype=np.int64)
    if len(timestamps) == 0 or np.any(np.diff(timestamps) <= 0):
        raise ConfirmedEventSpecialistError("M5 feature cache is empty or non-chronological")
    if bool((frame["ask_low"] < frame["bid_low"]).any()):
        raise ConfirmedEventSpecialistError("M5 cache contains crossed executable quotes")


def generate_candidates(
    frame: pd.DataFrame, contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    families = {str(row["family_id"]): row for row in contract["families"]}
    candidates = []
    candidates.extend(_session_sweep_candidates(frame, families["session_boundary_sweep_reclaim_v1"], contract))
    candidates.extend(_compression_retest_candidates(frame, families["compression_break_retest_v1"], contract))
    candidates.extend(_shock_failure_candidates(frame, families["shock_failure_reclaim_v1"], contract))
    return sorted(candidates, key=lambda row: (int(row["decision_timestamp_ms"]), row["family_id"], row["direction"]))


def _session_sweep_candidates(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    consumed: set[tuple[str, str, str]] = set()
    for profile in family["profiles"]:
        reference = frame[
            (frame["hour_utc"] >= int(profile["reference_start_hour_utc"]))
            & (frame["hour_utc"] < int(profile["reference_end_hour_utc"]))
        ]
        grouped = {}
        for date, part in reference.groupby("date_utc", sort=False):
            if len(part) >= int(family["minimum_reference_bars"]):
                grouped[str(date)] = (
                    float(part["mid_high"].max()),
                    float(part["mid_low"].min()),
                )
        decisions = frame[
            (frame["hour_utc"] >= int(profile["decision_start_hour_utc"]))
            & (frame["hour_utc"] < int(profile["decision_end_hour_utc"]))
        ]
        for index, row in decisions.iterrows():
            bounds = grouped.get(str(row["date_utc"]))
            if bounds is None or not _finite_signal_row(row):
                continue
            reference_high, reference_low = bounds
            atr = float(row["atr"])
            bar_range = float(row["mid_high"] - row["mid_low"])
            if bar_range <= 0 or float(row["quote_intensity_ratio"]) < float(
                family["minimum_quote_intensity_ratio"]
            ):
                continue
            lower_wick = (min(float(row["mid_open"]), float(row["mid_close"])) - float(row["mid_low"])) / bar_range
            upper_wick = (float(row["mid_high"]) - max(float(row["mid_open"]), float(row["mid_close"]))) / bar_range
            directions = []
            if (
                float(row["mid_low"]) <= reference_low - float(family["minimum_sweep_atr"]) * atr
                and float(row["mid_close"]) >= reference_low + float(family["minimum_reclaim_atr"]) * atr
                and lower_wick >= float(family["minimum_wick_fraction"])
                and float(row["tick_imbalance_5m"]) >= float(family["minimum_directional_tick_imbalance_5m"])
                and float(row["tick_imbalance_15m"]) >= float(family["minimum_directional_tick_imbalance_15m"])
            ):
                directions.append(("LONG", reference_low, float(row["bid_low"])))
            if (
                float(row["mid_high"]) >= reference_high + float(family["minimum_sweep_atr"]) * atr
                and float(row["mid_close"]) <= reference_high - float(family["minimum_reclaim_atr"]) * atr
                and upper_wick >= float(family["minimum_wick_fraction"])
                and float(row["tick_imbalance_5m"]) <= -float(family["minimum_directional_tick_imbalance_5m"])
                and float(row["tick_imbalance_15m"]) <= -float(family["minimum_directional_tick_imbalance_15m"])
            ):
                directions.append(("SHORT", reference_high, float(row["ask_high"])))
            for direction, boundary, extreme in directions:
                consumed_key = (str(profile["profile_id"]), str(row["date_utc"]), direction)
                if consumed_key in consumed:
                    continue
                candidate = _make_candidate(
                    row=row,
                    family=family,
                    profile_id=str(profile["profile_id"]),
                    direction=direction,
                    event_id=f"{profile['profile_id']}:{row['date_utc']}:{direction}",
                    structural_extreme=extreme,
                    reference_level=boundary,
                    contract=contract,
                )
                if candidate is not None:
                    rows.append(candidate)
                    consumed.add(consumed_key)
    return rows


def _compression_retest_candidates(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    consumed: set[str] = set()
    last_decision = {"LONG": -10**18, "SHORT": -10**18}
    lookback = int(family["compression_lookback_bars"])
    values = frame.reset_index(drop=True)
    timestamps = values["timestamp_ms"].to_numpy(dtype=np.int64)
    gap_ok = pd.Series(np.r_[False, np.diff(timestamps) == BAR_WIDTH_MS])
    history_contiguous = (
        gap_ok.rolling(lookback - 1, min_periods=lookback - 1).sum().shift(1)
        == lookback - 1
    )
    reference_highs = values["mid_high"].shift(1).rolling(lookback).max()
    reference_lows = values["mid_low"].shift(1).rolling(lookback).min()
    atr = values["atr"]
    in_hours = (values["hour_utc"] >= int(family["decision_start_hour_utc"])) & (
        values["hour_utc"] < int(family["decision_end_hour_utc"])
    )
    eligible = (
        _finite_signal_mask(values)
        & history_contiguous
        & in_hours
        & ((reference_highs - reference_lows) <= float(family["maximum_compression_range_atr"]) * atr)
        & (values["atr_ratio"] <= float(family["maximum_atr_ratio"]))
        & (values["body_fraction"] >= float(family["minimum_breakout_body_fraction"]))
        & (values["price_efficiency_5m"] >= float(family["minimum_breakout_efficiency"]))
        & (
            values["quote_intensity_ratio"]
            >= float(family["minimum_breakout_quote_intensity_ratio"])
        )
    )
    long_breakout = values["mid_close"] >= (
        reference_highs + float(family["minimum_breakout_atr"]) * atr
    )
    short_breakout = values["mid_close"] <= (
        reference_lows - float(family["minimum_breakout_atr"]) * atr
    )
    breakout_indices = np.flatnonzero(
        (eligible & (long_breakout | short_breakout)).to_numpy(dtype=bool)
    )
    breakout_indices = breakout_indices[breakout_indices < len(values) - 1]
    for breakout_index in breakout_indices:
        breakout = values.iloc[breakout_index]
        atr = float(breakout["atr"])
        reference_high = float(reference_highs.iloc[breakout_index])
        reference_low = float(reference_lows.iloc[breakout_index])
        direction = None
        boundary = 0.0
        if bool(long_breakout.iloc[breakout_index]):
            direction, boundary = "LONG", reference_high
        elif bool(short_breakout.iloc[breakout_index]):
            direction, boundary = "SHORT", reference_low
        if direction is None:
            continue
        event_id = f"compression:{int(breakout['timestamp_ms'])}:{direction}"
        if event_id in consumed:
            continue
        end = min(len(values), breakout_index + 1 + int(family["retest_window_bars"]))
        for confirmation_index in range(breakout_index + 1, end):
            confirmation = values.iloc[confirmation_index]
            if not _finite_signal_row(confirmation) or not _in_hours(confirmation, family):
                continue
            if int(confirmation["timestamp_ms"]) - int(breakout["timestamp_ms"]) != (
                confirmation_index - breakout_index
            ) * BAR_WIDTH_MS:
                break
            directional_imbalance = float(confirmation["tick_imbalance_5m"]) * (
                1.0 if direction == "LONG" else -1.0
            )
            if directional_imbalance < float(family["minimum_directional_tick_imbalance_5m"]):
                continue
            if direction == "LONG":
                confirmed = (
                    float(confirmation["mid_low"]) <= boundary + float(family["maximum_retest_distance_atr"]) * atr
                    and float(confirmation["mid_close"]) >= boundary + float(family["minimum_retest_close_atr"]) * atr
                )
                structural_extreme = float(confirmation["bid_low"])
            else:
                confirmed = (
                    float(confirmation["mid_high"]) >= boundary - float(family["maximum_retest_distance_atr"]) * atr
                    and float(confirmation["mid_close"]) <= boundary - float(family["minimum_retest_close_atr"]) * atr
                )
                structural_extreme = float(confirmation["ask_high"])
            decision_ms = int(confirmation["timestamp_ms"]) + BAR_WIDTH_MS
            if (
                not confirmed
                or decision_ms - last_decision[direction]
                < int(family["event_cooldown_minutes"]) * 60_000
            ):
                continue
            candidate = _make_candidate(
                row=confirmation,
                family=family,
                profile_id="FIXED",
                direction=direction,
                event_id=event_id,
                structural_extreme=structural_extreme,
                reference_level=boundary,
                contract=contract,
            )
            if candidate is not None:
                rows.append(candidate)
                consumed.add(event_id)
                last_decision[direction] = decision_ms
            break
    return rows


def _shock_failure_candidates(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    values = frame.reset_index(drop=True)
    impulse_bars = int(family["impulse_bars"])
    consumed: set[str] = set()
    last_decision = {"LONG": -10**18, "SHORT": -10**18}
    timestamps = values["timestamp_ms"].to_numpy(dtype=np.int64)
    gap_ok = pd.Series(np.r_[False, np.diff(timestamps) == BAR_WIDTH_MS])
    contiguous = (
        gap_ok.rolling(impulse_bars - 1, min_periods=impulse_bars - 1).sum()
        == impulse_bars - 1
    )
    start_open = values["mid_open"].shift(impulse_bars - 1)
    impulse_values = values["mid_close"] - start_open
    first_leg = (
        values["mid_close"].shift(impulse_bars - 1) - start_open
    ).abs()
    later_legs = values["mid_close"].diff().abs().rolling(impulse_bars - 1).sum()
    path_distance = first_leg + later_legs
    efficiency = impulse_values.abs() / path_distance.replace(0, np.nan)
    maximum_quote_intensity = values["quote_intensity_ratio"].rolling(impulse_bars).max()
    in_hours = (values["hour_utc"] >= int(family["decision_start_hour_utc"])) & (
        values["hour_utc"] < int(family["decision_end_hour_utc"])
    )
    eligible = (
        _finite_signal_mask(values)
        & contiguous
        & in_hours
        & (impulse_values.abs() >= float(family["minimum_impulse_atr"]) * values["atr"])
        & (efficiency >= float(family["minimum_impulse_efficiency"]))
        & (
            maximum_quote_intensity
            >= float(family["minimum_impulse_quote_intensity_ratio"])
        )
    )
    end_indices = np.flatnonzero(eligible.to_numpy(dtype=bool))
    end_indices = end_indices[end_indices < len(values) - 1]
    for end_index in end_indices:
        impulse_rows = values.iloc[end_index - impulse_bars + 1 : end_index + 1]
        end_row = impulse_rows.iloc[-1]
        start_price = float(start_open.iloc[end_index])
        end_price = float(end_row["mid_close"])
        impulse = end_price - start_price
        direction = "SHORT" if impulse > 0 else "LONG"
        midpoint = start_price + float(family["minimum_retrace_fraction"]) * impulse
        event_id = f"shock:{int(end_row['timestamp_ms'])}:{direction}"
        if event_id in consumed:
            continue
        confirmation_end = min(
            len(values), end_index + 1 + int(family["confirmation_window_bars"])
        )
        for confirmation_index in range(end_index + 1, confirmation_end):
            confirmation = values.iloc[confirmation_index]
            if not _finite_signal_row(confirmation) or not _in_hours(confirmation, family):
                continue
            if int(confirmation["timestamp_ms"]) - int(end_row["timestamp_ms"]) != (
                confirmation_index - end_index
            ) * BAR_WIDTH_MS:
                break
            imbalance = float(confirmation["tick_imbalance_5m"])
            confirmed = (
                direction == "SHORT"
                and float(confirmation["mid_close"]) <= midpoint
                and imbalance <= -float(family["minimum_directional_tick_imbalance_5m"])
            ) or (
                direction == "LONG"
                and float(confirmation["mid_close"]) >= midpoint
                and imbalance >= float(family["minimum_directional_tick_imbalance_5m"])
            )
            decision_ms = int(confirmation["timestamp_ms"]) + BAR_WIDTH_MS
            if (
                not confirmed
                or decision_ms - last_decision[direction]
                < int(family["event_cooldown_minutes"]) * 60_000
            ):
                continue
            observed = values.iloc[end_index - impulse_bars + 1 : confirmation_index + 1]
            structural_extreme = (
                float(observed["ask_high"].max())
                if direction == "SHORT"
                else float(observed["bid_low"].min())
            )
            candidate = _make_candidate(
                row=confirmation,
                family=family,
                profile_id="FIXED",
                direction=direction,
                event_id=event_id,
                structural_extreme=structural_extreme,
                reference_level=midpoint,
                contract=contract,
            )
            if candidate is not None:
                rows.append(candidate)
                consumed.add(event_id)
                last_decision[direction] = decision_ms
            break
    return rows


def _make_candidate(
    *,
    row: Mapping[str, Any],
    family: Mapping[str, Any],
    profile_id: str,
    direction: str,
    event_id: str,
    structural_extreme: float,
    reference_level: float,
    contract: Mapping[str, Any],
) -> dict[str, Any] | None:
    atr = float(row["atr"])
    buffer = float(family["stop_buffer_atr"]) * atr
    if direction == "LONG":
        entry_proxy = float(row["ask_close"])
        raw_stop = entry_proxy - (structural_extreme - buffer)
    else:
        entry_proxy = float(row["bid_close"])
        raw_stop = structural_extreme + buffer - entry_proxy
    stop_distance = max(raw_stop, float(family["minimum_stop_atr"]) * atr)
    execution = contract["execution"]
    quantity = float(execution["lot_size"]) * float(
        execution["contract_size_ounces_per_lot"]
    )
    maximum_stop = min(
        float(family["maximum_stop_atr"]) * atr,
        float(execution["maximum_initial_risk_usd"]) / quantity,
    )
    if stop_distance <= 0 or stop_distance > maximum_stop:
        return None
    spread = float(row["tick_spread_last"])
    if spread / stop_distance > float(execution["maximum_entry_spread_r"]):
        return None
    decision_ms = int(row["timestamp_ms"]) + BAR_WIDTH_MS
    split = _split(decision_ms, contract)
    if split is None:
        return None
    payload = f"{family['family_id']}|{profile_id}|{event_id}|{decision_ms}|{direction}"
    return {
        "candidate_id": hashlib.sha256(payload.encode("ascii")).hexdigest(),
        "family_id": str(family["family_id"]),
        "profile_id": profile_id,
        "mechanism": str(family["mechanism"]),
        "event_id": event_id,
        "symbol": str(contract["symbol"]),
        "split": split,
        "direction": direction,
        "signal_bar_start_utc": _iso_ms(int(row["timestamp_ms"])),
        "decision_time_utc": _iso_ms(decision_ms),
        "decision_timestamp_ms": decision_ms,
        "signal_open": float(row["mid_open"]),
        "signal_high": float(row["mid_high"]),
        "signal_low": float(row["mid_low"]),
        "signal_close": float(row["mid_close"]),
        "atr": atr,
        "atr_ratio": float(row["atr_ratio"]),
        "body_fraction": float(row["body_fraction"]),
        "close_location": float(row["close_location"]),
        "price_efficiency_5m": float(row["price_efficiency_5m"]),
        "tick_imbalance_5m": float(row["tick_imbalance_5m"]),
        "tick_imbalance_15m": float(row["tick_imbalance_15m"]),
        "quote_intensity_ratio": float(row["quote_intensity_ratio"]),
        "reference_level": reference_level,
        "structural_extreme": structural_extreme,
        "stop_distance": stop_distance,
        "stop_distance_atr": stop_distance / atr,
        "reward_r": float(family["reward_r"]),
        "maximum_hold_hours": int(family["maximum_hold_hours"]),
        "signal_tick_count": int(row["xau_tick_count"]),
    }


def _finite_signal_row(row: Mapping[str, Any]) -> bool:
    return all(
        math.isfinite(float(row[name]))
        for name in (
            "atr",
            "atr_ratio",
            "tick_imbalance_5m",
            "tick_imbalance_15m",
            "quote_intensity_ratio",
            "tick_spread_last",
        )
    ) and float(row["atr"]) > 0


def _finite_signal_mask(frame: pd.DataFrame) -> pd.Series:
    columns = (
        "atr",
        "atr_ratio",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "quote_intensity_ratio",
        "tick_spread_last",
    )
    values = frame.loc[:, columns].to_numpy(dtype=float)
    return pd.Series(np.isfinite(values).all(axis=1) & (values[:, 0] > 0), index=frame.index)


def _contiguous(frame: pd.DataFrame) -> bool:
    if frame.empty:
        return False
    timestamps = frame["timestamp_ms"].to_numpy(dtype=np.int64)
    return bool(len(timestamps) == 1 or np.all(np.diff(timestamps) == BAR_WIDTH_MS))


def _in_hours(row: Mapping[str, Any], family: Mapping[str, Any]) -> bool:
    hour = int(row["hour_utc"])
    return int(family["decision_start_hour_utc"]) <= hour < int(
        family["decision_end_hour_utc"]
    )


def validate_candidates(candidates: Sequence[Mapping[str, Any]]) -> None:
    ids = [str(row["candidate_id"]) for row in candidates]
    keys = [
        (str(row["family_id"]), int(row["decision_timestamp_ms"]), str(row["direction"]))
        for row in candidates
    ]
    if len(ids) != len(set(ids)):
        raise ConfirmedEventSpecialistError("duplicate confirmed-event candidate IDs")
    if len(keys) != len(set(keys)):
        raise ConfirmedEventSpecialistError("duplicate confirmed-event candidate keys")
    if list(candidates) != sorted(
        candidates,
        key=lambda row: (
            int(row["decision_timestamp_ms"]),
            str(row["family_id"]),
            str(row["direction"]),
        ),
    ):
        raise ConfirmedEventSpecialistError("confirmed-event candidates are not chronological")


def replay_candidates(
    candidates: Sequence[Mapping[str, Any]],
    h1_bars: Sequence[Mapping[str, Any]],
    tick_store: VerifiedTickStore,
    contract: Mapping[str, Any],
) -> list[dict[str, Any]]:
    bars_by_hour = {int(row["timestamp_ms"]): row for row in h1_bars}
    return [
        _replay_candidate(candidate, bars_by_hour, tick_store, contract)
        for candidate in candidates
    ]


def _replay_candidate(
    candidate: Mapping[str, Any],
    bars_by_hour: Mapping[int, Mapping[str, Any]],
    tick_store: VerifiedTickStore,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    execution = contract["execution"]
    base = dict(candidate)
    delay_ms = int(execution["maximum_entry_delay_minutes"]) * 60_000
    entry_tick = tick_store.first_tick_at_or_after(
        int(candidate["decision_timestamp_ms"]), delay_ms
    )
    if entry_tick is None:
        return _empty_label(base, "INELIGIBLE", "NO_QUOTE_WITHIN_ENTRY_WINDOW")
    entry_ms = int(entry_tick.timestamp_ms)
    entry_bid = float(entry_tick.bid)
    entry_ask = float(entry_tick.ask)
    entry_spread = entry_ask - entry_bid
    stop_distance = float(candidate["stop_distance"])
    if entry_spread / stop_distance > float(execution["maximum_entry_spread_r"]):
        return _empty_label(base, "INELIGIBLE", "ENTRY_SPREAD_R")
    quantity = float(execution["lot_size"]) * float(
        execution["contract_size_ounces_per_lot"]
    )
    if stop_distance * quantity > float(execution["maximum_initial_risk_usd"]) + 1e-9:
        return _empty_label(base, "INELIGIBLE", "INITIAL_RISK_USD")
    direction = str(candidate["direction"])
    entry_price = entry_ask if direction == "LONG" else entry_bid
    if direction == "LONG":
        planned_stop = entry_price - stop_distance
        planned_target = entry_price + float(candidate["reward_r"]) * stop_distance
    else:
        planned_stop = entry_price + stop_distance
        planned_target = entry_price - float(candidate["reward_r"]) * stop_distance
    deadline_ms = entry_ms + int(candidate["maximum_hold_hours"]) * HOUR_MS
    grace_end_ms = deadline_ms + int(execution["maximum_timeout_exit_grace_hours"]) * HOUR_MS
    hour_ms = entry_ms - entry_ms % HOUR_MS
    maximum_favorable = 0.0
    maximum_adverse = 0.0
    exit_tick = None
    exit_price = None
    exit_reason = ""
    while hour_ms <= grace_end_ms:
        bar = bars_by_hour.get(hour_ms)
        side = "bid" if direction == "LONG" else "ask"
        low = float(bar[f"{side}_low"]) if bar is not None else None
        high = float(bar[f"{side}_high"]) if bar is not None else None
        boundary_possible = bool(
            bar is not None
            and (
                direction == "LONG"
                and (low <= planned_stop or high >= planned_target)
                or direction == "SHORT"
                and (high >= planned_stop or low <= planned_target)
            )
        )
        force_ticks = (
            hour_ms == entry_ms - entry_ms % HOUR_MS
            or boundary_possible
            or hour_ms <= deadline_ms < hour_ms + HOUR_MS
            or hour_ms > deadline_ms
            or bar is None
        )
        if not force_ticks and bar is not None:
            if direction == "LONG":
                maximum_favorable = max(maximum_favorable, high - entry_price)
                maximum_adverse = max(maximum_adverse, entry_price - low)
            else:
                maximum_favorable = max(maximum_favorable, entry_price - low)
                maximum_adverse = max(maximum_adverse, high - entry_price)
            hour_ms += HOUR_MS
            continue
        for tick in tick_store.load_hour(hour_ms):
            tick_ms = int(tick.timestamp_ms)
            if tick_ms < entry_ms:
                continue
            side_price = float(tick.bid) if direction == "LONG" else float(tick.ask)
            if direction == "LONG":
                maximum_favorable = max(maximum_favorable, side_price - entry_price)
                maximum_adverse = max(maximum_adverse, entry_price - side_price)
            else:
                maximum_favorable = max(maximum_favorable, entry_price - side_price)
                maximum_adverse = max(maximum_adverse, side_price - entry_price)
            if tick_ms <= deadline_ms:
                if direction == "LONG" and side_price <= planned_stop:
                    exit_tick, exit_price, exit_reason = tick, side_price, "STOP"
                    break
                if direction == "LONG" and side_price >= planned_target:
                    exit_tick, exit_price, exit_reason = tick, side_price, "TARGET"
                    break
                if direction == "SHORT" and side_price >= planned_stop:
                    exit_tick, exit_price, exit_reason = tick, side_price, "STOP"
                    break
                if direction == "SHORT" and side_price <= planned_target:
                    exit_tick, exit_price, exit_reason = tick, side_price, "TARGET"
                    break
            if tick_ms >= deadline_ms:
                exit_tick, exit_price, exit_reason = tick, side_price, "TIMEOUT"
                break
        if exit_tick is not None:
            break
        hour_ms += HOUR_MS
    if exit_tick is None or exit_price is None:
        return _empty_label(base, "UNRESOLVED", "EXIT_UNAVAILABLE")
    exit_ms = int(exit_tick.timestamp_ms)
    duration_hours = (exit_ms - entry_ms) / HOUR_MS
    price_move = exit_price - entry_price if direction == "LONG" else entry_price - exit_price
    gross_pnl = price_move * quantity
    execution_stress = float(execution["extra_execution_cost_usd"])
    holding_stress = duration_hours / 24.0 * float(
        execution["holding_cost_per_24h_usd"]
    )
    stress_net = gross_pnl - execution_stress - holding_stress
    risk_usd = stop_distance * quantity
    return {
        **base,
        "status": "RESOLVED",
        "entry_time_utc": _iso_ms(entry_ms),
        "entry_timestamp_ms": entry_ms,
        "exit_time_utc": _iso_ms(exit_ms),
        "exit_timestamp_ms": exit_ms,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "entry_bid": entry_bid,
        "entry_ask": entry_ask,
        "entry_spread": entry_spread,
        "entry_spread_r": entry_spread / stop_distance,
        "planned_stop": planned_stop,
        "planned_target": planned_target,
        "exit_reason": exit_reason,
        "duration_hours": duration_hours,
        "gross_pnl_usd": gross_pnl,
        "execution_stress_usd": execution_stress,
        "holding_stress_usd": holding_stress,
        "stress_net_pnl_usd": stress_net,
        "gross_r": gross_pnl / risk_usd,
        "stress_net_r": stress_net / risk_usd,
        "mfe_r": maximum_favorable / stop_distance,
        "mae_r": maximum_adverse / stop_distance,
        "label_profitable_after_stress": int(stress_net > 0),
    }


def _empty_label(base: Mapping[str, Any], status: str, reason: str) -> dict[str, Any]:
    return {
        **base,
        "status": status,
        "entry_time_utc": "",
        "entry_timestamp_ms": None,
        "exit_time_utc": "",
        "exit_timestamp_ms": None,
        "entry_price": None,
        "exit_price": None,
        "entry_bid": None,
        "entry_ask": None,
        "entry_spread": None,
        "entry_spread_r": None,
        "planned_stop": None,
        "planned_target": None,
        "exit_reason": reason,
        "duration_hours": None,
        "gross_pnl_usd": None,
        "execution_stress_usd": None,
        "holding_stress_usd": None,
        "stress_net_pnl_usd": None,
        "gross_r": None,
        "stress_net_r": None,
        "mfe_r": None,
        "mae_r": None,
        "label_profitable_after_stress": None,
    }


def build_report(
    *,
    phase1_root: Path,
    contract_file: Path,
    contract: Mapping[str, Any],
    source_audits: Sequence[Mapping[str, Any]],
    h1_audits: Sequence[Mapping[str, Any]],
    cache_manifest: Mapping[str, Any],
    features: pd.DataFrame,
    candidates: Sequence[Mapping[str, Any]],
    labels: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    resolved = [row for row in labels if row["status"] == "RESOLVED"]
    eligible = [row for row in labels if row["status"] != "INELIGIBLE"]
    unresolved = [row for row in labels if row["status"] == "UNRESOLVED"]
    source_days = _source_days(features, contract)
    family_ids = [str(row["family_id"]) for row in contract["families"]]
    segments = ("train", "validation", "internal_test", "exam")
    family_results: dict[str, Any] = {}
    flat_metrics = []
    train_survivors = []
    validation_survivors = []
    internal_survivors = []
    exam_survivors = []
    for family_id in family_ids:
        result: dict[str, Any] = {}
        opened = True
        for segment in segments:
            rows = [
                row
                for row in resolved
                if row["family_id"] == family_id and row["split"] == segment
            ]
            metrics = economic_metrics(rows, source_days[segment])
            gates = segment_gates(metrics, contract[f"{segment if segment != 'train' else 'family_train'}_gates"])
            passed = opened and all(gates.values())
            result[segment] = {
                "opened_for_decision": opened,
                "metrics": metrics,
                "gates": gates,
                "passed": passed,
            }
            flat_metrics.append(
                {
                    "family_id": family_id,
                    "segment": segment,
                    "opened_for_decision": opened,
                    "passed": passed,
                    **metrics,
                    **{f"gate_{key}": value for key, value in gates.items()},
                }
            )
            if segment == "train" and passed:
                train_survivors.append(family_id)
            elif segment == "validation" and passed:
                validation_survivors.append(family_id)
            elif segment == "internal_test" and passed:
                internal_survivors.append(family_id)
            elif segment == "exam" and passed:
                exam_survivors.append(family_id)
            opened = passed
        family_results[family_id] = result

    survivor_rows = [row for row in resolved if row["family_id"] in exam_survivors]
    portfolio_rows = portfolio_select(survivor_rows, contract)
    portfolio_by_segment = {
        segment: economic_metrics(
            [row for row in portfolio_rows if row["split"] == segment],
            source_days[segment],
        )
        for segment in segments
    }
    exam_episodes = episode_metrics(
        [row for row in portfolio_rows if row["split"] == "exam"]
    )
    portfolio_gates = portfolio_exam_gates(
        portfolio_by_segment["exam"], exam_episodes, contract
    )
    quality = contract["quality_gates"]
    resolved_share = len(resolved) / len(eligible) if eligible else 0.0
    quality_gates = {
        "all_expected_months_valid": len(source_audits)
        == int(contract["period"]["expected_months"]),
        "resolved_share_ge_minimum": resolved_share
        >= float(quality["minimum_resolved_share"]),
        "candidate_ids_unique": len({row["candidate_id"] for row in candidates})
        == len(candidates),
        "candidate_keys_unique": len(
            {
                (row["family_id"], row["decision_timestamp_ms"], row["direction"])
                for row in candidates
            }
        )
        == len(candidates),
        "candidates_chronological": list(candidates)
        == sorted(
            candidates,
            key=lambda row: (
                row["decision_timestamp_ms"],
                row["family_id"],
                row["direction"],
            ),
        ),
        "h1_source_reconciles": [row["month"] for row in source_audits]
        == [row["month"] for row in h1_audits],
    }
    classification = _classification(
        quality_gates,
        train_survivors,
        validation_survivors,
        internal_survivors,
        exam_survivors,
        portfolio_gates,
    )
    return {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "storage_root": str(_resolve_storage_root(contract)),
        "source_months": len(source_audits),
        "source_digest": _canonical_sha256(source_audits),
        "feature_cache": dict(cache_manifest),
        "feature_rows": len(features),
        "source_days": source_days,
        "candidate_count": len(candidates),
        "candidate_counts_by_family": dict(Counter(row["family_id"] for row in candidates)),
        "label_status_counts": dict(Counter(row["status"] for row in labels)),
        "ineligible_reasons": dict(
            Counter(row["exit_reason"] for row in labels if row["status"] == "INELIGIBLE")
        ),
        "unresolved_reasons": dict(Counter(row["exit_reason"] for row in unresolved)),
        "resolved_share": resolved_share,
        "quality_gates": quality_gates,
        "family_results": family_results,
        "stage_survivors": {
            "train": train_survivors,
            "validation": validation_survivors,
            "internal_test": internal_survivors,
            "exam": exam_survivors,
        },
        "portfolio": {
            "selected_trades": len(portfolio_rows),
            "by_segment": portfolio_by_segment,
            "exam_episode_metrics": exam_episodes,
            "exam_gates": portfolio_gates,
        },
        "authorization": {
            **dict(contract["authorization"]),
            "strategy_promotion_authorized": False,
            "forward_shadow_candidate": classification
            == "RESEARCH_SURVIVOR_FORWARD_SHADOW_ONLY",
            "demo_or_live_authorized": False,
        },
        "limitations": [
            "Every retrospective window has known program-level research contamination.",
            "A survivor is limited to prospective forward shadow before demo consideration.",
            "Shared-account floating equity, margin, and broker parity remain later gates.",
        ],
        "_family_metric_rows": flat_metrics,
        "_portfolio_rows": portfolio_rows,
    }


def economic_metrics(
    rows: Sequence[Mapping[str, Any]], source_days: int
) -> dict[str, Any]:
    ordered = sorted(
        rows, key=lambda row: (int(row["exit_timestamp_ms"]), str(row["candidate_id"]))
    )
    returns = [float(row["stress_net_r"]) for row in ordered]
    pnl = [float(row["stress_net_pnl_usd"]) for row in ordered]
    gains = sum(value for value in returns if value > 0)
    losses = -sum(value for value in returns if value < 0)
    cumulative = np.cumsum(returns) if returns else np.array([], dtype=float)
    months: dict[str, float] = defaultdict(float)
    for row in ordered:
        months[str(row["exit_time_utc"])[:7]] += float(row["stress_net_r"])
    positive_months = sum(value > 0 for value in months.values())
    top_five = sorted((value for value in returns if value > 0), reverse=True)[:5]
    top_ten = sorted((value for value in returns if value > 0), reverse=True)[:10]
    direction_counts = Counter(str(row["direction"]) for row in ordered)
    return {
        "trades": len(ordered),
        "wins": sum(value > 0 for value in returns),
        "win_rate_pct": 100.0 * sum(value > 0 for value in returns) / len(returns)
        if returns
        else 0.0,
        "stress_net_usd": sum(pnl),
        "stress_net_r": sum(returns),
        "stress_profit_factor": gains / losses if losses > 0 else None,
        "average_stress_r": sum(returns) / len(returns) if returns else 0.0,
        "max_closed_drawdown_r": _max_drawdown(cumulative),
        "source_days": source_days,
        "trades_per_source_day": len(ordered) / source_days if source_days else 0.0,
        "active_exit_months": len(months),
        "positive_exit_months": positive_months,
        "positive_exit_month_share": positive_months / len(months) if months else 0.0,
        "long_trades": direction_counts["LONG"],
        "short_trades": direction_counts["SHORT"],
        "top_five_winners_removed_net_r": sum(returns) - sum(top_five),
        "top_ten_winners_removed_net_r": sum(returns) - sum(top_ten),
    }


def segment_gates(
    metrics: Mapping[str, Any], configured: Mapping[str, Any]
) -> dict[str, bool]:
    profit_factor = metrics["stress_profit_factor"]
    gates = {
        "trades_ge_minimum": int(metrics["trades"]) >= int(configured["minimum_trades"]),
        "each_direction_ge_minimum": min(
            int(metrics["long_trades"]), int(metrics["short_trades"])
        )
        >= int(configured["minimum_trades_each_direction"]),
        "pf_ge_minimum": profit_factor is not None
        and float(profit_factor) >= float(configured["minimum_stress_profit_factor"]),
        "average_r_ge_minimum": float(metrics["average_stress_r"])
        >= float(configured["minimum_average_stress_r"]),
        "positive_month_share_ge_minimum": float(metrics["positive_exit_month_share"])
        >= float(configured["minimum_positive_exit_month_share"]),
        "drawdown_r_lte_maximum": float(metrics["max_closed_drawdown_r"])
        <= float(configured["maximum_closed_drawdown_r"]),
    }
    if "minimum_trades_per_source_day" in configured:
        gates["trades_per_source_day_ge_minimum"] = float(
            metrics["trades_per_source_day"]
        ) >= float(configured["minimum_trades_per_source_day"])
    if configured.get("require_top_ten_winners_removed_net_positive"):
        gates["top_ten_winners_removed_positive"] = float(
            metrics["top_ten_winners_removed_net_r"]
        ) > 0
    if configured.get("require_top_five_winners_removed_net_positive"):
        gates["top_five_winners_removed_positive"] = float(
            metrics["top_five_winners_removed_net_r"]
        ) > 0
    return gates


def portfolio_select(
    rows: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    configured = contract["portfolio_gates"]
    priority = {
        str(row["family_id"]): index for index, row in enumerate(contract["families"])
    }
    ordered = sorted(
        rows,
        key=lambda row: (
            int(row["entry_timestamp_ms"]),
            priority[str(row["family_id"])],
            str(row["candidate_id"]),
        ),
    )
    active: list[int] = []
    day_counts: Counter[str] = Counter()
    selected = []
    for row in ordered:
        entry_ms = int(row["entry_timestamp_ms"])
        active = [exit_ms for exit_ms in active if exit_ms > entry_ms]
        day = str(row["entry_time_utc"])[:10]
        if (
            len(active) >= int(configured["maximum_concurrent_trades"])
            or day_counts[day] >= int(configured["maximum_trades_per_utc_day"])
        ):
            continue
        selected.append(dict(row))
        active.append(int(row["exit_timestamp_ms"]))
        day_counts[day] += 1
    return selected


def episode_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = sorted(
        rows, key=lambda row: (int(row["entry_timestamp_ms"]), str(row["candidate_id"]))
    )
    episodes = []
    current = None
    for row in ordered:
        entry = int(row["entry_timestamp_ms"])
        exit_ms = int(row["exit_timestamp_ms"])
        if current is None or entry > int(current["end_ms"]):
            current = {
                "start_ms": entry,
                "end_ms": exit_ms,
                "net_r": float(row["stress_net_r"]),
                "trades": 1,
            }
            episodes.append(current)
        else:
            current["end_ms"] = max(int(current["end_ms"]), exit_ms)
            current["net_r"] = float(current["net_r"]) + float(row["stress_net_r"])
            current["trades"] = int(current["trades"]) + 1
    positive = [float(row["net_r"]) for row in episodes if float(row["net_r"]) > 0]
    total_net = sum(float(row["net_r"]) for row in episodes)
    top_three = sorted(positive, reverse=True)[:3]
    return {
        "episodes": len(episodes),
        "maximum_trades_one_episode": max(
            (int(row["trades"]) for row in episodes), default=0
        ),
        "top_episode_profit_share": max(positive, default=0.0) / sum(positive)
        if positive
        else 0.0,
        "top_three_episodes_removed_net_r": total_net - sum(top_three),
    }


def portfolio_exam_gates(
    metrics: Mapping[str, Any], episodes: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, bool]:
    configured = contract["portfolio_gates"]
    profit_factor = metrics["stress_profit_factor"]
    return {
        "trades_per_source_day_ge_minimum": float(metrics["trades_per_source_day"])
        >= float(configured["minimum_exam_trades_per_source_day"]),
        "pf_ge_minimum": profit_factor is not None
        and float(profit_factor) >= float(configured["minimum_exam_stress_profit_factor"]),
        "average_r_ge_minimum": float(metrics["average_stress_r"])
        >= float(configured["minimum_exam_average_stress_r"]),
        "drawdown_r_lte_maximum": float(metrics["max_closed_drawdown_r"])
        <= float(configured["maximum_exam_closed_drawdown_r"]),
        "top_episode_share_lte_maximum": float(episodes["top_episode_profit_share"])
        <= float(configured["maximum_top_episode_profit_share"]),
        "top_three_episodes_removed_positive": float(
            episodes["top_three_episodes_removed_net_r"]
        )
        > 0,
    }


def _classification(
    quality_gates: Mapping[str, bool],
    train: Sequence[str],
    validation: Sequence[str],
    internal: Sequence[str],
    exam: Sequence[str],
    portfolio_gates: Mapping[str, bool],
) -> str:
    if not all(quality_gates.values()):
        return "CONFIRMED_EVENT_SPECIALISTS_INVALID"
    if not train:
        return "NO_TRAIN_FAMILY_SURVIVOR"
    if not validation:
        return "NO_VALIDATION_FAMILY_SURVIVOR"
    if not internal:
        return "NO_INTERNAL_TEST_FAMILY_SURVIVOR"
    if not exam:
        return "NO_EXAM_FAMILY_SURVIVOR"
    if not all(portfolio_gates.values()):
        return "CONFIRMED_EVENT_PORTFOLIO_GATE_FAIL"
    return "RESEARCH_SURVIVOR_FORWARD_SHADOW_ONLY"


def _source_days(frame: pd.DataFrame, contract: Mapping[str, Any]) -> dict[str, int]:
    result = {}
    for segment in ("train", "validation", "internal_test", "exam"):
        start, end = _segment_bounds(segment, contract)
        selected = frame[
            (frame["timestamp_ms"] >= start) & (frame["timestamp_ms"] < end)
        ]
        result[segment] = int(selected["date_utc"].nunique())
    return result


def _split(timestamp_ms: int, contract: Mapping[str, Any]) -> str | None:
    for segment in ("train", "validation", "internal_test", "exam"):
        start, end = _segment_bounds(segment, contract)
        if start <= timestamp_ms < end:
            return segment
    return None


def _segment_bounds(segment: str, contract: Mapping[str, Any]) -> tuple[int, int]:
    windows = contract["windows"]
    if segment == "train":
        return _parse_ms(windows["train_start_utc"]), _parse_ms(
            windows["train_end_exclusive_utc"]
        )
    if segment == "validation":
        return _parse_ms(windows["train_end_exclusive_utc"]), _parse_ms(
            windows["validation_end_exclusive_utc"]
        )
    if segment == "internal_test":
        return _parse_ms(windows["validation_end_exclusive_utc"]), _parse_ms(
            windows["internal_test_end_exclusive_utc"]
        )
    return _parse_ms(windows["internal_test_end_exclusive_utc"]), _parse_ms(
        windows["exam_end_exclusive_utc"]
    )


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy Confirmed Event Specialists V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "## Source And Quality",
        "",
        f"- Source months: `{payload['source_months']}`",
        f"- M5 feature rows: `{payload['feature_rows']}`",
        f"- Candidates: `{payload['candidate_count']}`",
        f"- Resolved share: `{payload['resolved_share'] * 100.0:.2f}%`",
    ]
    for name, passed in payload["quality_gates"].items():
        lines.append(f"- Quality `{name}`: `{passed}`")
    lines.extend(["", "## Family Firewall", ""])
    for family, result in payload["family_results"].items():
        lines.append(f"### {family}")
        lines.append("")
        for segment in ("train", "validation", "internal_test", "exam"):
            row = result[segment]
            metrics = row["metrics"]
            pf = metrics["stress_profit_factor"]
            pf_text = "n/a" if pf is None else f"{pf:.3f}"
            lines.append(
                f"- {segment}: opened `{row['opened_for_decision']}`, passed `{row['passed']}`, "
                f"trades `{metrics['trades']}`, PF `{pf_text}`, average R "
                f"`{metrics['average_stress_r']:.4f}`, net R `{metrics['stress_net_r']:.2f}`"
            )
        lines.append("")
    lines.extend(["## Survivor Portfolio", ""])
    lines.append(f"- Exam survivors: `{payload['stage_survivors']['exam']}`")
    exam = payload["portfolio"]["by_segment"]["exam"]
    pf = exam["stress_profit_factor"]
    pf_text = "n/a" if pf is None else f"{pf:.3f}"
    lines.append(f"- Exam trades: `{exam['trades']}`")
    lines.append(f"- Exam trades/source day: `{exam['trades_per_source_day']:.3f}`")
    lines.append(f"- Exam stress PF: `{pf_text}`")
    lines.append(f"- Exam average stress R: `{exam['average_stress_r']:.4f}`")
    lines.append(f"- Exam closed drawdown R: `{exam['max_closed_drawdown_r']:.2f}`")
    for name, passed in payload["portfolio"]["exam_gates"].items():
        lines.append(f"- Portfolio gate `{name}`: `{passed}`")
    lines.extend(
        [
            "",
            "## Authorization",
            "",
            "- Research only: `true`",
            f"- Forward shadow candidate: `{payload['authorization']['forward_shadow_candidate']}`",
            "- Demo or live authorized: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def _max_drawdown(values: Sequence[float] | np.ndarray) -> float:
    peak = 0.0
    maximum = 0.0
    for value in values:
        current = float(value)
        peak = max(peak, current)
        maximum = max(maximum, peak - current)
    return maximum


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": _sha256_file(path), "bytes": path.stat().st_size}


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _parse_ms(value: Any) -> int:
    return int(datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp() * 1000)


def _iso_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, UTC).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")
