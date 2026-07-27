from __future__ import annotations

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
    active_weekday_fx_days,
    load_fx_m5,
    serialize,
    sha256_file,
)


CROSS_HORIZONS = [3, 6, 12, 24]
CROSS_FEATURE_COLUMNS = FEATURE_COLUMNS + [
    *[
        f"aligned_gbpusd_return_{horizon}_atr"
        for horizon in CROSS_HORIZONS
    ],
    *[
        f"aligned_usdjpy_return_{horizon}_atr"
        for horizon in CROSS_HORIZONS
    ],
    "gbpusd_range_atr",
    "gbpusd_tick_ratio",
    "usdjpy_range_atr",
    "usdjpy_tick_ratio",
]


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT / "config" / "frozen_neutral_crosspair.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_CROSSPAIR_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_crosspair_outcome_inspection") is not True:
        raise RuntimeError("Neutral cross-pair contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Neutral cross-pair preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    return checked


def crosspair_features(
    frame: pd.DataFrame,
    prefix: str,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    close = frame["bid_close"].astype(float)
    previous = close.shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous).abs(),
            (frame["bid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_bars = int(cfg["features"]["atr_bars"])
    atr = true_range.rolling(
        atr_bars, min_periods=atr_bars
    ).mean()
    median_bars = int(cfg["features"]["tick_median_bars"])
    prior_ticks = (
        frame["tick_count"]
        .shift(1)
        .rolling(median_bars, min_periods=median_bars)
        .median()
    )
    result = pd.DataFrame(index=frame.index)
    for horizon in cfg["features"][
        "crosspair_return_horizons_bars"
    ]:
        result[f"{prefix}_return_{horizon}_atr"] = (
            close - close.shift(int(horizon))
        ) / atr
    result[f"{prefix}_range_atr"] = (
        frame["bid_high"] - frame["bid_low"]
    ) / atr
    result[f"{prefix}_tick_ratio"] = (
        frame["tick_count"] / prior_ticks.replace(0, np.nan)
    )
    return result


def build_crosspair_dataset(
    eurusd: pd.DataFrame,
    state: pd.DataFrame,
    gbpusd: pd.DataFrame,
    usdjpy: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    dataset = build_labeled_dataset(eurusd, state, cfg)
    cross = crosspair_features(
        gbpusd, "gbpusd", cfg
    ).join(
        crosspair_features(usdjpy, "usdjpy", cfg),
        how="outer",
    )
    aligned = cross.reindex(
        pd.DatetimeIndex(dataset["signal_time_utc"])
    ).reset_index(drop=True)
    sign = np.where(dataset["side"].eq("LONG"), 1.0, -1.0)
    for horizon in cfg["features"][
        "crosspair_return_horizons_bars"
    ]:
        dataset[f"aligned_gbpusd_return_{horizon}_atr"] = (
            sign * aligned[f"gbpusd_return_{horizon}_atr"].to_numpy()
        )
        dataset[f"aligned_usdjpy_return_{horizon}_atr"] = (
            -sign * aligned[f"usdjpy_return_{horizon}_atr"].to_numpy()
        )
    for name in (
        "gbpusd_range_atr",
        "gbpusd_tick_ratio",
        "usdjpy_range_atr",
        "usdjpy_tick_ratio",
    ):
        dataset[name] = aligned[name].to_numpy()
    clip = float(cfg["features"]["clip_standardized_input"])
    dataset[CROSS_FEATURE_COLUMNS] = (
        dataset[CROSS_FEATURE_COLUMNS]
        .replace([np.inf, -np.inf], np.nan)
        .clip(-clip, clip)
    )
    return dataset.dropna(
        subset=CROSS_FEATURE_COLUMNS
    ).reset_index(drop=True)


def run_neutral_crosspair_with_config(
    cfg: dict[str, Any],
) -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    base = load_ensemble_config()
    eurusd, state, manifests = load_inputs(base)
    start = pd.Timestamp(base["data"]["start_utc"])
    end = pd.Timestamp(base["data"]["end_utc"])
    bar_root = Path(base["data"]["fx_bar_root"])
    gbpusd = load_fx_m5(bar_root, "GBPUSD", start, end)
    usdjpy = load_fx_m5(bar_root, "USDJPY", start, end)
    dataset = build_crosspair_dataset(
        eurusd, state, gbpusd, usdjpy, cfg
    )
    (
        threshold,
        development_qualified,
        threshold_sweep,
        development_coefficients,
    ) = select_development_threshold(
        dataset, cfg, CROSS_FEATURE_COLUMNS
    )
    selected_predictions, coefficients = walk_forward_predictions(
        dataset, threshold, cfg, CROSS_FEATURE_COLUMNS
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
        "source_manifests": manifests,
        "causality": {
            "eurusd_features": "Completed M5 plus lagged H1 state",
            "crosspair_features": (
                "Exact-timestamp completed GBPUSD and USDJPY M5 bars"
            ),
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
            "features": int(len(CROSS_FEATURE_COLUMNS)),
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
            "Cross-pair M5 information passed every frozen gate, but "
            "prospective confirmation remains mandatory."
            if admitted
            else "Cross-pair M5 information did not pass the frozen "
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


def run_neutral_crosspair() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    return run_neutral_crosspair_with_config(load_config())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
