# Hypothesis: eur_dual_session_d1_trend_continuation_v0

candidate_id: eur_dual_session_d1_trend_continuation_v0
candidate_version: v0
Hypothesis date: 2026-06-11
Hypothesis version: v0
Author / owner: Claude (independent technical reviewer) / maksoftwares
Expected trade count per year: 120-220
Expected cost-adjusted PF: 1.15-1.45
Expected losing-month percentage: 35%-55%
Expected worst single month: -8R to -16R
Expected R-multiple distribution: Many -1R initiative failures in chop, steady 2.0R trend-day wins, no dependence on one outsized winner.
Expected max consecutive zero months: 2
expected_median_stop_points: 375
expected_cost_R_at_measured_50_75_spread: 0.04

## Mechanical Definition

Symbol is EURUSD. All H1 windows use completed bars whose timestamp_utc equals the bar END converted to local time with IANA timezone rules. Daily trend state comes from completed EURUSD D1 bars only (last bar ending at or before the start of the trade date in New_York time): LONG-state when D1 EMA20 is above D1 EMA50, SHORT-state when below, nothing when equal. The trigger is the first H1 bar in either funded window - Europe/London bar-end 09:00, 10:00, or 11:00 (London morning), or America/New_York bar-end 09:00, 10:00, or 11:00 (US data/open window) - that closes in the trend direction, closes beyond the previous H1 bar's high (LONG) or below its low (SHORT), and has body at least 35 percent of its high-low range. Entry is market at the next available simulator quote. Stop distance is the maximum of 1.5 times H1 ATR(14) at the trigger bar and 375 points times the symbol point size (0.00375 price units for EURUSD). Target is a fixed 2.0R. Stop or target exits only, one position at a time, at most one setup per New_York calendar date. Implementation: `src/phase0/strategies/eur_dual_session_d1_trend_continuation_v0.py` (research registry only; not an approved EA).

## Expected Behavior

Near-daily decision cadence during trending regimes across both funded sessions; losing clusters in trend-transition months; per-cell samples on the 2016-2025 windows should exceed the trade-count floor comfortably. Matrix design and gates follow locked `docs/PHASE0_WAVE2_GATE_SET_V1.md` with the locked `docs/PHASE0_WAVE4_FX_GATE_ADDENDUM_V1.md` six-cell EURUSD adaptation (DATA_VENUE_ASYMMETRY_PRESENT disclosed; true holdout untouched).

## Why This Hypothesis Should Exist

EURUSD is a structurally different behavior space from the eleven finally-rejected XAUUSD candidates: different participants, different funded windows (London is its home session), and roughly one-third of gold's cost per unit of ATR-scaled risk (configured 12-point median spread against a 375-point stop floor gives cost_R near 0.03, versus about 0.10 for gold at measured spreads). The owner's demo ledger independently showed small EURUSD positives concentrated in exactly these two windows. The XAUUSD analogue of the entry leg (xau_d1_trend_ny_window_continuation_v0) is FAIL_REJECTED_VERSION_FINAL - disclosed as adjacent negative evidence; the claim under test is that the same funded-flow logic on a cheaper, London-anchored instrument with both home windows clears what gold could not.

## What Would Falsify It

The locked Wave-2 gate set with the locked Wave-4 FX addendum: fewer than 5 of 6 PF cells at 1.30, any cell under 40 trades, concentration breach (absolute caps at high frequency, normalized G4 at low frequency), drawdown or activity breach, p95-to-best PF ratio under 0.50, dukascopy PF under 1.20 in any cost model, modern-era PF under 1.10 in either broker, G9B realized cost breach, or adversarial review finding a logic mismatch. A failure is final for v0 under NO_TUNING_RULES.md; no post-result rescue of any kind.

status: LOCKED
