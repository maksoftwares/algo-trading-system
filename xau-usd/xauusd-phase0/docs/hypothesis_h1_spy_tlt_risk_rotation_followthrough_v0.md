# H1 SPY/TLT Risk-Rotation Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 traded ETF risk-rotation follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-8 during SPY/TLT risk-rotation regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 80-900
Expected cost-adjusted PF: 1.05-1.60
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: SPY/TLT risk-rotation follow-through should have many small losses, clustered 1.50R winners when XAU confirms equity/rates risk rotation, and no single-trade concentration.
Hypothesis SHA256: pending registration
Expert: `h1_spy_tlt_risk_rotation_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses public Yahoo daily OHLCV proxies for:

- `SPY`: broad US equity risk appetite proxy.
- `TLT`: long-duration Treasury ETF / risk-off duration proxy.

Features are shifted by one completed daily observation before merging into XAU H1 bars.

Risk-off rotation:

```text
risk_rotation_5d = log(TLT close / TLT close 5d ago) - log(SPY close / SPY close 5d ago)
risk_rotation_5d >= +0.0120
abs(risk_rotation_z126) >= 0.35
risk_rotation_abs_percentile252 >= 0.55
```

Long setup:

```text
risk-off rotation is active
XAU close > EMA50
EMA21 >= EMA50
XAU H1 12-bar return >= +0.0015
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return <= +0.0250
current H1 candle closes bullish
current H1 close location >= 0.60
```

Risk-on rotation is symmetric:

```text
risk_rotation_5d <= -0.0120
abs(risk_rotation_z126) >= 0.35
risk_rotation_abs_percentile252 >= 0.55
```

Short setup:

```text
risk-on rotation is active
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

The strategy should capture XAU confirmation in the same direction as shifted equity/rates risk rotation. It should not require support/resistance levels, round numbers, retest mechanics, or unshifted ETF values.

## Why This Hypothesis Should Exist

Gold may behave as a risk-off or duration-sensitive asset when equities sell off and long-duration Treasuries are bid. A SPY/TLT rotation proxy measures a different pressure axis from the failed TLT/UUP rates-dollar lane, so it deserves a separate locked first pass.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if SPY/TLT features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
