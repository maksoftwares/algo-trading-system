# EURUSD Neutral CME options-surface preregistration

Frozen: 2026-07-27

Campaign: `eurusd-neutral-cme-options-surface-v1`

Status: `BLOCKED_LICENSED_HISTORY_NOT_PRESENT`

## Hypothesis

Regime 1 may require forward-looking information that is absent from
EURUSD price bars and weekly aggregate positioning. The market-defined
25-delta EUR/USD risk reversal is a causal directional measure:

```text
RR25 = 25-delta call implied volatility
     - 25-delta put implied volatility
```

Positive RR25 fixes `LONG` EURUSD. Negative RR25 fixes `SHORT`. Zero or an
invalid surface fixes `CASH`. There is no fitted threshold, model, sign
selection, or oracle-label input.

## Official dataset and validated schema

CME DataMine dataset:

- dataset ID `0e3d0545a67b165bfb2ea9adf6f3f0c6`;
- dataset code `EOD_XCME_EUU_OPT_0`;
- `Premium Quoted European Style Options on Euro/US Dollar Futures`;
- catalog coverage 2016-08-09 through 2026-07-24;
- 7,524 listed files;
- daily gzip delivery;
- early 18:00 CT, preliminary 22:00 CT, final 10:00 CT on T+1.

The public schema and 2025-07-01 sample were inspected before any outcome
run. The file has explicit trade date, put/call, strike, contract year and
month, settlement, open interest, total volume, delta, implied volatility,
and last-trade-date columns. The sample has 100 rows and both `C` and `P`
records, but its delta and implied-volatility cells are empty. Therefore
the implementation must be able to reconstruct them from settlements.

## Frozen surface construction

1. Use only final EUU files.
2. Normalize strike as the integer file value divided by 10,000.
3. Group rows by trade date and last trade date.
4. Keep expiries from 20 through 45 calendar days and choose the expiry
   closest to 30 days.
5. Require at least seven same-strike call/put pairs.
6. Infer the futures forward and discount factor from:

   ```text
   call - put = discount * (forward - strike)
   ```

7. Use a valid reported implied volatility when present. Otherwise invert
   Black-76 from the official settlement.
8. Use a valid reported delta when present. Otherwise calculate absolute
   Black-76 forward delta.
9. Choose the call and put nearest absolute 0.25 delta; both must be
   within 0.08 delta of target.
10. Calculate RR25 in volatility percentage points and apply its sign
    without a magnitude threshold.

Any invalid parity fit, missing pair, non-invertible premium, inadequate
delta match, or missing final file is `CASH`.

## Availability and execution

The earliest decision is the first 00:00 UTC strictly after CME's final
10:00 CT T+1 release. Real file publication timestamps must supersede the
weekday approximation, especially around holidays.

Only Regime 1 Neutral candidates may trade. Execution remains frozen at
4-pip risk, 1.50R target, 12-hour maximum hold, exact bid/ask prices,
0.70-pip spread floor, 0.10-pip adverse slippage per side, stop-first
ambiguous M5 bars, and at most one trade per UTC date.

## Chronology and gates

Development is 2019-2022. Forward windows are 2023, 2024, 2025, and 2026
H1. The source, parser, surface rule, and direction must be frozen before
opening oracle membership or trade outcomes.

Development and every forward window must achieve:

- 45%-55% win rate;
- 1.35-1.75 realized payoff;
- PF at least 1.10 and positive expectancy;
- at least 25% exact oracle precision, 2% exact recall, and 25% same-side
  precision within 15 minutes.

Overall maximum drawdown may not exceed 30R. Net R must remain positive
after an extra half-pip round trip and after removing the largest 5% of
winners.

## Data blocker

The public Daily Bulletin cannot supply history: CME states that it keeps
only the top day and overwrites it when the next file is posted. The exact
EUU EOD dataset has the required 2016-2026 history and schema, but the
catalog lists complete history at USD 2,249. No licensed export, CME
DataMine entitlement, or corresponding local files are present.

No backtest may be represented as complete until final EUU files covering
2019-01-01 through 2026-06-30 are supplied and SHA-256 pinned. Current-day
PDFs, the public 100-row sample, CFTC aggregate options, or a spot proxy
are prohibited substitutes.
