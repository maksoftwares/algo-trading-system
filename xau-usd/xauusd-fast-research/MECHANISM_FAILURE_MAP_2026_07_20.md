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
