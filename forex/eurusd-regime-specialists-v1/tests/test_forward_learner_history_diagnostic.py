from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from eurusd_regime_specialists.forward_learner_history_diagnostic import (
    LEARNER_CONFIG,
    evaluate,
    load_engine,
    replay_day,
    write_outputs,
)


def _bar(engine, when, symbol, first, last, *, ticks=100):
    spread = 0.0001 if not symbol.endswith("JPY") else 0.01
    point = 0.00001 if not symbol.endswith("JPY") else 0.001
    return engine.Bar(
        interval_open=when,
        symbol=symbol,
        status="OK",
        copied_ticks=ticks,
        first_bid=first,
        first_ask=first + spread,
        last_bid=last,
        last_ask=last + spread,
        bid_high=max(first, last) + spread / 4,
        bid_low=min(first, last) - spread / 4,
        ask_high=max(first, last) + spread * 1.25,
        ask_low=min(first, last) + spread * 0.75,
        spread_mean_points=spread / point,
        point=point,
    )


def _grouped_day(engine):
    day = date(2026, 8, 3)
    start = datetime(2026, 8, 3, 4, 0)  # noqa: DTZ001 - engine uses naive UTC
    bases = {
        "EURUSD": 1.1600,
        "EURGBP": 0.8600,
        "EURJPY": 175.0,
        "GBPUSD": 1.3500,
        "USDJPY": 151.0,
    }
    grouped = {}
    for index in range(120):
        when = start + timedelta(minutes=5 * index)
        grouped[when] = {}
        for symbol, base in bases.items():
            direction = -1.0 if symbol == "USDJPY" else 1.0
            scale = 0.000002 if not symbol.endswith("JPY") else 0.0002
            first = base + direction * index * scale
            last = first + direction * scale / 2
            if symbol == "EURUSD":
                first = base
                last = base
            grouped[when][symbol] = _bar(
                engine,
                when,
                symbol,
                first,
                last,
                ticks=100 + index,
            )
    return day, grouped


def test_one_day_replay_matches_frozen_forward_engine_exactly() -> None:
    engine = load_engine()
    config = json.loads(LEARNER_CONFIG.read_text(encoding="utf-8"))
    day, grouped = _grouped_day(engine)
    expected_records, expected_summary = engine.process(grouped, config)
    record, weights, resolved_days = replay_day(
        day,
        grouped,
        [0.0] * 9,
        0,
        config,
        engine,
    )
    assert engine.json_safe(record) == engine.json_safe(expected_records[0])
    assert resolved_days == expected_summary["resolved_training_days"]
    assert engine.weights_hash(weights) == expected_summary["final_weights_hash"]


def test_diagnostic_never_authorizes_orders() -> None:
    config = json.loads(LEARNER_CONFIG.read_text(encoding="utf-8"))
    records = [
        {
            "decision_date": f"2026-09-{index + 1:02d}",
            "status": "RESOLVED",
            "training_days_before": 20 + index,
            "eligible_side": "LONG",
            "eligible_result_r": 1.5 if index % 2 == 0 else -1.0,
        }
        for index in range(20)
    ]
    result = evaluate(records, 40, config)
    assert result["status"] == "RETROSPECTIVE_DIAGNOSTIC_ONLY_NO_ADMISSION"
    assert result["demo_order_authorized"] is False
    assert result["primary"]["trades_per_validation_weekday"] == 1.0


def test_output_labels_diagnostic_and_never_claims_admission(tmp_path) -> None:
    config = json.loads(LEARNER_CONFIG.read_text(encoding="utf-8"))
    records = [
        {
            "decision_date": "2026-09-01",
            "status": "RESOLVED",
            "training_days_before": 20,
            "eligible_side": "LONG",
            "eligible_result_r": 1.5,
        }
    ]
    result = evaluate(records, 21, config)
    result["historical_bar_adapter"] = {
        "spread_mean_points_proxy": "test proxy"
    }
    write_outputs(records, result, tmp_path)
    markdown = (tmp_path / "RESULT.md").read_text(encoding="utf-8")
    serialized = json.loads((tmp_path / "RESULT.json").read_text(encoding="utf-8"))
    assert "RETROSPECTIVE DIAGNOSTIC ONLY -- NO ADMISSION" in markdown
    assert "intrabar tick-mean spread" in markdown
    assert serialized["demo_order_authorized"] is False
