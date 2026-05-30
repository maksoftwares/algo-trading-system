# H1 HG/GC Copper-Gold Rotation Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 copper/gold futures relative-pressure follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-15 during copper/gold rotation pressure regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 50-900
Expected cost-adjusted PF: 1.00-1.60
Expected losing-month percentage: 35%-80%
Expected worst single month: -8R to -35R
Expected max consecutive zero months: 5
Expected R-multiple distribution: H1 futures-rotation follow-through signals with losses near -1R and winners clustered near 1.50R when copper/gold relative pressure and XAU local direction align.
Hypothesis SHA256: pending registration
Expert: `h1_hg_gc_copper_gold_rotation_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses shifted public Yahoo daily futures proxies:

- `HG=F`: COMEX copper continuous futures proxy.
- `GC=F`: COMEX gold continuous futures proxy.

Both observations are shifted by one completed daily observation before merging into XAU H1 decisions.

Copper/gold rotation features:

```text
hg_return_5d = log(HG close / HG close 5 observations ago)
gc_return_5d = log(GC close / GC close 5 observations ago)
hg_return_20d = log(HG close / HG close 20 observations ago)
gc_return_20d = log(GC close / GC close 20 observations ago)
copper_gold_pressure_5d = hg_return_5d - gc_return_5d
copper_gold_pressure_20d = hg_return_20d - gc_return_20d
copper_gold_ratio = log(HG close / GC close)
copper_gold_pressure_z126 = rolling z-score of copper_gold_pressure_5d over 126 observations
copper_gold_pressure_abs_percentile252 = rolling percentile of abs(copper_gold_pressure_5d) over 252 observations
```

Active pressure:

```text
abs(copper_gold_pressure_5d) >= 0.0100
AND abs(copper_gold_pressure_z126) >= 0.35
AND copper_gold_pressure_abs_percentile252 >= 0.55
```

Long setup:

```text
active pressure is positive
copper_gold_pressure_z126 >= +0.35
XAU close > EMA50
XAU EMA21 >= EMA50
XAU H1 12-bar return >= +0.0015
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return <= +0.0250
current H1 candle closes bullish
current H1 close location >= 0.60
```

Short setup:

```text
active pressure is negative
copper_gold_pressure_z126 <= -0.35
XAU close < EMA50
XAU EMA21 <= EMA50
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
Decision hours: 07, 09, 11, 13, 15, 17, 19, 21 UTC
```

## Expected Behavior

The strategy should capture XAU follow-through when direct copper/gold futures relative pressure is strong and XAU has already started moving in the same direction. This tests whether industrial-metal versus monetary-metal pressure contains faster information than gold-only momentum.

## Why This Hypothesis Should Exist

The previous DBB/UUP and commodity-dollar ETF proxy lanes used ETF baskets and broad dollar pressure. This candidate is a new data class because it tests direct copper futures versus direct gold futures, not an ETF basket, not a dollar denominator, not a retest, and not a level-break continuation pattern.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if HG/GC observations are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
