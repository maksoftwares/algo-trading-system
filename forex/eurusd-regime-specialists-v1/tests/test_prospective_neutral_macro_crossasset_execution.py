from __future__ import annotations

import pandas as pd
import pytest

from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    ACTUAL_SEMANTICS,
    MARKET_SEMANTICS,
    attach_oracle_precision_labels,
    build_neutral_ownership_record,
    build_signal_ledger,
    build_signal_record,
    evaluate_admission,
    execute_signal,
    route_signals,
)


HASH = "a" * 64


def _actual(*, long: bool = False) -> dict:
    forecast = 0.2
    actual = 0.1 if long else 0.3
    return {
        "family": "CPI",
        "event_time_utc": "2026-08-12T12:30:00Z",
        "forecast_value": forecast,
        "forecast_observed_at_utc": "2026-08-12T11:30:00Z",
        "forecast_raw_snapshot_sha256": HASH,
        "tradingview_event_id": "event-1",
        "tradingview_ticker": "ECONOMICS:USIRMM",
        "actual_value": actual,
        "actual_observed_at_utc": "2026-08-12T12:32:00Z",
        "actual_raw_snapshot_sha256": "b" * 64,
        "surprise_value": actual - forecast,
        "macro_side": "LONG" if long else "SHORT",
        "capture_semantics": ACTUAL_SEMANTICS,
    }


def _market(*, long: bool = False) -> dict:
    return {
        "event_time_utc": "2026-08-12T12:30:00Z",
        "observation_start_utc": "2026-08-12T12:30:00Z",
        "observation_completed_at_utc": "2026-08-12T12:45:00Z",
        "market_observed_at_utc": "2026-08-12T12:46:01Z",
        "eurusd_pre_mid": 1.1000,
        "eurusd_post_mid": 1.1010 if long else 1.0990,
        "eurusd_observation_mid_high": 1.1012,
        "eurusd_observation_mid_low": 1.0998,
        "dxy_pre_mid": 100.0,
        "dxy_post_mid": 99.8 if long else 100.2,
        "treasury_pre_mid": 110.0,
        "treasury_post_mid": 110.2 if long else 109.8,
        "market_manifest_sha256": "c" * 64,
        "market_snapshot_sha256": "d" * 64,
        "capture_semantics": MARKET_SEMANTICS,
    }


def _ownership(*, neutral: bool = True) -> dict:
    direction = "NEUTRAL" if neutral else "USD_UP"
    return build_neutral_ownership_record(
        eligible_date="2026-08-12T00:00:00Z",
        state_timestamp_utc="2026-08-11T23:00:00Z",
        ownership_observed_at_utc="2026-08-12T00:02:00Z",
        direction=direction,
        shock=False,
        dxy_compressed=False,
        eurusd_compressed=False,
        source_hashes={
            "EURUSD": "1" * 64,
            "GBPUSD": "2" * 64,
            "USDJPY": "3" * 64,
            "DOLLARIDXUSD": "4" * 64,
            "USTBONDTRUSD": "5" * 64,
        },
    )


def _signal(*, long: bool = True) -> dict:
    return build_signal_record(
        _actual(long=long),
        _market(long=long),
        _ownership(),
    )


def _path(
    *,
    start: str = "2026-08-12T12:50:00Z",
    periods: int = 144,
    bid: float = 1.1000,
    spread: float = 0.0001,
) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="5min")
    return pd.DataFrame(
        {
            "bid_open": bid,
            "bid_high": bid + 0.0001,
            "bid_low": bid - 0.0001,
            "bid_close": bid,
            "ask_open": bid + spread,
            "ask_high": bid + spread + 0.0001,
            "ask_low": bid + spread - 0.0001,
            "ask_close": bid + spread,
        },
        index=index,
    )


def test_ownership_is_derived_from_exact_prior_h1_state() -> None:
    ownership = _ownership()
    assert ownership["is_neutral"] is True
    assert ownership["neutral_known_at_utc"] == pd.Timestamp(
        "2026-08-12T00:00:00Z"
    )
    with pytest.raises(ValueError, match="prior-date 23:00"):
        build_neutral_ownership_record(
            eligible_date="2026-08-12T00:00:00Z",
            state_timestamp_utc="2026-08-12T00:00:00Z",
            ownership_observed_at_utc="2026-08-12T00:02:00Z",
            direction="NEUTRAL",
            shock=False,
            dxy_compressed=False,
            eurusd_compressed=False,
            source_hashes={
                "EURUSD": "1" * 64,
                "GBPUSD": "2" * 64,
                "USDJPY": "3" * 64,
                "DOLLARIDXUSD": "4" * 64,
                "USTBONDTRUSD": "5" * 64,
            },
        )


def test_entry_is_strictly_after_all_evidence_not_completion_open() -> None:
    signal = _signal(long=False)
    assert signal["side"] == "SHORT"
    assert signal["observation_completed_at_utc"] == pd.Timestamp(
        "2026-08-12T12:45:00Z"
    )
    assert signal["market_observed_at_utc"] == pd.Timestamp(
        "2026-08-12T12:46:01Z"
    )
    assert signal["entry_time_utc"] == pd.Timestamp(
        "2026-08-12T12:50:00Z"
    )
    assert signal["broker_action_allowed"] is False


def test_market_snapshot_without_capture_lag_is_rejected() -> None:
    market = _market()
    market["market_observed_at_utc"] = "2026-08-12T12:45:59Z"
    with pytest.raises(ValueError, match="60-second capture lag"):
        build_signal_record(_actual(), market, _ownership())


def test_mismatched_event_or_tampered_surprise_is_rejected() -> None:
    market = _market()
    market["event_time_utc"] = "2026-08-12T12:35:00Z"
    with pytest.raises(ValueError, match="do not match"):
        build_signal_record(_actual(), market, _ownership())
    actual = _actual()
    actual["surprise_value"] = 99.0
    with pytest.raises(ValueError, match="does not match"):
        build_signal_record(actual, _market(), _ownership())


def test_non_neutral_ownership_produces_cash() -> None:
    signal = build_signal_record(
        _actual(),
        _market(),
        _ownership(neutral=False),
    )
    assert signal["side"] == "CASH"
    assert signal["reason"] == "DATE_NOT_NEUTRAL"


def test_tampered_neutral_ownership_is_rejected() -> None:
    ownership = _ownership(neutral=False)
    ownership["is_neutral"] = True
    with pytest.raises(ValueError, match="flag was altered"):
        build_signal_record(_actual(), _market(), ownership)


def test_bulk_linker_keeps_earliest_actual_revision() -> None:
    first = _actual()
    later = {**first}
    later["actual_observed_at_utc"] = "2026-08-12T12:35:00Z"
    later["actual_value"] = 0.4
    later["surprise_value"] = 0.2
    markets = pd.DataFrame([_market()])
    ownerships = pd.DataFrame([_ownership()])
    signals, census = build_signal_ledger(
        pd.DataFrame([later, first]),
        markets,
        ownerships,
    )
    assert len(signals) == 1
    assert signals["actual_observed_at_utc"].iloc[0] == pd.Timestamp(
        "2026-08-12T12:32:00Z"
    )
    assert census["linked_actual_rows"] == 2
    assert census["selected_actual_events"] == 1


def test_same_bar_stop_and_target_resolves_stop_first() -> None:
    signal = _signal(long=True)
    path = _path()
    path.iloc[0, path.columns.get_loc("bid_low")] = 1.0980
    path.iloc[0, path.columns.get_loc("bid_high")] = 1.1020
    path.iloc[0, path.columns.get_loc("ask_low")] = 1.0981
    path.iloc[0, path.columns.get_loc("ask_high")] = 1.1021
    result = execute_signal(
        signal,
        path,
        path_evidence_sha256="d" * 64,
    )
    assert result["status"] == "CLOSED"
    assert result["exit_reason"] == "STOP"
    assert result["stop_adjustment"] == "FLOOR"
    assert result["risk_pips"] == pytest.approx(4.0)
    assert result["r"] < -1.0


def test_target_path_realizes_near_frozen_one_point_five_r() -> None:
    signal = _signal(long=True)
    path = _path()
    path.iloc[1, path.columns.get_loc("bid_high")] = 1.1020
    path.iloc[1, path.columns.get_loc("ask_high")] = 1.1021
    result = execute_signal(
        signal,
        path,
        path_evidence_sha256="d" * 64,
    )
    assert result["exit_reason"] == "TARGET"
    assert 1.35 <= result["r"] <= 1.5


def test_missing_bar_keeps_trade_pending() -> None:
    signal = _signal(long=True)
    path = _path().drop(pd.Timestamp("2026-08-12T12:55:00Z"))
    result = execute_signal(
        signal,
        path,
        path_evidence_sha256="d" * 64,
    )
    assert result["status"] == "PENDING_INCOMPLETE_PATH"
    assert result["missing_timestamp_utc"] == pd.Timestamp(
        "2026-08-12T12:55:00Z"
    )


def test_structural_risk_above_ceiling_is_clamped_before_outcome() -> None:
    signal = _signal(long=True)
    signal["eurusd_observation_mid_low"] = 1.0900
    result = execute_signal(
        signal,
        _path(),
        path_evidence_sha256="d" * 64,
    )
    assert result["risk_pips"] == pytest.approx(25.0)
    assert result["stop_adjustment"] == "CEILING"


def test_pending_prior_trade_blocks_later_signal() -> None:
    first = _signal(long=True)
    second = {**first}
    second["signal_id"] = "f" * 64
    second["event_time_utc"] = pd.Timestamp(
        "2026-08-12T13:30:00Z"
    )
    second["entry_time_utc"] = pd.Timestamp(
        "2026-08-12T13:50:00Z"
    )
    routed = route_signals(
        pd.DataFrame([first, second]),
        _path(periods=1),
        path_evidence_sha256="d" * 64,
    )
    assert routed["status"].tolist() == [
        "PENDING_INCOMPLETE_PATH",
        "BLOCKED_PRIOR_POSITION_OUTCOME_PENDING",
    ]


def _synthetic_admission_ledger() -> pd.DataFrame:
    rows = []
    for index in range(30):
        win = index % 2 == 0
        side = "LONG" if index < 15 else "SHORT"
        value = 1.5 if win else -1.0
        rows.append(
            {
                "signal_id": f"{index:064x}",
                "status": "CLOSED",
                "entry_time_utc": pd.Timestamp(
                    "2026-08-01T00:00:00Z"
                )
                + pd.Timedelta(days=index),
                "exit_time_utc": pd.Timestamp(
                    "2026-08-01T01:00:00Z"
                )
                + pd.Timedelta(days=index),
                "side": side,
                "r": value,
                "extra_half_pip_stress_r": (
                    value - 0.125
                ),
                "oracle_same_day_same_side": index < 15,
                "path_evidence_sha256": "e" * 64,
            }
        )
    return pd.DataFrame(rows)


def test_admission_remains_accumulating_before_twelve_months() -> None:
    result = evaluate_admission(
        _synthetic_admission_ledger(),
        evaluated_at_utc="2027-01-01T00:00:00Z",
    )
    assert result["status"] == "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    assert result["gate_results"]["minimum_calendar_months"] is False
    assert result["broker_action_allowed"] is False


def test_empty_ledger_before_start_is_waiting_not_backfilled() -> None:
    result = evaluate_admission(
        pd.DataFrame(
            columns=[
                "signal_id",
                "status",
                "entry_time_utc",
                "exit_time_utc",
                "side",
                "r",
                "extra_half_pip_stress_r",
            ]
        ),
        evaluated_at_utc="2026-07-28T14:00:00Z",
    )
    assert result["status"] == "WAITING_FOR_PROSPECTIVE_START"
    assert result["historical_pnl_loaded"] is False


def test_all_frozen_gates_only_trigger_research_review() -> None:
    result = evaluate_admission(
        _synthetic_admission_ledger(),
        evaluated_at_utc="2027-08-01T00:00:00Z",
    )
    assert result["status"] == "RESEARCH_REVIEW_REQUIRED"
    assert result["research_review_allowed"] is True
    assert result["broker_action_allowed"] is False


def test_oracle_labels_are_attached_only_after_known_time() -> None:
    trades = _synthetic_admission_ledger().iloc[:1].drop(
        columns=["oracle_same_day_same_side"]
    )
    oracle = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2026-08-01T12:00:00Z"]
            ),
            "side": ["LONG"],
            "regime": ["NEUTRAL"],
            "oracle_label_known_time_utc": pd.to_datetime(
                ["2026-08-02T00:00:00Z"]
            ),
        }
    )
    labeled = attach_oracle_precision_labels(
        trades,
        oracle,
        evaluated_at_utc="2026-08-02T00:00:00Z",
    )
    assert labeled["oracle_same_day_same_side"].tolist() == [True]
    with pytest.raises(ValueError, match="not known"):
        attach_oracle_precision_labels(
            trades,
            oracle,
            evaluated_at_utc="2026-08-01T23:59:59Z",
        )
