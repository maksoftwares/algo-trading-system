from __future__ import annotations

import pandas as pd

from plan_prospective_neutral_operations import (
    _poll_interval,
    load_config,
    plan_event_actions,
    plan_ownership_cache_action,
)

EVENT_TIME = pd.Timestamp("2026-08-07T12:30:00Z")
EVENT = {
    "family": "NFP",
    "tradingview_event_id": "396495",
    "tradingview_ticker": "ECONOMICS:USNFP",
    "event_time_utc": EVENT_TIME,
}
LAST_CAPTURE = pd.Timestamp("2026-07-28T15:50:54Z")
FORECAST = {
    **EVENT,
    "forecast_value": 65000.0,
    "observed_at_utc": pd.Timestamp("2026-08-06T12:00:00Z"),
}
ACTUAL = {
    **EVENT,
    "actual_value": 70000.0,
    "actual_observed_at_utc": pd.Timestamp("2026-08-07T12:31:01Z"),
}
MARKET = {
    "event_time_utc": EVENT_TIME,
    "market_observed_at_utc": pd.Timestamp("2026-08-07T12:46:01Z"),
}
OWNERSHIP = {
    "eligible_date": "2026-08-07",
    "ownership_observed_at_utc": pd.Timestamp("2026-08-07T00:02:00Z"),
}
SIGNAL = {
    **EVENT,
    "signal_id": "a" * 64,
    "entry_time_utc": pd.Timestamp("2026-08-07T12:50:00Z"),
    "side": "SHORT",
}


def _plan(
    as_of: str,
    *,
    forecast=None,
    actual=None,
    market=None,
    ownership=None,
    signal=None,
    path=None,
    signal_persisted: bool = False,
    trade_persisted: bool = False,
    oracle_date_complete: bool = False,
):
    return plan_event_actions(
        EVENT,
        evaluated_at_utc=as_of,
        last_calendar_capture_utc=LAST_CAPTURE,
        forecast=forecast,
        actual=actual,
        market=market,
        ownership=ownership,
        signal=signal,
        path=path,
        signal_persisted=signal_persisted,
        trade_persisted=trade_persisted,
        oracle_date_complete=oracle_date_complete,
        config=load_config(),
    )


def _by_stage(actions):
    return {row["stage"]: row for row in actions}


def test_polling_cadence_tightens_without_using_outcomes() -> None:
    cadence = load_config()["polling_cadence"]
    assert _poll_interval(10 * 86400, cadence) == 86400
    assert _poll_interval(48 * 3600, cadence) == 21600
    assert _poll_interval(3 * 3600, cadence) == 3600
    assert _poll_interval(30 * 60, cadence) == 600
    assert _poll_interval(5 * 60, cadence) == 60
    assert _poll_interval(59, cadence) is None


def test_far_event_waits_for_next_daily_forecast_poll() -> None:
    actions = _by_stage(_plan("2026-07-28T16:15:00Z"))
    forecast = actions["PRE_RELEASE_FORECAST"]
    assert forecast["status"] == "SCHEDULED"
    assert forecast["due"] is False
    assert forecast["due_at_utc"] == LAST_CAPTURE + pd.Timedelta(days=1)
    assert forecast["command"] is None
    assert actions["NEUTRAL_OWNERSHIP"]["status"] == "SCHEDULED"
    assert "POST_RELEASE_ACTUAL" not in actions
    assert "EVENT_MARKET" not in actions


def test_ownership_cache_stage_is_due_only_for_newly_safe_missing_hours() -> None:
    config = load_config()
    due = plan_ownership_cache_action(
        {"missing_safe_symbol_hours": 5},
        evaluated_at_utc="2026-07-28T16:18:00Z",
        eligible_date=EVENT_TIME.normalize(),
        config=config,
    )
    assert due["status"] == "DUE"
    assert due["due"] is True
    assert "--eligible-date 2026-08-07" in due["command"]

    scheduled = plan_ownership_cache_action(
        {"missing_safe_symbol_hours": 0},
        evaluated_at_utc="2026-07-28T16:18:00Z",
        eligible_date=EVENT_TIME.normalize(),
        config=config,
    )
    assert scheduled["status"] == "SCHEDULED"
    assert scheduled["due"] is False
    assert scheduled["due_at_utc"] == pd.Timestamp("2026-07-28T17:01:00Z")


def test_due_poll_and_missed_forecast_are_fail_closed() -> None:
    due = _by_stage(_plan("2026-07-29T15:50:54Z"))
    assert due["PRE_RELEASE_FORECAST"]["status"] == "DUE"
    assert due["PRE_RELEASE_FORECAST"]["due"] is True
    assert (
        due["PRE_RELEASE_FORECAST"]["command"]
        == "python capture_prospective_tradingview_consensus.py capture --days-ahead 60"
    )

    missed = _plan("2026-08-07T12:29:00Z")
    assert missed == [
        {
            "stage": "PRE_RELEASE_FORECAST",
            "status": "MISSED_NO_TRADE",
            "due": False,
            "due_at_utc": None,
            "command": None,
            "reason": (
                "No admissible forecast existed by the frozen lead deadline"
            ),
        }
    ]


def test_release_actions_wait_then_become_due_at_exact_safe_times() -> None:
    before = _by_stage(
        _plan(
            "2026-08-07T12:30:59Z",
            forecast=FORECAST,
            ownership=OWNERSHIP,
        )
    )
    assert before["POST_RELEASE_ACTUAL"]["status"] == "SCHEDULED"
    assert before["EVENT_MARKET"]["status"] == "SCHEDULED"

    at_actual = _by_stage(
        _plan(
            "2026-08-07T12:31:00Z",
            forecast=FORECAST,
            ownership=OWNERSHIP,
        )
    )
    assert at_actual["POST_RELEASE_ACTUAL"]["status"] == "DUE"
    assert at_actual["EVENT_MARKET"]["status"] == "SCHEDULED"

    at_market = _by_stage(
        _plan(
            "2026-08-07T12:46:00Z",
            forecast=FORECAST,
            ownership=OWNERSHIP,
        )
    )
    assert at_market["POST_RELEASE_ACTUAL"]["status"] == "DUE"
    assert at_market["EVENT_MARKET"]["status"] == "DUE"
    assert "2026-08-07T12:30:00Z" in at_market["EVENT_MARKET"]["command"]


def test_signal_path_process_and_oracle_actions_are_sequenced() -> None:
    after_signal = _by_stage(
        _plan(
            "2026-08-07T12:47:00Z",
            forecast=FORECAST,
            actual=ACTUAL,
            market=MARKET,
            ownership=OWNERSHIP,
            signal=SIGNAL,
        )
    )
    assert after_signal["CAMPAIGN_PROCESS"]["status"] == "DUE"
    assert after_signal["TRADE_PATH"]["status"] == "SCHEDULED"
    assert after_signal["TRADE_PATH"]["due_at_utc"] == pd.Timestamp(
        "2026-08-08T00:51:00Z"
    )

    at_path = _by_stage(
        _plan(
            "2026-08-08T00:51:00Z",
            forecast=FORECAST,
            actual=ACTUAL,
            market=MARKET,
            ownership=OWNERSHIP,
            signal=SIGNAL,
            signal_persisted=True,
        )
    )
    assert at_path["CAMPAIGN_PROCESS"]["status"] == "CURRENT"
    assert at_path["TRADE_PATH"]["status"] == "DUE"
    assert SIGNAL["signal_id"] in at_path["TRADE_PATH"]["command"]

    complete_path = {
        "path_observed_at_utc": pd.Timestamp("2026-08-08T00:51:01Z")
    }
    terminal = _by_stage(
        _plan(
            "2026-08-08T00:51:01Z",
            forecast=FORECAST,
            actual=ACTUAL,
            market=MARKET,
            ownership=OWNERSHIP,
            signal=SIGNAL,
            path=complete_path,
            signal_persisted=True,
        )
    )
    assert terminal["TRADE_PATH"]["status"] == "CAPTURED"
    assert terminal["CAMPAIGN_PROCESS"]["status"] == "DUE"

    oracle_due = _by_stage(
        _plan(
            "2026-08-08T12:01:00Z",
            forecast=FORECAST,
            actual=ACTUAL,
            market=MARKET,
            ownership=OWNERSHIP,
            signal=SIGNAL,
            path=complete_path,
            signal_persisted=True,
            trade_persisted=True,
        )
    )
    assert oracle_due["ORACLE_EVALUATION"]["status"] == "DUE"
    assert "--oracle-date 2026-08-07" in oracle_due[
        "ORACLE_EVALUATION"
    ]["command"]


def test_planner_contract_is_read_only_and_frequency_neutral() -> None:
    config = load_config()
    assert config["network_requests_allowed"] is False
    assert config["broker_action_allowed"] is False
    assert config["forbidden"]["historical_pnl_loading"] is True
    assert config["forbidden"]["parameter_search"] is True
    assert config["forbidden"]["strategy_or_threshold_change"] is True
