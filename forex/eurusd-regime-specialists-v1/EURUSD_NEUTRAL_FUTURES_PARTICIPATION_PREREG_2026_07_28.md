# EURUSD Neutral exchange-participation preregistration

Date: 2026-07-28

Status: `FROZEN_BEFORE_HISTORICAL_OUTCOME_PASS`

## Hypothesis

The earlier Neutral direction models used spot prices, quoted
microstructure, cross pairs, DXY/Treasury prices, and weekly CFTC
positions. They did not observe daily participation in the exchange-traded
Euro and dollar instruments.

This campaign tests one new mechanism: a completed Euro FX futures move is
more informative when a dollar-bull instrument confirms the opposite
direction and both markets traded with above-normal combined volume.

This is not an options substitute. It is a separately bounded
exchange-participation experiment.

## Free source and evidence boundary

The source is a zero-cost, credential-free snapshot from Yahoo Finance's
public chart endpoint:

- CME Euro FX continuous futures (`6E=F`);
- Invesco DB US Dollar Index Bullish Fund (`UUP`) as the
  exchange-traded dollar-bull proxy.

The requested snapshot is 2018-01-01 through 2026-06-30. Raw JSON,
normalized Parquet, and the acquisition manifest reside under:

```text
D:/AlgoTradingData/research/
  eurusd-neutral-futures-participation-v1/
```

Every admitted source is hash-pinned in the frozen configuration. Yahoo is
a third-party, revisable continuous-contract source. The local snapshot is
research evidence only and is not claimed to reproduce an official CME
settlement archive.

## Fixed causal rule

For each non-shock, non-compressed Regime 1 `NEUTRAL` state at 00:00 UTC:

1. Use only the latest exchange session assigned to an earlier trade date.
   Each source row is conservatively considered available at 00:00 UTC on
   the following calendar day.
2. Require the Euro FX and UUP rows to have the same trade date and be no
   more than 96 hours old.
3. Define each directional vote from that session's close divided by open
   minus one. Invert the UUP vote because it is dollar-bull.
4. Require the Euro and inverted-UUP votes to agree.
5. For each source, divide session volume by the median of the preceding
   20 valid sessions. The current session is excluded from its own
   baseline.
6. Define participation as the geometric mean of the two volume ratios and
   require it to be at least 1.0.
7. Trade long when both directional votes are positive and short when both
   are negative. Otherwise remain cash.
8. Permit one entry per UTC date and one open position.
9. Use fixed 4-pip risk, 1.50R target, 12-hour maximum hold, a 0.7-pip
   retail spread floor, 0.1-pip adverse slippage per side, and stop-first
   handling when both barriers occur in the same M5 bar.

There is one rule, one participation threshold, no fitted model, no
parameter grid, and no subgroup selection.

## Outcome-blind census

The census was produced before any exit path or oracle membership was
opened:

| Item | Count |
|---|---:|
| Neutral midnight states | 655 |
| Same-date valid source pairs | 634 |
| Direction agreements | 446 |
| Trade candidates | 227 |
| Long / short | 105 / 122 |

Annual candidates are 36, 31, 38, 30, 22, 21, 31, and 18 for 2019 through
2026 H1 respectively.

## Chronology

- development: 2019-2022;
- validation: 2023 and 2024 separately;
- pseudo-out-of-sample: 2025 and 2026 H1 separately;
- trailing diagnostics: 3, 6, 12, 24, and 60 months.

All archived EURUSD history has been inspected by earlier campaigns.
Consequently these labels describe a disciplined chronological test, not
a pristine untouched holdout.

## Frozen admission gates

Development requires at least 60 trades. Each later window requires at
least 10 trades. Every window must have:

- 45% to 55% wins;
- realized payoff from 1.35 to 1.75;
- positive expectancy and PF at least 1.0.

Across the full archive, PF must be at least 1.30, extra-half-pip stressed
PF at least 1.15, maximum drawdown no more than 30R, and net return after
removing the largest 5% of winners must remain positive.

Forward exact oracle precision must be at least 40% and exact recall at
least 2%. Oracle data may be loaded only after the fixed trade ledger has
been generated.

Passing all historical gates can authorize only a prospective research
watchlist. Failure closes this exact rule without repair.
