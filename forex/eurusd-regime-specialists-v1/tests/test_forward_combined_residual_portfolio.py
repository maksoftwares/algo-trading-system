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
import forward_combined_residual_portfolio as module

LOCK = (
    ROOT
    / "EURUSD_FORWARD_COMBINED_RESIDUAL_PORTFOLIO_V2_LOCK_2026_07_30.sha256.json"
)


def _config() -> dict:
    return json.loads(module.CONFIG_PATH.read_text(encoding="utf-8"))


def _decision(
    day: date,
    training_days_before: int,
    *,
    side: str = "LONG",
    result_r: float = 1.5,
    regime: str = "BROAD_EUR_UP",
) -> dict:
    decision = datetime.combine(
        day,
        datetime.min.time(),
        tzinfo=UTC,
    ) + timedelta(hours=20)
    return {
        "decision_date": day.isoformat(),
        "decision_time_utc": decision.strftime("%Y.%m.%d %H:%M:%S"),
        "status": "RESOLVED",
        "regime": regime,
        "training_days_before": training_days_before,
        "eligible_side": side,
        "eligible_result_r": result_r,
        "long_outcome": {
            "side": "LONG",
            "outcome": "TARGET",
            "result_r": result_r,
            "exit_time": (
                decision + timedelta(hours=1)
            ).strftime("%Y.%m.%d %H:%M:%S"),
        },
        "short_outcome": {
            "side": "SHORT",
            "outcome": "STOP",
            "result_r": -1.0,
            "exit_time": (
                decision + timedelta(hours=1)
            ).strftime("%Y.%m.%d %H:%M:%S"),
        },
    }


def _m15_summary() -> dict:
    checks = {
        "minimum_resolved_trades": True,
        "minimum_observation_calendar_days": True,
        "minimum_active_calendar_months": True,
        "minimum_profit_factor": True,
        "minimum_stressed_profit_factor": True,
        "minimum_best_5pct_removed_profit_factor": True,
        "minimum_each_trade_sequence_half_profit_factor": True,
        "minimum_trades_per_regime": True,
        "minimum_component_profit_factor": True,
        "maximum_single_month_gross_profit_share": True,
        "zero_invalid_outcomes": True,
        "mt5_signal_parity": False,
        "shadow_soak": False,
    }
    return {
        "campaign_id": "EURUSD_M15_REGIME_FORWARD_V1",
        "terminal_outcomes": 0,
        "pending_signals": 0,
        "earliest_pending_signal_entry_time_utc": None,
        "admission": {
            "status": "WAITING_EXTERNAL_PARITY_AND_SOAK",
            "checks": checks,
        },
    }


def _daily_summary() -> dict:
    return {
        "campaign_id": "EURUSD_FORWARD_SELECTIVE_LEARNER_V1",
        "admission": {
            "research_economic_gates_pass": False,
            "mt5_parity_complete": False,
            "shadow_demo_soak_complete": False,
        },
    }


def _residual_summary(records: int = 0) -> dict:
    return {
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_REGIME_V1",
        "records": records,
        "admission": {
            "status": "WAITING_COMBINED_PORTFOLIO_AND_EXECUTION_PROOF",
            "checks": {
                "combined_portfolio_frequency_and_coverage": False,
                "mt5_signal_and_outcome_parity": False,
                "shadow_demo_soak": False,
            },
        },
    }


def _weekdays(count: int, start: date = date(2026, 9, 1)) -> list[date]:
    result = []
    cursor = start
    while len(result) < count:
        if cursor.weekday() < 5:
            result.append(cursor)
        cursor += timedelta(days=1)
    return result


def test_residual_normalization_uses_fixed_point_eight_dollar_risk() -> None:
    trade = module.normalize_residual_decisions(
        [_decision(date(2026, 9, 1), 20)],
        _config(),
    )[0]
    assert trade.component == "RESIDUAL_REGIME"
    assert trade.initial_risk_usd == 0.8
    assert round(trade.pnl_usd, 10) == 1.2
    assert round(trade.stressed_pnl_usd, 10) == 1.15


def test_validation_starts_after_both_online_warmups() -> None:
    daily = [_decision(date(2026, 8, 31), 20)]
    residual = [_decision(date(2026, 9, 2), 20)]
    start = module.validation_start_time(daily, residual, _config())
    assert start == datetime(2026, 9, 2, 20, 0, tzinfo=UTC)
    assert module.validation_start_time(daily, [], _config()) is None


def test_final_day_requires_both_terminal_ledgers() -> None:
    days = [date(2026, 9, 1), date(2026, 9, 2)]
    daily = [_decision(day, 20 + index) for index, day in enumerate(days)]
    residual = [_decision(days[0], 20)]
    assert module.finalized_validation_days(
        days,
        daily,
        residual,
        None,
    ) == [days[0]]


def test_risk_priority_protects_m15_before_research_components() -> None:
    config = copy.deepcopy(_config())
    config["causal_portfolio_risk"]["maximum_concurrent_positions"] = 1
    entry = datetime(2026, 9, 1, 20, 0, tzinfo=UTC)
    exit_time = entry + timedelta(hours=1)
    trades = [
        base.Trade(
            trade_id=source,
            component=(
                "M15_REGIME" if source.startswith("M15") else source
            ),
            source=source,
            entry_time=entry,
            exit_time=exit_time,
            initial_risk_usd=1.0,
            pnl_usd=1.0,
            stressed_pnl_usd=0.9,
        )
        for source in (
            "RESIDUAL_REGIME",
            "DAILY_CROSSPAIR",
            "M15_COMPRESSION",
            "M15_CHOP",
        )
    ]
    ledger = module.apply_causal_risk(trades, config)
    assert [row["trade_id"] for row in ledger] == [
        "M15_CHOP",
        "M15_COMPRESSION",
        "DAILY_CROSSPAIR",
        "RESIDUAL_REGIME",
    ]
    assert [row["accepted"] for row in ledger] == [
        True,
        False,
        False,
        False,
    ]


def test_target_frequency_and_edge_wait_for_external_proof() -> None:
    days = _weekdays(160)
    ledger = []
    for index, day in enumerate(days):
        component = (
            "M15_REGIME" if index % 4 in (0, 1) else "RESIDUAL_REGIME"
        )
        source = "M15_CHOP" if component == "M15_REGIME" else component
        pnl = 2.0 if index % 2 == 0 else -1.0
        entry = datetime.combine(
            day,
            datetime.min.time(),
            tzinfo=UTC,
        ) + timedelta(hours=8)
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
        _daily_summary(),
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
        "DAILY_CROSSPAIR": 0,
        "RESIDUAL_REGIME": 80,
    }
    assert metrics["checks"]["component_economic_admissions"] is True
    assert metrics["status"] == "WAITING_EXTERNAL_PARITY_AND_SOAK"
    assert metrics["demo_order_authorized"] is False


def test_participating_daily_component_cannot_bypass_its_own_admission() -> None:
    days = _weekdays(160)
    ledger = []
    for index, day in enumerate(days):
        component = (
            "M15_REGIME"
            if index % 6 in (0, 1)
            else "RESIDUAL_REGIME"
            if index % 6 in (2, 3)
            else "DAILY_CROSSPAIR"
        )
        source = (
            "M15_CHOP"
            if component == "M15_REGIME"
            else component
        )
        pnl = 2.0 if index % 2 == 0 else -1.0
        entry = datetime.combine(
            day,
            datetime.min.time(),
            tzinfo=UTC,
        ) + timedelta(hours=8)
        ledger.append(
            {
                "trade_id": f"participating-{index}",
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
        _daily_summary(),
        _residual_summary(),
        _config(),
    )
    assert metrics["daily_component_participates"] is True
    assert metrics["checks"]["component_economic_admissions"] is False
    assert metrics["status"] == "REJECTED_FORWARD_PORTFOLIO"


def test_residual_trade_before_warmup_is_refused() -> None:
    try:
        module.normalize_residual_decisions(
            [_decision(date(2026, 9, 1), 19)],
            _config(),
        )
    except ValueError as error:
        assert "before frozen warmup" in str(error)
    else:
        raise AssertionError("pre-warmup residual trade was accepted")


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
        raise AssertionError("prior combined-residual decision was mutated")


def test_frozen_contract_targets_actual_user_goal_without_orders() -> None:
    config = _config()
    gates = config["final_admission"]
    assert gates["minimum_trades_per_complete_weekday"] == 0.85
    assert gates["maximum_trades_per_complete_weekday"] == 1.25
    assert gates["minimum_weekday_trade_coverage"] == 0.65
    assert gates["minimum_win_rate"] == 0.45
    assert gates["maximum_win_rate"] == 0.60
    assert gates["minimum_payoff_ratio"] == 1.25
    assert gates["minimum_combined_profit_factor"] == 1.15
    assert config["demo_order_authorized"] is False
    assert "NO_ORDER_ROUTING_BEFORE_ALL_GATES" in config["prohibitions"]


def test_combined_residual_lock_matches_every_frozen_file() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["locked_before_forward_floor"] is True
    assert lock["locked_with_zero_forward_feature_rows"] is True
    assert lock["locked_with_zero_portfolio_decisions"] is True
    assert lock["historical_backtest_allowed"] is False
    assert lock["demo_order_authorized"] is False
    for relative, expected in lock["files"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
