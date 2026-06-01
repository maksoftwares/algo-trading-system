# H4 Month-Turn Flow Reversion v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 calendar-flow / month-turn liquidity unwind reversion
Entry / decision timeframe: H4 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 96-576
Expected median hold hours: 8-48
Expected decisions per week: 0-8 during month-end and month-start windows
Timeframe diversification qualifies: yes
Expected trade count per year: 25-500
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-80%
Expected worst single month: -6R to -30R
Expected max consecutive zero months: 5
Expected R-multiple distribution: sparse H4 month-turn reversal attempts with losses near -1R and 1.50R wins when multi-session flow pressure unwinds.
Hypothesis SHA256: pending registration
Expert: `h4_month_turn_flow_reversion_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, demo attachment, or live execution.

## Mechanical Definition

This candidate tests whether month-end and month-start XAUUSD flow pressure mean-reverts on a completed H4 candle after a multi-session stretch starts to reject. It is a higher-timeframe version of the rejected H1 month-turn reversion family, but the H4 rules are registered as a separate v0 hypothesis rather than tuned from the H1 result.

Month-turn window:

```text
month_day <= 4 or month_day >= 25
```

Long setup:

```text
H4 6-bar log return <= -0.0040
H4 3-bar log return >= -0.0015
H4 12-bar log return >= -0.0550
close - EMA40 >= -2.75 * H4 ATR(14)
close - EMA80 >= -3.50 * H4 ATR(14)
current H4 candle closes bullish
current H4 close location >= 0.58
```

Short setup:

```text
H4 6-bar log return >= +0.0040
H4 3-bar log return <= +0.0015
H4 12-bar log return <= +0.0550
close - EMA40 <= +2.75 * H4 ATR(14)
close - EMA80 <= +3.50 * H4 ATR(14)
current H4 candle closes bearish
current H4 close location <= 0.42
```

Execution:

```text
Entry: market at signal H4 close
Stop: 1.10 * H4 ATR(14)
Target: 1.50R
Time stop: 12 H4 bars
Duplicate control: maximum one signal per UTC day per direction
```

## Expected Behavior

The strategy should capture month-turn pressure unwind after XAU stretches in one direction and then prints a completed H4 rejection candle. The intended edge is calendar-flow exhaustion, not static level retest, round-number behavior, session-extreme behavior, ETF relative-value, volatility-premium, or macro proxy follow-through.

## Why This Hypothesis Should Exist

Month-end and month-start flows can produce positioning, benchmark, liquidity, and rebalance pressure. H1 month-turn attempts produced enough activity but failed expectancy. Moving the decision to H4 is a distinct attempt to reduce execution noise and cost sensitivity while requiring stronger completed-candle rejection.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, or if cost sensitivity fails. Do not tune v0 after results are known.

## Code Mapping

- Strategy: `src/phase0/strategies/h4_month_turn_flow_reversion_v0.py`
- Matrix data-context injection: `src/phase0/matrix.py`
- Synthetic smoke context: `src/phase0/synthetic.py`
- Focused smoke test: `tests/test_h4_month_turn_flow_reversion_v0.py`

## Safety Boundary

This is Phase 0 research code only. It must not place orders, modify positions, call MT5 trading APIs, or be attached to demo/live accounts. Any passing result only authorizes review and later dry-run planning, never live execution.
