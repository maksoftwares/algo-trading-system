from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from absorption_release import generate_candidates, load_config  # noqa: E402


def ticks(prices: list[float], step_ms: int = 100) -> pd.DataFrame:
    start = int(pd.Timestamp("2026-07-17T12:00:00Z").timestamp() * 1000)
    return pd.DataFrame(
        {
            "tick_time_msc": [start + index * step_ms for index in range(len(prices))],
            "bid": [price - 0.15 for price in prices],
            "ask": [price + 0.15 for price in prices],
            "spread_price": [0.30] * len(prices),
        }
    )


def permissive_config() -> dict:
    config = deepcopy(load_config(ROOT))
    config["feature"].update(
        {
            "absorption_lookback_ms": 700,
            "maximum_internal_quote_gap_ms": 200,
            "minimum_nonzero_mid_updates": 5,
            "maximum_absolute_update_imbalance": 0.20,
            "maximum_absorption_range_price": 0.20,
            "arm_expiry_ms": 1000,
            "minimum_release_price": 0.30,
            "post_trigger_refractory_ms": 1000,
        }
    )
    return config


def test_balanced_absorption_then_up_release_produces_long() -> None:
    prices = [100.00, 100.05, 100.00, 100.05, 100.00, 100.05, 100.00, 100.05, 100.40]
    candidates, structural = generate_candidates(ticks(prices), permissive_config())
    assert structural["absorption_arm_count"] >= 1
    assert candidates["candidate_side"].tolist() == ["LONG"]


def test_balanced_absorption_without_release_stays_empty() -> None:
    prices = [100.00, 100.05, 100.00, 100.05, 100.00, 100.05, 100.00, 100.05]
    candidates, structural = generate_candidates(ticks(prices), permissive_config())
    assert structural["absorption_arm_count"] >= 1
    assert candidates.empty
