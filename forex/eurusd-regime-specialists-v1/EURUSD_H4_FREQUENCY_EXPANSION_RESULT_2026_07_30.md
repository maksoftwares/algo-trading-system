# EURUSD H4 frequency expansion verdict

## Decision

Use the frozen **M15 first-break execution sleeve** as the higher-frequency
historical candidate. It increased the protected two-regime portfolio from 507
to 672 trades, a **32.54% gain**, while passing every predeclared edge-preservation
gate.

This is a post-selection historical result. It requires fresh confirmation and
does not authorize demo or live broker trading.

## Protected portfolio versus selected frequency sleeve

| Metric | Protected H60 | Selected M15 |
|---|---:|---:|
| Trades | 507 | 672 |
| Trades per weekday represented in data | 0.205 | 0.271 |
| Active trade dates | 496 | 652 |
| Trades per active trade date | 1.022 | 1.031 |
| Win rate | 47.93% | 45.68% |
| Realized payoff | 1.309 | 1.415 |
| Profit factor | 1.210 | 1.190 |
| Net R | +42.940R | +53.302R |
| Research-lot P&L | +$77.74 | +$105.21 |
| Maximum closed-trade drawdown | 11.373R | 11.679R |
| PF after removing best 5% of winners | 1.051 | 1.039 |

The added frequency did not come from loosening the trade economics. The M15
sleeve keeps the original regime ownership, 00:00-05:59 UTC reference range,
06:00-09:59 decision window, short direction, regime-specific body thresholds,
1.75 ATR stop, 1.25R target, 12-hour hold, bid/ask execution, and causal
information timing. It changes only the signal-resolution clock and still
allows at most the first qualifying break per regime and date.

Over the 9.5-year audit this is about 70.7 trades per year, or 5.9 per calendar
month. It is a material improvement over the anchor, but it is not a
four-trades-per-day system.

## Edge-preservation evidence

| Check | Selected M15 result |
|---|---:|
| +0.5 pip round-trip cost PF | 1.135 |
| +1.0 pip round-trip cost PF | 1.083 |
| Five-minute delay PF | 1.182 |
| Fifteen-minute delay PF | 1.167 |
| Trade-block bootstrap PF 5th percentile | 1.049 |
| Trade-block probability PF <= 1 | 1.20% |
| Calendar-block bootstrap PF 5th percentile | 1.082 |
| Latest 12-month PF | 1.597 |
| Latest six-month PF | 1.994 |
| Latest six-month net | +8.530R / +$15.51 |

All four frozen chronological blocks were profitable. Their profit factors were
1.102, 1.214, 1.100, and 1.467 from earliest to most recent.

## What did not work

| Frozen approach | Best frequency gain | Why it was not retained |
|---|---:|---|
| Later-session transfers | Additional candidates | Full-history PF below 1 |
| Unused H4 regimes | Additional candidates | Frozen bundles failed edge gates |
| Body-filter relaxation | 16.17% | Missed 20% gain and a chronology block failed |
| Same-day re-entry | 8.68% | Missed 20% gain and failed robustness gates |
| M30 first break | 16.77% | Preserved edge but missed the frozen 20% gain |
| M15 first break | 32.54% | Passed every frozen gate; selected |

## Interpretation

The useful change was earlier detection of the same regime-owned setup, not
forcing additional sessions, weak regimes, looser candles, or repeated entries.
The portfolio remains low frequency in absolute terms, but it now makes about
one-third more trades without losing its historical robustness profile.
