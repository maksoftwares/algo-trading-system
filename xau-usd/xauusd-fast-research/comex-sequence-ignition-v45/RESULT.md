# COMEX Sequence-Ignition V45 Result

## Decision

`V45_DEVELOPMENT_FAIL_TERMINAL`

V45 is permanently rejected. Validation and exam remain sealed. No threshold,
direction, hold, stop, target, or cost repair is authorized.

## Outcome-Blind Calibration

- Eligible weekdays: 20.
- Policies: exactly 1,000.
- Selected policy: `TC30__RL05__TS70__IM35__AC125`.
- Signals: 58, or 2.90/day.
- Active-day share: 95%.
- Direction: 29 long and 29 short.
- Economic outcomes opened: false.
- Calibration payload SHA-256:
  `a6b189f8b92d7c9fb720b9e7a5175cac58c59bf63ac7ffb8e5ae2a56aed74105`.
- Contract SHA-256:
  `3e950672a46401187d2bcddbc2634c53bd862a420c15b2c8c19c59a26cec019b`.

## Development

- Eligible full weekdays: 491.
- Resolved trades: 1,939.
- Frequency: 3.9491/day, above the locked 3.38697/day ceiling.
- Direction: 984 long and 955 short.
- Base net: `-$1,231.11`; stress net: `-$1,373.04`.
- Base PF: `0.4599`; stress PF: `0.4224`.
- Mean stress P/L: `-$0.7081/trade`.
- Profitable days: 18.33%; positive months: 0%.
- First-half/second-half stress PF: `0.4431/0.4021`.
- Top-five-winners-removed stress net: `-$1,410.19`.
- Closed stress drawdown: `$1,373.04` versus the `$250` maximum.
- Bootstrap p-value: `1.0`.

The ordered-event mechanism did not add positive evidence beyond static flow.
The development candidate and label rows may be used as disclosed training data
for a separately preregistered research ranker, but not as execution authority.
