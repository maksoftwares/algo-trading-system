# H1 TIP/IEF Real-Yield Rotation Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 traded ETF real-yield rotation follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-8 during TIP/IEF rotation regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 60-800
Expected cost-adjusted PF: 1.05-1.60
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: TIP/IEF real-yield rotation follow-through should have many small losses, clustered 1.50R winners when XAU confirms inflation-protection or nominal-duration rotation, and no single-trade concentration.
Hypothesis SHA256: pending registration
Expert: `h1_tip_ief_real_yield_rotation_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses public Yahoo daily OHLCV proxies for:

- `TIP`: inflation-protected Treasury ETF / real-yield and inflation-protection proxy.
- `IEF`: nominal 7-10 year Treasury ETF / intermediate-duration Treasury proxy.

Features are shifted by one completed daily observation before merging into XAU H1 bars.

Inflation-protection rotation:

```text
real_yield_rotation_5d = log(TIP close / TIP close 5d ago) - log(IEF close / IEF close 5d ago)
real_yield_rotation_5d >= +0.0035
abs(real_yield_rotation_z126) >= 0.35
real_yield_rotation_abs_percentile252 >= 0.55
```

Long setup:

```text
inflation-protection rotation is active
XAU close > EMA50
EMA21 >= EMA50
XAU H1 12-bar return >= +0.0015
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return <= +0.0250
current H1 candle closes bullish
current H1 close location >= 0.60
```

Nominal-duration rotation is symmetric:

```text
real_yield_rotation_5d <= -0.0035
abs(real_yield_rotation_z126) >= 0.35
real_yield_rotation_abs_percentile252 >= 0.55
```

Short setup:

```text
nominal-duration rotation is active
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

The strategy should capture XAU confirmation in the same direction as shifted inflation-protected versus nominal Treasury rotation. It should not require support/resistance levels, round numbers, retest mechanics, or unshifted ETF values.

## Why This Hypothesis Should Exist

Gold is sensitive to real-yield and inflation-protection pressure. TIP versus IEF is a traded ETF proxy that measures a different rates axis from the failed TLT/UUP and SPY/TLT candidates. If XAU confirms the same rotation intraday, the move may persist for several H1 bars.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if TIP/IEF features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
