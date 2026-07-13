from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r3_compression_acceptance_first_pullback_v1_exact as r3  # noqa: E402


def test_two_frozen_cells_use_one_identical_candidate() -> None:
    assert r3.WINDOWS == {
        "prehistory_2016_2021": ("2016.01.01", "2021.12.31"),
        "current_2022_2026": ("2022.07.01", "2026.06.30"),
    }
    first = r3.build_variants()[0]
    second = r3.build_variants()[0]
    assert first.name == second.name == r3.SOURCE_ID
    assert first.tester_inputs == second.tester_inputs == r3.R3_INPUTS
    assert r3.HISTORICAL_RUN_AUTHORIZED is True


def test_candidate_is_h1_acceptance_then_first_m15_pullback() -> None:
    inputs = r3.R3_INPUTS
    assert inputs["InpSignalMode"] == "25"
    assert inputs["InpDirectionMode"] == "0"
    assert inputs["InpRegimeRouterMode"] == "5"
    assert inputs["InpR3CompressionAtrPercentileLookback"] == "252"
    assert inputs["InpR3CompressionAtrPercentileMax"] == "30.00"
    assert inputs["InpR3CompressionBoxDays"] == "5"
    assert inputs["InpR3SetupLifetimeH1Bars"] == "24"
    assert inputs["InpR3AcceptBreakMarginH1Atr"] == "0.10"
    assert inputs["InpR3RetestWindowM15Bars"] == "12"
    assert inputs["InpR3ConsumeOnFirstTouch"] == "true"
    assert inputs["InpRiskReward"] == "2.00"


def test_candidate_has_locked_half_percent_risk_and_one_position() -> None:
    inputs = r3.R3_INPUTS
    assert inputs["InpUseRiskNormalizedLots"] == "true"
    assert inputs["InpRiskAmountUsd"] == "50.00"
    assert inputs["InpRejectRiskOvershootEnabled"] == "true"
    assert inputs["InpMaxRiskOvershootPct"] == "0.00"
    assert inputs["InpOnePositionPerMagic"] == "true"
    assert inputs["InpMaxOpenPositionsPerMagic"] == "1"
    assert inputs["InpMaxTradesPerDay"] == "0"


def test_frozen_input_hash_covers_mode25_and_fail_closed_risk_lane() -> None:
    assert r3.FROZEN_INPUTS_SHA256 == r3.stable_hash(r3.R3_INPUTS)
    assert r3.FROZEN_INPUTS_SHA256 == "ca53d3b0e4b19df61b45c110943452178f3b45b547ff154860b517d2c02bfc5f"


def test_candidate_has_no_calendar_session_or_pnl_masks() -> None:
    inputs = r3.R3_INPUTS
    for key in (
        "InpBlockedEntryHoursCsv",
        "InpBlockedEntryDayHoursCsv",
        "InpBlockedLongEntryHoursCsv",
        "InpBlockedShortEntryHoursCsv",
    ):
        assert inputs[key] == ""
    assert inputs["InpUseDirectionalSessionFilter"] == "false"
    assert inputs["InpLongSessionStartHour"] == "0"
    assert inputs["InpLongSessionEndHour"] == "24"
    assert inputs["InpShortSessionStartHour"] == "0"
    assert inputs["InpShortSessionEndHour"] == "24"
    assert inputs["InpPortfolioDailyGuardEnabled"] == "false"
    assert inputs["InpH4D1WeeklyLossGovernorEnabled"] == "false"
    assert inputs["InpH4D1PrevMonthHealthGateEnabled"] == "false"


def test_runner_is_fail_closed_until_new_ea_mode_and_telemetry_exist() -> None:
    source = r3.EA_SOURCE.read_text(encoding="utf-8")
    missing = [token for token in r3.REQUIRED_EA_TOKENS if token not in source]
    if missing:
        with pytest.raises(RuntimeError, match="not implemented"):
            r3.require_ready()
    else:
        r3.require_ready()


def _event_rows(*, duplicate_signal: bool = False, impure: bool = False) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    native = (
        "R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK_LONG|event_id=E1|"
        f"setup=COMPRESSED|phase=TRANSITION|shock={'1' if impure else '0'}|established=0"
    )
    signals = [
        {"stage": "R3_EVENT_REGISTERED", "reason": "event_id=E1|setup=COMPRESSED"},
        {"stage": "R3_H1_ACCEPTED", "reason": "event_id=E1|direction=LONG"},
        {
            "stage": "WOULD_SIGNAL",
            "timestamp_broker": "2024.01.02 03:15:00",
            "direction": "LONG",
            "reason": native,
        },
        {"stage": "R3_EVENT_CONSUMED", "reason": "event_id=E1|outcome=entry"},
    ]
    if duplicate_signal:
        signals.insert(3, dict(signals[2]))
    orders = [
        {
            "action": "ORDER_SEND_OK",
            "timestamp_broker": "2024.01.02 03:15:00",
            "direction": "LONG",
        }
    ]
    return signals, orders


def test_lifecycle_audit_proves_single_consumed_native_event() -> None:
    signals, orders = _event_rows()
    audit = r3.lifecycle_audit(signals, orders)
    assert audit["registered_events"] == 1
    assert audit["accepted_events"] == 1
    assert audit["consumed_events"] == 1
    assert audit["duplicate_signals"] == []
    assert audit["missing_consumptions"] == []
    assert audit["native_signal_failures"] == []
    assert audit["missing_executed_matches"] == []
    assert audit["executed_event_ids"] == ["E1"]
    assert audit["event_by_timestamp"] == {"2024.01.02 03:15:00": "E1"}


def test_lifecycle_audit_rejects_duplicate_or_impure_signal() -> None:
    signals, orders = _event_rows(duplicate_signal=True, impure=True)
    audit = r3.lifecycle_audit(signals, orders)
    assert audit["duplicate_signals"] == ["E1"]
    assert audit["native_signal_failures"] == ["E1"]
    assert audit["missing_executed_matches"] == ["2024.01.02 03:15:00|LONG"]


def test_window_end_incomplete_is_a_separate_right_censoring_outcome() -> None:
    signals = [
        {"stage": "R3_EVENT_REGISTERED", "reason": "event_id=E1|setup=COMPRESSED"},
        {
            "stage": "R3_EVENT_CONSUMED",
            "reason": "event_id=E1|outcome=window_end_incomplete",
        },
    ]
    audit = r3.lifecycle_audit(signals, [])
    assert "window_end_incomplete" in r3.ALLOWED_CONSUMPTION_OUTCOMES
    assert audit["window_end_incomplete_events"] == 1
    assert audit["window_end_incomplete_event_ids"] == ["E1"]
    assert audit["missing_consumptions"] == []
    assert audit["invalid_consumption_outcomes"] == []


def test_window_check_allows_at_most_one_right_censored_event() -> None:
    signals = []
    for event_id in ("E1", "E2"):
        signals.extend(
            [
                {
                    "stage": "R3_EVENT_REGISTERED",
                    "reason": f"event_id={event_id}|setup=COMPRESSED",
                },
                {
                    "stage": "R3_EVENT_CONSUMED",
                    "reason": f"event_id={event_id}|outcome=window_end_incomplete",
                },
            ]
        )
    lifecycle = r3.lifecycle_audit(signals, [])
    book = {
        "signals": 100,
        "stress_030_net": 1.0,
        "net": 2.0,
        "max_closed_dd": 1.0,
        "data": [],
    }
    drawdown = {
        "balance_relative": {"pct": 1.0},
        "equity_relative": {"pct": 1.0},
        "equity_maximal": {"usd": 1.0},
    }
    orders = {
        "actions": {},
        "guard_reasons": {},
        "unexplained_failure_count": 0,
        "actual_initial_risk_usd": {"count": 0, "missing_count": 0, "above_50_count": 0},
    }
    result = {"mt5_report_metrics": {"Total Trades": "0"}}
    checks = r3.window_checks(book, drawdown, orders, lifecycle, result)
    assert lifecycle["window_end_incomplete_events"] == 2
    assert checks["window_end_incomplete_lte_one"] is False


def test_drawdown_parsers_cover_both_mt5_formats() -> None:
    assert r3.parse_maximal_dd("1 733.37 (24.59%)") == {"usd": 1733.37, "pct": 24.59}
    assert r3.parse_relative_dd("31.06% (686.28)") == {"usd": 686.28, "pct": 31.06}
    assert r3.parse_maximal_dd(None) == {"usd": None, "pct": None}
    assert r3.parse_relative_dd(None) == {"usd": None, "pct": None}


def test_global_gate_requires_both_windows_and_both_directions() -> None:
    book = {
        "wr": 55.0,
        "wl": 2.1,
        "pf": 2.2,
        "stress_030_pf": 1.9,
        "stress_030_net": 500.0,
        "top10_removed_net": 100.0,
        "top3_days_removed_net": 100.0,
        "best_month_share_pct": 20.0,
    }
    long_shape = {"signals": 120, "stress_030_net": 300.0}
    short_shape = {"signals": 20, "stress_030_net": -5.0}
    years = {"exposure_years": 7, "positive_years": 5}
    events = {"best_event_share_pct": 5.0, "missing_event_trade_count": 0}
    windows = {
        "prehistory_2016_2021": {"checks": {"trades_ge_100": True}},
        "current_2022_2026": {"checks": {"trades_ge_100": False}},
    }
    checks = r3.global_checks(book, long_shape, short_shape, years, events, windows)
    assert checks["each_window_passes"] is False
    assert checks["short_trades_ge_50"] is False
    assert checks["short_stress_net_gt_0"] is False
    assert not all(checks.values())
