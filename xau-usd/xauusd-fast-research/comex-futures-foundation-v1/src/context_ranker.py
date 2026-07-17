from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


FEATURE_COLUMNS = [
    "direction_sign",
    "dir_flow_imbalance_5s",
    "dir_flow_imbalance_30s",
    "absolute_flow_imbalance_5s",
    "absolute_flow_imbalance_30s",
    "volume_share_5s_of_60s",
    "dir_price_impulse_ticks_5s",
    "absolute_price_impulse_ticks_5s",
    "log_contract_volume_5s",
    "dir_spot_return_5m_atr",
    "dir_spot_return_15m_atr",
    "dir_spot_return_60m_atr",
    "dir_ema_gap_atr",
    "dir_range_location_60m",
    "dir_tick_imbalance_5m",
    "dir_tick_imbalance_15m",
    "dir_microprice_edge_atr",
    "spot_price_efficiency_5m",
    "spot_atr_ratio",
    "spot_quote_intensity_ratio",
    "spot_spread_atr",
    "spot_body_fraction",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
]


def load_partitions(directory: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(directory.glob("*.parquet")):
        frame = pd.read_parquet(path)
        if not frame.empty:
            frames.append(frame)
    if not frames:
        raise ValueError(f"No nonempty Parquet partitions found under: {directory}")
    return pd.concat(frames, ignore_index=True)


def prepare_spot_context(m5: pd.DataFrame, *, bar_width_ms: int = 300_000) -> pd.DataFrame:
    required = {
        "timestamp_ms",
        "mid_high",
        "mid_low",
        "mid_close",
        "atr",
        "atr_ratio",
        "quote_intensity_ratio",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "tick_microprice_edge_last",
        "price_efficiency_5m",
        "tick_spread_last",
        "body_fraction",
    }
    missing = sorted(required - set(m5.columns))
    if missing:
        raise ValueError(f"M5 cache is missing context columns: {missing}")
    frame = m5.copy().sort_values("timestamp_ms", kind="stable").reset_index(drop=True)
    if frame["timestamp_ms"].duplicated().any():
        raise ValueError("M5 context contains duplicate bar starts.")
    frame["available_time_utc"] = pd.to_datetime(
        frame["timestamp_ms"].astype("int64") + int(bar_width_ms), unit="ms", utc=True
    )
    atr = frame["atr"].replace(0.0, np.nan)
    for bars, name in ((1, "5m"), (3, "15m"), (12, "60m")):
        frame[f"spot_return_{name}_atr"] = (frame["mid_close"] - frame["mid_close"].shift(bars)) / atr
    ema_fast = frame["mid_close"].ewm(span=12, adjust=False, min_periods=12).mean()
    ema_slow = frame["mid_close"].ewm(span=48, adjust=False, min_periods=48).mean()
    frame["ema_gap_atr"] = (ema_fast - ema_slow) / atr
    low = frame["mid_low"].rolling(12, min_periods=12).min()
    high = frame["mid_high"].rolling(12, min_periods=12).max()
    frame["range_location_60m"] = (frame["mid_close"] - low) / (high - low).replace(0.0, np.nan)
    frame["microprice_edge_atr"] = frame["tick_microprice_edge_last"] / atr
    frame["spot_spread_atr"] = frame["tick_spread_last"] / atr
    return frame


def join_context(candidates: pd.DataFrame, labels: pd.DataFrame, m5: pd.DataFrame) -> pd.DataFrame:
    label_columns = [
        "candidate_id",
        "family",
        "direction",
        "status",
        "entry_time_utc",
        "exit_time_utc",
        "stress_net_pnl_usd",
        "stress_net_r",
    ]
    missing = sorted(set(label_columns) - set(labels.columns))
    if missing:
        raise ValueError(f"Labels are missing ranker columns: {missing}")
    resolved = labels.loc[labels["status"] == "RESOLVED", label_columns]
    merged = candidates.merge(
        resolved,
        on=["candidate_id", "family", "direction"],
        how="inner",
        validate="one_to_one",
    )
    merged["feature_time_utc"] = pd.to_datetime(merged["feature_time_utc"], utc=True)
    spot = prepare_spot_context(m5)
    joined = pd.merge_asof(
        merged.sort_values("feature_time_utc", kind="stable"),
        spot.sort_values("available_time_utc", kind="stable"),
        left_on="feature_time_utc",
        right_on="available_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    if (joined["available_time_utc"] > joined["feature_time_utc"]).any():
        raise ValueError("Spot context join used an incomplete M5 bar.")
    sign = joined["direction"].map({"LONG": 1.0, "SHORT": -1.0})
    joined["direction_sign"] = sign
    joined["dir_flow_imbalance_5s"] = sign * joined["flow_imbalance_5s"]
    joined["dir_flow_imbalance_30s"] = sign * joined["flow_imbalance_30s"]
    joined["absolute_flow_imbalance_5s"] = joined["flow_imbalance_5s"].abs()
    joined["absolute_flow_imbalance_30s"] = joined["flow_imbalance_30s"].abs()
    joined["dir_price_impulse_ticks_5s"] = sign * joined["price_impulse_ticks_5s"]
    joined["absolute_price_impulse_ticks_5s"] = joined["price_impulse_ticks_5s"].abs()
    joined["log_contract_volume_5s"] = np.log1p(joined["contract_volume_5s"])
    for source, output in (
        ("spot_return_5m_atr", "dir_spot_return_5m_atr"),
        ("spot_return_15m_atr", "dir_spot_return_15m_atr"),
        ("spot_return_60m_atr", "dir_spot_return_60m_atr"),
        ("ema_gap_atr", "dir_ema_gap_atr"),
        ("tick_imbalance_5m", "dir_tick_imbalance_5m"),
        ("tick_imbalance_15m", "dir_tick_imbalance_15m"),
        ("microprice_edge_atr", "dir_microprice_edge_atr"),
    ):
        joined[output] = sign * joined[source]
    joined["dir_range_location_60m"] = np.where(
        sign > 0, joined["range_location_60m"], 1.0 - joined["range_location_60m"]
    )
    joined["spot_price_efficiency_5m"] = joined["price_efficiency_5m"]
    joined["spot_atr_ratio"] = joined["atr_ratio"]
    joined["spot_quote_intensity_ratio"] = joined["quote_intensity_ratio"]
    joined["spot_body_fraction"] = joined["body_fraction"]
    local = joined["feature_time_utc"].dt.tz_convert("America/New_York")
    hour = local.dt.hour + local.dt.minute / 60.0
    weekday = local.dt.weekday
    joined["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    joined["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    joined["weekday_sin"] = np.sin(2.0 * np.pi * weekday / 7.0)
    joined["weekday_cos"] = np.cos(2.0 * np.pi * weekday / 7.0)
    finite = np.isfinite(joined[FEATURE_COLUMNS].to_numpy(dtype=float)).all(axis=1)
    return joined.loc[finite].sort_values("feature_time_utc", kind="stable").reset_index(drop=True)


def _profit_factor(values: pd.Series) -> float | None:
    gains = float(values.loc[values > 0].sum())
    losses = float(-values.loc[values < 0].sum())
    return gains / losses if losses else None


def _drawdown(values: pd.Series) -> float:
    equity = values.cumsum()
    return float((equity.cummax().clip(lower=0.0) - equity).max()) if len(equity) else 0.0


def select_trades(scored: pd.DataFrame, threshold: float, config: Mapping[str, Any]) -> pd.DataFrame:
    eligible = scored.loc[scored["model_score"] >= threshold].sort_values(
        ["entry_time_utc", "model_score"], ascending=[True, False], kind="stable"
    )
    accepted = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    daily: dict[Any, int] = {}
    for _, row in eligible.iterrows():
        entry = pd.Timestamp(row["entry_time_utc"])
        exit_time = pd.Timestamp(row["exit_time_utc"])
        day = entry.date()
        if entry < position_until or entry < cooldown_until:
            continue
        if daily.get(day, 0) >= int(config["maximum_trades_per_family_day"]):
            continue
        accepted.append(row)
        position_until = exit_time
        cooldown_until = exit_time + pd.offsets.Minute(int(float(config["cooldown_minutes"])))
        daily[day] = daily.get(day, 0) + 1
    return pd.DataFrame(accepted)


def metrics(trades: pd.DataFrame, bounds: list[str], gate: Mapping[str, Any]) -> dict[str, Any]:
    values = trades["stress_net_r"].astype(float) if not trades.empty else pd.Series(dtype=float)
    days = int(np.busday_count(np.datetime64(pd.Timestamp(bounds[0]).date()), np.datetime64(pd.Timestamp(bounds[1]).date())))
    removed = values.drop(values.nlargest(min(int(gate["top_winners_removed"]), len(values))).index)
    pf = _profit_factor(values)
    result = {
        "trades": len(values),
        "trades_per_day": len(values) / days if days else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_profit_factor": pf,
        "average_stress_r": float(values.mean()) if len(values) else None,
        "maximum_drawdown_r": _drawdown(values),
        "top_winners_removed_stress_net_r": float(removed.sum()),
    }
    result["gate_pass"] = bool(
        result["trades"] >= int(gate["minimum_trades"])
        and result["trades_per_day"] >= float(gate["minimum_trades_per_day"])
        and (pf or 0.0) >= float(gate["minimum_stress_profit_factor"])
        and (result["average_stress_r"] or 0.0) >= float(gate["minimum_average_stress_r"])
        and result["maximum_drawdown_r"] <= float(gate["maximum_drawdown_r"])
        and result["top_winners_removed_stress_net_r"] > 0
    )
    return result


def run_ranker(dataset: pd.DataFrame, config: Mapping[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    exam_start = pd.Timestamp(config["windows"]["exam"][0])
    if (dataset["feature_time_utc"] >= exam_start).any():
        raise ValueError("Context ranker v1 refuses exam rows.")
    reports: dict[str, Any] = {}
    selections = []
    for family in sorted(dataset["family"].unique()):
        rows = dataset.loc[dataset["family"] == family]
        windows = {
            name: rows.loc[
                (rows["feature_time_utc"] >= pd.Timestamp(bounds[0]))
                & (rows["feature_time_utc"] < pd.Timestamp(bounds[1]))
            ].copy()
            for name, bounds in config["windows"].items()
            if name != "exam"
        }
        fit = windows["fit"]
        calibration = windows["calibration"]
        validation = windows["validation"]
        model_parameters = {
            key: value for key, value in config["model"].items() if key != "calibration_quantile"
        }
        model = HistGradientBoostingRegressor(**model_parameters)
        model.fit(fit[FEATURE_COLUMNS], fit["stress_net_r"])
        calibration["model_score"] = model.predict(calibration[FEATURE_COLUMNS])
        threshold = max(
            0.0,
            float(np.quantile(calibration["model_score"], config["model"]["calibration_quantile"])),
        )
        calibration_selected = select_trades(calibration, threshold, config["selection"])
        calibration_metrics = metrics(
            calibration_selected, config["windows"]["calibration"], config["gates"]["calibration"]
        )
        family_report: dict[str, Any] = {
            "fit_rows": len(fit),
            "calibration_rows": len(calibration),
            "threshold": threshold,
            "calibration": calibration_metrics,
            "validation_decision_eligible": calibration_metrics["gate_pass"],
        }
        if not calibration_selected.empty:
            selected = calibration_selected.copy()
            selected["stage"] = "calibration"
            selections.append(selected)
        if calibration_metrics["gate_pass"]:
            validation["model_score"] = model.predict(validation[FEATURE_COLUMNS])
            validation_selected = select_trades(validation, threshold, config["selection"])
            validation_metrics = metrics(
                validation_selected, config["windows"]["validation"], config["gates"]["validation"]
            )
            family_report["validation"] = validation_metrics
            if not validation_selected.empty:
                selected = validation_selected.copy()
                selected["stage"] = "validation"
                selections.append(selected)
        else:
            family_report["validation"] = {"status": "NOT_EVALUATED_AFTER_CALIBRATION_FAILURE"}
        reports[family] = family_report
    survivors = [
        family
        for family, report in reports.items()
        if report["calibration"]["gate_pass"] and report["validation"].get("gate_pass", False)
    ]
    return (
        {
            "contract_id": config["contract_id"],
            "families": reports,
            "surviving_specialists": survivors,
            "research_decision": "PASS" if survivors else "REJECT",
            "exam_status": "NOT_EVALUATED",
            "broker_action_authorized": False,
        },
        pd.concat(selections, ignore_index=True) if selections else pd.DataFrame(),
    )
