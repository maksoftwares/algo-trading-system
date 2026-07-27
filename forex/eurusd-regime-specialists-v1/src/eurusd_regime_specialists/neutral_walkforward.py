from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_causal import oracle_match
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    is_quarantined,
    remove_top_winners,
    serialize,
    sha256_file,
)


FAMILY = "N5_WALKFORWARD_LOGIT"
FEATURE_COLUMNS = [
    "aligned_return_1_atr",
    "aligned_return_3_atr",
    "aligned_return_6_atr",
    "aligned_return_12_atr",
    "aligned_return_24_atr",
    "aligned_ema_gap_atr",
    "aligned_anchor_gap_atr",
    "aligned_close_location",
    "side_room_atr",
    "range_atr",
    "tick_ratio",
    "aligned_dxy_gap_atr",
    "aligned_eurusd_h1_gap_atr",
    "aligned_bond_gap_atr",
    "dxy_range_12_atr",
    "eurusd_range_12_atr",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
]


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT / "config" / "frozen_neutral_walkforward.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_WALKFORWARD_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_walkforward_outcome_inspection") is not True:
        raise RuntimeError("Neutral walk-forward contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Neutral walk-forward preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    return checked


def _causal_candidate_features(
    m5: pd.DataFrame, state: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    feature_cfg = cfg["features"]
    frame = m5.copy()
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
    atr_bars = int(feature_cfg["atr_bars"])
    frame["atr"] = true_range.rolling(
        atr_bars, min_periods=atr_bars
    ).mean()
    extreme_bars = int(feature_cfg["rolling_extreme_bars"])
    frame["prior_high"] = (
        frame["bid_high"]
        .shift(1)
        .rolling(extreme_bars, min_periods=extreme_bars)
        .max()
    )
    frame["prior_low"] = (
        frame["bid_low"]
        .shift(1)
        .rolling(extreme_bars, min_periods=extreme_bars)
        .min()
    )
    median_bars = int(feature_cfg["tick_median_bars"])
    tick_median = (
        frame["tick_count"]
        .shift(1)
        .rolling(median_bars, min_periods=median_bars)
        .median()
    )
    frame["tick_ratio"] = frame["tick_count"] / tick_median.replace(
        0, np.nan
    )
    frame["ema_fast"] = close.ewm(
        span=int(feature_cfg["ema_fast_bars"]), adjust=False
    ).mean()
    frame["ema_slow"] = close.ewm(
        span=int(feature_cfg["ema_slow_bars"]), adjust=False
    ).mean()
    for horizon in feature_cfg["return_horizons_bars"]:
        frame[f"return_{horizon}_atr"] = (
            close - close.shift(int(horizon))
        ) / frame["atr"]
    frame["ema_gap_atr"] = (
        frame["ema_fast"] - frame["ema_slow"]
    ) / frame["atr"]
    frame["anchor_gap_atr"] = (
        close - frame["ema_slow"]
    ) / frame["atr"]
    bar_range = (frame["bid_high"] - frame["bid_low"]).replace(0, np.nan)
    frame["range_atr"] = bar_range / frame["atr"]
    frame["close_location"] = (
        (frame["bid_close"] - frame["bid_low"]) / bar_range
    ).fillna(0.5)
    frame["room_high_atr"] = (
        frame["prior_high"] - close
    ) / frame["atr"]
    frame["room_low_atr"] = (
        close - frame["prior_low"]
    ) / frame["atr"]

    schedule = int(cfg["candidate_schedule_minutes"])
    completion = frame.index + pd.Timedelta(minutes=5)
    scheduled = (completion.minute % schedule) == 0
    chosen = frame.loc[scheduled].copy()
    chosen["signal_time_utc"] = chosen.index
    chosen["completion_time_utc"] = (
        chosen.index + pd.Timedelta(minutes=5)
    )
    chosen["state_time_utc"] = (
        chosen["completion_time_utc"].dt.floor("h")
        - pd.Timedelta(hours=1)
    ).dt.as_unit("ns")
    state_columns = [
        "direction",
        "shock",
        "DXY_compressed",
        "EURUSD_compressed",
        "DXY_ema_fast",
        "DXY_ema_slow",
        "DXY_atr",
        "DXY_range_12_atr",
        "EURUSD_ema_fast",
        "EURUSD_ema_slow",
        "EURUSD_atr",
        "EURUSD_range_12_atr",
        "BOND_ema_fast",
        "BOND_ema_slow",
        "BOND_atr",
    ]
    states = (
        state[state_columns]
        .reset_index()
        .rename(columns={"timestamp_utc": "matched_state_time_utc"})
        .sort_values("matched_state_time_utc")
    )
    states["matched_state_time_utc"] = states[
        "matched_state_time_utc"
    ].dt.as_unit("ns")
    joined = pd.merge_asof(
        chosen.reset_index(drop=True).sort_values("state_time_utc"),
        states,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    shock = joined["shock"].astype("boolean").fillna(True)
    compression = (
        joined["DXY_compressed"].astype("boolean").fillna(False)
        & joined["EURUSD_compressed"].astype("boolean").fillna(False)
    )
    joined = joined[
        joined["direction"].eq("NEUTRAL") & ~shock & ~compression
    ].copy()
    joined["dxy_gap_atr"] = (
        joined["DXY_ema_fast"] - joined["DXY_ema_slow"]
    ) / joined["DXY_atr"].replace(0, np.nan)
    joined["eurusd_h1_gap_atr"] = (
        joined["EURUSD_ema_fast"] - joined["EURUSD_ema_slow"]
    ) / joined["EURUSD_atr"].replace(0, np.nan)
    joined["bond_gap_atr"] = (
        joined["BOND_ema_fast"] - joined["BOND_ema_slow"]
    ) / joined["BOND_atr"].replace(0, np.nan)
    hour = (
        joined["completion_time_utc"].dt.hour
        + joined["completion_time_utc"].dt.minute / 60.0
    )
    weekday = joined["completion_time_utc"].dt.weekday
    joined["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    joined["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    joined["weekday_sin"] = np.sin(2.0 * np.pi * weekday / 5.0)
    joined["weekday_cos"] = np.cos(2.0 * np.pi * weekday / 5.0)
    return joined


def _effective_ask(
    arrays: dict[str, np.ndarray], field: str, position: int, floor: float
) -> float:
    return max(
        float(arrays[f"ask_{field}"][position]),
        float(arrays[f"bid_{field}"][position]) + floor,
    )


def _labeled_outcome(
    position: int,
    index: pd.DatetimeIndex,
    arrays: dict[str, np.ndarray],
    side: str,
    cfg: dict[str, Any],
    risk_pips: float | None = None,
) -> dict[str, Any]:
    label_cfg = cfg["label"]
    spread_floor = (
        float(label_cfg["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(label_cfg["extra_slippage_pips_per_side"]) * PIP
    )
    selected_risk_pips = (
        float(risk_pips)
        if risk_pips is not None
        else float(label_cfg["risk_pips"])
    )
    risk = selected_risk_pips * PIP
    target_distance = float(label_cfg["target_r"]) * risk
    deadline = index[position] + pd.Timedelta(
        hours=float(label_cfg["maximum_hold_hours"])
    )
    end = min(
        max(int(index.searchsorted(deadline, side="right")) - 1, position),
        len(index) - 1,
    )
    if side == "LONG":
        entry = _effective_ask(
            arrays, "open", position, spread_floor
        ) + slippage
        stop = entry - risk
        target = entry + target_distance
    else:
        entry = float(arrays["bid_open"][position]) - slippage
        stop = entry + risk
        target = entry - target_distance
    exit_position = end
    reason = "TIME_12H"
    exit_price = None
    for cursor in range(position, end + 1):
        if side == "LONG":
            if float(arrays["bid_low"][cursor]) <= stop:
                exit_position = cursor
                exit_price = (
                    min(float(arrays["bid_open"][cursor]), stop)
                    - slippage
                )
                reason = "STOP"
                break
            if float(arrays["bid_high"][cursor]) >= target:
                exit_position = cursor
                exit_price = (
                    max(float(arrays["bid_open"][cursor]), target)
                    - slippage
                )
                reason = "TARGET"
                break
        else:
            ask_high = _effective_ask(
                arrays, "high", cursor, spread_floor
            )
            ask_low = _effective_ask(
                arrays, "low", cursor, spread_floor
            )
            ask_open = _effective_ask(
                arrays, "open", cursor, spread_floor
            )
            if ask_high >= stop:
                exit_position = cursor
                exit_price = max(ask_open, stop) + slippage
                reason = "STOP"
                break
            if ask_low <= target:
                exit_position = cursor
                exit_price = min(ask_open, target) + slippage
                reason = "TARGET"
                break
    if exit_price is None:
        if side == "LONG":
            exit_price = (
                float(arrays["bid_close"][exit_position]) - slippage
            )
        else:
            exit_price = (
                _effective_ask(
                    arrays, "close", exit_position, spread_floor
                )
                + slippage
            )
    pnl = (
        exit_price - entry if side == "LONG" else entry - exit_price
    )
    return {
        "entry_time_utc": index[position],
        "exit_time_utc": index[exit_position],
        "entry_price": entry,
        "stop_price": stop,
        "target_price": target,
        "exit_price": exit_price,
        "exit_reason": reason,
        "risk_distance": risk,
        "risk_pips": selected_risk_pips,
        "outcome_r": pnl / risk,
        "target_first": int(reason == "TARGET"),
        "fixed_0p01_lot_usd": pnl * 1000.0,
    }


def build_labeled_dataset(
    m5: pd.DataFrame, state: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    base = _causal_candidate_features(m5, state, cfg)
    index = m5.index
    arrays = {
        column: m5[column].to_numpy(dtype=float)
        for column in (
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
        )
    }
    horizons = [
        int(value) for value in cfg["features"]["return_horizons_bars"]
    ]
    clip = float(cfg["features"]["clip_standardized_input"])
    records = []
    for _, candidate in base.iterrows():
        position = int(
            index.searchsorted(
                candidate["completion_time_utc"], side="left"
            )
        )
        if position >= len(index):
            continue
        label_cfg = cfg["label"]
        if label_cfg.get("risk_mode", "FIXED") == "ATR_CLIPPED":
            candidate_risk_pips = float(
                np.clip(
                    float(candidate["atr"])
                    / PIP
                    * float(label_cfg["atr_multiple"]),
                    float(label_cfg["minimum_risk_pips"]),
                    float(label_cfg["maximum_risk_pips"]),
                )
            )
        else:
            candidate_risk_pips = float(label_cfg["risk_pips"])
        for side, sign in (("LONG", 1.0), ("SHORT", -1.0)):
            row = {
                "family": FAMILY,
                "side": side,
                "signal_time_utc": candidate["signal_time_utc"],
                "completion_time_utc": candidate[
                    "completion_time_utc"
                ],
            }
            for horizon in horizons:
                row[f"aligned_return_{horizon}_atr"] = (
                    sign * candidate[f"return_{horizon}_atr"]
                )
            row.update(
                {
                    "aligned_ema_gap_atr": (
                        sign * candidate["ema_gap_atr"]
                    ),
                    "aligned_anchor_gap_atr": (
                        sign * candidate["anchor_gap_atr"]
                    ),
                    "aligned_close_location": (
                        sign
                        * (2.0 * candidate["close_location"] - 1.0)
                    ),
                    "side_room_atr": (
                        candidate["room_high_atr"]
                        if side == "LONG"
                        else candidate["room_low_atr"]
                    ),
                    "range_atr": candidate["range_atr"],
                    "tick_ratio": candidate["tick_ratio"],
                    "aligned_dxy_gap_atr": (
                        -sign * candidate["dxy_gap_atr"]
                    ),
                    "aligned_eurusd_h1_gap_atr": (
                        sign * candidate["eurusd_h1_gap_atr"]
                    ),
                    "aligned_bond_gap_atr": (
                        sign * candidate["bond_gap_atr"]
                    ),
                    "dxy_range_12_atr": candidate[
                        "DXY_range_12_atr"
                    ],
                    "eurusd_range_12_atr": candidate[
                        "EURUSD_range_12_atr"
                    ],
                    "hour_sin": candidate["hour_sin"],
                    "hour_cos": candidate["hour_cos"],
                    "weekday_sin": candidate["weekday_sin"],
                    "weekday_cos": candidate["weekday_cos"],
                }
            )
            row.update(
                _labeled_outcome(
                    position,
                    index,
                    arrays,
                    side,
                    cfg,
                    candidate_risk_pips,
                )
            )
            records.append(row)
    dataset = pd.DataFrame(records)
    dataset[FEATURE_COLUMNS] = (
        dataset[FEATURE_COLUMNS]
        .replace([np.inf, -np.inf], np.nan)
        .clip(-clip, clip)
    )
    return dataset.dropna(subset=FEATURE_COLUMNS).sort_values(
        ["entry_time_utc", "side"]
    ).reset_index(drop=True)


def purged_training_rows(
    dataset: pd.DataFrame, cutoff: pd.Timestamp
) -> pd.DataFrame:
    return dataset[
        (dataset["entry_time_utc"] < cutoff)
        & (dataset["exit_time_utc"] < cutoff)
    ]


def fit_predict(
    training: pd.DataFrame,
    inference: pd.DataFrame,
    cfg: dict[str, Any],
    feature_columns: list[str] | None = None,
) -> tuple[np.ndarray, pd.DataFrame]:
    columns = feature_columns or FEATURE_COLUMNS
    model_cfg = cfg["model"]
    if model_cfg["type"] == "SHALLOW_HIST_GRADIENT_BOOSTING":
        model = HistGradientBoostingClassifier(
            learning_rate=float(model_cfg["learning_rate"]),
            max_iter=int(model_cfg["max_iter"]),
            max_leaf_nodes=int(model_cfg["max_leaf_nodes"]),
            min_samples_leaf=int(model_cfg["min_samples_leaf"]),
            l2_regularization=float(model_cfg["l2_regularization"]),
            early_stopping=False,
            random_state=int(model_cfg["random_state"]),
        )
        model.fit(
            training[columns], training["target_first"].astype(int)
        )
        probabilities = model.predict_proba(inference[columns])[:, 1]
        return probabilities, pd.DataFrame(
            {
                "feature": columns,
                "coefficient": [None] * len(columns),
            }
        )
    if model_cfg["type"] != "L2_LOGISTIC_REGRESSION":
        raise ValueError(f"Unknown model type: {model_cfg['type']}")
    scaler = StandardScaler()
    train_x = scaler.fit_transform(training[columns])
    model = LogisticRegression(
        penalty=model_cfg["penalty"],
        C=float(model_cfg["C"]),
        solver=model_cfg["solver"],
        max_iter=int(model_cfg["max_iter"]),
        class_weight=model_cfg["class_weight"],
        random_state=int(model_cfg["random_state"]),
    )
    model.fit(train_x, training["target_first"].astype(int))
    probabilities = model.predict_proba(
        scaler.transform(inference[columns])
    )[:, 1]
    coefficients = pd.DataFrame(
        {
            "feature": columns,
            "coefficient": model.coef_[0],
        }
    ).sort_values("coefficient", ascending=False)
    return probabilities, coefficients


def choose_side(
    predictions: pd.DataFrame, threshold: float
) -> pd.DataFrame:
    if predictions.empty:
        return predictions
    ordered = predictions.sort_values(
        ["completion_time_utc", "predicted_probability", "side"],
        ascending=[True, False, True],
    )
    chosen = ordered.drop_duplicates(
        "completion_time_utc", keep="first"
    )
    return chosen[
        chosen["predicted_probability"] >= threshold
    ].sort_values("entry_time_utc")


def route_outcomes(
    predictions: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame(
            columns=[
                "family",
                "side",
                "signal_time_utc",
                "completion_time_utc",
                "entry_time_utc",
                "exit_time_utc",
                "entry_price",
                "stop_price",
                "target_price",
                "exit_price",
                "exit_reason",
                "predicted_probability",
                "risk_distance",
                "risk_pips",
                "r",
                "extra_half_pip_stress_r",
                "fixed_0p01_lot_usd",
            ]
        )
    base = load_ensemble_config()
    open_until: pd.Timestamp | None = None
    daily_count: dict[str, int] = {}
    records = []
    for _, row in predictions.sort_values("entry_time_utc").iterrows():
        entry_time = row["entry_time_utc"]
        if open_until is not None and entry_time <= open_until:
            continue
        if is_quarantined(
            entry_time, "EURUSD", base["quarantine"]
        ):
            continue
        date = entry_time.strftime("%Y-%m-%d")
        if daily_count.get(date, 0) >= int(
            cfg["execution"]["max_trades_per_utc_day"]
        ):
            continue
        result_r = float(row["outcome_r"])
        risk = float(row["risk_distance"])
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "side": row["side"],
                "signal_time_utc": row["signal_time_utc"],
                "completion_time_utc": row[
                    "completion_time_utc"
                ],
                "entry_time_utc": entry_time,
                "exit_time_utc": row["exit_time_utc"],
                "entry_price": row["entry_price"],
                "stop_price": row["stop_price"],
                "target_price": row["target_price"],
                "exit_price": row["exit_price"],
                "exit_reason": row["exit_reason"],
                "predicted_probability": row[
                    "predicted_probability"
                ],
                "risk_distance": risk,
                "risk_pips": float(row["risk_pips"]),
                "r": result_r,
                "extra_half_pip_stress_r": (
                    result_r - 0.5 * PIP / risk
                ),
                "fixed_0p01_lot_usd": row[
                    "fixed_0p01_lot_usd"
                ],
            }
        )
        open_until = row["exit_time_utc"]
        daily_count[date] = daily_count.get(date, 0) + 1
    return pd.DataFrame(records)


def _period(
    frame: pd.DataFrame, start: str, end: str
) -> pd.DataFrame:
    return frame[
        (frame["entry_time_utc"] >= pd.Timestamp(start))
        & (frame["entry_time_utc"] <= pd.Timestamp(end))
    ]


def select_development_threshold(
    dataset: pd.DataFrame,
    cfg: dict[str, Any],
    feature_columns: list[str] | None = None,
) -> tuple[float, bool, pd.DataFrame, pd.DataFrame]:
    fit_start, fit_end = cfg["development"]["fit"]
    selection_start, selection_end = cfg["development"][
        "threshold_selection"
    ]
    training = dataset[
        (dataset["entry_time_utc"] >= pd.Timestamp(fit_start))
        & (dataset["exit_time_utc"] <= pd.Timestamp(fit_end))
    ]
    inference = _period(dataset, selection_start, selection_end).copy()
    probabilities, coefficients = fit_predict(
        training, inference, cfg, feature_columns
    )
    inference["predicted_probability"] = probabilities
    rows = []
    routed_by_threshold = {}
    minimum_trades = int(
        cfg["development"]["minimum_trades_each_threshold_year"]
    )
    minimum_pf = float(
        cfg["development"][
            "minimum_profit_factor_each_threshold_year"
        ]
    )
    for threshold in cfg["development"]["threshold_grid"]:
        routed = route_outcomes(
            choose_side(inference, float(threshold)), cfg
        )
        routed_by_threshold[float(threshold)] = routed
        metrics_2021 = payoff_metrics(
            routed[routed["entry_time_utc"].dt.year.eq(2021)]
            if not routed.empty
            else routed
        )
        metrics_2022 = payoff_metrics(
            routed[routed["entry_time_utc"].dt.year.eq(2022)]
            if not routed.empty
            else routed
        )
        qualified = (
            metrics_2021["trades"] >= minimum_trades
            and metrics_2022["trades"] >= minimum_trades
            and metrics_2021["profit_factor"] >= minimum_pf
            and metrics_2022["profit_factor"] >= minimum_pf
        )
        rows.append(
            {
                "threshold": float(threshold),
                "qualified": qualified,
                "trades_2021": metrics_2021["trades"],
                "pf_2021": metrics_2021["profit_factor"],
                "net_r_2021": metrics_2021["net_r"],
                "trades_2022": metrics_2022["trades"],
                "pf_2022": metrics_2022["profit_factor"],
                "net_r_2022": metrics_2022["net_r"],
                "minimum_annual_pf": min(
                    metrics_2021["profit_factor"],
                    metrics_2022["profit_factor"],
                ),
                "total_net_r": (
                    metrics_2021["net_r"] + metrics_2022["net_r"]
                ),
            }
        )
    sweep = pd.DataFrame(rows)
    qualified_rows = sweep[sweep["qualified"]]
    choice_pool = qualified_rows if not qualified_rows.empty else sweep
    selected_row = choice_pool.sort_values(
        ["minimum_annual_pf", "total_net_r", "threshold"],
        ascending=[False, False, False],
    ).iloc[0]
    selected_threshold = float(selected_row["threshold"])
    return (
        selected_threshold,
        bool(selected_row["qualified"]),
        sweep,
        coefficients,
    )


def walk_forward_predictions(
    dataset: pd.DataFrame,
    threshold: float,
    cfg: dict[str, Any],
    feature_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prediction_frames = []
    coefficient_frames = []
    for name, (start, end) in cfg["walk_forward_windows"].items():
        cutoff = pd.Timestamp(start)
        training = purged_training_rows(dataset, cutoff)
        inference = _period(dataset, start, end).copy()
        probabilities, coefficients = fit_predict(
            training, inference, cfg, feature_columns
        )
        inference["predicted_probability"] = probabilities
        inference["walk_forward_window"] = name
        prediction_frames.append(
            choose_side(inference, threshold)
        )
        coefficients["walk_forward_window"] = name
        coefficients["training_rows"] = len(training)
        coefficient_frames.append(coefficients)
    selected = pd.concat(prediction_frames, ignore_index=True)
    coefficients = pd.concat(coefficient_frames, ignore_index=True)
    return selected, coefficients


def _summary(
    trades: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, Any]:
    windows = {
        name: payoff_metrics(_period(trades, start, end))
        for name, (start, end) in cfg[
            "walk_forward_windows"
        ].items()
    }
    return {
        "overall": payoff_metrics(trades),
        "windows": windows,
        "top_5_percent_winners_removed": payoff_metrics(
            remove_top_winners(trades)
        ),
        "extra_half_pip_round_trip": payoff_metrics(
            trades, "extra_half_pip_stress_r"
        ),
    }


def _admitted(
    summary: dict[str, Any],
    development_qualified: bool,
    cfg: dict[str, Any],
) -> bool:
    gate = cfg["final_admission"]
    return (
        development_qualified
        and all(
            block["trades"]
            >= int(gate["minimum_trades_each_walk_forward_window"])
            and float(gate["minimum_win_rate"])
            <= block["win_rate"]
            <= float(gate["maximum_win_rate"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= block["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and block["profit_factor"]
            >= float(gate["minimum_profit_factor"])
            and block["expectancy_r"]
            > float(gate["minimum_expectancy_r"])
            for block in summary["windows"].values()
        )
        and summary["overall"]["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r_overall"])
        and summary["top_5_percent_winners_removed"]["net_r"] > 0
        and summary["extra_half_pip_round_trip"]["net_r"] > 0
    )


def run_neutral_walkforward() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    cfg = load_config()
    base = load_ensemble_config()
    m5, state, manifests = load_inputs(base)
    dataset = build_labeled_dataset(m5, state, cfg)
    (
        threshold,
        development_qualified,
        threshold_sweep,
        development_coefficients,
    ) = select_development_threshold(dataset, cfg)
    selected_predictions, coefficients = walk_forward_predictions(
        dataset, threshold, cfg
    )
    trades = route_outcomes(selected_predictions, cfg)
    summary = _summary(trades, cfg)
    admitted = _admitted(summary, development_qualified, cfg)
    oracle_metrics, matches = oracle_match(trades, cfg)
    recent_start = "2026-01-01T00:00:00Z"
    recent_end = "2026-06-30T23:59:59Z"
    recent = _period(trades, recent_start, recent_end)
    recent_metrics = payoff_metrics(recent)
    recent_metrics["fixed_0p01_lot_usd"] = (
        float(recent["fixed_0p01_lot_usd"].sum())
        if not recent.empty
        else 0.0
    )
    recent_metrics["trades_per_weekday"] = (
        len(recent)
        / active_weekday_fx_days(
            m5,
            pd.Timestamp(recent_start),
            pd.Timestamp(recent_end),
        )
    )
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_WALKFORWARD_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "causality": {
            "features": "Completed M5 and lagged completed H1 state only",
            "training_labels": (
                "Future paths are used only after each historical label exit"
            ),
            "refit_purge": (
                "Every training label exit is strictly before inference"
            ),
            "oracle_usage": cfg["oracle_usage"],
            "future_information_at_inference": False,
        },
        "dataset": {
            "rows": int(len(dataset)),
            "timestamps": int(
                dataset["completion_time_utc"].nunique()
            ),
            "long_rows": int(dataset["side"].eq("LONG").sum()),
            "short_rows": int(dataset["side"].eq("SHORT").sum()),
            "positive_label_rate": float(dataset["target_first"].mean()),
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
            "The locked regularized model passed every chronological and "
            "robustness gate, but still requires prospective confirmation."
            if admitted
            else "The locked regularized model failed its development or "
            "walk-forward admission gates and is not deployable."
        ),
    }
    development_coefficients["walk_forward_window"] = "DEVELOPMENT_FIT"
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
