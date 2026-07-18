from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
from typing import Any

import pandas as pd


RESEARCH_ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = RESEARCH_ROOT / "chop-m30-dukascopy-portability-v1" / "src" / "portability.py"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_module("xau_chop_m5_highvol_base_portability", BASE_PATH)

ROTATION = "CHOP_RANGE_ROTATION_CONTINUATION_V1"
HIGH_VOL = "HIGH_VOL_CHOP"


@dataclass(frozen=True)
class PortabilityRun:
    signals: pd.DataFrame
    trades: pd.DataFrame
    source_m5: pd.DataFrame
    evidence: dict[str, Any]


def select_candidate(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()
    if not candidates["strategy_id"].eq(ROTATION).all():
        raise ValueError("Unexpected strategy outside the fixed rotation family")
    selected = candidates.loc[candidates["volatility_subtype"].eq(HIGH_VOL)].copy()
    if not selected.empty and not selected["volatility_subtype"].eq(HIGH_VOL).all():
        raise AssertionError("Non-high-volatility subtype escaped the fixed filter")
    return selected.sort_values(["signal_time", "direction"], kind="mergesort")


def run_portability(config: dict[str, Any]) -> PortabilityRun:
    source_m5, evidence = BASE.SHARED_DATA.load_m5(config)
    point_size = float(config["execution"]["point_size"])
    m5 = BASE.adapt_m5(source_m5, point_size)
    h4 = BASE.SHARED_DATA.aggregate_complete_bars(m5, 240, "H4")
    regime = BASE.classify_chop(h4, config["regime"])
    m5_regime = BASE.attach_regime(m5, regime.bars)
    candidates = BASE.rotation_signals(
        m5_regime,
        BASE.clock_bars(5),
        config["rotation"],
    )
    selected = select_candidate(candidates)
    result = BASE.run_cell(
        m5_regime,
        selected,
        "M5",
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
        "m5_rows": int(len(m5)),
        "h4_rows": int(len(h4)),
        "chop_episodes": int(len(regime.episodes)),
        "all_rotation_signal_rows": int(len(candidates)),
        "highvol_rotation_signal_rows": int(len(selected)),
        "ledger_signal_rows": int(len(result.signals)),
        "trade_rows": int(len(trades)),
    }
    return PortabilityRun(result.signals, trades, m5, evidence)


stage_metrics = BASE.stage_metrics
evaluate_gate = BASE.evaluate_gate
