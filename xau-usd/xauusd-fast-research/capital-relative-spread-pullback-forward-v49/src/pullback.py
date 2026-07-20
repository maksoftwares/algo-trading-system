from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_PATTERN = re.compile(r"XAUUSD_(\d{8})\.csv$")
CANDIDATE_COLUMNS = (
    "timestamp_utc",
    "tick_time_msc",
    "date_utc",
    "utc_block_start_ms",
    "bid",
    "ask",
    "mid",
    "spread_price",
    "scale_dollars",
    "impulse_dollars",
    "pullback_dollars",
    "resume_dollars",
    "retracement_fraction",
    "spread_baseline_dollars",
    "spread_ratio_to_baseline",
    "signed_update_imbalance",
    "displacement_price",
    "candidate_side",
)


def load_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / "config" / "capital_relative_spread_pullback_forward_v49.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], omitted_key: str) -> str:
    work = dict(payload)
    work.pop(omitted_key, None)
    encoded = json.dumps(
        work, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()).replace("\\", "/"),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def calibration_date(path: Path) -> pd.Timestamp:
    match = CALIBRATION_PATTERN.search(path.name)
    if match is None:
        raise ValueError(f"V49 calibration filename lacks a date: {path}")
    return pd.Timestamp(match.group(1), tz="UTC")


def discover_calibration_files(config: Mapping[str, Any]) -> list[Path]:
    source = config["calibration_source"]
    start = pd.Timestamp(source["start_inclusive_utc"])
    end = pd.Timestamp(source["end_exclusive_utc"])
    return [
        path
        for path in sorted(Path(source["directory"]).glob(source["filename_glob"]))
        if start <= calibration_date(path) < end
    ]


def load_calibration_quotes(
    paths: Iterable[Path], config: Mapping[str, Any]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    source = config["calibration_source"]
    frames: list[pd.DataFrame] = []
    records: list[dict[str, Any]] = []
    columns = [
        "tick_time_msc",
        "seconds_since_tick",
        "tick_fresh",
        "account",
        "server",
        "symbol",
        "bid",
        "ask",
        "spread_price",
        "is_rollover_window",
    ]
    for path in sorted(Path(value) for value in paths):
        frame = pd.read_csv(path, usecols=columns)
        record = file_record(path)
        record["source_date_utc"] = calibration_date(path).strftime("%Y-%m-%d")
        record["raw_rows"] = int(len(frame))
        records.append(record)
        if frame.empty:
            continue
        if not frame["account"].eq(int(source["account_login"])).all():
            raise ValueError(f"V49 calibration account mismatch: {path}")
        if not frame["server"].eq(source["account_server"]).all():
            raise ValueError(f"V49 calibration server mismatch: {path}")
        if not frame["symbol"].eq(source["symbol"]).all():
            raise ValueError(f"V49 calibration symbol mismatch: {path}")
        fresh = frame["tick_fresh"].astype(str).str.lower().eq("true")
        rollover = frame["is_rollover_window"].astype(str).str.lower().eq("true")
        numeric = ("tick_time_msc", "seconds_since_tick", "bid", "ask", "spread_price")
        for column in numeric:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[list(numeric)].isna().any().any():
            raise ValueError(f"V49 calibration numeric parse failure: {path}")
        frame = frame.loc[
            fresh
            & frame["seconds_since_tick"].le(int(source["maximum_seconds_since_tick"]))
            & ~rollover
        ].copy()
        frame["tick_time_msc"] = frame["tick_time_msc"].astype(np.int64)
        if bool(
            np.any(
                (frame["bid"].to_numpy() <= 0)
                | (frame["ask"].to_numpy() < frame["bid"].to_numpy())
            )
        ):
            raise ValueError(f"V49 calibration has invalid quotes: {path}")
        frames.append(frame[["tick_time_msc", "bid", "ask", "spread_price"]])
    if not frames:
        return pd.DataFrame(
            columns=["tick_time_msc", "bid", "ask", "spread_price"]
        ), records
    quotes = (
        pd.concat(frames, ignore_index=True)
        .sort_values("tick_time_msc", kind="mergesort")
        .drop_duplicates("tick_time_msc", keep="last")
        .reset_index(drop=True)
    )
    return quotes, records


def resample_quotes(quotes: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    if quotes.empty:
        return pd.DataFrame(
            columns=[
                "tick_time_msc",
                "source_time_msc",
                "quote_age_ms",
                "bid",
                "ask",
                "mid",
                "spread_price",
                "date_utc",
            ]
        )
    sampling = config["sampling"]
    interval = int(sampling["interval_ms"])
    times = quotes["tick_time_msc"].to_numpy(dtype=np.int64)
    first = int(((times[0] + interval - 1) // interval) * interval)
    last = int((times[-1] // interval) * interval)
    boundaries = np.arange(first, last + 1, interval, dtype=np.int64)
    indexes = np.searchsorted(times, boundaries, side="right") - 1
    valid = indexes >= 0
    safe = np.maximum(indexes, 0)
    ages = boundaries - times[safe]
    valid &= (ages >= 0) & (ages <= int(sampling["maximum_quote_age_ms"]))
    boundaries = boundaries[valid]
    indexes = indexes[valid]
    ages = ages[valid]
    bid = quotes["bid"].to_numpy(dtype=float)[indexes]
    ask = quotes["ask"].to_numpy(dtype=float)[indexes]
    spread = quotes["spread_price"].to_numpy(dtype=float)[indexes]
    timestamps = pd.to_datetime(boundaries, unit="ms", utc=True)
    return pd.DataFrame(
        {
            "tick_time_msc": boundaries,
            "source_time_msc": times[indexes],
            "quote_age_ms": ages,
            "bid": bid,
            "ask": ask,
            "mid": (bid + ask) / 2.0,
            "spread_price": spread,
            "date_utc": timestamps.strftime("%Y-%m-%d"),
        }
    )


def policy_grid(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    grid = config["grid"]
    policies: list[dict[str, Any]] = []
    for impulse in grid["impulse_scale_multiples"]:
        for retracement in grid["maximum_retracement_fractions"]:
            for resume in grid["minimum_resume_scale_multiples"]:
                for cooldown in grid["cooldown_minutes"]:
                    policies.append(
                        {
                            "policy_id": f"I{int(impulse * 10):03d}__R{int(retracement * 100):02d}__S{int(resume * 10):02d}__C{int(cooldown):02d}",
                            "impulse_scale_multiple": float(impulse),
                            "maximum_retracement_fraction": float(retracement),
                            "minimum_resume_scale_multiple": float(resume),
                            "cooldown_minutes": int(cooldown),
                        }
                    )
    return policies


def build_features(bars: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    feature = config["feature"]
    frame = bars.sort_values("tick_time_msc", kind="mergesort").copy()
    changes = frame["mid"].diff().abs()
    frame["scale_dollars"] = (
        changes.shift(int(feature["baseline_shift_samples"]))
        .rolling(
            int(feature["baseline_samples"]),
            min_periods=int(feature["baseline_minimum_samples"]),
        )
        .quantile(float(feature["baseline_quantile"]))
        .clip(lower=float(feature["minimum_scale_dollars"]))
    )
    impulse_start = frame["mid"].shift(int(feature["impulse_start_lag_samples"]))
    impulse_end = frame["mid"].shift(int(feature["impulse_end_lag_samples"]))
    pullback_end = frame["mid"].shift(int(feature["pullback_end_lag_samples"]))
    frame["impulse_dollars"] = impulse_end - impulse_start
    frame["pullback_dollars"] = pullback_end - impulse_end
    frame["resume_dollars"] = frame["mid"] - pullback_end
    frame["retracement_fraction"] = np.divide(
        frame["pullback_dollars"].abs(),
        frame["impulse_dollars"].abs(),
        out=np.full(len(frame), np.nan),
        where=frame["impulse_dollars"].abs().to_numpy() > 0,
    )
    frame["impulse_side"] = np.sign(frame["impulse_dollars"])
    frame["spread_baseline_dollars"] = (
        frame["spread_price"]
        .shift(int(feature["spread_baseline_shift_samples"]))
        .rolling(
            int(feature["spread_baseline_samples"]),
            min_periods=int(feature["spread_baseline_minimum_samples"]),
        )
        .median()
    )
    frame["spread_ratio_to_baseline"] = np.divide(
        frame["spread_price"],
        frame["spread_baseline_dollars"],
        out=np.full(len(frame), np.nan),
        where=frame["spread_baseline_dollars"].to_numpy() > 0,
    )
    frame["pullback_opposes"] = (
        np.sign(frame["pullback_dollars"]) == -frame["impulse_side"]
    )
    frame["resume_aligns"] = np.sign(frame["resume_dollars"]) == frame["impulse_side"]
    return frame


def generate_candidates(
    features: pd.DataFrame, policy: Mapping[str, Any], config: Mapping[str, Any]
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)
    feature = config["feature"]
    gate = (
        features["scale_dollars"].notna()
        & features["impulse_side"].ne(0)
        & features["pullback_opposes"]
        & features["resume_aligns"]
        & features["impulse_dollars"]
        .abs()
        .ge(float(policy["impulse_scale_multiple"]) * features["scale_dollars"])
        & features["retracement_fraction"].ge(
            float(feature["minimum_retracement_fraction"])
        )
        & features["retracement_fraction"].le(
            float(policy["maximum_retracement_fraction"])
        )
        & features["resume_dollars"]
        .abs()
        .ge(float(policy["minimum_resume_scale_multiple"]) * features["scale_dollars"])
        & features["spread_baseline_dollars"].notna()
        & features["spread_ratio_to_baseline"].le(
            float(feature["maximum_spread_to_baseline_ratio"])
        )
        & features["spread_price"].le(float(feature["maximum_absolute_spread_dollars"]))
    )
    contiguous = (
        features["tick_time_msc"].diff().eq(int(config["sampling"]["interval_ms"]))
    )
    rising = gate & ~(gate.shift(1, fill_value=False) & contiguous)
    raw = features.loc[rising].copy()
    cooldown_ms = int(policy["cooldown_minutes"]) * 60 * 1000
    kept: list[int] = []
    last = -(10**30)
    for index, timestamp in zip(raw.index, raw["tick_time_msc"], strict=True):
        if int(timestamp) - last >= cooldown_ms:
            kept.append(index)
            last = int(timestamp)
    selected = raw.loc[kept].copy()
    if selected.empty:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)
    timestamps = pd.to_datetime(selected["tick_time_msc"], unit="ms", utc=True)
    block_ms = 4 * 60 * 60 * 1000
    selected["timestamp_utc"] = timestamps.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    selected["date_utc"] = timestamps.dt.strftime("%Y-%m-%d")
    selected["utc_block_start_ms"] = (
        selected["tick_time_msc"].astype(np.int64) // block_ms
    ) * block_ms
    selected["signed_update_imbalance"] = selected["impulse_side"].astype(float)
    selected["displacement_price"] = (
        selected["impulse_dollars"]
        + selected["pullback_dollars"]
        + selected["resume_dollars"]
    )
    selected["candidate_side"] = np.where(
        selected["impulse_side"].gt(0), "LONG", "SHORT"
    )
    return selected.loc[:, CANDIDATE_COLUMNS].reset_index(drop=True)


def eligible_calibration_dates(
    bars: pd.DataFrame, config: Mapping[str, Any]
) -> list[str]:
    minimum = int(config["sampling"]["minimum_samples_per_calibration_weekday"])
    counts = bars.groupby("date_utc").size()
    return [
        date
        for date, count in counts.items()
        if pd.Timestamp(date).weekday() < 5 and int(count) >= minimum
    ]


def policy_metrics(
    candidates: pd.DataFrame, eligible_dates: list[str]
) -> dict[str, Any]:
    dates = pd.DataFrame({"date_utc": eligible_dates})
    daily = candidates.groupby("date_utc").size().rename("candidates").reset_index()
    daily = dates.merge(daily, on="date_utc", how="left")
    daily["candidates"] = daily["candidates"].fillna(0).astype(int)
    midpoint = len(daily) // 2
    first = daily.iloc[:midpoint]
    second = daily.iloc[midpoint:]
    long_count = int(candidates["candidate_side"].eq("LONG").sum())
    short_count = int(candidates["candidate_side"].eq("SHORT").sum())
    total = int(len(candidates))
    return {
        "candidates": total,
        "eligible_weekdays": int(len(daily)),
        "candidates_per_weekday": float(total / len(daily)) if len(daily) else 0.0,
        "active_day_share": float(daily["candidates"].gt(0).mean())
        if len(daily)
        else 0.0,
        "long_candidates": long_count,
        "short_candidates": short_count,
        "minority_direction_share": float(min(long_count, short_count) / total)
        if total
        else 0.0,
        "first_half_candidates_per_weekday": float(first["candidates"].mean())
        if len(first)
        else 0.0,
        "second_half_candidates_per_weekday": float(second["candidates"].mean())
        if len(second)
        else 0.0,
    }


def select_policy(
    grid: pd.DataFrame, config: Mapping[str, Any]
) -> dict[str, Any] | None:
    selection = config["calibration_selection"]
    eligible = grid.loc[
        grid["candidates_per_weekday"].between(
            float(selection["minimum_candidates_per_weekday"]),
            float(selection["maximum_candidates_per_weekday"]),
        )
        & grid["active_day_share"].ge(float(selection["minimum_active_day_share"]))
        & grid["minority_direction_share"].ge(
            float(selection["minimum_direction_share"])
        )
        & grid["first_half_candidates_per_weekday"].between(
            float(selection["minimum_half_candidates_per_weekday"]),
            float(selection["maximum_half_candidates_per_weekday"]),
        )
        & grid["second_half_candidates_per_weekday"].between(
            float(selection["minimum_half_candidates_per_weekday"]),
            float(selection["maximum_half_candidates_per_weekday"]),
        )
    ].copy()
    if eligible.empty:
        return None
    eligible["density_distance"] = (
        eligible["candidates_per_weekday"]
        - float(selection["target_candidates_per_weekday"])
    ).abs()
    ordered = eligible.sort_values(
        [
            "density_distance",
            "impulse_scale_multiple",
            "minimum_resume_scale_multiple",
            "maximum_retracement_fraction",
            "cooldown_minutes",
            "policy_id",
        ],
        ascending=[True, False, False, True, False, True],
        kind="mergesort",
    )
    return ordered.iloc[0].to_dict()


def frozen_v24_root(config: Mapping[str, Any]) -> Path:
    return (ROOT / str(config["frozen_v24_1"]["root_relative"])).resolve()


def load_locked_v24(config: Mapping[str, Any]) -> ModuleType:
    frozen = config["frozen_v24_1"]
    dependency_root = frozen_v24_root(config)
    for relative, expected in (
        (frozen["config_relative"], frozen["config_file_sha256"]),
        (frozen["module_relative"], frozen["module_file_sha256"]),
        (frozen["contract_relative"], frozen["contract_file_sha256"]),
    ):
        path = dependency_root / str(relative)
        if not path.is_file() or sha256_file(path) != str(expected):
            raise ValueError(f"V49 frozen V24.1 dependency changed: {path}")
    contract = json.loads(
        (dependency_root / str(frozen["contract_relative"])).read_text(encoding="utf-8")
    )
    if contract["contract_sha256"] != frozen["contract_sha256"]:
        raise ValueError("V49 frozen V24.1 contract identity changed")
    module_path = dependency_root / str(frozen["module_relative"])
    spec = importlib.util.spec_from_file_location(
        "v49_locked_v24_microburst", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def adjusted_stage_audit(
    trades: pd.DataFrame,
    stage_dates: list[str],
    partition: str,
    config: Mapping[str, Any],
    v24: ModuleType,
) -> tuple[dict[str, Any], pd.DataFrame]:
    audit, daily = v24.evaluate_stage(trades, stage_dates, partition, config)
    multiple = config["multiple_testing"]
    values = daily.sort_values("date_utc")["base_pnl_dollars"].to_numpy(dtype=float)
    block = int(multiple["block_length_weekdays"])
    observed = float(values.mean())
    centered = values - observed
    rng = np.random.default_rng(int(multiple["daily_bootstrap_seed"]))
    samples = int(multiple["daily_bootstrap_samples"])
    blocks = int(np.ceil(len(values) / block))
    starts = rng.integers(0, len(values), size=(samples, blocks))
    indexes = (starts[..., None] + np.arange(block)) % len(values)
    boot = centered[indexes].reshape(samples, -1)[:, : len(values)].mean(axis=1)
    pvalue = float((1 + np.count_nonzero(boot >= observed)) / (samples + 1))
    passed = pvalue <= float(multiple["maximum_one_sided_pvalue"])
    audit["metrics"]["selection_adjusted_daily_block_bootstrap_pvalue"] = pvalue
    audit["gate_checks"]["selection_adjusted_daily_block_bootstrap_pvalue"] = passed
    audit["gate_passed"] = bool(audit["gate_passed"] and passed)
    audit["registered_capital_forward_hypotheses"] = int(
        multiple["registered_capital_forward_hypotheses"]
    )
    audit["bonferroni_stage_alpha"] = float(multiple["maximum_one_sided_pvalue"])
    return audit, daily
