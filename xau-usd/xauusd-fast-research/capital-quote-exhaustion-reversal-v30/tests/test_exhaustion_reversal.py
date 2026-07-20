from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from exhaustion_reversal import generate_candidates, load_config  # noqa: E402


def ticks(prices: list[float], step_ms: int = 100) -> pd.DataFrame:
    start = int(pd.Timestamp("2026-07-17T12:00:00Z").timestamp() * 1000)
    rows = []
    for index, mid in enumerate(prices):
        rows.append(
            {
                "tick_time_msc": start + index * step_ms,
                "bid": mid - 0.15,
                "ask": mid + 0.15,
                "spread_price": 0.30,
            }
        )
    return pd.DataFrame(rows)


def permissive_config() -> dict:
    config = deepcopy(load_config(ROOT))
    config["feature"].update(
        {
            "lookback_ms": 300,
            "maximum_boundary_quote_age_ms": 100,
            "maximum_internal_quote_gap_ms": 200,
            "minimum_nonzero_mid_updates": 3,
            "minimum_absolute_update_imbalance": 0.50,
            "minimum_absolute_displacement_price": 0.30,
            "arm_expiry_ms": 1000,
            "minimum_retracement_price": 0.15,
            "minimum_consecutive_counter_updates": 3,
            "post_trigger_refractory_ms": 1000,
        }
    )
    return config


def test_up_impulse_then_confirmed_retracement_produces_short() -> None:
    prices = [100.00, 100.05, 100.10, 100.20, 100.35, 100.40, 100.35, 100.30, 100.20]
    candidates, structural = generate_candidates(ticks(prices), permissive_config())
    assert structural["impulse_arm_count"] >= 1
    assert structural["raw_trigger_count"] == 1
    assert candidates["candidate_side"].tolist() == ["SHORT"]


def test_down_impulse_then_confirmed_retracement_produces_long() -> None:
    prices = [100.40, 100.35, 100.30, 100.20, 100.00, 99.90, 99.95, 100.00, 100.20]
    candidates, _ = generate_candidates(ticks(prices), permissive_config())
    assert candidates["candidate_side"].tolist() == ["LONG"]


def test_monotonic_impulse_does_not_create_reversal() -> None:
    prices = [100.00, 100.05, 100.10, 100.20, 100.35, 100.45, 100.55, 100.65]
    candidates, structural = generate_candidates(ticks(prices), permissive_config())
    assert structural["impulse_arm_count"] >= 1
    assert candidates.empty


def test_one_candidate_is_kept_per_four_hour_block() -> None:
    pattern = [100.00, 100.05, 100.10, 100.20, 100.35, 100.40, 100.35, 100.30, 100.20]
    frame = ticks(pattern)
    second = ticks(pattern)
    second["tick_time_msc"] += 60_000
    candidates, structural = generate_candidates(
        pd.concat([frame, second], ignore_index=True), permissive_config()
    )
    assert structural["raw_trigger_count"] == 2
    assert len(candidates) == 1
