# Claude Review Prompt - A3 Soft Retest V2 Candidate

You are reviewing an algo-trading repo change for account `1033669`, XAUUSD only. Please act as a strict independent trading-system reviewer. Do not rubber-stamp. Prioritize leakage, overfit, insufficient validation, implementation mistakes, unsafe deployment assumptions, and any reason this should not be attached for demo trading yet.

## Context

We found and hash-locked a new A3 signal-quality candidate:

`A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2`

The candidate is not live and is not attached. It is currently locked only for fresh validation. A3 remains paused.

## Candidate Rule

Start from the same raw `breakout_retest` would-signal. Keep the signal only when all checks pass:

```text
bars_after_break = retest_index - break_index
1 <= bars_after_break <= 15

retest_atr = average M5 high-low range over the 14 completed bars ending before the retest bar

LONG:
  retest.close >= level_price + 0.05 * retest_atr
  confirmation.close > level_price
  confirmation close location >= 0.60

SHORT:
  retest.close <= level_price - 0.05 * retest_atr
  confirmation.close < level_price
  confirmation close location <= 0.40

confirmation body / confirmation range >= 0.45
```

Fixed exit remains `1.50R`. One virtual position per candidate. No round-family promotion. No session-only filter. No exit-management change mixed into this candidate.

## Evidence To Review

Main locked candidate doc:

`xau-usd/xauusd-phase1/docs/A3_SIGNAL_QUALITY_V2_SOFT_RETEST_W15_B45_C60_RCM05_2026_06_18.md`

Main discovery report:

`xau-usd/xauusd-phase1/outputs/reports/A3_SIGNAL_QUALITY_EXTENDED_DISCOVERY_V2_CANDIDATE_2026_06_18.md`

Discovery runner:

`xau-usd/xauusd-phase1/scripts/run_a3_signal_quality_extended_discovery.py`

Baseline correction:

`xau-usd/xauusd-phase1/scripts/run_a3_signal_quality_offline_discovery.py`

Focused tests:

`xau-usd/xauusd-phase1/tests/test_a3_signal_quality_extended_discovery.py`
`xau-usd/xauusd-phase1/tests/test_a3_signal_quality_offline_discovery.py`

Relevant commits:

```text
4ea352f Lock A3 soft retest V2 candidate
6bcfcae Correct A3 SQ03 baseline comparisons
daaa44a Run A3 signal quality offline discovery
e5e925c Lock A3 signal quality diagnostic sweep
c257dd6 Lock A3 signal quality addendum
3a42a4c Prepare A3 signal quality SQ-00
```

## Reported Discovery Metrics

Offline historical discovery on phase0 Dukascopy XAUUSD bars, `2025-01-02` through `2025-07-01`:

| Metric | B0 raw one-position baseline | V2 candidate |
| --- | ---: | ---: |
| Accepted signals | 1453 | 586 |
| Signal retention | 100.00% | 40.33% |
| Opened virtual trades | 885 | 490 |
| Trade retention vs B0 | 100.00% | 55.37% |
| Median weekly trade retention | 100.00% | 59.38% |
| Profit factor | 1.2484 | 1.9186 |
| Expectancy | +0.1356R | +0.4031R |
| Win rate | 45.42% | 56.12% |
| Bad-signal loss share | 50.10% | 35.81% |
| Bad-signal loss share improvement | 0.00% | 28.52% |
| Max consecutive losses | 14 | 6 |
| Max drawdown | 20.5R | 7.5R |
| Weeks with at least 15 trades | 23 | 20 |
| Long / short opened trades | 499 / 386 | 281 / 209 |
| H1 regimes represented | rising and falling | rising and falling |

Estimated demo-start replay, `2026-06-01 15:10:00` to `2026-06-18 03:00:00`, using read-only exported MT5 bars and actual XAUUSD conversion:

```text
candidate opened trades: 38
estimated PnL: about +1001 AED
net R: +27.0R
win rate: 68.42%
PF: 3.25
max drawdown: 3.0R
max consecutive losses: 3
```

Important caveat: the June 2026 demo-start replay is too small for final validation and cannot be used as promotion evidence.

## Known Boundaries

- A3 is still paused.
- No MT5 runtime/profile/preset/order/position/broker action should be made from this evidence alone.
- Discovery data must not be reused as final promotion evidence.
- We need a fresh validation window before any attach/trading.
- The current candidate is a Python/discovery lock, not an MQL EA implementation yet.

## Review Questions

Please answer in a structured review:

1. Is the candidate definition logically sound and deterministic from completed bars only?
2. Do you see any lookahead, leakage, timestamp/indexing bug, ATR-window ambiguity, or mismatch between docs and code?
3. Is the baseline correction in `run_a3_signal_quality_offline_discovery.py` correct: B0 means one-position B0, trade retention is versus B0 opened trades, and median weekly retention is gated?
4. Are the discovery metrics enough to justify locking this as a V2 candidate for fresh validation?
5. Are there signs of overfitting from the selected thresholds `15`, `0.45`, `0.60`, `0.05 ATR`?
6. Should the June 2026 demo-start replay be treated only as supporting context, not validation?
7. What additional tests should Codex add before MQL implementation?
8. What exact MQL parity checks are required before A3 attach?
9. What fresh validation gates must pass before demo trading on account `1033669`?
10. Give a verdict:
    - `NO-GO`: do not implement/attach
    - `BUILD_ONLY`: implement observer/shadow only, no broker action
    - `SHADOW_VALIDATE`: attach shadow-only after safeguards
    - `DEMO_TRADE_READY`: broker-action demo attach may proceed after owner authorization

Be conservative. If anything is uncertain, call it out as a blocker or required follow-up.
