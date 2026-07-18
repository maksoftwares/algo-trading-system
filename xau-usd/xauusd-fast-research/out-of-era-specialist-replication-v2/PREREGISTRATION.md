# XAUUSD Out-of-Era Specialist Replication V2

Date: `2026-07-18`

## Purpose

This package opens the previously unused 2010-01-01 through 2016-06-30
Dukascopy period exactly once for five fixed candidates. It supersedes the
locked-but-unopened V1 replication and breakout V2 packages after their event
dependency was invalidated.

## Registered Family

1. `R1_UPTREND_PORTABILITY_EXACT`: unchanged portfolio-constrained R1 rule.
2. `R1B_STRICT_COMPRESSION_EXACT`: unchanged strict compression variant.
3. `COMPRESSION_LONG_PORTABILITY_EXACT`: unchanged broader long compression
   breakout.
4. `FOMC_IMPULSE_CHOP_RR2_V6`: attempt 11,112. It uses the corrected FOMC
   impulse mechanics without parameter changes and accepts candidates only when
   the last causally completed H4 regime is `CHOP`.
5. `FOMC_IMPULSE_STABLE_NON_UPTREND_RR2_V7`: attempt 11,113. It uses the same
   event mechanics in stable `CHOP`, `COMPRESSION`, or `TREND_DOWN` states. This
   broader rule was registered because the outcome-free old-period preflight
   showed the CHOP-only sample could not reach its minimum-trade gate. In the
   already-opened 2016-2026 discovery evidence, CHOP and TREND_DOWN were positive
   in both reported eras while COMPRESSION was flat rather than negative.

The FOMC regime restrictions were registered after the unchanged broad FOMC rule
showed positive but concentrated 2022-2026 holdout economics. No 2010-2016
returns had been opened when this restriction, its gate, or its release-time
rules were written.

## Official Calendar

Only statements attached to regular meetings on the Federal Reserve historical
pages are eligible. Conference calls and statement links outside the sealed
date range are excluded mechanically.

- Before 2013-03-20, the release clock is `14:15 America/New_York`.
- From 2013-03-20 onward, it is `14:00 America/New_York`.

The switch is supported by the Federal Reserve's 2013-03-13 announcement that
regular-meeting policy statements would now be released at 2:00 p.m. Eastern.
All historical pages, statement pages, the timing announcement, the derived
calendar, and their hashes are frozen before outcomes.

## Data And Execution

- XAUUSD: free Dukascopy Bid/Ask ticks, 78 complete calendar months.
- Price candidates: unchanged source code and portfolio policies.
- Event candidate: causal M5 signal bars and causal H4 regime only.
- Event exits: verified lossless normalized ticks whose source manifests and
  partitions are contract-hashed before outcomes.
- Costs, spread ceilings, stop ceilings, stop-first ordering, and holding costs
  are frozen in the JSON contract.

Any missing month, source hash change, duplicate event, ambiguous historical
heading, future regime timestamp, crossed quote, or outcome-like prelock column
fails closed.

## Decision Rule

All five candidates form one Holm family. Candidate-specific economic gates are
fixed in the JSON contract. Surviving ledgers are then checked pairwise for
same-direction entry overlap and daily P&L correlation in a fixed selection
order. R1B and broad compression cannot both count as independent merely because
both are profitable. The two FOMC variants also share one mechanism family, so
at most one can count as a distinct survivor.

No same-version rescue, inversion, threshold adjustment, window change,
direction removal, or subgroup selection is permitted after opening outcomes.
A pass is research evidence only and still requires combined-era portfolio and
prospective shadow validation.

## Authority

Research only. Paid data, Databento, broker actions, model training, Python
prediction serving, EA consumption, demo trading, and live trading are not
authorized.
