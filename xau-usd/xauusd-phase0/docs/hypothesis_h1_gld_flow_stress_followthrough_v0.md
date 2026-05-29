# H1 GLD Flow Stress Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: GLD ETF flow-stress H1 follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-120
Expected median hold hours: 2-10
Expected decisions per week: 0-5 after high-volume GLD flow-stress days
Timeframe diversification qualifies: yes
Expected trade count per year: 80-700
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 3
Expected R-multiple distribution: GLD flow-stress follow-through should be sparse with clustered 1.50R winners after high-volume ETF-flow shocks, but should fail if it is simply H1 trend-following noise.
Hypothesis SHA256: pending registration
Expert: `h1_gld_flow_stress_followthrough_v0`
Status: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate tests the opposite interpretation of the H1 GLD-flow stress-reversal failure: if GLD ETF flow shocks are not reliably faded on H1, the stress may instead continue when XAU confirms the same direction on completed H1 bars.

Data:

- Public GLD daily OHLCV proxy from `data/reference/etf/gld_daily_yahoo_2015_2025.csv`.
- GLD features are shifted by one completed daily observation before merging to XAU H1 bars.
- XAUUSD H1 completed bars provide the entry/follow-through state.

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
GLD 1-day return >= +0.0030
XAU H1 12-bar return >= +0.0020
XAU H1 6-bar return >= 0.0
XAU H1 24-bar return <= +0.0250
XAU close > EMA50
EMA21 >= EMA50
current H1 candle closes bullish
current H1 close location >= 0.60
```

Short setup:

```text
GLD 1-day return <= -0.0030
XAU H1 12-bar return <= -0.0020
XAU H1 6-bar return <= 0.0
XAU H1 24-bar return >= -0.0250
XAU close < EMA50
EMA21 <= EMA50
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

This candidate should pass only if GLD ETF flow stress creates cross-broker directional follow-through on XAU H1.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.

## Why This Hypothesis Should Exist

Large GLD daily participation shocks can represent public ETF-flow pressure. If H1 reversal timing fails, same-direction H1 follow-through may be the more accurate expression: flow shock plus XAU confirmation indicates continued allocation pressure rather than exhaustion.

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
- Any future improvement changes the GLD stress thresholds, H1 follow-through state, stop size, target, or frequency rule after seeing this v0 result.
