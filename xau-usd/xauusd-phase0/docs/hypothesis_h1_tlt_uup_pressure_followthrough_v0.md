# H1 TLT/UUP Pressure Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 traded ETF rates/dollar pressure follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-8 during TLT/UUP pressure regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 80-900
Expected cost-adjusted PF: 1.05-1.60
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: TLT/UUP pressure follow-through should have many small losses, clustered 1.50R winners when XAU confirms traded rates/dollar pressure, and no single-trade concentration.
Hypothesis SHA256: pending registration
Expert: `h1_tlt_uup_pressure_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate tests the paired interpretation of `h1_tlt_uup_pressure_reversion_v0`: if XAU does not profitably fade TLT/UUP pressure dislocations, it may instead continue in the same direction once H1 confirms.

Gold-supportive pressure:

```text
gold_pressure_5d = log(TLT close / TLT close 5d ago) - log(UUP close / UUP close 5d ago)
gold_pressure_5d >= +0.0060
abs(gold_pressure_z126) >= 0.35
gold_pressure_abs_percentile252 >= 0.55
```

Long setup:

```text
gold-supportive pressure is active
XAU close > EMA50
EMA21 >= EMA50
XAU H1 12-bar return >= +0.0015
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return <= +0.0250
current H1 candle closes bullish
current H1 close location >= 0.60
```

Short setup:

```text
gold_pressure_5d <= -0.0060
abs(gold_pressure_z126) >= 0.35
gold_pressure_abs_percentile252 >= 0.55
XAU close < EMA50
EMA21 <= EMA50
XAU H1 12-bar return <= -0.0015
XAU H1 6-bar return <= +0.0005
XAU H1 24-bar return >= -0.0250
current H1 candle closes bearish
current H1 close location <= 0.40
```

Execution:

```text
Entry: market at signal bar close
Stop: 1.05 x H1 ATR(14)
Target: 1.50R
Time stop: 10 H1 bars
Duplicate control: maximum one signal per UTC day per direction
Decision hours: 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, 21:00 UTC
```

## Expected Behavior

The strategy should pass only if XAU confirmation in the same direction as shifted TLT/UUP pressure has cross-broker persistence after costs. It does not use support/resistance levels, round numbers, retest mechanics, or unshifted ETF values.

## Why This Hypothesis Should Exist

The TLT/UUP reversion interpretation failed with healthy trade count and negative PF across all broker windows. This paired candidate tests whether the same traded pressure data points to continuation rather than dislocation fade.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if TLT/UUP features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
