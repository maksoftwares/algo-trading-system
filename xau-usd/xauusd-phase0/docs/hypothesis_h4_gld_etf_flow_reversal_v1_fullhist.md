# Hypothesis: h4_gld_etf_flow_reversal_v1_fullhist

candidate_id: h4_gld_etf_flow_reversal_v1_fullhist
candidate_version: v1_fullhist
Hypothesis date: 2026-06-11
Hypothesis version: v1_fullhist
Author / owner: Claude (independent technical reviewer) / maksoftwares
Expected trade count per year: 25-45
Expected cost-adjusted PF: 1.20-1.60
Expected losing-month percentage: 35%-60%
Expected worst single month: -5R to -12R
Expected R-multiple distribution: Clustered reversal wins after flow extremes, -1R failures when flows keep trending, no dependence on one outsized winner.
Expected max consecutive zero months: 3
expected_median_stop_points: 450
expected_cost_R_at_measured_50_75_spread: 0.11

## Mechanical Definition

Mechanical rules are byte-identical to `h4_gld_etf_flow_reversal_v0` by subclass alias (`src/phase0/strategies/h4_gld_etf_flow_reversal_v1_fullhist.py`); source v0 hypothesis SHA256 `2aa540060366b2363dcc3c5e4a3925916320f571d8b70b2cda7a574318ec72dd`, source v0 strategy SHA256 `4eb3872c589d40637347180b65df0b11826b3e8bbcee17dfe78f42848127081e`. The ONLY changes are (a) evaluation window = full available offline broker windows ending no later than 2025-06-30 (Capital.com and Dukascopy full target window; Pepperstone owner-accepted partial 2019-2021 with DATA_WINDOW_ASYMMETRY_PRESENT) and (b) gate set = locked `docs/PHASE0_LOWFREQ_GATE_SET_V1.md` selected per `docs/PHASE0_WAVE2_GATE_SET_V1.md` frequency rule. The GLD ETF daily-flow proxy frame (public Yahoo GLD OHLCV, 2015-01 through 2025-06-30) is unchanged.

## Expected Behavior

Low frequency (the v0 era cells produced 29-39 trades per 3-year cell; full windows should produce roughly 90-110 trades in the decade cells while Pepperstone remains near its v0 count, which the locked G2 gate will judge without mercy). The normalized G4 concentration gate applies at this frequency by design.

## Why This Hypothesis Should Exist

`h4_gld_etf_flow_reversal_v0` is the strongest independent lead in the project's entire rejection ledger: PF >= 1.30 in 9 of 9 cells INCLUDING at p95 stress cost, across all three broker-era blocks - the only audited candidate with full PF survival that is not breakout_retest-family. It was rejected solely on the 40-trade floor (29/39/36 per era cell), the old absolute concentration caps (since shown to be miscalibrated for low-frequency candidates and replaced by normalized G4), and the zero-month activity cap. This is a robustness re-test on triple the data under the corrected calibration - the exact precedent set by the Lane A v1_fullhist re-tests - not a tune: no rule, threshold, filter, or parameter changes. The twelve 2026-06-10/11 rejections (including the three Lane A re-tests, which had weaker PF evidence than this lead) are disclosed as the multiplicity context; D2 family-clustered Reality Check applies if matrix gates pass.

## What Would Falsify It

The locked PHASE0_LOWFREQ_GATE_SET_V1 (selected per the Wave-2 frequency rule): fewer than 7 of 9 PF cells at 1.30, any cell under 40 trades (Pepperstone's 2019-2021 window is the known risk), normalized concentration breach, drawdown or activity breach (max 3 consecutive zero-trade months - the second known risk for a bursty flow signal), p95-to-best PF ratio under 0.50, G7 cross-venue floor under 1.20, G8 modern-era failure, G9B realized cost breach, or adversarial review finding a logic mismatch. A failure is final for this version under NO_TUNING_RULES.md; no post-result rescue of any kind.

status: LOCKED
