# Hypothesis: <Expert Name>

Expert name:
Hypothesis date:
Hypothesis version: v1.0
Author / owner:
Mechanic family: <level-and-pullback / mean-reversion / macro-regime / intermarket / volatility / other>
Entry / decision timeframe: <M5 / M15 / H1 / H4 / D1 / W1>
Expected median hold bars M5-equivalent:
Expected median hold hours:
Expected decisions per week:
Timeframe diversification qualifies: <yes/no>

## Mechanical Definition

Write the exact non-optimized rule set here before running any backtest.

If the hypothesis claims timeframe diversification, it must satisfy both:

- expected median hold time exceeds 24 hours
- expected trade count is below 100 per year

A D1, W1, or prior-session reference level with M5 entries does not qualify as timeframe diversification.

## Expected Behavior

Expected trade count per year: <N> +/- 20%

Expected cost-adjusted PF: <PF> +/- 0.3

Expected losing-month percentage: <N>% +/- 10%

Expected worst single month: $<negative amount>

Expected max consecutive zero months: <N>

Expected R-multiple distribution:

## Why This Hypothesis Should Exist

Explain the market behavior this expert is meant to capture.

## What Would Falsify It

List concrete gate failures or evidence that should reject the expert.
