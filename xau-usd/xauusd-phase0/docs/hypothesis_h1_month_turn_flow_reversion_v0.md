# H1 Month-Turn Flow Reversion v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 month-turn flow unwind / mean reversion
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-96
Expected median hold hours: 2-8
Expected decisions per week: 0-10, concentrated near month-end and month-start windows
Timeframe diversification qualifies: yes
Expected trade count per year: 30-450
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-80%
Expected worst single month: -8R to -30R
Expected max consecutive zero months: 5
Expected R-multiple distribution: month-turn overextension losses near -1R with 1.35R recoveries when flow-driven stretches unwind.
Hypothesis SHA256: pending registration
Expert: `h1_month_turn_flow_reversion_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, demo attachment, or live execution.

## Mechanical Definition

This candidate tests whether month-end and month-start flow pressure in XAUUSD mean-reverts after short H1 overextensions. It is the opposite mechanism of `h1_month_turn_flow_continuation_v0`, which was rejected first-pass and must not be tuned in place.

Month-turn window:

```text
month_day <= 4 or month_day >= 25
decision hour UTC in {07, 11, 15, 19}
```

Long setup:

```text
H1 24-bar log return <= -0.0030
H1 6-bar log return <= -0.0010
close - EMA21 <= -0.25 * H1 ATR(14)
close - EMA50 >= -2.75 * H1 ATR(14)
current H1 candle closes bearish
current H1 close location <= 0.38
```

Short setup:

```text
H1 24-bar log return >= +0.0030
H1 6-bar log return >= +0.0010
close - EMA21 >= +0.25 * H1 ATR(14)
close - EMA50 <= +2.75 * H1 ATR(14)
current H1 candle closes bullish
current H1 close location >= 0.62
```

Execution:

```text
Entry: market at signal H1 close
Stop: 0.95 * H1 ATR(14)
Target: 1.35R
Time stop: 8 H1 bars
Duplicate control: maximum one signal per UTC day per direction
```

## Expected Behavior

The strategy should capture temporary exhaustion near month-end/month-start when positioning, benchmark, or liquidity flows push XAU too far intraday and then partially unwind. It should not require a static level or breakout-retest structure.

## Why This Hypothesis Should Exist

The month-turn continuation candidate produced adequate sample size and some Capital.com/Pepperstone positive pockets but failed cross-broker PF strength. Testing a reversion mechanism under the same calendar-flow family is a distinct hypothesis, not a filter added to the failed continuation version.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, or if cost sensitivity fails. Do not tune v0 after results are known.
