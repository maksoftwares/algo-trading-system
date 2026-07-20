# Macro-Informed Bidirectional Router V36 Preregistration

This contract is locked before calculating V36 model scores, policy economics,
or any V36 survivor decision. Prior V1 outcomes are already known, so every
historical block remains contaminated diagnostic evidence.

## Single fixed hypothesis

The V1 candidate stream had sufficient event density but failed to choose a
profitable direction in the final block. V36 tests one structural hypothesis:
causal dollar-index and Treasury total-return pressure contains incremental
information for choosing among the already frozen long/short actions.

No candidate trigger, label, exit, cost, target, stop, model hyperparameter,
fit/calibration boundary, policy, gate, Core trade, or risk weight may change.

## Fixed features

The 81 V1 router features remain unchanged. Following the input-only amendment
recorded in `PRE_OUTCOME_AMENDMENT.md`, V36 adds exactly:

- eight raw pressure features: DXY and Treasury across H1 and H4 returns,
  standardized by trailing D2 and D10 volatility;
- eight route-aligned pressure features, each raw pressure multiplied by the
  candidate action direction (`LONG=+1`, `SHORT=-1`);
- one macro feature-age field in minutes.

DXY pressure is the negative standardized DXY return. Bond pressure is the
positive standardized Treasury total-return return. A trailing volatility scale
is shifted by one return before rolling, so the current return cannot alter its
own denominator. Returns require exact contiguous M15 timestamps.

Macro bars are timestamped at the end of their completed 15-minute bucket. Each
action receives only the latest macro timestamp less than or equal to its signal
time and no older than 15 minutes. All frozen V1 action rows remain in the sample.
Macro fields may be missing when no causal observation or contiguous return is
available because the locked model handles missing values natively; infinity is
prohibited. Labels and economic outcomes are never used by the feature builder.

## Unchanged walk-forward model

- HistGradientBoostingRegressor predicts clipped stress USD for each action.
- Trailing fit lookback: 24 months.
- Fit ends before a separate three-month calibration block.
- Refit interval: three months.
- Recency half-life: 12 months.
- Fit target clip: `[-15, 20]` USD; evaluation uses unclipped stress USD.
- The best action is chosen once per event.
- Its score is converted to an empirical percentile using only the immediately
  preceding calibration block.
- Fit and calibration rows must have exits strictly before their boundaries.
- Unsafe-shock rows are excluded.

## Exactly 1,000 unchanged policies

The Cartesian grid is unchanged from V1:

- score percentiles 0.50 through 0.95 in 0.05 increments;
- daily caps 3, 4, 5, 6, and 8;
- entry separations 0, 5, 15, 30, and 60 minutes;
- maximum active Expansion trades 2 and 3;
- Expansion risk weights 0.25 and 0.50.

`10 * 5 * 5 * 2 * 2 = 1,000`.

Core is never filtered, removed, or resized. Frequency counts every weekday,
including zero-trade weekdays.

## Unchanged blocks and gates

- development: 2021-07 through 2023-06;
- validation: 2023-07 through 2024-06;
- confirmation: 2024-07 through 2025-06;
- final: 2025-07 through 2026-06.

Every policy must pass every block:

- combined frequency from 3.0 through 4.2 trades per weekday;
- Expansion PF at least 1.20;
- combined PF at least 1.50;
- positive Expansion net and average USD;
- at least 50% positive Expansion calendar months;
- positive Expansion and combined P&L after removing ten largest winners;
- combined net no lower than Core;
- combined closed-trade drawdown no more than 125% of Core.

## Decision and authority

Zero all-block survivors rejects this feature hypothesis. Any survivor is only a
historical robustness candidate and must next pass prospective shadow evidence,
MT5 parity, and shared-account floating-equity simulation. No result in this
package authorizes broker action, execution, model serving, EA consumption,
account changes, demo trading, or live trading.
