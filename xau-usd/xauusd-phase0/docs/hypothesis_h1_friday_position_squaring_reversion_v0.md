# H1 Friday Position-Squaring Reversion v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Friday position-squaring / H1 reversion
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 18-72
Expected median hold hours: 1.5-6
Expected decisions per week: 0-2 near Friday US-session windows
Timeframe diversification qualifies: yes
Expected trade count per year: 50-350
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-75%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Friday position squaring should create sparse but repeatable reversions after one-day directional extensions; reject if strength is one-broker only or driven by a few end-of-week outliers.
Hypothesis SHA256: pending registration
Expert: `h1_friday_position_squaring_reversion_v0`
Status: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate tests whether XAUUSD tends to mean-revert during Friday US-session windows after a directional 24-hour H1 move, as discretionary and institutional flows reduce exposure before the weekend. It is not a retest, round-number, macro, ETF-flow, COT, futures-basis, or general session impulse rule.

Features are computed only from completed H1 bars:

- H1 ATR(14)
- H1 EMA(50)
- H1 log return over 6 and 24 completed H1 bars
- current H1 candle close location
- distance from EMA50 in ATR units

Decision timestamps are fixed before testing:

```text
Friday only
13:00, 14:00, 15:00, 16:00, 17:00, 18:00 UTC
```

Long setup:

```text
H1 return over 24 bars <= -0.0040
H1 return over 6 bars <= -0.0015
close is not more than 2.0 ATR below EMA50
current H1 candle closes bearish
current H1 close location <= 0.38
```

Short setup:

```text
H1 return over 24 bars >= +0.0040
H1 return over 6 bars >= +0.0015
close is not more than 2.0 ATR above EMA50
current H1 candle closes bullish
current H1 close location >= 0.62
```

Execution model:

```text
Entry: market at signal bar close
Stop: 0.95 x H1 ATR(14)
Target: 1.25R
Time stop: 6 H1 bars
Duplicate control: maximum one signal per ISO week per direction
```

## Expected Behavior

This candidate should only pass if Friday position-squaring creates a cross-broker tendency for one-day extremes to unwind during the Friday US session.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by Friday timing plus position-squaring, not by generic mean reversion.

## Why This Hypothesis Should Exist

Gold can experience position reduction into the weekend when a large one-day move has already occurred. This v0 tests whether that calendar/liquidity behavior creates a short mean-reversion window during Friday US-session hours.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one month, or a few Friday outliers.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the Friday window, return thresholds, stop size, target, or frequency rule after seeing this v0 result.
