# H1 HG/GC Copper-Gold Rotation Reversal v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 copper/gold futures relative-pressure overextension reversal
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-15 during copper/gold rotation pressure regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 50-900
Expected cost-adjusted PF: 0.90-1.60
Expected losing-month percentage: 35%-85%
Expected worst single month: -8R to -35R
Expected max consecutive zero months: 5
Expected R-multiple distribution: H1 futures-rotation reversal signals with losses near -1R and winners clustered near 1.50R when copper/gold relative pressure and local XAU extension exhaust.
Hypothesis SHA256: pending registration
Expert: `h1_hg_gc_copper_gold_rotation_reversal_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses the same shifted public Yahoo daily futures proxies as the paired follow-through test:

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

Short reversal setup:

```text
active pressure is positive
copper_gold_pressure_z126 >= +0.35
XAU close > EMA50
XAU EMA21 >= EMA50
XAU H1 12-bar return >= +0.0025
XAU H1 6-bar return >= +0.0005
XAU H1 24-bar return <= +0.0300
current H1 candle closes bearish
current H1 close location <= 0.35
```

Long reversal setup:

```text
active pressure is negative
copper_gold_pressure_z126 <= -0.35
XAU close < EMA50
XAU EMA21 <= EMA50
XAU H1 12-bar return <= -0.0025
XAU H1 6-bar return <= -0.0005
XAU H1 24-bar return >= -0.0300
current H1 candle closes bullish
current H1 close location >= 0.65
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

The strategy should capture XAU reversal after strong copper/gold relative pressure coincides with a same-direction local XAU extension and then an H1 rejection candle. This is the paired contrary claim to the follow-through version: the pressure may mark overextension rather than continuation.

## Why This Hypothesis Should Exist

The paired follow-through version was rejected, but that does not prove the HG/GC data class is useless. A reversal expression tests a materially different market behavior while keeping fixed first-pass thresholds and no post-result tuning. It is still not a breakout, retest, level, or pullback EA.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if HG/GC observations are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
