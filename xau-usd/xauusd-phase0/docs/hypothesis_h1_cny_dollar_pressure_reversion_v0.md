# H1 CNY-Dollar Pressure Reversion v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 official CNY-dollar macro/FX pressure / XAU local exhaustion reversion
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-12 during CNY-dollar pressure regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 40-900
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -32R
Expected max consecutive zero months: 4
Expected R-multiple distribution: sparse-to-moderate H1 events with stop losses near -1R and clustered 1.40R wins when official CNY-dollar pressure is stretched but XAU rejects a local exhaustion move.
Hypothesis SHA256: pending registration
Expert: `h1_cny_dollar_pressure_reversion_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses official public FRED daily macro/FX series:

- `DEXCHUS`: China / U.S. foreign exchange rate, Chinese yuan per U.S. dollar.
- `DTWEXBGS`: nominal broad U.S. dollar index.

The FRED observations are shifted by one completed daily observation before merging into XAU H1 decisions.

CNY-dollar pressure:

```text
cny_per_usd_return_5d = log(DEXCHUS / DEXCHUS 5d ago)
dollar_index_return_5d = log(DTWEXBGS / DTWEXBGS 5d ago)
cny_dollar_pressure_5d = cny_per_usd_return_5d + 0.50 * dollar_index_return_5d
abs(cny_dollar_pressure_5d) >= 0.0060
abs(cny_dollar_pressure_z126) >= 0.35
cny_dollar_pressure_abs_percentile252 >= 0.55
```

Long setup:

```text
CNY-dollar pressure >= +0.0060, meaning yuan weakness and broad dollar strength
XAU H1 12-bar return <= -0.0020
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return >= -0.0300
current H1 candle closes bullish
current H1 close location >= 0.58
current close is not more than 2.25 ATR below EMA50
```

Short setup:

```text
CNY-dollar pressure <= -0.0060, meaning yuan strength and broad dollar weakness
XAU H1 12-bar return >= +0.0020
XAU H1 6-bar return <= +0.0005
XAU H1 24-bar return <= +0.0300
current H1 candle closes bearish
current H1 close location <= 0.42
current close is not more than 2.25 ATR above EMA50
```

Execution:

```text
Entry: market at signal bar close
Stop: 0.95 x H1 ATR(14)
Target: 1.40R
Time stop: 10 H1 bars
Duplicate control: maximum one signal per UTC day per direction
Decision hours: 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, 21:00 UTC
```

## Expected Behavior

The strategy should capture XAU mean reversion when official CNY-dollar pressure is stretched and XAU rejects a local move in the pressure-consistent direction. It is the paired opposite expression of the rejected CNY-dollar follow-through candidate, not a tuned variant of it.

## Why This Hypothesis Should Exist

The prior CNY-dollar follow-through candidate rejected the idea that XAU reliably extends in the same direction as official CNY-dollar pressure. A plausible opposite mechanism is that strong macro/FX pressure can already be discounted intraday, leaving a local exhaustion/reversion setup when the H1 path rejects continuation. This remains distinct from retest, round-number, session, GLD-flow, futures-volume, options-volatility, credit-risk, sector-rotation, and M5 path-structure candidates.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if FRED observations are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
