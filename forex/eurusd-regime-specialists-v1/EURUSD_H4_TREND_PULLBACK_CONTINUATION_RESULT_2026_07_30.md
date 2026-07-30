# EURUSD H4 trend-pullback continuation result

Date: 2026-07-30

Status: **DEVELOPMENT_REJECTED_VALIDATION_UNOPENED**

Demo-order authorization: **false**

## Decision

The frozen later-session H4 trend-pullback hypothesis failed development.
Neither mirrored direction qualified, so locked 2022H2-2026H1 validation
remained unopened and no post-result repair was attempted.

| Expert | Trades | Win rate | Payoff | PF | +0.5 pip PF | Net R |
|---|---:|---:|---:|---:|---:|---:|
| Trend-up EMA rejection long | 86 | 44.19% | 1.348 | 1.067 | 1.014 | +2.73 |
| Trend-down EMA rejection short | 107 | 38.32% | 1.214 | 0.754 | 0.706 | -13.36 |

Trend-up long failed the 100-trade floor, PF, stressed PF, early-block PF, and
winner-removal gates. Its early 2017-2019 PF was 0.995 and best-5%-removed full
PF was 0.883.

Trend-down short met the sample floor but failed every edge gate. Its
2017-2019 PF was 0.635 and 2020-2022H1 PF was 0.995. Best-5%-removed full PF was
0.589.

The hypothesis produced a causal mechanism distinct from the protected
breakout, but not a positive-expectancy one. EMA period, clock, body threshold,
side, stop, target, and hold are retired together for this exact family.

## Capacity implication

At 12:00 UTC in the two-year broker window, the 424 dates left empty by
protected M15 are distributed approximately as follows:

| Available H4 state | Empty weekdays | Share |
|---|---:|---:|
| Chop | 109 | 25.71% |
| Trend up | 83 | 19.58% |
| Compression | 72 | 16.98% |
| Trend down | 71 | 16.75% |
| Transition | 46 | 10.85% |
| Unsafe | 39 | 9.20% |

Trend states offer substantial theoretical capacity, but the frozen pullback
entry did not monetize it. Chop is the largest single remaining state and is
the next distinct-mechanism target.

## Reproducibility

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_h4_trend_pullback_continuation.py
```

Hashes:

- Frozen config:
  `b5a3d9cc11e68475fe66d832dca850887ed6032c8cb575ab639477c7f85498c7`
- Source data:
  `8281d96ccbc3488f98586894fe58f6988eaa5376601a0bfaec874fd9f08f1f45`
- `RESULT.json`:
  `00bb89525c92106d7bec670e7b5baea03c2cf4dc89cfd2a1ffd8b72a7fb2401c`
- `RESULT.md`:
  `15f1f313a3588f0f7a0eb0fe646e2a4fb776951bdb0b958c734e69b362b2a1ab`
- `VALIDATION_TRADES.csv`:
  `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6`

