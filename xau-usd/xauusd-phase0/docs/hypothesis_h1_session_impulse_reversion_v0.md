# H1 Session Impulse Reversion v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: session impulse exhaustion / H1 mean reversion
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-96
Expected median hold hours: 2-8
Expected decisions per week: 3-20 during London/New York session windows
Timeframe diversification qualifies: yes
Expected trade count per year: 150-1200
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-70%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 2
Expected R-multiple distribution: session impulse exhaustion should create many small stopped reversals and occasional clustered 1.35R winners after overextended H1 displacement; reject if performance is one-broker only or indistinguishable from a weak pullback filter.
Hypothesis SHA256: pending registration
Expert: `h1_session_impulse_reversion_v0`
Status: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate tests whether H1 session-hour impulse bars in XAUUSD temporarily overshoot fair value and mean-revert before a larger trend continuation develops. It is not a level, retest, round-number, macro, ETF-flow, COT, or futures-basis hypothesis.

Features are computed only from completed H1 bars:

- H1 ATR(14)
- H1 EMA(21)
- H1 EMA(50)
- H1 log return over 3, 6, and 24 completed H1 bars
- current H1 candle close location
- distance from EMA21 and EMA50 in ATR units

Decision timestamps are fixed before testing:

```text
08:00, 09:00, 10:00, 14:00, 15:00, 16:00, 19:00, 20:00 UTC
Monday through Friday only
```

Long setup:

```text
H1 return over 3 bars <= -0.0015
H1 return over 6 bars <= -0.0020
H1 return over 24 bars >= -0.0180
close is at least 0.35 ATR below EMA21
close is not more than 1.25 ATR below EMA50
current H1 candle closes bearish
current H1 close location <= 0.35
```

Short setup:

```text
H1 return over 3 bars >= +0.0015
H1 return over 6 bars >= +0.0020
H1 return over 24 bars <= +0.0180
close is at least 0.35 ATR above EMA21
close is not more than 1.25 ATR above EMA50
current H1 candle closes bullish
current H1 close location >= 0.65
```

Execution model:

```text
Entry: market at signal bar close
Stop: 0.90 x H1 ATR(14)
Target: 1.35R
Time stop: 8 H1 bars
Duplicate control: maximum one signal per UTC day per direction
```

## Expected Behavior

Expected trade count: 150 to 1,200 trades per broker-window cell over the Phase 0 matrix.
Expected PF: at least 1.30 in 7/9 cells if the session impulse exhaustion edge is real.
Expected losing-month percentage: below 45%.
Expected worst month: no worse than -8R.
Expected max zero-trade months: no more than 3.
Expected R distribution: many small losses, moderate winning clusters after overextended session moves unwind.

## Why This Hypothesis Should Exist

Gold can overreact during active London/New York liquidity windows when short-horizon flows push price away from its H1 moving-value area. The thesis is that a completed H1 displacement with an extreme close location has temporarily exhausted directional pressure, creating a short mean-reversion window before the broader market chooses a new direction.

## What Would Falsify It

Reject this candidate if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any broker-window cell has fewer than 40 trades
- activity, concentration, cost-sensitivity, decile, multisymbol, intrabar, or adversarial gates fail
- strength appears in only one broker window
- the candidate only works under favorable cost assumptions

If rejected, do not tune v0 in place. Any revisit must be a new versioned hypothesis and hash-locked before testing.
