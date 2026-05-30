# H1 MOVE/VIX Bond-Vol Shock Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 bond-volatility shock follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 36-216
Expected median hold hours: 3-18
Expected decisions per week: 0-10 during rates-volatility stress regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 30-500
Expected cost-adjusted PF: 0.90-1.60
Expected losing-month percentage: 35%-85%
Expected worst single month: -8R to -35R
Expected max consecutive zero months: 8
Expected R-multiple distribution: H1 bond-volatility stress continuation signals with losses near -1R and winners clustered near 1.50R when MOVE rises materially more than VIX and XAU confirms local direction.
Hypothesis SHA256: pending registration
Expert: `h1_move_vix_bond_vol_shock_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses shifted public daily volatility proxies:

- MOVE daily close from the public Yahoo MOVE proxy already stored in `data/reference/rates/move_daily_yahoo_2015_2025.csv`.
- VIX daily close from the existing shifted VIX context.

Both observations are shifted by one completed daily observation before merging into XAU H1 decisions.

Bond-volatility stress is active when:

```text
move_return_5d >= 0.060
AND move_return_5d > vix_return_5d + 0.015
AND move_vix_ratio_z252 >= 0.35
AND (move_vix_ratio_change_5d >= 0.035 OR move_vix_ratio_change_z126 >= 0.40)
```

Long follow-through setup:

```text
bond-volatility stress is active
XAU H1 6-bar return >= +0.0025
XAU H1 24-bar return <= +0.0300
current H1 candle closes bullish
current H1 close location >= 0.60
current H1 close >= EMA40 - 0.70 x H1 ATR14
```

Short follow-through setup:

```text
bond-volatility stress is active
XAU H1 6-bar return <= -0.0025
XAU H1 24-bar return >= -0.0300
current H1 candle closes bearish
current H1 close location <= 0.40
current H1 close <= EMA40 + 0.70 x H1 ATR14
```

Execution:

```text
Entry: market at signal bar close
Stop: 1.10 x H1 ATR(14)
Target: 1.50R
Time stop: 18 H1 bars
Duplicate control: maximum one signal per UTC day per direction
```

## Expected Behavior

The strategy should capture XAU follow-through when a rates-volatility shock is stronger than the equity-volatility shock and XAU has already confirmed local directional movement. This is the paired follow-through expression for the already rejected MOVE/VIX reversal lane.

## Why This Hypothesis Should Exist

Bond-volatility shocks can affect gold through duration, real-rate uncertainty, and safe-haven flows. The prior reversal version tested overreaction. This v0 tests whether the same stress instead supports directional continuation. It is not a breakout/retest or level-pullback EA.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if MOVE/VIX observations are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
