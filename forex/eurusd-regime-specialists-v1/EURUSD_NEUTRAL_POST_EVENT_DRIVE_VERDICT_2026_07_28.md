# EURUSD Neutral post-event drive verdict

## Verdict

`REJECTED_NEUTRAL_POST_EVENT_DRIVE_V1`

The pinned event clock and source remain available, but this exact direct
post-release strategy is closed without event, currency, impulse, risk, or
direction repair.

The rule used only the latest qualifying event on each Neutral UTC date and
three completed M5 bars after that event. Dukascopy actual, forecast, previous,
impact, and other non-point-in-time numeric fields remained prohibited.

## Frozen branch selection

The 2019-2022 development window selected `MOMENTUM`, as preregistered:

| Branch | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| Momentum | 285 | 35.44% | 1.446 | 0.794 | -37.81R |
| Reversal | 285 | 34.39% | 1.434 | 0.751 | -47.49R |

Momentum was the less-bad branch, but both branches lost and development
selection failed its admission gate.

## Chronological forward result

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2023 | 54 | 37.04% | 1.349 | 0.794 | -6.99R |
| 2024 | 55 | 30.91% | 1.314 | 0.588 | -15.90R |
| 2025 | 64 | 34.38% | 1.428 | 0.748 | -10.61R |
| 2026 H1 | 37 | 43.24% | 1.459 | 1.112 | +2.39R |
| Forward total | 210 | 35.71% | 1.388 | 0.771 | -31.11R |

The requested latest six months were profitable and close to the desired
payoff structure. They were not independently selected, however, and the same
locked rule lost in development and in every preceding forward year. The
2026 H1 improvement therefore cannot justify demo trading.

## Robustness and oracle resemblance

- extra-half-pip stress: PF 0.679 and -46.95R;
- best 5% of winners removed: PF 0.650 and -47.55R;
- forward daily portfolio PF: 0.771;
- forward daily portfolio drawdown: 9.63 portfolio R;
- exact oracle matches: 0 of 210;
- same-side 15-minute oracle matches: 0 of 210.

The zero oracle matches are informative. The hindsight oracle was concentrated
at the fixed first-hour scan clocks, while direct event entries occurred at
their causal post-release times. This rule did not approximate the oracle's
entry locations, even when it happened to profit in 2026 H1.

## Interpretation

The structure stop and 1.5R target produced the intended payoff shape, but the
directional edge was insufficient. At a forward payoff of 1.388, break-even
requires about 41.88% wins; the rule achieved only 35.71%. This is a side-
selection deficit of roughly 6.17 percentage points, not a frequency problem.

The rule produced 495 outcome-blind candidates on 642 Neutral dates, including
37 in the latest six months. No four-trades-per-day requirement was applied.
Lower frequency improved the latest block but did not create a stable
multi-year edge.

No post-outcome reversal, event-title subgroup, currency split, impulse
threshold, alternate observation length, risk cutoff, or 2026-only activation
is authorized for this locked family.

## Integrity

Deterministic result:

`outputs/neutral_post_event_drive/RESULT.json`

SHA-256:

`5a20e4cb75dcec0383dab83494d389a30442c431ae55d8b9726a199b84439b24`

Final status remains `RESEARCH_FAILURE_NOT_DEMO_READY`; Regime 1 remains
`CASH`.
