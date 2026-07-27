from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_causal import oracle_match
from .neutral_walkforward import (
    FEATURE_COLUMNS,
    _admitted,
    _period,
    _summary,
    build_labeled_dataset,
    route_outcomes,
    select_development_threshold,
    walk_forward_predictions,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    serialize,
    sha256_file,
)


MICRO_COLUMNS = [
    "aligned_quote_change_imbalance",
    "aligned_three_bar_quote_change_imbalance",
    "aligned_path_efficiency",
    "aligned_late_return_pips",
    "volume_imbalance",
    "spread_mean_pips",
    "spread_std_pips",
    "spread_max_pips",
    "spread_last_pips",
    "realized_variance_pips2",
    "late_tick_share",
    "tick_count_ratio_24",
]
MODEL_FEATURE_COLUMNS = FEATURE_COLUMNS + MICRO_COLUMNS
CACHE_VERSION = "v1"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_tick_microstructure.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_TICK_MICROSTRUCTURE_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_tick_microstructure_outcome_inspection")
        is not True
    ):
        raise RuntimeError("Neutral tick-microstructure contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral tick-microstructure preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    return checked


def aggregate_tick_payload(
    payload: dict[str, Any], late_bar_seconds: int = 60
) -> list[dict[str, Any]]:
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    if any(
        key not in payload
        for key in ("timestamp", "multiplier", "bid", "ask", *arrays)
    ):
        raise ValueError("Malformed tick payload")
    lengths = {len(payload[key]) for key in arrays}
    if len(lengths) != 1:
        raise ValueError("Inconsistent tick payload arrays")
    count = len(payload["times"])
    if count == 0:
        return []
    if payload["bid"] is None or payload["ask"] is None:
        raise ValueError("Nonempty tick payload has null base price")
    timestamps = int(payload["timestamp"]) + np.cumsum(
        np.asarray(payload["times"], dtype=np.int64)
    )
    multiplier = float(payload["multiplier"])
    bids = float(payload["bid"]) + np.cumsum(
        np.asarray(payload["bids"], dtype=np.float64)
    ) * multiplier
    asks = float(payload["ask"]) + np.cumsum(
        np.asarray(payload["asks"], dtype=np.float64)
    ) * multiplier
    if np.any(asks < bids):
        raise ValueError("Decoded ask below bid")
    bid_volumes = np.asarray(payload["bidVolumes"], dtype=np.float64)
    ask_volumes = np.asarray(payload["askVolumes"], dtype=np.float64)
    buckets = timestamps // 300_000 * 300_000
    _, starts, counts = np.unique(
        buckets, return_index=True, return_counts=True
    )
    rows = []
    late_ms = int(late_bar_seconds) * 1000
    for start, bucket_count in zip(starts, counts, strict=True):
        stop = int(start + bucket_count)
        bucket = int(buckets[start])
        mid = (bids[start:stop] + asks[start:stop]) / 2.0
        spread_pips = (asks[start:stop] - bids[start:stop]) / PIP
        changes_pips = np.diff(mid) / PIP
        up = int((changes_pips > 0).sum())
        down = int((changes_pips < 0).sum())
        directional = up + down
        quote_imbalance = (
            (up - down) / directional if directional else 0.0
        )
        absolute_path = float(np.abs(changes_pips).sum())
        path_efficiency = (
            float((mid[-1] - mid[0]) / PIP) / absolute_path
            if absolute_path > 0
            else 0.0
        )
        volume_total = float(
            bid_volumes[start:stop].sum()
            + ask_volumes[start:stop].sum()
        )
        volume_imbalance = (
            float(
                bid_volumes[start:stop].sum()
                - ask_volumes[start:stop].sum()
            )
            / volume_total
            if volume_total > 0
            else 0.0
        )
        late_start = bucket + 300_000 - late_ms
        late_offset = int(
            np.searchsorted(
                timestamps[start:stop], late_start, side="left"
            )
        )
        late_mid = mid[min(late_offset, len(mid) - 1)]
        late_count = max(len(mid) - late_offset, 0)
        rows.append(
            {
                "timestamp_ms": bucket,
                "tick_count_raw": int(bucket_count),
                "quote_change_imbalance": quote_imbalance,
                "path_efficiency": path_efficiency,
                "late_return_pips": float(
                    (mid[-1] - late_mid) / PIP
                ),
                "volume_imbalance": volume_imbalance,
                "spread_mean_pips": float(spread_pips.mean()),
                "spread_std_pips": float(spread_pips.std()),
                "spread_max_pips": float(spread_pips.max()),
                "spread_last_pips": float(spread_pips[-1]),
                "realized_variance_pips2": float(
                    np.square(changes_pips).sum()
                ),
                "late_tick_share": float(late_count / len(mid)),
            }
        )
    return rows


def load_tick_microstructure(
    raw_root: Path,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    cache_root = PACKAGE_ROOT / "outputs" / "cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    cache = cache_root / f"EURUSD_M5_MICROSTRUCTURE_{CACHE_VERSION}.parquet"
    manifest_path = cache_root / (
        f"EURUSD_M5_MICROSTRUCTURE_{CACHE_VERSION}.manifest.json"
    )
    if cache.exists() and manifest_path.exists():
        frame = pd.read_parquet(cache)
        frame["timestamp_utc"] = pd.to_datetime(
            frame["timestamp_utc"], utc=True
        )
        return (
            frame.set_index("timestamp_utc").sort_index(),
            json.loads(manifest_path.read_text(encoding="utf-8")),
        )
    symbol_root = raw_root / "EURUSD"
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    rows: list[dict[str, Any]] = []
    source_digest = hashlib.sha256()
    files_seen = 0
    populated_files = 0
    late_seconds = int(cfg["features"]["late_bar_seconds"])
    for path in sorted(symbol_root.glob("year=*/month=*/*.json")):
        stamp = path.stem
        if len(stamp) != 10 or not stamp.isdigit():
            continue
        hour = pd.to_datetime(stamp, format="%Y%m%d%H", utc=True)
        hour_ms = int(hour.timestamp() * 1000)
        if hour_ms < start_ms or hour_ms > end_ms:
            continue
        raw = path.read_bytes()
        source_digest.update(
            path.relative_to(raw_root).as_posix().encode("utf-8")
        )
        source_digest.update(hashlib.sha256(raw).digest())
        files_seen += 1
        decoded = aggregate_tick_payload(
            json.loads(raw), late_seconds
        )
        if decoded:
            populated_files += 1
            rows.extend(decoded)
    if not rows:
        raise RuntimeError("No EURUSD tick microstructure rows decoded")
    frame = pd.DataFrame(rows).sort_values("timestamp_ms")
    frame = frame.drop_duplicates("timestamp_ms", keep="last")
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_ms"], unit="ms", utc=True
    )
    frame = frame[
        (frame["timestamp_utc"] >= start)
        & (frame["timestamp_utc"] <= end)
    ]
    rolling = int(cfg["features"]["microstructure_rolling_bars"])
    frame["three_bar_quote_change_imbalance"] = (
        frame["quote_change_imbalance"]
        .rolling(rolling, min_periods=rolling)
        .mean()
    )
    frame["tick_count_ratio_24"] = (
        frame["tick_count_raw"]
        / frame["tick_count_raw"]
        .shift(1)
        .rolling(
            int(cfg["features"]["tick_median_bars"]),
            min_periods=int(cfg["features"]["tick_median_bars"]),
        )
        .median()
        .replace(0, np.nan)
    )
    frame.to_parquet(cache, index=False, compression="zstd")
    manifest = {
        "source_root": str(symbol_root),
        "source_chain_sha256": source_digest.hexdigest(),
        "files_seen": files_seen,
        "populated_files": populated_files,
        "m5_rows": int(len(frame)),
        "first_utc": frame["timestamp_utc"].min().isoformat(),
        "last_utc": frame["timestamp_utc"].max().isoformat(),
        "cache_path": str(cache),
        "cache_sha256": sha256_file(cache),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return frame.set_index("timestamp_utc"), manifest


def build_microstructure_dataset(
    eurusd: pd.DataFrame,
    state: pd.DataFrame,
    microstructure: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    dataset = build_labeled_dataset(eurusd, state, cfg)
    aligned = microstructure.reindex(
        pd.DatetimeIndex(dataset["signal_time_utc"])
    ).reset_index(drop=True)
    sign = np.where(dataset["side"].eq("LONG"), 1.0, -1.0)
    dataset["aligned_quote_change_imbalance"] = (
        sign * aligned["quote_change_imbalance"].to_numpy()
    )
    dataset["aligned_three_bar_quote_change_imbalance"] = (
        sign
        * aligned["three_bar_quote_change_imbalance"].to_numpy()
    )
    dataset["aligned_path_efficiency"] = (
        sign * aligned["path_efficiency"].to_numpy()
    )
    dataset["aligned_late_return_pips"] = (
        sign * aligned["late_return_pips"].to_numpy()
    )
    for column in (
        "volume_imbalance",
        "spread_mean_pips",
        "spread_std_pips",
        "spread_max_pips",
        "spread_last_pips",
        "realized_variance_pips2",
        "late_tick_share",
        "tick_count_ratio_24",
    ):
        dataset[column] = aligned[column].to_numpy()
    clip = float(cfg["features"]["clip_standardized_input"])
    dataset[MODEL_FEATURE_COLUMNS] = (
        dataset[MODEL_FEATURE_COLUMNS]
        .replace([np.inf, -np.inf], np.nan)
        .clip(-clip, clip)
    )
    return dataset.dropna(
        subset=MODEL_FEATURE_COLUMNS
    ).reset_index(drop=True)


def run_neutral_tick_microstructure_with_config(
    cfg: dict[str, Any],
    model_feature_columns: list[str] | None = None,
) -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    selected_features = model_feature_columns or MODEL_FEATURE_COLUMNS
    base = load_ensemble_config()
    eurusd, state, manifests = load_inputs(base)
    start = pd.Timestamp(base["data"]["start_utc"])
    end = pd.Timestamp(base["data"]["end_utc"])
    microstructure, tick_manifest = load_tick_microstructure(
        Path(base["data"]["dukascopy_raw_root"]),
        start,
        end,
        cfg,
    )
    dataset = build_microstructure_dataset(
        eurusd, state, microstructure, cfg
    )
    (
        threshold,
        development_qualified,
        threshold_sweep,
        development_coefficients,
    ) = select_development_threshold(
        dataset, cfg, selected_features
    )
    selected_predictions, coefficients = walk_forward_predictions(
        dataset, threshold, cfg, selected_features
    )
    trades = route_outcomes(selected_predictions, cfg)
    summary = _summary(trades, cfg)
    admitted = _admitted(summary, development_qualified, cfg)
    oracle_metrics, matches = oracle_match(trades, cfg)
    recent = _period(
        trades,
        "2026-01-01T00:00:00Z",
        "2026-06-30T23:59:59Z",
    )
    recent_metrics = payoff_metrics(recent)
    recent_metrics["fixed_0p01_lot_usd"] = (
        float(recent["fixed_0p01_lot_usd"].sum())
        if not recent.empty
        else 0.0
    )
    recent_metrics["trades_per_weekday"] = (
        len(recent)
        / active_weekday_fx_days(
            eurusd,
            pd.Timestamp("2026-01-01T00:00:00Z"),
            pd.Timestamp("2026-06-30T23:59:59Z"),
        )
    )
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else (
                "REJECTED_"
                + cfg["campaign_id"].upper().replace("-", "_")
            )
        ),
        "information_status": cfg["information_status"],
        "source_manifests": {
            **manifests,
            "EURUSD_TICKS": tick_manifest,
        },
        "causality": {
            "microstructure": (
                "Raw ticks aggregated only through completed signal M5 bar"
            ),
            "missing_policy": "No forward fill",
            "training_label_purge": (
                "Label exit strictly precedes every inference refit"
            ),
            "oracle_usage": cfg["oracle_usage"],
            "future_information_at_inference": False,
        },
        "dataset": {
            "rows": int(len(dataset)),
            "timestamps": int(
                dataset["completion_time_utc"].nunique()
            ),
            "positive_label_rate": float(dataset["target_first"].mean()),
            "features": int(len(selected_features)),
        },
        "development": {
            "selected_threshold": threshold,
            "qualified": development_qualified,
            "thresholds_tested": int(len(threshold_sweep)),
        },
        "walk_forward": {
            "admitted": admitted,
            **summary,
            "recent_six_months": recent_metrics,
            "oracle_imitation": oracle_metrics,
        },
        "verdict": (
            "Tick microstructure passed every frozen causal gate; "
            "prospective confirmation is still required."
            if admitted
            else "Completed tick microstructure did not pass the frozen "
            "development and walk-forward gates."
        ),
    }
    development_coefficients[
        "walk_forward_window"
    ] = "DEVELOPMENT_FIT"
    artifacts = {
        "LABELED_DATASET": dataset,
        "THRESHOLD_SWEEP": threshold_sweep,
        "SELECTED_PREDICTIONS": selected_predictions,
        "TRADES": trades,
        "ORACLE_MATCHES": matches,
        "MODEL_COEFFICIENTS": pd.concat(
            [development_coefficients, coefficients],
            ignore_index=True,
        ),
    }
    return result, artifacts


def run_neutral_tick_microstructure() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    return run_neutral_tick_microstructure_with_config(load_config())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
