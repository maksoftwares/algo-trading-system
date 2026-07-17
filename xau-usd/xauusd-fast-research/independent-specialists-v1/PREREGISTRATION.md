# XAUUSD Independent Specialists V1 Preregistration

Date: `2026-07-17`

## Objective

Test whether complete Dukascopy Bid/Ask history supports several independent gold
specialists with positive after-cost expectancy, useful combined frequency, and
controlled drawdown. This is a bounded rejection screen, not an optimizer.

## Frozen Families

1. `R1_H1_TREND_PULLBACK_LONG_V1`: H4 uptrend ownership, completed H1 pullback and
   bullish resumption, structural stop, 2R target.
2. `R2_H1_TREND_PULLBACK_SHORT_V1`: symmetric H4 downtrend ownership and bearish
   H1 resumption.
3. `R3_H1_COMPRESSION_BREAK_RETEST_V1`: completed H1 compression, separate breakout,
   later M15 retest-and-hold, 2R target.
4. `R4_M15_SESSION_EXPANSION_V1`: London/Asia or New York/London range expansion,
   completed M15 confirmation, 1.5R target.
5. `R5_M30_CHOP_ROTATION_V1`: H4 chop ownership, prior M30 excursion, equilibrium
   recapture and rotation target. This independently checks the earlier incomplete
   Capital.com clue on the complete Dukascopy source.

Shock, unsafe volatility, unknown state, and unresolved transition are abstain
states. R1/R2 own H4 trends, R3 owns H4 compression, and R5 owns H4 chop. R4 is
identified by a separate completed session-range expansion and may act only when
the H4 state is resolved and non-unsafe. Its overlap with every other family is
therefore measured explicitly rather than assumed independent.

## Data And Causality

- Source: verified Dukascopy XAUUSD Bid/Ask cache, 120 months.
- Locked cache SHA-256: `e587306f530a615dfdc6f869c4f79f881cfa0b572e078fd26d3c9995fbc66228`.
- Signal features use completed bars only.
- Entry is the next contiguous M5 open: long at Ask, short at Bid.
- Long exits use Bid and short exits use Ask.
- Stop/target collisions in one M5 bar are stop-first.
- Native spread is embedded in the side-specific prices.
- Stress subtracts `$0.30` per 0.01-lot trade, `$0.35` per 24 hours held, and
  another `0.05R` adverse slippage.

## Chronological Firewall

- Train: 2016-07-01 through 2020-06-30.
- Validation: 2020-07-01 through 2022-06-30.
- Internal test: 2022-07-01 through 2024-06-30.
- Exam: 2024-07-01 through 2026-06-30.
- Prospective holdout begins 2026-07-01.

Validation is eligible only after a train pass. Internal test is eligible only after
train and validation pass. Exam is eligible only after all earlier stages pass. The
repository has inspected retrospective history before, so no retrospective window is
described as untouched.

## Acceptance Boundary

Each specialist must pass minimum sample size, stress PF, average stress R, active
month stability, drawdown, and winner-removal gates in every eligible stage. The
combined exam target is at least `0.8` accepted trades per source day, stress PF at
least `1.30`, average stress R at least `0.05`, and closed drawdown at most `20R`.
Every survivor pair must also keep same-direction entries within 60 minutes at or
below `20%` of the smaller trade set and absolute daily stress-P&L correlation at
or below `0.60`.

The nominal research risk ceiling is `$50` at 0.01 lot. Current-account feasibility
at approximately `$8.17` risk is reported separately and cannot change economic
classification.

## Anti-Overfit Rule

The five definitions and their numerical settings are frozen before outcome scoring.
No failed family is repaired, inverted, session-masked, or threshold-tuned in V1.
Any later mechanism requires a new preregistration and version.

## Authorization

Research only. No model training authorization, EA signal consumption, broker action,
demo promotion, or live promotion follows from this campaign.
