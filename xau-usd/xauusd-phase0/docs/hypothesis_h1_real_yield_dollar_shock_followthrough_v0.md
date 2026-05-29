# H1 Real-Yield Dollar Shock Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 macro shock follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-6 during joint macro shock windows
Timeframe diversification qualifies: yes
Expected trade count per year: 80-700
Expected cost-adjusted PF: 1.05-1.60
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: macro-shock follow-through should have clustered 1.50R winners when real-yield and broad-dollar pressure persists intraday, but should fail if it is just trend-chasing noise.
Hypothesis SHA256: pending registration
Expert: `h1_real_yield_dollar_shock_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate tests the opposite interpretation of `h1_real_yield_dollar_shock_reversal_v0`: if joint real-yield and broad-dollar shocks do not reliably revert on H1, they may instead continue when XAU confirms the same direction on completed H1 bars.

Data:

- FRED `DFII10` real-yield data.
- FRED `DTWEXBGS` broad-dollar index data.
- Macro features are shifted by one completed daily observation before merging to XAU H1 bars.
- XAUUSD H1 completed bars provide the entry/follow-through state.

Decision timestamps are fixed:

```text
07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, 21:00 UTC
```

Long setup:

```text
20-business-day real-yield change <= -0.12
20-business-day broad-dollar log return <= -0.0030
min(real-yield z252, dollar-return z252) <= -0.45
XAU H1 12-bar return >= +0.0020
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return <= +0.0250
XAU close > EMA50
EMA21 >= EMA50
EMA50 distance <= +2.5 ATR
current H1 candle closes bullish
current H1 close location >= 0.60
```

Short setup:

```text
20-business-day real-yield change >= +0.12
20-business-day broad-dollar log return >= +0.0030
max(real-yield z252, dollar-return z252) >= +0.45
XAU H1 12-bar return <= -0.0020
XAU H1 6-bar return <= +0.0005
XAU H1 24-bar return >= -0.0250
XAU close < EMA50
EMA21 <= EMA50
EMA50 distance >= -2.5 ATR
current H1 candle closes bearish
current H1 close location <= 0.40
```

Execution model:

```text
Entry: market at signal bar close
Stop: 1.05 x H1 ATR(14)
Target: 1.50R
Time stop: 10 H1 bars
Duplicate control: maximum one signal per UTC day per direction
```

## Expected Behavior

This should trade more often than H4 macro momentum and should not require a level/retest event. It should pass only if macro-shock pressure persists across broker windows after costs. Same-family breakout-retest candidates do not count as evidence for this hypothesis.

## Why This Hypothesis Should Exist

Real yields and the broad dollar directly pressure gold. When both move together, intraday XAU selling or buying may persist as macro participants rebalance. If that pressure is real, completed H1 trend-confirmation candles should show cost-adjusted continuation without needing a prior support/resistance break.

## What Would Falsify It

Reject the hypothesis if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the edge is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if macro data coverage/shift discipline is incomplete. Do not tune v0 after results are known.
