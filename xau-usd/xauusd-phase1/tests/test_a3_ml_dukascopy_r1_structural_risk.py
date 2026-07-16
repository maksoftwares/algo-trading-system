from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_r1_structural_risk import (  # noqa: E402
    admit_trades,
    episode_monte_carlo,
    exact_tick_equity,
    exposure_episodes,
)


def _row(
    candidate_id: str,
    entry: datetime,
    exit_time: datetime,
    *,
    entry_price: float = 100.0,
    entry_bid: float = 99.0,
    stop: float = 90.0,
    gross: float = 10.0,
    holding: float = 0.0,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "entry_time_utc": entry.isoformat().replace("+00:00", "Z"),
        "exit_time_utc": exit_time.isoformat().replace("+00:00", "Z"),
        "entry_dt": entry,
        "exit_dt": exit_time,
        "entry_ms": int(entry.timestamp() * 1000),
        "exit_ms": int(exit_time.timestamp() * 1000),
        "entry_price_value": entry_price,
        "entry_bid_value": entry_bid,
        "gross_pnl_value": gross,
        "holding_stress_value": holding,
        "stress_net_value": gross - holding - 0.3,
        "initial_risk_usd": entry_price - stop,
        "margin_usd": entry_price / 50.0,
        "units": 1.0,
    }


def _contract() -> dict:
    return {
        "account": {
            "initial_balance_usd": 1000.0,
            "server_utc_offset_hours": 4,
            "margin_call_level_pct": 100.0,
        },
        "execution_stress": {
            "extra_cost_per_trade_usd": 0.3,
            "holding_cost_per_24h_usd": 0.0,
        },
        "capital_observation_balances_usd": [1000.0],
        "monte_carlo": {
            "seed": 7,
            "simulations": 100,
            "ruin_equity_fraction": 0.5,
            "drawdown_warning_fraction": 0.15,
        },
    }


def _profile(**overrides: float | int | str) -> dict:
    values = {
        "name": "fixture",
        "maximum_concurrent_positions": 8,
        "maximum_trade_initial_risk_pct": 100.0,
        "maximum_total_initial_risk_pct": 100.0,
        "maximum_same_direction_initial_risk_pct": 100.0,
        "maximum_margin_utilization_pct": 100.0,
        "daily_realized_loss_halt_pct": 100.0,
    }
    values.update(overrides)
    return values


def test_admission_rejects_total_risk_without_reading_future_profit() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        _row("a", start, start + timedelta(hours=2), gross=-500.0),
        _row("b", start + timedelta(hours=1), start + timedelta(hours=3), gross=500.0),
    ]
    profile = _profile(
        maximum_total_initial_risk_pct=1.5,
        maximum_same_direction_initial_risk_pct=1.5,
    )

    decisions, accepted = admit_trades(rows, profile, _contract())

    assert [row["candidate_id"] for row in accepted] == ["a"]
    assert decisions[1]["decision_reason"] == "MAX_TOTAL_INITIAL_RISK"


def test_exact_tick_equity_reconciles_spread_cost_and_exit() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    exit_time = start + timedelta(minutes=30)
    row = _row("a", start, exit_time)

    class Store:
        def load_hour(self, _hour: int):
            return (
                SimpleNamespace(timestamp_ms=row["entry_ms"], bid=99.0, ask=100.0),
                SimpleNamespace(timestamp_ms=row["exit_ms"], bid=110.0, ask=111.0),
            )

    equity, hourly = exact_tick_equity({"fixture": [row]}, Store(), _contract())

    result = equity["fixture"]
    assert result["final_stress_balance_usd"] == pytest.approx(1009.7)
    assert result["final_native_balance_usd"] == pytest.approx(1010.0)
    assert result["max_floating_drawdown_usd"] == pytest.approx(1.3)
    assert result["gross_exit_reconciliation_max_abs_usd"] == pytest.approx(0.0)
    assert len(hourly) == 1


def test_exposure_episodes_merge_transitive_overlap() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        _row("a", start, start + timedelta(hours=2)),
        _row("b", start + timedelta(hours=1), start + timedelta(hours=4)),
        _row("c", start + timedelta(hours=5), start + timedelta(hours=6)),
    ]

    episodes = exposure_episodes(rows)

    assert [row["trades"] for row in episodes] == [2, 1]
    assert episodes[0]["end_ms"] == rows[1]["exit_ms"]


def test_episode_monte_carlo_is_seeded_and_reports_probabilities() -> None:
    episodes = [
        {"stress_net_usd": 100.0},
        {"stress_net_usd": -50.0},
        {"stress_net_usd": 25.0},
    ]

    first = episode_monte_carlo(episodes, _contract())
    second = episode_monte_carlo(episodes, _contract())

    assert first == second
    assert 0.0 <= first["ruin_probability"] <= 1.0
    assert 0.0 <= first["drawdown_warning_probability"] <= 1.0


def test_capital_observation_tracks_absolute_and_relative_drawdown_independently() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    first_exit = start + timedelta(minutes=20)
    second_entry = start + timedelta(minutes=30)
    second_exit = start + timedelta(minutes=50)
    rows = [
        _row("a", start, first_exit, gross=100.0),
        _row(
            "b",
            second_entry,
            second_exit,
            entry_price=200.0,
            entry_bid=200.0,
            gross=-80.0,
        ),
    ]

    class Store:
        def load_hour(self, _hour: int):
            return (
                SimpleNamespace(timestamp_ms=rows[0]["entry_ms"], bid=99.0, ask=100.0),
                SimpleNamespace(timestamp_ms=rows[0]["exit_ms"], bid=200.0, ask=201.0),
                SimpleNamespace(timestamp_ms=rows[1]["entry_ms"], bid=200.0, ask=201.0),
                SimpleNamespace(timestamp_ms=rows[1]["exit_ms"], bid=120.0, ask=121.0),
            )

    equity, _ = exact_tick_equity({"fixture": rows}, Store(), _contract())
    observation = equity["fixture"]["capital_observations"]["1000.00"]

    assert observation["max_floating_drawdown_usd"] == pytest.approx(80.3)
    assert observation["max_floating_drawdown_pct"] > 7.0
