# H1 Macro Composite State Reversion v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 macro-composite exhaustion reversion
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-96
Expected median hold hours: 2-8
Expected decisions per week: 0-8 during macro-composite extremes
Timeframe diversification qualifies: yes
Expected trade count per year: 80-800
Expected cost-adjusted PF: 1.05-1.60
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H1 exhaustion reversions should have many small losses, clustered 1.35R winners after macro-state overextension, and no single-trade concentration.
Hypothesis SHA256: pending registration
Expert: `h1_macro_composite_state_reversion_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate tests whether a fixed macro-composite extreme creates intraday overextension that reverts on completed H1 candles. It uses the same shifted macro inputs as the H4 macro-composite candidates: real yield, broad dollar, breakevens, Treasury curve, credit spreads, VIX, GVZ, and financial conditions.

Short setup:

```text
macro_composite_score >= +3
macro_bull_votes >= 4
XAU H1 24-bar return >= +0.0040
XAU H1 12-bar return >= +0.0020
XAU H1 6-bar return >= -0.0005
EMA50 distance is between +0.50 and +3.50 ATR
current H1 candle closes bearish
current H1 close location <= 0.42
```

Long setup:

```text
macro_composite_score <= -3
macro_bear_votes >= 4
XAU H1 24-bar return <= -0.0040
XAU H1 12-bar return <= -0.0020
XAU H1 6-bar return <= +0.0005
EMA50 distance is between -3.50 and -0.50 ATR
current H1 candle closes bullish
current H1 close location >= 0.58
```

Execution:

```text
Entry: market at signal bar close
Stop: 1.00 x H1 ATR(14)
Target: 1.35R
Time stop: 8 H1 bars
Duplicate control: maximum one signal per UTC day per direction
```

## Expected Behavior

The strategy should produce more observations than the H4 macro-composite v0 while retaining cross-broker expectancy. It should be rejected if it only works in one broker window or if the edge disappears under measured cost assumptions.

## Why This Hypothesis Should Exist

The H4 macro-composite risk-state v0 had the strongest non-level macro lead, but activity and concentration were insufficient. This H1 version tests a different mechanism: not macro-following, but short-term exhaustion after price overreacts inside a strong macro state.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if fewer than 9/9 cells clear trade count, if concentration or activity gates fail, if the result is broker-specific, or if any macro input is unshifted or incomplete. Do not tune v0 after results are known.
