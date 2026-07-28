# EURUSD Neutral capacity-selective post-event verdict

## Verdict

`REJECTED_NEUTRAL_CAPACITY_SELECTIVE_POST_EVENT_V1`

Outcome-blind capacity calibration improved the unconditional post-event rule,
but the exact 0.40 model is closed without threshold, year, feature, event, or
direction repair.

## Chronological result

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2023 | 24 | 37.50% | 1.297 | 0.778 | -3.23R |
| 2024 | 18 | 50.00% | 1.391 | 1.391 | +3.57R |
| 2025 | 24 | 29.17% | 1.302 | 0.536 | -7.99R |
| 2026 H1 | 9 | 44.44% | 1.468 | 1.175 | +0.88R |
| Forward total | 75 | 38.67% | 1.353 | 0.853 | -6.77R |

Both 2024 and the requested latest six months were profitable. Both 2023 and
2025 failed. The overall win rate remained below the roughly 42.50% required
to break even at the realized 1.353 payoff.

The latest six months are close to the user's desired shape—44.44% wins,
1.468 payoff, and PF 1.175—but contain only nine trades. They cannot override
the losses in two independent forward windows.

## Robustness and oracle resemblance

- extra-half-pip stress: PF 0.769 and -11.32R;
- best 5% of winners removed: PF 0.723 and -12.75R;
- forward daily portfolio PF: 0.853;
- forward daily portfolio drawdown: 2.88 portfolio R;
- exact oracle matches: 0 of 75;
- same-side 15-minute oracle matches: 0 of 75.

The model reduced the N29 forward loss from -31.11R to -6.77R and raised PF
from 0.771 to 0.853. Selection helped, but did not create a stable positive
edge or approximate the oracle's fixed-clock entries.

## Integrity

The threshold was selected before P&L as the highest member of the fixed
0.42/0.41/0.40 ladder providing at least eight candidates in each window. The
75-candidate manifest was hash-locked before its outcomes were loaded.

Deterministic result:

`outputs/neutral_capacity_selective_post_event/RESULT.json`

SHA-256:

`64043a6d99629fda0f982b088a1506f714d71fd7a2780b47dd55a6166ab210ae`

Final status remains `RESEARCH_FAILURE_NOT_DEMO_READY`; Regime 1 remains
`CASH`.
