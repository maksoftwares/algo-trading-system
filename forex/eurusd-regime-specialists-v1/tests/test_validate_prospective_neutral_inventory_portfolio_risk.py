from __future__ import annotations

from pathlib import Path

import pandas as pd

import validate_prospective_neutral_inventory_portfolio_risk as risk


def _ticks(rows: list[tuple[str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["timestamp_utc", "bid", "ask"]).assign(
        timestamp_utc=lambda frame: pd.to_datetime(
            frame["timestamp_utc"], utc=True
        )
    )


def _trade(
    *,
    signal_id: str = "a",
    side: str = "LONG",
    entry_fill: float = 1.1001,
    result_r: float = 1.5,
    ticks: pd.DataFrame | None = None,
) -> dict:
    market = (
        _ticks(
            [
                ("2026-07-30T00:05:00Z", 1.1000, 1.1001),
                ("2026-07-30T00:10:00Z", 1.0998, 1.0999),
                ("2026-07-30T00:15:00Z", 1.1010, 1.1011),
            ]
        )
        if ticks is None
        else ticks
    )
    return {
        "signal_id": signal_id,
        "component": "primary_0005",
        "clock": "0005",
        "entry_date_utc": "2026-07-30",
        "scheduled_entry_time_utc": pd.Timestamp("2026-07-30T00:05:00Z"),
        "side": side,
        "ticks": market,
        "execution": {
            "status": "CLOSED",
            "side": side,
            "entry_time_utc": pd.Timestamp("2026-07-30T00:05:00Z"),
            "entry_tick_time_utc": pd.Timestamp("2026-07-30T00:05:00Z"),
            "entry_fill": entry_fill,
            "exit_time_utc": pd.Timestamp("2026-07-30T00:15:00Z"),
            "exit_bid": float(market.iloc[-1]["bid"]),
            "exit_ask": float(market.iloc[-1]["ask"]),
            "r": result_r,
            "extra_half_pip_stress_r": result_r - 0.5 / 6.0,
            "fixed_stop_pips": 6.0,
            "fixed_target_pips": 9.0,
            "adverse_slippage_pips_per_side": 0.1,
        },
    }


def test_risk_contract_freezes_account_delay_and_monte_carlo() -> None:
    cfg = risk.load_config()
    assert cfg["account_contract"]["declared_research_balance_usd"] == 1000.0
    assert cfg["account_contract"]["fixed_lots_per_position"] == 0.01
    assert cfg["stress_contract"]["delayed_entry_seconds"] == [5, 30]
    assert cfg["monte_carlo_contract"]["simulations"] == 20000
    assert cfg["admission"]["maximum_base_floating_drawdown_fraction"] == 0.05
    assert cfg["broker_action_allowed"] is False


def test_long_mark_to_market_uses_bid_and_exit_slippage() -> None:
    curve = risk.trade_mark_to_market_r(_trade())
    assert curve.iloc[0]["unrealized_r"] < 0.0
    expected_last = (1.1010 - 0.1 * 0.0001 - 1.1001) / 0.0001 / 6.0
    assert abs(curve.iloc[-1]["unrealized_r"] - expected_last) < 1e-12


def test_short_mark_to_market_uses_ask_and_exit_slippage() -> None:
    trade = _trade(side="SHORT", entry_fill=1.1000, result_r=-1.0)
    curve = risk.trade_mark_to_market_r(trade)
    expected_last = (1.1000 - (1.1011 + 0.1 * 0.0001)) / 0.0001 / 6.0
    assert abs(curve.iloc[-1]["unrealized_r"] - expected_last) < 1e-12


def test_floating_drawdown_captures_intratrade_equity() -> None:
    metrics = risk.floating_drawdown(
        [_trade()],
        extra_round_trip_pips=0.0,
        balance_usd=1000.0,
        usd_pip_value=0.1,
    )
    assert metrics["maximum_floating_drawdown_r"] > 0.5
    assert metrics["ending_equity_r"] == 1.5
    assert metrics["maximum_floating_drawdown_usd"] < 1.0


def test_exposure_and_margin_use_fixed_point_zero_one_lot() -> None:
    metrics = risk.exposure_and_margin(
        [_trade()], risk.load_config()["account_contract"]
    )
    assert metrics["maximum_gross_lots"] == 0.01
    assert 1100.0 < metrics["maximum_absolute_eurusd_notional_usd"] < 1101.0
    assert metrics["maximum_margin_utilization_fraction"] < 0.04


def test_five_second_delay_reexecutes_on_later_tick() -> None:
    trade = _trade(
        ticks=_ticks(
            [
                ("2026-07-30T00:05:00Z", 1.1000, 1.1001),
                ("2026-07-30T00:05:05Z", 1.0998, 1.0999),
                ("2026-07-30T00:05:10Z", 1.1010, 1.1011),
            ]
        )
    )
    delayed = risk.delayed_execution_metrics([trade], 5)
    assert delayed["fill_rate"] == 1.0
    assert delayed["metrics"]["trades"] == 1
    assert delayed["interval_integrity"]["no_position_overlap"] is True


def test_moving_block_bootstrap_is_deterministic() -> None:
    kwargs = {
        "simulations": 100,
        "block_length": 2,
        "seed": 7,
        "extra_cost_r": 0.1,
        "balance_usd": 10.0,
        "risk_usd_per_r": 1.0,
        "ruin_equity_usd": 0.0,
        "hard_drawdown_fraction": 0.1,
        "quantiles": [0.5, 0.95],
    }
    first = risk.moving_block_bootstrap([1.0, -1.0, -1.0], **kwargs)
    second = risk.moving_block_bootstrap([1.0, -1.0, -1.0], **kwargs)
    assert first == second
    assert first["simulations_run"] == 100
    assert first["hard_drawdown_probability"] > 0.0


def test_zero_evidence_status_waits_without_network_or_broker(tmp_path: Path) -> None:
    status = risk.build_status(
        evaluated_at_utc="2026-07-29T12:20:00Z",
        primary_path_root=tmp_path / "primary",
        transfer_path_root=tmp_path / "transfer",
        verify_lock=False,
    )
    assert status["status"] == "WAITING_FOR_PROSPECTIVE_START"
    assert status["closed_paths"] == 0
    assert status["controlled_demo_ready"] is False
    assert status["network_request_made"] is False
    assert status["broker_action_allowed"] is False


def test_portfolio_risk_lock_verifies() -> None:
    lock = risk.verify_preregistration()
    assert lock["locked_before_first_portfolio_observation"] is True
    assert lock["historical_backtest_allowed"] is False
    assert lock["broker_action_allowed"] is False
