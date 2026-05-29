# H1 GLD Flow Stress Reversal v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: GLD ETF flow-stress H1 reversal
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-96
Expected median hold hours: 2-8
Expected decisions per week: 0-5 after high-volume GLD flow-stress days
Timeframe diversification qualifies: yes
Expected trade count per year: 80-600
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: GLD flow-stress reversals should be sparse with moderate 1.45R wins after high-volume ETF-flow shocks, but should fail if broader H1 sampling dilutes the H4 GLD-flow lead.
Hypothesis SHA256: pending registration
Expert: `h1_gld_flow_stress_reversal_v0`
Status: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate is a versioned, result-informed GLD-flow stress reversal test. The earlier H4 GLD-flow v0 candidate had 9/9 PF cells above 1.30 but failed trade count, zero-activity, and concentration. This H1 candidate asks whether the same public GLD ETF daily OHLCV stress mechanism can produce enough additional observations without becoming a level/retest system.

Data:

- Public GLD daily OHLCV proxy from `data/reference/etf/gld_daily_yahoo_2015_2025.csv`.
- GLD features are shifted by one completed daily observation before merging to XAU H1 bars.
- XAUUSD H1 completed bars provide the entry/reversal state.

GLD flow stress is active only when:

```text
GLD volume percentile over 252 observations >= 0.75
max(GLD log-volume z126, GLD dollar-volume z126) >= 0.80
abs(GLD 1-day log return) >= 0.0030
```

Decision timestamps are fixed:

```text
07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, 21:00 UTC
```

Long setup:

```text
GLD 1-day return <= -0.0030
XAU H1 12-bar return <= -0.0020
XAU H1 6-bar return <= +0.0005
XAU H1 24-bar return >= -0.0200
XAU close is not more than 2.0 ATR below EMA50
current H1 candle closes bullish
current H1 close location >= 0.58
```

Short setup:

```text
GLD 1-day return >= +0.0030
XAU H1 12-bar return >= +0.0020
XAU H1 6-bar return >= -0.0005
XAU H1 24-bar return <= +0.0200
XAU close is not more than 2.0 ATR above EMA50
current H1 candle closes bearish
current H1 close location <= 0.42
```

Execution model:

```text
Entry: market at signal bar close
Stop: 0.95 x H1 ATR(14)
Target: 1.45R
Time stop: 8 H1 bars
Duplicate control: maximum one signal per UTC day per direction
```

## Expected Behavior

This candidate should pass only if GLD ETF flow stress has a cross-broker reversal effect that survives broader H1 sampling.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.

## Why This Hypothesis Should Exist

Large GLD daily participation shocks can represent public ETF-flow stress. The prior H4 reversal version showed cross-broker PF strength but insufficient observations. This H1 version tests whether completed H1 reversal candles after the same shifted GLD-flow shock can provide a broader sample while preserving the underlying stress-reversal mechanism.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one GLD shock cluster, or one month.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the GLD stress thresholds, H1 reversal state, stop size, target, or frequency rule after seeing this v0 result.
