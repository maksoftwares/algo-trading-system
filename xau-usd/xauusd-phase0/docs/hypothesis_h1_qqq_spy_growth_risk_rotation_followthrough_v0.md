# H1 QQQ/SPY Growth Risk Rotation Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 equity growth-risk rotation / XAU follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-14 during growth-risk rotation regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 50-1000
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -32R
Expected max consecutive zero months: 4
Expected R-multiple distribution: sparse-to-moderate events with small losses and clustered 1.50R winners when growth-risk rotation and XAU H1 confirmation align.
Hypothesis SHA256: pending registration
Expert: `h1_qqq_spy_growth_risk_rotation_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses public Yahoo daily OHLCV for:

- `QQQ`: Nasdaq/growth-risk proxy.
- `SPY`: broad US equity proxy.

The QQQ/SPY features are shifted by one completed daily observation before merging into XAU H1 decisions.

Growth-risk rotation:

```text
qqq_return_5d = log(QQQ close / QQQ close 5d ago)
spy_return_5d = log(SPY close / SPY close 5d ago)
growth_rotation_5d = qqq_return_5d - spy_return_5d
abs(growth_rotation_5d) >= 0.0100
abs(growth_rotation_z126) >= 0.35
growth_rotation_abs_percentile252 >= 0.55
```

Long setup:

```text
QQQ underperforms SPY, so growth_rotation_5d <= -0.0100
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
QQQ outperforms SPY, so growth_rotation_5d >= +0.0100
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

The strategy should capture XAU follow-through when growth-risk stress is visible through QQQ underperforming SPY and XAU confirms higher, or when aggressive growth-risk appetite coincides with confirmed XAU downside.

## Why This Hypothesis Should Exist

QQQ/SPY growth-risk rotation is distinct from retest, round-number, FX, crypto, GLD-flow, credit-risk, rates-dollar, commodity-dollar, futures-volume, COT, sector-defensive, and calendar candidates. It is a style-rotation proxy rather than a broad equity-versus-Treasury or sector-versus-sector proxy.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if QQQ/SPY features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
