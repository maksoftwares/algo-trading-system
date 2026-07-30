from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "src" / "forward_combined_frequency_portfolio.py"
CONFIG = ROOT / "config" / "frozen_forward_combined_frequency_portfolio_v1.json"
LOCK = ROOT / "EURUSD_FORWARD_COMBINED_FREQUENCY_PORTFOLIO_LOCK_2026_07_30.sha256.json"
PRESTART = (
    ROOT
    / "outputs"
    / "forward_combined_frequency_portfolio_prestart"
    / "FORWARD_SUMMARY.json"
)


def _module():
    spec = importlib.util.spec_from_file_location("combined_forward", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _daily_record(
    day: date,
    training_days_before: int,
    *,
    side: str = "LONG",
    result_r: float = 1.5,
    status: str = "RESOLVED",
) -> dict:
    decision = datetime.combine(
        day,
        datetime.min.time(),
        tzinfo=UTC,
    ) + timedelta(hours=8)
    record = {
        "decision_date": day.isoformat(),
        "decision_time_utc": decision.strftime("%Y.%m.%d %H:%M:%S"),
        "status": status,
        "eligible_side": side if training_days_before >= 20 else "CASH",
        "training_days_before": training_days_before,
        "eligible_result_r": (
            result_r if training_days_before >= 20 and status == "RESOLVED" else None
        ),
    }
    if status == "RESOLVED":
        record["long_outcome"] = {
            "side": "LONG",
            "outcome": "TARGET",
            "result_r": result_r,
            "exit_time": (decision + timedelta(hours=1)).strftime("%Y.%m.%d %H:%M:%S"),
        }
        record["short_outcome"] = {
            "side": "SHORT",
            "outcome": "STOP",
            "result_r": -1.0,
            "exit_time": (decision + timedelta(hours=1)).strftime("%Y.%m.%d %H:%M:%S"),
        }
    return record


def _feature_file(path: Path, days: list[date], intervals: int = 240) -> None:
    header = (
        "evidence_scope,interval_open_configured_utc,source_symbol,"
        "source_status,valid_two_sided_quote_count\n"
    )
    lines = [header]
    for day in days:
        start = datetime.combine(day, datetime.min.time())
        for index in range(intervals):
            timestamp = start + timedelta(minutes=5 * index)
            lines.append(
                "PROSPECTIVE_DEMO,"
                f"{timestamp.strftime('%Y.%m.%d %H:%M:%S')},"
                "EURUSD,OK,10\n"
            )
    path.write_text("".join(lines), encoding="utf-8")


def _m15_summary(terminal: int = 0, pending: int = 0) -> dict:
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
        "terminal_outcomes": terminal,
        "pending_signals": pending,
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
            "research_economic_gates_pass": True,
            "mt5_parity_complete": False,
            "shadow_demo_soak_complete": False,
        },
    }


def test_daily_normalization_uses_fixed_point_eight_dollar_risk() -> None:
    module = _module()
    day = date(2026, 8, 31)
    trades = module.normalize_daily_decisions(
        [_daily_record(day, 20, result_r=1.5)],
        _config(),
    )
    assert len(trades) == 1
    assert trades[0].initial_risk_usd == 0.8
    assert round(trades[0].pnl_usd, 10) == 1.2
    assert round(trades[0].stressed_pnl_usd, 10) == 1.15


def test_complete_denominator_starts_only_after_warmup(
    tmp_path: Path,
) -> None:
    module = _module()
    days = [date(2026, 8, 28), date(2026, 8, 31)]
    decisions = [
        _daily_record(days[0], 19),
        _daily_record(days[1], 20),
    ]
    feature_csv = tmp_path / "features.csv"
    _feature_file(feature_csv, days)
    start = module.validation_start_time(decisions, _config())
    assert start is not None
    complete = module.load_complete_weekdays(
        feature_csv,
        _config(),
        start,
    )
    assert complete == [days[1]]


def test_same_timestamp_risk_priority_is_frozen() -> None:
    module = _module()
    config = copy.deepcopy(_config())
    config["causal_portfolio_risk"]["maximum_concurrent_positions"] = 1
    entry = datetime(2026, 8, 31, 8, 0, tzinfo=UTC)
    exit_time = entry + timedelta(hours=1)
    trades = [
        module.Trade(
            trade_id="compression",
            component="M15_REGIME",
            source="M15_COMPRESSION",
            entry_time=entry,
            exit_time=exit_time,
            initial_risk_usd=1.0,
            pnl_usd=1.0,
            stressed_pnl_usd=0.9,
        ),
        module.Trade(
            trade_id="daily",
            component="DAILY_CROSSPAIR",
            source="DAILY_CROSSPAIR",
            entry_time=entry,
            exit_time=exit_time,
            initial_risk_usd=0.8,
            pnl_usd=1.0,
            stressed_pnl_usd=0.9,
        ),
        module.Trade(
            trade_id="chop",
            component="M15_REGIME",
            source="M15_CHOP",
            entry_time=entry,
            exit_time=exit_time,
            initial_risk_usd=2.0,
            pnl_usd=1.0,
            stressed_pnl_usd=0.9,
        ),
    ]
    ledger = module.apply_causal_risk(trades, config)
    assert [row["trade_id"] for row in ledger] == [
        "chop",
        "daily",
        "compression",
    ]
    assert [row["accepted"] for row in ledger] == [True, False, False]


def test_admission_can_reach_frequency_and_edge_without_authorizing_orders() -> None:
    module = _module()
    start = date(2026, 9, 1)
    days = []
    cursor = start
    while len(days) < 160:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor += timedelta(days=1)
    ledger = []
    for index, day in enumerate(days):
        pnl = 2.0 if index % 2 == 0 else -1.0
        entry = datetime.combine(
            day,
            datetime.min.time(),
            tzinfo=UTC,
        ) + timedelta(hours=8)
        ledger.append(
            {
                "trade_id": f"trade-{index}",
                "component": (
                    "M15_REGIME" if index % 4 in (0, 1) else "DAILY_CROSSPAIR"
                ),
                "source": ("M15_CHOP" if index % 4 in (0, 1) else "DAILY_CROSSPAIR"),
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
        _config(),
    )
    assert metrics["trades_per_complete_weekday"] == 1.0
    assert metrics["profit_factor"] == 2.0
    assert metrics["component_profit_factors"] == {
        "M15_REGIME": 2.0,
        "DAILY_CROSSPAIR": 2.0,
    }
    assert metrics["status"] == "WAITING_EXTERNAL_PARITY_AND_SOAK"
    assert metrics["demo_order_authorized"] is False


def test_pending_m15_day_is_not_finalized(tmp_path: Path) -> None:
    module = _module()
    day = date(2026, 8, 31)
    decisions = [_daily_record(day, 20)]
    feature_csv = tmp_path / "features.csv"
    _feature_file(feature_csv, [day])
    m15_summary = _m15_summary(pending=1)
    m15_summary["earliest_pending_signal_entry_time_utc"] = "2026-08-31T06:15:00+00:00"
    ledger, summary = module.process(
        [],
        m15_summary,
        decisions,
        _daily_summary(),
        feature_csv,
        _config(),
    )
    assert ledger == []
    assert summary["raw_complete_validation_weekdays"] == 1
    assert summary["complete_validation_weekdays"] == 0
    assert summary["causally_unfinalized_complete_weekdays"] == 1


def test_zero_prestart_evidence_is_safe_and_waiting(tmp_path: Path) -> None:
    module = _module()
    feature_csv = tmp_path / "features.csv"
    _feature_file(feature_csv, [])
    ledger, summary = module.process(
        [],
        _m15_summary(),
        [],
        _daily_summary(),
        feature_csv,
        _config(),
    )
    assert ledger == []
    assert summary["admission"]["status"] == "WAITING_MINIMUM_EVIDENCE"
    assert summary["demo_order_authorized"] is False


def test_combined_ledger_is_append_only() -> None:
    module = _module()
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
        raise AssertionError("prior combined portfolio decision was mutated")


def test_frozen_contract_contains_frequency_and_no_tuning_guards() -> None:
    config = _config()
    assert config["final_admission"]["minimum_trades_per_complete_weekday"] == 0.85
    assert config["final_admission"]["maximum_trades_per_complete_weekday"] == 1.25
    assert config["final_admission"]["minimum_combined_profit_factor"] == 1.15
    assert config["demo_order_authorized"] is False
    assert "NO_COMPONENT_DELETION" in config["prohibitions"]
    assert "NO_THRESHOLD_TUNING" in config["prohibitions"]
    assert "NO_ORDER_ROUTING_BEFORE_ALL_GATES" in config["prohibitions"]


def test_combined_portfolio_lock_matches_every_frozen_file() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["locked_before_forward_floor"] is True
    assert lock["demo_order_authorized"] is False
    for relative, expected in lock["files"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative


def test_captured_combined_prestart_is_waiting_and_no_order() -> None:
    summary = json.loads(PRESTART.read_text(encoding="utf-8"))
    assert summary["raw_complete_validation_weekdays"] == 0
    assert summary["complete_validation_weekdays"] == 0
    assert summary["portfolio_decisions"] == 0
    assert summary["admission"]["combined_trades"] == 0
    assert summary["admission"]["status"] == "WAITING_MINIMUM_EVIDENCE"
    assert summary["demo_order_authorized"] is False
