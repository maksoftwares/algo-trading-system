# XAUUSD Calendar And Session Specialists V1 Preregistration

## Purpose

Prior campaigns found one under-sampled uptrend near-survivor and one event-fade
near-survivor, while broad regime, microstructure, COMEX lead/lag, and weekly CFTC
families failed. This campaign tests a genuinely different source of repeatable
opportunity: persistent time-of-day and completed-session behavior.

## Registered Mechanics

1. `UTC_HOUR_DIRECTIONAL_CARRY`: fixed long or short exposure beginning at a
   registered UTC hour.
2. `WEEKDAY_HOUR_DIRECTIONAL_CARRY`: fixed exposure for one weekday and UTC
   hour combination.
3. `PRIOR_SESSION_CONTINUATION`: follow a completed 3-24 hour XAU impulse at a
   registered six-hour session boundary.
4. `PRIOR_SESSION_REVERSAL`: fade that completed impulse.
5. `SESSION_RANGE_EXTREME_REVERSION`: at a session boundary, fade a completed
   close near the edge of its rolling 6-48 hour range.

Exactly 200 deterministic, coverage-eligible policies per mechanic are locked,
for 1,000 attempts numbered 10,094 through 11,093. Coverage selection may inspect
timestamps and raw signal counts only; it may not inspect returns or trade outcomes.

## Causality And Execution

- Decisions occur only after a completed H1 bar.
- Returns, ATR, rolling ranges, weekday, and UTC hour are known at the decision.
- Entry is the next contiguous native M5 Ask for a long or Bid for a short.
- Stops and targets execute on the opposite quote side; stop wins same-M5
  ambiguity and gap-through stops receive the worse executable open.
- Native spread, a fixed ticket cost, holding cost, and stress slippage are charged.
- A policy may hold one position and take at most one trade per UTC day.
- Significance uses all source trading days, including zero-trade days.

## Chronological Firewall

- Discovery: 2016-07-01 through 2020-12-31.
- Confirmation: 2021-01-01 through 2022-12-31.
- Internal test: 2023-01-01 through 2024-12-31.
- Exam: 2025-01-01 through 2026-06-30.

Benjamini-Hochberg correction is applied across all incoming policies at each
stage. At most one unchanged policy per mechanic may advance. A failed stage seals
all later outcomes for that policy.

Research only. No model training, Python serving, EA use, demo/live orders, broker
action, Databento use, or paid acquisition is authorized.
