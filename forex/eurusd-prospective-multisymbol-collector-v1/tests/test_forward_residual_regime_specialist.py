from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from src import forward_selective_learner as base
from src.forward_residual_regime_specialist import (
    CONFIG_PATH,
    admission_metrics,
    classify_regime,
    process,
    select_side,
    side_statistics,
)


def _config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _context(strength_15=0.1, strength_60=0.2, strength_240=0.1, agreement=0.0):
    return {
        "strength_15": strength_15,
        "strength_60": strength_60,
        "strength_240": strength_240,
        "agreement_15": agreement,
        "agreement_60": agreement,
        "agreement_240": agreement,
        "signed_activity_60": 0.0,
        "cost_pressure": 0.0,
    }


def _bar(when, symbol, first, last):
    point = 0.001 if symbol.endswith("JPY") else 0.00001
    spread = 10 * point
    return base.Bar(
        interval_open=when,
        symbol=symbol,
        status="OK",
        copied_ticks=100,
        first_bid=first,
        first_ask=first + spread,
        last_bid=last,
        last_ask=last + spread,
        bid_high=max(first, last) + spread,
        bid_low=min(first, last) - spread,
        ask_high=max(first, last) + 2 * spread,
        ask_low=min(first, last),
        spread_mean_points=10.0,
        point=point,
    )


def _complete_day(config, day=date(2026, 8, 3)):
    decision = datetime.combine(day, datetime.min.time()) + timedelta(hours=20)
    start = decision - timedelta(hours=4)
    symbols = ["EURUSD", "EURGBP", "EURJPY", "GBPUSD", "USDJPY"]
    bases = {
        "EURUSD": 1.15,
        "EURGBP": 0.86,
        "EURJPY": 175.0,
        "GBPUSD": 1.34,
        "USDJPY": 151.0,
    }
    grouped = {}
    for index in range(120):
        when = start + timedelta(minutes=5 * index)
        grouped[when] = {}
        for symbol in symbols:
            scale = 0.000002 if not symbol.endswith("JPY") else 0.0002
            direction = -1 if symbol == "USDJPY" else 1
            first = bases[symbol] + direction * scale * index
            last = first + direction * scale
            grouped[when][symbol] = _bar(when, symbol, first, last)
    return grouped


def test_regime_rules_are_exclusive_and_ordered() -> None:
    config = _config()
    assert classify_regime(_context(), config) == "CROSSPAIR_COMPRESSION"
    assert (
        classify_regime(
            _context(strength_240=0.8, agreement=0.5),
            config,
        )
        == "BROAD_EUR_UP"
    )
    assert (
        classify_regime(
            _context(strength_240=-0.8, agreement=-0.5),
            config,
        )
        == "BROAD_EUR_DOWN"
    )
    assert (
        classify_regime(
            _context(strength_15=-0.8, strength_240=0.4),
            config,
        )
        == "SHORT_LONG_DISAGREEMENT"
    )


def test_selector_never_borrows_another_regime_history() -> None:
    config = _config()
    histories = {
        "BROAD_EUR_UP": {
            "LONG": [1.5] * 20,
            "SHORT": [-1.0] * 20,
        },
        "MIXED_TRANSITION": {"LONG": [], "SHORT": []},
    }
    side, reason, stats = select_side(
        histories,
        "MIXED_TRANSITION",
        20,
        _context(strength_60=1.0),
        config,
    )
    assert side == "CASH"
    assert reason == "NO_REGIME_SIDE_ADMITTED"
    assert stats["LONG"]["observations"] == 0


def test_side_statistics_apply_cost_and_shrinkage() -> None:
    config = _config()
    values = [1.5] * 7 + [-1.0] * 3
    stats = side_statistics(values, config)
    assert stats["observations"] == 10
    assert stats["profit_factor"] == 3.5
    assert stats["shrunk_expectancy_r"] == 0.375
    assert stats["admitted"] is True


def test_upstream_owned_day_is_vetoed_and_not_used_for_training() -> None:
    config = _config()
    grouped = _complete_day(config)
    records, summary = process(grouped, {"2026-08-03"}, config)
    assert len(records) == 1
    assert records[0]["status"] == "UPSTREAM_OWNED"
    assert records[0]["eligible_side"] == "CASH"
    assert summary["resolved_residual_days"] == 0
    assert summary["demo_order_authorized"] is False


def test_admission_never_authorizes_orders_without_combined_proof() -> None:
    config = _config()
    records = []
    for index in range(200):
        value = 1.5 if index % 2 == 0 else -1.0
        records.append(
            {
                "decision_date": (
                    date(2026, 8, 3) + timedelta(days=index)
                ).isoformat(),
                "status": "RESOLVED",
                "eligible_side": "LONG",
                "eligible_result_r": value,
            }
        )
    admission = admission_metrics(records, config)
    assert admission["checks"]["combined_portfolio_frequency_and_coverage"] is False
    assert admission["checks"]["mt5_signal_and_outcome_parity"] is False
    assert admission["demo_order_authorized"] is False
