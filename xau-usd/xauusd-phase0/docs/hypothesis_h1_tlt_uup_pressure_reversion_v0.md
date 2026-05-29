# H1 TLT/UUP Pressure Reversion v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 traded ETF rates/dollar pressure reversion
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-96
Expected median hold hours: 2-8
Expected decisions per week: 0-8 during TLT/UUP pressure dislocations
Timeframe diversification qualifies: yes
Expected trade count per year: 80-900
Expected cost-adjusted PF: 1.05-1.60
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: TLT/UUP pressure reversions should produce many small losses, clustered 1.40R winners after XAU temporarily moves against traded rates/dollar pressure, and no single-trade concentration.
Hypothesis SHA256: pending registration
Expert: `h1_tlt_uup_pressure_reversion_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses public Yahoo daily OHLCV proxies for:

- `TLT`: long-duration Treasury ETF, used as a traded rates-duration proxy.
- `UUP`: US dollar bull ETF, used as a traded dollar proxy.

Features are shifted by one completed daily observation before merging into XAU H1 bars.

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
XAU H1 12-bar return <= -0.0015
XAU H1 6-bar return <= +0.0005
XAU H1 24-bar return >= -0.0250
EMA50 distance >= -2.5 ATR
current H1 candle closes bullish
current H1 close location >= 0.58
```

Gold-negative pressure is symmetric:

```text
gold_pressure_5d <= -0.0060
abs(gold_pressure_z126) >= 0.35
gold_pressure_abs_percentile252 >= 0.55
```

Short setup:

```text
gold-negative pressure is active
XAU H1 12-bar return >= +0.0015
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return <= +0.0250
EMA50 distance <= +2.5 ATR
current H1 candle closes bearish
current H1 close location <= 0.42
```

Execution:

```text
Entry: market at signal bar close
Stop: 0.95 x H1 ATR(14)
Target: 1.40R
Time stop: 8 H1 bars
Duplicate control: maximum one signal per UTC day per direction
Decision hours: 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, 21:00 UTC
```

## Expected Behavior

The strategy should capture temporary XAU disagreement with traded rates/dollar ETF pressure. It should not require support/resistance levels, round numbers, breakout/retest mechanics, or unshifted macro data.

## Why This Hypothesis Should Exist

Gold often responds to both duration/rates and the US dollar. FRED macro versions use official daily observations, but traded ETFs may reveal market-implied pressure differently. If TLT is rising while UUP is falling, XAU weakness may be a short-lived dislocation; if TLT is falling while UUP is rising, XAU strength may be vulnerable to reversal.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if TLT/UUP features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
