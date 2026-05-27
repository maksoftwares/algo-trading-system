# Next Independent Research Lane

Last updated: 2026-05-27

Overall status: DATA_CLASS_CANDIDATE_REJECTED

This document defines what can still be done while Phase 1 soak, code-freeze, and measured-cost clocks mature. It does not approve any new EA and it does not reopen rejected candidates.

## Current Finding

The current approved/provisional set is still one correlated edge family:

```text
level-and-pullback / breakout-retest
```

The project has already tested 67 tracked candidates, including non-level, H4/D1/W1, intermarket, macro-regime, volatility-regime, event-regime, AI-style fixed-state concepts, and a non-authoritative GC continuous futures daily-volume proxy. No genuinely independent candidate has passed first pass. Candidate 67, `h4_gold_futures_volume_climax_v0`, was written, SHA256-locked, synthetic-smoke PASS, unblocked with a `GC=F` daily-volume proxy, and rejected first-pass.

## Research Boundary

Allowed:

- new versioned hypotheses
- new data classes
- mechanical definitions written before testing
- SHA256 registration before any result-producing run
- one small smoke check before matrix
- first-pass rejection without tuning

Forbidden:

- tuning rejected v0 candidates in place
- relabeling same-family retests as diversification
- lowering Phase 0 gates because an idea is low frequency
- starting EA code for a candidate before Phase 0 PASS
- using Phase 2 paper-mode as a way to rescue failed Phase 0 logic

## Current Data Constraint

The existing local evidence set is strong for:

- XAUUSD OHLC bars across Capital.com, Pepperstone, and Dukascopy
- EURUSD/USDJPY proxy bars
- XAGUSD relative bars
- public daily or weekly macro proxies from FRED/CFTC where already acquired
- deterministic event slots

The current evidence set is weak or missing for:

- real exchange-traded gold futures volume
- COMEX order-flow or depth
- options skew beyond coarse GVZ-style daily volatility
- broker-specific execution/fill slippage
- live news surprise magnitude
- intraday Treasury/real-yield shocks

That means the next independent candidate should either be:

```text
A. a genuinely new data-class hypothesis, or
B. a current-data hypothesis with a clearly different mechanism from breakout/retest and from rejected v0 families.
```

## Candidate Triage

| Candidate idea | Data class | Current-data feasible | Independence | Recommendation |
| --- | --- | --- | --- | --- |
| `h4_us_session_liquidity_reversal_v0` | XAU OHLC only | Yes | Medium | REJECTED_FIRST_PASS; do not tune v0. |
| `h4_gold_futures_volume_climax_v0` | GC continuous futures daily-volume proxy | Yes | High | REJECTED_FIRST_PASS using Yahoo `GC=F`; primary CME/order-flow data remains a separate future lane. |
| `h1_real_yield_intraday_shock_v0` | Intraday rates/real-yield proxy | No | High | Defer until intraday rate data exists. |
| `h1_news_surprise_repricing_v0` | Actual economic surprise values | No | High | Defer until event surprise data exists. |
| `d1_macro_liquidity_regime_v0` | Central-bank liquidity and USD funding proxies | Partial | High | Possible later, but likely slow-moving and low trade count. |
| `xau_options_skew_reversal_v0` | Gold options skew | No | High | Defer until options-skew source exists. |

## Recommended Immediate Candidate

The latest current-data candidate was:

```text
h4_us_session_liquidity_reversal_v0
```

Mechanism:

```text
During the US cash session, XAU sometimes makes an H4 directional liquidity run that exhausts rather than continues.
The candidate fades only unusually large H4 moves occurring during the US overlap/NY session, after the H4 candle closes back inside its own range.
```

Why this is not same-family:

- It does not trade retests of levels.
- It does not require a broken support/resistance level.
- It is a volatility-exhaustion reversal, not a breakout continuation.
- It uses H4 session-location and range expansion, not M5/M15 retest mechanics.

Why it is still risky:

- Similar exhaustion/reversal ideas have failed before.
- Current data lacks true volume/order-flow confirmation.
- The mechanism may be too weak after spread/cost.
- It may fail concentration or PF survival quickly, which is acceptable.

## Pre-Registration Status

Before any result-producing run, the following files now exist:

```text
docs/hypothesis_h4_us_session_liquidity_reversal_v0.md
src/phase0/strategies/h4_us_session_liquidity_reversal_v0.py
tests/test_h4_us_session_liquidity_reversal_v0.py
```

Registration, smoke, and first-pass status:

```text
Research hypothesis: REGISTERED
SHA256: 3746ce113d49c1bb1a17402fcba6bf82a8c01a95c5c07bca642da96f6589826c
Synthetic smoke: PASS
First-pass matrix: REJECTED_FIRST_PASS
Matrix trades: 378
PF cells >= 1.30: 0/9
Minimum cell trades: 32
```

## First-Pass Result

`h4_us_session_liquidity_reversal_v0` did not clear the first hard gate. It produced weakly positive returns, but no matrix cell reached PF 1.30 and six cells had fewer than 40 trades. The correct action is to reject v0 without tuning.

Required mechanical definition:

- H4 candle completes during US/NY session hours.
- H4 true range must be above a pre-defined ATR multiple.
- Candle must reject the extreme by closing back inside a defined fraction of its range.
- Entry occurs at the next H4 open or equivalent bar-open simulation.
- Stop is beyond the H4 extreme plus ATR buffer.
- Target is fixed-R, no adaptive optimization.
- Maximum one signal per symbol per day.
- No news filters unless pre-registered as fixed blackout times.

Suggested fixed first-pass parameters:

```text
H4 ATR lookback: 14
Minimum H4 true range: 1.35 x ATR14
Rejection close fraction: close back inside 35% of candle range from the extreme
Stop buffer: 0.15 x ATR14
Target: 1.35R
Time stop: 12 H4 bars
One trade per UTC day
```

These are first-pass values, not tuning handles. If this version fails, reject it and do not tune v0.

## Pass/Fail Rule

Use the same Phase 0 first-pass rule:

```text
PASS only if at least 7/9 matrix cells reach PF >= 1.30,
trade count is sufficient,
concentration gates pass,
cost sensitivity passes,
and no procedural gate is bypassed.
```

If it fails, record it as:

```text
REJECTED_FIRST_PASS
```

Then move to a new data-class candidate rather than another OHLC-only exhaustion variation.

## Better Strategic Next Move

The stronger next research move is to add a new data class before more OHLC-only attempts:

```text
Primary COMEX/CME futures volume/order-flow or options-skew data.
```

Reason:

The current OHLC/macro/intermarket search has already covered enough nearby hypotheses that another OHLC-only candidate has a low prior probability. The non-authoritative GC continuous-volume proxy also failed, so the next lift should be a higher-quality new data source rather than another local threshold idea.
