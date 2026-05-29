# H1 TLT/SHY Duration Rotation Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 traded ETF Treasury-duration rotation follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-12 during duration bid/selloff regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 70-1100
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -28R
Expected max consecutive zero months: 3
Expected R-multiple distribution: duration-rotation follow-through should show many small losses, clustered 1.50R winners when XAU confirms long-duration Treasury pressure, and no single-trade concentration.
Hypothesis SHA256: pending registration
Expert: `h1_tlt_shy_duration_rotation_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses public Yahoo daily OHLCV proxies for:

- `TLT`: long-duration Treasury ETF proxy.
- `SHY`: short-duration Treasury ETF proxy.

Features are shifted by one completed daily observation before merging into XAU H1 bars.

Duration pressure:

```text
duration_pressure_5d = log(TLT close / TLT close 5d ago) - log(SHY close / SHY close 5d ago)
duration_pressure_5d >= +0.0060
abs(duration_pressure_z126) >= 0.35
duration_pressure_abs_percentile252 >= 0.55
```

Long setup:

```text
duration pressure is positive
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
duration_pressure_5d <= -0.0060
abs(duration_pressure_z126) >= 0.35
duration_pressure_abs_percentile252 >= 0.55
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

The strategy should capture XAU confirmation in the same direction as shifted long-duration Treasury pressure versus short-duration Treasury pressure. It should not require support/resistance levels, round numbers, retest mechanics, or unshifted ETF values.

## Why This Hypothesis Should Exist

Gold can respond to real-rate and duration repricing. TLT/SHY isolates long-duration Treasury pressure from short-duration cash-like Treasury behavior more directly than the rejected TLT/UUP rates-dollar lane, so it deserves a separate locked first pass.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if TLT/SHY features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
