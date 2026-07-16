# A3 ML Macro Regime Event Census V1 Decision

Date: 2026-07-16

Classification: `MACRO_REGIME_EVENT_CENSUS_NO_TRAIN_SURVIVOR`

## Decision

Reject all eight V1 macro family-direction policies. Do not route them to ML, exact-tick
specialist replay, shared-account composition, forward shadow, demo, or live execution.
Do not tune a V1 threshold, direction, stop, target, hold, or subgroup after seeing the
result.

The result is a valid economic rejection. All source, causal-availability, uniqueness,
chronology, cost, and label-quality gates passed.

## Source And Correctness

- verified Dukascopy XAUUSD Bid/Ask M5 rows: 708,538;
- derived contiguous H1 rows: 59,003;
- gold source period: 2016-07 through 2026-06;
- target-broker spread floor: $0.75;
- additional execution stress: $0.30 per 0.01 lot;
- minimum initial stop distance: $7.00;
- macro inputs: `DFII10`, `DGS2`, `DGS10`, and `DTWEXBGS`;
- macro rows per source: 2,630;
- macro coverage inside the research window: 100%;
- two-calendar-day macro availability lag: enforced on every H1 row;
- generated events: 2,824;
- resolved labels: 2,712;
- intentionally ineligible labels: 105;
- unresolved partition-edge labels: 7;
- resolved-or-ineligible event share: 99.7521%;
- duplicate event IDs: 0.

Entry was the next contiguous M5 quote after the completed H1 decision. Long entries
used Ask and exits used Bid; short entries used Bid and exits used Ask. Stop gaps used
the worse executable open and same-M5 stop/target collisions were stop-first. No label
crossed a train, validation, internal-test, or exam boundary.

The macro files are current-vintage FRED histories, not a full ALFRED real-time-vintage
panel. The disclosed historical-revision risk remains.

## Coverage

Broad event counts across all four windows:

- macro-aligned H1 trend pullback: 706 long and 610 short;
- macro-aligned H1 range break: 371 long and 292 short;
- macro-shock H1 continuation: 317 long and 352 short;
- macro-divergence H1 reclaim: 81 long and 95 short.

The wider H1 geometry solved the execution scarcity seen in M5 research. Only 12 events
failed stressed cost/R, 46 exceeded the fixed $50 risk ceiling, and 47 lacked a
contiguous next entry bar. The campaign failed because of expectancy and stability,
not because spreads removed nearly all opportunities.

## Frozen Train Results

### Macro-aligned H1 trend pullback

- long: 269 trades, PF 0.675, average -0.2372R, net -63.8104R;
- short: 218 trades, PF 0.446, average -0.4752R, net -103.5985R;
- both directions failed PF, average R, month stability, drawdown, bootstrap, and
  winner-removal gates.

Macro agreement did not repair the price-only trend-pullback mechanism.

### Macro-aligned H1 range break

- long: 135 trades, PF 0.870, average -0.0763R, net -10.3006R;
- short: 111 trades, PF 0.477, average -0.3571R, net -39.6418R;
- both directions failed economic and robustness gates.

### Macro-shock H1 continuation

- long: 82 trades, PF 1.054, average +0.0275R, net +2.2524R;
- short: 103 trades, PF 0.878, average -0.0705R, net -7.2591R.

The long cell was close to break-even but failed minimum events, PF, average R,
bootstrap, and winner-removal gates. Its bootstrap 2.5th percentile was -0.2804R and
removing the ten largest winners made net -11.9633R. It is not a usable edge.

### Macro-divergence H1 reclaim

- long: 27 trades, PF 0.568, average -0.3090R;
- short: 38 trades, PF 1.179, average +0.0794R, net +3.0182R.

The short cell failed sample size, positive-month, bootstrap, and winner-removal gates.
Its bootstrap 2.5th percentile was -0.3088R and winner-removed net was -10.8142R. It is
a sparse clue, not authorization to promote the direction or retune the family.

## What Was Learned

1. Wider H1 risk geometry can admit economically executable gold opportunities under
   the measured target-broker cost floor.
2. Lagged daily real yields and the broad dollar index are useful regime context but do
   not supply reliable intraday entry timing by themselves.
3. Macro alignment did not rescue trend pullbacks or range breaks; those mechanisms
   were negative with adequate train samples.
4. The two positive cells depended on too few observations and too few winners.
5. There is still no economically positive, sufficiently large label population for ML.
   Training a ranker now would violate the preregistered boundary.
6. The current price-plus-daily-macro data does not support the requested couple of
   qualified trades per day at acceptable robustness.

## Next Research Direction

Iteration 6 should first determine whether a verified intraday rates and dollar source
is available in the existing Dukascopy instrument universe. The most relevant additions
are an intraday United States 10-year yield or Treasury proxy and a dollar-index feed.
Those data could align macro repricing with the actual H1 signal hour rather than a
two-day-lag daily state.

If such source data cannot be verified, stop extending the high-frequency price-only
branch. Preserve the profitable but lower-frequency R1 comparator as the research base
and focus on prospective evidence rather than inventing more candle variants.

V1's mildly positive shock-long and divergence-short cells may not be selected, tuned,
or combined after outcome inspection.

## Artifact Lock

- contract SHA256:
  `0b870dd345c1889cd9bfe930380b16eb683198b8b3800767decdccae8ea759f7`
- H1 feature CSV SHA256 (57,926,165 bytes):
  `185afaf4a23f9475567ebfbad5b4ea319bc10950970fc9e00d091f238c1265f7`
- events CSV SHA256:
  `a77fb5d51c9eeac3f6c5b73ebfd60c7006cec93ecc8b52dbf065a49705f03132`
- labels CSV SHA256:
  `35134dec16de835d93367263250d9c2fc52686fc876fa8b937dc0cf6bf81752d`
- metrics CSV SHA256:
  `21e24a00feb2d3fe9d7a711ba52120b9c128fa1502d5f7db1b18e57409b1c2aa`
- JSON report SHA256:
  `16d45144aa10ff69b96b7f230b3bc7ecfad098b647f5915c6b8cdde75bbe705c`
- Markdown report SHA256:
  `11badddf8f1bc61dadd90b052d62deb525fec1d833ccee3f28fa5391739df047`

The large H1 feature table remains in the local research workspace and is reproducible
from the four locked macro files, the Dukascopy cache, and commit `61619ea3`.

## Authorization

- research result recorded: yes;
- specialist hypothesis authorized: no;
- exact-tick replay authorized: no;
- model training authorized: no;
- Python predictions authorized: no;
- EA consumption authorized: no;
- demo authorization: no;
- live authorization: no.
