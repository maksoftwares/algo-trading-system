# CFTC Options-Positioning Mechanics V1 Preregistration

## Purpose

This campaign tests whether official weekly gold options positioning contains a
causal routing signal for XAUUSD. It is a genuinely new information source. The
earlier COT candidates used futures-only positioning; this campaign subtracts
futures-only records from futures-and-options-combined records to estimate
delta-equivalent option positions.

## Registered Mechanics

1. `MM_OPTIONS_FLOW_CONTINUATION`: follow a standardized weekly managed-money
   option-positioning change.
2. `MM_OPTIONS_CROWDING_REVERSAL`: fade an extreme managed-money option level,
   optionally after price extends with the crowd.
3. `PRODUCER_MM_OPTIONS_DIVERGENCE`: follow the managed-money side of an extreme
   producer-versus-managed-money option-positioning divergence.
4. `SWAP_OPTIONS_HEDGE_PRESSURE`: trade opposite an extreme swap-dealer option
   positioning change, treating dealer pressure as hedging rather than alpha.
5. `OPTIONS_FUTURES_DISLOCATION`: follow an extreme managed-money options-minus-
   futures positioning dislocation.

Exactly 200 deterministic policies per mechanic are admitted after an
outcome-blind raw-signal coverage check, for 1,000 attempts numbered 8,094
through 9,093. Coverage selection may inspect only contemporaneously available
features in the discovery window. It may not inspect entries, exits, or P&L.

## Causality

- The official CFTC report is usable only from the first Monday strictly after
  its as-of date at 00:00 UTC.
- Positioning z-scores use means and standard deviations from prior reports;
  the current report is excluded from its own baseline.
- Price confirmation uses only a completed H1 bar.
- Entry is the first contiguous M5 quote after that H1 close, at Ask for long
  and Bid for short.
- Stops are resolved before targets when both occur inside one M5 bar.
- Weekly report blocks, including zero-trade blocks, drive significance tests.

## Chronology

- Discovery: 2016-07-01 through 2020-12-31.
- Confirmation: 2021-01-01 through 2022-12-31.
- Internal test: 2023-01-01 through 2024-12-31.
- Exam: 2025-01-01 through 2026-06-30.

Only discovery is opened initially. Each later stage remains sealed unless an
unchanged policy passes every prior gate and is named in a hashed advancement
lock. Benjamini-Hochberg correction is applied across every policy entering a
stage.

## Authority

Research only. This campaign cannot authorize model training, Python serving,
EA consumption, demo orders, live orders, broker actions, Databento use, or any
paid data request.

