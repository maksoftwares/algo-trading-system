# EURUSD frozen daily learner: historical diagnostic

## Verdict

The frozen forward daily learner is **rejected as the frequency-completion
sleeve**. It remains a disarmed prospective experiment, but its exact causal
historical replay does not support either the required frequency or a positive
edge. It must not be tuned from this result or admitted to demo ordering.

## Exact replay result

The unchanged forward engine was initialized with zero weights and replayed
chronologically over hash-verified EURUSD, EURGBP, EURJPY, GBPUSD, and USDJPY
M5 bid/ask bars from 2016-07-01 through 2026-06-30.

| Metric | Result |
|---|---:|
| Validation weekdays after the 20-day warmup | 2,571 |
| Qualified trades | 34 |
| Trades per validation weekday | 0.0132 |
| Win rate | 38.24% |
| Payoff ratio | 1.469 |
| Profit factor | 0.909 |
| PF after +0.5-pip stress | 0.821 |
| Net result | -1.925R |
| Net at 0.01 lot | -$1.54 |
| Latest 12 months | 0 trades |

The weak result is not caused only by the admission threshold. Forcing the
learner's preferred side to trade on every post-warmup weekday produced 2,571
trades, PF 0.912, and -140.66R. Taking the opposite side every day produced PF
0.942 and -92.24R. More trades therefore expose a negative raw signal rather
than recover hidden edge.

## Frequency gap

The broker-transferred M15 chop-plus-compression first-break expert contributes
0.2031 trades per weekday. Adding the daily learner's historical 0.0132 rate
projects only **0.2163 trades per weekday before overlap and risk caps**.

| Target | Still missing |
|---|---:|
| Minimum combined admission frequency, 0.85/day | 0.6337/day |
| Desired operating point, 1.00/day | 0.7837/day |

The current protected expert supplies real historical edge, but not enough
opportunities. The missing component must therefore be one or more genuinely
independent regime specialists; relaxing this daily learner would add losses.

## Interpretation boundary

- This is a retrospective falsification diagnostic, not forward evidence.
- No learner threshold or parameter was changed.
- The source bars contain bid/ask OHLC but not intrabar tick-mean spread. The
  adapter uses the mean of the bar-open and bar-close spread for that feature;
  outcomes use native bid/ask highs and lows.
- The live combined validator remains disarmed and requires its frozen forward
  admission gates, execution parity, and soak before any demo order is allowed.

## Reproducibility

- `outputs/forward_learner_history_diagnostic/RESULT.json` SHA-256:
  `d908649d627b52262e7506adea004dd9e00fa845a82bea55de46c9a603aab36a`
- `outputs/forward_learner_history_diagnostic/RESULT.md` SHA-256:
  `f95e6078bda13b7c8daeb2471b0673701b713a5f1f8295ecd6a738160715b532`
- Focused forward/M15/diagnostic test suite: 36 passed.
