# EURUSD Neutral symmetric RSI 1.5R verdict

Date: `2026-07-28`

Status: `REJECTED_NEUTRAL_SYMMETRIC_RSI_1P5R_V1 / NO RETUNE`

## Frozen question

The prior adaptive-frequency fallback showed a profitable but fragile Neutral
slice with the wrong payoff shape and almost entirely long exposure. This
single locked test removed its post-selection machinery:

- causal `NEUTRAL` state only;
- symmetric completed-M15 RSI extremes;
- no blocked hours, body filter, calendar mask, or H4 size overlay;
- one position, no frequency quota;
- 1.4 ATR / six-bar structural stop;
- 1.50R target and 12-hour maximum hold;
- executable bid/ask, 0.7-pip minimum spread, and 0.1-pip slippage per side.

The rule, source, costs, windows, gates, and hashes were committed before the
census or P&L was opened.

## Outcome-blind census

The census passed, so the one frozen backtest was allowed:

| Census | Long | Short | Total |
|---|---:|---:|---:|
| Causal Neutral signals | 1,933 | 1,987 | 3,920 |

Every chronological block exceeded its fixed sample floor. Capacity was not the
problem.

## Backtest

The one-position router executed 1,433 trades. It skipped 2,486 signals while
a prior position remained open and one trade whose stop exceeded 70 pips.

| Slice | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| 2019-2022 development | 788 | 39.97% | 1.410 | 0.939 | -28.23 |
| 2023 chronological | 201 | 31.34% | 1.493 | 0.681 | -42.37 |
| 2024 chronological | 149 | 33.56% | 1.426 | 0.720 | -27.20 |
| 2025 chronological | 197 | 37.56% | 1.422 | 0.855 | -17.84 |
| 2026 H1 recent | 98 | 41.84% | 1.428 | 1.027 | +1.52 |
| **Overall** | **1,433** | **37.89%** | **1.424** | **0.869** | **-114.11** |

At fixed 0.01 lot, the full ledger loses `$96.33`. The apparent recent
`+1.52R` is also negative at fixed 0.01 lot (`-$2.75`) because its larger-risk
losers carry more dollar weight.

## 2026 H1 stress

The only marginally positive R block does not survive basic robustness:

| 2026 H1 | PF | Net R | Ex-best-5% PF |
|---|---:|---:|---:|
| Native cost | 1.027 | +1.52 | 0.895 |
| Extra 0.5-pip round trip | 0.928 | -4.30 | 0.807 |

Only three of six months are positive in R terms. January and March lose
`-5.79R` and `-4.59R`; June supplies `+6.86R`. The frozen decision policy
forbids using 2026 as a post-outcome activation window.

## Direction and oracle audit

| Side | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| Long | 713 | 40.67% | 1.415 | 0.970 | -12.29 |
| Short | 720 | 35.14% | 1.434 | 0.777 | -101.82 |

Deleting shorts would be post-outcome selection and is explicitly prohibited.

The strategy matches only 20 oracle trades exactly and 29 within 15 minutes:
1.40% exact precision, 0.76% exact recall, 2.02% tolerant precision, and 1.11%
tolerant recall. It does not approximate the Neutral oracle's entries closely.

## Robustness

- Best 5% removed: PF `0.745`, net `-221.71R`.
- Extra 0.5 pip: PF `0.785`, net `-198.65R`.
- Maximum closed drawdown: `129.87R`.
- Exit counts: 846 stops, 485 targets, and 102 time exits.
- Failed gates: win rate, overall PF, every-window profitability, both-side
  profitability, drawdown, winner removal, cost stress, oracle precision, and
  oracle recall.
- Passed gates: sample size and realized payoff shape.

## Decision

The entry hypothesis does not provide the missing directional edge. Widening
the target successfully produces a 1.424 payoff, but win rate remains far below
the requested approximately 50%, leaving PF below one. The exact symmetric
rule is closed without threshold, side, hour, stop, hold, or RR changes.

Regime 1 remains `CASH`. The next valid confirmation path is a newly arriving,
prospectively locked shadow period for a previously frozen candidate or a
materially new decision-time information source—not another transformation of
the same archived RSI/bar features.

Result SHA256:
`2e3ea98d1f66daba53abcfe898e4ae9513c3d722c59de1f32289af20103c07d1`.
