# H1 Financial Conditions Shock Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 financial-conditions shock follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-216
Expected median hold hours: 2-18
Expected decisions per week: 0-10 during financial-conditions shock regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 40-700
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -35R
Expected max consecutive zero months: 5
Expected R-multiple distribution: sparse H1 financial-conditions shocks with stop losses near -1R and clustered 1.45R wins when financial stress/relief and local XAU direction align.
Hypothesis SHA256: pending registration
Expert: `h1_financial_conditions_shock_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses shifted public FRED financial-conditions series:

- `NFCI`: Chicago Fed National Financial Conditions Index.
- `ANFCI`: Chicago Fed Adjusted National Financial Conditions Index.

The FRED observations are shifted by one completed weekly observation before merging into XAU H1 decisions.

Financial-conditions shock features:

```text
nfci_change_4w = NFCI - NFCI 4 observations ago
anfci_change_4w = ANFCI - ANFCI 4 observations ago
nfci_percentile156 = rolling percentile rank of NFCI over 156 observations
```

Tightening shock:

```text
nfci_change_4w >= +0.12
OR anfci_change_4w >= +0.10
OR nfci_percentile156 >= 0.65
```

Easing shock:

```text
nfci_change_4w <= -0.12
OR anfci_change_4w <= -0.10
OR nfci_percentile156 <= 0.35
```

Long setup:

```text
tightening financial-conditions shock is active
XAU H1 24-bar return >= +0.0040
XAU H1 8-bar return >= -0.0010
current H1 candle closes bullish
current H1 close location >= 0.58
close >= EMA50 * 0.985
```

Short setup:

```text
easing financial-conditions shock is active
XAU H1 24-bar return <= -0.0040
XAU H1 8-bar return <= +0.0010
current H1 candle closes bearish
current H1 close location <= 0.42
close <= EMA50 * 1.015
```

Execution:

```text
Entry: market at signal bar close
Stop: 1.00 x H1 ATR(14)
Target: 1.45R
Time stop: 18 H1 bars
Duplicate control: maximum one signal per UTC day per direction
Decision hours: 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, 21:00 UTC
```

## Expected Behavior

The strategy should capture XAU continuation when shifted financial-conditions shocks and local XAU direction agree. Tightening financial conditions should support long safe-haven continuation; easing financial conditions should support short continuation if gold is already weakening.

## Why This Hypothesis Should Exist

The existing H1 financial-conditions shock reversal candidate rejected the opposite hypothesis: that XAU overreacts to NFCI/ANFCI shocks and then reverses. This candidate tests the paired follow-through mechanism without changing the data class after seeing the reversal result. It is distinct from retest, round-number, session, GLD-flow, futures-volume, options-volatility, FX-rotation, Treasury-curve-only, corporate-credit-only, and M5 path-structure candidates.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if FRED observations are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
