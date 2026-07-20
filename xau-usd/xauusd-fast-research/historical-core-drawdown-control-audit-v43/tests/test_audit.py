from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit import (  # noqa: E402
    account_sizing,
    apply_frozen_r1_cap,
    drawdown_episode,
    exact_tick_drawdown,
    load_dukascopy_hour,
    mark_portability_policy,
)


def ledger() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_id": "a",
                "specialist_id": "R1",
                "source_strategy": "BOX",
                "entry_time_utc": pd.Timestamp("2026-01-05T10:00Z"),
                "exit_time_utc": pd.Timestamp("2026-01-06T10:00Z"),
                "pnl_usd_0p01_equiv": -2.0,
            },
            {
                "trade_id": "b",
                "specialist_id": "R1",
                "source_strategy": "BOX",
                "entry_time_utc": pd.Timestamp("2026-01-05T11:00Z"),
                "exit_time_utc": pd.Timestamp("2026-01-06T11:00Z"),
                "pnl_usd_0p01_equiv": -3.0,
            },
            {
                "trade_id": "c",
                "specialist_id": "R1",
                "source_strategy": "BOX",
                "entry_time_utc": pd.Timestamp("2026-01-06T09:00Z"),
                "exit_time_utc": pd.Timestamp("2026-01-06T12:00Z"),
                "pnl_usd_0p01_equiv": 4.0,
            },
            {
                "trade_id": "other",
                "specialist_id": "R2",
                "source_strategy": "OTHER",
                "entry_time_utc": pd.Timestamp("2026-01-05T11:00Z"),
                "exit_time_utc": pd.Timestamp("2026-01-05T12:00Z"),
                "pnl_usd_0p01_equiv": 1.0,
            },
        ]
    )


def test_frozen_cap_preserves_other_specialists_and_enforces_daily_limit() -> None:
    kept, decisions = apply_frozen_r1_cap(
        ledger(),
        {
            "specialist_id": "R1",
            "source_strategy": "BOX",
            "maximum_concurrent_positions": 2,
            "maximum_entries_per_utc_day": 1,
        },
    )
    assert set(kept["trade_id"]) == {"a", "c", "other"}
    rejected = decisions.loc[~decisions["accepted"]].iloc[0]
    assert rejected["trade_id"] == "b"
    assert rejected["decision_reason"] == "MAXIMUM_ENTRIES_PER_UTC_DAY"


def test_drawdown_episode_reports_peak_and_trough() -> None:
    frame = pd.DataFrame(
        {
            "trade_id": ["a", "b", "c"],
            "exit": pd.to_datetime(
                ["2026-01-01", "2026-01-02", "2026-01-03"], utc=True
            ),
            "pnl": [10.0, -4.0, -9.0],
        }
    )
    result = drawdown_episode(frame, "pnl", "exit", pd.Timestamp("2025-12-31T00:00Z"))
    assert result["maximum_drawdown_dollars"] == pytest.approx(13.0)
    assert result["peak_time_utc"].startswith("2026-01-01")
    assert result["trough_time_utc"].startswith("2026-01-03")


def test_account_sizing_fails_when_broker_minimum_is_too_large() -> None:
    result = account_sizing(
        500.0,
        {
            "current_equity_dollars": 3000.0,
            "reference_lot": 0.01,
            "broker_minimum_lot": 0.01,
            "broker_lot_step": 0.01,
            "maximum_equity_drawdown_fraction": 0.15,
            "capital_safety_buffer_multiple": 1.25,
            "legacy_core_floating_drawdown_dollars": 1000.0,
        },
    )
    assert result["minimum_equity_capped_r1_dollars"] == pytest.approx(3333.3333)
    assert result["buffered_minimum_equity_capped_r1_dollars"] == pytest.approx(
        4166.6667
    )
    assert result["maximum_lot_at_current_equity_with_buffer"] == pytest.approx(0.0072)
    assert result["broker_can_express_safe_lot"] is False


def test_raw_hour_decoder_reconstructs_delta_encoded_quotes(tmp_path: Path) -> None:
    path = tmp_path / "hour.json"
    path.write_text(
        json.dumps(
            {
                "timestamp": 1000,
                "multiplier": 0.001,
                "bid": 2000.0,
                "ask": 2000.2,
                "times": [1, 2],
                "bids": [10, -5],
                "asks": [10, 5],
                "bidVolumes": [1, 1],
                "askVolumes": [1, 1],
            }
        ),
        encoding="utf-8",
    )
    ticks = load_dukascopy_hour(path)
    assert ticks["timestamp_ms"].tolist() == [1001, 1003]
    assert ticks["bid"].tolist() == pytest.approx([2000.010, 2000.005])
    assert ticks["ask"].tolist() == pytest.approx([2000.210, 2000.215])


def test_marking_uses_intrabar_low_and_realized_exit() -> None:
    m5 = pd.DataFrame(
        {
            "bar_start_utc": pd.to_datetime(
                ["2026-01-01T00:00Z", "2026-01-01T00:05Z"], utc=True
            ),
            "bar_end_utc": pd.to_datetime(
                ["2026-01-01T00:05Z", "2026-01-01T00:10Z"], utc=True
            ),
            "bid_low": [98.0, 99.0],
            "bid_high": [102.0, 103.0],
        }
    )
    trades = pd.DataFrame(
        {
            "entry_time": [pd.Timestamp("2026-01-01T00:00Z")],
            "exit_time": [pd.Timestamp("2026-01-01T00:05Z")],
            "entry_price": [100.0],
            "exit_price": [102.0],
            "stop": [95.0],
            "target": [102.0],
            "initial_risk_price": [5.0],
            "stress_net_r": [0.3],
            "exit_reason": ["TARGET"],
        }
    )
    result = mark_portability_policy(
        trades,
        m5,
        {
            "ticket_cost_usd": 0.0,
            "holding_cost_per_24h_usd": 0.0,
            "stress_slippage_r": 0.0,
        },
        stress=False,
    )
    assert result["maximum_drawdown_dollars"] == pytest.approx(4.0)


def test_exact_tick_drawdown_uses_two_verified_hours() -> None:
    peak = pd.DataFrame({"timestamp_ms": [1000, 2000], "bid": [101.0, 103.0]})
    trough = pd.DataFrame({"timestamp_ms": [3000, 4000], "bid": [99.0, 97.0]})
    trades = pd.DataFrame(
        {
            "entry_time": [pd.Timestamp(0, unit="ms", tz="UTC")],
            "exit_time": [pd.Timestamp(5000, unit="ms", tz="UTC")],
            "entry_price": [100.0],
            "exit_price": [100.0],
            "stop": [90.0],
            "target": [110.0],
            "initial_risk_price": [10.0],
            "stress_net_r": [0.0],
        }
    )
    result = exact_tick_drawdown(
        peak,
        trough,
        trades,
        {
            "ticket_cost_usd": 0.0,
            "holding_cost_per_24h_usd": 0.0,
            "stress_slippage_r": 0.0,
        },
        stress=False,
    )
    assert result["maximum_drawdown_dollars"] == pytest.approx(6.0)
