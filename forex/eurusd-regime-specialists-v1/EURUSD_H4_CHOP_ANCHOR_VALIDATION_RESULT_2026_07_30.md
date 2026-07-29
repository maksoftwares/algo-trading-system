# EURUSD H4 chop anchor validation result

Status: **POSITIVE_HISTORICAL_ANCHOR_NOT_STATISTICALLY_VALIDATED**

This is a retrospective causal validation, not a pristine out-of-sample test and not permission to trade a broker account.

## Unchanged full-history anchor

- Trades: 349
- Win rate: 50.14%
- Realized payoff: 1.186
- Profit factor: 1.200
- Net: 32.275R
- Maximum closed-trade drawdown: 12.385R
- PF after removing the best 5% of winners: 1.061

## Recent periods

- Latest 12 months: 27 trades, PF 1.985, +8.973R
- Latest 6 months: 15 trades, PF 1.483, +2.929R

## Execution degradation

- +0.5 pip round trip: PF 1.145
- +1.0 pip round trip: PF 1.094
- 5-minute delayed entry: PF 1.143
- 15-minute delayed entry: PF 1.161
- 0.5 pip per 21:00 UTC rollover crossing: PF 1.198

## Sampling uncertainty

- Five-trade circular block bootstrap PF 5th percentile: 0.998
- Mean R/trade 5th percentile: -0.0011
- Estimated probability PF <= 1: 5.22%

Failed frozen gates: bootstrap_base_pf_5pct, bootstrap_base_mean_r_5pct, bootstrap_probability_pf_lte_1.

The historical PnL is real within this replay. Validation status depends on the frozen robustness and uncertainty gates; no failed gate is hidden or retuned.
