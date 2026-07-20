# XAUUSD Frequency Mechanism Failure Map

Date: 2026-07-20
Status: historical development audit; no execution authority

## Objective

Preserve the byte-identical five-specialist Core while adding enough genuinely
independent positive-expectancy activity to reach 3-4 combined trades per
weekday. The final-year Core reference is 160 trades over 261 weekdays, or
0.6130268199/day. A satellite therefore needs 2.3869731801-3.3869731801/day.

## What The Evidence Rules Out

| Mechanism lane | Authoritative evidence | Result | Reuse rule |
|---|---|---|---|
| Frozen deterministic Core | audited Core ledger | PF 3.4918, USD 4,508.78 net, 0.613/day | Preserve unchanged |
| Generic high-frequency bar expansions | V12, V18-V21 | Frequency can reach 3-4/day, but recent/stressed economics fail | No quota filling or threshold rescue |
| Trend pullback, failure, and trailing variants | V14, V15, trailing-trend V1 | No admission survivor | New work needs a different causal input |
| Session and calendar effects | calendar-session V1, literature-timed-effects V1 | No survivor | Do not search more clock buckets on the same history |
| Compression, chop, and stationarity variants | compression replications and chop V18-V21 | No robust survivor | No mirror or parameter rescue |
| DXY, bond, dislocation, and macro exhaustion | intraday-macro V1/V2 | No survivor | Aggregate macro direction alone is retired |
| Scheduled CPI, PPI, NFP, and FOMC aftermath | corrected event and holdout campaigns | Sparse and not multiplicity/stability supported | Event sleeves cannot solve daily frequency |
| COMEX total-flow, auction, VWAP, session, and lead/lag | COMEX campaigns | No chronological survivor | Total flow alone is retired |
| COMEX large-versus-small aggressor-flow continuation | V32/V33 | 2.383 resolved trades/day, base PF 0.493, stress PF 0.455 | Terminal; validation/exam sealed, no mirror rescue |
| COMEX exhausted-flow transition and sequence ignition | V44/V45/V68 | Continuations failed near PF 0.46; fixed anti-signal reached 0.967/day but stress PF 0.401 and USD 410.41 DD | Terminal in both directions; no threshold, quota, or mirror reuse |
| Subsecond COMEX receipt-to-spot innovation | V69/V70 | Corrected lane reached 0.784/day and low DD, but base PF 1.054, stress PF 0.941, both halves below 1, p=1.0 | Terminal; no clock, horizon, threshold, exit, or cost rescue |
| COMEX fixed round-price barrier rejection | V71 | 0.780/day, base PF 0.512, stress PF 0.473, both halves below 0.53, USD 282.92 DD | Terminal; no spacing, window, breakout mirror, exit, or threshold rescue |
| Tokenized-gold and cross-venue divergence | PAXG and Capital-Dukascopy campaigns | No robust causal economic lane | No lag/threshold reuse on exposed history |
| Capital quote exhaustion reversal | V30 | 5.9/day, base PF 0.7171, stress PF 0.5907 | Terminal; no tuning or mirror |
| Capital quote absorption release | V31 | 5.4/day, base PF 0.4924, stress PF 0.3816 | Terminal; no tuning or mirror |

## What Is Actually Missing

The project is not missing price history, computing capacity, candidate volume,
or a backtest framework. It is missing 2.39-3.39 daily opportunities whose
direction is knowable before entry and whose movement is large enough to clear
spread and slippage in every required chronological partition.

Historical data already consulted by these campaigns remains useful for
development but is not independent proof. Every new historical survivor must
be frozen and then earn admission on untouched forward evidence.

## Completed Independent Lane

COMEX large-versus-small aggressor-flow divergence was the next registered lane.
Existing COMEX work had aggregated all signed volume; V32/V33 separately tested
whether large-lot directional pressure opposed by small-trade flow predicted a
larger, slower XAUUSD continuation move. It did not.

The lane did satisfy its process requirements:

1. use only completed COMEX trade windows and causal, backward-looking size
   classifications;
2. choose any activity thresholds using frequency and direction balance only,
   before spot outcomes are opened;
3. use verified Dukascopy bid/ask ticks for side-correct entry and exit;
4. use a locked holding and risk rule large enough to test movement beyond
   transaction costs;
5. open chronological stages sequentially and stop at the first failed gate;
6. counted the full registered family in multiplicity controls; and
7. remained research-only.

V32 failed its first frequency-only grid at 2.15 candidates/day without opening
economics. The preregistered V33 density repair reached 2.9 calibration
candidates/day, locked, and resolved 1,170 development trades. Both chronological
halves lost money and the full stress PF was 0.455. The family is terminal and
cannot be mirrored or tuned on the exposed outcomes.

## Authoritative Active Paths

No remaining historical family is promoted by this map. The two active paths
with an unexposed information boundary are:

1. V24.1/V26 Capital quote microburst and gap-restart forward collection; and
2. complete same-period Core reconstruction for R1-R5, followed by one shared
   forward portfolio timeline.

Historical exploration may continue only for a mechanism with a materially new
causal input. It cannot delay or replace the untouched forward proof.

## V68 Fixed Anti-Signal Result

V68 tested the only defensible mirror audit of V44/V45: one preregistered union,
source direction inverted exactly once, earliest candidate per UTC date, and no
outcome-selected threshold, quota, session, stop, target, or hold change. It
reached the intended density but failed every economic and stability gate.

- 475 resolved trades over 491 eligible full weekdays, or `0.967413/day`;
- 235 longs and 240 shorts;
- USD `-365.52` base and USD `-402.40` stress net;
- base PF `0.4338` and stress PF `0.4006`;
- first/second-half stress PF `0.3804/0.4241`;
- zero positive months, USD `410.41` stress DD, and bootstrap p-value `1.0`.

Decision: `V68_DEVELOPMENT_FAIL_TERMINAL`. Validation and exam remain sealed.
The result shows that weak V44/V45 continuation was not a hidden reversible
edge; both sides are dominated by noise and cost. New historical work must use
a new causal variable, such as a directly synchronized cross-venue price
innovation, and may not recycle these exposed source outcomes.

## V69/V70 Receipt-Time Innovation Result

V69 preregistered a subsecond cross-venue mechanism using Databento receipt
timestamps and raw Dukascopy quotes. Its outcome-blind calibration selected a
two-second policy at exactly `0.80/day`, but development stopped before writing
outcomes because the code incorrectly required publisher event time not to
exceed receive time. V69 remains immutable as an engineering stop.

V70 removed only that invalid cross-clock assertion, recorded the anomaly
count, repeated calibration, and froze the same selected policy. Development
then produced `385` resolved trades over `491` weekdays (`0.784114/day`), with
`184` longs and `201` shorts. Base economics were barely positive at USD
`18.71` and PF `1.054`; realistic stress was USD `-21.45` at PF `0.941`.
First/second-half stress PF was `0.978/0.906`, only `43.48%` of months were
positive, winner-removed stress net was USD `-54.95`, and bootstrap p-value was
`1.0`. Closed DD was low at USD `37.55`, but low risk does not replace edge.

Decision: `V70_DEVELOPMENT_FAIL_TERMINAL`. Validation and exam remain sealed.
Direct event-time COMEX-to-spot innovation is now exposed and retired. Further
historical work must use a different causal variable, not a faster/slower
version or a post-outcome exit modification.

## V71 Fixed Round-Barrier Rejection Result

V71 tested an untried causal variable: probes through mechanically fixed COMEX
round prices followed by a completed rejection and opposite aggressor flow.
Exactly 1,000 policies were registered, and outcome-blind calibration selected
USD `10` barriers, a `120`-second window, USD `0.40` probe, USD `0.80`
rejection, and `0.25` opposite-flow imbalance at exactly `0.80/day`.

Development retained density at `383` resolved trades over `491` weekdays
(`0.780041/day`) with `203` longs and `180` shorts, but the edge failed
decisively. Base/stress PF was `0.512/0.473`, stress net was USD `-268.00`,
first/second-half stress PF was `0.430/0.521`, positive months were `13.04%`,
winner-removed stress net was USD `-284.24`, closed DD was USD `282.92`, and
bootstrap p-value was `1.0`.

Decision: `V71_DEVELOPMENT_FAIL_TERMINAL`. Validation and exam remain sealed.
The barrier family cannot be mirrored into breakout continuation or retuned on
the exposed outcomes. A successor needs another causal variable.

## V73 Fixed Silver Anti-Signal Result

V73 performed the one allowed directional falsification of V72. It inherited
the exact locked event policy and execution, inverted direction once, and began
only after V72's exposed cutoff. Fresh development resolved `242` trades over
`257` weekdays (`0.941634/day`), with `136` longs and `106` shorts. Base/stress
net was USD `-136.62/-154.25`; base/stress PF was `0.3987/0.3554`;
first/second-half stress PF was `0.3359/0.3730`; no month was positive;
winner-removed stress net was USD `-166.38`; stressed DD was USD `154.25`; and
bootstrap p-value was `1.0`.

Decision: `V73_DEVELOPMENT_FAIL_TERMINAL`. Contract SHA-256:
`c0949fe88fd157df89bf9a06b96f5fd2ee9f6eaefc2fb6b4330c93807c998ee7`.
All later stages remain sealed. V72/V73 show that the raw silver-lag event is
not a hidden reversible edge under the locked tradable geometry. Both
directions and all associated threshold or exit rescues are retired.

## V74 Raw DXY-to-XAU Event-Time Result

V74 tested a new raw event-time input: a DXY quote shock followed by the expected
inverse XAU catch-up. Its source audit covered `180` frozen symbol-months,
`131,424` hourly rows, and `447,967,303` declared ticks through June 2026.
Outcome-blind calibration selected a one-second, 1.0 bps DXY move, 0.5 bps
innovation, zero-response, two-quote policy at `18/22 = 0.818182/day`, with nine
long and nine short candidates.

Development resolved `710` trades over `871` eligible weekdays
(`0.815155/day`), split `368` long and `342` short. Base/stress net was USD
`-462.04/-516.71`; base/stress PF was `0.3904/0.3519`; first/second-half stress
PF was `0.3230/0.3822`; no month was positive; winner-removed stress net was USD
`-541.04`; stressed DD was USD `517.76`; and bootstrap p-value was `1.0`.

Decision: `V74_DEVELOPMENT_FAIL_TERMINAL`. Contract SHA-256:
`8e0ec9b0dd27282f9186976d97bd709d919764b34f0478a218aaa82ee78ca28d`.
Later stages remain sealed. No event threshold or execution rescue is allowed.
One fixed direction inversion may begin only on the unopened July 2022 period;
after that test, the raw DXY family is terminal in both directions.

## V75 Fixed DXY Anti-Signal Result

V75 performed the one allowed directional falsification of V74. It inherited
the exact locked event policy and execution, inverted direction once, and began
only after V74's exposed cutoff. Fresh development resolved `231` trades over
`256` weekdays (`0.902344/day`), with `115` longs and `116` shorts. Base/stress
net was USD `-131.42/-148.20`; base/stress PF was `0.4445/0.4025`;
first/second-half stress PF was `0.4536/0.3592`; one of 12 months was positive;
winner-removed stress net was USD `-166.78`; stressed DD was USD `153.99`; and
bootstrap p-value was `1.0`.

Decision: `V75_DEVELOPMENT_FAIL_TERMINAL`. Contract SHA-256:
`9384d5c77a82346f057a53759d4dfc200c54531c7d49c1349634965875b6d816`.
All later stages remain sealed. V74/V75 show that this raw DXY-lag event is not
a hidden reversible edge under the locked tradable geometry. Both directions
and all associated threshold, timing, or exit rescues are retired.

## V76 Raw Treasury-Bond-to-XAU Event-Time Result

V76 tested a new raw event-time input: a U.S. Treasury bond price shock followed
by the expected same-direction XAU catch-up. Its source audit covered `180`
frozen symbol-months, `131,424` hourly rows, and `445,583,861` declared ticks
through June 2026. Outcome-blind calibration registered `1,000` policies and
selected a two-second, 0.5 bps source-move, 0.5 bps innovation, zero-response,
five-quote policy at `9/9 = 1.0/day`, with seven long and two short candidates.

Development resolved `730` trades over `828` eligible weekdays
(`0.881643/day`), split exactly `365` long and `365` short. Base/stress net was
USD `-512.26/-567.63`; base/stress PF was `0.3301/0.2952`;
first/second-half stress PF was `0.2233/0.3668`; no month was positive;
winner-removed stress net was USD `-584.37`; stressed DD was USD `567.88`; and
bootstrap p-value was `1.0`.

Decision: `V76_DEVELOPMENT_FAIL_TERMINAL`. Contract SHA-256:
`56151a77385d55c6a19c577016075fa92b17db137e845695b472bd5e78b0f681`.
Later stages remain sealed. No event threshold or execution rescue is allowed.
One fixed direction inversion may begin only on the unopened July 2022 period;
after that test, the raw Treasury-bond family is terminal in both directions.

## V77 Fixed Treasury-Bond Anti-Signal Result

V77 performed the one allowed directional falsification of V76. It inherited
the exact locked event policy and execution, inverted direction once, and began
only after V76's exposed cutoff. Fresh development resolved `228` trades over
`253` weekdays (`0.901186/day`), with `109` longs and `119` shorts. Base/stress
net was USD `-188.78/-204.96`; base/stress PF was `0.2677/0.2406`;
first/second-half stress PF was `0.2031/0.2776`; no month was positive;
winner-removed stress net was USD `-216.73`; stressed DD was USD `210.51`; and
bootstrap p-value was `1.0`.

Decision: `V77_DEVELOPMENT_FAIL_TERMINAL`. Contract SHA-256:
`51450419d51bb4b5bc983f313269b1f7980dcf14c6b6adf2c232f8c095d2b3af`.
All later stages remain sealed. V76/V77 show that this raw Treasury-bond event is
not a hidden reversible edge under the locked tradable geometry. Both directions
and all associated threshold, timing, or exit rescues are retired.

## V78 Raw FX Dollar-Consensus Event-Time Result

V78 tested a materially different joint input: EURUSD and USDJPY had to agree on
dollar direction before an XAU event-time catch-up candidate existed. Its source
audit covered `216` frozen symbol-months, `157,824` hourly rows, and `608,967,406`
declared ticks through June 2024. Outcome-blind calibration registered `1,000`
policies and selected a strict one-second consensus policy at `37/44 =
0.840909/day`, with 21 long and 16 short candidates.

Development resolved `613` trades over `723` eligible weekdays
(`0.847856/day`), split `322` long and `291` short. Base/stress net was USD
`-406.33/-452.66`; base/stress PF was `0.3394/0.3023`; first/second-half stress
PF was `0.2499/0.3410`; no month was positive; winner-removed stress net was USD
`-474.61`; stressed DD was USD `454.91`; and bootstrap p-value was `1.0`.

Decision: `V78_DEVELOPMENT_FAIL_TERMINAL`. Contract SHA-256:
`92dea393027f32e6d9e0e05220033fd63aa777f027b9f1c650ec6bb9485db091`.
Later stages remain sealed. No event threshold or execution rescue is allowed.
One fixed direction inversion may begin only on the unopened July 2021 period;
after that test, the raw FX-consensus family is terminal in both directions.

## V72 Raw XAG-to-XAU Event-Time Catch-Up Result

V72 introduced a materially new causal input: raw, synchronized Dukascopy
XAGUSD quote movement compared with only already-known XAUUSD quotes. Its source
audit validated 144 frozen symbol-month manifests, 105,216 hourly rows, and
370,219,394 declared ticks from July 2018 through June 2024. Outcome-blind July
2018 calibration registered exactly 1,000 policies and selected a one-second,
4.0 bps XAG move, 2.5 bps innovation, 0.50 response-ratio, five-quote policy at
17/21 eligible weekdays (`0.809524/day`).

Development resolved `693` trades over `745` eligible weekdays
(`0.930201/day`), split `315` long and `378` short. Base/stress net was USD
`-491.63/-542.61`; base/stress PF was `0.2973/0.2646`; first/second-half stress
PF was `0.2293/0.2892`; no month was positive; winner-removed stress net was USD
`-561.59`; stressed DD was USD `543.21`; and bootstrap p-value was `1.0`.

Decision: `V72_DEVELOPMENT_FAIL_TERMINAL`. Contract SHA-256:
`1f95f6442f037aa71b7c33886aa56722cefbab5d485c1285dd10127a1003cc90`.
Confirmation, validation, and exam remain sealed. The same-direction catch-up
interpretation, thresholds, horizon, response rule, and execution are retired.
The persistent, directionally symmetric loss permits one new preregistered
anti-signal hypothesis, but that successor must keep the event policy fixed,
invert direction exactly once, and begin only in the unopened July 2021 period.

## Routes Not Counted As Solutions

- Splitting one position into several tickets does not create independent
  opportunities or additional ML labels.
- Pyramiding the frozen Core changes its risk and is not additive edge.
- Forcing a minimum number of daily entries replaces evidence with a quota.
- Selecting a mirror, horizon, or threshold after viewing the same outcomes is
  overfitting.
- Training ML on frequent losing candidates cannot manufacture positive
  expectancy.

The active V24.1 and V26 forward collectors continue independently. Their
untouched evidence is complementary to, not replaced by, the next historical
mechanism campaign.
