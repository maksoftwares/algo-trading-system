from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import replication  # noqa: E402


def _config() -> dict:
    return json.loads(
        (ROOT / "config" / "macro_transition_proxy_replication_v2.json").read_text(
            encoding="utf-8"
        )
    )


def test_candidate_is_exact_v1_attempt_23925() -> None:
    candidate = _config()["candidate"]
    assert candidate["source_attempt_no"] == 23925
    assert candidate["source_variant_id"] == "00e072837bf6f6e2"
    assert candidate["parameters"] == {
        "body_min": 0.2,
        "geometry_id": "T_BALANCED",
        "gold_horizon": "H1",
        "hour_window": "ALL",
        "macro_key": "H1_D2",
        "maximum_alignment_atr": 0.25,
        "pressure_min": 0.5,
        "require_confirmation": False,
        "transition_age_max": 48,
    }


def _decision_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dxy_pressure_H1_D2": [1.0, 1.0],
            "bond_pressure_H1_D2": [1.1, 1.1],
            "gold_return_H1_atr": [0.0, 0.0],
            "body": [0.3, 0.3],
            "candle_direction": [-1, -1],
            "regime": ["TRANSITION_UNKNOWN", "UNSAFE_SHOCK"],
            "hour_utc": [15, 15],
            "atr14": [2.0, 2.0],
            "transition_age_m15": [12, 12],
            "last_resolved_regime": ["TREND_UP", "TREND_UP"],
            "ancestry_direction": [1, 1],
            "execution_index": [10, 11],
        }
    )


def test_candidate_abstains_in_shock() -> None:
    row = replication.fixed_manifest_row(_config())
    parameters = json.loads(row.parameters_json)
    mask, direction = replication.V1.signal_mask_direction(
        _decision_frame(), row.mechanic, parameters
    )
    assert mask.tolist() == [True, False]
    assert direction.tolist() == [1, 1]


def test_unique_pool_does_not_double_count_same_gold_event() -> None:
    frame = pd.DataFrame(
        {
            "proxy_symbol": ["TLTUSD", "IEFUSD", "TLTUSD"],
            "signal_time": pd.to_datetime(
                ["2018-01-01T12:00:00Z", "2018-01-01T12:00:00Z", "2018-01-02T12:00:00Z"]
            ),
            "entry_time": pd.to_datetime(
                ["2018-01-01T12:15:00Z", "2018-01-01T12:15:00Z", "2018-01-02T12:15:00Z"]
            ),
            "direction_sign": [1, 1, -1],
            "stress_net_r": [1.0, 1.0, -0.5],
        }
    )
    unique, overlap = replication.unique_pooled_trades(frame)
    assert overlap == 1
    assert len(unique) == 2
    assert unique["stress_net_r"].sum() == pytest.approx(0.5)


def test_closed_drawdown_includes_initial_equity() -> None:
    assert replication.closed_drawdown(pd.Series([-1.0, 2.0, -0.5])) == pytest.approx(1.0)


def test_proxy_gates_require_every_registered_condition() -> None:
    gates = _config()["gates"]
    summary = {
        "trades": 8,
        "stress_net_r": 1.0,
        "stress_profit_factor": 1.2,
        "average_stress_r": 0.10,
        "top_winners_removed_stress_net_r": 0.1,
        "closed_drawdown_r": 2.0,
    }
    assert all(replication.proxy_gate_checks(summary, gates).values())
    summary["trades"] = 7
    assert not all(replication.proxy_gate_checks(summary, gates).values())


def test_same_bar_stop_target_collision_is_stop_first() -> None:
    starts = pd.date_range("2024-01-01", periods=3, freq="15min", tz="UTC")
    values = np.array([timestamp.value for timestamp in starts], dtype=np.int64)
    arrays = {
        "starts": values,
        "ends": values + 15 * 60 * 1_000_000_000,
        "signals": values + 15 * 60 * 1_000_000_000,
        "atr14": np.array([1.0, 1.0, 1.0]),
        "bid_open": np.array([100.0, 100.0, 100.0]),
        "ask_open": np.array([100.2, 100.2, 100.2]),
        "bid_high": np.array([100.0, 102.5, 100.0]),
        "bid_low": np.array([100.0, 98.0, 100.0]),
        "ask_high": np.array([100.2, 102.7, 100.2]),
        "ask_low": np.array([100.2, 98.2, 100.2]),
    }
    geometry = {"stop_atr": 1.0, "target_r": 1.0, "maximum_hold_hours": 1.0}
    execution = {
        "maximum_entry_gap_minutes": 20,
        "maximum_horizon_gap_hours": 72,
        "maximum_entry_spread_r": 0.25,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.0,
    }
    trade = replication.ROUTER.simulate_fixed_trade(arrays, 0, 1, geometry, execution)
    assert trade is not None
    assert trade["exit_reason"] == "STOP_AMBIGUOUS"
    assert trade["gross_r"] == pytest.approx(-1.0)
