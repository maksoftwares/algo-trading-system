# H1 Broker FX USD Pressure Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 broker-consistent FX dollar-pressure follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-18 during USD-pressure regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 80-1600
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -30R
Expected max consecutive zero months: 3
Expected R-multiple distribution: many small losses, clustered 1.50R winners when broker-consistent USD pressure aligns with confirmed XAU H1 direction, and no single-trade concentration.
Hypothesis SHA256: pending registration
Expert: `h1_broker_fx_usd_pressure_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses broker-consistent processed H1 bars for:

- `EURUSD`: inverse dollar pressure proxy.
- `USDJPY`: direct dollar pressure proxy.

The proxy features are shifted by one completed H1 observation before any XAU decision is made.

USD pressure:

```text
eurusd_return_12h = log(EURUSD close / EURUSD close 12h ago)
usdjpy_return_12h = log(USDJPY close / USDJPY close 12h ago)
usd_pressure_12h = mean(-eurusd_return_12h, usdjpy_return_12h)
abs(usd_pressure_12h) >= 0.0018
abs(usd_pressure_z120) >= 0.35
usd_pressure_abs_percentile240 >= 0.55
```

Long setup:

```text
USD pressure is negative, so usd_pressure_12h <= -0.0018
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
USD pressure is positive, so usd_pressure_12h >= +0.0018
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

The strategy should capture XAU follow-through when broad USD pressure measured from EURUSD and USDJPY is already aligned and XAU confirms in the same direction on H1. Negative USD pressure should favor XAU long continuation; positive USD pressure should favor XAU short continuation.

## Why This Hypothesis Should Exist

This is mechanically independent from retest, round-number, swing-breakout, ETF-flow, credit-risk, real-yield ETF, futures-volume, COT, session, and calendar candidates. It also differs from `gold_fx_proxy_divergence_v0`: this candidate follows direct USD pressure after XAU confirmation; it does not trade XAU residual divergence against a rolling beta model.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if EURUSD/USDJPY features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
