# A1 XAU H4/D1 No-Op Parity Audit Preregistration

Date: 2026-07-07

## Scope

Run an exact-MT5 no-op rerun for the two H4/D1 long components inside the current `F67-H16 no-f33` frontier:

- `h4_d1_long_best_box2_atr80`
- `h4_d1_long_broad_box3_atr60`

The run must leave both new repair controls disabled:

- `InpH4D1SupportiveStateGuardEnabled=false`
- `InpH4D1WeeklyLossGovernorEnabled=false`

The run must also pin the archived tester session behavior observed in the original baseline:

- `InpBlockedEntryDayHoursCsv=5:20`

Reason: the original H4/D1 baseline order log saw Friday server-hour `20:00` H4/D1 signals but MT5 rejected them with retcode `10018 market closed`. A first no-op audit under the refreshed tester environment accepted exactly those Friday `20:00` orders, creating a `+15` trade / `+730.55 USD` drift. The parity audit therefore treats Friday `20:00` as an archived-comparison session boundary, not as a strategy tuning rule.

No TP/SL, source priority, session/hour mask, frequency-source setting, source membership, or dedupe rule is changed.

## Purpose

This is not a strategy improvement probe. It is an audit row requested after review of commit `4e2f63c`.

The audit must prove that the current exact-MT5 H4/D1 rerun plus offline exact-ledger recomposition reproduces the established baseline when no new guard is enabled.

## Baseline

Baseline artifact:

- `outputs/reports/A1_XAU_HYBRID_F67_H16_NO_F33_COMPOSITION_202207_202606_KEPT.csv`

Baseline headline:

- Signals: `3751`
- WR: `50.23%`
- W/L: `2.0002`
- Active weekdays: `86.39%`
- PF: `2.0336`
- Net: `22294.46 USD`
- Stress `-$0.30/ticket` W/L: `1.9029`
- Exit-time positive weeks: `54.81%`
- Worst week: `-878.18 USD`
- Recent 3M net: `-1226.32 USD`
- May 2026 net: `-1055.98 USD`

## Recomposition

1. Run exact MT5 Strategy Tester for both H4/D1 components with baseline inputs and no new guard enabled.
2. Remove the baseline H4/D1 rows and the previously removed `step1_f33_r30_be_never` source from `A1_XAU_HYBRID_F67_H16_EXACT_REPAIR_202207_202606_HYBRID_RAW.csv`.
3. Add the two no-op H4/D1 exact-MT5 replacement ledgers.
4. Dedupe using the existing signal-composition function.
5. Score full-window metrics, stress `-$0.30/ticket`, recent 3M, May 2026, weekly shape, source contributions, row-count deltas, and guard block counts.

## Pass/Fail

PASS requires all of:

- Total kept signal count exactly equals baseline.
- Total net differs from baseline by no more than `0.01 USD`.
- WR differs from baseline by no more than `0.01 percentage points`.
- W/L differs from baseline by no more than `0.0001`.
- Active weekdays differs from baseline by no more than `0.01 percentage points`.
- Positive weeks differs from baseline by no more than `0.01 percentage points`.
- Worst week differs from baseline by no more than `0.01 USD`.
- Recent 3M net differs from baseline by no more than `0.01 USD`.
- May 2026 net differs from baseline by no more than `0.01 USD`.
- H4/D1 source-level kept signal counts and net match baseline within the same count and `0.01 USD` tolerances.

If this audit fails, stop new source work until the recomposition drift is explained.
