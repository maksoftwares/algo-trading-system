# H1 XLP/XLY Consumer Rotation Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 traded ETF consumer-defensive versus consumer-discretionary follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-12 during consumer defensive/risk-appetite rotation regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 60-1000
Expected cost-adjusted PF: 1.05-1.60
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -28R
Expected max consecutive zero months: 3
Expected R-multiple distribution: consumer-sector rotation follow-through should show many small losses, clustered 1.50R winners when XAU confirms defensive or risk-on pressure, and no single-trade concentration.
Hypothesis SHA256: pending registration
Expert: `h1_xlp_xly_consumer_rotation_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses public Yahoo daily OHLCV proxies for:

- `XLP`: consumer staples ETF proxy.
- `XLY`: consumer discretionary ETF proxy.

Features are shifted by one completed daily observation before merging into XAU H1 bars.

Consumer defensive rotation pressure:

```text
consumer_rotation_5d = log(XLP close / XLP close 5d ago) - log(XLY close / XLY close 5d ago)
consumer_rotation_5d >= +0.0090
abs(consumer_rotation_z126) >= 0.35
consumer_rotation_abs_percentile252 >= 0.55
```

Long setup:

```text
consumer defensive pressure is positive
XAU close > EMA50
EMA21 >= EMA50
XAU H1 12-bar return >= +0.0015
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return <= +0.0250
current H1 candle closes bullish
current H1 close location >= 0.60
```

Risk-on discretionary pressure is symmetric:

```text
consumer_rotation_5d <= -0.0090
abs(consumer_rotation_z126) >= 0.35
consumer_rotation_abs_percentile252 >= 0.55
```

Short setup:

```text
consumer defensive pressure is negative
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

The strategy should capture XAU follow-through when consumer staples outperform discretionary stocks and XAU confirms higher, or when discretionary risk appetite dominates and XAU confirms lower.

## Why This Hypothesis Should Exist

XLP versus XLY is mechanically distinct from retest, credit-risk, commodity, metals, rates-dollar, COT, GLD-flow, and XLU/XLK lanes. It tests whether consumer-sector defensive rotation carries information about gold demand that survives after H1 XAU confirmation.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if XLP/XLY features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
