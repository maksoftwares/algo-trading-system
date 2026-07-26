# V14 Prospective Preregistration

## Purpose

Test whether the historically selected B1+B2+B3 Expected-R filter improves
the exact V60 deterministic portfolio on untouched future candidates without
materially reducing opportunity frequency.

## Boundary

Only candidates scheduled at or after `2026-07-27T03:00:00Z` are eligible.
The model, pooled threshold, source transformations, protocol, and authority
state must be locked before that boundary. Historical outcomes informed the
design and are disclosed; no historical result can pass this forward test.

## Population

The population is every immutable V13 candidate fact at or after the boundary.
V14 may score a row only after V13 has finalized its causal B1+B2 facts and a
completed Dukascopy macro snapshot covers the candidate's completed UTC-hour
endpoint. V13 model selection is ignored.

## Policy

The frozen partial-pooling Ridge model uses 44 numeric B1+B2+B3 features and a
single pooled score threshold corresponding to a 5% historical structural
weight veto quantile. Score at or above threshold means retain. Score below
threshold means research-only veto. Missing, stale, incomplete, or delayed
features mean retain by abstention.

## Two disjoint decisions

Validation opens after at least 20 eligible weekdays, 40 resolved scored
candidates, and five scored families. Confirmation starts only after a passing
validation and requires a later disjoint period with at least 40 additional
eligible weekdays, 120 resolved scored candidates, and six scored families.
Same-version tuning or refitting after the boundary is prohibited.

## Required economic gates

For both stages, replay the exact V60 portfolio constraints and V57 post-loss
cooldown independently for raw and ML-routed candidates. V14 must:

- retain at least 90% of raw executed trades;
- produce strictly higher net P&L than raw;
- have profit factor no worse than raw;
- have closed-trade drawdown no worse than raw;
- have positive P&L delta in the latest reported stage;
- have a weekly-block bootstrap 5% lower bound of P&L delta above zero;
- avoid a pass driven by one family or one isolated winner.

Failure, insufficient data, or mixed evidence leaves deterministic V60
unchanged and ML unauthorized.

## Authority

Prospective research scoring is authorized. Python serving, ML shadow use, EA
consumption, broker action, demo execution, and live execution are prohibited.
