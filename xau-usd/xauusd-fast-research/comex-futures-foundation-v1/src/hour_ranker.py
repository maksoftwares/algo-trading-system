from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from context_ranker import metrics, prepare_spot_context, select_trades
from tbbo_features import add_flow_features, aggregate_trade_seconds
from trade_campaign import filter_session_with_warmup


SPOT_FEATURES = [
    "spot_return_5m_atr", "spot_return_15m_atr", "spot_return_60m_atr",
    "ema_gap_atr", "range_location_60m", "tick_imbalance_5m",
    "tick_imbalance_15m", "microprice_edge_atr", "price_efficiency_5m",
    "atr_ratio", "quote_intensity_ratio", "spot_spread_atr", "body_fraction",
    "hour_sin", "hour_cos", "weekday_sin", "weekday_cos",
]
COMEX_FEATURES = [
    "comex_flow_5s", "comex_flow_30s", "comex_abs_flow_5s",
    "comex_abs_flow_30s", "comex_log_volume_5s", "comex_volume_share_5s_60s",
    "comex_impulse_5s", "comex_impulse_30s",
]
FEATURE_COLUMNS = [*SPOT_FEATURES, *COMEX_FEATURES]


def regular_signals(m5: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    context = prepare_spot_context(m5).reset_index().rename(columns={"index": "m5_index"})
    context["signal_time"] = context["available_time_utc"]
    local = context["signal_time"].dt.tz_convert("America/New_York")
    minutes = local.dt.hour * 60 + local.dt.minute
    mask = (
        (context["signal_time"] >= pd.Timestamp(start))
        & (context["signal_time"] < pd.Timestamp(end))
        & (local.dt.minute % 15 == 0)
        & (minutes >= 510)
        & (minutes < 810)
    )
    selected = context.loc[mask].copy()
    hour = local.loc[mask].dt.hour + local.loc[mask].dt.minute / 60.0
    weekday = local.loc[mask].dt.weekday
    selected["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    selected["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    selected["weekday_sin"] = np.sin(2.0 * np.pi * weekday / 7.0)
    selected["weekday_cos"] = np.cos(2.0 * np.pi * weekday / 7.0)
    selected["source_date"] = selected["signal_time"].dt.strftime("%Y%m%d")
    selected["target_return_atr"] = (
        context["mid_close"].shift(-12).loc[selected.index] - selected["mid_close"]
    ) / selected["atr"]
    return selected.loc[np.isfinite(selected[SPOT_FEATURES + ["target_return_atr"]]).all(axis=1)].reset_index(drop=True)


def label_both_directions(signals: pd.DataFrame, m5: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    rows = m5.reset_index(drop=True)
    output = signals.copy()
    horizon = int(config["horizon_m5_bars"])
    stop_atr = float(config["stop_atr"])
    long_r = []
    short_r = []
    long_exit = []
    short_exit = []
    for signal in output.itertuples(index=False):
        current = int(signal.m5_index)
        entry_index = current + 1
        exit_index = current + horizon
        atr = float(signal.atr)
        risk = stop_atr * atr
        entry_long = float(rows.iloc[entry_index]["ask_open"])
        entry_short = float(rows.iloc[entry_index]["bid_open"])
        stop_long = entry_long - risk
        stop_short = entry_short + risk
        exit_long = float(rows.iloc[exit_index]["bid_close"])
        exit_short = float(rows.iloc[exit_index]["ask_close"])
        long_time = short_time = pd.to_datetime(
            int(rows.iloc[exit_index]["timestamp_ms"]) + 300_000, unit="ms", utc=True
        )
        for position in range(entry_index, exit_index + 1):
            bar = rows.iloc[position]
            bar_time = pd.to_datetime(int(bar["timestamp_ms"]), unit="ms", utc=True)
            if float(bar["bid_open"]) <= stop_long:
                exit_long = float(bar["bid_open"])
                long_time = bar_time
                break
            if float(bar["bid_low"]) <= stop_long:
                exit_long = stop_long
                long_time = bar_time + pd.offsets.Minute(5)
                break
        for position in range(entry_index, exit_index + 1):
            bar = rows.iloc[position]
            bar_time = pd.to_datetime(int(bar["timestamp_ms"]), unit="ms", utc=True)
            if float(bar["ask_open"]) >= stop_short:
                exit_short = float(bar["ask_open"])
                short_time = bar_time
                break
            if float(bar["ask_high"]) >= stop_short:
                exit_short = stop_short
                short_time = bar_time + pd.offsets.Minute(5)
                break
        cost_r = float(config["ticket_cost_usd"]) / risk + float(config["stress_slippage_r"])
        long_r.append((exit_long - entry_long) / risk - cost_r)
        short_r.append((entry_short - exit_short) / risk - cost_r)
        long_exit.append(long_time)
        short_exit.append(short_time)
    output["long_stress_net_r"] = long_r
    output["short_stress_net_r"] = short_r
    output["long_exit_time"] = long_exit
    output["short_exit_time"] = short_exit
    output["entry_time_utc"] = output["signal_time"]
    return output


def align_hour_comex(events: pd.DataFrame, signals: pd.DataFrame, feature_config: Mapping[str, Any]) -> pd.DataFrame:
    session = filter_session_with_warmup(events, feature_config)
    seconds = aggregate_trade_seconds(session, tick_size=float(feature_config["tick_size"]))
    features = add_flow_features(seconds, feature_config).sort_values("feature_time_utc")
    joined = pd.merge_asof(
        signals.sort_values("signal_time"), features,
        left_on="signal_time", right_on="feature_time_utc", direction="backward",
        tolerance=timedelta(seconds=2),
    )
    joined = joined.loc[joined["feature_time_utc"].notna()].copy()
    if (joined["feature_time_utc"] > joined["signal_time"]).any():
        raise ValueError("Hour ranker joined a future COMEX second.")
    joined["comex_flow_5s"] = joined["flow_imbalance_5s"]
    joined["comex_flow_30s"] = joined["flow_imbalance_30s"]
    joined["comex_abs_flow_5s"] = joined["flow_imbalance_5s"].abs()
    joined["comex_abs_flow_30s"] = joined["flow_imbalance_30s"].abs()
    joined["comex_log_volume_5s"] = np.log1p(joined["contract_volume_5s"])
    joined["comex_volume_share_5s_60s"] = joined["volume_share_5s_of_60s"]
    joined["comex_impulse_5s"] = joined["price_impulse_ticks_5s"]
    joined["comex_impulse_30s"] = joined["price_impulse_ticks_30s"]
    finite = np.isfinite(joined[FEATURE_COLUMNS].to_numpy(dtype=float)).all(axis=1)
    return joined.loc[finite].reset_index(drop=True)


def _scored_trades(rows: pd.DataFrame, threshold: float, selection: Mapping[str, Any]) -> pd.DataFrame:
    scored = rows.loc[rows["model_score"].abs() >= threshold].copy()
    scored["direction"] = np.where(scored["model_score"] >= 0, "LONG", "SHORT")
    scored["stress_net_r"] = np.where(
        scored["direction"] == "LONG", scored["long_stress_net_r"], scored["short_stress_net_r"]
    )
    scored["exit_time_utc"] = np.where(
        scored["direction"] == "LONG", scored["long_exit_time"], scored["short_exit_time"]
    )
    scored["model_score"] = scored["model_score"].abs()
    return select_trades(scored, threshold, selection)


def run_hour_ranker(dataset: pd.DataFrame, config: Mapping[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    exam_start = pd.Timestamp(config["windows"]["exam"][0])
    if (dataset["signal_time"] >= exam_start).any():
        raise ValueError("Hour ranker V1 refuses exam rows.")
    split = {
        name: dataset.loc[(dataset["signal_time"] >= pd.Timestamp(bounds[0])) & (dataset["signal_time"] < pd.Timestamp(bounds[1]))].copy()
        for name, bounds in config["windows"].items() if name != "exam"
    }
    parameters = {key: value for key, value in config["model"].items() if key != "calibration_absolute_score_quantile"}
    model = HistGradientBoostingRegressor(**parameters)
    model.fit(split["fit"][FEATURE_COLUMNS], split["fit"]["target_return_atr"])
    calibration = split["calibration"]
    calibration["model_score"] = model.predict(calibration[FEATURE_COLUMNS])
    threshold = float(np.quantile(calibration["model_score"].abs(), config["model"]["calibration_absolute_score_quantile"]))
    calibration_selected = _scored_trades(calibration, threshold, config["selection"])
    calibration_metrics = metrics(calibration_selected, config["windows"]["calibration"], config["gates"]["calibration"])
    report: dict[str, Any] = {"fit_rows": len(split["fit"]), "calibration_rows": len(calibration), "threshold": threshold, "calibration": calibration_metrics, "validation_decision_eligible": calibration_metrics["gate_pass"]}
    selections = []
    if not calibration_selected.empty:
        chosen = calibration_selected.copy()
        chosen["stage"] = "calibration"
        selections.append(chosen)
    if calibration_metrics["gate_pass"]:
        validation = split["validation"]
        validation["model_score"] = model.predict(validation[FEATURE_COLUMNS])
        validation_selected = _scored_trades(validation, threshold, config["selection"])
        report["validation"] = metrics(validation_selected, config["windows"]["validation"], config["gates"]["validation"])
        if not validation_selected.empty:
            chosen = validation_selected.copy()
            chosen["stage"] = "validation"
            selections.append(chosen)
    else:
        report["validation"] = {"status": "NOT_EVALUATED_AFTER_CALIBRATION_FAILURE"}
    survivor = calibration_metrics["gate_pass"] and report["validation"].get("gate_pass", False)
    return ({"contract_id": config["contract_id"], "research_decision": "PASS" if survivor else "REJECT", "specialist": report, "exam_status": "NOT_EVALUATED", "broker_action_authorized": False}, pd.concat(selections, ignore_index=True) if selections else pd.DataFrame())
