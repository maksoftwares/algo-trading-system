# A3 ML Dukascopy M15 Expansion Ranker Discovery V1 Preregistration

Date: `2026-07-16`

## Purpose

Measure whether the newly built causal tick-liquidity and synchronized cross-market features can rank the frozen M15 range-expansion candidates. This is a development diagnostic, not a strategy promotion campaign.

## Frozen Input

- Candidate and outcome mechanics are hash-bound to the M15 range-expansion contract.
- Features are hash-bound through that contract to the six-year causal feature cache.
- Fit period: `2018-07-01` through `2019-06-30`.
- Development evaluation: `2019-07-01` through `2020-06-30`.
- No outcome on or after `2020-07-01` is authorized or generated.

## Frozen Model And Policies

- Use the one histogram gradient-boosting regressor already frozen in the expansion contract.
- Predict stressed net R.
- Derive cutoffs only from fit-period scores.
- Evaluate top 60%, 45%, 30%, and 20% retention.
- Keep one concurrent XAUUSD trade, at most two trades per UTC day, and a 30-minute cooldown.

## Pass Standard

A diagnostic survivor needs meaningful predictive discrimination plus positive stressed economics, including:

- AUC at least `0.54` or Spearman rank correlation at least `0.05`;
- at least 50 selected trades;
- stressed PF at least `1.10`;
- average stressed result at least `0.03R`;
- at least half of active months positive;
- no more than `15R` closed drawdown;
- positive net after removing the ten largest winners.

Even a pass only justifies a separately preregistered validation campaign. It cannot authorize demo or live trading.

Failure closes this feature/family combination. No post-outcome model, feature, or retention tuning is allowed.
