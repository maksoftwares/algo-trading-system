# H1 Tick-Volume Climax Continuation v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 participation-flow / tick-volume climax continuation
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 36-144
Expected median hold hours: 3-12
Expected decisions per week: 0-12 during high-participation windows
Timeframe diversification qualifies: yes
Expected trade count per year: 40-700
Expected cost-adjusted PF: 1.05-1.70
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -30R
Expected max consecutive zero months: 4
Expected R-multiple distribution: moderate H1 participation bursts with clustered -1R losses when the burst exhausts and 1.45R wins when participation follows through.
Hypothesis SHA256: pending registration
Expert: `h1_tick_volume_climax_continuation_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, demo attachment, or live execution.

## Mechanical Definition

This candidate tests the opposite thesis of the failed H1 tick-volume climax reversal: a large H1 candle with unusually high tick participation should continue when the candle closes strongly in its direction and short-term H1 momentum agrees.

All features use completed H1 bars only.

Participation climax:

```text
tick_count_z = (current_tick_count - rolling_mean_240_prior) / rolling_std_240_prior
tick_count_ratio = current_tick_count / rolling_median_240_prior
tick_count_z >= 1.10
tick_count_ratio >= 1.18
```

Bar quality:

```text
0.80 <= h1_range_atr <= 3.80
h1_body_ratio >= 0.45
abs(h1_return_24) <= 0.030
```

Long setup:

```text
H1 close > H1 open
H1 move >= +0.45 ATR
H1 6-bar log return >= +0.0010
H1 close location >= 0.72
H1 close >= EMA21
EMA21 >= 0.998 * EMA50
```

Short setup:

```text
H1 close < H1 open
H1 move <= -0.45 ATR
H1 6-bar log return <= -0.0010
H1 close location <= 0.28
H1 close <= EMA21
EMA21 <= 1.002 * EMA50
```

Execution:

```text
Entry: market at signal H1 close
Long stop: signal H1 low - 0.20 * H1 ATR(14)
Short stop: signal H1 high + 0.20 * H1 ATR(14)
Target: 1.45R
Time stop: 12 H1 bars
Duplicate control: maximum one signal per UTC day per direction
Weekend filter: no Saturday/Sunday signals
```

## Expected Behavior

The strategy should capture XAU continuation after participation shocks. If a high-tick-count H1 bar closes near its extreme and aligns with short-term momentum, the next several H1 bars should sometimes continue as late participants and stop-driven liquidity extend the move.

## Why This Hypothesis Should Exist

The rejected tick-volume climax reversal candidate showed that fading high-participation H1 candles was not robust. This v0 hypothesis tests the separate continuation mechanism rather than tuning the rejected reversal entry. It is distinct from breakout-retest, round-number, session-extreme, macro-FX rotation, ETF-flow, and static level-retest families.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if tick-volume participation is unavailable or unstable by broker. Do not tune v0 after results are known.
