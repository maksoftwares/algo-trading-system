# H1 Credit Spread Shock Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 corporate credit-spread shock follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-216
Expected median hold hours: 2-18
Expected decisions per week: 0-10 during credit-spread shock regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 40-700
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -35R
Expected max consecutive zero months: 5
Expected R-multiple distribution: sparse H1 corporate-credit shocks with stop losses near -1R and clustered 1.45R wins when credit stress/relief and local XAU direction align.
Hypothesis SHA256: pending registration
Expert: `h1_credit_spread_shock_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses shifted public FRED corporate-credit spread series:

- `BAA10Y`: Moody's seasoned Baa corporate bond yield relative to 10-year Treasury.
- `AAA10Y`: Moody's seasoned Aaa corporate bond yield relative to 10-year Treasury.

The FRED observations are shifted by one completed daily observation before merging into XAU H1 decisions.

Credit shock features:

```text
credit_quality_spread = BAA10Y - AAA10Y
baa10y_change_10d = BAA10Y - BAA10Y 10 observations ago
credit_quality_spread_change_10d = credit_quality_spread - credit_quality_spread 10 observations ago
baa10y_change_z252 = rolling z-score of baa10y_change_10d
credit_quality_spread_change_z252 = rolling z-score of credit_quality_spread_change_10d
```

Credit-stress shock:

```text
(baa10y_change_10d >= +0.12 and credit_quality_spread_change_10d >= +0.03)
OR baa10y_change_z252 >= +0.75
OR credit_quality_spread_change_z252 >= +0.75
```

Credit-relief shock:

```text
(baa10y_change_10d <= -0.12 and credit_quality_spread_change_10d <= -0.03)
OR baa10y_change_z252 <= -0.75
OR credit_quality_spread_change_z252 <= -0.75
```

Long setup:

```text
credit-stress shock is active
XAU H1 24-bar return >= +0.0040
XAU H1 8-bar return >= -0.0010
current H1 candle closes bullish
current H1 close location >= 0.58
close >= EMA50 * 0.985
```

Short setup:

```text
credit-relief shock is active
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

The strategy should capture XAU continuation when shifted corporate-credit shocks and local XAU direction agree. Credit stress should support long safe-haven continuation; credit relief should support short continuation if gold is already weakening.

## Why This Hypothesis Should Exist

The existing H1 credit-spread shock reversal candidate rejected the opposite hypothesis: that XAU overreacts to credit-spread shocks and then reverses. This candidate tests the paired follow-through mechanism without changing the data class after seeing the reversal result. It is distinct from retest, round-number, session, GLD-flow, futures-volume, options-volatility, FX-rotation, Treasury-curve-only, and M5 path-structure candidates.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if FRED observations are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
