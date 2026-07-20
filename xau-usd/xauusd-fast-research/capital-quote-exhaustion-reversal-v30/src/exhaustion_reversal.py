from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
CANDIDATE_COLUMNS = (
    "timestamp_utc",
    "tick_time_msc",
    "date_utc",
    "utc_block_start_ms",
    "bid",
    "ask",
    "mid",
    "spread_price",
    "impulse_start_time_msc",
    "impulse_arm_time_msc",
    "impulse_side",
    "impulse_displacement_price",
    "impulse_update_imbalance",
    "impulse_nonzero_updates",
    "extreme_price",
    "retracement_price",
    "consecutive_counter_updates",
    "candidate_side",
)


def load_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / "config" / "capital_quote_exhaustion_reversal_v30.json"
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
        work,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


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
            raise ValueError(f"V30 frozen V24.1 dependency changed: {path}")
    contract = json.loads(
        (dependency_root / str(frozen["contract_relative"])).read_text(encoding="utf-8")
    )
    if str(contract["contract_sha256"]) != str(frozen["contract_sha256"]):
        raise ValueError("V30 frozen V24.1 contract identity changed")
    module_path = dependency_root / str(frozen["module_relative"])
    spec = importlib.util.spec_from_file_location("v30_locked_v24", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def development_source_paths(config: Mapping[str, Any]) -> list[Path]:
    source = config["development_source"]
    directory = (ROOT / str(source["directory"])).resolve()
    return sorted(directory.glob(str(source["filename_glob"])))


def _parse_development_file(path: Path, config: Mapping[str, Any]) -> pd.DataFrame:
    columns = (
        "dataset_version",
        "account_scope",
        "account_label",
        "symbol",
        "time_utc",
        "time_msc",
        "bid",
        "ask",
        "spread_price",
    )
    frame = pd.read_csv(path, usecols=list(columns))
    if frame.empty:
        return frame
    source = config["development_source"]
    checks = (
        frame["dataset_version"].eq(source["dataset_version"]).all(),
        frame["account_scope"].eq(int(source["account_scope"])).all(),
        frame["account_label"].eq(source["account_label"]).all(),
        frame["symbol"].eq(source["symbol"]).all(),
    )
    if not all(checks):
        raise ValueError(f"V30 development identity mismatch: {path}")
    parsed = pd.to_datetime(frame["time_utc"], utc=True, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"V30 invalid development timestamp: {path}")
    frame = frame.rename(columns={"time_msc": "tick_time_msc"})
    for column in ("tick_time_msc", "bid", "ask", "spread_price"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[["tick_time_msc", "bid", "ask", "spread_price"]].isna().any().any():
        raise ValueError(f"V30 invalid development numeric value: {path}")
    frame["tick_time_msc"] = frame["tick_time_msc"].astype(np.int64)
    parsed_ms = parsed.array.as_unit("ms").asi8.astype(np.int64, copy=False)
    maximum_disagreement = int(
        config["data_quality"]["maximum_timestamp_disagreement_ms"]
    )
    if bool(np.any(np.abs(parsed_ms - frame["tick_time_msc"]) > maximum_disagreement)):
        raise ValueError(f"V30 development timestamp disagreement: {path}")
    spread_error = np.abs(
        (frame["ask"].to_numpy(float) - frame["bid"].to_numpy(float))
        - frame["spread_price"].to_numpy(float)
    )
    if bool(
        np.any(
            spread_error > float(config["data_quality"]["maximum_spread_field_error"])
        )
    ):
        raise ValueError(f"V30 development spread mismatch: {path}")
    return frame.loc[:, ["tick_time_msc", "bid", "ask", "spread_price"]]


def load_development_ticks(
    paths: Iterable[Path], config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    records: list[dict[str, Any]] = []
    raw_daily_records: list[dict[str, Any]] = []
    for path in sorted(Path(value) for value in paths):
        frame = _parse_development_file(path, config)
        records.append(
            {
                "path": str(path.resolve()).replace("\\", "/"),
                "bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
                "raw_rows": int(len(frame)),
            }
        )
        if frame.empty:
            continue
        date_utc = pd.Timestamp(
            int(frame["tick_time_msc"].iloc[0]), unit="ms", tz="UTC"
        ).strftime("%Y-%m-%d")
        raw_daily_records.append(
            {
                "date_utc": date_utc,
                "raw_rows": int(len(frame)),
                "unique_milliseconds": int(frame["tick_time_msc"].nunique()),
            }
        )
        frames.append(frame)
    if not frames:
        return (
            pd.DataFrame(),
            {"source_files": records, "raw_rows": 0, "unique_rows": 0},
            pd.DataFrame(),
        )
    raw = pd.concat(frames, ignore_index=True)
    ticks = (
        raw.drop_duplicates("tick_time_msc", keep="last")
        .sort_values("tick_time_msc", kind="mergesort")
        .reset_index(drop=True)
    )
    ticks["timestamp_utc"] = pd.to_datetime(
        ticks["tick_time_msc"], unit="ms", utc=True
    ).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    ticks["date_utc"] = pd.to_datetime(
        ticks["tick_time_msc"], unit="ms", utc=True
    ).dt.strftime("%Y-%m-%d")
    raw_daily = pd.DataFrame(raw_daily_records)
    if not raw_daily.empty:
        raw_daily = raw_daily.groupby("date_utc", as_index=False).sum()
        raw_daily["duplicate_millisecond_rows"] = (
            raw_daily["raw_rows"] - raw_daily["unique_milliseconds"]
        )
        raw_daily["duplicate_millisecond_share"] = (
            raw_daily["duplicate_millisecond_rows"] / raw_daily["raw_rows"]
        )
    audit = {
        "source_files": records,
        "raw_rows": int(len(raw)),
        "unique_rows": int(len(ticks)),
        "duplicate_millisecond_rows": int(len(raw) - len(ticks)),
        "daily_source_quality": raw_daily.to_dict(orient="records"),
    }
    return ticks, audit, raw_daily


def generate_candidates(
    ticks: pd.DataFrame, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if ticks.empty:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS), {
            "impulse_arm_count": 0,
            "raw_trigger_count": 0,
        }
    feature = config["feature"]
    times = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
    bid = ticks["bid"].to_numpy(dtype=float)
    ask = ticks["ask"].to_numpy(dtype=float)
    spread = ticks["spread_price"].to_numpy(dtype=float)
    mid = (bid + ask) / 2.0
    target = times - int(feature["lookback_ms"])
    starts = np.searchsorted(times, target, side="right") - 1
    valid_start = starts >= 0
    safe_starts = np.maximum(starts, 0)
    boundary_age = target - times[safe_starts]
    delta = np.diff(mid, prepend=mid[0])
    signs = np.sign(delta)
    nonzero = signs != 0
    signed_prefix = np.concatenate(([0.0], np.cumsum(signs)))
    count_prefix = np.concatenate(([0], np.cumsum(nonzero.astype(np.int64))))
    index = np.arange(len(times), dtype=np.int64)
    update_sum = signed_prefix[index + 1] - signed_prefix[safe_starts + 1]
    update_count = count_prefix[index + 1] - count_prefix[safe_starts + 1]
    imbalance = np.divide(
        update_sum,
        update_count,
        out=np.zeros(len(times), dtype=float),
        where=update_count > 0,
    )
    displacement = mid - mid[safe_starts]
    gaps = np.diff(times, prepend=times[0])
    v24 = load_locked_v24(config)
    maximum_internal_gap = v24._rolling_internal_max_gap(gaps, safe_starts)
    impulse_gate = (
        valid_start
        & (boundary_age >= 0)
        & (boundary_age <= int(feature["maximum_boundary_quote_age_ms"]))
        & (maximum_internal_gap <= int(feature["maximum_internal_quote_gap_ms"]))
        & (spread <= float(feature["maximum_spread_price"]))
        & (update_count >= int(feature["minimum_nonzero_mid_updates"]))
        & (np.abs(imbalance) >= float(feature["minimum_absolute_update_imbalance"]))
        & (
            np.abs(displacement)
            >= float(feature["minimum_absolute_displacement_price"])
        )
        & (np.sign(imbalance) == np.sign(displacement))
        & (np.sign(displacement) != 0)
    )
    block_ms = int(config["episode"]["utc_block_hours"]) * 60 * 60 * 1000
    expiry_ms = int(feature["arm_expiry_ms"])
    retracement_required = float(feature["minimum_retracement_price"])
    counter_required = int(feature["minimum_consecutive_counter_updates"])
    refractory_ms = int(feature["post_trigger_refractory_ms"])
    armed: dict[str, Any] | None = None
    refractory_until = -1
    arms = 0
    records: list[dict[str, Any]] = []
    for i in range(len(times)):
        now = int(times[i])
        if armed is not None:
            if now - int(armed["arm_time"]) > expiry_ms:
                armed = None
            else:
                impulse_side = int(armed["impulse_side"])
                move = float(delta[i])
                if impulse_side > 0:
                    if mid[i] > float(armed["extreme"]):
                        armed["extreme"] = float(mid[i])
                        armed["counter"] = 0
                    elif move < 0:
                        armed["counter"] = int(armed["counter"]) + 1
                    elif move > 0:
                        armed["counter"] = 0
                    retracement = float(armed["extreme"]) - float(mid[i])
                    candidate_side = "SHORT"
                else:
                    if mid[i] < float(armed["extreme"]):
                        armed["extreme"] = float(mid[i])
                        armed["counter"] = 0
                    elif move > 0:
                        armed["counter"] = int(armed["counter"]) + 1
                    elif move < 0:
                        armed["counter"] = 0
                    retracement = float(mid[i]) - float(armed["extreme"])
                    candidate_side = "LONG"
                if (
                    retracement >= retracement_required
                    and int(armed["counter"]) >= counter_required
                    and spread[i] <= float(feature["maximum_spread_price"])
                ):
                    timestamp = pd.Timestamp(now, unit="ms", tz="UTC")
                    records.append(
                        {
                            "timestamp_utc": timestamp.strftime(
                                "%Y-%m-%dT%H:%M:%S.%fZ"
                            ),
                            "tick_time_msc": now,
                            "date_utc": timestamp.strftime("%Y-%m-%d"),
                            "utc_block_start_ms": int((now // block_ms) * block_ms),
                            "bid": float(bid[i]),
                            "ask": float(ask[i]),
                            "mid": float(mid[i]),
                            "spread_price": float(spread[i]),
                            "impulse_start_time_msc": int(armed["start_time"]),
                            "impulse_arm_time_msc": int(armed["arm_time"]),
                            "impulse_side": "UP" if impulse_side > 0 else "DOWN",
                            "impulse_displacement_price": float(armed["displacement"]),
                            "impulse_update_imbalance": float(armed["imbalance"]),
                            "impulse_nonzero_updates": int(armed["updates"]),
                            "extreme_price": float(armed["extreme"]),
                            "retracement_price": retracement,
                            "consecutive_counter_updates": int(armed["counter"]),
                            "candidate_side": candidate_side,
                        }
                    )
                    armed = None
                    refractory_until = now + refractory_ms
        if armed is None and now >= refractory_until and bool(impulse_gate[i]):
            impulse_side = 1 if displacement[i] > 0 else -1
            armed = {
                "impulse_side": impulse_side,
                "start_time": int(times[safe_starts[i]]),
                "arm_time": now,
                "extreme": float(mid[i]),
                "counter": 0,
                "displacement": float(displacement[i]),
                "imbalance": float(imbalance[i]),
                "updates": int(update_count[i]),
            }
            arms += 1
    raw_count = len(records)
    candidates = pd.DataFrame(records, columns=CANDIDATE_COLUMNS)
    if not candidates.empty:
        candidates = (
            candidates.sort_values("tick_time_msc", kind="mergesort")
            .drop_duplicates("utc_block_start_ms", keep="first")
            .reset_index(drop=True)
        )
        maximum = int(config["episode"]["maximum_candidates_per_utc_day"])
        if int(candidates.groupby("date_utc").size().max()) > maximum:
            raise ValueError("V30 candidate count exceeded its daily structural cap")
    return candidates, {
        "impulse_arm_count": int(arms),
        "raw_trigger_count": int(raw_count),
    }


def selection_adjusted_evaluation(
    trades: pd.DataFrame,
    stage_dates: list[str],
    partition: str,
    config: Mapping[str, Any],
    v24: ModuleType,
) -> tuple[dict[str, Any], pd.DataFrame]:
    audit, daily = v24.evaluate_stage(trades, stage_dates, partition, config)
    multiple = config["multiple_testing"]
    values = daily.sort_values("date_utc")["base_pnl_dollars"].to_numpy(float)
    block_length = int(multiple["block_length_weekdays"])
    observed_mean = float(values.mean())
    centered = values - observed_mean
    rng = np.random.default_rng(int(multiple["daily_bootstrap_seed"]))
    sample_count = int(multiple["daily_bootstrap_samples"])
    block_count = int(np.ceil(len(values) / block_length))
    starts = rng.integers(0, len(values), size=(sample_count, block_count))
    offsets = np.arange(block_length, dtype=np.int64)
    indexes = (starts[..., None] + offsets) % len(values)
    bootstrap = (
        centered[indexes].reshape(sample_count, -1)[:, : len(values)].mean(axis=1)
    )
    pvalue = float(
        (1 + int(np.count_nonzero(bootstrap >= observed_mean))) / (sample_count + 1)
    )
    passed = pvalue <= float(multiple["maximum_one_sided_pvalue"])
    audit["schema_version"] = "xauusd_v30_forward_stage_audit"
    audit["metrics"]["selection_adjusted_daily_block_bootstrap_pvalue"] = pvalue
    audit["gate_checks"]["selection_adjusted_daily_block_bootstrap_pvalue"] = passed
    audit["gate_passed"] = bool(audit["gate_passed"] and passed)
    audit["registered_capital_forward_hypotheses"] = int(
        multiple["registered_capital_forward_hypotheses"]
    )
    audit["bonferroni_stage_alpha"] = float(multiple["maximum_one_sided_pvalue"])
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    return audit, daily
