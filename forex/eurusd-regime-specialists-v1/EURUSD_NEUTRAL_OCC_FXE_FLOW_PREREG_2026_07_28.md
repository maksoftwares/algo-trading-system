# EURUSD Neutral OCC FXE customer-flow preregistration

Date: 2026-07-28

Status: `FROZEN_BEFORE_HISTORICAL_OUTCOME_PASS`

## Hypothesis

The Neutral oracle's missing variable is direction. Price-only,
cross-asset, futures-participation, and aggregate weekly positioning
signals have failed to identify it.

This campaign tests a genuinely new causal source: daily OCC-cleared
customer call and put volume on FXE options. Relative demand for FXE calls
versus puts is used as a directional euro vote after normalizing for the
instrument's structural put/call bias.

## Official free source

OCC documents a credential-free Volume Query Batch Processing endpoint
with underlying-symbol, account-type, and call/put controls. The frozen
query is:

```text
volumeQueryType=O
symbolType=U
symbol=FXE
reportType=D
accountType=C
productKind=OSTK
porc=BOTH
```

The endpoint retains approximately two rolling years. The acquired window
is 2024-07-29 through 2026-06-30. It contains 502 weekday responses, 482
with records, 134,069 customer calls, and 222,686 customer puts. Raw
responses, a chain hash, normalized Parquet, and a manifest reside at:

```text
D:/AlgoTradingData/research/eurusd-neutral-occ-fxe-flow-v1/
```

The source and manifest are hash-pinned. No account, OTP, paid service, or
scraping bypass is used.

## Fixed causal rule

For each 00:00 UTC state classified as non-shock, non-compressed Regime 1
`NEUTRAL`:

1. Use only the latest OCC report considered available at 00:00 UTC on the
   calendar day after its trade date. Maximum source age is 96 hours.
2. Aggregate customer call and put volume across exchanges.
3. Define raw imbalance as `log1p(calls) - log1p(puts)`.
4. Subtract the median raw imbalance of the preceding 20 source sessions.
   The current session is excluded from this baseline.
5. Divide total customer volume by its preceding-20-session median and
   require a ratio of at least 1.0.
6. Trade long when normalized imbalance is positive and short when it is
   negative. Ties, missing reports, no-record reports, and insufficient
   baseline history remain cash.
7. Permit one entry and one position per UTC date.
8. Use fixed 4-pip risk, 1.50R target, 12-hour maximum hold, a 0.7-pip
   retail spread floor, 0.1-pip adverse slippage per side, and stop-first
   same-bar handling.

There is one fixed rule, no fitted model, no threshold grid, and no
post-outcome choice between raw and normalized put/call ratios.

## Outcome-blind census

The candidate ledger was built before EURUSD exits or oracle membership
were opened:

| Item | Count |
|---|---:|
| Neutral midnight states in source window | 142 |
| Source-available states | 139 |
| Active-participation trades | 78 |
| Long / short | 41 / 37 |

Chronological counts are:

- development: 24;
- validation 2025 Q2-Q3: 18;
- pseudo-OOS 2025 Q4-2026 Q1: 28;
- final 2026 Q2: 8.

## Chronology and gates

The four windows above are evaluated independently. Minimum sample sizes
are 20, 10, 10, and 5. Each window must have 45%-55% wins, realized payoff
from 1.35 to 1.75, positive expectancy, and PF at least 1.0.

Across all 78 candidates, PF must be at least 1.30, extra-half-pip stressed
PF at least 1.15, maximum drawdown no more than 20R, exact oracle precision
at least 40%, and net return after removing the largest 5% of winners must
remain positive.

All EURUSD execution history has been inspected previously, so even this
new source is not pristine proof. Passing can authorize only prospective
watchlist collection. Failure closes this exact rule without repair.
