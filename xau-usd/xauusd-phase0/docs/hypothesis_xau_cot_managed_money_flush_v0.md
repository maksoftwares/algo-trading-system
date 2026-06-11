# Hypothesis: xau_cot_managed_money_flush_v0

candidate_id: xau_cot_managed_money_flush_v0
candidate_version: v0
Hypothesis date: 2026-06-10
Hypothesis version: v0
Author / owner: Claude (independent technical reviewer) / maksoftwares
Expected trade count per year: 30-90
Expected cost-adjusted PF: 1.15-1.55
Expected losing-month percentage: 35%-60%
Expected worst single month: -5R to -12R
Expected R-multiple distribution: Clustered -1R failures inside flush windows, fewer 2.0R recovery wins, no dependence on one outsized winner.
Expected max consecutive zero months: 3
expected_median_stop_points: 600
expected_cost_R_at_measured_50_75_spread: 0.08

## Mechanical Definition

All H1 windows use completed bars whose timestamp_utc equals the bar END converted to America/New_York local time with IANA timezone rules. Positioning state comes from the cot_gold frame (CFTC disaggregated gold futures): weekly net managed-money position equals managed_money_long_all minus managed_money_short_all; its z-score is computed against the trailing 156 available reports (minimum 52 required, otherwise no state). Report availability lag is fixed at 4 calendar days after report_date; only reports available at or before the start of the New_York trade date are used. A LONG bias exists while the latest available z-score is at or below -1.25 (managed-money washout); a SHORT bias exists while it is at or above +1.25 (crowded-long blowout); otherwise no setup. The trigger is the first H1 bar with New_York bar-end time 10:00, 11:00, or 12:00 that closes in the bias direction, closes beyond the previous H1 bar's high (LONG) or below its low (SHORT), and has body at least 35 percent of its high-low range. Entry is market at the next available simulator quote. Stop distance is the maximum of 1.5 times H1 ATR(14) at the trigger bar and 3.75 price units (375 points). Target is a fixed 2.0R. Stop or target exits only, one position at a time, at most one setup per New_York date. Implementation: `src/phase0/strategies/xau_cot_managed_money_flush_v0.py` (research registry only; not an approved EA).

## Expected Behavior

Low, bursty frequency concentrated in positioning-extreme regimes; multi-week one-sided exposure inside a flush; quiet years may press against per-cell trade-count floors, which the gates will judge. Gate selection follows locked `docs/PHASE0_WAVE2_GATE_SET_V1.md` (frequency-aware; this file is registered as a later wave referencing that gate set), on the locked full per-broker windows with Pepperstone owner-accepted partial and true holdout untouched.

## Why This Hypothesis Should Exist

CFTC positioning is real institutional exposure, not a price-derived indicator. Extreme managed-money washouts mark forced de-risking whose unwind plays out over days-to-weeks, and the funded NY-morning window is where that re-risking flow executes. The nearest rejected relatives are cot_gold_positioning_reversal_v0, h1_cot_positioning_continuation_v0, and h4_cot_gc_volume_capitulation_reversal_v0 (REJECTED_FIRST_PASS - different state definitions, entry scales, and stop economics, disclosed as adjacent negative evidence), plus xau_d1_trend_ny_window_continuation_v0 (FAIL_REJECTED_VERSION_FINAL 2026-06-10 - the unconditioned ancestor of the entry leg; this NEW design replaces the trend gate with an independent positioning-extreme gate).

## What Would Falsify It

The locked PHASE0_WAVE2_GATE_SET_V1 selection: fewer than 7 of 9 PF cells at 1.30, any cell under 40 trades, concentration breach (absolute caps at high frequency, normalized G4 at low frequency), drawdown or activity breach, p95-to-best PF ratio under 0.50, G7 cross-venue floor under 1.20, G8 modern-era failure, G9B realized cost breach, or adversarial review finding a logic mismatch. A failure is final for v0 under NO_TUNING_RULES.md; no post-result rescue of any kind.

status: LOCKED
