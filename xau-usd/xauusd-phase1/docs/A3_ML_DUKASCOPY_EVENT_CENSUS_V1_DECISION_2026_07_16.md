# A3 ML Dukascopy Event Census V1 Decision

Date: 2026-07-16

Classification: `EVENT_CENSUS_NO_TRAIN_SURVIVOR`

## Decision

Reject all eight V1 family-direction hypotheses. Do not route them to ML, exact-tick
specialist replay, shared-account composition, forward shadow, demo, or live execution.
Do not loosen the V1 spread ceiling, entry rules, barriers, contexts, or gates and rerun
under the same version.

The result is a valid negative research result. The source and label pipeline passed.

## Source And Correctness

- verified Dukascopy XAUUSD Bid/Ask source: 120 of 120 months;
- source period: 2016-07 through 2026-06;
- causal M5 feature rows: 708,538;
- source days: 1,244 train, 621 validation, 620 internal test, and 624 exam;
- generated broad events: 44,364;
- event IDs and family-profile-time-direction keys: unique;
- events: chronological;
- source report, feature hash, row count, and source digest: matched the lock;
- labeled or intentionally ineligible event share: 99.5176%;
- events with at least one resolved barrier label: 10.6122%.

The first run exposed a quality-accounting defect: explicit entry-spread rejections were
incorrectly counted as unlabeled. Commit `1d30ba46` corrected only that definition and
added a regression test. It did not change an event, spread cap, label, economic metric,
or acceptance gate. The final run passed every quality gate.

Long entries used Ask and long exits used Bid. Short entries used Bid and short exits
used Ask. Stop gaps used the worse executable bar open. Same-bar stop/target collisions
were stop-first. Native spread, an additional $0.30 per event, and time-proportional
holding stress were included.

## Coverage Result

The census generated broad populations before execution eligibility:

- trend pullback resumption: 17,626 long and 16,252 short events;
- session opening drive: 622 long and 564 short events;
- session range break: 2,160 long and 1,985 short events;
- volatility expansion break: 2,536 long and 2,619 short events.

However, 117,936 of 133,092 barrier labels were intentionally ineligible because entry
spread exceeded 0.15ATR. Another 390 were rejected for a non-contiguous next bar and one
for the fixed initial-risk ceiling. There were 13,393 resolved barrier labels and 1,372
unresolved labels near unavailable forward paths.

This is the main structural weakness: Dukascopy's executable XAUUSD spread is large
relative to M5 ATR for most of the ten-year history. A short-hold strategy with stops of
only 0.50ATR to 1.00ATR begins with too much execution friction.

Eligibility was also strongly nonstationary. Depending on family and direction, only
0.84% to 6.19% of train events had a resolved barrier path, versus roughly 19.83% to
50.30% for session families in exam. Recent higher volatility made a fixed absolute
spread smaller relative to ATR. A recent-period result cannot rescue the sparse older
population.

## Frozen Train Results

No family-direction hypothesis selected a barrier profile. All 24 fixed
family-direction-barrier policies failed at least one train gate, and none reached the
chronological validation decision.

### Trend pullback resumption

This was the only large eligible population, with up to 180 long and 199 short train
events depending on barrier horizon. It still missed the 200-event minimum and was
economically poor:

- long 0.75ATR/1.125ATR: PF 0.435, average -0.4912R, net -78.5931R;
- short 0.75ATR/1.125ATR: PF 0.553, average -0.3564R, net -61.6498R;
- both directions failed average R, stability, winner-removal, and drawdown gates.

The directional horizon labels confirm that this was not only a stop-placement problem.
Train long mean gross return was negative at 30, 60, 120, and 240 minutes. Train short
mean gross return was negative through 120 minutes and only +0.0963ATR at 240 minutes;
after stress it was -0.0760ATR.

### Session range break

Only 34 long and 49 short train events had resolved barrier paths. Every long policy was
negative. The least-bad short barrier policy still had PF 0.564, average -0.3392R, and
net -16.6222R.

The 240-minute short horizon had positive mean stress return of +0.3400ATR, but it had
only 49 events and none of the preregistered barrier policies survived. It is diagnostic
evidence only and cannot be promoted or used to retune V1.

### Session opening drive

Only two long and five short train events were execution-eligible. The short cells were
positive but failed sample size, bootstrap, and winner-removal gates. Removing the few
winners made every policy negative. This is not usable evidence.

### Volatility expansion break

Only 13 long and 14 short train events had any resolved barrier path. The 1.00ATR short
policy had PF 1.270 and average +0.1571R across 11 events, but its bootstrap 2.5th
percentile was -1.1770R and removing the winners produced -6.4075R. The sample is noise,
not an edge.

## What Is Lacking

1. The current events do not have stable train expectancy. More historical rows cannot
   repair a negative label population.
2. M5-scale stop distances are economically mismatched to the executable spread during
   much of the history.
3. Positive cells have inadequate independent events and depend on a handful of winners.
4. Execution eligibility changes materially across volatility eras, so recent frequency
   overstates ten-year portability.
5. There is still no qualified label population for ML. Training a classifier on these
   outcomes would teach it mostly noise and execution-cost artifacts.
6. Two qualified trades per day remains a research objective, not an evidenced property.
   Forcing this frequency would weaken expectancy.

## Next Research Direction

Iteration 5 should move the trade geometry to a timescale where signal movement can
plausibly dominate spread while preserving causal Bid/Ask execution. It should be a new
preregistration, not a V1 threshold change.

The next campaign should:

- use M15/H1 decision structure and four-hour to multi-day holding horizons;
- define stops from completed session or H1 structure rather than 0.50-1.00 M5 ATR;
- cap total stressed execution cost as a fraction of initial risk;
- compare Dukascopy spread assumptions with the target broker's observer spread logs;
- test distinct regime specialists rather than one all-weather strategy;
- keep train, validation, internal test, exam, and prospective firewalls;
- require adequate sample size, positive winner-removed net, month stability, cost stress,
  and exact-tick replay before portfolio work;
- continue to abstain when no positive-expectancy event exists.

No V1 context subgroup, horizon, or barrier may be selected after seeing these outcomes.

## Artifact Lock

- contract SHA256:
  `64255db3e0cfebf1ef9da9a746b29b03cb60ba27d7b24f7d11082ddf38e055ce`
- events CSV SHA256 (17,650,081 bytes):
  `4115027fb291337fccd81f7b59324924c06f8c959374d69914bbda532df1f71c`
- horizon labels CSV SHA256 (42,372,840 bytes):
  `472c062d13b264341c2bcae63b167a789d3dfd94e4172825f0ac2cb88b572268`
- barrier labels CSV SHA256 (36,206,285 bytes):
  `96d780e83259a247e130956dc0efa1660357a709026193b3a3b6733640d6be74`
- policy metrics CSV SHA256:
  `f43fbb413a9005ab13e7d63e221393cd3cf52f5155b5205ced9917483d97b7e1`
- context metrics CSV SHA256:
  `58c49ca708e20daf801483b47c4037af71c971bb77415601d25fb58b2fbc7071`
- JSON report SHA256:
  `6342b772989661714c4b046700f9246ac012a474a23e4c27e35e16b5e91e94a3`
- Markdown report SHA256:
  `17facbd81e1a6836bd4133c94f6c867a7302824d09294b2a270a23b630d854d8`

The three large row-level CSVs remain in the external research workspace and are
reproducible from the locked source and implementation. Compact metrics and reports are
versioned with this decision.

## Authorization

- research result recorded: yes;
- specialist hypothesis authorized: no;
- exact-tick specialist replay authorized: no;
- Python prediction authorization: no;
- EA consumption authorization: no;
- demo authorization: no;
- live authorization: no.
