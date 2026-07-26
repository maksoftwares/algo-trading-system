from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd


def _weighted_auc_batches(
    target: np.ndarray,
    score: np.ndarray,
    base_weight: np.ndarray,
    block_index: np.ndarray,
    block_counts: np.ndarray,
    *,
    batch_size: int = 250,
) -> np.ndarray:
    order = np.argsort(score, kind="stable")
    sorted_score = score[order]
    sorted_target = target[order]
    sorted_weight = base_weight[order]
    sorted_blocks = block_index[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_score) != 0.0) + 1]
    results = np.full(len(block_counts), np.nan, dtype=float)
    for first in range(0, len(block_counts), batch_size):
        counts = block_counts[first : first + batch_size]
        weights = counts[:, sorted_blocks] * sorted_weight[None, :]
        positive = np.add.reduceat(weights * sorted_target[None, :], starts, axis=1)
        negative = np.add.reduceat(
            weights * (1 - sorted_target)[None, :], starts, axis=1
        )
        cumulative_negative = np.cumsum(negative, axis=1) - negative
        numerator = np.sum(positive * (cumulative_negative + 0.5 * negative), axis=1)
        positive_total = positive.sum(axis=1)
        negative_total = negative.sum(axis=1)
        denominator = positive_total * negative_total
        local = np.divide(
            numerator,
            denominator,
            out=np.full_like(numerator, np.nan),
            where=denominator > 0.0,
        )
        results[first : first + len(local)] = local
    return results


def _interval(values: np.ndarray, confidence: float) -> dict[str, float]:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    alpha = (1.0 - confidence) / 2.0
    return {
        "lower": float(np.quantile(clean, alpha)),
        "median": float(np.quantile(clean, 0.5)),
        "upper": float(np.quantile(clean, 1.0 - alpha)),
        "valid_resamples": len(clean),
    }


def primary_block_bootstrap(
    frame: pd.DataFrame, contract: Mapping[str, Any]
) -> dict[str, Any]:
    settings = contract["bootstrap"]
    ordered = frame.sort_values(
        ["decision_time", "candidate_id"], kind="stable"
    ).reset_index(drop=True)
    dates = ordered["decision_time"].dt.tz_convert("UTC").dt.date.to_numpy()
    origin = np.datetime64(min(dates), "D")
    business_index = np.busday_count(origin, np.asarray(dates, dtype="datetime64[D]"))
    block_width = int(settings["block_weekdays"])
    block_index = (business_index // block_width).astype(int)
    block_count = int(block_index.max()) + 1

    resamples = int(settings["resamples"])
    rng = np.random.default_rng(int(settings["seed"]))
    multiplicity = rng.multinomial(
        block_count, np.full(block_count, 1.0 / block_count), size=resamples
    )
    target = ordered["target"].to_numpy(dtype=int)
    probability = ordered["probability"].to_numpy(dtype=float)
    weights = ordered["structural_weight"].to_numpy(dtype=float)
    outcome = ordered["stress_net_r"].to_numpy(dtype=float)
    selected = ordered["selected"].to_numpy(dtype=bool)

    auc = _weighted_auc_batches(target, probability, weights, block_index, multiplicity)
    base_weight = np.bincount(block_index, weights=weights, minlength=block_count)
    base_weighted_r = np.bincount(
        block_index, weights=weights * outcome, minlength=block_count
    )
    selected_weight = np.bincount(
        block_index, weights=weights * selected, minlength=block_count
    )
    selected_weighted_r = np.bincount(
        block_index, weights=weights * outcome * selected, minlength=block_count
    )
    base_mean = (multiplicity @ base_weighted_r) / (multiplicity @ base_weight)
    selected_denominator = multiplicity @ selected_weight
    selected_mean = np.divide(
        multiplicity @ selected_weighted_r,
        selected_denominator,
        out=np.full(resamples, np.nan),
        where=selected_denominator > 0.0,
    )
    delta = selected_mean - base_mean
    confidence = float(settings["confidence"])
    return {
        "schema_version": "xauusd_step_4_primary_block_bootstrap_v1",
        "resamples": resamples,
        "seed": int(settings["seed"]),
        "block_weekdays": block_width,
        "calendar_blocks": block_count,
        "weighted_roc_auc": _interval(auc, confidence),
        "selected_weighted_mean_stress_r": _interval(selected_mean, confidence),
        "selected_minus_baseline_weighted_mean_stress_r": _interval(delta, confidence),
    }
