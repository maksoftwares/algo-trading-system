# EURUSD Neutral selective multivenue-agreement verdict

## Verdict

`REJECTED_NEUTRAL_SELECTIVE_MULTIVENUE_AGREEMENT_V1`

Allowing the strategy to stay in cash reduced frequency from four forced
trades per source-complete Neutral date to 2.077 trades per date. It did not
create a profitable edge. The frozen agreement rule lost in the development
period and every chronological validation period, including the last six
months.

This exact rule is closed without a magnitude threshold, clock filter, venue
weight, side reversal, or subgroup repair.

## Frozen rule tested

- Kraken EUR/USD and Binance EURUSDT each contributed their normalized
  executed-flow imbalance over the three completed M5 bars immediately before
  each 00:00, 00:15, 00:30, or 00:45 UTC decision.
- Both nonnegative: LONG.
- Both negative: SHORT.
- Disagreement: CASH.
- No model, fit, magnitude threshold, daily quota, or clock selection.
- The existing 4-pip stop, 6-pip target, spread floor, slippage, stop-first
  same-bar rule, and 12-hour hold limit remained unchanged.

The rule, census, execution, gates, code, and tests were hash-locked before
the subgroup's P&L or oracle matches were exposed.

## Outcome-blind frequency

| Window | Source days | Trades | Traded days | Cash-only days | Trades/source day |
|---|---:|---:|---:|---:|---:|
| 2020-2021 development | 133 | 294 | 126 | 7 | 2.211 |
| 2022-2023 validation | 140 | 298 | 133 | 7 | 2.129 |
| 2024 validation | 62 | 114 | 52 | 10 | 1.839 |
| 2025 pseudo-OOS | 79 | 167 | 73 | 6 | 2.114 |
| 2026 H1 pseudo-OOS | 39 | 68 | 35 | 4 | 1.744 |
| Overall | 453 | 941 | 419 | 34 | 2.077 |

## Backtest

| Window | Trades | Win rate | Payoff | PF | Net R | Conditional side accuracy |
|---|---:|---:|---:|---:|---:|---:|
| 2020-2021 development | 294 | 31.63% | 1.439 | 0.666 | -68.85 | 51.96% |
| 2022-2023 validation | 298 | 31.88% | 1.438 | 0.673 | -68.10 | 48.72% |
| 2024 validation | 114 | 35.09% | 1.439 | 0.778 | -16.85 | 51.28% |
| 2025 pseudo-OOS | 167 | 32.93% | 1.439 | 0.707 | -33.68 | 52.38% |
| 2026 H1 / last six months | 68 | 20.59% | 1.438 | 0.373 | -34.75 | 42.42% |
| Overall | 941 | 31.56% | 1.439 | 0.663 | -222.23 | 50.34% |

Every ticket-level and daily portfolio window was below break-even. Overall
daily portfolio PF was 0.535 with -55.56 portfolio R and 57.00 portfolio R
maximum drawdown.

## Robustness and oracle resemblance

| Check | Result |
|---|---:|
| Extra 0.5-pip round-trip PF | 0.541 |
| Extra 0.5-pip round-trip net | -339.85R |
| Best 5% of winners removed PF | 0.556 |
| Best 5% of winners removed net | -293.03R |
| Exact oracle precision | 18.70% |
| Same-side 15-minute precision | 42.30% |

Only the tolerant oracle-precision gate passed. Frequency was deliberately
not an admission gate. The strategy failed every economic window, overall
PF, stress, winner-removal, drawdown, exact-oracle, and recent-six-month
gate.

## Interpretation

The earlier four-trades-per-day constraint was not the cause of the loss.
Agreement retained roughly half the parent decisions, but the chosen side
was correct only 50.34% of the time when one side was available. The 31.56%
realized win rate remained far below the roughly 41% break-even rate implied
by the 1.439 realized payoff.

The sharp deterioration in 2026 H1 also rules out demo promotion. A
historical pass would have required six months and 200 new post-lock
observations anyway; this historical failure cancels that path with zero
post-lock observations.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_selective_multivenue_agreement.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_selective_multivenue_agreement.py backtest
```

Deterministic result artifact:

- `outputs/neutral_selective_multivenue_agreement/RESULT.json`
- SHA-256:
  `a1e741e59d012cbd53155ebad42ba2ca61c3e95cd6926b0c1429fe208d9fa5e4`
