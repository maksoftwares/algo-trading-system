# Causal Candidate Quality ML V1 Preregistration

Status: `STEP_1_RULES_FROZEN_NO_DATASET_NO_MODEL`

Created UTC: `2026-07-21T20:19:32Z`

Repository base: `11bd1a791262bda1e2ccbdb6f65e37c7f498cdb1`

## Purpose

The first ML task is a pooled, research-only candidate-quality meta-labeler. It
asks whether information available when a deterministic XAUUSD candidate is
created can estimate:

1. expected stressed net return in initial-risk units; and
2. the probability that stressed net return is positive.

The first model does not generate entries, reverse direction, change stops or
targets, choose holding horizons, size risk, reinstate broker-ineligible rows,
or override the portfolio risk engine. It may score frozen V59/V60 Core trades
offline, but it may not suppress or alter any Core trade in demo execution.

The primary action is one unique candidate under one mechanically frozen action
contract for its source family. Alternative horizons remain vector-valued
diagnostic labels attached to the same candidate; they cannot become extra
independent training rows.

## Frozen Baseline

The comparison portfolio is byte-bound V59/V60:

- `815` broker-expressible Core trades;
- `1,379` accepted add-on trades;
- `2,194` total accepted trades;
- final-year frequency `1.394636` trades per weekday;
- final-year net USD `2,537.35`, PF `1.975779`, and closed drawdown USD
  `152.59`;
- whole-account floating drawdown USD `329.64`, or USD `412.06` with the
  frozen 25% buffer; and
- hard buffered floating-drawdown limit USD `449.7675`.

The exact V59 result, V59 accepted-trade ledger, V60 result, V60 price ledger,
and current canonical deployment configuration are SHA-256 bound in the JSON
contract. V59/V60 rules, trades, sizes, risk controls, and runtime behavior are
immutable controls for this campaign.

## Evidence Boundary

All inspected data through `2026-06-30T23:59:59Z` is development evidence. A
historical pass may reject an architecture or nominate a later prospective
test, but it cannot authorize model serving, demo attachment, live attachment,
EA consumption, or broker action.

Data collected after July 20 but before a final trained-model hash is locked is
infrastructure and data-quality evidence only. It cannot be retroactively called
the model's forward exam. A prospective model window starts strictly after the
final model, feature list, dataset contract, and decision policy are hashed.

Step 1 itself authorizes no candidate outcome read, counterfactual label build,
feature build, model fit, threshold fit, or portfolio simulation. The next
allowed operation is Step 2: metadata-only inventory and integrity auditing.

## Population Separation

Four populations must remain separately identified:

1. `CANONICAL`: exact candidates from the frozen deployable source families,
   including mechanically valid candidates historically blocked by portfolio
   capacity or risk policy;
2. `RESEARCH_NEGATIVE`: candidates from failed, retired, mirrored, or exhausted
   experimental families;
3. `COMEX_RESEARCH`: candidates or features requiring historical COMEX data;
4. `PROSPECTIVE_CAPITAL`: candidates created after the final model lock from
   newly collected Capital evidence.

The primary model is fitted on the verified canonical candidate universe.
Research-negative rows may be used only in separately reported robustness or
out-of-domain diagnostics. They cannot dominate, enlarge, or rescue the primary
population. COMEX-enabled results remain research-only until an affordable,
causal live COMEX feature source and its delivery latency are independently
verified.

The `320` fractional R5 rows below the broker's `0.01`-lot minimum remain
`broker_executable=false`. They may be retained as economic diagnostics but
cannot enter executable-model gates or frequency claims.

## Permitted Data Roles

### Dukascopy

Dukascopy XAUUSD bid/ask history may supply causal spot features and historical
counterfactual label proxies: executable-side entry and exit, spread, stop and
target ordering, gap handling, MFE, MAE, and realized volatility. These are
historical proxy labels, not claims about exact Capital fills.

Ten-year Dukascopy Forex, XAGUSD, dollar-consensus, and bond-proxy histories may
supply completed, backward-as-of cross-asset context after timestamp, coverage,
and direction normalization pass Step 2. They cannot supply future-smoothed
states or full-history normalizers.

### COMEX

Already acquired Databento `GLBX.MDP3` `GC.v.0` trade prints may supply a
separate historical feature ablation using trade count, volume, aggressor side
when valid, intensity, price response, roll state, and causal futures/spot
relationships. The trades schema cannot be described as order-book depth.
Instrument identity and roll boundaries must be preserved. Vendor receive time
is not local availability; any eventual live contract must add measured delivery
and processing latency.

### Capital And MT5

Capital quote logs may measure broker spread transfer, basis, staleness, and
prospective execution differences. Their short history cannot become the main
historical representation source. MT5 and Python ledgers provide source lineage,
candidate identity, geometry, native position/deal evidence, and demo parity.
Weaker MT5 historical prices cannot silently override the locked bid/ask label
proxy.

HistData is prohibited as an independent feature source because its audited M5
surface duplicated Dukascopy. No Databento purchase, new account, API request,
or additional paid/free-credit acquisition is authorized.

## Causal Record Contract

Every candidate must carry:

- immutable `candidate_id`, source, family, direction, and population;
- structural and conservative episode IDs;
- source event time, signal-bar end, decision time, feature cutoff, earliest
  eligible entry, and label end;
- source availability and provenance, including hashes;
- frozen stop, target, maximum hold, latency, and cost contract;
- historical accept/reject state for audit only; and
- explicit data-quality, broker-executable, and label-resolution status.

The invariant is:

```text
source_available_at <= feature_cutoff <= decision_time <= entry_eligible_time
```

All market joins are exact or backward-as-of. Nearest joins, future fills,
forming bars, outcome-defined regimes, full-history scaling, and timestamps or
IDs used as memorization features are prohibited.

## Labels

Historical rejection is not a loss label. Every mechanically valid candidate is
replayed under its frozen family action contract regardless of historical
acceptance, unless execution evidence is unavailable or corrupt.

Long entries use executable Ask and exits use Bid. Short entries use Bid and
exits use Ask. The bid/ask path already contains spread, which cannot be charged
twice. Ticket fees, frozen slippage stress, holding cost, and broker-transfer
stress are separate fields.

The primary continuous target is `stress_net_r`. The secondary binary target is
`stress_net_r > 0`. Required diagnostic labels are base net R, target-before-
stop, MFE R, MAE R, holding minutes, cost R, exit reason, and resolution status.
Rows with missing initial risk, ambiguous event ordering, no executable quote,
or incomplete hold paths fail closed and are counted rather than silently
dropped.

## Features And Budget

Only four nested, preregistered feature blocks may be tested:

1. deterministic candidate geometry, frozen source identity, direction, and
   deterministic regime context;
2. block 1 plus XAUUSD spread, return, volatility, range, efficiency, intensity,
   and staleness aggregates;
3. block 2 plus completed Forex, silver, dollar-consensus, and bond-proxy state;
4. block 3 plus causal COMEX trade-flow and futures/spot aggregates.

Exact deployable source identity is permitted as a controlled categorical effect.
Experiment number, attempt ID, candidate ID, result version, P/L-derived family
selection, and post-outcome tags are forbidden predictors.

The primary feature list may contain at most `64` columns. Permitted raw-event
aggregation windows are `30 seconds`, `5 minutes`, `15 minutes`, and `60
minutes`. Slow context may use completed `H1`, `H4`, and `D1` values. The Step 2
audit may prove a predeclared field unavailable and remove it; it may not invent
a substitute. The exact ordered column list must be separately hashed before
labels are joined or any model is fitted.

Raw-event neural encoders, automated feature generation, feature selection by
outcome, SMOTE, random oversampling, and shuffled splits are prohibited in V1.
Probabilistic regime modeling is outside the first model and requires a later
contract after the aggregated-feature baseline is evaluated.

## Episodes, Splits, And Weighting

Every action sibling from one candidate and every structural duplicate remains
in one split. Structural episode identity is primary. A separate conservative
overlap graph is used for confidence intervals and effective-size reporting;
time proximity alone cannot transitively merge an unlimited chain of events.

The historical diagnostic uses six expanding July-to-July outer test eras from
`2020-07-01` through `2026-07-01`. For each era, the immediately preceding six
calendar months are calibration and all earlier eligible history is fit data.
Fit labels must end before calibration starts; calibration labels must end
before test starts. Planned label overlap and all episode siblings are purged.

Training uses the one primary action row per unique candidate. Primary training
weights are frozen only after Step 2 reports structural episodes, conservative
overlap, and concentration. The choice must be locked before outcome labels are
opened. Unweighted and conservative uniqueness-weighted results are mandatory
sensitivity reports, not alternative models available for winner selection.

Uncertainty is calculated on chronological episode blocks, not independent rows.
The primary economic bootstrap block is fixed at five weekdays. Step 2 must also
report outcome-blind candidate-time dependence and any resulting conservative
effective-size diagnostic, but it cannot change the primary bootstrap to rescue
an outcome. Nominal row counts cannot be reported as effective sample size.

## Model And Decision Budget

There are two learned architecture pairs. The first three nested feature blocks
produce exactly `6` registered primary pipelines in every full-history outer
fold:

1. an L2 logistic classifier paired with a ridge expected-R regressor; and
2. a shallow histogram-gradient-boosting classifier paired with a shallow
   histogram-gradient-boosting expected-R regressor.

The COMEX block adds exactly `2` research-only pipelines in the three eligible
outer eras from `2023-07-01` through `2026-07-01`. It cannot be backfilled into
earlier eras, compete as a full-history winner, or authorize deployment. This is
`8` total registered architecture/feature combinations, but never eight fitted
in an era without COMEX history.

Parameters are fixed in the JSON contract. Null base-rate and mean-R predictors
are mandatory comparisons but do not count as learned attempts. No parameter
grid, seed search, threshold search, feature search, family-specific rescue, or
separate specialist models are permitted.

The decision rule is fixed:

- `TAKE` only when predicted stressed expected R is greater than `+0.05R`, the
  predicted positive-return probability is greater than the training-fold
  source-family base rate, data quality passes, and the row is broker-executable;
- `SKIP` when predicted stressed expected R is below `0R`;
- `ABSTAIN` otherwise, including missing, stale, unsupported, or out-of-domain
  input.

No daily quota or outcome-selected retention target is allowed.

## Historical Nomination Gates

All gates are required. Failure is terminal for V1; there is no same-version
repair.

### Data and discrimination

- exact candidate and source reconciliation passes;
- zero future or nearest-time joins;
- at least `50` resolved TAKE decisions and `0.25` TAKEs per eligible weekday in
  every outer test era;
- aggregate weighted ROC AUC at least `0.55` and no outer era below `0.50`;
- aggregate relative Brier improvement at least `2%` versus the fold-local base
  rate and no outer era with worse Brier than base rate;
- aggregate expected-R rank correlation is positive; and
- aggregate expected calibration error is at most `0.05`.

### Economics and stability

- every outer era has positive selected stress net, positive mean stress R, and
  stress PF at least `1.10`;
- aggregate selected stress PF is at least `1.25`;
- aggregate stress net remains positive after removing the five largest winners;
- at least `70%` of rolling six-month selected windows are positive;
- any direction with at least `50` selected rows has positive stress net;
- standalone selected closed drawdown is at most USD `250`;
- adding any nominated satellite decisions to byte-identical V59/V60 keeps the
  buffered shared-account floating drawdown at or below USD `449.7675`;
- every V59/V60 trade and its risk treatment remains byte-identical; and
- a five-weekday episode-block bootstrap 90% lower confidence bound for mean
  selected daily stress P/L is greater than zero.

A Core-filtering counterfactual is diagnostic only and cannot satisfy an
execution gate. The first execution-facing nomination may add or rank satellite
candidates without changing Core.

## Prospective Confirmation

A historical survivor may only nominate an unchanged, separately approved,
sealed batch-scoring protocol. It is not attached to MT5 and does not influence
demo trades.

Validation begins after the final model hash and continues until both `20` full
weekdays and `50` resolved TAKE decisions exist. If validation passes unchanged,
confirmation uses the next disjoint period satisfying the same minimums. Each
stage requires positive stress net, stress PF at least `1.10`, positive net after
the largest winner is removed, no V59/V60 trade change, and no portfolio hard-
stop breach. Confirmation additionally requires stress PF at least `1.20`.

Any failure retires the model version. Passage still grants no execution; a
separate owner/reviewer authorization and deployment contract are mandatory.

## Step 1 Decision

Step 1 is complete only when the Markdown and JSON contracts are hashed, the
governance tests pass, and the lock verifies idempotently. Completion means the
rules are frozen. It does not mean data readiness, model training, profitability,
or deployment readiness.
