from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from context_ranker import metrics, select_trades
from tbbo_features import add_flow_features, aggregate_trade_seconds
from trade_campaign import filter_session_with_warmup


SPOT_FEATURES = [
    "dir_return_15m_atr", "dir_return_1h_atr", "dir_return_4h_atr",
    "dir_return_24h_atr", "range_atr", "atr_ratio", "body_fraction",
    "dir_close_location", "efficiency_ratio_16", "dir_ema32_distance_atr",
    "quote_intensity_ratio_m15", "dir_tick_imbalance_5m",
    "dir_tick_imbalance_15m", "m5_quote_intensity_ratio", "spread_atr",
    "hour_sin", "hour_cos", "weekday_sin", "weekday_cos",
]
COMEX_FEATURES = [
    "comex_dir_flow_5s", "comex_dir_flow_30s", "comex_abs_flow_5s",
    "comex_abs_flow_30s", "comex_log_volume_5s", "comex_volume_share_5s_60s",
    "comex_dir_impulse_5s", "comex_dir_impulse_30s",
]
FEATURE_COLUMNS = [*SPOT_FEATURES, *COMEX_FEATURES]


def align_comex_context(
    events: pd.DataFrame,
    candidates: pd.DataFrame,
    feature_config: Mapping[str, Any],
) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()
    session_events = filter_session_with_warmup(events, feature_config)
    seconds = aggregate_trade_seconds(session_events, tick_size=float(feature_config["tick_size"]))
    features = add_flow_features(seconds, feature_config).sort_values("feature_time_utc")
    left = candidates.copy()
    left["signal_time"] = pd.to_datetime(left["signal_time"], utc=True)
    joined = pd.merge_asof(
        left.sort_values("signal_time"),
        features,
        left_on="signal_time",
        right_on="feature_time_utc",
        direction="backward",
        tolerance=timedelta(seconds=2),
    )
    joined = joined.loc[joined["feature_time_utc"].notna()].copy()
    if (joined["feature_time_utc"] > joined["signal_time"]).any():
        raise ValueError("COMEX context join used a future second.")
    sign = joined["direction_sign"].astype(float)
    joined["comex_dir_flow_5s"] = sign * joined["flow_imbalance_5s"]
    joined["comex_dir_flow_30s"] = sign * joined["flow_imbalance_30s"]
    joined["comex_abs_flow_5s"] = joined["flow_imbalance_5s"].abs()
    joined["comex_abs_flow_30s"] = joined["flow_imbalance_30s"].abs()
    joined["comex_log_volume_5s"] = np.log1p(joined["contract_volume_5s"])
    joined["comex_volume_share_5s_60s"] = joined["volume_share_5s_of_60s"]
    joined["comex_dir_impulse_5s"] = sign * joined["price_impulse_ticks_5s"]
    joined["comex_dir_impulse_30s"] = sign * joined["price_impulse_ticks_30s"]
    finite = np.isfinite(joined[FEATURE_COLUMNS].to_numpy(dtype=float)).all(axis=1)
    return joined.loc[finite].reset_index(drop=True)


def run_m15_ranker(dataset: pd.DataFrame, config: Mapping[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    exam_start = pd.Timestamp(config["windows"]["exam"][0])
    if (dataset["signal_time"] >= exam_start).any():
        raise ValueError("COMEX M15 ranker V1 refuses exam rows.")
    reports = {}
    selections = []
    parameters = {key: value for key, value in config["model"].items() if key != "calibration_quantile"}
    for family in sorted(dataset["family_id"].unique()):
        rows = dataset.loc[dataset["family_id"] == family]
        split = {
            name: rows.loc[
                (rows["signal_time"] >= pd.Timestamp(bounds[0]))
                & (rows["signal_time"] < pd.Timestamp(bounds[1]))
            ].copy()
            for name, bounds in config["windows"].items() if name != "exam"
        }
        model = HistGradientBoostingRegressor(**parameters)
        model.fit(split["fit"][FEATURE_COLUMNS], split["fit"]["stress_net_r"])
        calibration = split["calibration"]
        calibration["model_score"] = model.predict(calibration[FEATURE_COLUMNS])
        threshold = float(np.quantile(calibration["model_score"], config["model"]["calibration_quantile"]))
        calibration_selected = select_trades(calibration, threshold, config["selection"])
        calibration_metrics = metrics(calibration_selected, config["windows"]["calibration"], config["gates"]["calibration"])
        report: dict[str, Any] = {"fit_rows": len(split["fit"]), "calibration_rows": len(calibration), "threshold": threshold, "calibration": calibration_metrics, "validation_decision_eligible": calibration_metrics["gate_pass"]}
        if not calibration_selected.empty:
            chosen = calibration_selected.copy()
            chosen["stage"] = "calibration"
            selections.append(chosen)
        if calibration_metrics["gate_pass"]:
            validation = split["validation"]
            validation["model_score"] = model.predict(validation[FEATURE_COLUMNS])
            validation_selected = select_trades(validation, threshold, config["selection"])
            report["validation"] = metrics(validation_selected, config["windows"]["validation"], config["gates"]["validation"])
            if not validation_selected.empty:
                chosen = validation_selected.copy()
                chosen["stage"] = "validation"
                selections.append(chosen)
        else:
            report["validation"] = {"status": "NOT_EVALUATED_AFTER_CALIBRATION_FAILURE"}
        reports[family] = report
    survivors = [family for family, report in reports.items() if report["calibration"]["gate_pass"] and report["validation"].get("gate_pass", False)]
    return ({"contract_id": config["contract_id"], "families": reports, "surviving_specialists": survivors, "research_decision": "PASS" if survivors else "REJECT", "exam_status": "NOT_EVALUATED", "broker_action_authorized": False}, pd.concat(selections, ignore_index=True) if selections else pd.DataFrame())


def source_date(path: Path) -> str:
    part = path.name.split("-")[-1].split(".")[0]
    if len(part) != 8 or not part.isdigit():
        raise ValueError(f"Cannot parse DBN source date: {path.name}")
    return part
