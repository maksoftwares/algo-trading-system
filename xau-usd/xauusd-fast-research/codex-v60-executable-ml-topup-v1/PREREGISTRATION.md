# V60 Executable ML Top-Up V1 Preregistration

Locked before the source-aware feature matrix or any V1 model result was
calculated.

## Status Of The Evidence

The architecture was chosen after earlier V60 outcomes were visible. Therefore,
this is historical development evidence, not a new holdout. A complete pass may
nominate a fail-closed prospective demo-shadow candidate only. It cannot
authorize ML-influenced orders.

## Question

Can ML improve executable V60 allocation when it:

1. leaves every accepted baseline trade at `0.01` lots;
2. proposes a `0.01` top-up only when separate expected-P&L and win-probability
   models both support the trade;
3. learns only from trades whose historical initial risk is known;
4. uses source identity and market state available before entry; and
5. remains subordinate to all existing deterministic risk limits?

This directly addresses the earlier failure. Skipping weak-ranked trades removed
positive expectancy, while continuous fractional sizing could not be expressed
from a `0.01`-lot base.

## Population And Features

The current nine-source V60 population is reconstructed from the frozen
fee-stressed ledger. R5 is excluded and the V57 120-minute same-direction
post-loss cooldown is replayed causally.

M5 cache timestamps are bar-open timestamps. Every market feature must use:

```text
bar_open_timestamp + 5 minutes <= trade_entry_timestamp
```

The model receives:

- the previously audited 16 market features;
- `is_long` and `is_core`; and
- one-hot execution-source identity.

No entry or exit outcome, future bar, future regime, P&L, holding time, trade
risk, active portfolio state, or later observation may be a feature.

## Frozen Model

For each target entry year from 2021 through 2026:

- train only rows with known historical initial risk;
- require `exit_time < target_year_start - 48 hours`;
- fit a bagged shallow histogram gradient-boosted regressor to fee-stressed USD
  P&L winsorized at the training 1st and 99th percentiles;
- fit a separately bagged shallow histogram gradient-boosted classifier to
  `fee_stress_pnl_usd > 0`;
- use 40 bootstrap bags and primary ensemble seed `0`;
- use seeds 1 through 4 only as sensitivity diagnostics;
- causally rank each component against prior out-of-sample scores after 100
  observations, and against that year's training prediction distribution
  before 100 observations;
- form `joint_score = 0.5 * expected_pnl_rank + 0.5 * win_probability_rank`.

A top-up is proposed only when:

```text
expected_pnl_rank > 0.50
win_probability_rank > 0.50
joint_score > 0.80
```

The primary model includes source identity. Three locked diagnostics may not
replace it: expected-P&L rank alone, win-probability rank alone, and a
market-only dual model.

## Broker Policy

- Every baseline trade remains `0.01` lots.
- A proposed top-up changes the trade to `0.02` lots only when initial risk is
  known and all current source, account, directional, add-on, and concurrent
  limits remain satisfied.
- Missing risk, an unknown source limit, or an active unknown-risk position
  rejects the top-up.
- No trade may be skipped or reduced.
- No lot other than `0.01` or `0.02` is permitted.

## Required Gates

Every gate must pass:

1. No incomplete M5 bar reaches any feature.
2. No missing-risk trade is used for training or receives a top-up.
3. Full-period net P&L and profit factor are no worse than deterministic V60.
4. Full floating-equity drawdown is no worse than V60.
5. Net/floating-drawdown improves by at least 5%.
6. Green-month share is no more than two percentage points below V60.
7. At least five of six entry years have nonnegative P&L improvement.
8. A four-week moving-block bootstrap has a one-sided 95% lower P&L-delta bound
   above zero.
9. For 2025-07-01 through 2026-06-30, net P&L, profit factor, and closed-trade
   drawdown are each no worse than V60.
10. At least four of the five frozen seeds have nonnegative P&L improvement.
11. All top-ups and concurrent historical paths respect the frozen risk limits.

The current-account floating stop is not used as a full-history gate because
deterministic V60 itself exceeds that dollar stop on the historical record.
Any future broker-action candidate must separately simulate halt and restart
behavior at the intended activation equity.

## Decision

A failed gate quarantines V1 and leaves deterministic V60 unchanged. A complete
historical pass permits preparation of prospective shadow plumbing only; it
does not activate that plumbing and does not authorize broker action.
