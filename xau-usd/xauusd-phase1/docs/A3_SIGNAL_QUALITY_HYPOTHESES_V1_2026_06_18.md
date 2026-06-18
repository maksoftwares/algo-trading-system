# A3 Signal Quality Hypotheses V1 - 2026-06-18

Status: `PRE_REGISTERED_LOCK_PENDING_MANIFEST`

Scope:

- Account: `1033669`
- Symbol: `XAUUSD`
- Family: breakout-retest
- Decision timeframe: `M5`
- Runtime mode: shadow only
- Broker action: prohibited
- Existing A3 lanes `933200`, `933300`, and `933400`: remain paused
- Profit-lock manager: remains dry-run/disarmed

This document pre-registers the A3 signal-quality repair hypotheses before any new shadow observer is implemented. Thresholds in this file are frozen for the V1 forward window. Do not inspect forward results and then revise these rules under the same version.

## Baseline Invariants

All candidates in this V1 round use these invariants:

- Reward target: `1.50R`.
- Stop distance: `max(raw stop, broker stops level + 5 points, 3 x current spread, 300 XAU points)`.
- Measured spread cap: `75 points`.
- Post-floor estimated cost_R: `<= 0.15R`.
- Session: Dubai `16:00-19:59` using `TimeGMT()+240` minutes.
- Broker-server hour must be logged in parallel and mapped back to the Dubai session window.
- One virtual breakout-family position at a time.
- No real `OrderSend`.
- No `CTrade`.
- No SL/TP modification.
- Missing indicator, missing timestamp, mixed higher-timeframe state, or unavailable market data blocks the candidate and is logged.

## Primary Candidate

Candidate id: `A3_SQ_COMBINED_V1`

Promotion eligibility: yes, this is the only promotion-eligible candidate in this V1 round.

Definition:

- Apply all baseline invariants.
- Require the strict MTF alignment rule.
- Require the strict retest confirmation rule.
- Log every blocked reason and every accepted virtual trade.

## Diagnostic Ablation A

Candidate id: `A3_SQ_MTF_ONLY_V1`

Promotion eligibility: no. Diagnostic only.

Use the baseline breakout-retest entry logic plus strict MTF alignment.

Long requires all:

```text
D1 close[1] > D1 EMA20[1] > D1 EMA50[1]
H1 EMA20[1] - H1 EMA20[4] >= +50 XAU points
M15 EMA20[1] - M15 EMA20[4] >= +50 XAU points
```

Short requires all:

```text
D1 close[1] < D1 EMA20[1] < D1 EMA50[1]
H1 EMA20[1] - H1 EMA20[4] <= -50 XAU points
M15 EMA20[1] - M15 EMA20[4] <= -50 XAU points
```

Rules:

- Completed bars only.
- Any unavailable indicator blocks the candidate.
- Mixed D1 bias blocks the candidate.
- Neutral H1 or M15 slope blocks the candidate.
- No per-direction exceptions.

## Diagnostic Ablation B

Candidate id: `A3_SQ_RETEST_ONLY_V1`

Promotion eligibility: no. Diagnostic only.

Use baseline session and cost logic plus this strict retest rule:

```text
Break close beyond level >= 0.30 x M5 ATR14
First retest only
Retest occurs 1-5 completed M5 bars after break
Retest penetration beyond level <= 0.15 x M5 ATR14
Retest closes back on breakout side by >= 0.05 x M5 ATR14
Confirmation candle body/range >= 0.60
Long confirmation close location: (close-low)/(high-low) >= 0.80
Short confirmation close location: (close-low)/(high-low) <= 0.20
Opposite wick <= 0.25 x candle range
Long confirmation close > retest high
Short confirmation close < retest low
Invalidating close through the level before confirmation = reject
```

## Multiplicity Rule

- `A3_SQ_COMBINED_V1` is primary.
- `A3_SQ_MTF_ONLY_V1` and `A3_SQ_RETEST_ONLY_V1` are explanatory diagnostics.
- Do not promote an ablation if the primary fails.
- Do not change thresholds during the forward window.
- Session and cost are baseline safety invariants, not optimization knobs in this round.
- Do not repurpose weak-family impulse-veto thresholds for this breakout-family hypothesis.

## Shadow Execution Evidence Contract

The future shadow observer must use tick-level virtual execution:

- Virtual long entry: observed ask on first eligible tick after signal.
- Virtual short entry: observed bid on first eligible tick after signal.
- SL/TP: baseline post-floor geometry.
- Evaluation: every tick.
- Exit: first actual tick crossing SL or TP.
- Log: virtual fill, MFE, MAE, exit, net R, measured spread, estimated cost_R, broker-server time, Dubai time, candidate id, hypothesis version, and hypothesis hash.
- One virtual position per candidate.
- No broker-action API calls.

Bar replay may be used for diagnostics, but quarantined bar replay is not promotion evidence for this hypothesis.

## Minimum Shadow Sample

The primary candidate must accumulate all of:

- At least `100` closed virtual trades.
- At least `20` active market days.
- At least `4` calendar weeks.
- At least `25` long and at least `25` short trades unless a new one-sided hypothesis is separately registered.
- At least `3` distinct weeks with at least `15` trades.

## Performance Gates

All gates must pass before any broker-action proposal:

- Win rate `>= 50%`.
- Profit factor `>= 1.30` after measured spread/cost.
- Net expectancy `>= +0.15R` per trade.
- P95 cost_R `<= 0.15R`.
- No accepted trade cost_R `> 0.15R`.
- Max consecutive losses `<= 8`.
- Max drawdown `<= 8R`.
- Largest single trade contribution `<= 10%` of net PnL.
- Top five trades contribution `<= 40%` of net PnL.
- No single day contributes more than `30%` of positive net PnL.
- At least `3` of `4` weekly buckets have PF `>= 1.0`.
- Session compliance `100%`.
- Duplicate family entries `0`.
- Unknown or missing indicator decisions are blocked and separately reported.

## Parity Gates

Before broker action is proposed:

- MQL5 observer decisions must match an independent Python reproduction on at least `99%` of evaluated completed-bar decisions.
- All mismatches must be classified.
- There must be no unresolved lookahead or data-timestamp mismatch.
- Virtual entry, SL, and TP calculations must match a second implementation within one symbol point.

## Reactivation Boundary

This hypothesis does not authorize reactivation.

Broker action can only be reconsidered after:

1. The shadow candidate passes all gates.
2. Independent reviewer signoff is recorded.
3. Owner approves the exact version and hash.
4. Compile proof shows `0 errors, 0 warnings`.
5. A profile backup is taken.
6. Zero A3 exposure baseline is verified.
7. One new lane only is attached.
8. Fixed lot remains `0.01`.
9. A micro demo pilot limit is explicitly defined.
10. First-order and first-day reconciliation are complete.
11. No other A3 breakout lane is active.

Until then, effective A3 runtime authorization remains `A3_ENTRY_LANES_PAUSED`.
