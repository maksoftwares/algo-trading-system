from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from spot_labels import label_candidates
from tbbo_features import (
    add_flow_features,
    aggregate_trade_seconds,
    generate_trade_candidates,
    load_trades_dbn,
)


CANDIDATE_COLUMNS = [
    "candidate_id",
    "feature_time_utc",
    "instrument_id",
    "family",
    "direction",
    "contract_volume_5s",
    "flow_imbalance_5s",
    "flow_imbalance_30s",
    "volume_share_5s_of_60s",
    "price_impulse_ticks_5s",
]


def discover_dbn_files(job_directory: Path) -> list[Path]:
    if not job_directory.is_dir():
        raise FileNotFoundError(f"Databento job directory is missing: {job_directory}")
    files = sorted(
        path
        for path in job_directory.rglob("*")
        if path.is_file() and (path.name.endswith(".dbn") or path.name.endswith(".dbn.zst"))
    )
    if not files:
        raise FileNotFoundError(f"No DBN data files found under: {job_directory}")
    return files


def filter_session_with_warmup(
    events: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    frame = events.copy()
    if "ts_event" not in frame.columns and frame.index.name == "ts_event":
        frame = frame.reset_index()
    if "ts_event" not in frame.columns:
        raise ValueError("Trade input is missing ts_event.")
    frame["ts_event"] = pd.to_datetime(frame["ts_event"], utc=True)
    local = frame["ts_event"].dt.tz_convert(config["session"]["timezone"])
    seconds = local.dt.hour * 3600 + local.dt.minute * 60 + local.dt.second
    start_hour, start_minute = (int(value) for value in config["session"]["start"].split(":"))
    end_hour, end_minute = (int(value) for value in config["session"]["end"].split(":"))
    start = start_hour * 3600 + start_minute * 60 - int(config["instrument_warmup_seconds"])
    end = end_hour * 3600 + end_minute * 60
    if start < 0 or end <= start:
        raise ValueError("The locked session must fit within one local calendar day.")
    return frame.loc[(seconds >= start) & (seconds < end)].copy()


def candidates_for_events(events: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    session_events = filter_session_with_warmup(events, config)
    if session_events.empty:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)
    seconds = aggregate_trade_seconds(session_events, tick_size=float(config["tick_size"]))
    features = add_flow_features(seconds, config)
    candidates = generate_trade_candidates(features, config)
    if candidates.empty:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)
    decision_ms = candidates["feature_time_utc"].astype("int64") // 1_000_000
    candidates.insert(
        0,
        "candidate_id",
        candidates["family"].astype(str)
        + ":"
        + decision_ms.astype(str)
        + ":"
        + candidates["direction"].astype(str)
        + ":"
        + candidates["instrument_id"].astype(str),
    )
    if candidates["candidate_id"].duplicated().any():
        raise ValueError("Candidate generation produced duplicate deterministic IDs.")
    return candidates[CANDIDATE_COLUMNS].reset_index(drop=True)


def process_candidate_file(
    source: Path,
    destination: Path,
    config: Mapping[str, Any],
    *,
    loader: Callable[[Path], pd.DataFrame] = load_trades_dbn,
) -> pd.DataFrame:
    candidates = candidates_for_events(loader(source), config)
    destination.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_parquet(destination, index=False)
    return candidates


def process_label_file(
    candidates_path: Path,
    destination: Path,
    *,
    atr_source: Any,
    tick_store: Any,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    candidates = pd.read_parquet(candidates_path)
    if candidates.empty:
        labels = pd.DataFrame()
    else:
        labels = label_candidates(
            candidates,
            atr_source=atr_source,
            tick_store=tick_store,
            config=config,
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    labels.to_parquet(destination, index=False)
    return labels


def _profit_factor(values: pd.Series) -> float | None:
    positive = float(values.loc[values > 0].sum())
    negative = float(-values.loc[values < 0].sum())
    if negative == 0:
        return None
    return positive / negative


def _maximum_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    equity = values.cumsum()
    peaks = equity.cummax().clip(lower=0.0)
    return float((peaks - equity).max())


def _maximum_consecutive_losses(values: pd.Series) -> int:
    maximum = current = 0
    for value in values:
        current = current + 1 if value < 0 else 0
        maximum = max(maximum, current)
    return maximum


def _trading_days(bounds: Sequence[str]) -> int:
    start = np.datetime64(pd.Timestamp(bounds[0]).date())
    end = np.datetime64(pd.Timestamp(bounds[1]).date())
    return int(np.busday_count(start, end))


def summarize_group(
    rows: pd.DataFrame,
    *,
    split: str,
    family: str,
    trading_days: int,
    gates: Mapping[str, Any],
) -> dict[str, Any]:
    ordered = rows.sort_values(["exit_time_utc", "candidate_id"], kind="stable")
    baseline = ordered["baseline_net_pnl_usd"].astype(float)
    stress = ordered["stress_net_pnl_usd"].astype(float)
    stress_r = ordered["stress_net_r"].astype(float)
    trades = len(ordered)
    baseline_pf_infinite = bool((baseline > 0).any() and not (baseline < 0).any())
    stress_pf_infinite = bool((stress > 0).any() and not (stress < 0).any())
    metrics = {
        "split": split,
        "family": family,
        "trades": trades,
        "trading_days": trading_days,
        "trades_per_trading_day": trades / trading_days if trading_days else 0.0,
        "baseline_net_pnl_usd": float(baseline.sum()),
        "stress_net_pnl_usd": float(stress.sum()),
        "profit_factor": _profit_factor(baseline),
        "profit_factor_is_infinite": baseline_pf_infinite,
        "stress_profit_factor": _profit_factor(stress),
        "stress_profit_factor_is_infinite": stress_pf_infinite,
        "average_stress_r": float(stress_r.mean()) if trades else None,
        "win_rate_after_stress": float((stress > 0).mean()) if trades else None,
        "maximum_closed_trade_drawdown_usd": _maximum_drawdown(stress),
        "maximum_consecutive_losses": _maximum_consecutive_losses(stress),
    }
    finite_pf = float("inf") if baseline_pf_infinite else (metrics["profit_factor"] or 0.0)
    finite_stress_pf = (
        float("inf") if stress_pf_infinite else (metrics["stress_profit_factor"] or 0.0)
    )
    metrics["gate_pass"] = bool(
        trades >= int(gates["minimum_trades"])
        and finite_pf >= float(gates["minimum_profit_factor"])
        and finite_stress_pf >= float(gates["minimum_stress_profit_factor"])
        and (metrics["average_stress_r"] or 0.0) >= float(gates["minimum_average_stress_r"])
        and metrics["trades_per_trading_day"]
        >= float(gates["minimum_trades_per_trading_day"])
    )
    return metrics


def build_evidence_report(labels: pd.DataFrame, config: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "candidate_id",
        "family",
        "split",
        "status",
        "exit_time_utc",
        "baseline_net_pnl_usd",
        "stress_net_pnl_usd",
        "stress_net_r",
    }
    missing = sorted(required - set(labels.columns))
    if missing:
        raise ValueError(f"Labels are missing evidence columns: {missing}")
    if labels["candidate_id"].duplicated().any():
        raise ValueError("Labels contain duplicate candidate IDs.")
    resolved = labels.loc[labels["status"] == "RESOLVED"].copy()
    summaries: list[dict[str, Any]] = []
    families = sorted(config["families"])
    for split, bounds in config["splits"].items():
        split_rows = resolved.loc[resolved["split"] == split]
        days = _trading_days(bounds)
        for family in [*families, "ALL"]:
            group = split_rows if family == "ALL" else split_rows.loc[split_rows["family"] == family]
            summaries.append(
                summarize_group(
                    group,
                    split=split,
                    family=family,
                    trading_days=days,
                    gates=config["gates"][split],
                )
            )
    survivors = []
    for family in families:
        family_rows = [row for row in summaries if row["family"] == family]
        if len(family_rows) == len(config["splits"]) and all(row["gate_pass"] for row in family_rows):
            survivors.append(family)
    status_counts = {
        str(key): int(value) for key, value in labels["status"].value_counts(dropna=False).items()
    }
    reason_counts = {
        str(key): int(value)
        for key, value in labels.loc[labels["status"] != "RESOLVED", "reason"]
        .value_counts(dropna=False)
        .items()
    }
    return {
        "contract_id": config["contract_id"],
        "label_rows": len(labels),
        "status_counts": status_counts,
        "ineligible_reason_counts": reason_counts,
        "summaries": summaries,
        "surviving_specialists": survivors,
        "research_decision": "PASS" if survivors else "REJECT",
        "broker_action_authorized": False,
    }
