from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "mt5-compression-portability-v1" / "src" / "portability.py"


def _load_base() -> Any:
    name = "xau_mt5_compression_portability_base"
    spec = importlib.util.spec_from_file_location(name, BASE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load compression portability base from {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()


@dataclass(frozen=True)
class R1PortabilityRun:
    candidates: pd.DataFrame
    all_trades: pd.DataFrame
    policy_trades: pd.DataFrame
    source_m5: pd.DataFrame
    evidence: dict[str, Any]


def ema_trend_stack(
    frame: pd.DataFrame,
    fast_period: int,
    slow_period: int,
    slope_lag: int,
) -> pd.DataFrame:
    result = frame.copy()
    result["ema_fast"] = result["bid_close"].ewm(
        span=fast_period, adjust=False, min_periods=fast_period
    ).mean()
    result["ema_slow"] = result["bid_close"].ewm(
        span=slow_period, adjust=False, min_periods=slow_period
    ).mean()
    result["trend_up"] = (
        (result["bid_close"] > result["ema_fast"])
        & (result["ema_fast"] > result["ema_slow"])
        & (result["ema_fast"] >= result["ema_fast"].shift(slope_lag))
        & (result["ema_slow"] >= result["ema_slow"].shift(slope_lag))
    )
    result["supportive_up"] = (
        (result["bid_close"] > result["ema_fast"])
        & (result["ema_fast"] >= result["ema_fast"].shift(slope_lag))
    )
    return result


def _percentile_rank_last(window: np.ndarray) -> float:
    valid = window[np.isfinite(window)]
    if len(valid) != len(window) or not len(valid):
        return np.nan
    return float(100.0 * np.count_nonzero(valid <= valid[-1]) / len(valid))


def attach_r1_regime(
    m5: pd.DataFrame,
    d1: pd.DataFrame,
    h4: pd.DataFrame,
    signal: dict[str, Any],
    regime: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    minimum_rows = int(signal["minimum_m5_rows_per_calendar_bucket"])
    h1 = BASE.aggregate_calendar_bars(m5, 60, "H1", minimum_rows)
    h1["atr_h1"] = BASE.atr(h1, int(regime["h1_atr_period"]))
    h1["shock_h1"] = (
        (h1["bid_high"] - h1["bid_low"])
        >= float(regime["shock_h1_range_atr_multiple"]) * h1["atr_h1"]
    )

    fast = int(regime["fast_ema_period"])
    slow = int(regime["slow_ema_period"])
    lag = int(regime["slope_lag_bars"])
    d1_regime = ema_trend_stack(d1, fast, slow, lag)
    persistence = int(regime["d1_persistence_bars"])
    persistent = d1_regime["trend_up"].copy()
    for shift in range(1, persistence):
        persistent &= d1_regime["trend_up"].shift(shift).fillna(False).astype(bool)
    d1_regime["d1_trend_persistent_up"] = persistent
    shock_lookback = int(regime["shock_d1_atr_lookback"])
    d1_regime["shock_atr_percentile_d1"] = d1_regime["atr_d1"].rolling(
        shock_lookback, min_periods=shock_lookback
    ).apply(_percentile_rank_last, raw=True)
    d1_regime["shock_d1"] = d1_regime["shock_atr_percentile_d1"] >= float(
        regime["shock_d1_atr_percentile_min"]
    )

    h4_regime = ema_trend_stack(h4, fast, slow, lag)
    d1_columns = [
        "timestamp_utc",
        "d1_trend_persistent_up",
        "supportive_up",
        "shock_d1",
        "shock_atr_percentile_d1",
    ]
    enriched = pd.merge_asof(
        h4_regime.sort_values("timestamp_utc"),
        d1_regime[d1_columns].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
        suffixes=("_h4", "_d1"),
    )
    enriched = pd.merge_asof(
        enriched.sort_values("timestamp_utc"),
        h1[["timestamp_utc", "shock_h1"]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    enriched["regime_shock"] = enriched["shock_h1"].fillna(False) | enriched[
        "shock_d1"
    ].fillna(False)
    enriched["r1_regime_uptrend"] = (
        ~enriched["regime_shock"]
        & enriched["d1_trend_persistent_up"].fillna(False)
        & enriched["trend_up"].fillna(False)
    )
    enriched["r1_allowed"] = enriched["r1_regime_uptrend"] & enriched[
        "supportive_up_d1"
    ].fillna(False)
    return enriched, h1


def generate_r1_candidates(
    h4: pd.DataFrame, signal: dict[str, Any]
) -> pd.DataFrame:
    base = BASE.generate_candidates(h4, signal)
    if base.empty:
        return base
    regime = h4[
        [
            "timestamp_utc",
            "r1_allowed",
            "regime_shock",
            "d1_trend_persistent_up",
            "trend_up",
            "shock_atr_percentile_d1",
        ]
    ].rename(columns={"timestamp_utc": "signal_time", "trend_up": "h4_trend_up"})
    candidates = base.merge(regime, on="signal_time", how="left", validate="one_to_one")
    return candidates.loc[candidates["r1_allowed"].fillna(False)].reset_index(drop=True)


def run_portability(config: dict[str, Any]) -> R1PortabilityRun:
    m5, evidence = BASE.SHARED_DATA.load_m5(config)
    d1, h4 = BASE.prepare_signal_bars(m5, config["signal"])
    enriched, h1 = attach_r1_regime(
        m5, d1, h4, config["signal"], config["regime"]
    )
    candidates = generate_r1_candidates(enriched, config["signal"])
    candidate_ledger, all_trades = BASE.simulate_candidates(
        m5, candidates, config["execution"]
    )
    policies = [
        BASE.apply_policy(all_trades, policy_id, settings)
        for policy_id, settings in config["policies"].items()
    ]
    policy_trades = pd.concat(policies, ignore_index=True) if policies else pd.DataFrame()
    evidence = {
        **evidence,
        "d1_rows": int(len(d1)),
        "h1_rows": int(len(h1)),
        "h4_rows": int(len(h4)),
        "r1_candidate_rows": int(len(candidates)),
        "executable_candidate_rows": int(len(all_trades)),
    }
    return R1PortabilityRun(
        candidate_ledger, all_trades, policy_trades, m5, evidence
    )


stage_metrics = BASE.stage_metrics
evaluate_gate = BASE.evaluate_gate
