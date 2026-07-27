from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .neutral_oracle_imitation import (
    _window_pass,
    build_dataset,
    economic_metrics,
    fit_oracle_model,
    oracle_match_metrics,
    purged_oracle_training_rows,
    route_concurrent,
)
from .neutral_tick_microstructure import MODEL_FEATURE_COLUMNS
from .neutral_walkforward import choose_side
from .research import (
    PACKAGE_ROOT,
    serialize,
    sha256_file,
    wilder_average,
)


FAMILY = "N8_NEUTRAL_SYNCHRONOUS_CROSSASSET"
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_synchronous_crossasset"
)


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_synchronous_crossasset.json"
        ).read_text(encoding="utf-8")
    )


def load_parent_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_oracle_imitation.json"
        ).read_text(encoding="utf-8")
    )


def runtime_config(
    cfg: dict[str, Any], parent: dict[str, Any]
) -> dict[str, Any]:
    result = dict(parent)
    for key in (
        "campaign_id",
        "information_status",
        "model",
        "development",
        "walk_forward_windows",
        "final_admission",
    ):
        result[key] = cfg[key]
    return result


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_SYNCHRONOUS_CROSSASSET_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get(
            "locked_before_synchronous_crossasset_outcome_pass"
        )
        is not True
    ):
        raise RuntimeError("Synchronous cross-asset contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Synchronous cross-asset preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    source = Path(load_config()["source"]["historical_path"])
    actual_source = sha256_file(source)
    expected_source = load_config()["source"]["historical_sha256"]
    if actual_source != expected_source:
        raise RuntimeError("Synchronous cross-asset source hash mismatch")
    checked[str(source)] = actual_source
    return checked


def _instrument_features(
    macro: pd.DataFrame,
    prefix: str,
    short_name: str,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    feature_cfg = cfg["crossasset_features"]
    available = macro[
        macro[f"{prefix}_available"].fillna(False).astype(bool)
    ].copy()
    close = available[f"{prefix}_mid_close"].astype(float)
    high = available[f"{prefix}_mid_high"].astype(float)
    low = available[f"{prefix}_mid_low"].astype(float)
    previous = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous).abs(),
            (low - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = wilder_average(
        true_range, int(feature_cfg["atr_bars"])
    ).replace(0, np.nan)
    result = pd.DataFrame(index=available.index)
    for horizon in feature_cfg["return_horizons_bars"]:
        result[f"{short_name}_m5_return_{horizon}_atr"] = (
            close - close.shift(int(horizon))
        ) / atr
    bar_range = (high - low).replace(0, np.nan)
    result[f"{short_name}_m5_close_location"] = (
        2.0 * (close - low) / bar_range - 1.0
    ).fillna(0.0)
    result[f"{short_name}_m5_range_atr"] = bar_range / atr
    baseline = int(feature_cfg["tick_and_spread_baseline_bars"])
    tick_count = available[f"{prefix}_mid_tick_count"].astype(float)
    tick_baseline = (
        tick_count.shift(1)
        .rolling(baseline, min_periods=baseline)
        .median()
        .replace(0, np.nan)
    )
    result[f"{short_name}_m5_tick_ratio_24"] = (
        tick_count / tick_baseline
    )
    spread = (
        available[f"{prefix}_ask_close"].astype(float)
        - available[f"{prefix}_bid_close"].astype(float)
    )
    spread_baseline = (
        spread.shift(1)
        .rolling(baseline, min_periods=baseline)
        .median()
        .replace(0, np.nan)
    )
    result[f"{short_name}_m5_spread_ratio_24"] = (
        spread / spread_baseline
    )
    return result.reindex(macro.index)


def build_crossasset_features(
    macro: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    frame = macro.copy()
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_utc"], utc=True
    )
    frame = (
        frame.drop_duplicates("timestamp_utc", keep="last")
        .sort_values("timestamp_utc")
        .set_index("timestamp_utc")
    )
    features = pd.concat(
        [
            _instrument_features(
                frame, "dollaridxusd", "dxy", cfg
            ),
            _instrument_features(
                frame, "ustbondtrusd", "bond", cfg
            ),
        ],
        axis=1,
    )
    features["both_available"] = (
        frame["dollaridxusd_available"].fillna(False).astype(bool)
        & frame["ustbondtrusd_available"].fillna(False).astype(bool)
    )
    return features


def attach_crossasset_features(
    dataset: pd.DataFrame,
    features: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    aligned = features.reindex(
        pd.DatetimeIndex(dataset["signal_time_utc"])
    ).reset_index(drop=True)
    sign = np.where(dataset["side"].eq("LONG"), 1.0, -1.0)
    result = dataset.copy()
    for horizon in cfg["crossasset_features"][
        "return_horizons_bars"
    ]:
        result[f"aligned_dxy_m5_return_{horizon}_atr"] = (
            -sign
            * aligned[
                f"dxy_m5_return_{horizon}_atr"
            ].to_numpy()
        )
        result[f"aligned_bond_m5_return_{horizon}_atr"] = (
            sign
            * aligned[
                f"bond_m5_return_{horizon}_atr"
            ].to_numpy()
        )
    result["aligned_dxy_m5_close_location"] = (
        -sign * aligned["dxy_m5_close_location"].to_numpy()
    )
    result["aligned_bond_m5_close_location"] = (
        sign * aligned["bond_m5_close_location"].to_numpy()
    )
    for short_name in ("dxy", "bond"):
        for suffix in (
            "m5_range_atr",
            "m5_tick_ratio_24",
            "m5_spread_ratio_24",
        ):
            result[f"{short_name}_{suffix}"] = aligned[
                f"{short_name}_{suffix}"
            ].to_numpy()
    result["aligned_joint_pressure_1"] = (
        result["aligned_dxy_m5_return_1_atr"]
        + result["aligned_bond_m5_return_1_atr"]
    ) / 2.0
    result["dxy_bond_support_agreement_1"] = (
        result["aligned_dxy_m5_return_1_atr"]
        * result["aligned_bond_m5_return_1_atr"]
    )
    result["crossasset_both_available"] = aligned[
        "both_available"
    ].fillna(False).to_numpy()
    columns = cfg["crossasset_features"]["columns"]
    clip = float(
        cfg["crossasset_features"]["clip_standardized_input"]
    )
    result[columns] = (
        result[columns]
        .replace([np.inf, -np.inf], np.nan)
        .clip(-clip, clip)
    )
    result = result[
        result["crossasset_both_available"]
    ].dropna(subset=columns)
    expected_completion = (
        result["signal_time_utc"] + pd.Timedelta(minutes=5)
    )
    if not expected_completion.equals(
        result["completion_time_utc"]
    ):
        raise RuntimeError(
            "Cross-asset bar is not fully completed at decision time"
        )
    return result.reset_index(drop=True)


def load_augmented_dataset(
    cfg: dict[str, Any], parent: dict[str, Any]
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
    pd.DataFrame,
]:
    dataset, oracle, manifests, eurusd = build_dataset(parent)
    source = Path(cfg["source"]["historical_path"])
    macro = pd.read_parquet(source)
    features = build_crossasset_features(macro, cfg)
    augmented = attach_crossasset_features(dataset, features, cfg)
    manifests = {
        **manifests,
        "SYNCHRONOUS_CROSSASSET_M5": {
            "path": str(source),
            "sha256": sha256_file(source),
            "rows": int(len(macro)),
            "first_utc": pd.to_datetime(
                macro["timestamp_utc"], utc=True
            ).min().isoformat(),
            "last_utc": pd.to_datetime(
                macro["timestamp_utc"], utc=True
            ).max().isoformat(),
            "prospective_parity": cfg["source"][
                "prospective_parity"
            ],
        },
    }
    return augmented, oracle, manifests, eurusd


def select_development_threshold(
    dataset: pd.DataFrame,
    oracle: pd.DataFrame,
    eurusd: pd.DataFrame,
    cfg: dict[str, Any],
    features: list[str],
) -> tuple[float, bool, pd.DataFrame, pd.DataFrame]:
    fit_start, fit_end = map(
        pd.Timestamp, cfg["development"]["fit"]
    )
    selection_start, selection_end = map(
        pd.Timestamp, cfg["development"]["threshold_selection"]
    )
    training = dataset[
        (dataset["entry_time_utc"] >= fit_start)
        & (dataset["entry_time_utc"] <= fit_end)
        & (dataset["oracle_label_known_time_utc"] < selection_start)
    ]
    inference = dataset[
        (dataset["entry_time_utc"] >= selection_start)
        & (dataset["entry_time_utc"] <= selection_end)
    ].copy()
    probabilities, coefficients = fit_oracle_model(
        training, inference, cfg, features
    )
    inference["predicted_probability"] = probabilities
    rows: list[dict[str, Any]] = []
    minimum = int(
        cfg["development"]["minimum_trades_each_threshold_year"]
    )
    for threshold in cfg["development"]["threshold_grid"]:
        selected = choose_side(inference, float(threshold))
        trades = route_concurrent(selected, cfg)
        imitation, _ = oracle_match_metrics(
            trades,
            oracle,
            selection_start,
            selection_end,
            int(cfg["oracle_matching"]["secondary_tolerance_minutes"]),
        )
        economics = economic_metrics(
            trades, eurusd, selection_start, selection_end, cfg
        )
        counts = {
            year: int(
                trades["entry_time_utc"].dt.year.eq(year).sum()
            )
            for year in (2021, 2022)
        }
        rows.append(
            {
                "threshold": float(threshold),
                "eligible_frequency": all(
                    value >= minimum for value in counts.values()
                ),
                "trades_2021": counts[2021],
                "trades_2022": counts[2022],
                **imitation,
                "profit_factor": economics["profit_factor"],
                "net_r": economics["net_r"],
            }
        )
    sweep = pd.DataFrame(rows)
    eligible = sweep[sweep["eligible_frequency"]]
    fallback = eligible.empty
    ranked = sweep if fallback else eligible
    chosen = ranked.sort_values(
        ["exact_f1", "tolerant_f1", "net_r", "threshold"],
        ascending=[False, False, False, False],
    ).iloc[0]
    qualified = (
        not fallback
        and chosen["exact_precision"]
        >= float(cfg["development"]["minimum_exact_precision"])
        and chosen["exact_recall"]
        >= float(cfg["development"]["minimum_exact_recall"])
    )
    sweep["selected"] = sweep["threshold"].eq(chosen["threshold"])
    sweep["fallback_after_frequency_failure"] = fallback
    return float(chosen["threshold"]), bool(qualified), sweep, coefficients


def run_synchronous_crossasset() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_lock()
    frozen = load_config()
    parent = load_parent_config()
    cfg = runtime_config(frozen, parent)
    dataset, oracle, manifests, eurusd = load_augmented_dataset(
        frozen, parent
    )
    feature_columns = (
        MODEL_FEATURE_COLUMNS
        + frozen["crossasset_features"]["columns"]
    )
    threshold, development_qualified, sweep, development_coef = (
        select_development_threshold(
            dataset, oracle, eurusd, cfg, feature_columns
        )
    )
    trades_parts: list[pd.DataFrame] = []
    prediction_parts: list[pd.DataFrame] = []
    match_parts: list[pd.DataFrame] = []
    coefficient_parts = [
        development_coef.assign(
            walk_forward_window="DEVELOPMENT_FIT"
        )
    ]
    windows: dict[str, Any] = {}
    for name, (start_raw, end_raw) in cfg[
        "walk_forward_windows"
    ].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        training = purged_oracle_training_rows(dataset, start)
        inference = dataset[
            (dataset["entry_time_utc"] >= start)
            & (dataset["entry_time_utc"] <= end)
        ].copy()
        probabilities, coefficients = fit_oracle_model(
            training, inference, cfg, feature_columns
        )
        inference["predicted_probability"] = probabilities
        selected = choose_side(inference, threshold)
        trades = route_concurrent(selected, cfg)
        trades["family"] = FAMILY
        trades["walk_forward_window"] = name
        selected["walk_forward_window"] = name
        coefficients["walk_forward_window"] = name
        economics = economic_metrics(
            trades, eurusd, start, end, cfg
        )
        imitation, matches = oracle_match_metrics(
            trades,
            oracle,
            start,
            end,
            int(cfg["oracle_matching"]["secondary_tolerance_minutes"]),
        )
        matches["walk_forward_window"] = name
        windows[name] = {
            "training_rows": int(len(training)),
            "inference_rows": int(len(inference)),
            "passed": _window_pass(economics, cfg),
            "economics": economics,
            "oracle_imitation": imitation,
        }
        trades_parts.append(trades)
        prediction_parts.append(selected)
        match_parts.append(matches)
        coefficient_parts.append(coefficients)
    trades = pd.concat(trades_parts, ignore_index=True)
    predictions = pd.concat(prediction_parts, ignore_index=True)
    matches = pd.concat(match_parts, ignore_index=True)
    coefficients = pd.concat(coefficient_parts, ignore_index=True)
    oos_start = min(
        pd.Timestamp(value[0])
        for value in cfg["walk_forward_windows"].values()
    )
    oos_end = max(
        pd.Timestamp(value[1])
        for value in cfg["walk_forward_windows"].values()
    )
    economics = economic_metrics(
        trades, eurusd, oos_start, oos_end, cfg
    )
    imitation, _ = oracle_match_metrics(
        trades,
        oracle,
        oos_start,
        oos_end,
        int(cfg["oracle_matching"]["secondary_tolerance_minutes"]),
    )
    membership_breakdown = {}
    for member, name in (
        (1, "exact_oracle_members"),
        (0, "nonmembers"),
    ):
        metrics = payoff_metrics(
            trades[trades["oracle_member"].eq(member)]
        )
        membership_breakdown[name] = {
            key: (
                None
                if isinstance(value, (float, np.floating))
                and not np.isfinite(value)
                else value
            )
            for key, value in metrics.items()
        }
    gate = cfg["final_admission"]
    imitation_pass = (
        imitation["exact_precision"]
        >= float(gate["minimum_exact_match_precision_overall"])
        and imitation["exact_recall"]
        >= float(gate["minimum_exact_match_recall_overall"])
        and imitation["tolerant_precision"]
        >= float(gate["minimum_15m_match_precision_overall"])
    )
    admitted = (
        development_qualified
        and all(value["passed"] for value in windows.values())
        and imitation_pass
        and economics["extra_half_pip_stress_net_r"] > 0
    )
    baseline = frozen["baseline_comparison"]
    result = {
        "campaign_id": frozen["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_SYNCHRONOUS_CROSSASSET_V1"
        ),
        "research_only": True,
        "broker_action_allowed": False,
        "information_status": frozen["information_status"],
        "source_manifests": manifests,
        "causality": {
            "crossasset_join": (
                "Exact M5 bar-start timestamp joined to EURUSD signal bar; "
                "usable only at the shared five-minute completion"
            ),
            "missing_policy": "Both symbols required; no forward fill",
            "oracle_at_inference": False,
            "future_scores_used_for_routing": False,
        },
        "dataset": {
            "rows": int(len(dataset)),
            "timestamps": int(
                dataset["completion_time_utc"].nunique()
            ),
            "oracle_positive_rows": int(
                dataset["oracle_member"].sum()
            ),
            "oracle_positive_rate": float(
                dataset["oracle_member"].mean()
            ),
            "features": len(feature_columns),
            "new_crossasset_features": len(
                frozen["crossasset_features"]["columns"]
            ),
        },
        "development": {
            "selected_threshold": threshold,
            "qualified": development_qualified,
            "thresholds_tested": int(len(sweep)),
        },
        "walk_forward": {
            "admitted": admitted,
            "windows": windows,
            "overall_economics": economics,
            "overall_oracle_imitation": imitation,
            "outcomes_by_exact_oracle_membership": membership_breakdown,
            "imitation_gate_passed": imitation_pass,
        },
        "baseline_comparison": {
            **baseline,
            "profit_factor_delta": (
                economics["profit_factor"]
                - float(baseline["overall_profit_factor"])
            ),
            "exact_precision_delta": (
                imitation["exact_precision"]
                - float(baseline["overall_exact_precision"])
            ),
        },
        "verdict": (
            "Synchronized completed DXY and Treasury M5 features passed "
            "every frozen gate; prospective confirmation is mandatory."
            if admitted
            else "Synchronized completed DXY and Treasury M5 features "
            "failed at least one frozen development, economic, imitation, "
            "or stress gate and do not admit a Regime 1 expert."
        ),
    }
    artifacts = {
        "THRESHOLD_SWEEP": sweep,
        "SELECTED_PREDICTIONS": predictions,
        "TRADES": trades,
        "ORACLE_MATCHES": matches,
        "MODEL_COEFFICIENTS": coefficients,
    }
    return result, artifacts


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
