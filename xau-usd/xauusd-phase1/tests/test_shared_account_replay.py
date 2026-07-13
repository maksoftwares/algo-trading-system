from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ml.a3_meta_v1.shared_account_replay import (
    _admit_candidates,
    _closed_stats,
    _equity_replay,
    _magic_audit,
    _market_session_day,
    _normalize_bar,
)


UTC = timezone.utc


def _candidate(candidate_id: str, entry: datetime, exit_: datetime, direction: str, profit: float) -> dict:
    return {
        "candidate_id": candidate_id,
        "source": candidate_id.split(":")[0],
        "assigned_regime": "R1" if direction == "LONG" else "R2",
        "entry_time": entry.strftime("%Y.%m.%d %H:%M:%S"),
        "entry_dt": entry,
        "exit_time": exit_.strftime("%Y.%m.%d %H:%M:%S"),
        "exit_dt": exit_,
        "direction": direction,
        "entry_deal": candidate_id.split(":")[-1],
        "exit_deal": "99",
        "magic": "1",
        "volume": 1.0,
        "entry_price": 100.0,
        "exit_price": 100.0 + profit if direction == "LONG" else 100.0 - profit,
        "stop_loss": 90.0 if direction == "LONG" else 110.0,
        "take_profit": 120.0 if direction == "LONG" else 80.0,
        "initial_risk_usd": 10.0,
        "notional_usd": 100.0,
        "profit_usd": profit,
        "exit_comment": "fixture",
    }


def _bars(start: datetime, count: int = 4) -> list[dict]:
    return [
        {
            "start": start + timedelta(minutes=5 * index),
            "end": start + timedelta(minutes=5 * (index + 1)),
            "bid_low": 90.0,
            "bid_high": 110.0,
            "bid_close": 100.0,
            "ask_low": 90.0,
            "ask_high": 110.0,
            "ask_close": 100.0,
        }
        for index in range(count)
    ]


def test_admission_rejects_concurrent_candidate_without_using_future_pnl() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    candidates = [
        _candidate("r1:1", start, start + timedelta(minutes=15), "LONG", -50.0),
        _candidate("r2:2", start + timedelta(minutes=5), start + timedelta(minutes=10), "SHORT", 50.0),
    ]
    bars = _bars(start)
    profile = {
        "max_concurrent_positions": 1,
        "max_trade_initial_risk_pct": 100.0,
        "max_total_initial_risk_pct": 100.0,
        "max_same_direction_initial_risk_pct": 100.0,
        "max_margin_utilization_pct": 100.0,
        "daily_realized_loss_halt_pct": 100.0,
    }
    contract = {
        "initial_balance_usd": 1000.0,
        "stress_cost_per_trade_usd": 0.0,
        "assumed_leverage": 20.0,
        "contract_size": 1.0,
    }

    decisions, accepted = _admit_candidates(candidates, profile, contract, bars, [bar["end"] for bar in bars])

    assert [row["candidate_id"] for row in accepted] == ["r1:1"]
    assert decisions[1]["decision_reason"] == "MAX_CONCURRENT_POSITIONS"


def test_equity_replay_marks_liquidation_side_and_realizes_exact_exit() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    trade = _candidate("r1:1", start, start + timedelta(minutes=10), "LONG", -10.0)
    bars = _bars(start, count=3)

    result = _equity_replay(
        [trade],
        bars,
        initial_balance=1000.0,
        contract_size=1.0,
        assumed_leverage=20.0,
        exit_cost=0.0,
    )

    assert result["final_stressed_balance_usd"] == 990.0
    assert result["max_equity_drawdown_usd"] >= 10.0
    assert result["max_concurrent_positions"] == 1


def test_closed_stats_uses_market_days_not_only_active_days_for_frequency() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        _candidate("r1:1", start, start + timedelta(hours=1), "LONG", 10.0),
        _candidate("r2:2", start, start + timedelta(hours=2), "SHORT", -5.0),
    ]
    days = [f"2026-01-{day:02d}" for day in range(1, 11)]

    result = _closed_stats(rows, days, cost=0.0)

    assert result["trades_per_market_day"] == 0.2
    assert result["trades_per_active_day"] == 2.0
    assert result["net_usd"] == 5.0


def test_magic_audit_fails_when_specialists_share_ownership_namespace() -> None:
    result = _magic_audit(
        [
            {"source": "r1", "magic_numbers": ["932200"]},
            {"source": "r2", "magic_numbers": ["932200"]},
        ]
    )

    assert result == {
        "by_source": {"r1": ["932200"], "r2": ["932200"]},
        "collisions": ["932200"],
        "unique": False,
    }


def test_mt5_bid_bar_derives_ask_from_point_spread() -> None:
    result = _normalize_bar(
        {
            "bar_start_utc": "2026-01-01 00:00:00",
            "bar_end_utc": "2026-01-01 00:05:00",
            "open": "100",
            "high": "102",
            "low": "99",
            "close": "101",
            "spread": "30",
        },
        "mt5_bid_plus_spread",
    )

    assert result["bid_close"] == 101.0
    assert result["ask_close"] == 101.3


def test_market_session_day_groups_sunday_evening_with_monday() -> None:
    assert _market_session_day(datetime(2026, 1, 4, 22, 0, tzinfo=UTC)) == "2026-01-05"
    assert _market_session_day(datetime(2026, 1, 5, 12, 0, tzinfo=UTC)) == "2026-01-05"
