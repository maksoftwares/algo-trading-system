# EURUSD Neutral DTCC OTC FX-options preregistration

Date: 2026-07-28

Status: `FROZEN_BEFORE_HISTORICAL_OUTCOME_PASS`

## Hypothesis

The Neutral oracle's unresolved variable is the direction selected at the
00:00 UTC opening. Price, cross-pair, Treasury/DXY, weekly positioning,
exchange-volume, OCC-listed-options, and two-sided price-selection rules
have not identified that direction reliably.

This campaign tests a genuinely different causal source: transaction-level
public dissemination of executed OTC EUR/USD vanilla options. Standalone
new calls and puts with 7-90 day tenor are treated as a directional hedging
flow proxy. Call-versus-put EUR notional and USD premium imbalances receive
equal fixed weight after each is centered on its own trailing structural
bias.

## Official free source

The CFTC requires registered swap data repositories to publish transaction
and pricing data in machine-readable form. DTCC's Public Price Dissemination
dashboard exposes its CFTC search without credentials:

- <https://www.cftc.gov/MarketReports/SwapsReports/index.htm>
- <https://pddata.dtcc.com/ppd/search>

The acquired source window is 2025-07-29 through 2026-06-30. It contains
674 raw responses, 337 calendar dates, 248 active source sessions, 7,154
qualified calls, and 6,649 qualified puts. Median daily qualified counts on
active sessions are 27 calls and 25 puts.

Raw responses, a deterministic chain hash, normalized Parquet, and a
manifest reside at:

```text
D:/AlgoTradingData/research/eurusd-neutral-dtcc-fx-options-v1/
```

The source and manifest are hash-pinned. No login, account, OTP, or paid
service is used.

## Frozen source qualification

Only records satisfying every condition below are included:

1. jurisdiction `CFTC` and asset class `FOREIGNEXCHANGE`;
2. UPI short name exactly `NA/O Van Call EUR USD` or
   `NA/O Van Put EUR USD`;
3. action `NEWT`, event `TRAD`, and package indicator `FALSE`;
4. underlying exactly `EUR USD`;
5. dissemination no earlier than execution and no more than 24 hours later;
6. expiry tenor from 7 through 90 calendar days;
7. directional option notional denominated in EUR and premium denominated
   in USD;
8. positive notional and premium; and
9. deduplication only by DTCC dissemination identifier.

Corrections, modifications, terminations, errors, package transactions,
stale reports, non-vanilla structures, and unusable currencies remain
excluded. Historical rows are grouped by their actual public dissemination
UTC date and become eligible only at the next UTC midnight.

## Fixed causal rule

For each 00:00 UTC state classified as non-shock, non-compressed Regime 1
`NEUTRAL`:

1. Use the latest eligible source session no older than 96 hours.
2. Define notional imbalance as
   `log1p(call EUR notional) - log1p(put EUR notional)`.
3. Define premium imbalance as
   `log1p(call USD premium) - log1p(put USD premium)`.
4. Center each imbalance by subtracting its preceding 20-active-session
   median. The current source session is excluded.
5. Define the composite as 0.5 times normalized notional imbalance plus
   0.5 times normalized premium imbalance.
6. Trade long when the composite is positive and short when it is negative.
   Ties, missing data, stale data, and insufficient baseline history remain
   cash.
7. Permit one entry and one position per UTC date. There is no activity
   threshold or fitted coefficient.
8. Use fixed 4-pip risk, 1.50R target, 12-hour maximum hold, a 0.7-pip
   retail spread floor, 0.1-pip adverse slippage per side, and stop-first
   same-bar handling.

There is one fixed rule, no fitted model, no threshold grid, no tenor
alternative, and no post-outcome choice between notional and premium flow.

## Outcome-blind census

The source was joined only to decision timestamps and regime state before
this lock. EURUSD exits and oracle membership were not opened.

| Item | Count |
|---|---:|
| Neutral midnight states | 66 |
| Source-available states | 66 |
| Trade candidates | 66 |
| Long / short | 29 / 37 |
| Development, 2025 Sep-Dec | 27 |
| Pseudo-OOS, 2026 Q1 | 22 |
| Final, 2026 Q2 | 17 |

## Chronology and gates

Each window must meet its frozen minimum sample size of 12, 8, and 5,
respectively. Each must have 45%-55% wins, realized payoff from 1.35 to
1.75, positive expectancy, and PF at least 1.0.

Across all 66 candidates, PF must be at least 1.30, extra-half-pip stressed
PF at least 1.15, maximum drawdown no more than 20R, exact oracle precision
at least 40%, and net return after removing the largest 5% of winners must
remain positive.

The EURUSD execution archive has been inspected in previous campaigns, so
even this new external source is not pristine proof. A pass can authorize
only an untouched prospective watchlist. A failure closes this exact rule
without reversal, threshold repair, subperiod selection, or source-field
mining.
