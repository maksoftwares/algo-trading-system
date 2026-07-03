# Claude Review Prompt — A1 XAU M5 Momentum Portfolio Combination Candidate

Boundary: offline review only. Do not touch MT5 runtime, charts, presets, orders, positions, or live/demo account state.

Codex created a portfolio-combination diagnostic because the owner clarified that sparse strategies are not acceptable as the primary lane. The target is now:

```text
multiple trades on active days
win rate above 50%
positive net result after costs
enough active days to support a daily-profit style system
```

Files to review:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.json
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_PORTFOLIO_COMBINATION_DIAGNOSTIC_2026_07_02.csv
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQUENCY_REQUIREMENT_VERDICT_2026_07_02.md
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQ_FIRST_V13_DIRECTIONAL_MASK_VERDICT_2026_07_02.md
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_V4_V13_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md
```

Source exact MT5 reports:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_DIRECTIONAL_MASK_FOUR_YEAR_2022_07_2026_06.json
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_ALT_FOUR_YEAR_2022_07_2026_06.json
```

Codex's current candidate:

```text
v4_plus_v13_leading_raw
```

Reported four-year portfolio result:

```text
Trades: 2918
Win rate: 63.23%
Net: +1905.00 USD
PF: 1.29
Active days: 692
Trades / active day: 4.22
Multi-trade days: 518
Positive months: 33
Negative months: 15
Top-25 removed: +1572.88 USD
Max closed DD: 132.63 USD
Decision: REVIEW_CANDIDATE
```

Comparison:

```text
V4 only: 1132 trades, WR 65.90%, +1042.07 USD, PF 1.45, 383 active days, max DD 88.84
V13 leading only: 1786 trades, WR 61.53%, +862.93 USD, PF 1.20, 668 active days, max DD 192.51
Raw V4+V13: 2918 trades, WR 63.23%, +1905.00 USD, PF 1.29, 692 active days, max DD 132.63
```

Questions:

1. Independently recompute the portfolio metrics from the referenced trade CSVs. Do the numbers match?
2. Is raw V4+V13 a legitimate portfolio improvement, or is it just stacking/duplicate leverage?
3. Does the improved active-day coverage justify the lower PF and higher drawdown versus V4 alone?
4. Is `v4_plus_v13_no_morning_raw` better because it has PF 1.32 and lower worst month, or worse because it has lower net?
5. Which portfolio should be the forward-test candidate, if any?
6. What frozen forward-test spec would you recommend if owner approves demo testing?
7. What kill rules should apply so we do not repeat the broad-overtrading mistake?
8. Should V4 and V13 use separate magic numbers, separate order comments, and separate daily caps, or should they be treated as one combined family exposure?
9. Review the draft forward spec. Is `932200` for V4 and `932201` for V13 acceptable, and are the daily/rolling kill rules strict enough?

Return a verdict:

```text
ENDORSE
ENDORSE_WITH_CHANGES
REVISE
REJECT
```

Please be rigorous but constructive. The owner wants a system that actually trades often enough, not a beautiful low-frequency artifact. Challenge the candidate, but if a viable forward-test shape exists, specify it clearly.
