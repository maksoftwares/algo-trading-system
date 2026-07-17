# A3 ML A2 Intraday Context Ranker V1 Preregistration

Date: 2026-07-17

## Objective

Test whether new causal intraday information can rank the exact A2
`breakout_retest` trade population into a profitable, sufficiently frequent
subset. The mechanical A2 source produced 7,007 position-ID-paired trades and
was near break-even before this experiment. ML may rank or abstain; it does not
invent entries or alter the EA's entry, stop, target, or management rules.

The full machine-readable contract is
`config/ml/a3_ml_a2_intraday_context_ranker_v1.json`.

## Source Freeze

The raw MT5 deals, orders, signals, summary, and trades files were copied
byte-for-byte into
`C:/DukascopyTickDataFoundationV1/external/a2-breakout-retest-ranker-v1`.

Source integrity before preregistration:

- 7,007 unique completed positions;
- 7,007 successful entry orders;
- 14,014 deals;
- exactly two deals for every position;
- one-to-one trade/order join;
- positive stop, target, and stop-distance values for every trade.

MT5 did not expose a usable history-quality percentage. This remains a material
limitation and prevents the source from being described as pristine broker
history.

## New Information

Each A2 entry receives features from exactly the M5 bar completed five minutes
before entry. No current or future entry bar is used.

The feature set combines:

1. Verified XAUUSD tick pressure, spread, liquidity, realized volatility, and
   trend/range/shock state.
2. Causal XAGUSD, EURUSD, and USDJPY returns.
3. Newly validated intraday dollar-index and U.S. Treasury-bond price CFD
   proxies.
4. The original A2 spread, risk distance, and estimated-cost context.

No quote is forward-filled and no return may cross a timestamp gap. Dollar and
bond return scales use only prior observations and are lagged one bar.

## Label And Cost Lock

The MT5 source profit already reflects the A2 executable entry and exit path.
For target-broker stress, each trade subtracts:

- any uplift required to move its A2 entry spread to the locked $0.75 floor;
- an additional $0.30 execution cost per 0.01 lot;
- $0.35 per 24 hours held.

Risk is reconstructed from the successful entry order's locked stop distance.
The regression target is stressed net R. Positive-class diagnostics use
`stress_net_r > 0`.

The legacy field name `profit_aed` is not accepted as proof of account currency.
The source P&L numerically matches one-ounce XAU price movement at 0.01 lot, but
currency provenance remains disclosed rather than silently assumed.

## Chronology

| Segment | Window |
|---|---|
| Train | 2019-01-01 through 2020-12-31 |
| Validation | 2021-01-01 through 2021-12-31 |
| Internal test | 2022-01-01 through 2022-12-31 |
| Exam | 2023-01-01 through 2024-06-30 |

Any trade whose exit crosses a segment boundary is excluded from that segment.
The train selection policy uses three expanding, forward OOF folds. Every fit
row's actual exit must precede its fold's evaluation start.

## Model And Selection Lock

V1 uses one shallow histogram gradient-boosting regressor with fixed complexity.
No hyperparameter search is permitted.

Three OOF retention policies are tested: top 75%, 60%, and 45% by predicted
stressed R. Their absolute score cutoffs are frozen from OOF predictions. At
most four source trades may be selected per UTC day.

The winning policy must pass predictive, frequency, cost-stressed PF, average-R,
month-stability, drawdown, direction-balance, winner-removal, and calendar-month
bootstrap gates. It is selected by bootstrap lower bound, then PF, then higher
retention. A later segment opens only after the preceding segment passes.

## Interpretation Boundary

This experiment is materially different from the rejected A2 model because the
prior model had only sparse candle and calendar context. V1 adds validated
intraday macro, cross-market, tick-pressure, spread, and liquidity features.

The history has program-level research contamination and is not called an
untouched holdout. Failure means this feature/model combination is rejected
without changing retention, features, or model complexity in the same
iteration.

Passing all historical gates would authorize exact target-broker and shared-risk
qualification only. It would not directly authorize Python demo predictions,
EA consumption, broker action, or live capital.
