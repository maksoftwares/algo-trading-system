# EURUSD Neutral DTCC matched-premium-skew preregistration

Date: 2026-07-28

Status: `FROZEN_BEFORE_SKEW_OUTCOME_PASS`

## Hypothesis

The first DTCC experiment treated executed OTC call and put totals as
directional flow. It failed and is closed without reversal or repair.

This campaign tests the distinct options-surface hypothesis that motivated
the earlier CME risk-reversal work but could not be evaluated for lack of
history: whether matched OTM call-versus-put premium richness contains
causal directional information. Transaction size is not used to vote on
direction. Instead, each option premium is scaled by spot-adjusted
notional, and calls and puts are matched on tenor and absolute moneyness
before their premium rates are compared.

No DTCC skew value was joined to an EURUSD exit or oracle label before this
contract and census were frozen.

## Free source and causal spot

DTCC's credential-free CFTC Public Price Dissemination data supplies the
executed option fields. EURUSD M5 bid/ask bars supply only the latest
mid-close completed before each option execution:

- <https://www.cftc.gov/MarketReports/SwapsReports/index.htm>
- <https://pddata.dtcc.com/ppd/search>

Source artifacts are stored at:

```text
D:/AlgoTradingData/research/eurusd-neutral-dtcc-skew-v1/
```

The hash-pinned source contains 4,277 qualified standalone OTM trades:
2,549 calls and 1,728 puts. Deterministic matching produced 610 pairs over
204 source dates. Requiring at least three pairs leaves 103 eligible source
sessions from 2025-08-01 through 2026-06-30. No login, OTP, or paid data is
used.

## Frozen surface construction

1. Inherit the DTCC standalone `NEWT/TRAD` vanilla-record qualification,
   real-time dissemination constraint, and dissemination-ID deduplication.
2. Restrict expiry tenor to 14-60 calendar days.
3. At each option execution, use the mid-close of the latest M5 EURUSD bar
   completed beforehand, with maximum age 30 minutes.
4. Keep OTM calls and puts with absolute log moneyness from 0.001 through
   0.03.
5. Define premium rate as USD premium divided by EUR notional times causal
   EURUSD spot.
6. Match calls and puts from the same dissemination UTC date when tenor
   differs by no more than seven days and absolute log moneyness by no more
   than 0.0025.
7. Sort possible pairs by normalized tenor-plus-moneyness distance and
   greedily accept the closest pairs without trade reuse. Identifier order
   breaks ties.
8. Define pair skew as log call premium rate minus log matched-put premium
   rate. Daily skew is the median pair skew.
9. A source session is eligible only with at least three matched pairs.

These boundaries implement an approximately one-month, symmetrically OTM
premium-skew proxy. There is no implied-volatility model, interest-rate
assumption, fitted delta, alternative pairing result, or post-outcome
surface choice.

## Fixed causal trading rule

For each 00:00 UTC state classified as non-shock, non-compressed Regime 1
`NEUTRAL`:

1. Use the latest eligible source session no older than 96 hours.
2. Subtract the median daily skew of the preceding 20 eligible source
   sessions. The current session is excluded.
3. Trade long when normalized skew is positive and short when it is
   negative. Ties, missing or stale data, and insufficient baseline history
   remain cash.
4. Permit one entry and one position per UTC date.
5. Use fixed 4-pip risk, 1.50R target, 12-hour maximum hold, a 0.7-pip
   retail spread floor, 0.1-pip adverse slippage per side, and stop-first
   same-bar handling.

There is one fixed direction rule, no model, no threshold grid, and no
choice between raw and normalized skew after outcomes.

## Outcome-blind census

| Item | Count |
|---|---:|
| Neutral midnight states | 63 |
| Source-available trades | 48 |
| Long / short | 24 / 24 |
| Development, 2025 Q4 | 16 |
| Pseudo-OOS, 2026 Q1 | 18 |
| Final, 2026 Q2 | 14 |

## Chronology and gates

Each window must meet its frozen minimum sample size of 10, 8, and 5,
respectively. Each must have 45%-55% wins, realized payoff from 1.35 to
1.75, positive expectancy, and PF at least 1.0.

Across all 48 candidates, PF must be at least 1.30, extra-half-pip stressed
PF at least 1.15, maximum drawdown no more than 20R, exact oracle precision
at least 40%, and net return after removing the largest 5% of winners must
remain positive.

All EURUSD execution history has been inspected in earlier campaigns. A
historical pass can authorize only an untouched prospective watchlist. A
failure closes this exact matched-skew rule without direction reversal,
surface repair, threshold search, or subperiod selection.
