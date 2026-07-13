from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EA_PATH = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
EA_TEXT = EA_PATH.read_text(encoding="utf-8")


@dataclass(frozen=True)
class CounterDecision:
    counted: bool
    ordinal: int
    outcome: str


@dataclass
class CompletedBarWindow:
    """Causal reference model: only distinct completed-bar identities consume lifetime."""

    limit: int
    anchor_bar: int
    bars_seen: int = 0
    last_counted_bar: int = 0
    active: bool = True

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError("limit must be positive")
        self.last_counted_bar = self.anchor_bar

    def observe(self, completed_bar: int, terminal_outcome: str | None = None) -> CounterDecision:
        if not self.active:
            return CounterDecision(False, self.bars_seen, "inactive")
        if completed_bar == self.last_counted_bar:
            return CounterDecision(False, self.bars_seen, "duplicate_or_anchor")
        if completed_bar < self.last_counted_bar:
            raise ValueError("completed bars must be observed causally")

        self.last_counted_bar = completed_bar
        self.bars_seen += 1
        if terminal_outcome is not None:
            self.active = False
            return CounterDecision(True, self.bars_seen, terminal_outcome)
        if self.bars_seen == self.limit:
            self.active = False
            return CounterDecision(True, self.bars_seen, "expired")
        return CounterDecision(True, self.bars_seen, "waiting")

    def rearm(self, anchor_bar: int) -> None:
        self.anchor_bar = anchor_bar
        self.bars_seen = 0
        self.last_counted_bar = anchor_bar
        self.active = True


@dataclass(frozen=True)
class SourceWindowContract:
    name: str
    limit: int
    counter: str
    cursor: str
    helper: str
    anchor: str
    reset_start: str
    reset_end: str
    arm_start: str
    arm_end: str
    signal_start: str
    signal_end: str
    window_input: str
    expiry_state: str
    final_marker: str
    terminal_marker: str
    expiry_outcome: str
    mode24_second_window: bool = False


CONTRACTS = (
    SourceWindowContract(
        name="mode22_r2_pdl_retest",
        limit=8,
        counter="g_r2_pdl_retest_m15_bars_observed",
        cursor="g_r2_pdl_last_counted_m15_bar",
        helper="R2PdlTakeDistinctCompletedM15Bar",
        anchor="g_r2_pdl_break_time",
        reset_start="void ResetR2PriorD1LowBreakState()",
        reset_end="bool PriorCompletedD1LowAtTime",
        arm_start="bool ArmR2PriorD1LowBreakAtH1Shift",
        arm_end="void RefreshR2PriorD1LowBreakState()",
        signal_start="bool TryR2PriorD1LowFirstRetestShortSignal",
        signal_end="void ResetR1PriorD1HighBreakState()",
        window_input="InpR2PdlRetestWindowM15Bars",
        expiry_state="g_r2_pdl_break_expiry",
        final_marker="final_retest_bar",
        terminal_marker="const bool rejected_level",
        expiry_outcome='"r2_pdl_expired"',
    ),
    SourceWindowContract(
        name="mode23_r1_pdh_retest",
        limit=8,
        counter="g_r1_pdh_retest_m15_bars_observed",
        cursor="g_r1_pdh_last_counted_m15_bar",
        helper="R1PdhTakeDistinctCompletedM15Bar",
        anchor="g_r1_pdh_break_time",
        reset_start="void ResetR1PriorD1HighBreakState()",
        reset_end="bool PriorCompletedD1HighAtTime",
        arm_start="bool ArmR1PriorD1HighBreakAtH1Shift",
        arm_end="void RefreshR1PriorD1HighBreakState()",
        signal_start="bool TryR1PriorD1HighFirstRetestLongSignal",
        signal_end="bool R2LhfMatureDowntrendOwnershipAllows()",
        window_input="InpR1PdhRetestWindowM15Bars",
        expiry_state="g_r1_pdh_break_expiry",
        final_marker="final_retest_bar",
        terminal_marker="const bool touched_level",
        expiry_outcome='"r1_pdh_expired"',
    ),
    SourceWindowContract(
        name="mode24_r2_lhf_reset",
        limit=16,
        counter="g_r2_lhf_reset_m15_bars_observed",
        cursor="g_r2_lhf_last_counted_m15_bar",
        helper="R2LhfTakeDistinctCompletedM15Bar",
        anchor="g_r2_lhf_setup_time",
        reset_start="void ConsumeR2LhfSetup",
        reset_end="bool ArmR2LhfLegOneAtH1Shift",
        arm_start="bool ArmR2LhfLegOneAtH1Shift",
        arm_end="void RefreshR2LhfLegOneState()",
        signal_start="bool TryR2SecondContinuationLowerHighShortSignal",
        signal_end="bool R1HlfMatureD1AtShift",
        window_input="InpR2LhfResetWindowM15Bars",
        expiry_state="g_r2_lhf_reset_expiry",
        final_marker="final_reset_bar",
        terminal_marker="double pivot_high = 0.0;",
        expiry_outcome='"r2_lhf_reset_expired"',
    ),
    SourceWindowContract(
        name="mode24_r2_lhf_second_break",
        limit=16,
        counter="g_r2_lhf_second_break_m15_bars_observed",
        cursor="g_r2_lhf_last_counted_m15_bar",
        helper="R2LhfTakeDistinctCompletedM15Bar",
        anchor="g_r2_lhf_setup_time",
        reset_start="void ConsumeR2LhfSetup",
        reset_end="bool ArmR2LhfLegOneAtH1Shift",
        arm_start="bool ArmR2LhfLegOneAtH1Shift",
        arm_end="void RefreshR2LhfLegOneState()",
        signal_start="bool TryR2SecondContinuationLowerHighShortSignal",
        signal_end="bool R1HlfMatureD1AtShift",
        window_input="InpR2LhfSecondBreakWindowM15Bars",
        expiry_state="g_r2_lhf_second_break_expiry",
        final_marker="final_second_break_bar",
        terminal_marker="const bool touched_second_break",
        expiry_outcome='"r2_lhf_second_break_expired"',
        mode24_second_window=True,
    ),
)


def _block(start: str, end: str) -> str:
    start_index = EA_TEXT.index(start)
    return EA_TEXT[start_index : EA_TEXT.index(end, start_index)]


def _zeroed(block: str, token: str) -> bool:
    return re.search(rf"\b{re.escape(token)}\s*=\s*0\s*;", block) is not None


def _increment_index(block: str, token: str) -> int:
    patterns = (
        rf"\b{re.escape(token)}\s*\+\+\s*;",
        rf"\+\+\s*{re.escape(token)}\s*;",
        rf"\b{re.escape(token)}\s*\+=\s*1\s*;",
    )
    positions = [match.start() for pattern in patterns if (match := re.search(pattern, block))]
    if not positions:
        raise AssertionError(f"{token} is never incremented exactly once")
    return min(positions)


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_reference_counter_ignores_repeated_ticks_and_elapsed_gaps(
    contract: SourceWindowContract,
) -> None:
    window = CompletedBarWindow(contract.limit, anchor_bar=1_000)
    assert window.observe(1_000) == CounterDecision(False, 0, "duplicate_or_anchor")
    assert window.observe(1_900) == CounterDecision(True, 1, "waiting")
    assert window.observe(1_900) == CounterDecision(False, 1, "duplicate_or_anchor")
    # A multi-day wall-clock jump represents one newly completed decision bar here.
    assert window.observe(900_000) == CounterDecision(True, 2, "waiting")
    assert window.bars_seen == 2


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_reference_counter_evaluates_final_bar_before_expiry(
    contract: SourceWindowContract,
) -> None:
    accepted = CompletedBarWindow(contract.limit, anchor_bar=10_000)
    for ordinal in range(1, contract.limit):
        assert accepted.observe(10_000 + ordinal * 900).outcome == "waiting"
    final = accepted.observe(10_000 + contract.limit * 900, "terminal_event")
    assert final == CounterDecision(True, contract.limit, "terminal_event")

    expired = CompletedBarWindow(contract.limit, anchor_bar=20_000)
    for ordinal in range(1, contract.limit):
        assert expired.observe(20_000 + ordinal * 900).outcome == "waiting"
    assert expired.observe(20_000 + contract.limit * 900) == CounterDecision(
        True, contract.limit, "expired"
    )
    assert expired.observe(20_000 + (contract.limit + 1) * 900) == CounterDecision(
        False, contract.limit, "inactive"
    )


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_reference_counter_reset_and_rearm_clear_all_lifetime_state(
    contract: SourceWindowContract,
) -> None:
    window = CompletedBarWindow(contract.limit, anchor_bar=30_000)
    for ordinal in range(1, 4):
        window.observe(30_000 + ordinal * 900)
    assert window.bars_seen == 3
    window.rearm(anchor_bar=700_000)
    assert window.bars_seen == 0
    assert window.last_counted_bar == 700_000
    assert window.observe(700_000).counted is False
    assert window.observe(900_000) == CounterDecision(True, 1, "waiting")


def test_reference_mode24_second_window_starts_after_pivot_confirmation_bar() -> None:
    reset = CompletedBarWindow(16, anchor_bar=100_000)
    for ordinal in range(1, 5):
        reset.observe(100_000 + ordinal * 900)
    pivot_bar = 100_000 + 5 * 900
    assert reset.observe(pivot_bar, "pivot_confirmed").ordinal == 5

    second_break = CompletedBarWindow(16, anchor_bar=pivot_bar)
    assert second_break.observe(pivot_bar).counted is False
    for ordinal in range(1, 16):
        assert second_break.observe(pivot_bar + ordinal * 900).outcome == "waiting"
    assert second_break.observe(
        pivot_bar + 16 * 900, "second_break_attempt"
    ) == CounterDecision(True, 16, "second_break_attempt")


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_ea_declares_completed_m15_counter_and_distinct_bar_cursor(
    contract: SourceWindowContract,
) -> None:
    assert re.search(rf"\bint\s+{re.escape(contract.counter)}\s*=\s*0\s*;", EA_TEXT)
    assert re.search(rf"\bdatetime\s+{re.escape(contract.cursor)}\s*=\s*0\s*;", EA_TEXT)


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_ea_uses_one_distinct_completed_m15_bar_helper(
    contract: SourceWindowContract,
) -> None:
    helper_signature = f"bool {contract.helper}(datetime &m15_bar_time, datetime &m15_close_time)"
    assert helper_signature in EA_TEXT
    helper = _block(helper_signature, contract.signal_start)
    duplicate_guard = f"m15_bar_time == {contract.cursor}"
    anchor_guard = f"m15_close_time <= {contract.anchor}"
    cursor_assignment = f"{contract.cursor} = m15_bar_time;"
    assert duplicate_guard in helper
    assert anchor_guard in helper
    assert cursor_assignment in helper
    assert helper.index(duplicate_guard) < helper.index(anchor_guard) < helper.index(cursor_assignment)
    assert f"if(!{contract.helper}(m15_bar_time, m15_close_time))" in _block(
        contract.signal_start, contract.signal_end
    )


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_ea_counter_state_is_cleared_on_consume_and_rearm(
    contract: SourceWindowContract,
) -> None:
    reset = _block(contract.reset_start, contract.reset_end)
    arm = _block(contract.arm_start, contract.arm_end)
    assert _zeroed(reset, contract.counter)
    assert _zeroed(reset, contract.cursor)
    assert _zeroed(arm, contract.counter)
    assert _zeroed(arm, contract.cursor)
    if contract.mode24_second_window:
        signal = _block(contract.signal_start, contract.signal_end)
        pivot_start = signal.index("g_r2_lhf_pivot_confirmation_time = m15_close_time;")
        state_change = signal.index(
            "g_r2_lhf_state = R2_LHF_STATE_LOWER_HIGH_CONFIRMED;", pivot_start
        )
        transition = signal[pivot_start:state_change]
        assert _zeroed(transition, contract.counter)
        assert not _zeroed(transition, contract.cursor)


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_ea_has_no_wall_clock_lifetime_eligibility(
    contract: SourceWindowContract,
) -> None:
    signal = _block(contract.signal_start, contract.signal_end)
    assert contract.expiry_state not in signal


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_ea_evaluates_terminal_event_on_final_bar_then_expires_same_bar(
    contract: SourceWindowContract,
) -> None:
    signal = _block(contract.signal_start, contract.signal_end)
    helper_call_text = f"if(!{contract.helper}(m15_bar_time, m15_close_time))"
    assert helper_call_text in signal
    helper_call = signal.index(helper_call_text)
    increment = _increment_index(signal, contract.counter)
    final_marker = signal.index(contract.final_marker, increment)
    terminal_marker = signal.index(contract.terminal_marker, final_marker)
    expiry_outcome = signal.rindex(contract.expiry_outcome)
    assert helper_call < increment < final_marker < terminal_marker < expiry_outcome
    assert contract.window_input in signal[final_marker:terminal_marker]
    assert signal.rfind(
        f"if({contract.final_marker})", terminal_marker, expiry_outcome
    ) > terminal_marker
