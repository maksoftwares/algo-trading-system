from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA_PATH = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"


@dataclass(frozen=True)
class EntryObservation:
    counted: bool
    ordinal: int
    outcome: str
    candidate: bool = False
    order_allowed: bool = False
    trace: tuple[str, ...] = ()


@dataclass
class RepeatingImpulseReference:
    """Identity-only reference model for the frozen mode-27 scalar lifecycle."""

    entry_limit: int = 3
    last_scanned_m15_bar: int = 0
    active_event_id: str = ""
    impulse_time: int = 0
    last_counted_m5_bar: int = 0
    entry_bars_seen: int = 0
    registrations: list[str] = field(default_factory=list)
    consumptions: list[tuple[str, str, int]] = field(default_factory=list)

    def scan_completed_m15(self, bar_open_time: int, qualifies: bool) -> str:
        if bar_open_time <= 0:
            raise ValueError("completed M15 identity must be positive")
        if self.last_scanned_m15_bar == 0:
            self.last_scanned_m15_bar = bar_open_time
            return "initialized_no_backfill"
        if bar_open_time == self.last_scanned_m15_bar:
            return "duplicate"
        if bar_open_time < self.last_scanned_m15_bar:
            raise ValueError("completed M15 bars must be observed causally")

        self.last_scanned_m15_bar = bar_open_time
        if self.active_event_id:
            return "active_event_not_overwritten"
        if not qualifies:
            return "not_impulse"

        self.impulse_time = bar_open_time + 900
        self.active_event_id = f"R2ICR_{self.impulse_time}"
        self.last_counted_m5_bar = 0
        self.entry_bars_seen = 0
        self.registrations.append(self.active_event_id)
        return "registered"

    def _consume(self, outcome: str) -> None:
        self.consumptions.append(
            (self.active_event_id, outcome, self.entry_bars_seen)
        )
        self.active_event_id = ""

    def observe_completed_m5(
        self,
        bar_close_time: int,
        *,
        owned: bool,
        touch: bool,
        quality_ok: bool = False,
        guards_ok: bool = False,
    ) -> EntryObservation:
        if not self.active_event_id:
            return EntryObservation(False, self.entry_bars_seen, "inactive")
        if bar_close_time <= self.impulse_time:
            return EntryObservation(False, self.entry_bars_seen, "anchor_or_earlier")
        if bar_close_time == self.last_counted_m5_bar:
            return EntryObservation(False, self.entry_bars_seen, "duplicate")
        if self.last_counted_m5_bar and bar_close_time < self.last_counted_m5_bar:
            raise ValueError("completed M5 bars must be observed causally")

        self.last_counted_m5_bar = bar_close_time
        self.entry_bars_seen += 1
        trace = ["entry_decision", "ownership"]
        if not owned:
            # Ownership is resolved before price touch. An unowned decision cannot be
            # represented later as the first-break attempt.
            trace.append("consume:ownership_lost")
            self._consume("ownership_lost")
            return EntryObservation(
                True,
                self.entry_bars_seen,
                "ownership_lost",
                trace=tuple(trace),
            )

        trace.append("touch")
        if touch:
            # The event becomes unavailable before quality or any execution guard.
            trace.append("consume:first_break_attempt")
            self._consume("first_break_attempt")
            trace.append("quality")
            candidate = quality_ok
            trace.append("guards")
            return EntryObservation(
                True,
                self.entry_bars_seen,
                "first_break_attempt",
                candidate=candidate,
                order_allowed=candidate and guards_ok,
                trace=tuple(trace),
            )

        if self.entry_bars_seen == self.entry_limit:
            trace.append("consume:entry_window_expired")
            self._consume("entry_window_expired")
            return EntryObservation(
                True,
                self.entry_bars_seen,
                "entry_window_expired",
                trace=tuple(trace),
            )
        return EntryObservation(
            True,
            self.entry_bars_seen,
            "waiting",
            trace=tuple(trace),
        )


@dataclass(frozen=True)
class HoldObservation:
    counted: bool
    ordinal: int
    outcome: str
    close_attempted: bool = False
    close_succeeded: bool = False
    trace: tuple[str, ...] = ()


@dataclass
class CompletedM5HoldReference:
    entry_time: int
    limit: int = 12
    last_counted_bar: int = 0
    bars_seen: int = 0
    position_open: bool = True

    def observe(self, bar_close_time: int, *, owned: bool) -> HoldObservation:
        if not self.position_open:
            return HoldObservation(False, self.bars_seen, "position_closed")
        if bar_close_time <= self.entry_time:
            return HoldObservation(False, self.bars_seen, "entry_or_earlier")
        if bar_close_time == self.last_counted_bar:
            return HoldObservation(False, self.bars_seen, "duplicate")
        if self.last_counted_bar and bar_close_time < self.last_counted_bar:
            raise ValueError("completed holding bars must be observed causally")

        self.last_counted_bar = bar_close_time
        self.bars_seen += 1
        trace = ["hold_decision", "ownership"]
        if not owned:
            trace.append("close:ownership_exit")
            self.position_open = False
            return HoldObservation(
                True,
                self.bars_seen,
                "ownership_exit",
                True,
                True,
                tuple(trace),
            )
        if self.bars_seen == self.limit:
            trace.append("close:structural_time_exit")
            self.position_open = False
            return HoldObservation(
                True,
                self.bars_seen,
                "structural_time_exit",
                True,
                True,
                tuple(trace),
            )
        return HoldObservation(True, self.bars_seen, "holding", trace=tuple(trace))


def _source() -> str:
    return EA_PATH.read_text(encoding="utf-8")


def _function(name: str) -> str:
    source = _source()
    match = re.search(
        rf"(?m)^(?:bool|void|string|int|double|datetime)\s+{re.escape(name)}\s*\(",
        source,
    )
    if match is None:
        raise AssertionError(f"missing EA function: {name}")
    brace = source.index("{", match.start())
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start() : index + 1]
    raise AssertionError(f"unterminated EA function: {name}")


def _assert_tokens(text: str, tokens: tuple[str, ...], context: str) -> None:
    missing = [token for token in tokens if token not in text]
    assert not missing, f"{context} missing tokens: {missing}"


def test_reference_registration_is_no_backfill_scalar_and_repeats_after_consumption() -> None:
    model = RepeatingImpulseReference()
    assert model.scan_completed_m15(10_000, qualifies=True) == "initialized_no_backfill"
    assert model.registrations == []
    assert model.scan_completed_m15(10_900, qualifies=True) == "registered"
    first_event = model.active_event_id
    assert first_event == "R2ICR_11800"
    assert model.scan_completed_m15(11_800, qualifies=True) == "active_event_not_overwritten"
    assert model.active_event_id == first_event
    assert model.registrations == [first_event]

    consumed = model.observe_completed_m5(
        12_100, owned=True, touch=True, quality_ok=False, guards_ok=False
    )
    assert consumed.outcome == "first_break_attempt"
    assert model.active_event_id == ""
    assert model.scan_completed_m15(12_700, qualifies=True) == "registered"
    assert model.registrations == [first_event, "R2ICR_13600"]


def test_reference_entry_counter_uses_distinct_completed_bars_and_final_bar_is_inclusive() -> None:
    model = RepeatingImpulseReference()
    model.scan_completed_m15(20_000, qualifies=False)
    model.scan_completed_m15(20_900, qualifies=True)
    anchor = model.impulse_time

    assert model.observe_completed_m5(
        anchor, owned=True, touch=False
    ).outcome == "anchor_or_earlier"
    first = model.observe_completed_m5(anchor + 300, owned=True, touch=False)
    assert (first.counted, first.ordinal, first.outcome) == (True, 1, "waiting")
    assert model.observe_completed_m5(
        anchor + 300, owned=True, touch=False
    ).outcome == "duplicate"
    # A weekend-sized elapsed gap is one observed completed decision bar.
    second = model.observe_completed_m5(anchor + 300_000, owned=True, touch=False)
    assert (second.ordinal, second.outcome) == (2, "waiting")
    final = model.observe_completed_m5(
        anchor + 600_000,
        owned=True,
        touch=True,
        quality_ok=True,
        guards_ok=True,
    )
    assert (final.ordinal, final.outcome, final.order_allowed) == (
        3,
        "first_break_attempt",
        True,
    )
    assert "consume:entry_window_expired" not in final.trace

    expiry = RepeatingImpulseReference()
    expiry.scan_completed_m15(40_000, qualifies=False)
    expiry.scan_completed_m15(40_900, qualifies=True)
    for ordinal in range(1, 3):
        assert expiry.observe_completed_m5(
            expiry.impulse_time + ordinal * 300, owned=True, touch=False
        ).outcome == "waiting"
    third = expiry.observe_completed_m5(
        expiry.impulse_time + 900, owned=True, touch=False
    )
    assert (third.ordinal, third.outcome) == (3, "entry_window_expired")


def test_reference_first_touch_is_consumed_before_quality_and_guards_with_no_retry() -> None:
    model = RepeatingImpulseReference()
    model.scan_completed_m15(50_000, qualifies=False)
    model.scan_completed_m15(50_900, qualifies=True)
    model.observe_completed_m5(model.impulse_time + 300, owned=True, touch=False)
    attempted = model.observe_completed_m5(
        model.impulse_time + 600,
        owned=True,
        touch=True,
        quality_ok=True,
        guards_ok=False,
    )
    assert attempted.trace.index("consume:first_break_attempt") < attempted.trace.index(
        "quality"
    ) < attempted.trace.index("guards")
    assert attempted.candidate is True
    assert attempted.order_allowed is False
    assert model.observe_completed_m5(
        model.impulse_time + 900,
        owned=True,
        touch=True,
        quality_ok=True,
        guards_ok=True,
    ).outcome == "inactive"
    assert len(model.consumptions) == 1

    lost = RepeatingImpulseReference()
    lost.scan_completed_m15(70_000, qualifies=False)
    lost.scan_completed_m15(70_900, qualifies=True)
    unowned = lost.observe_completed_m5(
        lost.impulse_time + 300,
        owned=False,
        touch=True,
        quality_ok=True,
        guards_ok=True,
    )
    assert unowned.outcome == "ownership_lost"
    assert "touch" not in unowned.trace


def test_reference_holding_counts_completed_bars_and_closes_on_loss_or_ordinal_12() -> None:
    horizon = CompletedM5HoldReference(entry_time=100_000)
    assert horizon.observe(100_000, owned=True).outcome == "entry_or_earlier"
    first = horizon.observe(100_300, owned=True)
    assert (first.ordinal, first.outcome) == (1, "holding")
    assert horizon.observe(100_300, owned=True).outcome == "duplicate"
    # Elapsed time is intentionally irrelevant to the ordinal.
    second = horizon.observe(900_000, owned=True)
    assert (second.ordinal, second.outcome) == (2, "holding")
    for ordinal in range(3, 12):
        assert horizon.observe(900_000 + ordinal * 300, owned=True).outcome == "holding"
    twelfth = horizon.observe(900_000 + 12 * 300, owned=True)
    assert (twelfth.ordinal, twelfth.outcome) == (12, "structural_time_exit")
    assert twelfth.close_attempted and twelfth.close_succeeded
    assert twelfth.trace[0] == "hold_decision"

    ownership = CompletedM5HoldReference(entry_time=200_000)
    exit_row = ownership.observe(500_000, owned=False)
    assert (exit_row.ordinal, exit_row.outcome) == (1, "ownership_exit")
    assert exit_row.trace == (
        "hold_decision",
        "ownership",
        "close:ownership_exit",
    )


def test_mode27_enum_is_append_only_and_mode28_reservation_is_preserved() -> None:
    source = _source()
    expected = (
        ("SIGNAL_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT", 22),
        ("SIGNAL_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG", 23),
        ("SIGNAL_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT", 24),
        ("SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK", 25),
        ("SIGNAL_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG", 26),
        ("SIGNAL_R2_M15_IMPULSE_M5_CONTINUATION_SHORT", 27),
        ("SIGNAL_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM", 28),
    )
    positions: list[int] = []
    for name, value in expected:
        match = re.search(rf"\b{re.escape(name)}\s*=\s*{value}\b", source)
        assert match is not None, (name, value)
        positions.append(match.start())
    assert positions == sorted(positions)


def test_mode27_source_declares_frozen_inputs_and_identity_counter_state() -> None:
    source = _source()
    expected_inputs = {
        "InpR2IcrAtrPeriod": ("int", "14"),
        "InpR2IcrMaturityD1Bars": ("int", "3"),
        "InpR2IcrImpulseLookbackM15Bars": ("int", "8"),
        "InpR2IcrImpulseMinRangeM15Atr": ("double", "0.75"),
        "InpR2IcrImpulseMinBodyFraction": ("double", "0.50"),
        "InpR2IcrImpulseCloseLocationMax": ("double", "0.30"),
        "InpR2IcrEntryWindowM5Bars": ("int", "3"),
        "InpR2IcrFirstBreakTouchM5Atr": ("double", "0.05"),
        "InpR2IcrFirstBreakCloseM5Atr": ("double", "0.05"),
        "InpR2IcrResumeMinBodyFraction": ("double", "0.45"),
        "InpR2IcrResumeCloseLocationMax": ("double", "0.30"),
        "InpR2IcrStopBufferM15Atr": ("double", "0.10"),
        "InpR2IcrMaxStopM15Atr": ("double", "1.50"),
        "InpR2IcrMaxHoldM5Bars": ("int", "12"),
        "InpR2IcrExitOnOwnershipLoss": ("bool", "true"),
        "InpR2IcrConsumeFirstBreak": ("bool", "true"),
    }
    missing_inputs = [
        name
        for name, (kind, value) in expected_inputs.items()
        if re.search(
            rf"input\s+{kind}\s+{re.escape(name)}\s*=\s*{re.escape(value)}\s*;",
            source,
        )
        is None
    ]
    assert not missing_inputs, f"missing or changed frozen mode27 inputs: {missing_inputs}"

    globals_required = {
        "g_r2_icr_event_active": ("bool", "false"),
        "g_r2_icr_last_logged_d1_bar": ("datetime", "0"),
        "g_r2_icr_last_scanned_m15_bar": ("datetime", "0"),
        "g_r2_icr_impulse_time": ("datetime", "0"),
        "g_r2_icr_consumed_event_time": ("datetime", "0"),
        "g_r2_icr_last_counted_m5_bar": ("datetime", "0"),
        "g_r2_icr_entry_m5_bars_seen": ("int", "0"),
        "g_r2_icr_signal_attempt_time": ("datetime", "0"),
        "g_r2_icr_hold_m5_bars_seen": ("int", "0"),
        "g_r2_icr_last_hold_m5_bar": ("datetime", "0"),
        "g_r2_icr_entry_time": ("datetime", "0"),
        "g_r2_icr_position_ticket": ("ulong", "0"),
        "g_r2_icr_position_id": ("long", "0"),
    }
    missing_globals = [
        name
        for name, (kind, value) in globals_required.items()
        if re.search(
            rf"(?m)^\s*{kind}\s+{re.escape(name)}\s*=\s*{re.escape(value)}\s*;",
            source,
        )
        is None
    ]
    assert not missing_globals, f"mode27 global state missing: {missing_globals}"


def test_mode27_ownership_is_mature_completed_d1_h4_down_and_nonshock() -> None:
    ownership = _function("R2IcrMatureDowntrendOwnershipAllows")
    _assert_tokens(
        ownership,
        (
            "InpR2IcrMaturityD1Bars != 3",
            "InpRegimeRequireH4Confirm",
            "RegimeShockState()",
            "CurrentXauRegime() != XAU_REGIME_DOWNTREND",
            "for(int shift = 1; shift <= InpR2IcrMaturityD1Bars; shift++)",
            "RegimeTrendStackAtShift(PERIOD_D1, shift, false)",
            "RegimeTrendStackAtShift(PERIOD_H4, 1, false)",
        ),
        "R2 mature-DOWN ownership",
    )
    assert "PERIOD_D1, 0" not in ownership
    assert "PERIOD_H4, 0" not in ownership


def test_mode27_m15_registration_is_no_backfill_scalar_and_repeatable() -> None:
    refresh = _function("RefreshR2IcrImpulseState")
    duplicate = refresh.index(
        "latest_m15_bar == g_r2_icr_last_scanned_m15_bar"
    )
    init = refresh.index("if(g_r2_icr_last_scanned_m15_bar == 0)")
    init_assignment = refresh.index(
        "g_r2_icr_last_scanned_m15_bar = latest_m15_bar;", init
    )
    init_return = refresh.index("return;", init)
    live_assignment = refresh.index(
        "g_r2_icr_last_scanned_m15_bar = latest_m15_bar;", init_return
    )
    register = refresh.index("RegisterR2IcrImpulseAtM15Shift(1)")
    active_guard = refresh.index("if(g_r2_icr_event_active)")
    assert duplicate < init < init_assignment < init_return
    assert init_return < live_assignment < active_guard < register
    assert refresh.count("RegisterR2IcrImpulseAtM15Shift(1)") == 1
    _assert_tokens(
        refresh,
        (
            "iTime(InpTargetSymbol, PERIOD_M15, 1)",
            "g_r2_icr_last_scanned_m15_bar = latest_m15_bar;",
        ),
        "mode27 M15 refresh",
    )

    qualifies = _function("R2IcrImpulseQualifiesAtM15Shift")
    _assert_tokens(
        qualifies,
        (
            "TimeframeLow(PERIOD_M15, shift + 1, lookback)",
            "close < open",
            "close < prior_low",
            "range >= MathMax(0.0, InpR2IcrImpulseMinRangeM15Atr) * m15_atr",
            "body_fraction >= MathMax(0.0, InpR2IcrImpulseMinBodyFraction)",
            "close_location <= InpR2IcrImpulseCloseLocationMax",
        ),
        "mode27 completed-M15 impulse",
    )
    assert "PERIOD_M15, 0" not in qualifies

    register_body = _function("RegisterR2IcrImpulseAtM15Shift")
    assert register_body.index("R2IcrMatureDowntrendOwnershipAllows()") < register_body.index(
        "R2IcrImpulseQualifiesAtM15Shift(shift"
    )
    _assert_tokens(
        register_body,
        (
            "g_r2_icr_event_active = true;",
            "g_r2_icr_entry_m5_bars_seen = 0;",
            "g_r2_icr_last_counted_m5_bar = 0;",
            "R2_ICR_IMPULSE_REGISTERED",
        ),
        "mode27 impulse registration",
    )
    signal = _function("TryR2M15ImpulseM5ContinuationShortSignal")
    assert signal.index("RefreshR2IcrD1OwnershipTelemetry()") < signal.index(
        "RefreshR2IcrImpulseState()"
    )


def test_mode27_entry_window_is_distinct_m5_counter_with_inclusive_final_decision() -> None:
    helper = _function("R2IcrTakeDistinctCompletedM5Bar")
    duplicate = helper.index("m5_bar_time == g_r2_icr_last_counted_m5_bar")
    anchor = helper.index("m5_close_time <= g_r2_icr_impulse_time")
    assignment = helper.index("g_r2_icr_last_counted_m5_bar = m5_bar_time")
    assert duplicate < anchor < assignment

    signal = _function("TryR2M15ImpulseM5ContinuationShortSignal")
    helper_call = signal.index("R2IcrTakeDistinctCompletedM5Bar(")
    increment = signal.index("g_r2_icr_entry_m5_bars_seen++")
    final_bar = signal.index("const bool final_entry_bar", increment)
    ownership = signal.index("const bool owned", final_bar)
    touch = signal.index("const bool first_touch", ownership)
    decision_log = signal.index("LogR2IcrEntryDecision(", touch)
    ownership_branch = signal.index("if(!owned)", decision_log)
    no_touch_branch = signal.index("if(!first_touch)", ownership_branch)
    expiry = signal.index('"entry_window_expired"', no_touch_branch)
    assert (
        helper_call
        < increment
        < final_bar
        < ownership
        < touch
        < decision_log
        < ownership_branch
        < no_touch_branch
        < expiry
    )
    assert "InpR2IcrEntryWindowM5Bars" in signal[final_bar:expiry]
    assert re.search(r"const bool first_touch\s*=\s*owned\s*&&", signal)
    for forbidden in (
        "TimeCurrent() - g_r2_icr",
        "InpR2IcrEntryWindowM5Bars * PeriodSeconds",
        "g_r2_icr_impulse_time + InpR2IcrEntryWindowM5Bars",
    ):
        assert forbidden not in signal


def test_mode27_first_touch_consumes_before_quality_or_execution_guards() -> None:
    signal = _function("TryR2M15ImpulseM5ContinuationShortSignal")
    touch = signal.index("const bool first_touch")
    reserve = signal.index("ReserveR2IcrFirstBreakConsumption()", touch)
    quality = signal.index("const bool accepted_resume", reserve)
    assert touch < reserve < quality
    assert signal.count("ReserveR2IcrFirstBreakConsumption()") == 1
    reserve_body = _function("ReserveR2IcrFirstBreakConsumption")
    _assert_tokens(
        reserve_body,
        (
            "g_r2_icr_event_active = false;",
            "first_break_attempt",
            "R2_ICR_EVENT_CONSUMED",
        ),
        "mode27 first-break reservation",
    )
    pre_reserve = signal[:reserve]
    for forbidden_guard in (
        "CountOwnOpenPositions(",
        "R2IcrHardRiskAllowed(",
        "ClaimSignalSlot(",
        "g_trade.Sell(",
    ):
        assert forbidden_guard not in pre_reserve

    m15_dispatch = _function("IsM15DecisionSignalMode")
    assert "SIGNAL_R2_M15_IMPULSE_M5_CONTINUATION_SHORT" not in m15_dispatch
    evaluator = _function("EvaluateCompletedM5Bar")
    mode_flag = evaluator.index("const bool r2_icr_mode")
    early_call = evaluator.index("TryR2M15ImpulseM5ContinuationShortSignal(", mode_flag)
    generic_prerequisite = evaluator.index("if(iBars(InpTargetSymbol, PERIOD_M5)")
    assert mode_flag < early_call < generic_prerequisite
    assert evaluator.count("TryR2M15ImpulseM5ContinuationShortSignal(") == 1


def test_mode27_sell_ordercalcprofit_risk_is_fail_closed_and_precedes_claim() -> None:
    hard_risk = _function("R2IcrHardRiskAllowed")
    _assert_tokens(
        hard_risk,
        (
            "actual_risk_usd = -1.0",
            "const double hard_limit_usd = 50.00",
            'direction != "SHORT"',
            "NormalizeLotsForSymbol(lots)",
            "MathAbs(normalized_lots - lots) > 0.0000001",
            'AccountInfoString(ACCOUNT_CURRENCY) != "USD"',
            "MathAbs(InpRiskAmountUsd - hard_limit_usd) > 0.0000001",
            "MathAbs(InpMaxRiskOvershootPct) > 0.0000001",
            "OrderCalcProfit(ORDER_TYPE_SELL",
            "projected_pnl >= 0.0",
            "actual_risk_usd = -projected_pnl",
            "actual_risk_usd <= hard_limit_usd + 0.0000001",
        ),
        "mode27 hard SELL risk",
    )

    evaluator = _function("EvaluateCompletedM5Bar")
    risk_call = evaluator.index("R2IcrHardRiskAllowed(")
    claim = evaluator.index("ClaimSignalSlot(", risk_call)
    assert risk_call < claim
    _assert_tokens(
        evaluator,
        (
            'risk_block_reason = "r2_icr_normalized_entry_to_stop_risk_overshoot"',
            "g_r2_icr_signal_attempt_time",
            "ArmR2IcrPositionTracking(",
            'LogOrder("ORDER_SEND_OK"',
            '"OrderCalcProfit"',
        ),
        "mode27 execution integration",
    )
    success = evaluator.index("ArmR2IcrPositionTracking(", risk_call)
    success_log = evaluator.index('LogOrder("ORDER_SEND_OK"', success)
    assert claim < success < success_log
    sent_branch = evaluator.rfind("if(sent)", claim, success)
    assert claim < sent_branch < success

    source = _source()
    _assert_tokens(
        source,
        (
            '"actual_risk_usd", "intended_risk_usd", "risk_calc_method"',
            "actual_risk_usd >= 0.0 ? DoubleToString(actual_risk_usd, 6) : \"\"",
        ),
        "order-risk CSV schema",
    )


def test_mode27_hold_and_ownership_exits_use_completed_m5_and_success_telemetry() -> None:
    arm = _function("ArmR2IcrPositionTracking")
    _assert_tokens(
        arm,
        (
            "g_r2_icr_hold_m5_bars_seen = 0;",
            "g_r2_icr_last_hold_m5_bar = 0;",
            "g_r2_icr_entry_time",
            "g_r2_icr_position_ticket",
            "g_r2_icr_position_id",
        ),
        "mode27 position tracking arm",
    )

    hold = _function("ProcessR2IcrHoldDecisionOnCompletedM5Bar")
    duplicate = hold.index("m5_bar_time == g_r2_icr_last_hold_m5_bar")
    anchor = hold.index("m5_close_time <= g_r2_icr_entry_time")
    assign = hold.index("g_r2_icr_last_hold_m5_bar = m5_bar_time")
    increment = hold.index("g_r2_icr_hold_m5_bars_seen++", assign)
    decision = hold.index("LogR2IcrHoldDecision(", increment)
    ownership = hold.index("if(!owned)", decision)
    ownership_exit = hold.index('"r2_icr_ownership_exit"', ownership)
    horizon = hold.index("InpR2IcrMaxHoldM5Bars", ownership_exit)
    horizon_exit = hold.index('"r2_icr_structural_time_exit"', horizon)
    assert duplicate < anchor < assign < increment < decision < ownership < ownership_exit
    assert ownership_exit < horizon < horizon_exit
    for forbidden in (
        "TimeCurrent() - g_r2_icr_entry_time",
        "InpR2IcrMaxHoldM5Bars * PeriodSeconds",
        "g_r2_icr_entry_time +",
    ):
        assert forbidden not in hold

    close = _function("CloseR2IcrTrackedPosition")
    send = close.index("SendManagedClose(")
    failed_stage = close.index("R2_ICR_POSITION_EXIT_FAILED", send)
    success_stage = close.index("R2_ICR_POSITION_EXIT", failed_stage + 1)
    assert send < failed_stage < success_stage
    _assert_tokens(
        close,
        (
            "close_attempted=1",
            "close_succeeded=1",
            "position_id=",
            "ticket=",
            "entry_time=",
            "decision_bar_time=",
            "hold_bar_ordinal=",
        ),
        "mode27 successful close telemetry",
    )
    _assert_tokens(
        hold,
        (
            "PositionSelectByTicket(g_r2_icr_position_ticket)",
            "ResetR2IcrPositionTracking()",
        ),
        "mode27 closed-position tracking cleanup",
    )

    evaluator = _function("EvaluateCompletedM5Bar")
    hold_call = evaluator.index("ProcessR2IcrHoldDecisionOnCompletedM5Bar()")
    signal_call = evaluator.index("TryR2M15ImpulseM5ContinuationShortSignal(")
    assert hold_call < signal_call


def test_mode27_lifecycle_and_position_schemas_are_machine_joinable() -> None:
    source = _source()
    _assert_tokens(
        source,
        (
            "R2_ICR_D1_OWNERSHIP",
            "R2_ICR_IMPULSE_REGISTERED",
            "R2_ICR_ENTRY_DECISION",
            "R2_ICR_EVENT_CONSUMED",
            "R2_ICR_HOLD_DECISION",
            "R2_ICR_POSITION_EXIT",
            "R2_M15_IMPULSE_M5_CONTINUATION_SHORT_STATE_downtrend",
        ),
        "mode27 lifecycle stages",
    )

    ownership = _function("LogR2IcrD1Ownership")
    _assert_tokens(
        ownership,
        (
            "d1_time=",
            "d1_shift=1",
            "backfill=0",
            "d1_shift1_time=",
            "d1_shift2_time=",
            "d1_shift3_time=",
            "h4_time=",
            "mature=",
            "direction_state=",
            "h4_down=",
            "phase=",
            "shock=",
            "maturity=",
        ),
        "mode27 ownership telemetry",
    )
    lifecycle = _function("LogR2IcrLifecycle")
    _assert_tokens(
        lifecycle,
        (
            "event_id=",
            "setup_time=",
            "from=",
            "to=",
            "outcome=",
            "setup=DOWN|phase=ESTABLISHED|shock=0|maturity=3",
            "impulse_bar_time=",
            "impulse_time=",
            "m15_shift=1|backfill=0",
            "entry_bars_seen=",
            "deinit=",
        ),
        "mode27 event lifecycle telemetry",
    )
    entry = _function("LogR2IcrEntryDecision")
    _assert_tokens(
        entry,
        (
            "decision_bar_time=",
            "entry_bar_ordinal=",
            "touch=",
            "owned=",
        ),
        "mode27 entry-decision telemetry",
    )
    hold = _function("LogR2IcrHoldDecision")
    _assert_tokens(
        hold,
        (
            "entry_time=",
            "position_id=",
            "ticket=",
            "position_open=1",
            "owned=",
            "decision_bar_time=",
            "hold_bar_ordinal=",
        ),
        "mode27 hold-decision telemetry",
    )

    deinit = _function("OnDeinit")
    _assert_tokens(
        deinit,
        (
            "SIGNAL_R2_M15_IMPULSE_M5_CONTINUATION_SHORT",
            'ConsumeR2IcrEvent("tester_deinit"',
        ),
        "mode27 truthful tester-end cleanup",
    )
