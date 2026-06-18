# A3 Signal Quality Diagnostic Sweep V1 - 2026-06-18

Status: `LOCKED`

Scope:

- Account: `1033669`
- Symbol: `XAUUSD`
- Family under repair: breakout-retest only
- Runtime mode: offline discovery first, then shadow-only only if discovery is promising
- Broker action: prohibited
- Existing A3 lanes `933200`, `933300`, and `933400`: remain paused
- Profit-lock manager: remains dry-run/disarmed

This document pre-registers the diagnostic sweep used to find a frequency-preserving signal-quality repair candidate. It is hypothesis-generation only. It is not promotion evidence, not broker-action authorization, and not permission to attach an MT5 observer.

## Discovery Versus Validation

- Diagnostic sweep results may select no candidate.
- Diagnostic sweep results may select one candidate for a future locked V2 hypothesis.
- Diagnostic sweep results may not be reused as V2 promotion evidence.
- If a diagnostic wins, stop using the discovery window, lock a new `A3_SIGNAL_QUALITY_V2_<candidate>.md`, and validate on a fresh window.
- Locked V1 candidates must be implemented exactly as written in `A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md`; do not relax V1 to recover frequency.

## Shared Base Event

Every candidate starts from the same raw `breakout_retest` would-signal event.

For every raw event, log:

- `signal_id`
- account
- symbol
- base family
- direction
- break bar time
- retest bar time
- confirmation bar time
- level price
- Dubai session bucket
- broker-server time bucket
- all candidate keep/block decisions
- block reason if rejected

Rejected rows must stay in the ledger. Do not hide blocked signals.

## Baselines

### `B0_RAW_ALL_SESSION`

Definition:

- Current raw breakout-retest would-signal.
- No new trend filter.
- No new retest-quality filter.
- All Dubai session buckets logged.
- Current stop-floor and cost calculations retained.

Role: frequency and quality reference.

### `B1_EVENING_BASELINE`

Definition:

- `B0_RAW_ALL_SESSION`.
- Dubai session restricted to `16:00-19:59`.

Role: apples-to-apples reference for locked V1, whose session is already fixed.

## Frequency-Preserving Diagnostics

### `F_LOOSE_CT_VETO`

Block only strongly counter-trend H1 signals.

Completed-bar definition:

```text
h1_slope_points =
    (H1 EMA20[1] - H1 EMA20[4]) / point

LONG blocked only when h1_slope_points <= -50
SHORT blocked only when h1_slope_points >= +50
Neutral or weak slope is kept.
Unavailable H1 data = DATA_UNAVAILABLE.
```

Expected frequency hypothesis: `70-90%` of `B0_RAW_ALL_SESSION`.

### `F_H1_ALIGN`

Definition:

```text
LONG:
  H1 close[1] > H1 EMA20[1]
  AND H1 EMA20[1] > H1 EMA20[4]

SHORT:
  H1 close[1] < H1 EMA20[1]
  AND H1 EMA20[1] < H1 EMA20[4]
```

No minimum magnitude beyond correct sign.

Expected frequency hypothesis: `50-70%` of `B0_RAW_ALL_SESSION`.

### `F_H1_M15_ALIGN`

Definition:

- Apply `F_H1_ALIGN`.
- Also require the same completed-bar sign logic on M15:

```text
LONG:
  M15 close[1] > M15 EMA20[1]
  AND M15 EMA20[1] > M15 EMA20[4]

SHORT:
  M15 close[1] < M15 EMA20[1]
  AND M15 EMA20[1] < M15 EMA20[4]
```

Expected frequency hypothesis: `35-55%` of `B0_RAW_ALL_SESSION`.

### `F_RETEST_LIGHT`

Keep the baseline break requirement and add moderate structure only:

```text
Break close beyond level >= 0.30 x M5 ATR14
Retest occurs within 1-10 completed M5 bars after the break
No completed M5 candle closes through the invalid side of the level between break and confirmation
Confirmation candle body/range >= 0.40

LONG close location:
  (close - low) / (high - low) >= 0.65

SHORT close location:
  (close - low) / (high - low) <= 0.35

Confirmation closes on the breakout side of the level
```

Strict penetration and wick limits are intentionally not part of this diagnostic.

Expected frequency hypothesis: `45-70%` of `B0_RAW_ALL_SESSION`.

### `F_LOOSE_CT_PLUS_RETEST_LIGHT`

Definition:

```text
F_LOOSE_CT_VETO
+
F_RETEST_LIGHT
```

Expected frequency hypothesis: `35-55%` of `B0_RAW_ALL_SESSION`.

## Locked V1 Candidates Included In Sweep

### `A3_SQ_MTF_ONLY_V1`

- Implement exactly as locked in `A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md`.
- Diagnostic only.
- Expected frequency hypothesis: `15-30%` of `B0_RAW_ALL_SESSION`.

### `A3_SQ_RETEST_ONLY_V1`

- Implement exactly as locked in `A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md`.
- Diagnostic only.
- Expected frequency hypothesis: `40-60%` of `B0_RAW_ALL_SESSION`.

### `A3_SQ_COMBINED_V1`

- Implement exactly as locked in `A3_SIGNAL_QUALITY_HYPOTHESES_V1_2026_06_18.md`.
- This is the only currently promotion-eligible V1 candidate.
- Expected frequency hypothesis: `5-15%` of `B0_RAW_ALL_SESSION`.

## Offline Discovery Inputs

The first discovery screen uses existing historical bars plus available 10-second position-path data. This coarse offline replay is not promotion evidence. It is only a cheap go/no-go screen before building the heavier MQL5 forward apparatus.

Required data provenance:

- input file paths;
- row counts;
- first and last timestamp per file;
- SHA256 for each input artifact;
- timezone interpretation;
- missing-data summary.

## Metrics Per Candidate

Report at minimum:

- raw base signals;
- accepted signals;
- signal retention percent versus `B0_RAW_ALL_SESSION`;
- opened virtual trades;
- virtual-trade retention percent versus `B0_RAW_ALL_SESSION`;
- closed trades;
- Dubai session buckets;
- direction counts;
- win rate;
- profit factor after executable bid/ask costs;
- net expectancy in R;
- net R;
- max drawdown in R;
- max consecutive losses;
- P50 and P95 cost_R;
- largest trade contribution;
- top-five contribution;
- best-day contribution;
- weekly PF;
- rising and falling regime coverage;
- blocked bucket expectancy;
- kept bucket expectancy;
- bad-signal loss share;
- give-back loss share.

## Frequency Floor

Any frequency-preserving future V2 candidate must satisfy all of:

```text
signal retention >= 40% of B0
virtual-trade retention >= 35% of B0
closed virtual trades >= 100
median weekly trades >= 40% of B0 median weekly trades
```

A candidate that improves PF by blocking nearly everything fails this project objective.

## V2 Registration Eligibility

A diagnostic may be selected for a future locked V2 only if the discovery window shows all of:

```text
signal retention >= 40%
closed virtual trades >= 100
PF >= 1.20
expectancy >= +0.10R
PF improvement versus B0 >= +0.15
  OR expectancy improvement versus B0 >= +0.05R
blocked bucket expectancy worse than kept bucket
bad-signal loss share improves by >=20% relative
no concentration breach
both rising and falling regimes represented
```

These are V2 registration eligibility gates only. They are not broker-action gates.

## Loss Attribution

Use fixed `1.50R` exits for every entry-filter candidate. Do not mix entry repair with exit-management changes.

For losing virtual trades, classify by path order:

```text
BAD_SIGNAL:
  -0.50R is reached before +0.50R
  OR +0.50R is never reached before final SL

MIXED:
  +0.50R is reached first
  but maximum favorable excursion remains below +0.75R
  and the trade later loses

BAD_EXIT_GIVEBACK:
  +0.75R is reached before -0.50R
  and the trade later closes at <= 0R

NEAR_TP_GIVEBACK:
  +1.25R is reached
  TP at +1.50R is not reached
  trade later closes at <= 0R
```

Exit-management research is Stage 2 and must not be folded into this entry-filter discovery sweep.

## Required SQ-03 Output

The offline discovery screen must produce:

- candidate frequency-quality table;
- loss-attribution table;
- data manifest;
- blocked-versus-kept expectancy table;
- session and direction stratification;
- regime coverage;
- concentration checks;
- explicit decision: `STOP_NO_CANDIDATE` or `PROCEED_TO_FORWARD_APPARATUS_CANDIDATE_<id>`.

If no candidate clears the V2 registration eligibility bar, A3 stays paused and the MQL5 forward observer apparatus is not built.

## No-Go Conditions

A3 remains paused if any one is true:

- any A3 entry lane is proposed for reactivation;
- round-retest is proposed for promotion or combination;
- signal retention is below `40%` for the candidate;
- virtual-trade retention is below `35%` for the candidate;
- sample minimum is not reached;
- only one market regime is represented;
- PF or expectancy gate fails;
- blocked bucket is not worse than kept bucket;
- bad-signal loss share is not materially improved;
- concentration gate fails;
- any threshold is changed after this lock;
- discovery results are reused as promotion evidence.

## Reactivation Boundary

This diagnostic sweep does not authorize live trading, demo broker action, profile edits, preset arming, observer attachment, lot changes, SL/TP changes, or account changes. A3 remains paused.
