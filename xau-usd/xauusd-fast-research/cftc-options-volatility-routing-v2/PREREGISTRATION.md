# CFTC Options Volatility Routing V2 Preregistration

## New Hypothesis

Directional CFTC options-positioning V1 failed discovery. V2 does not invert,
tune, or relabel those rules. It tests a different role for the same external
source: option activity may identify when volatility is likely to expand or
contract, while completed XAUUSD price structure determines trade direction.

## Registered Mechanics

1. `OPTIONS_OI_EXPANSION_BREAKOUT`: trade an H1 channel break when weekly
   option-equivalent open-interest growth is unusually high.
2. `OPTIONS_OI_CONTRACTION_REVERSAL`: fade a completed multi-hour XAU impulse
   when option-equivalent open interest contracts unusually fast and the H1
   candle confirms the reversal.
3. `MM_OPTIONS_SPREAD_BUILD_BREAKOUT`: trade an H1 channel break when managed-
   money option spreading increases unusually fast.
4. `SWAP_OPTIONS_SPREAD_BUILD_BREAKOUT`: trade an H1 channel break when swap-
   dealer option spreading increases unusually fast.
5. `GROSS_OPTION_ACTIVITY_COMPRESSION_BREAKOUT`: trade an H1 channel break from
   price compression when total reportable option activity is unusually high.

Exactly 200 deterministic, coverage-eligible policies per mechanic are locked,
for 1,000 attempts numbered 9,094 through 10,093. Coverage inspection uses no
trade outcome or P&L.

## Causality And Execution

- CFTC values become usable only on the first Monday strictly after the report
  as-of date.
- Every activity z-score excludes the current report from its baseline.
- Channels, impulses, ATR, and compression use completed H1 bars only.
- Entry is the next contiguous native M5 Ask for long or Bid for short.
- Stop wins any same-M5 stop/target ambiguity.
- One trade per UTC day and three trades per CFTC report are allowed per policy.
- Significance uses weekly report blocks including zero-trade blocks.

Discovery, confirmation, internal test, and exam retain the frozen V1 date
boundaries and gates. Later stages remain sealed unless a prior unchanged
passer is recorded in a hashed advancement lock.

Research only. No model training, Python serving, EA use, demo/live orders,
broker action, Databento use, or paid acquisition is authorized.
