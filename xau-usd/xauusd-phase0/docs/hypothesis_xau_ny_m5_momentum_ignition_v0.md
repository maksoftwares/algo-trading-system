# Hypothesis: xau_ny_m5_momentum_ignition_v0

candidate_id: xau_ny_m5_momentum_ignition_v0
candidate_version: v0
Hypothesis date: 2026-06-11
Hypothesis version: v0
Author / owner: Claude (independent technical reviewer) / maksoftwares
Expected trade count per year: 60-150
Expected cost-adjusted PF: 1.15-1.50
Expected losing-month percentage: 35%-55%
Expected worst single month: -6R to -14R
Expected R-multiple distribution: Many -1R failed ignitions, steady 1.5R continuation wins inside the funded window, no dependence on one outsized winner.
Expected max consecutive zero months: 2
expected_median_stop_points: 450
expected_cost_R_at_measured_50_75_spread: 0.11

## Mechanical Definition

Symbol is XAUUSD with M5 decision bars (timestamp_utc equals bar END, converted to America/New_York local time with IANA timezone rules). The trigger window is M5 bars whose New_York bar-end time is between 09:35 and 12:00 inclusive. The trigger is three consecutive completed M5 bars closing in the same direction where each bar's high-low range is at least 1.2 times M5 ATR(20) at that bar and the absolute net move from the first bar's open to the third bar's close is at least 2.0 times M5 ATR(20) at the third bar; the third bar must end inside the trigger window. Entry is market at the next available simulator quote in the ignition direction. Stop distance is the maximum of 8 times M5 ATR(20) at the third bar and 3.75 price units (375 points); placed adverse to the entry direction. Target is a fixed 1.5R. Stop or target exits only, one position at a time, at most one setup per America/New_York calendar date. Implementation: `src/phase0/strategies/xau_ny_m5_momentum_ignition_v0.py` (research registry only; not an approved EA).

## Expected Behavior

Bursty, data-day-clustered frequency; quick -1R failures when ignition marks exhaustion; wins resolve within the US session. Windows, matrix, and gates: locked full per-broker windows, locked `docs/PHASE0_WAVE2_GATE_SET_V1.md` frequency-aware selection, Pepperstone owner-accepted partial, true holdout untouched.

## Why This Hypothesis Should Exist

All thirteen 2026-06-10/11 final rejections used H1-or-higher decision bars; the only signal layer that has ever passed this project's gates is M5 microstructure inside the funded NY window (the breakout_retest family, 7/9 cells on 66k trades), and the historical M5 candidates were all judged with tight pre-measured-cost stops under the since-corrected era-rotated matrix and absolute concentration caps. This candidate tests the one structurally untested combination: an M5-scale participation-burst mechanic (no level, no retest - mechanically independent of breakout_retest, to be defended at Gate 9 and judged by D2 family clustering) with wide ATR-floored cost-safe stops on full decade windows. The session research independently measured that the NY morning carries the day's straightest, fastest-paid moves. m5_impulse_continuation_v0 is REJECTED_FIRST_PASS and is the nearest rejected relative (different impulse definition, tight stops, old calibration); its rejection counts as adjacent negative evidence.

## What Would Falsify It

The locked PHASE0_WAVE2_GATE_SET_V1 selection: fewer than 7 of 9 PF cells at 1.30, any cell under 40 trades, concentration breach (absolute caps at high frequency, normalized G4 at low frequency), drawdown or activity breach, p95-to-best PF ratio under 0.50, G7 cross-venue floor under 1.20, G8 modern-era failure, G9B realized cost breach, or adversarial review finding a logic mismatch. A failure is final for v0 under NO_TUNING_RULES.md; no post-result rescue of any kind. If this fails, the M5-independent-mechanic cell of the design space is closed on the current information set.

status: LOCKED
