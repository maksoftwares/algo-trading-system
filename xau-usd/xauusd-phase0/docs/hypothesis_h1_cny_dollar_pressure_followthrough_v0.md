# H1 CNY-Dollar Pressure Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 official CNY-dollar macro/FX pressure / XAU follow-through
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
Expected R-multiple distribution: sparse-to-moderate H1 events with stop losses near -1R and clustered 1.50R wins when official CNY-dollar pressure and XAU confirmation align.
Hypothesis SHA256: d3415e70b40650b43c84f76f1ee301aabfff3fc7c6d3e8e17602a8d904cab0c7
Expert: `h1_cny_dollar_pressure_followthrough_v0`
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
CNY-dollar pressure <= -0.0060, meaning yuan strength and broad dollar weakness
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
CNY-dollar pressure >= +0.0060, meaning yuan weakness and broad dollar strength
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

The strategy should capture XAU follow-through when official CNY-dollar pressure and local XAU trend agree. Yuan strength plus broad dollar weakness should support long XAU continuation; yuan weakness plus broad dollar strength should support short XAU continuation.

## Why This Hypothesis Should Exist

The prior CYB/UUP yuan-dollar ETF proxy candidate is data-blocked because CYB coverage ends in 2023. This candidate tests the same macro family with a different and more authoritative input class: official FRED exchange-rate and broad-dollar series. It is distinct from retest, round-number, session, GLD-flow, futures-volume, options-volatility, credit-risk, sector-rotation, and M5 path-structure candidates.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if FRED observations are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
