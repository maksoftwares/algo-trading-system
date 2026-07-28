# EURUSD Neutral consensus event-confirmation verdict

## Verdict

`REJECTED_NEUTRAL_CONSENSUS_EVENT_CONFIRMATION_V1`

The low-frequency event-confirmed rule passed its outcome-blind census, kept
the intended payoff shape, and resembled the hindsight oracle's same-day
direction. It did not produce stable profitability. The exact rule is closed
without selecting its SHORT, NFP, 2023, or 2024 slices.

No demo or live action is authorized.

## Outcome-blind census

Of 220 directional CPI, PPI, and NFP surprises, 69 occurred on UTC dates
already classified Neutral at 00:00. Forty-nine had a completed 15-minute
EURUSD reaction agreeing with the surprise side.

| Window | Confirmed candidates |
|---|---:|
| 2019-2022 development | 27 |
| 2023 | 9 |
| 2024 | 4 |
| 2025 | 6 |
| 2026 H1 | 3 |
| Total | 49 |

The 49 candidates occurred on 49 distinct dates and comprised 26 LONG, 23
SHORT, 12 CPI, 19 PPI, and 18 NFP signals. All frozen capacity gates passed.
All 49 executed; none overlapped an open position.

## Full-history result

| Trades | Win rate | Realized payoff | PF | Net | Fixed 0.01 lot |
|---:|---:|---:|---:|---:|---:|
| 49 | 36.73% | 1.522 | 0.884 | -3.38R | -$5.07 |

The payoff exceeded the requested 1.5 area, but the win rate did not. At a
1.522 payoff, break-even requires approximately 39.65% wins. The result was
2.92 percentage points short.

## Chronological result

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2019-2022 development | 27 | 33.33% | 1.532 | 0.766 | -3.73R |
| 2023 | 9 | 55.56% | 1.483 | 1.854 | +3.44R |
| 2024 | 4 | 50.00% | 1.483 | 1.483 | +0.97R |
| 2025 | 6 | 16.67% | 1.483 | 0.297 | -3.54R |
| 2026 H1 | 3 | 33.33% | 1.483 | 0.742 | -0.52R |

The combined 2023-2026 forward block was marginally positive at 22 trades,
40.91% wins, PF 1.027, and +0.35R. That aggregate hides a complete regime
break: 2023 and 2024 passed, while 2025 and 2026 H1 failed. It is not robust
enough for activation.

## Requested last six months

| Date | Release | Side | Confirming 15m reaction | Result |
|---|---|---|---:|---:|
| 2026-01-09 | NFP | LONG | +12.40 pips | -1.007R |
| 2026-02-27 | PPI | SHORT | -7.85 pips | -1.007R |
| 2026-06-05 | NFP | SHORT | -28.15 pips | +1.493R |

The three-trade January-June result was PF 0.742, -0.52R, and -$0.78 at fixed
0.01 lot. The additional 0.5-pip round-trip stress reduced it to -0.62R.
This is low frequency, as permitted, but it is not profitable and the sample
is too small to support demo promotion.

## Robustness and oracle relationship

- Extra-0.5-pip full-history PF: 0.833; net -5.01R.
- Best-5%-of-winners removed PF: 0.729; net -7.86R.
- Maximum drawdown: 8.94R.
- Same-day, same-side oracle precision: 63.27% (31 of 49), passing its gate.
- Exact and 15-minute clock matches: zero, because event entries occur hours
  after the oracle's fixed first-hour clocks.

Same-day resemblance alone did not create economic edge. Both LONG and SHORT
sample sizes passed, but LONG lost at PF 0.774 and SHORT was only approximately
flat at PF 1.014. NFP was similarly near flat at PF 1.038. Selecting those
slices now would be post-outcome overfitting.

## Interpretation

Waiting for price to confirm the macro surprise improved the consensus
research path from the 4-pip midnight carry's PF 0.755 to PF 0.884 and raised
realized payoff to 1.522. The remaining issue is instability, especially the
2025-2026 deterioration, not insufficient trade frequency.

The historical consensus field was retrieved after its events. Even a
profitable result would still have required prospectively captured,
pre-release forecasts and a new untouched sample.

## Integrity

- Census SHA-256:
  `c1cc5edf596cd93a2581b3d1f2e02235c292363f59028aed87219d4cb9821ad1`
- Candidate manifest SHA-256:
  `aeeee70e80c2fae07a2e6d5acdc81ce5acf7a07b385c4a439eaf9e6638f9f82e`
- Result SHA-256:
  `2b605f1cae0e5c86896ecf767ab721ae3c389351acbae88fcd8817fef4277846`
- Trade ledger SHA-256:
  `ddf4e7b8b09fec9bdea5ee0f8e68e9a9e2782bd073808dcd0dd44d1a94417c90`
- Oracle-match artifact SHA-256:
  `00176eb9d0058c1325252487bf441380812da093417bb8af9882bae25dcab789`
