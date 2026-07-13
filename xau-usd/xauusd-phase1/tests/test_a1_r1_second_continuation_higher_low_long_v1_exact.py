from __future__ import annotations

import copy
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
RUNNER_PATH = SCRIPTS / "run_a1_r1_second_continuation_higher_low_long_v1_exact.py"
EA_PATH = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r1_second_continuation_higher_low_long_v1_exact as runner  # noqa: E402
import run_a1_r2_second_continuation_lower_high_short_v1_exact as r2  # noqa: E402


def _passing_metrics() -> dict[str, float]:
    return {
        "trades": 120,
        "owned_regime_episodes": 4,
        "exposure_years": 4,
        "profitable_years": 3,
        "win_rate_pct": 52.0,
        "avg_win_loss": 2.10,
        "profit_factor": 2.20,
        "stress_profit_factor": 1.80,
        "stress_net_usd": 500.0,
        "pre_recent_net_usd": 400.0,
        "top10_removed_net_usd": 100.0,
        "top3_days_removed_net_usd": 150.0,
        "best_month_share_pct": 25.0,
        "max_episode_positive_net_share_pct": 45.0,
        "native_setup_purity_pct": 100.0,
        "native_entry_purity_pct": 100.0,
        "owned_state_net_usd": 1_000.0,
        "required_overlap_controls": len(runner.REQUIRED_OVERLAP_CONTROLS),
        "required_overlap_controls_expected": len(runner.REQUIRED_OVERLAP_CONTROLS),
        "available_overlap_controls": len(runner.REQUIRED_OVERLAP_CONTROLS),
        "max_same_direction_overlap_pct": 19.99,
        "future_bar_violations": 0,
        "retrospective_pivot_entry_violations": 0,
        "active_state_overwrite_violations": 0,
        "multiple_consumption_violations": 0,
        "lifecycle_evidence_complete": 1,
        "missing_event_trade_count": 0,
        "successful_orders": 120,
        "mt5_trades": 120,
        "normalized_trades": 120,
        "unexplained_send_failures": 0,
        "open_positions_at_end": 0,
        "forbidden_guard_blocks": 0,
        "missing_initial_risk_calculations": 0,
        "max_executed_initial_risk_usd": 50.0,
        "balance_dd_relative_pct": 15.0,
        "equity_dd_relative_pct": 18.0,
        "net_usd": 1_000.0,
        "equity_dd_maximal_usd": 400.0,
        "closed_ledger_dd_usd": 250.0,
    }


def test_r1_hlf_is_one_frozen_complete_fail_closed_runner() -> None:
    variants = runner.build_variants()
    checks = runner.static_checks(variants)
    assert len(variants) == 1
    assert variants[0].name == runner.VARIANT_NAME
    assert variants[0].tester_inputs == runner.FROZEN_INPUTS
    assert all(checks.values()), checks
    assert runner.RUNNER_SCAFFOLD_ONLY is False
    assert runner.RUNNER_EVALUATOR_COMPLETE is True
    assert runner.HISTORICAL_RUN_AUTHORIZED is True
    assert runner.PREREG.exists()
    assert (
        "PREREGISTERED_COMPLETE_FAIL_CLOSED_RUNNER_MODE26_NOT_IMPLEMENTED_NOT_RUN"
        in runner.PREREG.read_text(encoding="utf-8")
    )
    assert runner.PROPOSED_SIGNAL_MODE == 26
    assert runner.ADMINISTRATIVE_RENUMBERING == {
        "from_proposed_mode": 25,
        "to_proposed_mode": 26,
        "reason": "mode25_refrozen_for_r3_compression_h1_accept_m15_first_pullback",
        "before_implementation_compile_or_history": True,
    }


def test_r1_hlf_freezes_both_exact_windows_and_input_hash() -> None:
    assert [window["name"] for window in runner.WINDOWS] == [
        "prehistory_201601_202112",
        "primary_202207_202606",
    ]
    assert [(window["from_date"], window["to_date"]) for window in runner.WINDOWS] == [
        ("2016.01.01", "2021.12.31"),
        ("2022.07.01", "2026.06.30"),
    ]
    assert runner.stable_hash(runner.FROZEN_INPUTS) == runner.EXPECTED_FROZEN_INPUT_SHA256
    assert runner.EXPECTED_FROZEN_INPUT_SHA256 == (
        "9fb023f1b492f9acec4d68c3880bcacdc757e0460ae33db9b9789f9d6f213418"
    )


def test_mode23_attrition_diagnosis_is_exactly_frozen_from_csvs() -> None:
    pre = runner.MODE23_ATTRITION["prehistory_201601_202112"]
    primary = runner.MODE23_ATTRITION["primary_202207_202606"]
    for row in (pre, primary):
        terminal = (
            row["expired"]
            + row["first_retest_rejected"]
            + row["invalidated"]
            + row["would_signal"]
        )
        assert terminal == row["observable_terminal_outcomes"]
        assert row["generic_no_candidate"] + terminal == row["decision_rows"]
        assert row["would_signal"] / terminal < 0.02
    assert pre["expired"] / pre["observable_terminal_outcomes"] > 0.60
    assert primary["expired"] / primary["observable_terminal_outcomes"] > 0.75
    assert pre["executed"] == 0
    assert primary["executed"] == 1


def test_r1_hlf_is_the_directional_parameter_mirror_of_mature_r2_lhf() -> None:
    left = runner.FROZEN_INPUTS
    right = r2.FROZEN_INPUTS
    mirrored = {
        "InpR1HlfAtrPeriod": "InpR2LhfAtrPeriod",
        "InpR1HlfMaturityD1Bars": "InpR2LhfMaturityD1Bars",
        "InpR1HlfLeg1LookbackH1Bars": "InpR2LhfLeg1LookbackH1Bars",
        "InpR1HlfLeg1BreakMarginH1Atr": "InpR2LhfLeg1BreakMarginH1Atr",
        "InpR1HlfLeg1MinRangeH1Atr": "InpR2LhfLeg1MinRangeH1Atr",
        "InpR1HlfLeg1MinBodyFraction": "InpR2LhfLeg1MinBodyFraction",
        "InpR1HlfResetWindowM15Bars": "InpR2LhfResetWindowM15Bars",
        "InpR1HlfPivotLeftBars": "InpR2LhfPivotLeftBars",
        "InpR1HlfPivotRightBars": "InpR2LhfPivotRightBars",
        "InpR1HlfResetMinDepthH1Atr": "InpR2LhfResetMinDepthH1Atr",
        "InpR1HlfHigherLowMarginH1Atr": "InpR2LhfLowerHighMarginH1Atr",
        "InpR1HlfSecondBreakWindowM15Bars": "InpR2LhfSecondBreakWindowM15Bars",
        "InpR1HlfSecondTouchM15Atr": "InpR2LhfSecondTouchM15Atr",
        "InpR1HlfSecondCloseM15Atr": "InpR2LhfSecondCloseM15Atr",
        "InpR1HlfSecondMinBodyFraction": "InpR2LhfSecondMinBodyFraction",
        "InpR1HlfInvalidBreakdownH1Atr": "InpR2LhfInvalidReclaimH1Atr",
        "InpR1HlfStopBufferM15Atr": "InpR2LhfStopBufferM15Atr",
        "InpR1HlfMaxStopH1Atr": "InpR2LhfMaxStopH1Atr",
    }
    for r1_key, r2_key in mirrored.items():
        assert left[r1_key] == right[r2_key], (r1_key, r2_key)
    assert left["InpR1HlfLeg1CloseLocationMin"] == "0.75"
    assert right["InpR2LhfLeg1CloseLocationMax"] == "0.25"
    assert left["InpR1HlfSecondCloseLocationMin"] == "0.75"
    assert right["InpR2LhfSecondCloseLocationMax"] == "0.25"
    assert left["InpRegimeRouterMode"] == "1"
    assert right["InpRegimeRouterMode"] == "2"
    assert left["InpDirectionMode"] == "1"
    assert right["InpDirectionMode"] == "2"


def test_r1_hlf_freezes_mature_uptrend_and_first_event_geometry() -> None:
    inputs = runner.FROZEN_INPUTS
    assert inputs["InpSignalMode"] == "26"
    assert inputs["InpRegimeRouterMode"] == "1"
    assert inputs["InpDirectionMode"] == "1"
    assert inputs["InpRiskReward"] == "2.00"
    assert inputs["InpR1HlfMaturityD1Bars"] == "3"
    assert inputs["InpR1HlfLeg1LookbackH1Bars"] == "12"
    assert inputs["InpR1HlfResetWindowM15Bars"] == "16"
    assert inputs["InpR1HlfPivotLeftBars"] == "2"
    assert inputs["InpR1HlfPivotRightBars"] == "2"
    assert inputs["InpR1HlfSecondBreakWindowM15Bars"] == "16"
    assert inputs["InpR1HlfSecondMinBodyFraction"] == "0.50"
    assert inputs["InpR1HlfSecondCloseLocationMin"] == "0.75"


def test_r1_hlf_hard_caps_risk_and_forbids_stacking_masks_or_governors() -> None:
    inputs = runner.FROZEN_INPUTS
    assert runner.DEPOSIT_USD == 10_000.0
    assert runner.RISK_AMOUNT_USD == 50.0
    assert inputs["InpUseRiskNormalizedLots"] == "true"
    assert inputs["InpRiskAmountUsd"] == "50.00"
    assert inputs["InpRejectRiskOvershootEnabled"] == "true"
    assert inputs["InpMaxRiskOvershootPct"] == "0.00"
    assert inputs["InpOnePositionPerMagic"] == "true"
    assert inputs["InpMaxOpenPositionsPerMagic"] == "1"
    assert inputs["InpMaxTradesPerDay"] == "0"
    assert inputs["InpCooldownMinutes"] == "0"
    assert inputs["InpBlockedEntryHoursCsv"] == ""
    assert inputs["InpBlockedEntryDayHoursCsv"] == ""
    assert inputs["InpBlockedLongEntryHoursCsv"] == ""
    assert inputs["InpBlockedShortEntryHoursCsv"] == ""
    assert inputs["InpUseDirectionalSessionFilter"] == "false"
    assert inputs["InpPortfolioDailyGuardEnabled"] == "false"
    assert inputs["InpH4D1PrevMonthHealthGateEnabled"] == "false"
    assert inputs["InpH4D1WeeklyLossGovernorEnabled"] == "false"


def test_r1_hlf_is_structurally_distinct_and_preregisters_causal_consumption() -> None:
    inputs = runner.FROZEN_INPUTS
    prereg = runner.PREREG.read_text(encoding="utf-8")
    assert not any(key.startswith("InpR1Pdh") for key in inputs)
    assert not any(key.startswith("InpR1Pullback") for key in inputs)
    assert not any(key.startswith("InpD1Compression") for key in inputs)
    assert inputs["InpMinAtrAbsoluteForEntry"] == "0.00"
    assert "does not use a prior-D1 high or first retest" in prereg
    assert "first chronological confirmed pivot is consumed" in prereg
    assert "There is no later-pivot retry" in prereg
    assert "is the only second-break attempt" in prereg
    assert "never enter retrospectively" in prereg
    assert "administratively renumbered from proposed mode 25" in prereg
    assert "append mode 26 without renumbering" in prereg


def _ea_source() -> str:
    return EA_PATH.read_text(encoding="utf-8")


def _ea_function(name: str) -> str:
    source = _ea_source()
    match = re.search(rf"(?m)^\w+\s+{re.escape(name)}\(", source)
    if match is None:
        raise AssertionError(f"missing EA function: {name}")
    start = match.start()
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unterminated EA function: {name}")


def test_r1_hlf_implementation_readiness_is_complete_and_history_is_authorized() -> None:
    readiness = runner.implementation_readiness()
    source = _ea_source()
    assert readiness == {token: token in source for token in runner.REQUIRED_EA_TOKENS}
    assert all(readiness.values()), readiness
    assert runner.HISTORICAL_RUN_AUTHORIZED is True


def test_mode26_is_append_only_m15_dispatch_and_preserves_modes22_to25_and_router5() -> None:
    source = _ea_source()
    for token in (
        "SIGNAL_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT = 22",
        "SIGNAL_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG = 23",
        "SIGNAL_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT = 24",
        "SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK = 25",
        "SIGNAL_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG = 26",
    ):
        assert token in source

    m15_modes = _ea_function("IsM15DecisionSignalMode")
    assert "SIGNAL_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG" in m15_modes
    evaluator = _ea_function("EvaluateCompletedM5Bar")
    assert "TryR1SecondContinuationHigherLowLongSignal(" in evaluator
    assert (
        "InpSignalMode != SIGNAL_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG" in evaluator
    )

    router = _ea_function("RegimeRouterAllows")
    router5 = router[
        router.index("REGIME_ROUTER_R3_COMPRESSION_RELEASE_SHOCK_BLOCK") :
        router.index("REGIME_ROUTER_R4_CHOP_ONLY")
    ]
    assert "SIGNAL_D1_COMPRESSION_H4_EXPANSION" in router5
    assert "SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK" in router5
    assert "SIGNAL_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG" not in router5


def test_mode26_uses_distinct_completed_bar_counters_not_elapsed_time_windows() -> None:
    take_bar = _ea_function("R1HlfTakeDistinctCompletedM15Bar")
    assert "m15_bar_time == g_r1_hlf_last_counted_m15_bar" in take_bar
    assert "m15_close_time <= g_r1_hlf_setup_time" in take_bar
    assert (
        take_bar.index("m15_close_time <= g_r1_hlf_setup_time")
        < take_bar.index("g_r1_hlf_last_counted_m15_bar = m15_bar_time")
    )

    signal = _ea_function("TryR1SecondContinuationHigherLowLongSignal")
    assert "g_r1_hlf_reset_m15_bars_observed++" in signal
    assert "g_r1_hlf_second_break_m15_bars_observed++" in signal
    assert "InpR1HlfResetWindowM15Bars" in signal
    assert "InpR1HlfSecondBreakWindowM15Bars" in signal
    for forbidden in (
        "reset_expiry",
        "second_break_expiry",
        "TimeCurrent() - g_r1_hlf",
        "InpR1HlfResetWindowM15Bars * PeriodSeconds",
        "InpR1HlfSecondBreakWindowM15Bars * PeriodSeconds",
    ):
        assert forbidden not in signal

    wait_branch_start = signal.index(
        "if(waiting_for_pivot)", signal.index("const double range = high - low")
    )
    wait_branch = signal[wait_branch_start:]
    assert wait_branch.index("R1HlfFirstConfirmedPivotLow(") < wait_branch.index(
        'FinalizeR1HlfSetupConsumption("pivot_window_expired")'
    )
    second_branch = signal[signal.index("const bool touched_second_break") :]
    assert second_branch.index("ReserveR1HlfFirstSecondBreakConsumption()") < second_branch.index(
        "const bool accepted_second_break"
    )


def test_mode26_no_init_backfill_no_active_overwrite_and_causal_first_pivot() -> None:
    refresh = _ea_function("RefreshR1HlfLegOneState")
    init_start = refresh.index("if(g_r1_hlf_last_scanned_h1_bar == 0)")
    init_branch = refresh[
        init_start : refresh.index("// Active scalar state", init_start)
    ]
    assert "g_r1_hlf_last_scanned_h1_bar = latest_h1_bar;" in init_branch
    assert "return;" in init_branch
    assert "ArmR1HlfLegOneAtH1Shift" not in init_branch
    assert refresh.index("g_r1_hlf_state != R1_HLF_STATE_IDLE") < refresh.index(
        "ArmR1HlfLegOneAtH1Shift(1)"
    )

    pivot = _ea_function("R1HlfFirstConfirmedPivotLow")
    assert "const int pivot_shift = right_bars + 1" in pivot
    assert "offset <= left_bars" in pivot
    assert "offset <= right_bars" in pivot
    assert pivot.count("candidate_low >= comparison_low") == 2
    assert "pivot_close_time <= g_r1_hlf_setup_time" in pivot

    signal = _ea_function("TryR1SecondContinuationHigherLowLongSignal")
    assert "pivot_ordinal=1" in _ea_function("LogR1HlfLifecycle")
    assert signal.count("R1HlfFirstConfirmedPivotLow(") == 1
    assert 'FinalizeR1HlfSetupConsumption("first_pivot_rejected")' in signal
    assert 'FinalizeR1HlfSetupConsumption("second_break_before_arm")' in signal


def test_mode26_emits_complete_native_lifecycle_and_mature_episode_identity() -> None:
    lifecycle = _ea_function("LogR1HlfLifecycle")
    for token in (
        "event_id=",
        "episode_id=",
        "setup_time=",
        "canonical_direction=UP|phase=ESTABLISHED|shock=0|compatibility=uptrend",
        "pivot_ordinal=1",
        "pivot_time=",
        "pivot_confirmation_time=",
        "attempt_ordinal=1",
        "attempt_time=",
        "consumed_time=",
        "outcome=",
    ):
        assert token in lifecycle

    signal = _ea_function("TryR1SecondContinuationHigherLowLongSignal")
    for stage in runner.LIFECYCLE_STAGES.values():
        assert stage in _ea_source()
    assert runner.SIGNAL_PREFIX in signal

    ownership = _ea_function("R1HlfMatureUptrendOwnershipAllows")
    assert "RegimeShockState()" in ownership
    assert "CurrentXauRegime() != XAU_REGIME_UPTREND" in ownership
    assert "R1HlfMatureD1AtShift(1)" in ownership
    assert "RegimeTrendStackAtShift(PERIOD_H4, 1, true)" in ownership
    episode = _ea_function("R1HlfEpisodeIdAtSetup")
    assert "R1HlfMatureD1AtShift(shift)" in episode


def test_mode26_buy_ordercalcprofit_guard_precedes_claim_and_success_logs_risk() -> None:
    hard_risk = _ea_function("R1HlfHardRiskAllowed")
    assert 'direction != "LONG"' in hard_risk
    assert "OrderCalcProfit(ORDER_TYPE_BUY" in hard_risk
    assert "actual_risk_usd <= hard_limit_usd + 0.0000001" in hard_risk
    assert 'AccountInfoString(ACCOUNT_CURRENCY) != "USD"' in hard_risk

    source = _ea_source()
    assert '"actual_risk_usd", "intended_risk_usd", "risk_calc_method"' in source
    evaluator = _ea_function("EvaluateCompletedM5Bar")
    assert evaluator.index("R1HlfHardRiskAllowed(") < evaluator.index("ClaimSignalSlot(")
    assert 'risk_block_reason = "risk_amount_overshoot"' in evaluator
    success = evaluator[evaluator.index('LogOrder("ORDER_SEND_OK"') :]
    assert "InpRiskAmountUsd" in success
    assert '"OrderCalcProfit"' in success


def test_r1_hlf_complete_runner_reaches_mt5_only_after_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    source = RUNNER_PATH.read_text(encoding="utf-8")
    assert ".run_variants(" in source
    assert "_NORMALIZED_TRADES.csv" in source
    assert "_LIFECYCLE_AUDIT.json" in source
    assert "_OVERLAP_AUDIT.json" in source
    assert "_ORDERCALCPROFIT_RISK_AUDIT.json" in source
    assert "_EQUITY_DRAWDOWN_AUDIT.json" in source

    called = False

    def authorized_run(**_kwargs: object) -> dict[str, object]:
        nonlocal called
        called = True
        raise RuntimeError("authorized MT5 sentinel")

    monkeypatch.setattr(runner.mt5, "run_variants", authorized_run)
    monkeypatch.setattr(sys, "argv", [str(RUNNER_PATH)])
    with pytest.raises(RuntimeError, match="authorized MT5 sentinel"):
        runner.main()
    assert called is True


def _native_event_rows(
    *, duplicate_signal: bool = False, confirmation_time: str = "2024.01.02 02:00:00"
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    native = "canonical_direction=UP|phase=ESTABLISHED|shock=0|compatibility=uptrend"
    signals = [
        {
            "timestamp_broker": "2024.01.02 01:00:00",
            "stage": runner.LIFECYCLE_STAGES["registered"],
            "direction": "NONE",
            "reason": (
                "event_id=E1|episode_id=EP1|setup_time=2024.01.02 01:00:00|" + native
            ),
        },
        {
            "timestamp_broker": confirmation_time,
            "stage": runner.LIFECYCLE_STAGES["pivot"],
            "direction": "NONE",
            "reason": (
                "event_id=E1|pivot_ordinal=1|pivot_time=2024.01.02 01:30:00|"
                f"pivot_confirmation_time={confirmation_time}|outcome=confirmed"
            ),
        },
        {
            "timestamp_broker": "2024.01.02 02:15:00",
            "stage": runner.LIFECYCLE_STAGES["second_break"],
            "direction": "LONG",
            "reason": (
                "event_id=E1|attempt_ordinal=1|attempt_time=2024.01.02 02:15:00|"
                "outcome=entry_attempt"
            ),
        },
        {
            "timestamp_broker": "2024.01.02 02:15:00",
            "stage": "WOULD_SIGNAL",
            "direction": "LONG",
            "reason": (
                f"{runner.SIGNAL_PREFIX}|event_id=E1|episode_id=EP1|" + native
            ),
        },
        {
            "timestamp_broker": "2024.01.02 02:15:00",
            "stage": runner.LIFECYCLE_STAGES["consumed"],
            "direction": "LONG",
            "reason": (
                "event_id=E1|consumed_time=2024.01.02 02:15:00|outcome=entry_attempt"
            ),
        },
    ]
    if duplicate_signal:
        signals.insert(4, dict(signals[3]))
    orders = [
        {
            "timestamp_broker": "2024.01.02 02:15:00",
            "action": "ORDER_SEND_OK",
            "direction": "LONG",
            "reason": "pass",
        }
    ]
    return signals, orders


def test_lifecycle_audit_accepts_one_native_causal_consumed_event() -> None:
    signals, orders = _native_event_rows()
    audit = runner.lifecycle_audit(signals, orders)
    assert audit["registered_events"] == 1
    assert audit["pivot_events"] == 1
    assert audit["second_break_events"] == 1
    assert audit["consumed_events"] == 1
    assert audit["would_signal_events"] == 1
    assert audit["setup_purity_pct"] == 100.0
    assert audit["entry_purity_pct"] == 100.0
    assert audit["future_bar_violations"] == []
    assert audit["retrospective_pivot_entry_violations"] == []
    assert audit["active_state_overwrite_violations"] == []
    assert audit["multiple_consumption_violations"] == []
    assert audit["lifecycle_evidence_complete"] is True
    assert audit["event_by_timestamp"]["2024.01.02 02:15:00"]["event_id"] == "E1"


def test_lifecycle_audit_rejects_duplicate_signal_and_retrospective_pivot() -> None:
    signals, orders = _native_event_rows(
        duplicate_signal=True, confirmation_time="2024.01.02 01:45:00"
    )
    audit = runner.lifecycle_audit(signals, orders)
    assert audit["duplicate_signals"] == ["E1"]
    assert audit["multiple_consumption_violations"] == ["E1"]
    assert "E1|confirmation_before_two_right_bars" in audit[
        "retrospective_pivot_entry_violations"
    ]
    assert audit["missing_executed_matches"] == ["2024.01.02 02:15:00|LONG"]
    assert audit["lifecycle_evidence_complete"] is False


def _write_dict_rows(path: Path, rows: list[dict[str, str]], delimiter: str = ",") -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


def test_ordercalcprofit_risk_audit_requires_method_and_caps_actual_risk(tmp_path: Path) -> None:
    order_path = tmp_path / "orders.tsv"
    trade_path = tmp_path / "trades.csv"
    order_rows = [
        {
            "timestamp_broker": "2024.01.02 02:15:00",
            "action": "ORDER_SEND_OK",
            "direction": "LONG",
            "intended_risk_usd": "50.00",
            "actual_risk_usd": "49.75",
            "risk_calc_method": "OrderCalcProfit",
            "reason": "pass",
            "retcode": "10009",
            "retcode_description": "done",
        }
    ]
    _write_dict_rows(order_path, order_rows, "\t")
    _write_dict_rows(
        trade_path,
        [{"entry_time": "2024.01.02 02:15:00", "exit_time": "2024.01.02 03:00:00"}],
    )
    result = {
        "order_csv": str(order_path),
        "trade_csv": str(trade_path),
        "mt5_report_metrics": {"Total Trades": "1"},
    }
    audit = runner.execution_risk_audit(result, order_rows)
    assert audit["successful_orders"] == 1
    assert audit["mt5_trades"] == 1
    assert audit["missing_initial_risk_calculations"] == 0
    assert audit["actual_initial_risk_usd"]["maximum"] == 49.75
    assert audit["actual_initial_risk_usd"]["above_50_count"] == 0

    missing_method = [dict(order_rows[0], risk_calc_method="")]
    audit = runner.execution_risk_audit(result, missing_method)
    assert audit["missing_initial_risk_calculations"] == 1
    assert audit["actual_initial_risk_usd"]["count"] == 0


def test_overlap_audit_is_same_direction_within_fifteen_minutes_and_fail_closed(
    tmp_path: Path,
) -> None:
    control = tmp_path / "control.csv"
    missing = tmp_path / "missing.csv"
    _write_dict_rows(
        control,
        [
            {"entry_time": "2024-01-02 02:25:00", "direction": "LONG"},
            {"entry_time": "2024-01-03 05:00:00", "direction": "SHORT"},
        ],
    )
    candidate = [
        {"entry_time": datetime(2024, 1, 2, 2, 15), "direction": "LONG"},
        {"entry_time": datetime(2024, 1, 4, 2, 15), "direction": "LONG"},
    ]
    audit = runner.overlap_audit(candidate, {"present": control, "missing": missing})
    assert audit["required_controls"] == 2
    assert audit["available_controls"] == 1
    assert audit["max_same_direction_overlap_pct"] == 50.0
    assert audit["rows"][0]["overlap_count"] == 1
    assert audit["rows"][1]["available"] is False


def test_equity_drawdown_parsers_fail_closed_on_missing_mt5_fields() -> None:
    assert runner.parse_maximal_dd("1 733.37 (24.59%)") == {"usd": 1733.37, "pct": 24.59}
    assert runner.parse_relative_dd("31.06% (686.28)") == {"usd": 686.28, "pct": 31.06}
    missing = runner.drawdown_audit({"mt5_report_metrics": {}})
    assert missing["equity_maximal"] == {"usd": None, "pct": None}
    assert missing["equity_relative"] == {"usd": None, "pct": None}


def test_run_window_writes_every_required_evidence_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    signal_path = tmp_path / "signals.tsv"
    order_path = tmp_path / "orders.tsv"
    trade_path = tmp_path / "trades.csv"
    control_path = tmp_path / "control.csv"
    signals, _ = _native_event_rows()
    order_rows = [
        {
            "timestamp_broker": "2024.01.02 02:15:00",
            "action": "ORDER_SEND_OK",
            "direction": "LONG",
            "lots": "0.10",
            "entry_reference": "2000.00",
            "sl": "1995.00",
            "intended_risk_usd": "50.00",
            "actual_risk_usd": "49.50",
            "risk_calc_method": "OrderCalcProfit",
            "reason": "pass",
            "retcode": "10009",
            "retcode_description": "done",
        }
    ]
    trade_rows = [
        {
            "entry_time": "2024.01.02 02:15:00",
            "entry_date": "2024-01-02",
            "direction": "LONG",
            "volume": "0.10",
            "profit_aed": "100.00",
            "exit_time": "2024.01.02 03:00:00",
        }
    ]
    _write_dict_rows(signal_path, signals, "\t")
    _write_dict_rows(order_path, order_rows, "\t")
    _write_dict_rows(trade_path, trade_rows)
    _write_dict_rows(control_path, [{"entry_time": "2024-01-10 00:00:00", "direction": "LONG"}])
    fake_result = {
        "name": runner.VARIANT_NAME,
        "signal_csv": str(signal_path),
        "order_csv": str(order_path),
        "trade_csv": str(trade_path),
        "mt5_report_metrics": {
            "Total Trades": "1",
            "Balance Drawdown Maximal": "20.00 (0.20%)",
            "Balance Drawdown Relative": "0.20% (20.00)",
            "Equity Drawdown Maximal": "25.00 (0.25%)",
            "Equity Drawdown Relative": "0.25% (25.00)",
        },
    }

    monkeypatch.setattr(runner, "REPORTS_DIR", tmp_path)
    monkeypatch.setitem(
        runner.OVERLAP_CONTROL_FILES_BY_WINDOW,
        "primary_202207_202606",
        {"control": control_path},
    )
    monkeypatch.setattr(
        runner.mt5,
        "run_variants",
        lambda **_kwargs: {"variants": [fake_result]},
    )
    window = {
        "name": "primary_202207_202606",
        "from_date": "2022.07.01",
        "to_date": "2026.06.30",
        "pre_recent_end": "2025.12.31",
    }
    result = runner.run_window(window, timeout=1)
    assert result["evidence_metrics"]["normalized_trades"] == 1
    assert result["evidence_metrics"]["lifecycle_evidence_complete"] == 1
    assert result["evidence_metrics"]["max_executed_initial_risk_usd"] == 49.5
    for suffix in (
        "NORMALIZED_TRADES.csv",
        "LIFECYCLE_AUDIT.json",
        "LIFECYCLE_EVENTS.csv",
        "OVERLAP_AUDIT.json",
        "OVERLAP_AUDIT.csv",
        "ORDERCALCPROFIT_RISK_AUDIT.json",
        "ORDERCALCPROFIT_RISK_AUDIT.csv",
        "EQUITY_DRAWDOWN_AUDIT.json",
        "REAL_EVIDENCE_GATES.json",
    ):
        assert list(tmp_path.glob(f"*{suffix}")), suffix


def test_global_window_gate_contract_passes_only_complete_evidence() -> None:
    checks = runner.window_gate_checks(_passing_metrics())
    assert all(value for group in checks.values() for value in group.values()), checks

    too_few = _passing_metrics()
    too_few["trades"] = 99
    assert not runner.window_gate_checks(too_few)["alpha_checks"]["trades_ge_100"]

    strict_overlap = _passing_metrics()
    strict_overlap["max_same_direction_overlap_pct"] = 20.0
    assert not runner.window_gate_checks(strict_overlap)["regime_independence_checks"][
        "same_event_overlap_strictly_below_20pct"
    ]

    risk_overshoot = _passing_metrics()
    risk_overshoot["max_executed_initial_risk_usd"] = 50.0001
    assert not runner.window_gate_checks(risk_overshoot)["execution_risk_checks"][
        "max_executed_initial_risk_lte_50usd"
    ]

    missing_equity_dd = _passing_metrics()
    missing_equity_dd["equity_dd_maximal_usd"] = None
    assert not all(runner.window_gate_checks(missing_equity_dd)["drawdown_checks"].values())


def test_global_decision_separates_alpha_reject_from_drawdown_only_failure() -> None:
    static = runner.static_checks()
    passing = runner.window_gate_checks(_passing_metrics())
    windows = [copy.deepcopy(passing), copy.deepcopy(passing)]
    assert runner.decide(static, windows) == "R1_HLF_SECOND_CONTINUATION_FULLY_QUALIFIED"

    windows[1]["drawdown_checks"]["equity_dd_relative_lte_20"] = False
    assert runner.decide(static, windows) == (
        "R1_HLF_SECOND_CONTINUATION_ALPHA_ONLY_RISK_REPAIR_REQUIRED"
    )

    windows[0]["alpha_checks"]["wr_ge_50"] = False
    assert runner.decide(static, windows) == "R1_HLF_SECOND_CONTINUATION_REJECT"
