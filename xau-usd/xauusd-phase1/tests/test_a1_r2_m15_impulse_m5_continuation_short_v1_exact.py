from __future__ import annotations

import copy
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
RUNNER_PATH = SCRIPTS / "run_a1_r2_m15_impulse_m5_continuation_short_v1_exact.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r2_m15_impulse_m5_continuation_short_v1_exact as runner  # noqa: E402


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


def _valid_lifecycle_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    event_id = "R2ICR_2000"
    common = (
        f"|event_id={event_id}|setup_time=2000|impulse_bar_time=1100|impulse_time=2000"
        "|m15_shift=1|backfill=0"
        "|setup=DOWN|phase=ESTABLISHED|shock=0|maturity=3"
    )
    signals = [
        {
            "timestamp_broker": "2026.01.01 08:00:00",
            "stage": "R2_ICR_D1_OWNERSHIP",
            "direction": "NONE",
            "reason": (
                "R2_ICR_D1_OWNERSHIP|d1_time=1000|mature=1|state=downtrend"
                "|d1_shift=1|backfill=0|direction_state=DOWN|h4_down=1"
                "|d1_shift1_time=1000|d1_shift2_time=900|d1_shift3_time=800|h4_time=1900"
                "|setup=DOWN|phase=ESTABLISHED|shock=0|maturity=3"
            ),
        },
        {
            "timestamp_broker": "2026.01.01 09:00:00",
            "stage": "R2_ICR_IMPULSE_REGISTERED",
            "direction": "NONE",
            "reason": (
                "R2_ICR_LIFECYCLE"
                + common
                + "|from=IDLE|to=WAIT_FIRST_M5_BREAK|outcome=impulse_registered"
            ),
        },
        {
            "timestamp_broker": "2026.01.01 09:05:00",
            "stage": "R2_ICR_ENTRY_DECISION",
            "direction": "NONE",
            "reason": (
                "R2_ICR_ENTRY_DECISION"
                + common
                + "|decision_bar_time=2300|entry_bar_ordinal=1|touch=1|owned=1"
            ),
        },
        {
            "timestamp_broker": "2026.01.01 09:05:00",
            "stage": "R2_ICR_EVENT_CONSUMED",
            "direction": "NONE",
            "reason": (
                "R2_ICR_LIFECYCLE"
                + common
                + "|attempt_time=2300|attempt_ordinal=1|entry_bars_seen=1"
                + "|from=WAIT_FIRST_M5_BREAK|to=IDLE|outcome=first_break_attempt"
            ),
        },
        {
            "timestamp_broker": "2026.01.01 09:05:00",
            "stage": "WOULD_SIGNAL",
            "direction": "SHORT",
            "reason": (
                "R2_M15_IMPULSE_M5_CONTINUATION_SHORT_STATE_downtrend"
                + common
                + "|attempt_time=2300|attempt_ordinal=1"
            ),
        },
    ]
    orders = [
        {
            "timestamp_broker": "2026.01.01 09:05:00",
            "action": "ORDER_SEND_OK",
            "direction": "SHORT",
            "actual_risk_usd": "49.900000",
            "reason": "pass",
        }
    ]
    return signals, orders


def _hold_decision(
    ordinal: int,
    decision_time: int,
    *,
    timestamp: str,
    owned: str = "1",
) -> dict[str, str]:
    return {
        "timestamp_broker": timestamp,
        "stage": "R2_ICR_HOLD_DECISION",
        "direction": "SHORT",
        "reason": (
            "R2_ICR_HOLD_DECISION|event_id=R2ICR_2000|entry_time=2300"
            f"|decision_bar_time={decision_time}|hold_bar_ordinal={ordinal}"
            f"|position_id=P1|ticket=T1|position_open=1|owned={owned}"
        ),
    }


def _position_exit(
    ordinal: int,
    decision_time: int,
    *,
    timestamp: str,
    outcome: str = "structural_time_exit",
) -> dict[str, str]:
    return {
        "timestamp_broker": timestamp,
        "stage": "R2_ICR_POSITION_EXIT",
        "direction": "SHORT",
        "reason": (
            f"R2_ICR_POSITION_EXIT|event_id=R2ICR_2000|outcome={outcome}"
            f"|entry_time=2300|decision_bar_time={decision_time}|hold_bar_ordinal={ordinal}"
            "|position_id=P1|ticket=T1|close_attempted=1|close_succeeded=1"
        ),
    }


def test_mode27_is_one_frozen_complete_but_locked_runner() -> None:
    variants = runner.build_variants()
    checks = runner.static_checks(variants)
    assert len(variants) == 1
    assert variants[0].name == runner.VARIANT_NAME
    assert variants[0].tester_inputs == runner.FROZEN_INPUTS
    assert all(checks.values()), checks
    assert runner.RUNNER_COMPLETE is True
    assert runner.HISTORICAL_RUN_AUTHORIZED is False
    assert runner.PREREG.exists()


def test_mode27_hash_windows_and_reserved_identity_are_frozen() -> None:
    assert runner.PROPOSED_SIGNAL_MODE == 27
    assert [(row["from_date"], row["to_date"]) for row in runner.WINDOWS] == [
        ("2016.01.01", "2021.12.31"),
        ("2022.07.01", "2026.06.30"),
    ]
    assert runner.stable_hash(runner.FROZEN_INPUTS) == (
        "58621fea70c35ecda9eabbb18877158aff660482b93041bf50e2eb03ff18d3c4"
    )
    assert runner.stable_hash(runner.FROZEN_INPUTS) == runner.EXPECTED_FROZEN_INPUT_SHA256


def test_mode24_counts_are_diagnostic_but_nonconforming() -> None:
    pre = runner.MODE24_DIAGNOSIS["prehistory_201601_202112"]
    primary = runner.MODE24_DIAGNOSIS["primary_202207_202606"]
    assert (pre["registered"], pre["pivots"], pre["first_break_attempts"], pre["would_signals"], pre["executions"]) == (120, 40, 25, 3, 0)
    assert (primary["registered"], primary["pivots"], primary["first_break_attempts"], primary["would_signals"], primary["executions"]) == (82, 28, 15, 5, 2)
    assert pre["continuation_without_reset"] == 66
    assert primary["continuation_without_reset"] == 50
    assert runner.MODE24_CAUSAL_STATUS == "NONCONFORMING_WALL_CLOCK_LIFETIME_DIAGNOSTIC_ONLY"


def test_mode27_is_not_a_mode22_or_mode24_or_calendar_sibling() -> None:
    inputs = runner.FROZEN_INPUTS
    assert inputs["InpSignalMode"] == "27"
    assert not any(key.startswith("InpR2Pdl") for key in inputs)
    assert not any(key.startswith("InpR2Lhf") for key in inputs)
    assert not any(key.startswith("InpR2Pullback") for key in inputs)
    assert not any(key.startswith("InpBearImpulseRetest") for key in inputs)
    assert inputs["InpMinAtrAbsoluteForEntry"] == "0.00"
    assert inputs["InpBlockedEntryHoursCsv"] == ""
    assert inputs["InpBlockedEntryDayHoursCsv"] == ""
    prereg = runner.PREREG.read_text(encoding="utf-8")
    assert "has no H1 leg, pivot, lower-high, or reset state" in prereg
    assert "first M5 continuation attempt" in prereg
    assert "entry_m5_bars_seen=0" in prereg
    assert "hold_m5_bars_seen=0" in prereg
    assert "elapsed seconds" in prereg
    source = RUNNER_PATH.read_text(encoding="utf-8")
    assert "entry_window_" + "seconds" not in source
    assert ".total_seconds()" + " / 300.0" not in source


def test_mode27_repeats_per_impulse_but_consumes_each_event_once() -> None:
    inputs = runner.FROZEN_INPUTS
    assert inputs["InpR2IcrImpulseLookbackM15Bars"] == "8"
    assert inputs["InpR2IcrEntryWindowM5Bars"] == "3"
    assert inputs["InpR2IcrConsumeFirstBreak"] == "true"
    assert inputs["InpR2IcrMaxHoldM5Bars"] == "12"
    assert inputs["InpR2IcrExitOnOwnershipLoss"] == "true"
    assert inputs["InpOnePositionPerMagic"] == "true"
    assert inputs["InpMaxOpenPositionsPerMagic"] == "1"


def test_mode27_hard_risk_and_payoff_contract_are_frozen() -> None:
    inputs = runner.FROZEN_INPUTS
    assert runner.DEPOSIT_USD == 10_000.0
    assert runner.RISK_AMOUNT_USD == 50.0
    assert inputs["InpRiskReward"] == "2.00"
    assert inputs["InpUseRiskNormalizedLots"] == "true"
    assert inputs["InpRiskAmountUsd"] == "50.00"
    assert inputs["InpRejectRiskOvershootEnabled"] == "true"
    assert inputs["InpMaxRiskOvershootPct"] == "0.00"
    assert "OrderCalcProfit(ORDER_TYPE_SELL" in runner.REQUIRED_EA_TOKENS
    assert "r2_icr_normalized_entry_to_stop_risk_overshoot" in runner.REQUIRED_EA_TOKENS


def test_mode27_identity_is_reserved_but_implementation_and_history_remain_locked() -> None:
    readiness = runner.implementation_readiness()
    assert not all(readiness.values())
    assert readiness["SIGNAL_R2_M15_IMPULSE_M5_CONTINUATION_SHORT = 27"] is True
    assert any(not ready for token, ready in readiness.items() if "SIGNAL_R2_M15" not in token)
    source = RUNNER_PATH.read_text(encoding="utf-8")
    guard = source.index("if not HISTORICAL_RUN_AUTHORIZED:")
    control_preflight = source.index("control_readiness = overlap_control_readiness()", guard)
    invocation = source.index("mt5.run_variants(", guard)
    assert guard < control_preflight < invocation


def test_mode27_lifecycle_audit_reconstructs_native_scalar_impulse() -> None:
    signals, orders = _valid_lifecycle_rows()
    audit = runner.lifecycle_audit(signals, orders)
    assert audit["registered_events"] == 1
    assert audit["consumed_events"] == 1
    assert audit["signal_events"] == 1
    assert len(audit["entry_decision_rows"]) == 1
    assert audit["ownership_episode_count"] == 1
    assert audit["registered_episode_ids"] == {"R2ICR_2000": 1}
    for key in (
        "duplicate_registrations",
        "duplicate_consumptions",
        "duplicate_signals",
        "missing_consumptions",
        "active_state_overwrite_violations",
        "transition_violations",
        "future_bar_violations",
        "retrospective_entry_violations",
        "native_setup_failures",
        "native_signal_failures",
        "ownership_observation_violations",
        "impulse_registration_violations",
        "missing_executed_signal_matches",
        "entry_counter_violations",
        "hold_counter_violations",
        "orphan_position_exits",
        "invalid_position_exits",
    ):
        assert audit[key] == [], (key, audit[key])


def test_mode27_lifecycle_audit_fails_backfill_and_duplicate_consumption() -> None:
    signals, orders = _valid_lifecycle_rows()
    signals[1]["reason"] = signals[1]["reason"].replace("backfill=0", "backfill=1")
    signals.insert(4, dict(signals[3]))
    audit = runner.lifecycle_audit(signals, orders)
    assert audit["future_bar_violations"] == ["R2ICR_2000"]
    assert audit["duplicate_consumptions"] == ["R2ICR_2000"]
    assert audit["transition_violations"]


def test_mode27_registration_requires_exact_completed_m15_and_latest_owned_context() -> None:
    signals, orders = _valid_lifecycle_rows()
    signals[1]["reason"] = signals[1]["reason"].replace(
        "impulse_bar_time=1100", "impulse_bar_time=1000"
    )
    bad_time = runner.lifecycle_audit(signals, orders)
    assert bad_time["future_bar_violations"] == ["R2ICR_2000"]

    signals, orders = _valid_lifecycle_rows()
    unowned = runner.lifecycle_audit(signals[1:], orders)
    assert unowned["native_setup_failures"] == ["R2ICR_2000"]


def test_mode27_mature_false_ownership_does_not_create_an_episode() -> None:
    ownership = {
        "stage": "R2_ICR_D1_OWNERSHIP",
        "reason": (
            "R2_ICR_D1_OWNERSHIP|d1_time=1000|d1_shift=1|backfill=0|mature=0"
            "|state=chop|direction_state=NEUTRAL|h4_down=0|setup=NONE"
            "|d1_shift1_time=1000|d1_shift2_time=900|d1_shift3_time=800|h4_time=1900"
            "|phase=TRANSITION|shock=0|maturity=3"
        ),
    }
    audit = runner.lifecycle_audit([ownership], [])
    assert audit["ownership_observation_violations"] == []
    assert audit["ownership_episode_count"] == 0


def test_mode27_first_attempt_requires_first_logged_touch_and_owned_decisions() -> None:
    signals, orders = _valid_lifecycle_rows()
    signals[2]["reason"] = signals[2]["reason"].replace("touch=1", "touch=0")
    no_touch = runner.lifecycle_audit(signals, orders)
    assert "R2ICR_2000|attempt_ordinal" in no_touch["entry_counter_violations"]

    signals, orders = _valid_lifecycle_rows()
    signals[2]["reason"] = signals[2]["reason"].replace("owned=1", "owned=0")
    unowned = runner.lifecycle_audit(signals, orders)
    assert "R2ICR_2000|attempt_ordinal" in unowned["entry_counter_violations"]


def test_mode27_tester_deinit_is_truthful_right_censoring() -> None:
    signals, _ = _valid_lifecycle_rows()
    rows = signals[:2]
    common = (
        "|event_id=R2ICR_2000|setup_time=2000|impulse_bar_time=1100|impulse_time=2000"
        "|m15_shift=1|backfill=0|setup=DOWN|phase=ESTABLISHED|shock=0|maturity=3"
    )
    rows.append(
        {
            "stage": "R2_ICR_EVENT_CONSUMED",
            "reason": (
                "R2_ICR_LIFECYCLE"
                + common
                + "|entry_bars_seen=0|deinit=1|from=WAIT_FIRST_M5_BREAK|to=IDLE"
                "|outcome=tester_deinit"
            ),
        }
    )
    audit = runner.lifecycle_audit(rows, [])
    assert audit["tester_deinit_events"] == 1
    assert audit["entry_counter_violations"] == []
    rows[-1]["reason"] = rows[-1]["reason"].replace("deinit=1", "deinit=0")
    invalid = runner.lifecycle_audit(rows, [])
    assert "R2ICR_2000|tester_deinit" in invalid["entry_counter_violations"]


def test_mode27_lifecycle_audit_rejects_bad_attempt_time_and_unowned_exit() -> None:
    signals, orders = _valid_lifecycle_rows()
    signals[-1]["reason"] = signals[-1]["reason"].replace("attempt_time=2300", "attempt_time=2000")
    signals.extend(
        [
            {
                "timestamp_broker": "2026.01.01 09:10:00",
                "stage": "R2_ICR_POSITION_EXIT",
                "direction": "SHORT",
                "reason": (
                    "R2_ICR_POSITION_EXIT|event_id=R2ICR_ORPHAN"
                    "|outcome=ownership_exit|close_attempted=1|hold_bar_ordinal=2"
                ),
            },
            {
                "timestamp_broker": "2026.01.01 09:10:00",
                "stage": "R2_ICR_POSITION_EXIT",
                "direction": "SHORT",
                "reason": (
                    "R2_ICR_POSITION_EXIT|event_id=R2ICR_2000"
                    "|outcome=generic_management|close_attempted=0|hold_bar_ordinal=0"
                ),
            },
        ]
    )
    audit = runner.lifecycle_audit(signals, orders)
    assert audit["retrospective_entry_violations"] == ["R2ICR_2000"]
    assert audit["orphan_position_exits"] == ["R2ICR_ORPHAN"]
    assert audit["invalid_position_exits"] == ["R2ICR_2000"]


def test_mode27_entry_counter_allows_wall_clock_gap_between_completed_bars() -> None:
    signals, orders = _valid_lifecycle_rows()
    for row in signals:
        row["reason"] = row["reason"].replace("decision_bar_time=2300", "decision_bar_time=200000")
        row["reason"] = row["reason"].replace("attempt_time=2300", "attempt_time=200000")
    audit = runner.lifecycle_audit(signals, orders)
    assert audit["entry_counter_violations"] == []
    assert audit["retrospective_entry_violations"] == []


def test_mode27_holding_audit_uses_completed_bar_ordinals_not_elapsed_time() -> None:
    entry = datetime(2026, 1, 2, 20, 55)
    rows = [
        {
            "entry_time": entry,
            "exit_time": entry + timedelta(days=2, hours=2),
            "event_id": "R2ICR_2000",
        }
    ]
    signals, orders = _valid_lifecycle_rows()
    for ordinal, decision_time in ((1, 200000), (2, 200300)):
        signals.append(
            _hold_decision(
                ordinal,
                decision_time,
                timestamp="2026.01.04 23:00:00",
            )
        )
    lifecycle = runner.lifecycle_audit(signals, orders)
    passed = runner.holding_audit(rows, lifecycle)
    assert passed["maximum_holding_m5_bars"] == 2
    assert passed["holding_horizon_violations"] == []


def test_mode27_holding_counter_requires_close_on_completed_bar_12() -> None:
    entry = datetime(2026, 1, 1, 9, 5)
    rows = [{"entry_time": entry, "exit_time": entry + timedelta(hours=1), "event_id": "R2ICR_2000"}]
    signals, orders = _valid_lifecycle_rows()
    for ordinal in range(1, 13):
        signals.append(
            _hold_decision(
                ordinal,
                3000 + ordinal * 300,
                timestamp="2026.01.01 10:05:00",
            )
        )
    failed_lifecycle = runner.lifecycle_audit(signals, orders)
    assert runner.holding_audit(rows, failed_lifecycle)["holding_horizon_violations"] == [
        "R2ICR_2000|horizon_without_close"
    ]
    signals.append(
        _position_exit(
            12,
            3000 + 12 * 300,
            timestamp="2026.01.01 10:05:00",
        )
    )
    passed_lifecycle = runner.lifecycle_audit(signals, orders)
    assert runner.holding_audit(rows, passed_lifecycle)["holding_horizon_violations"] == []


def test_mode27_ownership_exit_joins_hold_decision_and_actual_mt5_exit() -> None:
    entry = datetime(2026, 1, 1, 9, 5)
    rows = [
        {
            "entry_time": entry,
            "exit_time": datetime(2026, 1, 1, 9, 10),
            "event_id": "R2ICR_2000",
        }
    ]
    signals, orders = _valid_lifecycle_rows()
    signals.extend(
        [
            _hold_decision(1, 2600, timestamp="2026.01.01 09:10:00", owned="0"),
            _position_exit(
                1,
                2600,
                timestamp="2026.01.01 09:10:00",
                outcome="ownership_exit",
            ),
        ]
    )
    lifecycle = runner.lifecycle_audit(signals, orders)
    assert lifecycle["hold_counter_violations"] == []
    assert lifecycle["invalid_position_exits"] == []
    holding = runner.holding_audit(rows, lifecycle)
    assert holding["actual_mode_exit_matches"] == 1
    assert holding["holding_horizon_violations"] == []

    rows[0]["exit_time"] = datetime(2026, 1, 1, 9, 30)
    mismatch = runner.holding_audit(rows, lifecycle)
    assert "R2ICR_2000|actual_exit_not_reconciled" in mismatch["holding_horizon_violations"]


def test_mode27_position_exit_requires_successful_close_telemetry() -> None:
    signals, orders = _valid_lifecycle_rows()
    signals.extend(
        [
            _hold_decision(1, 2600, timestamp="2026.01.01 09:10:00", owned="0"),
            _position_exit(
                1,
                2600,
                timestamp="2026.01.01 09:10:00",
                outcome="ownership_exit",
            ),
        ]
    )
    signals[-1]["reason"] = signals[-1]["reason"].replace(
        "close_succeeded=1", "close_succeeded=0"
    )
    lifecycle = runner.lifecycle_audit(signals, orders)
    assert lifecycle["invalid_position_exits"] == ["R2ICR_2000"]


def test_mode27_overlap_controls_exclude_nonconforming_ledgers_and_require_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert len(runner.REQUIRED_OVERLAP_CONTROLS) == 5
    assert not (
        set(runner.REQUIRED_OVERLAP_CONTROLS) & runner.INVALID_COUNTER_OVERLAP_CONTROLS
    )
    assert all(
        runner.CONTROL_PROVENANCE[control]["ready"] is True
        for control in runner.REQUIRED_OVERLAP_CONTROLS
    )
    control = runner.REQUIRED_OVERLAP_CONTROLS[0]
    monkeypatch.setitem(
        runner.CONTROL_PROVENANCE,
        control,
        {"ready": False, "basis": "test_nonconforming"},
    )
    audit = runner.overlap_audit("primary_202207_202606", [])
    row = next(item for item in audit if item["control"] == control)
    assert row["available"] is False
    assert row["provenance_ready"] is False


def test_mode27_global_gates_fail_closed_for_overlap_risk_and_dd() -> None:
    checks = runner.window_gate_checks(_passing_metrics())
    assert all(value for group in checks.values() for value in group.values()), checks

    overlap = _passing_metrics()
    overlap["max_same_direction_overlap_pct"] = 20.0
    assert not runner.window_gate_checks(overlap)["regime_independence_checks"][
        "same_event_overlap_strictly_below_20pct"
    ]
    missing_control = _passing_metrics()
    missing_control["available_overlap_controls"] -= 1
    assert not runner.window_gate_checks(missing_control)["regime_independence_checks"][
        "all_required_overlap_controls_available"
    ]
    risk = _passing_metrics()
    risk["max_executed_initial_risk_usd"] = 50.0001
    assert not runner.window_gate_checks(risk)["execution_risk_checks"][
        "max_executed_initial_risk_lte_50usd"
    ]
    dd = _passing_metrics()
    dd["equity_dd_maximal_usd"] = None
    assert not all(runner.window_gate_checks(dd)["drawdown_checks"].values())


def test_mode27_decision_separates_alpha_and_drawdown_failures() -> None:
    static = runner.static_checks()
    passing = runner.window_gate_checks(_passing_metrics())
    windows = [copy.deepcopy(passing), copy.deepcopy(passing)]
    assert runner.decide(static, windows) == "R2_ICR_M15_M5_CONTINUATION_FULLY_QUALIFIED"
    windows[1]["drawdown_checks"]["equity_dd_relative_lte_20"] = False
    assert runner.decide(static, windows) == (
        "R2_ICR_M15_M5_CONTINUATION_ALPHA_ONLY_RISK_REPAIR_REQUIRED"
    )
    windows[0]["alpha_checks"]["wr_ge_50"] = False
    assert runner.decide(static, windows) == "R2_ICR_M15_M5_CONTINUATION_REJECT"
