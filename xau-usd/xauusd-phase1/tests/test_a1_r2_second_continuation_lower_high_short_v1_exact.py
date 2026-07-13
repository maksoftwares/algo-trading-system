from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
RUNNER_PATH = SCRIPTS / "run_a1_r2_second_continuation_lower_high_short_v1_exact.py"
EA_PATH = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r2_second_continuation_lower_high_short_v1_exact as runner  # noqa: E402


def _ea_text() -> str:
    return EA_PATH.read_text(encoding="utf-8")


def _function_block(text: str, signature: str, next_signature: str) -> str:
    start = text.index(signature)
    end = text.index(next_signature, start)
    return text[start:end]


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
        "available_overlap_controls": len(runner.REQUIRED_OVERLAP_CONTROLS),
        "max_same_direction_overlap_pct": 19.99,
        "future_bar_violations": 0,
        "retrospective_pivot_entry_violations": 0,
        "active_state_overwrite_violations": 0,
        "multiple_consumption_violations": 0,
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


def test_r2_lhf_is_one_frozen_authorized_exact_cell() -> None:
    variants = runner.build_variants()
    checks = runner.static_checks(variants)
    assert len(variants) == 1
    assert variants[0].name == runner.VARIANT_NAME
    assert variants[0].tester_inputs == runner.FROZEN_INPUTS
    assert all(checks.values()), checks
    assert runner.RUNNER_SCAFFOLD_ONLY is False
    assert runner.HISTORICAL_RUN_AUTHORIZED is True
    assert runner.PREREG.exists()


def test_r2_lhf_freezes_both_exact_windows_and_input_hash() -> None:
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
        "d86bbb02074ff4cfdc6464a7c00e3f5792c2ecb6e8181e9a6837f36f85b2f12c"
    )


def test_r2_lhf_freezes_mature_downtrend_and_first_event_state_geometry() -> None:
    inputs = runner.FROZEN_INPUTS
    assert inputs["InpSignalMode"] == "24"
    assert inputs["InpRegimeRouterMode"] == "2"
    assert inputs["InpDirectionMode"] == "2"
    assert inputs["InpRiskReward"] == "2.00"
    assert inputs["InpR2LhfMaturityD1Bars"] == "3"
    assert inputs["InpR2LhfLeg1LookbackH1Bars"] == "12"
    assert inputs["InpR2LhfResetWindowM15Bars"] == "16"
    assert inputs["InpR2LhfPivotLeftBars"] == "2"
    assert inputs["InpR2LhfPivotRightBars"] == "2"
    assert inputs["InpR2LhfSecondBreakWindowM15Bars"] == "16"
    assert inputs["InpR2LhfSecondMinBodyFraction"] == "0.50"
    assert inputs["InpR2LhfSecondCloseLocationMax"] == "0.25"


def test_r2_lhf_hard_caps_risk_at_50usd_and_forbids_stacking_or_masks() -> None:
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


def test_r2_lhf_is_structurally_distinct_and_preregisters_consumption() -> None:
    inputs = runner.FROZEN_INPUTS
    prereg = runner.PREREG.read_text(encoding="utf-8")
    assert not any(key.startswith("InpR2Pdl") for key in inputs)
    assert not any(key.startswith("InpR2Pullback") for key in inputs)
    assert not any(key.startswith("InpBearImpulseRetest") for key in inputs)
    assert inputs["InpMinAtrAbsoluteForEntry"] == "0.00"
    assert "first chronological confirmed pivot is consumed" in prereg
    assert "There is no later-pivot retry" in prereg
    assert "is the only second-break attempt" in prereg
    assert "never enter retrospectively" in prereg


def test_r2_lhf_implementation_is_present_and_history_is_authorized() -> None:
    readiness = runner.implementation_readiness()
    source = runner.EA_SOURCE.read_text(encoding="utf-8")
    assert readiness == {token: token in source for token in runner.REQUIRED_EA_TOKENS}
    assert all(readiness.values()), readiness
    assert runner.HISTORICAL_RUN_AUTHORIZED is True


def test_mode24_is_appended_without_changing_mode23_or_router5() -> None:
    source = _ea_text()
    mode23 = source.index("SIGNAL_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG = 23,")
    mode24 = source.index("SIGNAL_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT = 24")
    assert mode23 < mode24
    assert "REGIME_ROUTER_R3_COMPRESSION_RELEASE_SHOCK_BLOCK = 5" in source
    assert "InpSignalMode == SIGNAL_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT" in source


def test_mode24_no_backfill_and_scalar_overlap_semantics_are_source_locked() -> None:
    source = _ea_text()
    refresh = _function_block(
        source,
        "void RefreshR2LhfLegOneState()",
        "bool R2LhfFirstConfirmedPivotHigh",
    )
    init_index = refresh.index("if(g_r2_lhf_last_scanned_h1_bar == 0)")
    cursor_index = refresh.index("g_r2_lhf_last_scanned_h1_bar = latest_h1_bar;", init_index)
    active_index = refresh.rindex("if(g_r2_lhf_state != R2_LHF_STATE_IDLE)")
    arm_index = refresh.index("ArmR2LhfLegOneAtH1Shift(1);")
    assert init_index < cursor_index < active_index < arm_index
    assert "for(" not in refresh
    declarations = source[source.index("R2LhfState g_r2_lhf_state") : source.index("datetime g_last_trade_time")]
    assert "g_r2_lhf_setup_time" in declarations
    assert "g_r2_lhf_consumed_setup_time" in declarations
    assert "[]" not in declarations


def test_mode24_enforces_mature_three_d1_ownership_at_setup_and_entry() -> None:
    source = _ea_text()
    ownership = _function_block(
        source,
        "bool R2LhfMatureDowntrendOwnershipAllows()",
        "void ConsumeR2LhfSetup",
    )
    assert "InpR2LhfMaturityD1Bars != 3" in ownership
    assert "CurrentXauRegime() != XAU_REGIME_DOWNTREND" in ownership
    assert "RegimeTrendStackAtShift(PERIOD_D1, shift, false)" in ownership
    assert "RegimeTrendStackAtShift(PERIOD_H4, 1, false)" in ownership
    arm = _function_block(source, "bool ArmR2LhfLegOneAtH1Shift", "void RefreshR2LhfLegOneState")
    signal = _function_block(
        source,
        "bool TryR2SecondContinuationLowerHighShortSignal",
        "bool TryWeeklyLevel",
    )
    assert "if(!R2LhfMatureDowntrendOwnershipAllows())" in arm
    assert "if(!R2LhfMatureDowntrendOwnershipAllows())" in signal
    assert '"r2_lhf_entry_regime_ownership_block"' in source


def test_mode24_first_pivot_and_second_break_are_consumed_without_retry() -> None:
    source = _ea_text()
    pivot = _function_block(
        source,
        "bool R2LhfFirstConfirmedPivotHigh",
        "bool R2LhfPivotRightBarsTouchedLegOneLow",
    )
    assert "const int pivot_shift = right_bars + 1;" in pivot
    assert "candidate <= right_high" in pivot
    assert "candidate <= left_high" in pivot
    signal = _function_block(
        source,
        "bool TryR2SecondContinuationLowerHighShortSignal",
        "bool TryWeeklyLevel",
    )
    rejected_pivot = signal.index('ConsumeR2LhfSetup("r2_lhf_first_pivot_rejected")')
    before_arm = signal.index('ConsumeR2LhfSetup("r2_lhf_second_break_before_arm")')
    lower_high_state = signal.index("g_r2_lhf_state = R2_LHF_STATE_LOWER_HIGH_CONFIRMED;")
    assert rejected_pivot < before_arm < lower_high_state
    touched = signal.index("const bool touched_second_break")
    consumed = signal.index('ConsumeR2LhfSetup("r2_lhf_first_second_break_consumed")')
    body = signal.index("const double body_fraction", consumed)
    quality = signal.index("const bool accepted_second_break", consumed)
    assert touched < consumed < body < quality
    assert '"r2_lhf_first_second_break_rejected"' in signal


def test_mode24_hard_risk_is_ordercalcprofit_based_and_precedes_claim() -> None:
    source = _ea_text()
    hard_risk = _function_block(source, "bool R2LhfHardRiskAllowed", "double RecentHigh")
    assert "const double hard_limit_usd = 50.00;" in hard_risk
    assert 'AccountInfoString(ACCOUNT_CURRENCY) != "USD"' in hard_risk
    assert "MathAbs(InpMaxRiskOvershootPct) > 0.0000001" in hard_risk
    assert "OrderCalcProfit(ORDER_TYPE_SELL" in hard_risk
    lots = source.index("const double order_lots = LotsForStopDistance(stop_distance);")
    exact_risk = source.index("R2LhfHardRiskAllowed(direction, stop_distance, order_lots, bid, ask, actual_risk_usd)")
    claim_time = source.index("const datetime claim_signal_time", exact_risk)
    claim = source.index("if(!ClaimSignalSlot(direction, claim_signal_time", claim_time)
    assert lots < exact_risk < claim_time < claim
    assert '"reason", "actual_risk_usd"' in source
    assert '"pass", logged_actual_risk_usd' in source


def test_r2_lhf_complete_runner_guards_before_historical_invocation() -> None:
    source = RUNNER_PATH.read_text(encoding="utf-8")
    guard = source.index("if not HISTORICAL_RUN_AUTHORIZED:")
    invocation = source.index("mt5.run_variants(", guard)
    assert guard < invocation
    assert 'raise RuntimeError("Historical execution is locked pending explicit authorization")' in source


def _valid_lifecycle_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    event_id = "R2LHF_2000"
    common = (
        f"|event_id={event_id}|setup_time=2000|setup=DOWN|phase=ESTABLISHED"
        "|shock=0|maturity=3|pivot_time=3000|confirm_time=5700"
    )
    signal_rows = [
        {
            "timestamp_broker": "2026.01.01 08:00:00",
            "stage": "R2_LHF_D1_OWNERSHIP",
            "direction": "NONE",
            "reason": (
                "R2_LHF_D1_OWNERSHIP|d1_time=1000|mature=1|state=downtrend"
                "|setup=DOWN|phase=ESTABLISHED|shock=0|maturity=3"
            ),
        },
        {
            "timestamp_broker": "2026.01.01 09:00:00",
            "stage": "R2_LHF_LEG_ONE_REGISTERED",
            "direction": "NONE",
            "reason": "R2_LHF_LIFECYCLE" + common + "|from=IDLE|to=WAIT_FIRST_PIVOT|outcome=leg_one_armed",
        },
        {
            "timestamp_broker": "2026.01.01 09:45:00",
            "stage": "R2_LHF_FIRST_PIVOT_CONFIRMED",
            "direction": "NONE",
            "reason": (
                "R2_LHF_LIFECYCLE"
                + common
                + "|from=WAIT_FIRST_PIVOT|to=LOWER_HIGH_CONFIRMED|outcome=first_pivot_confirmed"
            ),
        },
        {
            "timestamp_broker": "2026.01.01 10:00:00",
            "stage": "R2_LHF_EVENT_CONSUMED",
            "direction": "NONE",
            "reason": (
                "R2_LHF_LIFECYCLE"
                + common
                + "|from=LOWER_HIGH_CONFIRMED|to=IDLE|outcome=r2_lhf_first_second_break_consumed"
            ),
        },
        {
            "timestamp_broker": "2026.01.01 10:00:00",
            "stage": "WOULD_SIGNAL",
            "direction": "SHORT",
            "reason": "R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_STATE_downtrend" + common,
        },
    ]
    order_rows = [
        {
            "timestamp_broker": "2026.01.01 10:00:00",
            "action": "ORDER_SEND_OK",
            "direction": "SHORT",
            "actual_risk_usd": "50.000000",
            "reason": "pass",
        }
    ]
    return signal_rows, order_rows


def test_real_log_lifecycle_audit_reconstructs_one_scalar_event() -> None:
    signal_rows, order_rows = _valid_lifecycle_rows()
    result = runner.lifecycle_audit(signal_rows, order_rows)
    assert result["registered_events"] == 1
    assert result["pivot_events"] == 1
    assert result["consumed_events"] == 1
    assert result["signal_events"] == 1
    assert result["ownership_episode_count"] == 1
    assert result["registered_episode_ids"] == {"R2LHF_2000": 1}
    for key in (
        "duplicate_registrations",
        "duplicate_pivots",
        "duplicate_consumptions",
        "missing_consumptions",
        "active_state_overwrite_violations",
        "transition_violations",
        "future_bar_violations",
        "retrospective_entry_violations",
        "native_setup_failures",
        "native_signal_failures",
        "missing_executed_signal_matches",
    ):
        assert result[key] == [], (key, result[key])


def test_real_log_lifecycle_audit_detects_future_pivot_and_duplicate_consumption() -> None:
    signal_rows, order_rows = _valid_lifecycle_rows()
    signal_rows[2]["reason"] = signal_rows[2]["reason"].replace("confirm_time=5700", "confirm_time=4800")
    signal_rows.insert(4, dict(signal_rows[3]))
    result = runner.lifecycle_audit(signal_rows, order_rows)
    assert result["future_bar_violations"] == ["R2LHF_2000"]
    assert result["duplicate_consumptions"] == ["R2LHF_2000"]
    assert result["transition_violations"]


def test_risk_artifact_requires_machine_readable_success_risk_lte_50() -> None:
    _signals, order_rows = _valid_lifecycle_rows()
    result = {"mt5_report_metrics": {"Total Trades": "1"}}
    audit = runner.risk_execution_audit(result, order_rows, [{"exit_time": object()}])
    assert audit["successful_orders"] == 1
    assert audit["missing_initial_risk_calculations"] == 0
    assert audit["actual_initial_risk_usd"]["maximum"] == 50.0
    assert audit["actual_initial_risk_usd"]["above_50_count"] == 0

    order_rows[0]["actual_risk_usd"] = ""
    missing = runner.risk_execution_audit(result, order_rows, [{"exit_time": object()}])
    assert missing["missing_initial_risk_calculations"] == 1


def test_global_window_gate_contract_passes_only_complete_evidence() -> None:
    checks = runner.window_gate_checks(_passing_metrics())
    assert all(value for group in checks.values() for value in group.values()), checks

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
    assert runner.decide(static, windows) == "R2_LHF_SECOND_CONTINUATION_FULLY_QUALIFIED"

    windows[1]["drawdown_checks"]["equity_dd_relative_lte_20"] = False
    assert runner.decide(static, windows) == (
        "R2_LHF_SECOND_CONTINUATION_ALPHA_ONLY_RISK_REPAIR_REQUIRED"
    )

    windows[0]["alpha_checks"]["wr_ge_50"] = False
    assert runner.decide(static, windows) == "R2_LHF_SECOND_CONTINUATION_REJECT"
