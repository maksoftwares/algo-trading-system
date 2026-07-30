# EURUSD forward residual-regime protocol

## Purpose

This campaign tests whether a separate EURUSD specialist can add profitable
coverage on weekdays left unused by the protected M15 portfolio and the frozen
daily learner. It is forward-only research. It cannot place demo or live
orders.

The implementation and rules were frozen before the evidence floor
`2026.08.01 00:00:00` UTC, while the prospective feature ledger contained zero
post-floor rows and the residual decision ledger contained zero decisions.
Pre-floor and historical rows are prohibited.

## Residual ownership

At most one decision is evaluated per UTC weekday, at `20:00:00` UTC. A date is
owned by this specialist only when:

- the frozen M15 forward signal ledger has no signal on that UTC date; and
- the frozen daily learner has no eligible `LONG` or `SHORT` decision on that
  UTC date.

A missing or invalid upstream ledger causes a fail-closed cash result. An
upstream-owned date is recorded but is not added to the residual specialist's
training history.

## Causal information and regimes

Only observations available by the decision clock are used. EURUSD returns are
excluded from the direction features. The cross-pair inputs are EURGBP,
EURJPY, GBPUSD, and USDJPY, with USDJPY sign-inverted to maintain a common
EUR-strength orientation.

Every complete residual day belongs to exactly one ordered regime:

1. `CROSSPAIR_COMPRESSION`
2. `BROAD_EUR_UP`
3. `BROAD_EUR_DOWN`
4. `SHORT_LONG_DISAGREEMENT`
5. `MIXED_TRANSITION`

The thresholds, ordering, clock, stop, target, costs, and maximum hold are
frozen in the campaign configuration. They may not be tuned after prospective
evidence begins.

## Online specialist

Both long and short outcomes are observed after the full six-hour outcome path
is available. A side can use only prior, fully resolved residual days from the
same regime. Cross-regime borrowing is prohibited.

The first 20 resolved residual days are global warm-up. A regime-side then
needs at least 10 prior observations and must independently pass the frozen
shrunk-expectancy, raw profit-factor, stressed profit-factor, and recent
profit-factor gates. Failure means cash.

Outcomes assume:

- 8-pip stop;
- 12-pip target;
- 0.1-pip entry and 0.1-pip exit slippage;
- stop-first resolution for same-bar collisions; and
- six-hour maximum hold.

## Admission boundary

The specialist remains research-only until all frozen checks pass:

- at least 160 complete prospective weekdays;
- at least 80 resolved residual decisions;
- at least 50 eligible trades;
- at least 20% incremental weekday coverage;
- PF at least 1.15 and payoff ratio at least 1.25;
- PF at least 1.05 after 0.5-pip extra round-trip stress;
- PF at least 1.00 after removing the best 5% of trades;
- both chronological trade halves have PF strictly above 1.00;
- no single month supplies more than 50% of gross positive monthly R;
- the combined protected-plus-residual portfolio passes the frozen frequency
  and coverage gates;
- MT5 signal/outcome parity passes; and
- the required disarmed demo-shadow soak passes.

No standalone result can authorize orders. Promotion requires a separately
reviewed successor portfolio contract. The frozen campaign itself always
reports `demo_order_authorized=false`.

## Prohibitions

No retrospective backtest, threshold search, side reversal, clock search,
stop/target search, historical-row import, missing-data imputation, duplicate
upstream opportunity, or order path is allowed.
