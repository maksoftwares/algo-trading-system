# H1 ACWX/SPY Global Ex-US Rotation Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 global ex-US risk rotation / XAU follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-14 during global ex-US rotation regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 50-1000
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -32R
Expected max consecutive zero months: 4
Expected R-multiple distribution: sparse-to-moderate events with small losses and clustered 1.50R winners when ACWX/SPY risk rotation and XAU H1 confirmation align.
Hypothesis SHA256: pending registration
Expert: `h1_acwx_spy_global_ex_us_rotation_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses public Yahoo daily OHLCV for:

- `ACWX`: global ex-US equity ETF / global ex-US risk appetite and US-vs-rest-of-world rotation proxy.
- `SPY`: broad US equity proxy.

The ACWX/SPY features are shifted by one completed daily observation before merging into XAU H1 decisions.

global ex-US rotation:

```text
acwx_return_5d = log(ACWX close / ACWX close 5d ago)
spy_return_5d = log(SPY close / SPY close 5d ago)
global_ex_us_rotation_5d = acwx_return_5d - spy_return_5d
abs(global_ex_us_rotation_5d) >= 0.0100
abs(global_ex_us_rotation_z126) >= 0.35
global_ex_us_rotation_abs_percentile252 >= 0.55
```

Long setup:

```text
ACWX underperforms SPY, so global_ex_us_rotation_5d <= -0.0100
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
ACWX outperforms SPY, so global_ex_us_rotation_5d >= +0.0100
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

The strategy should capture XAU follow-through when global ex-US underperformance marks external-risk or USD-funding stress and XAU confirms higher, or when global ex-US outperformance marks risk appetite and XAU confirms lower.

## Why This Hypothesis Should Exist

ACWX/SPY global ex-US rotation is distinct from retest, round-number, FX-cross, crypto, GLD-flow, GDX/GLD miner-relative, credit-risk, rates-dollar, commodity-dollar, sector-defensive, precious-beta, QQQ/SPY growth rotation, IWM/SPY size rotation, and calendar candidates. It tests global risk transfer rather than level-break mechanics or a domestic US style/sector proxy.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if ACWX/SPY features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
