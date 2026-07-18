from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from passive import (  # noqa: E402
    generate_manifest,
    load_config,
    signal_orders,
    simulate_pending_limit,
)


EXECUTION = {
    "maximum_entry_gap_minutes": 20,
    "maximum_horizon_gap_hours": 72,
    "maximum_entry_spread_r": 0.20,
    "maximum_research_risk_usd": 50.0,
    "ounces_at_lot_size": 1.0,
    "ticket_cost_usd": 0.0,
    "holding_cost_per_24h_usd": 0.0,
    "stress_slippage_r": 0.0,
}


def _arrays(
    *,
    ask_low: list[float],
    bid_low: list[float],
    bid_high: list[float] | None = None,
) -> dict[str, np.ndarray]:
    count = len(ask_low)
    starts = np.arange(count, dtype=np.int64) * 300_000_000_000
    bid_high_values = bid_high or [100.4] * count
    return {
        "starts": starts,
        "ends": starts + 300_000_000_000,
        "bid_open": np.array([100.1] * count),
        "bid_high": np.array(bid_high_values),
        "bid_low": np.array(bid_low),
        "bid_close": np.array([100.1] * count),
        "ask_open": np.array([100.3] * count),
        "ask_high": np.array([100.6] * count),
        "ask_low": np.array(ask_low),
        "ask_close": np.array([100.3] * count),
    }


def _signal_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "mid_close": [99.0, 101.0],
            "ask_close": [99.1, 101.1],
            "bid_close": [98.9, 100.9],
            "atr14": [1.0, 1.0],
            "regime": ["CHOP", "CHOP"],
            "hour": [10, 10],
            "vwap_deviation_atr": [-1.0, 1.0],
            "anchored_vwap": [100.0, 100.0],
        }
    )


def test_manifest_is_complete_unique_and_contiguous() -> None:
    manifest = generate_manifest(load_config(ROOT)["selection"])
    assert len(manifest) == 1000
    assert manifest["attempt_no"].tolist() == list(range(21120, 22120))
    assert manifest["variant_id"].is_unique
    assert manifest.groupby("mechanic").size().eq(100).all()


def test_buy_limit_requires_ask_touch_not_bid_touch() -> None:
    arrays = _arrays(ask_low=[100.2, 100.2], bid_low=[99.8, 99.8])
    outcome = simulate_pending_limit(
        arrays,
        signal_time_ns=0,
        direction=1,
        limit=100.0,
        target=101.0,
        risk=1.0,
        signal_spread=0.1,
        pending_expiry_hours=0.15,
        hold_hours=1.0,
        execution=EXECUTION,
    )
    assert outcome is None


def test_fill_bar_stop_is_charged() -> None:
    arrays = _arrays(ask_low=[99.9, 100.2], bid_low=[98.8, 100.0])
    outcome = simulate_pending_limit(
        arrays,
        signal_time_ns=0,
        direction=1,
        limit=100.0,
        target=101.0,
        risk=1.0,
        signal_spread=0.1,
        pending_expiry_hours=1.0,
        hold_hours=1.0,
        execution=EXECUTION,
    )
    assert outcome is not None
    assert outcome["exit_reason"] in (
        "FILL_BAR_GAP_STOP",
        "FILL_BAR_STOP_AMBIGUOUS",
    )
    assert outcome["gross_r"] <= -1.0


def test_fill_bar_target_is_not_credited() -> None:
    arrays = _arrays(
        ask_low=[99.9, 100.2],
        bid_low=[99.5, 100.0],
        bid_high=[101.5, 100.4],
    )
    outcome = simulate_pending_limit(
        arrays,
        signal_time_ns=0,
        direction=1,
        limit=100.0,
        target=101.0,
        risk=1.0,
        signal_spread=0.1,
        pending_expiry_hours=1.0,
        hold_hours=0.0,
        execution=EXECUTION,
    )
    assert outcome is not None
    assert outcome["exit_reason"] == "FIXED_HORIZON"
    assert outcome["gross_r"] < 1.0


def test_vwap_orders_are_passive_and_shock_is_excluded() -> None:
    frame = _signal_frame()
    params = {
        "deviation_atr": 0.6,
        "target_mode": "ANCHOR",
        "entry_offset_atr": 0.2,
        "stop_atr": 1.0,
        "target_r": 1.5,
        "pending_expiry_hours": 2.0,
        "hold_hours": 4,
        "hour_window": "ALL",
    }
    passive_execution = {
        "minimum_anchor_reward_r": 0.5,
        "maximum_anchor_reward_r": 4.0,
        "minimum_pending_distance_r": 0.01,
    }
    mask, direction, limit, target = signal_orders(
        frame, "CHOP_VWAP_PASSIVE_FADE", params, passive_execution
    )
    assert mask.all()
    assert direction.tolist() == [1, -1]
    assert limit.iloc[0] < frame["ask_close"].iloc[0]
    assert limit.iloc[1] > frame["bid_close"].iloc[1]
    assert target.eq(100.0).all()

    shock = frame.copy()
    shock["regime"] = "UNSAFE_SHOCK"
    shock_mask, _, _, _ = signal_orders(
        shock, "CHOP_VWAP_PASSIVE_FADE", params, passive_execution
    )
    assert not shock_mask.any()
