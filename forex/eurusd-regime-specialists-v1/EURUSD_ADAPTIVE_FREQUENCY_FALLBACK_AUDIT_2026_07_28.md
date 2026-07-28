# EURUSD adaptive frequency fallback audit

Date: `2026-07-28`

Status: `REJECTED_AS_REGIME_1_IMITATION / NO_DEMO_PROMOTION`

The prior Capital.com result is reproducible from the two raw MT5 reports:
`697` trades, `57.82%` wins, PF
`1.3075`, and `$119.42` net.
The audit does not dispute that selected historical result. It rejects the
stronger claim that the portfolio is a robust, independent Regime 1 expert.

## What the headline concealed

- Realized payoff is `0.954`, not the requested
  approximately `1.5`.
- The best 5% of trades contribute
  `93.78%` of total net.
- PF after removing those winners is
  `1.019`.
- A further 0.5-pip round-trip haircut reduces full PF to
  `1.194`.
- The M15 sleeve supplies
  `91.1%` of all
  trades. Its H4 overlay merely changes the same trade from 0.01 to 0.02 lots;
  it is conditional leverage, not an independent expert.

The MT5 timestamps resolve to UTC: zero hours is the unique minimum-error
alignment for both sleeves against the independent Dukascopy bid/ask M5 cache.

## Causal Neutral / Regime 1 slice

Routing every entry through the exact completed-hour cross-asset classifier used
by the hindsight oracle leaves `116` Neutral trades:

| Scenario | Trades | Win rate | Payoff | PF | Net | Ex-best-5% PF |
|---|---:|---:|---:|---:|---:|---:|
| Historical sizing | 116 | 58.62% | 1.022 | 1.448 | $26.46 | 1.125 |
| Every trade 0.01 lot + 0.5 pip | 116 | 58.62% | 0.890 | 1.261 | $14.19 | 1.002 |

The fixed-size stressed slice remains positive in aggregate, but the
chronological tail does not:

| Slice | Trades | Win rate | Payoff | PF | Net | PF +0.5 pip | Net +0.5 pip |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024 H2 | 26 | 76.92% | 0.700 | 2.332 | $13.16 | 2.129 | $11.61 |
| 2025 | 56 | 57.14% | 1.051 | 1.401 | $13.09 | 1.293 | $9.94 |
| 2026 H1 | 34 | 47.06% | 1.139 | 1.013 | $0.21 | 0.898 | $-1.79 |

## Oracle resemblance

- Neutral fallback trades: `116`; Neutral
  oracle trades in the common window: `600`.
- Exact same-time/same-side matches: `0`.
- Same-side matches within 15 minutes: `0`.
- Fallback long share: `97.41%`; oracle long
  share: `52.83%`.
- Fallback nominal target: `0.80R`; oracle nominal target: `1.50R`.

This is profitable mean reversion in one adaptively selected historical slice,
not imitation of the Regime 1 oracle.

## Drawdown and provenance limits

The individual MT5 reports show maximum equity drawdown of
`$39.39` for the M15
sleeve and `$14.82`
for the control. A synchronized reconstruction over the 695 trades covered by
the independent Dukascopy window gives a conservative M5 floating-drawdown
proxy of
`$30.81`. The earlier
`$28.45` figure is closed-trade drawdown only. The proxy uses each M5 bid low
for longs and ask high for shorts, and can sum extremes that did not occur on
the same tick. It is therefore deliberately adverse, not an exact broker
tick-equity result.

The claimed `58` cross-sleeve overlaps are reproduced exactly. Of these,
`7` share the exact entry time and
`21` enter within 15
minutes; all `58` are opposing
long/short positions. Maximum exact-interval concurrency is
`2`. The two separate
tester reports do not establish whether the intended demo account nets or
hedges those positions.

The M15 source/report hashes match the prior verdict and its compile log says
zero errors and warnings. The control hashes were omitted from that verdict,
no control compile log binds source to EX5, and its report was produced with
ordering enabled plus 1:50 leverage rather than the archived shadow preset
plus 1:100 tester configuration. This blocks bit-for-bit shadow parity.

## Decision

Do not promote this fallback as the Neutral expert. Retain it as a diagnostic
entry hypothesis. Any next test must remove the frequency quota, use fixed
0.01-lot sizing, preserve the causal Neutral gate, target the owner's `1.5R`
payoff directly, and be frozen before its outcome is opened. All archived
history remains development data; only a new prospective shadow period can
provide genuinely untouched confirmation.
