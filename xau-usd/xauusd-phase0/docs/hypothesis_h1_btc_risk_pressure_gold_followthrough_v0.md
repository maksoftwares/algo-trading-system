# H1 BTC Risk Pressure Gold Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 crypto risk-pressure / XAU safe-haven follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-12 during large BTC risk-pressure regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 40-900
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -32R
Expected max consecutive zero months: 4
Expected R-multiple distribution: sparse-to-moderate events with small losses and clustered 1.50R winners when BTC risk pressure and XAU H1 confirmation align.
Hypothesis SHA256: pending registration
Expert: `h1_btc_risk_pressure_gold_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses public Yahoo daily OHLCV for:

- `BTC-USD`: crypto risk-appetite / risk-liquidation proxy.

The BTC features are shifted by one completed daily observation before merging into XAU H1 decisions.

BTC risk pressure:

```text
btc_return_5d = log(BTC close / BTC close 5d ago)
abs(btc_return_5d) >= 0.0800
abs(btc_return_z126) >= 0.50
btc_abs_return_percentile252 >= 0.60
```

Long setup:

```text
BTC sells off hard, so btc_return_5d <= -0.0800
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
BTC rallies hard, so btc_return_5d >= +0.0800
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

The strategy should capture XAU follow-through when large BTC drawdowns coincide with confirmed XAU safe-haven bid, or when large BTC rallies coincide with confirmed XAU downside. It treats crypto as a separate risk-pressure proxy, not as a gold-specific valuation anchor.

## Why This Hypothesis Should Exist

BTC-USD is a new data class relative to retest, round-number, ETF-flow, credit-risk, real-yield ETF, futures-volume, COT, FX, sector-rotation, and calendar candidates. The hypothesis is intentionally sparse and event-driven, using only pre-shifted daily BTC pressure plus H1 XAU confirmation.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if BTC features are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
