# H4 TIP/IEF Real-Yield Rotation Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 traded-ETF real-yield rotation overreaction reversal
Entry / decision timeframe: H4 completed-candle decisions with M5 execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 96-336
Expected median hold hours: 16-56
Expected decisions per week: 0-4
Timeframe diversification qualifies: yes
Expected trade count per year: 45-220
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 42%-60%
Expected worst single month: -8R to -15R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses, time stops, and occasional 1.55R winners after H4 spot-gold overreaction candles diverge from shifted TIP/IEF real-yield rotation. Reject if results require changing the rotation threshold, z-score threshold, H4 return windows, rejection candle rules, stop multiplier, target, or weekly signal cap after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

This candidate is deliberately higher-timeframe and intermarket/macro-proxy based. It is not a breakout-retest, round-level, GLD-flow, options-skew, or same-family level-pullback hypothesis.

## Mechanical Definition

`h4_tip_ief_real_yield_rotation_reversal_v0` tests whether H4 XAUUSD has a reversal edge after spot gold moves against a shifted traded-ETF real-yield rotation proxy and then prints a completed H4 rejection candle.

Data source:

- XAUUSD H4 OHLC bars.
- Public Yahoo TIP/IEF daily OHLCV proxy stored at `data/reference/etf/tip_ief_daily_yahoo_2015_2025.csv`.
- M5 bars are used only by the Phase 0 execution simulator after the H4 signal is generated.

Feature rules:

1. Compute H4 ATR(14), EMA(40), 6-bar log return, 12-bar log return, and 24-bar log return.
2. Compute shifted 5-day `TIP` return, shifted 5-day `IEF` return, and `real_yield_rotation_5d = TIP return - IEF return`.
3. Compute shifted 126-day z-score and 252-day absolute percentile of the rotation.
4. A rotation is active when:
   - `abs(real_yield_rotation_5d) >= 0.0035`
   - `abs(real_yield_rotation_z126) >= 0.35`
   - `real_yield_rotation_abs_percentile252 >= 0.55`
5. Allow at most one signal per ISO week and direction.
6. Long setup:
   - active positive TIP/IEF rotation
   - H4 12-bar XAU return `<= -0.0045`
   - H4 24-bar XAU return `>= -0.0450`
   - H4 6-bar XAU return `<= 0.0010`
   - current H4 candle closes above open
   - close location inside candle range `>= 0.60`
   - close is no more than 2.50 ATR below EMA40
7. Short setup:
   - active negative TIP/IEF rotation
   - H4 12-bar XAU return `>= 0.0045`
   - H4 24-bar XAU return `<= 0.0450`
   - H4 6-bar XAU return `>= -0.0010`
   - current H4 candle closes below open
   - close location inside candle range `<= 0.40`
   - close is no more than 2.50 ATR above EMA40
8. Entry is simulated at market from the next available M5 bar after the H4 signal.
9. Stop is 1.15 H4 ATR from estimated entry.
10. Target is 1.55R.
11. Time stop is 7 H4 bars.

## Expected Behavior

Expected trade count: moderate H4 frequency, likely 45-220 trades per year if TIP/IEF rotation cycles are frequent enough across brokers.
Expected PF: at least 1.30 in 7 of 9 matrix cells if traded real-yield rotation divergence has persistent XAU reversal value after costs.
Expected losing-month percentage: below 60%.
Expected worst month: no worse than -15R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

TIP/IEF relative performance is a public traded proxy for inflation-protection versus nominal-duration demand. Gold can temporarily diverge from that pressure when local spot positioning overshoots. This hypothesis tests whether a completed H4 rejection candle after such divergence is a lower-frequency reversal edge.

This is intentionally different from the approved breakout/retest family:

- no level break is required
- no retest is required
- no M5/M15 structure signal is used
- the causal input is shifted ETF real-yield rotation plus H4 overreaction, not support/resistance continuation

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the edge appears only in one broker window
- the only profitable cells depend on best-case costs

Do not tune v0 thresholds after first-pass results. Any future TIP/IEF real-yield rotation revisit needs a new versioned hypothesis and fresh SHA256 registration.

## Code Mapping

- Strategy implementation: `src/phase0/strategies/h4_tip_ief_real_yield_rotation_reversal_v0.py`
- Data loader: `src/phase0/tip_ief_real_yield_rotation_data.py`
- Synthetic smoke context: `src/phase0/synthetic.py::_h4_tip_ief_real_yield_rotation_reversal_context`
- Test: `tests/test_h4_tip_ief_real_yield_rotation_reversal_v0.py`
