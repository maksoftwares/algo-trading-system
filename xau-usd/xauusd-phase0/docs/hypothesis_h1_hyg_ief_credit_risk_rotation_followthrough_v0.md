# H1 HYG/IEF Credit-Risk Rotation Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 traded ETF credit-risk versus Treasury follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-12 during credit-risk rotation regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 60-1000
Expected cost-adjusted PF: 1.05-1.60
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -28R
Expected max consecutive zero months: 3
Expected R-multiple distribution: credit-risk rotation follow-through should show many small losses, clustered 1.50R winners when XAU confirms safe-haven or risk-on pressure, and no single-trade concentration.
Hypothesis SHA256: pending registration
Expert: `h1_hyg_ief_credit_risk_rotation_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses public Yahoo daily OHLCV proxies for:

- `HYG`: high-yield corporate bond ETF proxy.
- `IEF`: intermediate Treasury ETF proxy.

Features are shifted by one completed daily observation before merging into XAU H1 bars.

Credit-stress pressure:

```text
credit_stress_5d = log(IEF close / IEF close 5d ago) - log(HYG close / HYG close 5d ago)
credit_stress_5d >= +0.0060
abs(credit_stress_z126) >= 0.35
credit_stress_abs_percentile252 >= 0.55
```

Long setup:

```text
credit-stress pressure is positive
XAU close > EMA50
EMA21 >= EMA50
XAU H1 12-bar return >= +0.0015
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return <= +0.0250
current H1 candle closes bullish
current H1 close location >= 0.60
```

Risk-on pressure is symmetric:

```text
credit_stress_5d <= -0.0060
abs(credit_stress_z126) >= 0.35
credit_stress_abs_percentile252 >= 0.55
```

Short setup:

```text
credit-stress pressure is negative
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

The strategy should capture XAU follow-through when high-yield credit versus Treasury rotation confirms a risk-off or risk-on impulse and XAU has already moved in the matching direction on H1.

## Why This Hypothesis Should Exist

Credit-risk rotation is mechanically distinct from the rejected commodity, metals, GLD-flow, and retest families. HYG underperforming IEF can indicate credit stress and safe-haven demand; HYG outperforming IEF can indicate risk-on pressure that may weigh on XAU if XAU confirms lower.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if HYG/IEF features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
