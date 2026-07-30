from __future__ import annotations

import copy
import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "frozen_forward_selective_learner_v1.json"


def _load_module():
    path = ROOT / "src" / "forward_selective_learner.py"
    spec = importlib.util.spec_from_file_location(
        "eurusd_forward_selective_learner", path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _bar(module, when, symbol, first, last, low=None, high=None, ticks=100):
    spread = 0.0001
    return module.Bar(
        interval_open=when,
        symbol=symbol,
        status="OK",
        copied_ticks=ticks,
        first_bid=first,
        first_ask=first + spread,
        last_bid=last,
        last_ask=last + spread,
        bid_high=high if high is not None else max(first, last),
        bid_low=low if low is not None else min(first, last),
        ask_high=(high if high is not None else max(first, last)) + spread,
        ask_low=(low if low is not None else min(first, last)) + spread,
        spread_mean_points=10.0,
        point=0.00001,
    )


def _context_fixture(module):
    decision = datetime(2026, 8, 3, 8, 0)
    symbols = ["EURUSD", "EURGBP", "EURJPY", "GBPUSD", "USDJPY"]
    starts = {
        "EURUSD": 1.1600,
        "EURGBP": 0.8600,
        "EURJPY": 175.00,
        "GBPUSD": 1.3500,
        "USDJPY": 151.00,
    }
    grouped = {}
    for index in range(48):
        when = decision - timedelta(minutes=5 * (48 - index))
        grouped[when] = {}
        for symbol in symbols:
            step = (index + 1) * starts[symbol] * 0.00001
            if symbol == "USDJPY":
                step = -step
            grouped[when][symbol] = _bar(
                module,
                when,
                symbol,
                starts[symbol] + step,
                starts[symbol] + step * 1.01,
                ticks=100 + index,
            )
    return decision, grouped


def test_context_uses_only_completed_predecision_bars() -> None:
    module = _load_module()
    config = module.load_config(CONFIG)
    decision, grouped = _context_fixture(module)
    original = module.build_context(grouped, decision, config)
    assert original is not None

    contaminated = copy.deepcopy(grouped)
    contaminated[decision] = {
        symbol: _bar(module, decision, symbol, 1.0, 100.0)
        for symbol in config["predictor_symbols"]
    }
    assert module.build_context(contaminated, decision, config) == original


def test_same_bar_collision_is_stop_first() -> None:
    module = _load_module()
    config = module.load_config(CONFIG)
    decision = datetime(2026, 8, 3, 8, 0)
    grouped = {}
    for index in range(72):
        when = decision + timedelta(minutes=5 * index)
        grouped[when] = {
            "EURUSD": _bar(
                module,
                when,
                "EURUSD",
                1.1600,
                1.1600,
                low=1.1580 if index == 0 else 1.1600,
                high=1.1620 if index == 0 else 1.1600,
            )
        }
    long = module.resolve_side(grouped, decision, "LONG", config)
    short = module.resolve_side(grouped, decision, "SHORT", config)
    assert long is not None and long.outcome == "STOP"
    assert short is not None and short.outcome == "STOP"
    assert round(long.result_r, 6) == -1.0125
    assert round(short.result_r, 6) == -1.0125


def test_online_update_is_deterministic_and_past_only() -> None:
    module = _load_module()
    config = module.load_config(CONFIG)
    context = {
        "cost_pressure": 0.0,
        "strength_15": 0.5,
        "strength_60": 1.0,
        "strength_240": 0.25,
        "agreement_15": 0.5,
        "agreement_60": 1.0,
        "agreement_240": 0.5,
        "signed_activity_60": 0.2,
    }
    long_features = module.side_features(context, "LONG")
    short_features = module.side_features(context, "SHORT")
    initial = [0.0] * 9
    updated = module.update_weights(
        initial,
        long_features,
        short_features,
        1,
        0,
        0,
        config,
    )
    assert updated == module.update_weights(
        initial,
        long_features,
        short_features,
        1,
        0,
        0,
        config,
    )
    assert module.predict_probability(updated, long_features) > 0.5
    assert module.predict_probability(updated, short_features) < 0.5


def test_process_emits_exactly_one_warmup_shadow_decision_per_day() -> None:
    module = _load_module()
    config = module.load_config(CONFIG)
    decision, grouped = _context_fixture(module)
    for index in range(72):
        when = decision + timedelta(minutes=5 * index)
        grouped[when] = {
            "EURUSD": _bar(
                module,
                when,
                "EURUSD",
                1.1600,
                1.1601,
                low=1.1599,
                high=1.1602,
            )
        }
    records, summary = module.process(grouped, config)
    assert len(records) == 1
    assert records[0]["decision_time_utc"] == "2026.08.03 08:00:00"
    assert records[0]["eligibility_reason"] == "WARMUP"
    assert records[0]["eligible_side"] == "CASH"
    assert summary["calendar_decisions"] == 1
    assert summary["resolved_training_days"] == 1
    assert summary["shadow_frequency_per_resolved_day"] == 1.0
    assert summary["admission"]["eligible_trades"] == 0
    assert summary["admission"]["demo_order_authorized"] is False


def test_frozen_contract_refuses_historical_or_tester_evidence(tmp_path) -> None:
    module = _load_module()
    config = module.load_config(CONFIG)
    text = CONFIG.read_text(encoding="utf-8")
    required = (
        '"evidence_scope_required": "PROSPECTIVE_DEMO"',
        '"forward_floor_utc": "2026.08.01 00:00:00"',
        '"maximum_decisions_per_utc_day": 1',
        '"minimum_probability": 0.45',
        '"minimum_side_margin": 0.03',
        '"NO_ARCHIVED_OR_TESTER_ROWS"',
        '"NO_ORDERS"',
    )
    for token in required:
        assert token in text

    invalid = tmp_path / "invalid.csv"
    invalid.write_text(
        (
            "evidence_scope,interval_open_configured_utc,source_symbol,"
            "source_status\n"
            "TESTER_SMOKE_NOT_FORWARD,2026.08.03 08:00:00,EURUSD,OK\n"
        ),
        encoding="utf-8",
    )
    try:
        module.load_forward_bars(invalid, config)
    except ValueError as error:
        assert "non-prospective evidence scope refused" in str(error)
    else:
        raise AssertionError("tester row was accepted")


def test_admission_metrics_include_every_frozen_robustness_gate() -> None:
    module = _load_module()
    config = module.load_config(CONFIG)
    records = [
        {
            "decision_date": f"2026-09-{index + 1:02d}",
            "eligible_result_r": 1.4875 if index % 2 == 0 else -1.0125,
        }
        for index in range(20)
    ]
    metrics = module.admission_metrics(records, 20, config)
    assert metrics["status"] == "WAITING_MINIMUM_EVIDENCE"
    assert metrics["stress_r_per_trade"] == 0.0625
    assert "minimum_stressed_profit_factor" in metrics["checks"]
    assert "minimum_best_five_removed_profit_factor" in metrics["checks"]
    assert "maximum_single_month_profit_share" in metrics["checks"]
    assert metrics["demo_order_authorized"] is False


def test_existing_forward_decisions_are_append_only() -> None:
    module = _load_module()
    existing = [
        {
            "decision_date": "2026-08-03",
            "status": "RESOLVED",
            "eligible_side": "CASH",
        }
    ]
    appended = existing + [
        {
            "decision_date": "2026-08-04",
            "status": "RESOLVED",
            "eligible_side": "CASH",
        }
    ]
    module.validate_append_only(existing, appended)

    mutated = copy.deepcopy(appended)
    mutated[0]["eligible_side"] = "LONG"
    try:
        module.validate_append_only(existing, mutated)
    except ValueError as error:
        assert "forward decision ledger mutation refused" in str(error)
    else:
        raise AssertionError("prior forward decision mutation was accepted")
