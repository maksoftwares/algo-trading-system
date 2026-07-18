# Transition Weighted Raw-Tick Confirmation V9

## Purpose

Confirm the exact V8 near-finalist on chronological Dukascopy XAUUSD bid/ask
ticks. No allocation, entry rule, geometry, threshold, or gate may change.

## Frozen portfolio

- Origin portfolio attempt: 25210
- Confirmation attempt: 25238
- Tie priority: attempt ascending
- 23925 macro ancestry reacceleration: 1.00 R
- 24877 residual breakout: 0.25 R
- 24995 single-factor resolution: 0.75 R
- 25048 ancestry overshoot reversal: 0.75 R

The V8 bar screen reported 330 trades, +33.055 R, PF 1.2465, minimum-era PF
1.1335, and 7.1405 R closed drawdown. It missed the unchanged total PF 1.25
gate. This confirmation is justified because the bar simulator uses conservative
stop-first ordering whenever both stop and target occur in one bar. Tick order
can resolve that ambiguity without tuning.

## Candidate and execution rules

Each source signal mask is regenerated from its sealed parent manifest. The
signal must map to the next complete gold M15 bar in the full execution frame.
The candidate file and all source hashes are locked before tick outcomes open.

Longs enter at ask and exit at bid. Shorts enter at bid and exit at ask. Stops
fill at the first observed executable crossing quote, including adverse
slippage. Targets fill at the locked target. Horizon exits use the first quote
at or after the fixed deadline. Each component applies its own original
non-overlap and four-trades-per-day cap before the frozen weighted portfolio
policy is applied.

## Gates and interpretation

The economic gates are unchanged. The historical p-value remains adjusted for
the 96 V8 allocations that exposed this near-finalist. A raw-tick economic pass
would establish a historical transition specialist candidate, not trading
authorization. Independent-period and prospective shadow evidence remain
required.

Same-version repair, paid data, model training, and trading authorization are
prohibited.

