from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import forward_combined_frequency_portfolio as base
import forward_live_combined_portfolio as module

CONFIG = ROOT / "config" / "frozen_forward_live_combined_portfolio_v3.json"
LOCK = (
    ROOT / "EURUSD_FORWARD_LIVE_COMBINED_PORTFOLIO_V3_LOCK_2026_07_30.sha256.json"
)


def _config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _signal(day: date, status: str = "PUBLISHED_SIGNAL") -> dict:
    side = "LONG" if status == "PUBLISHED_SIGNAL" else "CASH"
    return {
        "decision_id": f"EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1|{day.isoformat()}",
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1",
        "strategy_campaign_id": "EURUSD_FORWARD_RESIDUAL_REGIME_V1",
        "decision_date": day.isoformat(),
        "decision_time_utc": f"{day.isoformat()}T20:00:00Z",
        "published_at_utc": f"{day.isoformat()}T20:01:00Z",
        "status": status,
        "eligible_side": side,
        "eligibility_reason": "SYNTHETIC_TEST",
        "training_days_before": 20,
        "regime": "BROAD_EUR_UP" if side == "LONG" else "MIXED_TRANSITION",
        "demo_order_authorized": False,
    }


def _outcome(day: date, result_pips: float = 12.0) -> dict:
    decision_id = f"EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1|{day.isoformat()}"
    return {
        "outcome_id": f"EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_V1|{decision_id}",
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_V1",
        "decision_id": decision_id,
        "decision_date": day.isoformat(),
        "status": "RESOLVED",
        "eligible_side": "LONG",
        "regime": "BROAD_EUR_UP",
        "entry_time_utc": f"{day.isoformat()}T20:01:00.000000Z",
        "exit_time_utc": f"{day.isoformat()}T21:01:00.000000Z",
        "lots": 0.01,
        "result_pips": result_pips,
        "result_r": result_pips / 8.0,
        "pnl_usd": result_pips * 0.1,
        "stressed_pnl_usd": (result_pips - 0.5) * 0.1,
        "entry_tick_match_count": 1,
        "raw_tick_count": 100,
        "raw_tick_sha256": "a" * 64,
        "raw_tick_file": f"{'a' * 64}.json",
        "demo_order_authorized": False,
    }


def _parity(day: date, passed: bool = True) -> dict:
    decision_id = f"EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1|{day.isoformat()}"
    return {
        "parity_id": f"EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_V1|{decision_id}",
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_V1",
        "decision_id": decision_id,
        "decision_date": day.isoformat(),
        "publisher_status": "PUBLISHED_SIGNAL",
        "terminal_status": "RESOLVED",
        "comparisons": {"all": passed},
        "parity_pass": passed,
        "demo_order_authorized": False,
    }


def _m15_summary(external: bool = False) -> dict:
    return {
        "campaign_id": "EURUSD_M15_REGIME_FORWARD_V1",
        "terminal_outcomes": 0,
        "pending_signals": 0,
        "earliest_pending_signal_entry_time_utc": None,
        "admission": {
            "status": "WAITING_EXTERNAL_PARITY_AND_SOAK",
            "invalid_outcomes": 0,
            "checks": {
                "minimum_resolved_trades": True,
                "minimum_profit_factor": True,
                "mt5_signal_parity": external,
                "shadow_soak": external,
            },
        },
    }


def _residual_summary(external: bool = False) -> dict:
    return {
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_LIVE_OUTCOME_V1",
        "status": "WAITING_MT5_PARITY_AND_SOAK",
        "terminal_outcomes": 0,
        "selection_parity_rows": 0,
        "invalid_outcomes": 0,
        "selection_mismatches": 0,
        "checks": {
            "minimum_live_executable_outcomes": True,
            "minimum_profit_factor": True,
            "maximum_invalid_outcomes": True,
            "maximum_selection_mismatches": True,
            "mt5_ordering_parity": external,
            "shadow_demo_soak": external,
        },
    }


def _weekdays(count: int) -> list[date]:
    result: list[date] = []
    cursor = date(2026, 8, 3)
    while len(result) < count:
        if cursor.weekday() < 5:
            result.append(cursor)
        cursor += timedelta(days=1)
    return result


def test_live_normalization_uses_exact_broker_tick_outcome() -> None:
    day = date(2026, 8, 3)
    signal = _signal(day)
    trade = module.normalize_residual_live_outcomes(
        [_outcome(day)],
        {signal["decision_id"]: signal},
        _config(),
    )[0]
    assert trade.component == "RESIDUAL_LIVE"
    assert trade.initial_risk_usd == 0.8
    assert round(trade.pnl_usd, 10) == 1.2
    assert round(trade.stressed_pnl_usd, 10) == 1.15


def test_live_normalization_refuses_missing_raw_tick_proof() -> None:
    day = date(2026, 8, 3)
    signal = _signal(day)
    outcome = _outcome(day)
    outcome["entry_tick_match_count"] = 2
    try:
        module.normalize_residual_live_outcomes(
            [outcome],
            {signal["decision_id"]: signal},
            _config(),
        )
    except ValueError as error:
        assert "raw-tick proof" in str(error)
    else:
        raise AssertionError("ambiguous entry tick was accepted")


def test_validation_starts_only_after_residual_online_warmup() -> None:
    before = _signal(date(2026, 8, 3))
    before["training_days_before"] = 19
    after = _signal(date(2026, 8, 4))
    assert module.validation_start_time([before, after], _config()) == datetime(
        2026, 8, 4, 20, 0, tzinfo=UTC
    )


def test_final_day_requires_signal_parity_and_live_outcome() -> None:
    days = [date(2026, 8, 3), date(2026, 8, 4)]
    signals = [_signal(day) for day in days]
    signals_by_date = {item["decision_date"]: item for item in signals}
    first_id = signals[0]["decision_id"]
    assert module.finalized_validation_days(
        days,
        signals_by_date,
        {first_id: _outcome(days[0])},
        {first_id: _parity(days[0])},
        None,
    ) == [days[0]]


def test_cash_decision_finalizes_without_an_outcome() -> None:
    day = date(2026, 8, 3)
    signal = _signal(day, "PUBLISHED_CASH")
    assert module.finalized_validation_days(
        [day],
        {day.isoformat(): signal},
        {},
        {signal["decision_id"]: _parity(day)},
        None,
    ) == [day]


def test_protected_m15_has_same_timestamp_priority() -> None:
    config = copy.deepcopy(_config())
    config["causal_portfolio_risk"]["maximum_concurrent_positions"] = 1
    entry = datetime(2026, 8, 3, 20, 0, tzinfo=UTC)
    exit_time = entry + timedelta(hours=1)
    trades = [
        base.Trade(
            trade_id=source,
            component=(
                "M15_REGIME" if source.startswith("M15") else "RESIDUAL_LIVE"
            ),
            source=source,
            entry_time=entry,
            exit_time=exit_time,
            initial_risk_usd=1.0,
            pnl_usd=1.0,
            stressed_pnl_usd=0.9,
        )
        for source in ("RESIDUAL_LIVE", "M15_COMPRESSION", "M15_CHOP")
    ]
    ledger = module.apply_causal_risk(trades, config)
    assert [row["trade_id"] for row in ledger] == [
        "M15_CHOP",
        "M15_COMPRESSION",
        "RESIDUAL_LIVE",
    ]
    assert [row["accepted"] for row in ledger] == [True, False, False]


def test_target_frequency_and_edge_wait_for_external_proof() -> None:
    days = _weekdays(160)
    ledger = []
    for index, day in enumerate(days):
        component = "M15_REGIME" if index % 4 in (0, 1) else "RESIDUAL_LIVE"
        source = "M15_CHOP" if component == "M15_REGIME" else "RESIDUAL_LIVE"
        pnl = 2.0 if index % 2 == 0 else -1.0
        entry = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
        ledger.append(
            {
                "trade_id": f"trade-{index}",
                "component": component,
                "source": source,
                "entry_time_utc": entry.isoformat(),
                "exit_time_utc": (entry + timedelta(hours=1)).isoformat(),
                "initial_risk_usd": 1.0,
                "pnl_usd": pnl,
                "stressed_pnl_usd": pnl - 0.1,
                "accepted": True,
                "risk_decision": "ACCEPT",
                "open_positions_before": 0,
                "open_initial_risk_usd_before": 0.0,
                "open_initial_risk_usd_after": 1.0,
            }
        )
    metrics = module.admission_metrics(
        ledger,
        days,
        _m15_summary(),
        _residual_summary(),
        _config(),
    )
    assert metrics["trades_per_complete_weekday"] == 1.0
    assert metrics["weekday_trade_coverage"] == 1.0
    assert metrics["win_rate"] == 0.5
    assert metrics["payoff_ratio"] == 2.0
    assert metrics["profit_factor"] == 2.0
    assert metrics["component_trade_counts"] == {
        "M15_REGIME": 80,
        "RESIDUAL_LIVE": 80,
    }
    assert metrics["checks"]["component_economic_admissions"] is True
    assert metrics["status"] == "WAITING_EXTERNAL_PARITY_AND_SOAK"
    assert metrics["demo_order_authorized"] is False


def test_selection_mismatch_blocks_economic_admission() -> None:
    residual = _residual_summary()
    residual["selection_mismatches"] = 1
    residual["checks"]["maximum_selection_mismatches"] = False
    assert module._residual_live_economic(residual, _config()) is False


def test_residual_summary_counts_cannot_hide_invalid_evidence() -> None:
    day = date(2026, 8, 3)
    signal = _signal(day)
    outcome = _outcome(day)
    outcome["status"] = "INVALID_ENTRY_TICK_MATCH"
    outcome["pnl_usd"] = None
    outcome["stressed_pnl_usd"] = None
    parity = _parity(day, passed=False)
    summary = {
        **_residual_summary(),
        "published_decisions": 1,
        "terminal_outcomes": 1,
        "resolved_live_outcomes": 0,
        "invalid_outcomes": 0,
        "selection_parity_rows": 1,
        "selection_mismatches": 1,
        "pending_selection_parity": 0,
        "order_api_calls": 0,
        "position_mutation_attempts": 0,
        "demo_order_authorized": False,
    }
    try:
        module.validate_residual_summary_counts(
            [signal],
            [outcome],
            [parity],
            summary,
        )
    except ValueError as error:
        assert "invalid_outcomes" in str(error)
    else:
        raise AssertionError("summary hid an invalid residual outcome")


def test_append_only_ledger_rejects_mutation() -> None:
    existing = [{"trade_id": "a", "accepted": True, "pnl_usd": 1.0}]
    module.validate_append_only(
        existing,
        existing + [{"trade_id": "b", "accepted": False}],
    )
    mutated = copy.deepcopy(existing)
    mutated[0]["pnl_usd"] = -1.0
    try:
        module.validate_append_only(existing, mutated)
    except ValueError as error:
        assert "mutation refused" in str(error)
    else:
        raise AssertionError("prior live-combined decision was mutated")


def test_frozen_contract_excludes_research_and_rejected_daily_inputs() -> None:
    config = _config()
    assert config["historical_backtest_allowed"] is False
    assert config["excluded_components"]["DAILY_CROSSPAIR"]["may_participate"] is False
    assert config["final_admission"]["minimum_trades_per_complete_weekday"] == 0.85
    assert config["final_admission"]["maximum_trades_per_complete_weekday"] == 1.25
    assert config["final_admission"]["minimum_combined_profit_factor"] == 1.15
    assert config["demo_order_authorized"] is False
    assert "NO_RESEARCH_RESIDUAL_OUTCOME_INPUT" in config["prohibitions"]


def test_live_combined_lock_matches_every_frozen_file() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["locked_before_forward_floor"] is True
    assert lock["locked_with_zero_forward_feature_rows"] is True
    assert lock["locked_with_zero_live_component_outcomes"] is True
    assert lock["locked_with_zero_portfolio_decisions"] is True
    assert lock["historical_backtest_allowed"] is False
    assert lock["demo_order_authorized"] is False
    for relative, expected in lock["files"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
