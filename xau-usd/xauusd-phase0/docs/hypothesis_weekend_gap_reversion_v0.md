# Weekend Gap Reversion v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: weekend gap-fill calendar reversion
Entry / decision timeframe: first M15 completed candle after a >=24-hour market break
Expected median hold bars M5-equivalent: 12-96
Expected median hold hours: 1-8
Expected decisions per week: 0-2
Timeframe diversification qualifies: yes
Expected trade count per year: 10-80
Expected cost-adjusted PF: 0.90-1.70
Expected losing-month percentage: 35%-85%
Expected worst single month: -5R to -20R
Expected max consecutive zero months: 6
Expected R-multiple distribution: gap-fill attempts with losses near -1R and winners determined by distance back to the pre-gap close.
Hypothesis SHA256: pending registration
Expert: `weekend_gap_reversion_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses only broker XAUUSD M15 bars. It does not use support/resistance levels, retests, breakout confirmation, macro data, or external proxies.

Weekend / long-break gap:

```text
market_break_hours = current_m15_bar_start_utc - previous_m15_bar_start_utc
market_break_hours >= 24
market_break_hours <= 96
pre_gap_close = previous M15 close
gap_atr = (current M15 open - pre_gap_close) / M15 ATR(14)
abs(gap_atr) >= 0.35
```

Short gap-up reversion:

```text
gap_atr >= +0.35
current M15 close > pre_gap_close + 0.05 x ATR14
current M15 close < current M15 open
current M15 close location <= 0.40
reward/risk to pre_gap_close >= 1.15
```

Long gap-down reversion:

```text
gap_atr <= -0.35
current M15 close < pre_gap_close - 0.05 x ATR14
current M15 close > current M15 open
current M15 close location >= 0.60
reward/risk to pre_gap_close >= 1.15
```

Execution:

```text
Entry: market at signal M15 close
Stop: signal-bar high/low plus 0.35 x M15 ATR(14)
Target: pre_gap_close
Time stop: 96 M5 bars
Duplicate control: maximum one signal per ISO week per direction
```

## Expected Behavior

The strategy should capture mean reversion after large weekend or long-market-break gaps when the first M15 candle rejects continuation and leaves enough distance back to the pre-gap close.

## Why This Hypothesis Should Exist

This is a calendar/microstructure gap-fill hypothesis, not a trend, pullback, level, retest, intermarket, macro, or volatility-proxy expression. It tests whether broker-visible XAU weekend gaps revert often enough after costs to form an independent behavior family.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if the first M15 bar after a long market break is not used mechanically. Do not tune v0 after results are known.
