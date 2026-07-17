from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CHOP_SRC = ROOT / "chop-v1" / "src"
SHARED_DATA_PATH = ROOT / "independent-specialists-v1" / "src" / "data.py"
sys.path.insert(0, str(CHOP_SRC))

from backtest import run_cell  # noqa: E402
from data_adapter import aggregate_m30  # noqa: E402
from regime import attach_regime, classify_chop  # noqa: E402
from strategies import STRATEGY_IDS, clock_bars, rotation_signals  # noqa: E402


ROTATION = "CHOP_RANGE_ROTATION_CONTINUATION_V1"


def _load_shared_data() -> Any:
    name = "xau_chop_portability_shared_data"
    spec = importlib.util.spec_from_file_location(name, SHARED_DATA_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load shared data module from {SHARED_DATA_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SHARED_DATA = _load_shared_data()


@dataclass(frozen=True)
class PortabilityRun:
    signals: pd.DataFrame
    trades: pd.DataFrame
    source_m5: pd.DataFrame
    evidence: dict[str, Any]


def adapt_m5(source: pd.DataFrame, point_size: float) -> pd.DataFrame:
    frame = source.copy()
    required = {"tick_spread_max", "xau_tick_count"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Dukascopy feature cache is missing portability columns: {missing}")
    for column in ("bar_start_utc", "timestamp_utc"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], utc=True).astype("datetime64[ns, UTC]")
    spread_open = (frame["ask_open"] - frame["bid_open"]).clip(lower=0.0)
    spread_close = (frame["ask_close"] - frame["bid_close"]).clip(lower=0.0)
    frame["spread_open_points"] = spread_open / point_size
    frame["spread_close_points"] = spread_close / point_size
    frame["spread_median_points"] = (spread_open + spread_close) / (2.0 * point_size)
    frame["spread_p95_points"] = frame["tick_spread_max"].clip(lower=0.0) / point_size
    frame["volume_sum"] = frame["xau_tick_count"].astype(float)
    frame["broker"] = "dukascopy"
    frame["symbol"] = "XAUUSD"
    frame["timeframe"] = "M5"
    return frame


def run_portability(config: dict[str, Any]) -> PortabilityRun:
    source_m5, evidence = SHARED_DATA.load_m5(config)
    point_size = float(config["execution"]["point_size"])
    m5 = adapt_m5(source_m5, point_size)
    m30 = aggregate_m30(m5)
    m30["broker"] = "dukascopy"
    h4 = SHARED_DATA.aggregate_complete_bars(m5, 240, "H4")
    regime = classify_chop(h4, config["regime"])
    m30_regime = attach_regime(m30, regime.bars)
    m5_regime = attach_regime(m5, regime.bars)
    candidate_config = {
        "strategies": {
            "equilibrium": {"z": 2.0, "stop_atr": 1.25, "max_hold_hours": 12},
            "impulse": {"z": 2.25, "stop_buffer_atr": 0.25, "min_stop_atr": 0.5, "max_stop_atr": 2.0, "max_hold_hours": 9},
            "rotation": config["rotation"],
        }
    }
    all_candidates = rotation_signals(m30_regime, clock_bars(30), candidate_config["strategies"]["rotation"])
    if not all_candidates.empty and not all_candidates["strategy_id"].eq(ROTATION).all():
        raise AssertionError(f"Unexpected strategy ID outside frozen rotation family: {STRATEGY_IDS}")
    result = run_cell(
        m30_regime,
        all_candidates,
        "M30",
        int(config["execution"]["cooldown_hours"]),
        float(config["execution"]["stress_slippage_r"]),
        execution_bars=m5_regime,
    )
    trades = result.trades.copy()
    if not trades.empty:
        risk_usd = trades["initial_risk"] * float(config["execution"]["ounces"])
        holding_days = trades["holding_minutes"].clip(lower=0.0) / 1440.0
        extra_cost_r = (
            float(config["execution"]["ticket_cost_usd"])
            + holding_days * float(config["execution"]["holding_cost_per_24h_usd"])
        ) / risk_usd
        trades["extra_ticket_holding_cost_r"] = extra_cost_r
        trades["stress_net_r_before_extra_cost"] = trades["stress_net_r"]
        trades["stress_net_r"] = trades["stress_net_r"] - extra_cost_r
        trades["all_in_stress_cost_r"] = trades["stress_cost_r"] + extra_cost_r
    evidence = {
        **evidence,
        "m30_rows": int(len(m30)),
        "h4_rows": int(len(h4)),
        "chop_episodes": int(len(regime.episodes)),
        "signal_rows": int(len(result.signals)),
        "trade_rows": int(len(trades)),
    }
    return PortabilityRun(result.signals, trades, m5, evidence)


def profit_factor(values: pd.Series) -> float | None:
    positive = float(values.loc[values > 0].sum())
    negative = float(-values.loc[values < 0].sum())
    if negative == 0:
        return None if positive == 0 else float("inf")
    return positive / negative


def drawdown(values: pd.Series) -> float:
    equity = values.fillna(0.0).cumsum()
    return float((equity.cummax() - equity).max()) if len(equity) else 0.0


def stage_metrics(trades: pd.DataFrame, source_m5: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, top_n: int) -> dict[str, Any]:
    stage = trades.loc[(trades["entry_time"] >= start) & (trades["entry_time"] < end)].copy()
    source_days = int(
        source_m5.loc[
            (source_m5["bar_start_utc"] >= start) & (source_m5["bar_start_utc"] < end),
            "bar_start_utc",
        ].dt.date.nunique()
    )
    baseline = stage["net_r"].astype(float) if not stage.empty else pd.Series(dtype=float)
    stress = stage["stress_net_r"].astype(float) if not stage.empty else pd.Series(dtype=float)
    years = (
        stage.assign(year=stage["entry_time"].dt.year).groupby("year")["stress_net_r"].sum()
        if not stage.empty else pd.Series(dtype=float)
    )
    removed = stress.drop(stress.nlargest(min(top_n, len(stress))).index) if len(stress) else stress
    return {
        "trades": int(len(stage)),
        "source_days": source_days,
        "trades_per_source_day": len(stage) / source_days if source_days else 0.0,
        "net_r": float(baseline.sum()),
        "profit_factor": profit_factor(baseline),
        "average_r": float(baseline.mean()) if len(baseline) else 0.0,
        "stress_net_r": float(stress.sum()),
        "stress_profit_factor": profit_factor(stress),
        "average_stress_r": float(stress.mean()) if len(stress) else 0.0,
        "stress_drawdown_r": drawdown(stress),
        "positive_active_year_share": float((years > 0).mean()) if len(years) else 0.0,
        "top_winners_removed_stress_net_r": float(removed.sum()),
    }


def evaluate_gate(value: dict[str, Any], gate: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    checks = {
        "minimum_trades": value["trades"] >= int(gate["minimum_trades"]),
        "minimum_trades_per_source_day": value["trades_per_source_day"] >= float(gate["minimum_trades_per_source_day"]),
        "minimum_pf": value["profit_factor"] is not None and value["profit_factor"] >= float(gate["minimum_pf"]),
        "minimum_stress_pf": value["stress_profit_factor"] is not None and value["stress_profit_factor"] >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": value["average_stress_r"] >= float(gate["minimum_average_stress_r"]),
        "maximum_drawdown_r": value["stress_drawdown_r"] <= float(gate["maximum_drawdown_r"]),
        "top_winners_removed_positive": value["top_winners_removed_stress_net_r"] > 0,
    }
    if "minimum_positive_active_year_share" in gate:
        checks["minimum_positive_active_year_share"] = value["positive_active_year_share"] >= float(
            gate["minimum_positive_active_year_share"]
        )
    return all(checks.values()), checks
