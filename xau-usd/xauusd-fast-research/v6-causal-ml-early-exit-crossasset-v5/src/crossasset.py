from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.metrics import mean_pinball_loss


REPO_ROOT = Path(__file__).resolve().parents[4]
LANE_ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def verify_sources(config: Mapping[str, Any]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, source in config["sources"].items():
        path = resolve_path(source["path"])
        if not path.is_file():
            raise FileNotFoundError(f"Missing locked source {name}: {path}")
        actual = sha256_file(path)
        if actual != source["sha256"]:
            raise ValueError(
                f"Locked source drift for {name}: "
                f"expected {source['sha256']}, got {actual}"
            )
        observed[name] = actual
    return observed


def _verify_named_paths(
    expected_sources: Mapping[str, tuple[Path, str]],
) -> dict[str, dict[str, str]]:
    text_suffixes = {
        ".csv",
        ".json",
        ".md",
        ".py",
        ".txt",
        ".toml",
        ".yaml",
        ".yml",
    }
    observed: dict[str, dict[str, str]] = {}
    for name, (path, expected) in expected_sources.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing locked dependency {name}: {path}")
        payload = path.read_bytes()
        actual = hashlib.sha256(payload).hexdigest()
        mode = "exact_bytes"
        if actual != expected:
            normalized = payload.replace(b"\r\n", b"\n")
            normalized_hash = hashlib.sha256(normalized).hexdigest()
            if path.suffix.lower() not in text_suffixes or normalized_hash != expected:
                raise ValueError(
                    f"Locked dependency drift for {name}: "
                    f"expected {expected}, got {actual}"
                )
            mode = "crlf_to_lf"
        observed[name] = {
            "expected_sha256": expected,
            "observed_sha256": actual,
            "match_mode": mode,
        }
    return observed


def verify_dependency_sources(
    config: Mapping[str, Any],
    resolver=resolve_path,
) -> dict[str, dict[str, str]]:
    expected = {
        name: (resolver(source["path"]), source["sha256"])
        for name, source in config["sources"].items()
    }
    return _verify_named_paths(expected)


def verify_reproduction_sources(
    config: Mapping[str, Any],
    reproduction: ModuleType,
) -> dict[str, dict[str, str]]:
    expected: dict[str, tuple[Path, str]] = {}
    package = config["external_package"]
    package_root = reproduction.resolve_external_root(package["root"])
    for name, item in package["sources"].items():
        expected[f"external_package.{name}"] = (
            package_root / item["path"],
            item["sha256"],
        )
    for name, item in config["external_data"].items():
        expected[f"external_data.{name}"] = (
            Path(item["path"]),
            item["sha256"],
        )
    for name, item in config["canonical_v60"].items():
        expected[f"canonical_v60.{name}"] = (
            reproduction.resolve_repo_path(item["path"]),
            item["sha256"],
        )
    return _verify_named_paths(expected)


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_frozen_v4_policy(
    config: Mapping[str, Any], v4_config: Mapping[str, Any]
) -> None:
    for section in ("model", "action_policy", "walk_forward", "windows", "gates"):
        if config[section] != v4_config[section]:
            raise ValueError(f"V5 changed frozen V4 section: {section}")


def _validated_price_frame(
    timestamp: pd.Series,
    price: pd.Series,
    available: pd.Series,
    source_name: str,
) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamp, utc=True),
            "price": pd.to_numeric(price, errors="raise").astype(float),
            "available": available.astype(bool).to_numpy(),
        }
    )
    if frame["timestamp"].isna().any():
        raise ValueError(f"{source_name} contains invalid timestamps")
    if frame["timestamp"].duplicated().any():
        raise ValueError(f"{source_name} contains duplicate timestamps")
    if not frame["timestamp"].is_monotonic_increasing:
        raise ValueError(f"{source_name} timestamps are not sorted")
    valid_price = frame.loc[frame["available"], "price"]
    if (
        valid_price.empty
        or not np.isfinite(valid_price.to_numpy(dtype=float)).all()
        or valid_price.le(0.0).any()
    ):
        raise ValueError(f"{source_name} contains invalid available prices")
    return frame


def load_cross_asset_sources(
    config: Mapping[str, Any],
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    macro = pd.read_parquet(
        resolve_path(config["sources"]["dxy_treasury"]["path"]),
        columns=[
            "timestamp_utc",
            "dollaridxusd_mid_close",
            "ustbondtrusd_mid_close",
            "dollaridxusd_available",
            "ustbondtrusd_available",
        ],
    )
    sources = {
        "dxy": _validated_price_frame(
            macro["timestamp_utc"],
            macro["dollaridxusd_mid_close"],
            macro["dollaridxusd_available"],
            "dxy",
        ),
        "treasury": _validated_price_frame(
            macro["timestamp_utc"],
            macro["ustbondtrusd_mid_close"],
            macro["ustbondtrusd_available"],
            "treasury",
        ),
    }
    for name in ("eurusd", "gbpusd", "usdjpy"):
        raw = pd.read_parquet(
            resolve_path(config["sources"][name]["path"]),
            columns=["timestamp_ms", "bid_close", "ask_close"],
        )
        mid = (
            pd.to_numeric(raw["bid_close"], errors="raise")
            + pd.to_numeric(raw["ask_close"], errors="raise")
        ) / 2.0
        sources[name] = _validated_price_frame(
            pd.to_datetime(raw["timestamp_ms"], unit="ms", utc=True),
            mid,
            pd.Series(True, index=raw.index),
            name,
        )
    audit = {
        name: {
            "rows": int(len(frame)),
            "first_bar_utc": frame["timestamp"].min().isoformat(),
            "last_bar_utc": frame["timestamp"].max().isoformat(),
            "available_share": float(frame["available"].mean()),
        }
        for name, frame in sources.items()
    }
    return sources, audit


def causal_log_return(
    decision_times: pd.Series,
    source: pd.DataFrame,
    horizon_minutes: int,
    bar_minutes: int,
    maximum_staleness_minutes: int,
) -> pd.DataFrame:
    decisions = pd.to_datetime(decision_times, utc=True)
    decision_ns = (
        decisions.dt.tz_convert(None)
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
    )
    source_ns = (
        pd.to_datetime(source["timestamp"], utc=True)
        .dt.tz_convert(None)
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
    )
    price = source["price"].to_numpy(dtype=float)
    available = source["available"].to_numpy(dtype=bool)
    minute_ns = 60 * 1_000_000_000
    completed_cutoff = decision_ns - int(bar_minutes) * minute_ns
    past_cutoff = completed_cutoff - int(horizon_minutes) * minute_ns

    current_index = np.searchsorted(source_ns, completed_cutoff, side="right") - 1
    past_index = np.searchsorted(source_ns, past_cutoff, side="right") - 1
    safe_current = np.clip(current_index, 0, len(source_ns) - 1)
    safe_past = np.clip(past_index, 0, len(source_ns) - 1)
    current_age = (completed_cutoff - source_ns[safe_current]) / minute_ns
    past_age = (past_cutoff - source_ns[safe_past]) / minute_ns
    valid = (
        (current_index >= 0)
        & (past_index >= 0)
        & (current_age >= 0.0)
        & (past_age >= 0.0)
        & (current_age <= float(maximum_staleness_minutes))
        & (past_age <= float(maximum_staleness_minutes))
        & available[safe_current]
        & available[safe_past]
        & np.isfinite(price[safe_current])
        & np.isfinite(price[safe_past])
        & (price[safe_current] > 0.0)
        & (price[safe_past] > 0.0)
    )
    values = np.zeros(len(decisions), dtype=float)
    values[valid] = np.log(
        price[safe_current[valid]] / price[safe_past[valid]]
    )
    unavailable_age = float(maximum_staleness_minutes + bar_minutes)
    staleness = np.where(
        (current_index >= 0)
        & (current_age >= 0.0)
        & (current_age <= float(maximum_staleness_minutes))
        & available[safe_current],
        current_age,
        unavailable_age,
    )
    return pd.DataFrame(
        {
            "return": values,
            "available": valid.astype(float),
            "staleness_minutes": staleness.astype(float),
        },
        index=decision_times.index,
    )


def attach_cross_asset_features(
    snapshots: pd.DataFrame,
    sources: Mapping[str, pd.DataFrame],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    if "decision_time" not in snapshots:
        raise ValueError("Snapshots are missing decision_time")
    settings = config["cross_asset"]
    bar_minutes = int(settings["bar_minutes"])
    maximum_staleness = int(settings["maximum_staleness_minutes"])
    decision_times = snapshots["decision_time"]
    dxy_1h = causal_log_return(
        decision_times, sources["dxy"], 60, bar_minutes, maximum_staleness
    )
    dxy_4h = causal_log_return(
        decision_times, sources["dxy"], 240, bar_minutes, maximum_staleness
    )
    treasury_1h = causal_log_return(
        decision_times, sources["treasury"], 60, bar_minutes, maximum_staleness
    )
    treasury_4h = causal_log_return(
        decision_times, sources["treasury"], 240, bar_minutes, maximum_staleness
    )
    eurusd_1h = causal_log_return(
        decision_times, sources["eurusd"], 60, bar_minutes, maximum_staleness
    )
    gbpusd_1h = causal_log_return(
        decision_times, sources["gbpusd"], 60, bar_minutes, maximum_staleness
    )
    usdjpy_1h = causal_log_return(
        decision_times, sources["usdjpy"], 60, bar_minutes, maximum_staleness
    )
    common_available = (
        eurusd_1h["available"].astype(bool)
        & gbpusd_1h["available"].astype(bool)
        & usdjpy_1h["available"].astype(bool)
    )
    common_return = (
        -eurusd_1h["return"] - gbpusd_1h["return"] + usdjpy_1h["return"]
    ) / 3.0

    result = snapshots.copy()
    result["dxy_return_1h"] = dxy_1h["return"]
    result["dxy_return_4h"] = dxy_4h["return"]
    result["treasury_return_1h"] = treasury_1h["return"]
    result["treasury_return_4h"] = treasury_4h["return"]
    result["common_dollar_return_1h"] = common_return.where(
        common_available, 0.0
    )
    result["dxy_1h_available"] = dxy_1h["available"]
    result["dxy_4h_available"] = dxy_4h["available"]
    result["treasury_1h_available"] = treasury_1h["available"]
    result["treasury_4h_available"] = treasury_4h["available"]
    result["common_dollar_1h_available"] = common_available.astype(float)
    result["dxy_staleness_minutes"] = dxy_1h["staleness_minutes"]
    result["treasury_staleness_minutes"] = treasury_1h["staleness_minutes"]
    result["common_dollar_max_staleness_minutes"] = pd.concat(
        [
            eurusd_1h["staleness_minutes"],
            gbpusd_1h["staleness_minutes"],
            usdjpy_1h["staleness_minutes"],
        ],
        axis=1,
    ).max(axis=1)
    return result


def build_feature_matrix(
    snapshots: pd.DataFrame,
    v3_config: Mapping[str, Any],
    v3: ModuleType,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    base = v3.build_feature_matrix(snapshots, v3_config)
    names = list(config["cross_asset"]["features"])
    missing = sorted(set(names).difference(snapshots.columns))
    if missing:
        raise ValueError(f"Cross-asset snapshots are missing columns: {missing}")
    extra = snapshots.loc[:, names].apply(pd.to_numeric, errors="raise").astype(float)
    frame = pd.concat([base, extra], axis=1)
    if frame.columns.duplicated().any():
        raise ValueError("Duplicate feature names in V5 feature matrix")
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError("V5 feature matrix contains non-finite values")
    return frame


def annual_cross_asset_predictions(
    training_snapshots: pd.DataFrame,
    target_snapshots: pd.DataFrame,
    config: Mapping[str, Any],
    v3_config: Mapping[str, Any],
    v3: ModuleType,
    v4: ModuleType,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = config["walk_forward"]
    quantile = float(config["model"]["quantile"])
    prediction_frames: list[pd.DataFrame] = []
    logs: list[dict[str, Any]] = []
    for raw_year in settings["target_years"]:
        year = int(raw_year)
        train = v3.annual_training_split(
            training_snapshots, year, float(settings["purge_hours"])
        )
        target = target_snapshots.loc[
            pd.to_datetime(target_snapshots["entry_time"], utc=True).dt.year.eq(year)
        ].copy()
        if len(train) < int(settings["minimum_training_rows"]):
            raise ValueError(f"Insufficient training snapshots for {year}: {len(train)}")
        if target.empty:
            raise ValueError(f"No frozen V1 target snapshots for {year}")
        train_target = v4.benefit_r_target(train)
        target_actual = v4.benefit_r_target(target)
        model = v4.make_model(config)
        model.fit(
            build_feature_matrix(train, v3_config, v3, config),
            train_target,
            sample_weight=v3.decision_day_equal_weights(train),
        )
        score = model.predict(
            build_feature_matrix(target, v3_config, v3, config)
        )
        target["actual_benefit_r"] = target_actual
        target["predicted_lower_benefit_r"] = score
        target["utility_exit_trigger"] = v4.action_mask(target, score, config)
        prediction_frames.append(target)
        first = (
            target.loc[target["utility_exit_trigger"]]
            .sort_values(["source_trade_id", "checkpoint_minutes"], kind="mergesort")
            .drop_duplicates("source_trade_id", keep="first")
        )
        logs.append(
            {
                "target_year": year,
                "training_rows": int(len(train)),
                "training_last_original_exit_time": train[
                    "original_exit_time"
                ].max(),
                "training_target_mean_r": float(train_target.mean()),
                "training_target_q25_r": float(np.quantile(train_target, 0.25)),
                "target_rows": int(len(target)),
                "target_spearman": v4.rank_correlation(target_actual, score),
                "target_pinball_loss": float(
                    mean_pinball_loss(target_actual, score, alpha=quantile)
                ),
                "target_score_mean_r": float(np.mean(score)),
                "target_score_max_r": float(np.max(score)),
                "first_action_trades": int(len(first)),
                "first_action_positive_benefit_share": (
                    float(first["benefit_usd"].gt(0.0).mean())
                    if len(first)
                    else 0.0
                ),
                "first_action_net_benefit_usd": float(first["benefit_usd"].sum()),
                "first_action_worst_benefit_usd": (
                    float(first["benefit_usd"].min()) if len(first) else 0.0
                ),
            }
        )
    predictions = pd.concat(prediction_frames, ignore_index=True).sort_values(
        ["entry_time", "source_trade_id", "checkpoint_minutes"],
        kind="mergesort",
    )
    return predictions.reset_index(drop=True), pd.DataFrame(logs)


def coverage_audit(snapshots: pd.DataFrame) -> dict[str, float]:
    return {
        "dxy_1h_available_share": float(snapshots["dxy_1h_available"].mean()),
        "dxy_4h_available_share": float(snapshots["dxy_4h_available"].mean()),
        "treasury_1h_available_share": float(
            snapshots["treasury_1h_available"].mean()
        ),
        "treasury_4h_available_share": float(
            snapshots["treasury_4h_available"].mean()
        ),
        "common_dollar_1h_available_share": float(
            snapshots["common_dollar_1h_available"].mean()
        ),
    }
