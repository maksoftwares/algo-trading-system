# EURUSD Neutral H4 quiet-state transfer result

Status: `REJECTED_EXACT_H4_CONTROLS_NO_HISTORICAL_QUALIFIER`

The two previously promising H4 controls were replayed unchanged on 747,645
EURUSD M5 bid/ask bars. The audit covered January 2017 through June 2026,
charged a 0.7-pip retail spread floor and 0.1-pip adverse slippage per side,
and used complete M5 paths with stop-first ambiguity.

## Full-history result

| Specialist | Trades | Win rate | Payoff | PF | Stressed PF | Net R | Max DD | Ex-best-5% PF | Positive months |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H4 chop Asia/London short | 349 | 50.14% | 1.186 | 1.200 | 1.145 | +32.28 | 12.39R | 1.061 | 54.37% |
| H4 compression Asia/London short | 158 | 43.04% | 1.650 | 1.247 | 1.189 | +21.33 | 10.39R | 1.062 | 49.32% |

Both rules made money across the complete audit. Neither passed the frozen
quality standard.

The chop control reached the requested win-rate neighborhood and was positive
in every chronological block, but its 1.186 realized payoff, 1.200 PF, 1.145
stressed PF, and 54.37% positive-month share all missed their gates. Its strong
recent period cannot replace the weaker full history.

The compression control preserved a 1.650 payoff and 1.189 stressed PF, but
its win rate was only 43.04%, full PF was 1.247, and the 2022H2-2024H1 block
lost money at PF 0.931. Its latest twelve months were almost flat at PF 1.007,
and the latest six months fell to PF 0.837.

## Chronology

| Window | Chop trades | Chop PF | Compression trades | Compression PF |
|---|---:|---:|---:|---:|
| 2017-2019 | 102 | 1.313 | 60 | 1.483 |
| 2020-2022H1 | 105 | 1.099 | 39 | 1.218 |
| 2022H2-2024H1 | 82 | 1.053 | 29 | 0.931 |
| 2024H2-2026H1 | 60 | 1.457 | 30 | 1.160 |
| Latest 12 months | 27 | 1.985 | 25 | 1.007 |
| Latest 6 months | 15 | 1.483 | 8 | 0.837 |

## Decision

These are useful positive controls, but they are not the robust PF 1.30+
Regime-1 specialist requested by the owner. They remain research inputs only.
No year, side, target, regime threshold, or recent window is selected after
outcome inspection, and the two failures are not combined to hide their
standalone shortfalls.

No broker, account, terminal, demo, or live action occurred.
