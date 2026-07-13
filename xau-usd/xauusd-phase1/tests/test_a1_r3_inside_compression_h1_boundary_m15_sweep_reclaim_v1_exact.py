from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r3_inside_compression_h1_boundary_m15_sweep_reclaim_v1_exact as runner  # noqa: E402


EA = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"


def _context(episode_id: str = "EP1") -> dict[str, str]:
    return {
        "stage": "R3_CHOP_CONTEXT_DECISION",
        "timestamp_broker": "2024.01.02 01:00:00",
        "reason": (
            f"R3_CHOP_CONTEXT|context_id=C1|episode_id={episode_id}|d1_time=1704067200"
            "|d1_shift=1|backfill=0|owned=1|compressed=1|direction_state=NEUTRAL"
            "|shock=0|established=0|transition=0"
        ),
    }


def _h1_decision(event_id: str = "E1", episode_id: str = "EP1") -> dict[str, str]:
    return {
        "stage": "R3_CHOP_H1_DECISION",
        "timestamp_broker": "2024.01.02 01:00:00",
        "reason": (
            f"R3_CHOP_H1|event_id={event_id}|episode_id={episode_id}|context_id=C1"
            "|h1_bar_time=1704153600|setup_time=1704157200|h1_shift=1|backfill=0"
            "|owned=1|action=registered"
        ),
    }


def _registration(event_id: str = "E1", episode_id: str = "EP1") -> dict[str, str]:
    return {
        "stage": "R3_CHOP_EVENT_REGISTERED",
        "timestamp_broker": "2024.01.02 01:00:00",
        "reason": (
            "R3_CHOP_LIFECYCLE"
            f"|event_id={event_id}|episode_id={episode_id}|context_id=C1"
            "|setup_time=1704157200|h1_bar_time=1704153600|h1_shift=1|backfill=0"
            "|boundary_lookback=4|boundary_high=2100.00|boundary_low=2000.00|h1_atr=25.00"
            "|setup=COMPRESSED|entry=COMPRESSED"
            "|direction_state=NEUTRAL|shock=0|established=0|transition=0"
            "|from=IDLE|to=WAIT_FIRST_M15_SWEEP"
        ),
    }


def _decision(event_id: str = "E1", ordinal: int = 1, timestamp: int = 1704158100) -> dict[str, str]:
    return {
        "stage": "R3_CHOP_M15_DECISION",
        "timestamp_broker": "2024.01.02 01:15:00",
        "reason": (
            f"R3_CHOP_LIFECYCLE|event_id={event_id}|decision_bar_time={timestamp}"
            f"|m15_bar_ordinal={ordinal}"
        ),
    }


def _consumption(
    event_id: str = "E1",
    *,
    outcome: str = "entry",
    bars_seen: int = 1,
    attempt_ordinal: int = 1,
) -> dict[str, str]:
    deinit = "1" if outcome == "window_end_incomplete" else "0"
    return {
        "stage": "R3_CHOP_EVENT_CONSUMED",
        "timestamp_broker": "2024.01.02 01:15:00",
        "reason": (
            f"R3_CHOP_LIFECYCLE|event_id={event_id}|outcome={outcome}"
            f"|m15_bars_seen={bars_seen}|attempt_ordinal={attempt_ordinal}"
            f"|deinit={deinit}|from=WAIT_FIRST_M15_SWEEP|to=IDLE"
        ),
    }


def _signal(event_id: str = "E1", *, direction: str = "LONG") -> dict[str, str]:
    return {
        "stage": "WOULD_SIGNAL",
        "timestamp_broker": "2024.01.02 01:15:00",
        "direction": direction,
        "reason": (
            f"R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_{direction}"
            f"|event_id={event_id}|episode_id=EP1|setup=COMPRESSED|entry=COMPRESSED"
            "|direction_state=NEUTRAL|shock=0|established=0|transition=0"
            "|attempt_time=1704158100|attempt_ordinal=1"
        ),
    }


def test_mode28_is_one_frozen_authorized_complete_evaluator() -> None:
    variants = runner.build_variants()
    assert len(variants) == 1
    assert variants[0].tester_inputs == runner.FROZEN_INPUTS
    assert runner.PROPOSED_SIGNAL_MODE == 28
    assert runner.PROPOSED_ROUTER_MODE == 6
    assert runner.RUNNER_COMPLETE is True
    assert runner.HISTORICAL_RUN_AUTHORIZED is True
    assert all(runner.static_checks(variants).values())


def test_frozen_hash_and_two_eras_are_exact() -> None:
    assert runner.stable_hash(runner.FROZEN_INPUTS) == runner.EXPECTED_FROZEN_INPUT_SHA256
    assert runner.EXPECTED_FROZEN_INPUT_SHA256 == (
        "bb8f93fc783b0c08f6a08340310f3197fd9402f1556ccbdb2c890adb95ea47b3"
    )
    assert tuple((row["from_date"], row["to_date"]) for row in runner.WINDOWS) == (
        ("2016.01.01", "2021.12.31"),
        ("2022.07.01", "2026.06.30"),
    )


def test_candidate_is_inside_compression_not_mode25_release_sibling() -> None:
    prereg = runner.PREREG.read_text(encoding="utf-8")
    assert "trades *inside* an\neligible compression episode" in prereg
    assert "never requires an outside-box H1 release, acceptance, or pullback" in prereg
    assert "registers a fresh completed-H1 rolling-range event" in prereg
    assert runner.FROZEN_INPUTS["InpR3ChopH1BoundaryLookback"] == "4"
    assert runner.FROZEN_INPUTS["InpR3ChopEventWindowM15Bars"] == "4"


def test_symmetric_first_sweep_geometry_and_first_event_consumption_are_frozen() -> None:
    inputs = runner.FROZEN_INPUTS
    assert inputs["InpR3ChopSweepM15Atr"] == "0.05"
    assert inputs["InpR3ChopReclaimM15Atr"] == "0.05"
    assert inputs["InpR3ChopLongCloseLocationMin"] == "0.65"
    assert inputs["InpR3ChopShortCloseLocationMax"] == "0.35"
    assert inputs["InpR3ChopConsumeFirstSweep"] == "true"
    assert runner.SIGNAL_PREFIXES == {
        "R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_LONG",
        "R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_SHORT",
    }


def test_completed_bar_counter_and_h1_rollover_order_are_explicit() -> None:
    prereg = runner.PREREG.read_text(encoding="utf-8")
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "process the active event before registering" in prereg
    assert "Weekend, maintenance,\nand missing-market gaps consume no decision slots" in prereg
    assert "elapsed seconds are never converted" in prereg
    assert ".total_seconds() / 900" not in source
    assert "event_window_seconds" not in source


def test_no_masks_one_position_fixed_2r_and_hard_risk_are_frozen() -> None:
    inputs = runner.FROZEN_INPUTS
    assert inputs["InpRiskReward"] == "2.00"
    assert inputs["InpRiskAmountUsd"] == "50.00"
    assert inputs["InpRejectRiskOvershootEnabled"] == "true"
    assert inputs["InpMaxRiskOvershootPct"] == "0.00"
    assert inputs["InpOnePositionPerMagic"] == "true"
    assert inputs["InpMaxOpenPositionsPerMagic"] == "1"
    assert inputs["InpMaxTradesPerDay"] == "0"
    assert inputs["InpCooldownMinutes"] == "0"
    assert all(
        inputs[key] == ""
        for key in (
            "InpBlockedEntryHoursCsv",
            "InpBlockedEntryDayHoursCsv",
            "InpBlockedLongEntryHoursCsv",
            "InpBlockedShortEntryHoursCsv",
        )
    )
    assert inputs["InpPortfolioDailyGuardEnabled"] == "false"


def test_history_authorization_and_implementation_gate_precede_any_mt5_run() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")
    lock = source.index("if not HISTORICAL_RUN_AUTHORIZED:")
    run = source.index("exact = mt5.run_variants(")
    readiness = source.index("readiness = implementation_readiness()")
    assert readiness < lock < run
    assert "SIGNAL_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM = 28" in EA.read_text(
        encoding="utf-8"
    )
    assert all(runner.implementation_readiness().values())
    assert runner.HISTORICAL_RUN_AUTHORIZED is True


def test_future_authorization_does_not_invalidate_static_freeze(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner, "HISTORICAL_RUN_AUTHORIZED", True)
    assert all(runner.static_checks().values())


def test_lifecycle_audit_accepts_one_native_consumed_event_and_execution() -> None:
    signals = [_context(), _h1_decision(), _registration(), _decision(), _consumption(), _signal()]
    orders = [
        {
            "action": "ORDER_SEND_OK",
            "timestamp_broker": "2024.01.02 01:15:00",
            "direction": "LONG",
        }
    ]
    audit = runner.lifecycle_audit(signals, orders)
    assert audit["registered_events"] == 1
    assert audit["consumed_events"] == 1
    assert audit["signal_events"] == 1
    assert audit["duplicate_consumptions"] == []
    assert audit["transition_violations"] == []
    assert audit["completed_bar_counter_violations"] == []
    assert audit["context_decision_violations"] == []
    assert audit["h1_decision_violations"] == []
    assert audit["retrospective_entry_violations"] == []
    assert audit["native_setup_failures"] == []
    assert audit["native_signal_failures"] == []
    assert audit["missing_executed_signal_matches"] == []
    assert audit["executed_event_ids"] == ["E1"]


def test_lifecycle_audit_rejects_counter_gap_and_signal_before_consumption() -> None:
    bad_decision = _decision(ordinal=2)
    rows = [_context(), _h1_decision(), _registration(), bad_decision, _signal(), _consumption()]
    audit = runner.lifecycle_audit(rows, [])
    assert "E1|decision_sequence" in audit["completed_bar_counter_violations"]
    assert audit["retrospective_entry_violations"] == ["E1"]


def test_expiry_requires_exactly_four_completed_m15_decisions() -> None:
    decisions = [
        _decision(ordinal=ordinal, timestamp=1704157200 + ordinal * 900)
        for ordinal in range(1, 5)
    ]
    consumed = _consumption(outcome="expired", bars_seen=4, attempt_ordinal=0)
    audit = runner.lifecycle_audit([_registration(), *decisions, consumed], [])
    assert audit["completed_bar_counter_violations"] == []
    early = runner.lifecycle_audit(
        [_registration(), decisions[0], _consumption(outcome="expired", bars_seen=1)], []
    )
    assert "E1|expiry" in early["completed_bar_counter_violations"]


def test_registration_cannot_self_assert_owned_context_or_h1_causality() -> None:
    audit = runner.lifecycle_audit([_registration(), _consumption(outcome="shock", bars_seen=0)], [])
    assert audit["native_setup_failures"] == ["E1"]


def test_orphan_registered_h1_decision_is_rejected() -> None:
    audit = runner.lifecycle_audit([_context(), _h1_decision()], [])
    assert audit["h1_decision_violations"] == ["E1"]


def test_registration_must_join_latest_context_and_cannot_reactivate_after_handoff() -> None:
    ineligible = {
        "stage": "R3_CHOP_CONTEXT_DECISION",
        "reason": (
            "R3_CHOP_CONTEXT|context_id=C2|d1_time=1704153600|d1_shift=1|backfill=0"
            "|owned=0|compressed=0|direction_state=NEUTRAL|shock=0|established=0|transition=0"
        ),
    }
    latest = runner.lifecycle_audit(
        [_context(), ineligible, _h1_decision(), _registration(), _consumption(outcome="shock", bars_seen=0)],
        [],
    )
    assert latest["native_setup_failures"] == ["E1"]

    suspended = runner.lifecycle_audit(
        [
            _context(),
            _h1_decision(),
            _registration(),
            _consumption(outcome="trend_handoff", bars_seen=0),
            _h1_decision("E2"),
            _registration("E2"),
            _consumption("E2", outcome="shock", bars_seen=0),
        ],
        [],
    )
    assert "E2" in suspended["native_setup_failures"]


def test_consecutive_owned_contexts_must_keep_one_episode_id() -> None:
    next_context = {
        "stage": "R3_CHOP_CONTEXT_DECISION",
        "reason": (
            "R3_CHOP_CONTEXT|context_id=C2|episode_id=EP2|d1_time=1704153600"
            "|d1_shift=1|backfill=0|owned=1|compressed=1|direction_state=NEUTRAL"
            "|shock=0|established=0|transition=0"
        ),
    }
    audit = runner.lifecycle_audit([_context(), next_context], [])
    assert "C2|episode_continuity" in audit["context_decision_violations"]


def test_explicit_prior_context_suspension_allows_a_new_episode() -> None:
    next_context = {
        "stage": "R3_CHOP_CONTEXT_DECISION",
        "reason": (
            "R3_CHOP_CONTEXT|context_id=C2|episode_id=EP2|d1_time=1704153600"
            "|d1_shift=1|backfill=0|prior_context_suspended=1"
            "|owned=1|compressed=1|direction_state=NEUTRAL"
            "|shock=0|established=0|transition=0"
        ),
    }
    audit = runner.lifecycle_audit([_context(), next_context], [])
    assert audit["context_decision_violations"] == []


def test_right_censoring_is_separate_and_counted() -> None:
    rows: list[dict[str, str]] = []
    for event_id, episode in (("E1", "EP1"), ("E2", "EP2")):
        rows.extend(
            [
                _registration(event_id, episode),
                _consumption(
                    event_id,
                    outcome="window_end_incomplete",
                    bars_seen=0,
                    attempt_ordinal=0,
                ),
            ]
        )
    audit = runner.lifecycle_audit(rows, [])
    assert audit["window_end_incomplete_events"] == 2
    assert audit["window_end_incomplete_event_ids"] == ["E1", "E2"]
    assert audit["invalid_consumption_outcomes"] == []


def test_handoffs_are_terminal_owned_outcomes_not_entry_permissions() -> None:
    assert {"shock", "trend_handoff", "transition_handoff", "compression_lost"}.issubset(
        runner.ALLOWED_CONSUMPTION_OUTCOMES
    )
    prereg = runner.PREREG.read_text(encoding="utf-8")
    assert "the entire daily context are terminated immediately" in prereg
    assert "Mode 28 does not steal release,\ntransition, or established-trend trades" in prereg


def test_overlap_controls_cover_both_eras_and_closest_failed_family() -> None:
    assert len(runner.CONTROL_PATHS["prehistory_201601_202112"]) == 2
    assert len(runner.CONTROL_PATHS["primary_202207_202606"]) == 4
    assert "r4_m5_failed_break_killed" in runner.CONTROL_PATHS["primary_202207_202606"]
    assert all(
        "mode24" not in control
        for paths in runner.CONTROL_PATHS.values()
        for control in paths
    )
    assert all(
        runner.CONTROL_PROVENANCE[control]["ready"] is True
        for paths in runner.CONTROL_PATHS.values()
        for control in paths
    )
    assert all(path.exists() for paths in runner.CONTROL_PATHS.values() for path in paths.values())


def test_overlap_availability_fails_closed_on_bad_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        runner.CONTROL_PROVENANCE,
        "r1_box_clean_control",
        {"ready": False, "basis": "test_nonconforming"},
    )
    rows = runner.overlap_audit("prehistory_201601_202112", [])
    control = next(row for row in rows if row["control"] == "r1_box_clean_control")
    assert control["available"] is False
    assert control["provenance_ready"] is False


def test_global_gates_cover_direction_purity_concentration_and_drawdown() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")
    for token in (
        '"global_trades_ge_200"',
        '"long_trades_ge_50"',
        '"short_trades_ge_50"',
        '"episode_share_lte_50"',
        '"both_windows_non_drawdown_pass"',
        '"both_windows_drawdown_pass"',
        '"worst_equity_dd_lte_20"',
        '"each_window_net_to_equity_dd_ge_2"',
        '"each_window_equity_to_closed_dd_lte_2"',
    ):
        assert token in source


def test_decision_separates_alpha_failure_from_drawdown_failure() -> None:
    static = {"ready": True}
    checks = {
        "global_pf_ge_2": True,
        "both_windows_drawdown_pass": True,
        "worst_balance_dd_lte_20": True,
        "worst_equity_dd_lte_20": True,
        "each_window_net_to_equity_dd_ge_2": True,
        "each_window_equity_to_closed_dd_lte_2": True,
    }
    windows = [{}, {}]
    assert runner.decide(static, windows, {"checks": checks}).endswith("FULLY_QUALIFIED")
    alpha_bad = dict(checks, global_pf_ge_2=False)
    assert runner.decide(static, windows, {"checks": alpha_bad}).endswith("REJECT")
    dd_bad = dict(checks, worst_equity_dd_lte_20=False)
    assert runner.decide(static, windows, {"checks": dd_bad}).endswith(
        "ALPHA_ONLY_RISK_REPAIR_REQUIRED"
    )
