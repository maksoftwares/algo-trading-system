from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd

import campaign


RESEARCH_ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DATA = load_module(
    "macro_regime_routing_data",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "data.py",
)
REGIMES = load_module(
    "macro_regime_routing_regimes",
    RESEARCH_ROOT / "independent-specialists-v1" / "src" / "research.py",
)
ADAPTIVE = load_module(
    "macro_regime_routing_adaptive",
    RESEARCH_ROOT / "adaptive-h4-specialists-v1" / "src" / "adaptive.py",
)
FEATURES = load_module(
    "macro_regime_routing_features",
    RESEARCH_ROOT / "m15-regime-target-campaign-v1" / "src" / "campaign.py",
)
MACRO_DATA = load_module(
    "macro_regime_routing_macro_data",
    RESEARCH_ROOT / "intraday-macro-specialists-v1" / "src" / "data.py",
)
CLOCK = load_module(
    "macro_regime_routing_clock",
    RESEARCH_ROOT / "m15-regime-target-campaign-v2" / "src" / "correction.py",
)
ROUTER = load_module(
    "macro_regime_routing_execution",
    RESEARCH_ROOT / "walkforward-state-action-router-v1" / "src" / "router.py",
)
SCORE = load_module(
    "macro_regime_routing_score",
    RESEARCH_ROOT / "regime-mechanism-campaign-v1" / "src" / "campaign.py",
)


@dataclass(frozen=True)
class Foundation:
    decisions: pd.DataFrame
    execution_frame: pd.DataFrame
    arrays: dict[str, np.ndarray]
    evidence: dict[str, Any]


def load_foundation(config: Mapping[str, Any]) -> Foundation:
    bundle = DATA.load_bundle(dict(config))
    execution_frame = FEATURES.prepare_features(
        bundle.bars["M15"],
        bundle.bars["H4"],
        config,
        ADAPTIVE,
        REGIMES,
    )
    macro_m15, macro_evidence = MACRO_DATA.load_macro_m15(dict(config))
    decisions = campaign.enrich_frame(execution_frame, macro_m15, config)
    arrays = CLOCK.execution_arrays(execution_frame)
    if decisions.empty:
        raise ValueError("No exact macro-regime decisions are available")
    mapped = decisions["execution_index"].to_numpy(dtype=np.int64)
    if np.any(mapped < 0) or np.any(mapped >= len(execution_frame)):
        raise ValueError("Decision-to-execution mapping escaped the gold frame")
    mapped_times = execution_frame["timestamp_utc"].iloc[mapped].reset_index(drop=True)
    decision_times = decisions["timestamp_utc"].reset_index(drop=True)
    if not mapped_times.equals(decision_times):
        raise ValueError("Decision-to-execution timestamp mapping is not exact")
    next_gaps = (arrays["starts"][1:] - arrays["signals"][:-1]) / 60_000_000_000
    if np.any(next_gaps < 0.0):
        raise ValueError("Negative next-bar gap in the execution frame")
    evidence = {
        "gold": bundle.evidence,
        "macro": macro_evidence,
        "execution_rows": int(len(execution_frame)),
        "decision_rows": int(len(decisions)),
        "decision_start": decisions["timestamp_utc"].min().isoformat(),
        "decision_end": decisions["timestamp_utc"].max().isoformat(),
        "minimum_next_bar_gap_minutes": float(next_gaps.min()),
        "maximum_next_bar_gap_minutes": float(next_gaps.max()),
    }
    return Foundation(decisions, execution_frame, arrays, evidence)
