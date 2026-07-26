# Causal Candidate Quality ML V1 - Step 2B Contract

Status: `STEP_2B_DATASET_AND_FEATURE_CONTRACT_LOCKED`

Created UTC: `2026-07-22T04:31:52Z`

## Purpose

Step 2B freezes the exact dataset construction rules before any economic
outcome is opened. It authorizes no label calculation, feature materialization,
model fit, threshold fit, portfolio simulation, demo change, or live action.

The next stage may implement only the definitions locked here. Once Step 3
opens an outcome, changing any label, feature, population, deduplication,
weight, split, cost, or missing-data rule retires V1 and requires a new
preregistration.

## Populations

The primary model uses all `3,752` canonical candidates, not only the `2,194`
historically accepted candidates. Capacity, cooldown, drawdown, spread, and
other historical rejections remain audit fields and never become labels or
predictors. Each candidate receives its counterfactual outcome from the frozen
action and subsequent bid/ask path.

The journey failure library retains `117,534` action rows, `51,722` unique
candidate-directions, and `40,077` source events. Those rows are labeled and
reported separately in Step 3, but they cannot enter or rescue the primary V1
fit. This keeps genuine failed experiments available without letting thousands
of related strategy versions overwhelm the deployable candidate population.

The `115` additional archived trade ledgers stay in provenance quarantine.
They require a source-specific semantic adapter before row-level use. Their
existence is never treated as extra sample size.

## Raw Sources

Dukascopy XAUUSD raw bid/ask data is the sole historical price-path proxy for
primary labels. Complete frozen monthly manifests cover January 2010 through
June 2026. This includes the `241` canonical candidates before July 2016 that
the earlier ten-year derived feature cache did not cover.

The decoder is byte-bound to the tested Dukascopy delta decoder in
`dukascopy-microburst-replication-v25`. Each included month must be complete,
frozen, contain every calendar-hour file, and expose a 64-character aggregate
file digest.

DOLLARIDXUSD and USTBONDTRUSD are the only V1 cross-asset sources. Their
complete frozen histories cover January 2019 through June 2026. EURUSD,
GBPUSD, USDJPY, and XAGUSD are removed from V1 because their local histories do
not reach the newest outer eras. Multi-year median imputation is prohibited.

COMEX GC trades remain a research-only ablation for the final three outer
eras. Event time is eligible only through one second before feature cutoff.
Vendor receive time is not claimed as local live availability, and COMEX can
neither win the full-history comparison nor authorize deployment.

Capital paired quotes remain a short-history cost-transfer audit. They do not
replace Dukascopy labels or become a historical predictor.

## Action Geometry

Every canonical candidate uses one fixed primary action.

- R1 uses native pre-trade stop points multiplied by `0.01` price units.
- R2 and R3 use source-emitted signal ATR multiplied by frozen stop ATR.
- R4 uses source-emitted signal ATR multiplied by frozen stop ATR.
- R5 uses its recovered pre-policy signal ATR multiplied by frozen stop ATR.
- V7, V8, V25, and V57 use the pre-trade risk USD recorded by V57 divided by
  one ounce at `0.01` lot.

The initial stop distance is anchored to the Dukascopy executable entry. A
fixed R target is anchored to that same initial risk. A missing target means a
stop-plus-horizon action, not an inferred profit target.

## Label Replay

Entry is the first valid quote at or after `entry_eligible_time`, subject to the
family-specific maximum gap in the JSON contract. Longs enter at Ask and exit
on Bid; shorts enter at Bid and exit on Ask.

Stops fill at the first observed executable quote on or through the stop. This
retains adverse gap slippage. Targets fill at the locked target price on first
cross. Fixed horizons use the first executable quote at or after the deadline,
subject to the frozen family-specific gap. Raw tick order is authoritative and
there is no M5 fallback or nearest-time join.

R1 remains barrier-only. Its 90-day interval is a censoring and split-purge cap,
not a time exit. If neither barrier resolves by the cap, the economic target is
missing with `CENSORED_R1_OBSERVATION_CAP`.

The bid/ask path already includes spread. Base net R subtracts the USD `0.30`
ticket cost and USD `0.35` per 24 hours of holding, divided by initial risk USD.
Stress net R subtracts another `0.05R`. Spread is never charged twice.

High spread is neither an automatic loss nor an automatic exclusion. Invalid
risk, missing quotes, corrupt quotes, unexplained source gaps, incomplete paths,
and unavailable horizon quotes fail closed with an explicit unresolved status.
No unresolved row silently disappears.

Required labels include gross R, base and stress cost R, base and stress net R,
positive stress return, target-before-stop, MFE R, MAE R, holding minutes, exit
reason, label end, and resolution status. MFE and MAE use the executable exit
side from entry through the selected exit, inclusive.

## Features

The exact ordered raw feature surface has `59` columns, below the frozen limit
of `64`. The JSON contract is authoritative for names and formulas.

1. Block B1 has 16 deterministic candidate, geometry, family, direction, and
   UTC seasonal fields.
2. Block B2 adds 24 XAU spread, return, range, realized-variance, efficiency,
   intensity, staleness, and price-tick imbalance fields.
3. Block B3 adds 8 completed dollar-index and bond-proxy fields.
4. Block B4 adds 11 research-only COMEX trade-flow and relative-price fields.

Features include only ticks whose timestamp is at or before feature cutoff and
only bars whose end is at or before feature cutoff. All joins are exact or
backward-as-of. There is no future fill, forming bar, nearest join, full-history
normalization, outcome-driven feature selection, or automated feature search.

The M5 ATR reference is a 14-period Wilder ATR over completed midpoint M5 bars.
Raw windows are trailing `(cutoff - window, cutoff]` intervals. Slow returns use
completed H1/H4/D1-equivalent endpoints. Divisions by zero produce missing
values and are handled by the frozen missing-data policy, never by infinities.

Family, broad mechanic, stop mode, and target mode are categorical. Candidate
IDs, event IDs, source row IDs, exact timestamps, dates, attempt/version IDs,
historical policy decisions, and every outcome-derived field are prohibited
predictors.

## Preprocessing

Every preprocessing object is fitted inside the outer training fold only.
Numeric imputation uses the training-fold median. The linear pair additionally
uses training-fold standard scaling. Categorical values use training-fold
one-hot encoding with unknown values ignored by the transformer, but an unknown
family or broad mechanic forces the final action to `ABSTAIN_OUT_OF_DOMAIN`.

More than 5% missing values in any registered numeric training feature fails
that pipeline. Missing mandatory XAU inputs, XAU staleness above 300 seconds,
cross-asset staleness above 7,200 seconds, or COMEX staleness above 300 seconds
forces abstention for the affected block.

The 64-column cap applies to raw semantic features. One-hot expansion is
reported but does not create new research choices.

## Deduplication And Weights

Step 2A candidate IDs are primary identities. Exact semantic duplicates use
decision time, direction, broad mechanic, and frozen geometry. Canonical
lineage wins duplicate retention, but every duplicate source remains recorded.
Different mechanics at one event remain separate candidates in one structural
episode. Fuzzy matching by P/L or duration is prohibited.

Canonical primary weight is the Step 2A inverse structural-episode weight. Its
sum is `3,489`. Unweighted and conservative-overlap weighted metrics are fixed
sensitivity reports.

Journey action weight is:

```text
1 / candidate-directions in source event / actions attached to candidate
```

The weight sum is therefore exactly one per source event, or `40,077` overall.
This lets every unique failure remain available without counting alternative
horizons or mirrored directions as independent evidence.

SMOTE, random oversampling, row duplication, and outcome-selected weights are
prohibited.

## Walk-Forward Splits

The six July-to-July outer tests remain frozen. Each calibration interval is
the immediately preceding six calendar months, and fit data precedes
calibration.

Fit candidates require both planned observation end and later actual label end
to precede calibration start. Calibration candidates require both to precede
test start. Structural siblings stay in one split. Random or shuffled splitting
is prohibited.

The outcome-blind planned-interval counts are locked in the JSON contract. They
range from `702` fit rows in F2020 to `2,853` in F2025. Actual resolved counts
may only decrease through explicit label-resolution or source-quality status;
they may never increase through relaxed purging.

## Effective Sample Size

Nominal rows are not effective sample size. Step 3 must report structural
episode count, Kish effective size, and serial-correlation effective size. The
serial rule is Geyer's initial positive sequence over chronologically ordered
episode outcomes with at most 60 lags. The conservative effective size is their
minimum. Economic uncertainty uses the already frozen five-weekday block
bootstrap with 10,000 resamples and seed `60104`.

## Decision

Step 2B passes only when all bound files and monthly source manifests verify,
the exact feature definitions reconcile, the split counts match, the journey
weights sum to `40,077`, all controls remain closed, and a second run produces
the same lock.

Passing Step 2B authorizes only Step 3 label and causal feature construction.
It does not authorize model fitting, threshold fitting, demo attachment, ML
shadowing, EA consumption, or broker action.
