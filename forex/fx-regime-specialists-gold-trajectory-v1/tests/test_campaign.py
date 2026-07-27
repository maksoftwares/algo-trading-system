from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from fx_regime_specialists.campaign import (  # noqa: E402
    is_quarantined,
    metric_block,
    remove_top_winners,
    route_portfolio,
    verify_preregistration,
)
from fx_regime_specialists.seed_decomposition import verify_seed_lock, walk_seed_exit_to_cycle


def test_preregistration_hashes_are_locked():
    checked = verify_preregistration(PACKAGE_ROOT)
    assert len(checked) == 2


def test_seed_decomposition_hashes_are_locked():
    checked = verify_seed_lock(PACKAGE_ROOT)
    assert len(checked) == 2


def test_quarantine_is_symbol_specific_and_inclusive():
    quarantine = [
        {
            "start_utc": "2024-10-09T23:00:00Z",
            "end_utc": "2024-10-10T01:00:00Z",
            "symbols": ["EURUSD"],
        }
    ]
    assert is_quarantined(pd.Timestamp("2024-10-09T23:00:00Z"), "EURUSD", quarantine)
    assert not is_quarantined(pd.Timestamp("2024-10-09T23:00:00Z"), "GBPUSD", quarantine)


def test_metric_block_and_top_winner_removal():
    trades = pd.DataFrame({"r": [2.0, 1.0, -1.0, -1.0]})
    block = metric_block(trades)
    assert block["profit_factor"] == 1.5
    assert block["net_r"] == 1.0
    assert metric_block(remove_top_winners(trades))["net_r"] == -1.0


def test_drawdown_starts_from_zero_equity():
    trades = pd.DataFrame({"r": [-1.0, 0.25]})
    assert metric_block(trades)["max_drawdown_r"] == 1.0


def test_router_requires_admission():
    empty = route_portfolio(
        {"r1": pd.DataFrame()},
        [],
        {"priority": ["r1"], "daily_loss_stop_r": -2.0, "weekly_loss_stop_r": -4.0},
    )
    assert empty.empty


def test_router_enforces_single_concurrent_position():
    t0 = pd.Timestamp("2025-01-01T10:00:00Z")
    common = {
        "symbol": "USDJPY",
        "signal_time_utc": t0 - pd.Timedelta(hours=1),
        "side": "LONG",
        "entry_price": 1.0,
        "stop_price": 0.9,
        "target_price": 1.2,
        "exit_price": 1.2,
        "exit_reason": "TARGET",
        "risk_distance": 0.1,
        "r": 2.0,
        "extra_half_pip_stress_r": 1.9,
    }
    first = pd.DataFrame([{**common, "specialist": "r1", "entry_time_utc": t0, "exit_time_utc": t0 + pd.Timedelta(hours=2)}])
    second = pd.DataFrame([{**common, "specialist": "r2", "entry_time_utc": t0 + pd.Timedelta(hours=1), "exit_time_utc": t0 + pd.Timedelta(hours=3)}])
    routed = route_portfolio(
        {"r1": first, "r2": second},
        ["r1", "r2"],
        {"priority": ["r1", "r2"], "daily_loss_stop_r": -2.0, "weekly_loss_stop_r": -4.0},
    )
    assert len(routed) == 1
    assert routed.iloc[0]["specialist"] == "r1"


def test_cycle_exit_uses_boundary_open_when_no_price_exit():
    index = pd.date_range("2026-01-01T10:00:00Z", periods=3, freq="5min")
    m5 = pd.DataFrame(
        {
            "bid_open": [100.0, 100.1, 100.2],
            "bid_low": [99.9, 100.0, 100.1],
            "bid_high": [100.2, 100.3, 100.4],
            "ask_open": [100.01, 100.11, 100.21],
            "ask_low": [99.91, 100.01, 100.11],
            "ask_high": [100.21, 100.31, 100.41],
        },
        index=index,
    )
    exit_time, exit_price, reason = walk_seed_exit_to_cycle(
        m5, 0, 2, "LONG", 99.0, 101.0, 0.01
    )
    assert exit_time == index[2]
    assert exit_price == 100.19
    assert reason == "NEXT_CYCLE"
