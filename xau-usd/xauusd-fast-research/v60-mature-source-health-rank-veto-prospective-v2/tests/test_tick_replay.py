from __future__ import annotations

import pytest

from src.tick_replay import ExitFill, FrozenTrade, replay_ticks, trades_from_evidence


def test_trades_are_reconstructed_only_from_complete_immutable_events() -> None:
    common = {
        "candidate_id": "a",
        "event_id": "a",
        "source_id": "R1_PULLBACK",
        "entry_time_utc": "2026-08-26T00:00:00Z",
    }
    records = [
        {
            "event_type": "BASELINE_EXECUTION_DECISION",
            "payload": {**common, "would_veto": True},
        },
        {
            "event_type": "BROKER_EXECUTION",
            "payload": {
                **common,
                "broker_entry_time_utc": "2026-08-26T00:00:01Z",
                "direction": "LONG",
                "volume_lots": 0.01,
                "entry_price": 4700.0,
                "entry_cost_usd": -0.1,
            },
        },
        {
            "event_type": "BROKER_OUTCOME",
            "payload": {
                **common,
                "broker_exit_time_utc": "2026-08-26T01:00:00Z",
                "broker_pnl_usd": -10.0,
                "exit_fills": [
                    {
                        "exit_time_utc": "2026-08-26T01:00:00Z",
                        "volume_lots": 0.01,
                        "pnl_usd": -9.9,
                    }
                ],
            },
        },
        {
            "event_type": "BASELINE_EXECUTION_DECISION",
            "payload": {**common, "candidate_id": "incomplete", "would_veto": False},
        },
    ]
    trades = trades_from_evidence(records)
    assert len(trades) == 1
    assert trades[0].candidate_id == "a"
    assert trades[0].would_veto is True

    with pytest.raises(ValueError, match="Duplicate replay evidence event"):
        trades_from_evidence(records + [records[0]])


def test_exact_tick_replay_reconciles_pnl_and_portfolio_drawdown() -> None:
    trades = [
        FrozenTrade(
            "a",
            100,
            300,
            "LONG",
            1.0,
            100.0,
            0.0,
            -10.0,
            True,
            (ExitFill(300, 1.0, -10.0),),
        ),
        FrozenTrade(
            "b",
            200,
            400,
            "SHORT",
            1.0,
            110.0,
            0.0,
            10.0,
            False,
            (ExitFill(350, 0.4, 4.0), ExitFill(400, 0.6, 6.0)),
        ),
    ]
    ticks = [
        {"tick_time_msc": 100, "bid": 99.0, "ask": 101.0},
        {"tick_time_msc": 200, "bid": 104.0, "ask": 106.0},
        {"tick_time_msc": 250, "bid": 90.0, "ask": 92.0},
        {"tick_time_msc": 300, "bid": 105.0, "ask": 107.0},
        {"tick_time_msc": 400, "bid": 100.0, "ask": 102.0},
    ]
    result = replay_ticks(trades, ticks, contract_units_per_lot=1.0)
    assert result["ticks_evaluated"] == 5
    assert result["baseline_v60_net_pnl_usd"] == 0.0
    assert result["challenger_v2_net_pnl_usd"] == 10.0
    assert result["delta_net_pnl_usd"] == 10.0
    assert result["all_trades_have_tick_coverage"] is True
    assert result["baseline_v60_equity_drawdown_usd"] >= 0.0
    assert result["challenger_v2_equity_drawdown_usd"] >= 0.0
